# 09 — Guide d'utilisation : qui fait quoi pour que l'outil fonctionne au cabinet

> Pour : les membres du cabinet (administrateur, collaborateurs, expert-comptable) et Salim.
> Objectif : comprendre le rôle de chacun, l'ordre des opérations, et ce que fait la machine à la place
> de l'humain — ou justement pas.

---

## 1. L'outil en une phrase

À partir de la **balance arrêtée en cours d'année** (par exemple au 30 juin), OptiFisc estime l'**impôt sur
les sociétés** de l'année selon le CGI 2026, montre ce qu'on peut encore faire **avant la clôture** pour
le réduire légalement, gère les **acomptes**, et produit une **note au client** validée par l'expert-comptable.

## 2. Qui fait quoi : les cinq intervenants

| Intervenant | Qui c'est | Son rôle dans l'outil | Ce qu'il ne fait PAS |
|---|---|---|---|
| **Administrateur** | La personne qui gère l'outil (souvent un associé) | Installe l'outil, crée les comptes, attribue les dossiers, fait les sauvegardes | Ne prépare ni ne valide aucun dossier fiscal |
| **Collaborateur** | Le collaborateur comptable qui suit le client | Importe la balance, renseigne les hypothèses et les retraitements, simule les leviers, décide des acomptes, soumet le dossier | Ne valide rien ; ne voit que les dossiers qui lui sont attribués |
| **Expert-comptable** | Celui qui signe | Contrôle, valide ou renvoie le dossier ; valide les règles du référentiel ; génère les livrables définitifs | Ne gère pas les comptes utilisateurs |
| **Le moteur** (la machine) | Le programme de calcul | Calcule tout montant : projection, retraitements, IS, minimum de perception, acomptes, gain d'un levier | Ne décide rien ; n'invente aucune règle (elles sont écrites dans le référentiel) |
| **L'IA** (la machine, facultative) | Un modèle en ligne gratuit | Retrouve et explique les articles du CGI ; **propose** des pistes d'optimisation | Ne calcule jamais un impôt ; ne voit jamais le nom du client ni la balance ; ne décide rien |

> La règle d'or : **l'IA propose, le moteur chiffre, l'humain décide.**

## 3. Le circuit d'un dossier, étape par étape

| # | Étape | Qui | Ce qu'il fait | Ce que fait l'outil |
|---|---|---|---|---|
| 0 | Mise en place (une fois) | Administrateur | Crée les comptes ; attribue le dossier au collaborateur | Trace tout dans le journal |
| 1 | Balance | Collaborateur | Exporte la balance du logiciel comptable (Excel ou CSV), la dépose, lit le rapport de lecture, confirme | Lit le fichier, ignore titres/totaux/regroupements, contrôle l'équilibre |
| 2 | Hypothèses | Collaborateur | Indique le rythme d'activité du reste de l'année, les dotations non encore passées, l'IS N-1, l'AIB, les déficits | Projette la balance au 31/12 |
| 3 | Retraitements | Collaborateur | Vérifie les lignes calculées ; **répond à chaque question** (un montant ou « néant ») en cherchant dans les pièces indiquées | Calcule les 5 réintégrations automatiques, applique les plafonds |
| 4 | Calcul | Collaborateur | Lance le calcul, lit les alertes | IS de droit commun, minimum de perception, IS dû, seuil de bascule, piste d'audit |
| 5 | Leviers | Collaborateur | Simule des options (investissement, provision, don…), en retient une ou aucune ; peut demander des propositions à l'IA et les accepter/écarter | Chiffre chaque levier ; dit si le gain est une économie ou un simple décalage |
| 6 | Acomptes | Collaborateur | Décide de demander ou non une réduction des acomptes au DGI | Calcule l'échéancier, la date limite, la trésorerie préservée |
| 7a | Soumission | Collaborateur | Soumet le dossier | Vérifie la liste de contrôle ; fige le dossier |
| 7b | Validation | **Expert-comptable** | Contrôle la synthèse et la piste d'audit ; valide (ou renvoie avec un commentaire) | Fige le résultat validé (montants, date, valideur) |
| 7c | Livrables | **Expert-comptable** | Génère et relit la note de pilotage, le dossier de calcul et la lettre au DGI, puis les envoie | Produit les fichiers Word/Excel modifiables |
| 8 | Après | Client / DGI | Le client applique les décisions ; la demande d'acompte est déposée avant la date limite | — |

**Quand ?** L'outil est fait pour le **pilotage en cours d'année** : idéalement après la balance de juin, et
au plus tard **un mois avant l'échéance d'acompte** visée (le 10 décembre : demande avant le 10 novembre).

## 4. Pas à pas par rôle

### Administrateur — la première fois
1. Lancer `lancer.bat` ; sur l'écran « Installation », créer son compte (noter le mot de passe affiché une fois).
2. *Utilisateurs* → créer un compte par collaborateur et pour l'expert-comptable (transmettre à chacun son
   mot de passe provisoire ; il le changera à la première connexion).
3. Faire valider le **référentiel** par l'expert-comptable (voir ci-dessous) avant le premier vrai dossier.
4. Programmer une sauvegarde quotidienne (`sauvegarder.bat`).

### Expert-comptable — la première fois : valider les règles
Les 28 règles de retraitement sont livrées **« à valider »**. Dans *Référentiel des règles*, pour chaque
règle : lire l'article, vérifier les comptes et le taux sur un **cas chiffré**, puis « Valider la règle ».
Tant qu'une règle n'est pas validée, l'outil l'applique mais le signale, et la validation d'un dossier
demande de cocher « J'ai vérifié les règles non validées ».

### Collaborateur — pour chaque dossier
*Dossiers* → *Nouveau dossier* (ou ouvrir le dossier attribué) → suivre les onglets **1 à 7** dans l'ordre.
Un onglet coché ✓ est terminé. Si un onglet dit « pas encore accessible », il manque l'étape précédente.

### Expert-comptable — pour chaque dossier
*Dossiers* : les dossiers « À valider » sont en tête. Ouvrir → *Synthèse* (points d'attention) →
au besoin *Calcul* (piste d'audit) → *Livrer* : **Valider** ou **Renvoyer avec commentaire** →
générer les livrables définitifs.

## 5. Ce qui bloque, et pourquoi (questions fréquentes)

| Situation | Pourquoi | Que faire |
|---|---|---|
| « Avant de soumettre : … » | La liste de contrôle n'est pas complète (souvent : des retraitements non renseignés, ou pas de décision sur les acomptes) | Répondre aux saisies restantes (« néant » si rien), décider des acomptes, recalculer |
| « Le calcul n'est pas à jour » | Une donnée a changé après le calcul | Onglet *Calcul* → « Calculer » |
| Le dossier est en lecture seule | Il est soumis, validé ou livré : il est figé pour garantir ce que l'expert a validé | L'expert peut le **renvoyer** (s'il est à valider) ou le **rouvrir** avec un motif |
| Je ne vois pas un dossier | Un collaborateur ne voit que ses dossiers | L'administrateur ou l'expert l'attribue |
| L'IA refuse un dossier réel | Par défaut, rien d'un dossier réel n'est envoyé à un service en ligne | Normal (confidentialité) ; l'outil fonctionne sans IA |
| « Question non envoyée à l'IA » | La question contenait un montant ou un nom de client | La reformuler sur la loi, sans donnée du client |
| « Limite d'appels du modèle gratuit » | Quota du modèle gratuit atteint | Réessayer une minute plus tard ; la recherche d'articles marche toujours |
| Compte bloqué | 5 mots de passe faux | Attendre 15 minutes, ou l'administrateur réinitialise le mot de passe |

## 6. Ce que l'outil garantit (à dire au client et au jury)

- **Chaque montant est traçable** : règle, article du CGI, base et formule (*Calcul* → piste d'audit).
- **Rien n'est effacé** : le journal d'audit garde qui a fait quoi et quand.
- **Le validé est figé** : la note envoyée correspond exactement au résultat validé par l'expert.
- **La confidentialité** : les données clients restent sur le poste du cabinet ; l'IA ne reçoit que des
  textes de loi publics et, sur les dossiers de démonstration, un profil sans nom ni montant exact.
