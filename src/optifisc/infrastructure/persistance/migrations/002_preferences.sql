-- Préférences et progression du tutoriel, par utilisateur (ex. étapes cochées, guide masqué).
CREATE TABLE preferences (
    email TEXT NOT NULL,
    cle TEXT NOT NULL,
    valeur TEXT NOT NULL,              -- JSON
    PRIMARY KEY (email, cle)
);
