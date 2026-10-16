# 10 — Déroulé de la démonstration pour la soutenance (environ 10 minutes)

> Pour : Salim, le jour J. L'instance de **démonstration** a des raccourcis qui n'existent pas en cabinet :
> connexion en un clic, changement de rôle dans la barre latérale, « tout mettre à néant » sur les
> retraitements, session de 4 heures. Le formalisme reste **visible** pour le jury (rôles, validation,
> traçabilité) sans jamais te bloquer.

## Avant la soutenance (la veille et 15 minutes avant)

- [ ] Ouvrir l'URL de la démo en ligne (elle se « réveille ») ; sinon lancer en local :
      `set OPTIFISC_MODE=demo` puis `set OPTIFISC_MDP_DEMO=<mot de passe>` puis `lancer.bat`.
- [ ] Faire une question test à l'Assistant CGI (vérifie que le modèle gratuit répond).
- [ ] Avoir la vidéo de secours et les captures (`var/captures/`) prêtes.
- [ ] Redémarrer l'application juste avant : la base de démo repart à neuf.

## Le déroulé

| Minute | Rôle (barre latérale) | Action | Message au jury |
|---|---|---|---|
| 0 | — | Écran de connexion → **Collaborateur** | « Trois rôles séparés ; en cabinet, chacun a son compte et son mot de passe. » |
| 1 | Collaborateur | *Dossiers* : montrer le tableau, l'avancement, les filtres | « Chaque collaborateur ne voit que ses dossiers. » |
| 2 | Collaborateur | Ouvrir **BATI-PLUS** → onglet *1 Balance* (rapport de lecture) | « La balance réelle d'un logiciel comptable : titres, totaux et regroupements ignorés. » |
| 3 | Collaborateur | *3 Retraitements* : ouvrir une ligne (ex. R03 dons) puis **Tout mettre à néant** | « 28 règles du CGI, chacune avec son article ; en cabinet, chaque question s'examine une par une. » |
| 4 | Collaborateur | *4 Calcul* → **Calculer** ; montrer minimum de perception et piste d'audit | « L'IA ne calcule rien : tout montant sort du moteur, relié à un article. Démo identique à la V2 au franc près. » |
| 5 | Collaborateur | *5 Leviers* : simuler une provision → **gain 0** (minimum de perception) | « L'outil évite un conseil inutile : réduire le résultat ne sert à rien ici. » |
| 6 | Collaborateur | *6 Acomptes* : **Demander la réduction** | « Le vrai levier ici est la trésorerie : demande au DGI avant le 10/11. » |
| 7 | Collaborateur | Ouvrir **NOVA SERVICES** → *5 Leviers* → **Demander des propositions** | « L'agent IA propose, avec l'article ; le moteur rechiffre ; je décide. Le juge note la confiance. » |
| 8 | Collaborateur | BATI-PLUS → *7 Livrer* → **Soumettre** | « Le dossier est figé : il attend l'expert. » |
| 9 | **Expert** (barre latérale) | *Synthèse* → *Livrer* → **Valider** (cocher les règles non validées) → livrables définitifs | « La validation fige le résultat ; la note Word et l'Excel avec formules sont modifiables avant envoi. » |
| 10 | Expert | *Journal d'audit* | « Tout est tracé, rien ne s'efface. » |

## Si quelque chose ne marche pas

| Problème | Parade |
|---|---|
| L'IA ne répond pas (quota, réseau) | Dire que l'outil est conçu pour fonctionner sans IA ; montrer les articles trouvés localement ; passer à la suite |
| Pas d'internet | Instance locale en mode démo, IA désactivée ; vidéo pour la partie agent |
| Un écran se comporte mal | Redémarrer l'application (base de démo neuve) ou montrer les captures |
| Question du jury sur une règle | *Référentiel des règles* : article, comptes, cas chiffré, statut de validation |
