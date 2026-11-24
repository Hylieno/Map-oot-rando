# Décisions

- Citadelle. Les plans sont distincts par âge. Les étagères utilisent le
  placement renvoyé par OotrR. Les deux récompenses du bowling gardent
  leurs identifiants et partagent le repère du jeu.
- Château d’Hyrule. La cour a sa propre vue schématique pour garder
  les coordonnées de la lettre et des caisses. L’accès depuis la
  Citadelle utilise le repère de la vue enfant.
- Château de Ganon. Le trajet depuis la Citadelle utilise le passage
  adulte. Les deux châteaux partagent un repère géographique sur la
  carte générale, qui affiche le château de l’âge courant. L’effondrement
  a sa propre vue et conserve les coordonnées natives des pots.
- Intérieur du Château de Ganon. Les repères des épreuves viennent
  des événements de levée de barrière. La tour utilise les acteurs de
  terrain et la hauteur. Le pont d’entrée mène aux épreuves même si sa
  hauteur recoupe celle de l’accès à la tour.
- Vallée Gerudo. Un repère affine commun utilise le pont principal, le
  rondin, la tente adulte et les deux extrémités du passage. Les deux
  grottes utilisent leurs entrées issues de la scène.
- Forteresse Gerudo. Le passage depuis la vallée dépend de l’âge. Les
  deux scores du tir à l’arc partagent le repère de l’organisatrice.
  Les positions de la carte Gerudo viennent des quatre branches de la
  cinématique `Dm_Gerudo_0025`.
- Centre d’entraînement Gerudo. Les centres de salle et la hauteur de
  la passerelle sont lus dans la scène. Le retour vers la forteresse
  utilise le passage du hall. Les entrées historiques du catalogue
  conservent leur ID tant que leur acteur correspondant reste à vérifier.
- Désert hanté. Le schéma trace le rail natif du guide avec ses points
  de contrôle. Le repère est commun aux deux âges. Le passage de la
  forteresse utilise le portail de la scène adulte.
- Colosse du désert. L’entrée est, la porte du temple et le centre
  de l’oasis servent de repères pour le fond. La Grande Fée utilise le
  repère de la scène et le coffre souterrain celui de l’accès à sa grotte.
- Temple de l’Esprit. Les quatre captures utilisent un repère commun.
  Le numéro de salle et la hauteur distinguent les checks qui se
  superposent autour de la statue. Les passages des mains mènent
  directement aux galeries du deuxième étage.
- Lac Hylia. Les vues du lac et de la plaine partagent la scène native.
  L’alignement utilise le portail, les deux petites îles, le laboratoire,
  le ponton de pêche et l’île des flèches de feu. Le passage Zora
  apparaît dans les deux sens en vue enfant.
- Temple de l’Eau. La carte ouvre l’étage de l’entrée immergée. Le
  rez-de-chaussée comprend le bassin de Morpha, même si sa hauteur
  correspond à celle de l’étage supérieur.

- La carte générale réutilise l’illustration Nintendúo et les positions
  géographiques publiées par Ocarina Atlas. Tous les fonds locaux publiés
  viennent de Field Atlas et se chargent automatiquement.
- Bois Perdus. Le plan et l’itinéraire sont dessinés à partir des carrefours
  et passages observés dans les scènes du jeu. Les raccourcis Goron et Zora
  sont navigables dans les deux sens.
- Rivière Zora. Le coffre et les pots enterrés utilisent leurs entrées de
  grotte. Le mini-jeu des grenouilles est repéré au point où Link joue de
  l’ocarina dans la scène enfant.
- Domaine Zora. Les variantes adultes ont les mêmes passages et le même
  plan. Leurs placements sont réunis dans la vue adulte. Un placement
  commun à moins de 5 cm est représenté une fois avec l’ID OotrR d’origine.
- Fontaine Zora. Le repère du passage depuis le Domaine confirme des
  origines nord-sud distinctes pour les fonds enfant et adulte. Les checks
  derrière la paroi utilisent l’entrée du passage. Leurs coordonnées XYZ
  restent consultables.
- Caverne de glace. Une seule scène réunit les placements statiques et
  dynamiques. Le passage utilise l’entrée principale de la Fontaine adulte.
- Jabu-Jabu. Les plans d’étage partagent un repère X/Z contrôlé sur les
  positions d’acteurs. Les numéros de salle déterminent les niveaux des
  checks recoupés. L’arène de Barinade garde un schéma et les XYZ du jeu.
- Arbre Mojo. Le hall commun à plusieurs niveaux utilise la hauteur. Les
  autres salles recoupées utilisent le numéro d’origine. Les six checks
  de la salle de Gohma s’affichent dans l’arène.
- Temple de la Forêt. Les cours et les passerelles utilisent les numéros
  de salle vérifiés. Le coffre de la clé du boss, sans numéro de salle,
  utilise sa hauteur et le plan correspondant. Le cœur et Ganon spectral
  ont une vue dédiée.
- Puits de Cocorico. Les salles de la Loupe et du niveau profond utilisent
  le deuxième plan. Le passage du puits reprend le repère natif de Cocorico.
- Temple de l’Ombre. Les salles du bateau partagent le plan inférieur.
  Le numéro de salle garde les ennemis suspendus au même niveau que les
  checks au sol. Bongo Bongo et son cœur ont un schéma dédié.
- Link. Le marqueur et le changement automatique de zone sont deux commandes
  distinctes. Les coordonnées sont lues via la connexion mémoire OotrR.
  Les décalages du module et les champs de pose viennent de la documentation
  technique publiée par [Ocarina Atlas](https://github.com/antonioalvromero/Ocarina-Atlas).
- Bosquet sacré. Les entrées de grotte viennent des acteurs physiques
  correspondants. Les coordonnées en sous-sol restent accessibles dans les détails.
- Cocorico. Les fonds Field Atlas sans icônes sont validés sur six repères
  physiques. Les placements adultes sont séparés par variante de scène.
- Cimetière. La surface et les placements enfouis sont séparés par altitude
  vérifiée dans cette scène.
- Village Goron. Le fond commun est vérifié avec un repère indépendant sur
  la galerie est. Les marqueurs sont filtrés par étage et la grotte conserve
  une vue schématique.
- Caverne Dodongo. Un fond distinct est calibré pour chaque étage.
  L’arène est sous les deux plans et garde une vue schématique.
- Cratère du Péril. La corniche sud contrôle le recalage indépendamment.
  Les checks sous Y = 90 utilisent la vue souterraine. Le lien avec le
  Village Goron correspond au niveau de l’entrée côté cratère.
- Temple du Feu. Les cinq recadrages Field Atlas sont indexés par leur contenu.
  La projection X/Z et les seuils de niveaux suivent les mesures publiées
  par Ocarina Atlas. L’arène utilise le centre référencé par l’acteur du boss.
  [Source de la calibration](https://github.com/antonioalvromero/Ocarina-Atlas)

- Python sans dépendance pour le socle ; Tkinter prévu, cohérent avec OotrR.
- Ne pas développer une seconde logique d'accessibilité ni un lecteur mémoire.
- Réutiliser une session existante ; l'intégration événementielle reste à coder.
- Identifiant interne et nom affiché distincts ; aucun nom de check présumé réel.
- Métadonnées v1 avec révision upstream et provenance explicites. La provenance
  déclarée n'est pas une preuve cryptographique d'origine ; l'export réel doit
  être produit localement à partir d'un scan validé.
- Tests synthétiques exclusivement à ce stade. Aucun fichier propriétaire distribué.
- Pas de workflow de build Windows avant application fonctionnelle.
- Phase bornée audit + socle : quota Plus non observable. Vérification utilisateur
  requise avant une nouvelle phase importante, conformément à AGENTS.md.

- Deuxième phase autorisée par « Go » : interface et simulation testées.
- Le mode par défaut est explicitement synthétique ; aucun décor présenté comme
  la vraie forêt. Les noms de démonstration commencent par SIMULATED.
- Packaging Windows de préversion configuré maintenant que l'interface fonctionne ;
  portable en dossier pour réduire la complexité et sans publication de Release.

- Utiliser une grille cotée comme fond du schéma. Une image nécessiterait une
  source utilisable et un alignement vérifié pour chaque ressource.
- Utiliser le scanner de la copie OotrR locale et conserver les IDs du catalogue
  de seed. L'export crée uniquement un nouveau fichier JSON.

Le marquage manuel est limité aux checks sans indicateur de collecte et
l’interface l’identifie séparément. L’application retient les chemins localement
après une première lecture réussie. Un arrêt explicite désactive la reprise.

Le profil mémorise le répertoire choisi et suit le fichier lisible le plus
récent de la seed. Le lecteur mémoire OotrR est proposé en option et reste
en lecture seule. La carte utilise une sauvegarde correspondante comme
base et revient au fichier quand la mémoire ne convient pas.
