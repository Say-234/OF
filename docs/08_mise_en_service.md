# 08 — Mise en service (jalon J12)

Deux installations du même code (doc 06, §4.5) : **locale au cabinet** (dossiers réels) et **démonstration en
ligne** (dossiers fictifs, pour la soutenance). Plus un **plan B** si internet manque le jour J.

---

## 1. Installation au cabinet (Windows, un seul poste)

1. Installer **Python 3.12 ou plus récent** depuis python.org (cocher « Add python.exe to PATH »).
2. Copier le dossier `OF/` sur le poste (ou `git clone`).
3. Double-cliquer sur **`lancer.bat`**. Au premier lancement, il crée l'environnement Python et installe les
   dépendances (quelques minutes), copie `.env.exemple` en `.env`, puis ouvre l'application sur
   `http://localhost:8501`. L'application n'est accessible que depuis ce poste.
4. **Premier écran : « Installation »** → créer le compte administrateur. Le mot de passe initial s'affiche
   **une seule fois** : le noter, il devra être changé à la première connexion.
5. L'administrateur crée les comptes (menu *Utilisateurs*) : collaborateurs et expert-comptable. Chaque
   mot de passe initial s'affiche une fois et doit être changé à la première connexion.

Les données sont dans `var/optifisc_cabinet.sqlite`. Restreindre l'accès Windows au dossier `var/`.

## 2. Configurer l'IA (facultatif)

L'application fonctionne **entièrement sans IA** (la recherche d'articles reste disponible). Pour l'activer :

1. Créer une clé sur [openrouter.ai/keys](https://openrouter.ai/keys).
2. Choisir un **modèle gratuit** (nom terminé par `:free`) sur [openrouter.ai/models](https://openrouter.ai/models?max_price=0) ;
   les modèles gratuits changent souvent et ont des limites de débit.
3. Dans `.env` :
   ```
   OPTIFISC_IA=openrouter
   OPENROUTER_API_KEY=<votre clé>
   OPENROUTER_MODELE=<nom du modèle :free>
   ```
4. Relancer `lancer.bat`.

**Confidentialité** (doc 01, A.3) : par défaut, l'agent de propositions ne fonctionne **que sur les dossiers de
démonstration**. Pour un dossier réel, il faut l'activer explicitement (`OPTIFISC_IA_DOSSIERS_REELS=oui`)
— décision du cabinet, qui ne devrait l'être qu'avec un fournisseur d'IA confidentiel.

## 3. Démonstration en ligne (Streamlit Community Cloud)

À faire par Salim (compte personnel, données fictives uniquement) :

1. Créer un dépôt **GitHub** (privé si l'offre gratuite le permet) et y pousser le dossier `OF/`.
   Vérifier avant l'envoi que `.env` et `var/` n'y sont pas (ils sont exclus par `.gitignore`).
2. Sur [share.streamlit.io](https://share.streamlit.io) : *Create app* → choisir le dépôt, la branche, et le
   fichier principal **`src/optifisc/interface/streamlit/app.py`** ; Python 3.12 ou plus récent.
3. Dans *Advanced settings → Secrets*, coller :
   ```toml
   OPTIFISC_MODE = "demo"
   OPTIFISC_MDP_DEMO = "<mot de passe de démo à communiquer au jury>"
   OPTIFISC_IA = "openrouter"
   OPENROUTER_API_KEY = "<clé>"
   OPENROUTER_MODELE = "<modèle :free>"
   ```
4. Déployer. En mode démo, la base est **recréée à chaque démarrage** avec 3 comptes (`admin@demo.bj`,
   `expert@demo.bj`, `salim@demo.bj`) et 2 dossiers fictifs : BATI-PLUS (à préparer en direct) et
   NOVA SERVICES (déjà calculé, toutes les étapes visibles). Les comptes et le mot de passe s'affichent sur
   l'écran de connexion (« Comptes de démonstration »).
5. **La veille et le matin de la soutenance** : ouvrir l'URL quelques minutes avant (l'application gratuite
   se met en veille après une période d'inactivité).

## 4. Plan B le jour de la soutenance

- **Local** : sur le PC de Salim (ou depuis une clé USB contenant `OF/` et son `.venv`), en mode démo :
  ```bat
  set OPTIFISC_MODE=demo
  set OPTIFISC_MDP_DEMO=<mot de passe>
  lancer.bat
  ```
  Sans internet, laisser `OPTIFISC_IA=desactivee` : tout fonctionne sauf la rédaction par l'IA.
- **Vidéo** : enregistrer à l'avance le parcours complet (agent compris).
- **Captures** pour le mémoire : application lancée en mode démo, puis
  `.venv\Scripts\python scripts\captures.py --url http://localhost:8501 --mot-de-passe <mot de passe>`
  → images dans `var/captures/`.

## 5. Exploitation

| Sujet | Procédure |
|---|---|
| Sauvegarde | `sauvegarder.bat E:\OptiFisc` (copie cohérente même application ouverte) ; à planifier chaque jour dans le Planificateur de tâches. Tester une restauration : remplacer `var/optifisc_cabinet.sqlite` par une copie. |
| Nouvelle loi de finances | Créer `referentiel/2027/`, adapter les YAML, lancer les tests, puis l'expert re-valide les règles dans l'écran *Référentiel*. Une règle modifiée perd automatiquement sa validation. |
| Mise à jour du code | Sauvegarder, remplacer le code, relancer : les migrations de la base s'appliquent seules. |
| Tests | `.venv\Scripts\python -m pytest -q` (doivent rester verts). |
