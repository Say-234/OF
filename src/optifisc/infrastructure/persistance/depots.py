"""Dépôts SQLite : implémentent les ports DepotDossiers, DepotBalances, Journal, etc.

Toutes les requêtes sont PARAMÉTRÉES (« ? ») : une valeur saisie n'est jamais collée
dans le texte SQL, ce qui empêche l'injection SQL.
Les montants passent en TEXT (str(Decimal)) et reviennent en Decimal, sans perte.
"""
import json
from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal

from optifisc.domaine.balance import Balance, LigneBalance, RapportLecture
from optifisc.domaine.dossier import Ajustement, CategorieTaux, Dossier, EtatDossier, Hypotheses, Secteur
from optifisc.domaine.journal import EvenementAudit
from optifisc.domaine.scenario import LevierChoisi, Scenario
from optifisc.domaine.utilisateur import Role, Utilisateur

from .connexion import BaseSqlite


# ------------------------------------------------------------------ conversions JSON
def _en_json(valeur) -> str:
    return json.dumps(valeur, ensure_ascii=False, default=str)


def _dt(texte: str | None) -> datetime | None:
    return datetime.fromisoformat(texte) if texte else None


def _hypotheses_vers_dict(h: Hypotheses) -> dict:
    return {"mois_arrete": h.mois_arrete, "coef_activite": str(h.coef_activite),
            "ajustements": [[a.compte, a.libelle, str(a.montant)] for a in h.ajustements],
            "is_n_moins_1": str(h.is_n_moins_1), "aib_imputable": str(h.aib_imputable),
            "deficits_anterieurs": str(h.deficits_anterieurs),
            "acomptes_payes": None if h.acomptes_payes is None else str(h.acomptes_payes)}


def _hypotheses_depuis_dict(d: dict) -> Hypotheses:
    return Hypotheses(mois_arrete=d["mois_arrete"], coef_activite=Decimal(d["coef_activite"]),
                      ajustements=tuple(Ajustement(c, lib, Decimal(m)) for c, lib, m in d["ajustements"]),
                      is_n_moins_1=Decimal(d["is_n_moins_1"]), aib_imputable=Decimal(d["aib_imputable"]),
                      deficits_anterieurs=Decimal(d["deficits_anterieurs"]),
                      acomptes_payes=None if d["acomptes_payes"] is None else Decimal(d["acomptes_payes"]))


# ------------------------------------------------------------------ dossiers
class DepotDossiersSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def enregistrer(self, d: Dossier) -> None:
        with self.base.connexion() as cx:
            cx.execute(
                "INSERT INTO dossiers (id, raison_sociale, secteur, categorie_taux, exercice, demonstration, "
                "responsable, etat, hypotheses, saisies) VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET raison_sociale=excluded.raison_sociale, secteur=excluded.secteur, "
                "categorie_taux=excluded.categorie_taux, exercice=excluded.exercice, "
                "demonstration=excluded.demonstration, responsable=excluded.responsable, etat=excluded.etat, "
                "hypotheses=excluded.hypotheses, saisies=excluded.saisies",
                (d.id, d.raison_sociale, d.secteur.value, d.categorie_taux.value, d.exercice, int(d.demonstration),
                 d.responsable, d.etat.value, _en_json(_hypotheses_vers_dict(d.hypotheses)),
                 _en_json({k: str(v) for k, v in d.saisies.items()})))

    def charger(self, id_dossier: str) -> Dossier | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT * FROM dossiers WHERE id = ?", (id_dossier,)).fetchone()
        return self._dossier(ligne) if ligne else None

    def lister(self) -> list[Dossier]:
        with self.base.connexion() as cx:
            lignes = cx.execute("SELECT * FROM dossiers ORDER BY raison_sociale").fetchall()
        return [self._dossier(ligne) for ligne in lignes]

    @staticmethod
    def _dossier(ligne) -> Dossier:
        (id_, raison, secteur, categorie, exercice, demo, responsable, etat, hypotheses, saisies) = ligne
        return Dossier(id=id_, raison_sociale=raison, secteur=Secteur(secteur), categorie_taux=CategorieTaux(categorie),
                       exercice=exercice, demonstration=bool(demo), responsable=responsable, etat=EtatDossier(etat),
                       hypotheses=_hypotheses_depuis_dict(json.loads(hypotheses)),
                       saisies={k: Decimal(v) for k, v in json.loads(saisies).items()})


# ------------------------------------------------------------------ balances (historique conservé)
class DepotBalancesSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def enregistrer(self, dossier_id: str, balance: Balance, rapport: RapportLecture, date_arrete: date,
                    par: str, quand: datetime) -> None:
        lignes = [[li.compte, li.libelle, str(li.debit), str(li.credit)] for li in balance.lignes]
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO balances (dossier_id, date_arrete, lignes, rapport, importe_par, importe_le) "
                       "VALUES (?,?,?,?,?,?)", (dossier_id, date_arrete.isoformat(), _en_json(lignes),
                                                _en_json(asdict(rapport)), par, quand.isoformat()))

    def derniere(self, dossier_id: str) -> tuple[Balance, RapportLecture, date] | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT lignes, rapport, date_arrete FROM balances WHERE dossier_id = ? "
                               "ORDER BY id DESC LIMIT 1", (dossier_id,)).fetchone()
        if not ligne:
            return None
        lignes = tuple(LigneBalance(c, lib, Decimal(d), Decimal(k)) for c, lib, d, k in json.loads(ligne[0]))
        r = json.loads(ligne[1])
        rapport = RapportLecture(**{**r, "regroupements_ignores": tuple(r["regroupements_ignores"]),
                                    "valeurs_illisibles": tuple(r["valeurs_illisibles"])})
        return Balance(lignes), rapport, date.fromisoformat(ligne[2])


# ------------------------------------------------------------------ données annexes d'un dossier
class DepotDonneesDossierSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def sauver(self, dossier_id: str, cle: str, valeur: dict) -> None:
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO donnees_dossier (dossier_id, cle, valeur) VALUES (?,?,?) "
                       "ON CONFLICT(dossier_id, cle) DO UPDATE SET valeur = excluded.valeur",
                       (dossier_id, cle, _en_json(valeur)))

    def lire(self, dossier_id: str, cle: str) -> dict | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT valeur FROM donnees_dossier WHERE dossier_id = ? AND cle = ?",
                               (dossier_id, cle)).fetchone()
        return json.loads(ligne[0]) if ligne else None


# ------------------------------------------------------------------ scénarios
class DepotScenariosSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def enregistrer(self, s: Scenario) -> None:
        leviers = [{"id_levier": lv.id_levier, "parametres": lv.parametres} for lv in s.leviers]
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO scenarios (id, dossier_id, nom, leviers, gain_is, retenu) VALUES (?,?,?,?,?,?) "
                       "ON CONFLICT(id) DO UPDATE SET nom=excluded.nom, leviers=excluded.leviers, "
                       "gain_is=excluded.gain_is, retenu=excluded.retenu",
                       (s.id, s.dossier_id, s.nom, _en_json(leviers), str(s.gain_is), int(s.retenu)))

    def lister(self, dossier_id: str) -> list[Scenario]:
        with self.base.connexion() as cx:
            lignes = cx.execute("SELECT id, dossier_id, nom, leviers, gain_is, retenu FROM scenarios "
                                "WHERE dossier_id = ? ORDER BY nom", (dossier_id,)).fetchall()
        return [Scenario(id_, dos, nom, tuple(LevierChoisi(lv["id_levier"], lv["parametres"])
                                              for lv in json.loads(leviers)), Decimal(gain), bool(retenu))
                for id_, dos, nom, leviers, gain, retenu in lignes]

    def supprimer(self, scenario_id: str) -> None:
        with self.base.connexion() as cx:
            cx.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))


# ------------------------------------------------------------------ validation des règles
class DepotValidationsSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def valider(self, id_regle: str, version: str, par: str, cas: str, commentaire: str, quand: datetime) -> None:
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO validations_regles VALUES (?,?,?,?,?,?) ON CONFLICT(id_regle) DO UPDATE SET "
                       "version_referentiel=excluded.version_referentiel, valide_par=excluded.valide_par, "
                       "cas=excluded.cas, commentaire=excluded.commentaire, quand=excluded.quand",
                       (id_regle, version, par, cas, commentaire, quand.isoformat()))

    def annuler(self, id_regle: str) -> None:
        with self.base.connexion() as cx:
            cx.execute("DELETE FROM validations_regles WHERE id_regle = ?", (id_regle,))

    def lister(self) -> dict[str, dict]:
        with self.base.connexion() as cx:
            lignes = cx.execute("SELECT id_regle, version_referentiel, valide_par, cas, commentaire, quand "
                                "FROM validations_regles").fetchall()
        return {r: {"version": v, "valide_par": p, "cas": c, "commentaire": com, "quand": _dt(q)}
                for r, v, p, c, com, q in lignes}


# ------------------------------------------------------------------ utilisateurs
class DepotUtilisateursSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def ajouter(self, u: Utilisateur, sel: str, empreinte: str) -> None:
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO utilisateurs (email, nom, role, actif, doit_changer_mot_de_passe, sel, empreinte) "
                       "VALUES (?,?,?,?,?,?,?)", (u.email, u.nom, u.role.value, int(u.actif),
                                                  int(u.doit_changer_mot_de_passe), sel, empreinte))

    def charger(self, email: str) -> Utilisateur | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT email, nom, role, actif, doit_changer_mot_de_passe FROM utilisateurs "
                               "WHERE email = ?", (email,)).fetchone()
        return self._utilisateur(ligne) if ligne else None

    def lister(self) -> list[Utilisateur]:
        with self.base.connexion() as cx:
            lignes = cx.execute("SELECT email, nom, role, actif, doit_changer_mot_de_passe FROM utilisateurs "
                                "ORDER BY role, nom").fetchall()
        return [self._utilisateur(ligne) for ligne in lignes]

    def modifier(self, u: Utilisateur) -> None:
        with self.base.connexion() as cx:
            cx.execute("UPDATE utilisateurs SET nom = ?, role = ?, actif = ?, doit_changer_mot_de_passe = ? "
                       "WHERE email = ?", (u.nom, u.role.value, int(u.actif), int(u.doit_changer_mot_de_passe),
                                           u.email))

    def identifiants(self, email: str) -> tuple[str, str] | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT sel, empreinte FROM utilisateurs WHERE email = ?", (email,)).fetchone()
        return (ligne[0], ligne[1]) if ligne else None

    def changer_mot_de_passe(self, email: str, sel: str, empreinte: str, doit_changer: bool) -> None:
        with self.base.connexion() as cx:
            cx.execute("UPDATE utilisateurs SET sel = ?, empreinte = ?, doit_changer_mot_de_passe = ? WHERE email = ?",
                       (sel, empreinte, int(doit_changer), email))

    def etat_connexion(self, email: str) -> tuple[int, datetime | None]:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT echecs, bloque_jusqu FROM utilisateurs WHERE email = ?", (email,)).fetchone()
        return (ligne[0], _dt(ligne[1])) if ligne else (0, None)

    def noter_connexion(self, email: str, echecs: int, bloque_jusqu: datetime | None,
                        derniere: datetime | None) -> None:
        with self.base.connexion() as cx:
            cx.execute("UPDATE utilisateurs SET echecs = ?, bloque_jusqu = ?, "
                       "derniere_connexion = COALESCE(?, derniere_connexion) WHERE email = ?",
                       (echecs, bloque_jusqu.isoformat() if bloque_jusqu else None,
                        derniere.isoformat() if derniere else None, email))

    @staticmethod
    def _utilisateur(ligne) -> Utilisateur:
        email, nom, role, actif, doit_changer = ligne
        return Utilisateur(email, nom, Role(role), bool(actif), bool(doit_changer))


# ------------------------------------------------------------------ journal (ajout seul)
class JournalSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def ajouter(self, e: EvenementAudit) -> None:
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO journal (quand, utilisateur, role, dossier_id, action, detail, version_referentiel)"
                       " VALUES (?,?,?,?,?,?,?)", (e.quand.isoformat(timespec="seconds"), e.utilisateur, e.role,
                                                   e.dossier_id, e.action, e.detail, e.version_referentiel))

    def lister(self, dossier_id: str | None = None, limite: int = 50) -> list[EvenementAudit]:
        requete = "SELECT quand, utilisateur, role, action, detail, dossier_id, version_referentiel FROM journal"
        parametres: tuple = ()
        if dossier_id is not None:
            requete += " WHERE dossier_id = ?"
            parametres = (dossier_id,)
        requete += " ORDER BY id DESC LIMIT ?"
        with self.base.connexion() as cx:
            lignes = cx.execute(requete, (*parametres, limite)).fetchall()
        return [EvenementAudit(datetime.fromisoformat(q), u, r, a, d, dos, v) for q, u, r, a, d, dos, v in lignes]


# ------------------------------------------------------------------ préférences par utilisateur (tutoriel)
class DepotPreferencesSqlite:
    def __init__(self, base: BaseSqlite):
        self.base = base

    def sauver(self, email: str, cle: str, valeur: dict) -> None:
        with self.base.connexion() as cx:
            cx.execute("INSERT INTO preferences (email, cle, valeur) VALUES (?,?,?) "
                       "ON CONFLICT(email, cle) DO UPDATE SET valeur = excluded.valeur", (email, cle, _en_json(valeur)))

    def lire(self, email: str, cle: str) -> dict | None:
        with self.base.connexion() as cx:
            ligne = cx.execute("SELECT valeur FROM preferences WHERE email = ? AND cle = ?", (email, cle)).fetchone()
        return json.loads(ligne[0]) if ligne else None
