-- Schéma initial d'OptiFisc. Les montants sont stockés en TEXT (Decimal exact), les dates en ISO 8601.

CREATE TABLE utilisateurs (
    email TEXT PRIMARY KEY,
    nom TEXT NOT NULL,
    role TEXT NOT NULL,
    actif INTEGER NOT NULL DEFAULT 1,
    doit_changer_mot_de_passe INTEGER NOT NULL DEFAULT 0,
    sel TEXT NOT NULL,
    empreinte TEXT NOT NULL,
    echecs INTEGER NOT NULL DEFAULT 0,
    bloque_jusqu TEXT,
    derniere_connexion TEXT
);

CREATE TABLE dossiers (
    id TEXT PRIMARY KEY,
    raison_sociale TEXT NOT NULL,
    secteur TEXT NOT NULL,
    categorie_taux TEXT NOT NULL,
    exercice INTEGER NOT NULL,
    demonstration INTEGER NOT NULL DEFAULT 0,
    responsable TEXT NOT NULL DEFAULT '',
    etat TEXT NOT NULL,
    hypotheses TEXT NOT NULL,          -- JSON
    saisies TEXT NOT NULL              -- JSON {id_regle: "montant"}
);

CREATE TABLE balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id TEXT NOT NULL REFERENCES dossiers(id),
    date_arrete TEXT NOT NULL,
    lignes TEXT NOT NULL,              -- JSON [[compte, libellé, débit, crédit], …]
    rapport TEXT NOT NULL,             -- JSON du rapport de lecture
    importe_par TEXT NOT NULL,
    importe_le TEXT NOT NULL
);

CREATE TABLE donnees_dossier (
    dossier_id TEXT NOT NULL REFERENCES dossiers(id),
    cle TEXT NOT NULL,
    valeur TEXT NOT NULL,              -- JSON
    PRIMARY KEY (dossier_id, cle)
);

CREATE TABLE scenarios (
    id TEXT PRIMARY KEY,
    dossier_id TEXT NOT NULL REFERENCES dossiers(id),
    nom TEXT NOT NULL,
    leviers TEXT NOT NULL,             -- JSON
    gain_is TEXT NOT NULL,
    retenu INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE validations_regles (
    id_regle TEXT PRIMARY KEY,
    version_referentiel TEXT NOT NULL,
    valide_par TEXT NOT NULL,
    cas TEXT NOT NULL,
    commentaire TEXT NOT NULL,
    quand TEXT NOT NULL
);

-- Journal en ajout seul : le code n'offre aucune modification ni suppression.
CREATE TABLE journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quand TEXT NOT NULL,
    utilisateur TEXT NOT NULL,
    role TEXT NOT NULL,
    dossier_id TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    version_referentiel TEXT NOT NULL DEFAULT ''
);
CREATE INDEX journal_par_dossier ON journal (dossier_id, id);

-- Interdit techniquement la modification et la suppression du journal.
CREATE TRIGGER journal_sans_modification BEFORE UPDATE ON journal
BEGIN SELECT RAISE(ABORT, 'le journal est en ajout seul'); END;
CREATE TRIGGER journal_sans_suppression BEFORE DELETE ON journal
BEGIN SELECT RAISE(ABORT, 'le journal est en ajout seul'); END;
