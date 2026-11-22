# Architecture et audit initial

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
