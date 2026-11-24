# Architecture et audit initial

La barre de navigation mesure l’espace disponible après les commandes
de carte et d’étage. Si les destinations ne tiennent plus, un menu
reprend les mêmes actions. Il passe à la ligne quand la place l’exige.
La barre d’import place le suivi et la mémoire sur une seconde ligne
lorsque leurs commandes dépassent la largeur disponible.

Les entrées des temples de la Forêt, de l’Esprit et de l’Eau utilisent
les points d’apparition des scènes. Le retour du Temple de l’Eau
appartient au lac Hylia dans la scène partagée de la plaine.
Le pont de Kokiri reçoit son repère d’arrivée depuis la scène de la forêt.
Le retour vise l’entrée de Kokiri sur la carte de la plaine.
Les libellés des checks laissent la place aux symboles de passage.
La Caverne de glace possède deux passages distincts vers la Fontaine
Zora. Chaque passage sélectionne son propre repère de retour.

L’import lit la table facultative `MapParam` de la version effective du
NUP. Les coffres et les Skulltulas sont associés à un étage par leur
identifiant d’acteur. Le champ facultatif `dungeon_floor` indique le
numéro du jeu. Le rendu utilise cet étage quand il correspond à un
plan Field Atlas. Les cartes plus anciennes utilisent le numéro de
salle et la hauteur.

Au musée du Monde des rêves, le même acteur fournit les repères
pour le défi et le retour vers le lit de Link. Les passages qui
partagent un point ouvrent le même menu depuis le symbole et le libellé.

Entre le Temple du Temps et la Chambre des Sages, la navigation reprend
le piédestal de l’épée et le point de départ sur la plateforme.

Le diagnostic projette les coordonnées des marqueurs sur les fonds
Field Atlas déjà chargés. Pour les marqueurs proches d’un bord, il examine
le dessin dans un voisinage de quatre pixels. Les coordonnées d’un acteur
et celles de l’entrée affichée figurent séparément.

Les récompenses de dialogue utilisent les acteurs de leur scène pour
placer les marqueurs. Le vendeur Mojo du cratère est repéré dans la
scène enfant par son événement de vente. La collecte suit le même
identifiant OotrR que le catalogue de la seed.

La zone de clic regroupe les marqueurs de checks et de passages
qu’elle touche. Un menu expose chaque action quand le clic est ambigu.
Le symbole et le libellé d’un même passage partagent une action.
Sur la carte de destination, l’anneau d’arrivée reprend l’ancre du
passage de retour dans la vue sélectionnée. Les mains du Colosse et
les passages de Kokiri et des Bois Perdus utilisent les points d’apparition du
jeu quand ils figurent dans les métadonnées. Au Village Goron, l’arrivée
se dessine sur la galerie desservie par le raccourci.

Une recherche utilise les mêmes vues que les marqueurs. La sélection
d’un résultat ajuste le zoom à la vue de destination et centre le
marqueur. Le chargement différé du fond recalcule l’échelle à partir
de son emprise et conserve le marqueur sélectionné au centre.

La découverte des sauvegardes accorde une lecture de plus au fichier
suivi s’il devient temporairement illisible. Le dernier état vérifié
reste visible pendant cette attente. Sans nouvelle lecture valide,
le suivi peut reprendre avec une sauvegarde compatible plus ancienne.

Un réimport de même seed reprend les états des identifiants présents
dans les deux cartes pendant la reconnexion. Le suivi affiche le mode
déconnecté avec la dernière date vérifiée. Une nouvelle lecture par
OotrR remplace cet instantané. Pour le même dossier de sauvegardes,
le dernier fichier vérifié garde son droit à une nouvelle lecture
si l’écriture est en cours. Le choix manuel d’une autre sauvegarde
redémarre avec des états inconnus.

La carte d’Hyrule regroupe les destinations qui partagent le même
repère géographique. Elle calcule la vue de chaque destination à
l’âge sélectionné. Les libellés utilisent les espaces disponibles
autour des repères et les repères restent cliquables quelle que
soit la place disponible pour leur libellé.

Une carte importée peut conserver plusieurs régions dans le champ facultatif
`regions` du format v1. La ressource Banc détermine le repère d’une position.
Un check sans position garde la zone de son catalogue. Un même ID peut avoir une
position dans deux régions, comme le coffre du pont, et garde un état unique
dans le tracker. La navigation par entrée conserve l’âge et chaque vue
calcule son cadrage dans ses propres coordonnées.
Quand le scan OotrR ne fournit aucune position pour un check dans une
variante de scène, l’import peut retrouver son acteur par son dossier
Banc, son identifiant numérique et son type. Cette recherche couvre
toutes les zones prises en charge.

La **Carte d’Hyrule** s’ouvre au dézoom et place toutes les zones disponibles
sur une illustration à l’aide de coordonnées normalisées. Les passages locaux
utilisent leurs coordonnées de scène. Le sélecteur de zone, les boutons d’âge
et le sélecteur d’étage manipulent la même vue.
Le marqueur de Link lit les coordonnées et la scène sur la connexion mémoire
OotrR après validation du marqueur de seed. Le lecteur de position réutilise
l’adresse de module relocalisée par OotrR et vérifie les structures avant de
publier la pose. Une lecture de position indisponible masque le marqueur.
La navigation suivie réagit aux transitions de scène, d’âge et de
vue calculée. Une brève interruption de la position garde la vue
choisie et reprend le suivi à la prochaine transition.
Le Temple du Temps utilise les limites de la zone `TimeTemple` propres
à chaque âge dans la scène de la Citadelle. La Chambre des Sages utilise
sa ressource distincte et un seul plan aux deux âges.
Le Monde des rêves distingue le musée et la salle intermédiaire par
le nom de la ressource active. Les coffres du défi conservent leurs
identifiants individuels quand ils partagent les mêmes coordonnées.
Le Château d’Hyrule utilise la scène enfant. Les abords et la cour
partagent les coordonnées natives, avec une vue distincte pour la cour
située au-delà du plan publié. Le marqueur peut suivre ce passage.
Au Château de Ganon, les abords et l’effondrement ont deux repères
distincts. Le lecteur de position conserve le nom de la ressource
de scène pour les différencier dans le même dossier Banc.
À l’intérieur, le champ facultatif `level_points` d’une scène associe
chaque repère de la tour à un niveau. Les coordonnées X/Z se superposent
entre étages. Le coffre de clé utilise son numéro de salle et le suivi
de Link utilise la hauteur dans l’emprise de la tour.
Le passage adulte entre le moulin et la tombe de Dampé utilise les
événements de scène et leurs points d’arrivée natifs. Le regroupement
place les repères côté cimetière dans la vue souterraine que le suivi
de Link choisit à partir de sa hauteur.
Le champ facultatif `entrance` indique où accéder à un check souterrain
sur une carte de surface. Le rendu projette cet accès et les détails
conservent la position XYZ de l’acteur.
Le pont côté plaine est une vue de la scène Kokiri, sélectionnée
d’après les coordonnées de l’acteur ou de Link. La copie du coffre
dans les Bois Perdus reste dans le repère de cette scène.
Le centre d’entraînement Gerudo trace ses liaisons entre les centres
de salle et les portes natives. La passerelle garde sa vue distincte.
En Vallée Gerudo, les scènes des deux âges utilisent le même fond et le
même repère. Chaque entrée de grotte est résolue dans la scène de l’âge
du check.
À la Forteresse Gerudo, plusieurs coordonnées peuvent représenter le même
événement dans une seule scène. La carte Gerudo partage un ID de suivi à
tous ses points de remise.
Le Centre d’entraînement réutilise les repères par niveau pour séparer
les deux hauteurs du labyrinthe. Le numéro de salle de l’acteur et sa
hauteur déterminent la vue des checks. Le suivi de Link utilise sa
hauteur dans le périmètre du labyrinthe.
Le champ facultatif `routes` conserve les chemins X/Z associés à la
scène. Le Désert hanté projette la trajectoire du guide depuis les
segments de Bézier de la scène. Le cadrage inclut toute la courbe.
Au Colosse du désert, le fond et le repère X/Z sont communs aux deux
âges. Le passage conserve l’âge lors de la navigation.
Au Temple de l’Esprit, les passages latéraux ciblent un étage précis.
Les coffres des mains appartiennent au catalogue du temple et utilisent
leurs coordonnées dans la scène extérieure du Colosse.
Le lac Hylia conserve les ressources Banc de la plaine. Le rendu et
le suivi de Link utilisent la même limite X/Z pour choisir la vue
locale. Les libellés natifs du portail principal distinguent les
deux sens de navigation aux abords de cette limite.
Au Temple de l’Eau, le numéro de salle détermine le plan des checks.
Le suivi de Link utilise la hauteur et le périmètre des zones qui
chevauchent plusieurs étages. Le bassin de Morpha et son couloir figurent
avec les galeries basses. À l’est, la plateforme suit l’étage défini
par le coffre de la salle dans les données du jeu.
Le ranch Lon Lon réutilise la sélection de vue locale dans la scène
de la plaine. Un périmètre X/Z couvre la cour, l’enclos et les ruines.
Dans les zones Zora, à la Caverne de glace et au Temple du Feu, les identifiants typés du catalogue
peuvent compléter le scan par correspondance du hash et du type d’acteur
dans chaque scène, sans écraser un placement déjà produit pour cette vue.
Les ressources `Adult_Alternative` de Cocorico ont une vue adulte distincte.
Le suivi réutilise le snapshot accepté par OotrR et le manifest pour lire la
condition de scène. Les checks partagés gardent le même ID de suivi.
Au cimetière, le champ local `underground` distingue les placements fiables
sous la surface. Les deux niveaux gardent la même source Banc et le même
repère X/Z. L’âge reste indépendant du niveau.
Au Village Goron, les vues par étage déduisent le niveau de la hauteur Y
de chaque placement. Les étages principaux partagent le repère X/Z du
fond Field Atlas. L’ID et les coordonnées XYZ d’origine restent disponibles.
La caverne Dodongo utilise des ressources communes aux deux âges. Le menu
d’étage est partagé avec le Village Goron. Le dernier âge connu reste
disponible quand l’utilisateur rejoint une zone extérieure. La Caverne de
glace utilise ce même principe avec une seule vue.
Dans les donjons où le numéro de salle détermine le niveau, le champ facultatif `dungeon_room` conserve le numéro de
salle trouvé dans les données du jeu. L’attribution à un étage privilégie
la salle, car des acteurs suspendus peuvent dépasser la hauteur de leur étage.
Le Temple du Feu réutilise ce sélecteur. Ses cinq images sont des recadrages
d’une même projection orthographique. Les marqueurs reprennent les placements
du scan OotrR, avec résolution par type et identifiant d’acteur pour les
checks du catalogue restés sans position. La catégorie du cœur de boss
permet de le placer dans l’arène même à la hauteur du rez-de-chaussée.

Référence inspectée : Mozencaz/OotrR,
`283d3ec0f161d32e168afac45e502442c1ffb081`.
Le dépôt Map-oot-rando ne contenait initialement que AGENTS.md ; branche distante
main à `82860e51ae1bafadf71f205a5868993826e89e7b`.

## Résultats de lecture

- Licence racine OotrR MIT, copyright 2026 Mozencaz. Les données de logique
  dérivées d'Archipelago possèdent leur propre notice MIT. Aucun code upstream
  ni actif de jeu copié dans ce checkpoint. Toute distribution future de ces
  composants doit conserver leurs notices.
- `game/extra_sources.py:scan_world` appelle `remake_world.scan_maps`, collecte
  les sources, puis `check_names.label_entries`. Les variantes contiennent
  `position` (champ `Translate` des acteurs), `resource`, `index`, `label`.
- `check_names.label_entries` nomme les checks sur le scan complet, avec zone,
  lieu, catégorie et index ordonné X/Z/Y/identifiant. Ne pas recalculer les
  noms après filtrage à Kokiri Forest. `KF_rock_1` est un exemple non confirmé.
  L'identifiant interne avec hash est distinct du label lisible.
- `randomizer/full_randomizer.py` conserve dans les placements les couples
  resource/index ; `check_name` peut préférer le nom AP au label. Les chemins
  inspectés ne sérialisent pas les positions dans les placements et
  `tracking_metadata.build_tracking` ne les inclut pas dans tracking.json.
  Un export de métadonnées depuis le scan est donc nécessaire.
- `game/world_maps.py` est un adaptateur de génération/patch de récompenses,
  pas un moteur de rendu cartographique ; ne pas l'exécuter pour afficher la carte.
- `tracker/auto_tracker.TrackerSession` possède `check_state(id)` et `refresh()`.
  Il valide le marqueur de seed, lit la sauvegarde, fusionne éventuellement la
  mémoire, calcule l'accessibilité avec la logique de seed et vérifie son empreinte.
  Les échecs conservent le dernier état ; un changement de seed/slot exige reset.
- `tracker/live_memory.LiveGameData.snapshot` lit les bools et bool64 du processus.
  Le module contient aussi des fonctions d'écriture pour d'autres usages :
  elles sont exclues du compagnon. Ne pas importer/démarrer une deuxième session.
- `gui/randomizer_gui` utilise Tkinter ; `tracker_tick` relance toutes les secondes
  un worker de refresh, avec garde contre les lectures concurrentes et retour
  par file d'événements `tracker-update`. Point d'intégration envisagé : publier
  après cette mise à jour vers une fenêtre de carte partageant la même session.
- Dépendances upstream lues : zstandard, evfl, ainb, websockets, Pillow,
  texture2ddecoder. Aucune installée ou exécutée pour cet audit.

## Socle réalisé

`model.py` : variantes par paire identifiant/ressource, coordonnées 3D conservées,
projection brute X/Z, recherche et filtres indépendants du rendu.
`metadata.py` : export versionné des résultats du scan, validation stricte,
diagnostics des positions absentes. Aucune déduction de position.
`state.py` : adaptation passive de check_state, snapshots complets, reset explicite,
déconnexion conservant état et date, séparation simulation/données réelles.

Les appels `check_state` doivent être sérialisés avec le refresh par le propriétaire
pour constituer un lot cohérent. Le propriétaire doit fournir explicitement le
mode de connexion et l'heure : le résumé upstream est textuel et n'est pas un
contrat fiable pour inférer une connexion live. Ce branchement reste à développer.

Les ressources sont conservées séparément pour ne pas superposer aveuglément
intérieurs et variantes d'âge. La correspondance âge/étage et la transformation
visuelle (origine, échelle, orientation) restent à vérifier sur les données réelles.
Les sources d'événements sans position ne sont pas inventées ; leur diagnostic
exhaustif devra être complété par jointure avec le catalogue checks.json de seed.

## Interface du deuxième checkpoint

`gui.MapApplication` charge les métadonnées, affiche une seule ressource à la fois,
et propose une liste recherchable sur toutes les ressources. `view.Viewport` isole
les calculs de pan/zoom/cadrage. Une position absente reste dans la liste.
`simulation.Simulation` possède un StateStore distinct et ne démarre aucun lecteur.
Les événements simulés publient directement, puis provoquent le redraw Tk ; aucune
réouverture de fenêtre requise. Les changements simulés pendant une déconnexion
sont retenus jusqu'à la reconnexion. Importer d'autres métadonnées crée un état neuf.
Le jeu réel n'est toujours pas branché. Aucune inférence de règles ou d'étages.

## Export local

`python -m map_oot_rando.export` utilise le scanner de la révision OotrR épinglée.
Le catalogue fixe l'ID et le nom affiché. Le label du scan sert aussi à la recherche.
Pour les anciens coffres, la correspondance prend le hash du coffre dans Kokiri
Forest. Les autres checks sans correspondance restent dans la liste sans marqueur.
Le fond est une grille X/Z construite dans le même repère que les marqueurs.

### Alignement local du fond

Le réglage global établit le repère X/Z. Des correspondances nommées entre
des éléments du dessin et des coordonnées du catalogue corrigent ensuite
le raster dans un voisinage limité. Le rayon de correction protège les
autres repères et la borne de déformation évite les plis. Les positions de
jeu et la projection des checks restent fixes. Les fonds sans repère local
vérifié utilisent l’alignement global. Le moteur de correction n’est pas
spécifique à Kokiri, mais chaque dessin doit fournir des correspondances
utilisables ou des coordonnées déjà alignées.

### Projection contrôlée et source du fond

Le fond principal de Kokiri est l’image du menu de jeu publiée par
[Questfern](https://questfern.com/oot/guides/interactive-map/?area=kokiri). Son empreinte
fixe le lien entre les pixels de contrôle et la version du fond. Une seule
transformation globale est utilisée après contrôle des erreurs résiduelles,
détection des projections déformées et prédiction des repères laissés de côté.
La boutique est un repère indépendant lorsqu’elle est disponible.
Pour les captures qui fournissent déjà leur matrice de projection, l’import de
fichiers world utilise les coordonnées X/Z directement. Aucun ajustement
artistique n’est appliqué aux checks.

Les tables de capture publiées par
[Hyrule Tracker](https://github.com/jv-prado/hyrule-tracker/blob/5aa4239bf2801ff287713e0a1f77bdc7d6b5445b/src/core/position.ts)
ont été comparées sur le SVG Field Atlas. Elles donnaient des écarts plus
grands sur les maisons et sortaient deux placements supplémentaires du fond
pour la seed testée. Le scanner recherche aussi les noms de ressources
MapCapture et MapMenu dans le NUP local pour l’étude des projections natives.
La découverte de noms ne suffit pas à valider une texture ou sa projection.

### Profils locaux et marquage manuel

Les chemins sont mémorisés localement par identifiant de seed après validation
par OotrR. Le JSON de carte ne contient aucun chemin de sauvegarde. Les marques
manuelles utilisent le stockage OotrR, isolé par seed et chemin de sauvegarde.
Les actions arrivent au même worker que le rafraîchissement et sont validées
contre la dernière lecture avant toute écriture de marque.

### Mémoire et répertoire de sauvegardes

Un worker sérialisé possède une seule session OotrR et ferme son lecteur à
l’arrêt ou au changement de carte. Le lecteur mémoire est activé explicitement.
Le sélecteur classe les progress.sav par date et vérifie le marqueur de seed.
Il conserve les résultats de validation tant que les fichiers sont inchangés.
La session OotrR valide de nouveau le fichier et la mémoire avant de publier.
