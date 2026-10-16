"""Calcul de l'IS prévisionnel (UC07). Aucun montant n'est produit par l'IA.

  résultat comptable (balance projetée)
+ réintégrations − déductions                    (art. 15 à 43, référentiel)
− déficits antérieurs imputés                    (art. 43)
= résultat fiscal
  IS de droit commun = résultat fiscal × taux    (art. 46)
  minimum de perception = taux × produits encaissables, avec un plancher (art. 47)
  IS dû = le plus élevé des deux ; + redevance ORTB (art. 47-6)

Chaque montant est arrondi au franc sur sa ligne de piste d'audit ; les totaux
sont des sommes de lignes arrondies, pour que le tableau de passage tombe juste.
"""
from ..balance import Balance, Niveau
from ..dossier import Dossier
from ..montant import ZERO, arrondir_fcfa, en_pourcentage, en_texte
from ..referentiel import Referentiel, Sens
from ..resultat import Alerte, LigneAudit, ResultatFiscal
from .projection import facteur_projection, projeter
from .retraitements import Contexte, appliquer_retraitements, couts_hors_resultat


def calculer_is(balance: Balance, dossier: Dossier, referentiel: Referentiel,
                deja_projetee: bool = False) -> ResultatFiscal:
    p = referentiel.parametres
    plan = p.plan
    hyp = dossier.hypotheses
    bp = balance if deja_projetee else projeter(balance, hyp, plan)
    audit: list[LigneAudit] = []

    # ---- 1. résultat comptable projeté
    chiffre_affaires = bp.total_produits(plan.chiffre_affaires)
    produits = arrondir_fcfa(bp.total_produits(plan.produits))
    charges = arrondir_fcfa(bp.total_charges(plan.charges))
    rc = produits - charges
    audit.append(LigneAudit("1. Résultat comptable", "RC", "Produits − charges (classes 6, 7, 8 projetées)",
                            "AUDCIF / SYSCOHADA", produits, rc,
                            f"Produits {en_texte(produits)} − Charges {en_texte(charges)} "
                            f"(projection × {facteur_projection(hyp):.4f})"))

    # ---- 2. réintégrations et déductions
    impot_comptabilise = bp.total_charges(plan.impot_sur_resultat)
    ctx = Contexte(bp, plan, chiffre_affaires, rc, rc + impot_comptabilise)
    lignes = appliquer_retraitements(ctx, dossier, referentiel)
    noms_categories = {c.id: c.libelle for c in referentiel.categories}
    for ligne in lignes:
        if ligne.montant > 0:
            etape = "2. Réintégration" if ligne.sens is Sens.REINTEGRATION else "2. Déduction"
            audit.append(LigneAudit(etape, ligne.id_regle, ligne.libelle, ligne.article, ligne.base, ligne.montant,
                                    ligne.detail, noms_categories.get(ligne.categorie, "")))
    reintegrations = sum((li.montant for li in lignes if li.sens is Sens.REINTEGRATION), ZERO)
    deductions = sum((li.montant for li in lignes if li.sens is Sens.DEDUCTION), ZERO)

    # ---- 3. déficits antérieurs (imputation obligatoire sur le premier bénéfice)
    avant_deficits = rc + reintegrations - deductions
    deficit_impute = min(max(ZERO, avant_deficits), arrondir_fcfa(hyp.deficits_anterieurs))
    if deficit_impute:
        audit.append(LigneAudit("3. Déficits antérieurs", "ART43", "Imputation des déficits reportables",
                                "CGI art. 43", hyp.deficits_anterieurs, deficit_impute,
                                "Imputation obligatoire sur le premier bénéfice (art. 43-5)"))
    resultat_fiscal = avant_deficits - deficit_impute

    # ---- 4. IS de droit commun
    taux = p.taux_is[dossier.categorie_taux.value]
    is_dc = arrondir_fcfa(max(ZERO, resultat_fiscal) * taux)
    audit.append(LigneAudit("4. IS droit commun", "ART46", f"Résultat fiscal × {en_pourcentage(taux)}", "CGI art. 46",
                            resultat_fiscal, is_dc, f"{en_texte(max(ZERO, resultat_fiscal))} × {en_pourcentage(taux)}"))

    # ---- 5. minimum de perception
    exclus = p.comptes_exclus_encaissables
    encaissables = arrondir_fcfa(bp.total_produits(plan.produits, exclure=exclus))
    taux_min = p.taux_minimum[dossier.secteur.value]
    minimum = arrondir_fcfa(max(taux_min * encaissables, p.plancher_minimum))
    audit.append(LigneAudit("5. Minimum de perception", "ART47",
                            f"{en_pourcentage(taux_min)} des produits encaissables "
                            f"(plancher {en_texte(p.plancher_minimum)})", "CGI art. 47", encaissables, minimum,
                            f"Produits encaissables {en_texte(encaissables)} (hors comptes {', '.join(exclus)}) "
                            f"× {en_pourcentage(taux_min)}"))

    # ---- 6. IS dû et redevance ORTB
    au_minimum = minimum > is_dc
    is_du = max(is_dc, minimum)
    seuil = arrondir_fcfa(minimum / taux)
    regime = "minimum de perception" if au_minimum else "droit commun"
    audit.append(LigneAudit("6. IS dû", "IS", f"Le plus élevé des deux : {regime}", "CGI art. 46-47",
                            is_dc, is_du, f"max({en_texte(is_dc)} ; {en_texte(minimum)})"))
    audit.append(LigneAudit("7. Redevance ORTB", "ORTB", "Redevance au profit de l'ORTB", p.article_ortb,
                            ZERO, p.redevance_ortb, "Montant forfaitaire, payé avec l'acompte de mars"))

    # ---- 8. coûts hors résultat fiscal
    couts = couts_hors_resultat(dossier, referentiel)
    for cout in couts:
        audit.append(LigneAudit("8. Hors résultat fiscal", cout.id, cout.libelle, cout.article, cout.base,
                                cout.montant, f"Droit de timbre {en_pourcentage(p.taux_timbre_especes)} × "
                                              f"{en_texte(cout.base)} payés en espèces"))

    alertes = _alertes(dossier, referentiel, resultat_fiscal, seuil, au_minimum, lignes, couts)
    return ResultatFiscal(
        balance_projetee=bp, chiffre_affaires=arrondir_fcfa(chiffre_affaires), resultat_comptable=rc,
        retraitements=lignes, reintegrations=reintegrations, deductions=deductions,
        deficit_impute=deficit_impute, resultat_fiscal=resultat_fiscal, taux_is=taux, is_droit_commun=is_dc,
        produits_encaissables=encaissables, taux_minimum=taux_min, minimum_perception=minimum, is_du=is_du,
        au_minimum=au_minimum, seuil_bascule=seuil, redevance_ortb=p.redevance_ortb,
        version_referentiel=referentiel.version, audit=tuple(audit), alertes=alertes, hors_resultat=couts,
    )


def _alertes(dossier, referentiel, resultat_fiscal, seuil, au_minimum, lignes, couts) -> tuple[Alerte, ...]:
    """Explications propres au dossier, rédigées par modèles de phrases (sans IA, décision D1.6)."""
    p = referentiel.parametres
    alertes = []
    if au_minimum:
        alertes.append(Alerte("MINIMUM_PERCEPTION", Niveau.ATTENTION,
                              f"Le minimum de perception s'applique : tant que le résultat fiscal reste sous "
                              f"{en_texte(seuil)}, réduire le résultat ne diminue pas l'impôt. Les leviers utiles "
                              f"sont la trésorerie (acomptes) et le chiffre d'affaires encaissable."))
    elif resultat_fiscal - seuil < p.alerte_proximite_seuil * max(seuil, 1):
        alertes.append(Alerte("PROCHE_SEUIL", Niveau.ATTENTION,
                              f"Le résultat fiscal est proche du seuil de bascule ({en_texte(seuil)}) : au-delà "
                              f"d'une réduction de {en_texte(resultat_fiscal - seuil)}, c'est le minimum de "
                              f"perception qui s'appliquera."))
    if resultat_fiscal < 0:
        alertes.append(Alerte("DEFICIT", Niveau.INFO,
                              f"Résultat fiscal prévisionnel déficitaire ({en_texte(resultat_fiscal)}) : reportable "
                              f"{p.duree_report_deficitaire} exercices (art. 43) ; le minimum de perception reste dû."))
    mois = dossier.hypotheses.mois_arrete
    if mois < p.mois_minimum_projection:
        alertes.append(Alerte("PROJECTION_FRAGILE", Niveau.ATTENTION,
                              f"Balance arrêtée après {mois} mois : la projection multiplie l'activité par "
                              f"{12 / mois:.0f}. Résultat très sensible à la saisonnalité : ajuster le coefficient "
                              f"d'activité et les ajustements de fin d'année."))
    manquantes = [li for li in lignes if not li.renseignee]
    if manquantes:
        alertes.append(Alerte("SAISIES_MANQUANTES", Niveau.INFO,
                              f"{len(manquantes)} règle(s) à saisie non renseignée(s) : répondre par un montant ou "
                              f"« néant » avant de soumettre le dossier."))
    for cout in couts:
        alertes.append(Alerte("ESPECES", Niveau.ATTENTION,
                              f"{en_texte(cout.base)} de dépenses réglées en espèces (≥ {en_texte(p.seuil_especes)}) :"
                              f" droit de timbre de {en_texte(cout.montant)} ({cout.article}). À régulariser et à "
                              f"éviter d'ici la clôture."))
    return tuple(alertes)
