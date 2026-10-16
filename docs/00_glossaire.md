# 00 — Glossaire

Les termes sont classés en deux familles : **métier** (fiscalité, comptabilité) et **technique**
(programmation). Chaque définition technique dit aussi *pourquoi* le projet en a besoin.

## Termes métier

| Terme | Définition |
|---|---|
| **Balance générale** | Tableau de tous les comptes du plan comptable avec leurs totaux débit et crédit à une date donnée. C'est la donnée d'entrée de l'outil. |
| **Balance à date** | Balance arrêtée en cours d'exercice (ex. au 30 juin), et non à la clôture. |
| **Projection** | Estimation des comptes au 31/12 à partir de la balance à date (ex. 6 mois réalisés × 12/6). |
| **SYSCOHADA révisé** | Plan comptable de l'espace OHADA. Les classes 6 (charges) et 7 (produits) servent au résultat ; les classes 8 aux opérations hors activités ordinaires (HAO). |
| **Résultat comptable** | Produits − charges. |
| **Réintégration** | Charge comptabilisée que le fisc refuse de déduire (ex. amendes, art. 36) : on l'ajoute au résultat comptable. |
| **Déduction** | Produit comptabilisé que le fisc n'impose pas (ex. revenus de titres publics, art. 15) : on le retire. |
| **Résultat fiscal** | Résultat comptable + réintégrations − déductions − déficits antérieurs imputés. |
| **IS de droit commun** | Résultat fiscal × taux (30 %, ou 25 % pour l'industrie et l'enseignement privé), art. 46. |
| **Minimum de perception** | Impôt plancher calculé sur les produits encaissables (1 %, 3 % BTP, 10 % immobilier ; au moins 250 000 FCFA), art. 47. L'IS dû est le plus élevé des deux. |
| **Seuil de bascule** | Résultat fiscal au-dessus duquel l'IS de droit commun dépasse le minimum de perception. En dessous, réduire le résultat ne réduit pas l'impôt. |
| **Levier d'optimisation** | Décision légale prise avant la clôture qui modifie l'impôt (ex. amortissement dégressif, art. 40). |
| **Acomptes d'IS** | Quatre versements de 25 % de l'IS de l'année précédente (art. 51). On peut en demander la réduction si l'IS de l'année sera plus faible (art. 52). |
| **AIB** | Acompte sur impôt assis sur les bénéfices, prélevé par les fournisseurs et clients, imputable sur l'IS (art. 132-133). |
| **Redevance ORTB** | Montant forfaitaire ajouté à l'IS (art. 47-6). |
| **Piste d'audit** | Liste qui relie chaque montant calculé à la règle, à l'article, à la base et à la formule utilisés. |

## Termes techniques

| Terme | Définition | Pourquoi on en a besoin |
|---|---|---|
| **Python** | Langage de programmation lisible, très utilisé pour les données. | Langage unique de tout le projet. |
| **Environnement virtuel (`venv`)** | Dossier qui contient une copie isolée de Python et des bibliothèques du projet. | Éviter les conflits entre projets (c'est exactement ce qui a cassé les tests de la V2 lors de l'audit). |
| **Bibliothèque / dépendance** | Code écrit par d'autres, qu'on installe (ex. Streamlit). | Ne pas réinventer ce qui existe. |
| **`pyproject.toml`** | Fichier qui décrit le projet et liste ses dépendances. | Une seule source de vérité pour l'installation. |
| **Module / paquet** | Un fichier `.py` est un module ; un dossier de modules est un paquet. | Ranger le code par responsabilité. |
| **`dataclass`** | Façon courte d'écrire une classe qui sert surtout à porter des données. | Représenter un dossier, une ligne de balance, un résultat. |
| **Immuable (`frozen=True`)** | Un objet qu'on ne peut plus modifier après sa création. | Un résultat de calcul ne doit pas pouvoir être modifié en douce après coup. |
| **`Decimal`** | Type de nombre décimal exact de Python (contrairement à `float`). | Les montants doivent être exacts au franc près (voir doc 01). |
| **Type hints** | Annotations qui disent le type attendu (`montant: Decimal`). | Lisibilité et détection d'erreurs avant l'exécution. |
| **Test unitaire (`pytest`)** | Petit programme qui vérifie automatiquement qu'une fonction donne le résultat attendu. | Prouver qu'un calcul fiscal est juste, et le rester quand on modifie le code. |
| **YAML** | Format de fichier texte lisible par un humain (indentation, `clé: valeur`). | Écrire les règles fiscales sous une forme qu'un comptable peut relire. |
| **Validation de schéma (`pydantic`)** | Vérification automatique qu'un fichier de données a la bonne forme. | Refuser au démarrage un YAML mal écrit plutôt que planter au milieu d'un calcul. |
| **SQLite** | Base de données contenue dans un seul fichier, sans serveur. | Stocker dossiers, historique et utilisateurs sur le poste du cabinet. |
| **Migration** | Script numéroté qui fait évoluer la structure de la base. | Changer la base sans perdre les données existantes. |
| **Streamlit** | Bibliothèque qui transforme un script Python en application web. | Interface rapide à construire, utilisable dans le navigateur, sans écrire de JavaScript. |
| **`session_state`** | Mémoire de Streamlit propre à un utilisateur connecté. | Retenir l'utilisateur et le dossier ouvert d'un écran à l'autre. |
| **LLM** | Grand modèle de langage (IA générative de texte). | Rédiger des réponses à partir des articles du CGI. |
| **OpenRouter** | Service en ligne qui donne accès à de nombreux LLM par une seule API. | Fournisseur d'IA retenu (voir doc 01 pour les précautions). |
| **API / clé d'API** | Interface d'accès à un service distant ; la clé est le mot de passe de cet accès. | Appeler OpenRouter ; la clé ne doit jamais être écrite dans le code. |
| **RAG** | *Retrieval-Augmented Generation* : on cherche d'abord les bons articles, puis on demande au LLM de répondre **uniquement** à partir d'eux. | Limiter les inventions de l'IA et obliger à citer les articles. |
| **BM25** | Algorithme classique de recherche par mots-clés. | Retrouver les articles pertinents, localement, sans IA. |
| **Architecture hexagonale** | Organisation du code où le métier est au centre et ne dépend d'aucun outil technique (voir doc 01). | Pouvoir tester le calcul de l'IS sans base, sans écran, sans IA. |
| **Port** | Description (interface) d'un service dont le métier a besoin, sans dire comment il est fait. | Ex. « un fournisseur de réponses IA ». |
| **Adaptateur** | Implémentation concrète d'un port. | Ex. « fournisseur de réponses via OpenRouter ». |
| **Cas d'usage** | Une action métier complète (ex. « calculer l'IS prévisionnel »). | Unité d'organisation de la couche Application. |
| **Injection de dépendances** | On donne à un objet les services dont il a besoin, au lieu qu'il les crée lui-même. | Remplacer la vraie base par une fausse dans les tests. |
| **Hachage de mot de passe** | Transformation à sens unique d'un mot de passe ; on stocke l'empreinte, jamais le mot de passe. | Si la base est volée, les mots de passe ne le sont pas. |
| **Fail-closed** | Par défaut, refuser. On n'autorise que ce qui est explicitement permis. | Une erreur de configuration ne doit jamais ouvrir un droit. |
| **Agent IA** | LLM à qui l'on confie une mission et une boîte à outils. Il décide lui-même, tour après tour, quel outil utiliser, dans une limite de tours fixée par le code. | Proposer des axes d'optimisation (UC14) au lieu de seulement répondre à une question. |
| **Outil (*tool calling*)** | Fonction de notre code que le LLM peut demander d'exécuter. Il décrit l'appel ; c'est notre code qui l'exécute et lui renvoie le résultat. | L'agent chiffre un levier en appelant le **moteur déterministe** : il ne calcule jamais lui-même. |
| **Pseudonymisation** | Remplacement ou retrait des éléments qui identifient une personne ou une société (nom, IFU), avec des montants arrondis. | Construire le profil de dossier envoyé à l'agent sans révéler le client (doc 01, A.3). |
| **Maître-détail** | Schéma d'écran : une liste (le maître) et, en dessous ou à côté, le détail de l'élément sélectionné. | Schéma commun des écrans Retraitements, Leviers et Référentiel (doc 05). |
| **Modèle de décision (« Système 1 »)** | Modèle qui ne rédige pas de texte : il répond à des questions fermées (choix, échelle, oui/non) par des probabilités, en un seul calcul. Exemples : Jev, Laya. | Prioriser et juger les propositions de l'agent, vite et sans texte à analyser. |
| **Système 1 / Système 2** | Distinction de Kahneman : pensée rapide et intuitive / pensée lente et réfléchie. En IA : modèle de décision / LLM génératif. | Faire travailler les deux ensemble (doc 01, A.4). |
| **Calibration** | Un modèle est calibré si, parmi ses réponses données à 80 %, environ 80 % sont justes. C'est mesuré sur beaucoup de réponses, jamais garanti pour une seule. | Savoir quand une probabilité peut servir de seuil, et pourquoi ce seuil doit être vérifié sur nos propres dossiers. |
