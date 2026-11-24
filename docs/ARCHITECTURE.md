# Architecture et audit initial

Une carte importée peut conserver plusieurs régions dans le champ facultatif
`regions` du format v1. La ressource Banc détermine le repère d’une position.
Un check sans position garde la zone de son catalogue. Un même ID peut avoir une
position dans deux régions, comme le coffre du pont, et garde un état unique
dans le tracker. La navigation par entrée conserve l’âge et chaque vue
calcule son cadrage dans ses propres coordonnées.

La **Carte d’Hyrule** s’ouvre au dézoom et place toutes les zones disponibles
sur une illustration à l’aide de coordonnées normalisées. Les passages locaux
utilisent leurs coordonnées de scène. Le sélecteur de zone, les boutons d’âge
et le sélecteur d’étage manipulent la même vue.
Le marqueur de Link lit les coordonnées et la scène sur la connexion mémoire
OotrR après validation du marqueur de seed. Le lecteur de position réutilise
l’adresse de module relocalisée par OotrR et vérifie les structures avant de
publier la pose. Une lecture de position indisponible masque le marqueur.
La navigation suivie réagit aux transitions de scène ou d’âge.
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
Le champ facultatif `entrance` indique où accéder à un check souterrain
sur une carte de surface. Le rendu projette cet accès et les détails
conservent la position XYZ de l’acteur.
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
