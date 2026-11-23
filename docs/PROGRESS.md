# Checkpoint — 22 novembre 2026

La caverne Dodongo est reliée au mont du Péril. Les deux fonds Field Atlas
sont alignés indépendamment. L’arène présente deux checks avec leurs
coordonnées d’acteur et leurs IDs de suivi. Les étages sont communs aux
deux âges. Le retour au mont du Péril reprend le dernier âge choisi ou suivi.

Le Village Goron est relié au mont du Péril. Le fond est vérifié pour les
deux âges. Les quatre étages et la grotte séparent les checks selon leurs
coordonnées. La vue conserve l’étage lors d’un changement d’âge si cet
étage est disponible. Les deux checks des Gorons roulants restent à
associer à un emplacement vérifié.

Le mont du Péril est relié à Cocorico. Les vues enfant et adulte utilisent
un fond Field Atlas validé. Les six rupees enfouies de la seed de référence
appartiennent à la vue souterraine. Chaque mise à jour du code lance les tests Windows et
seuls les jalons marqués `[preview]` déclenchent aussi un build.

Le cimetière est accessible depuis Cocorico. Field Atlas fournit le fond
de surface. Les checks en sous-sol ont une vue schématique par âge.
Les intérieurs de tombe et la course de Dampé restent à dessiner.

Cocorico est relié à la plaine. Ses fonds enfant et adulte de Field Atlas
s’alignent automatiquement. Le suivi bascule vers la variante après
l’incendie quand les données de la seed et de la partie confirment la
condition utilisée par OotrR. La validation en jeu reste à faire.

La plaine d’Hyrule est accessible depuis Kokiri et utilise la carte Questfern.
La vue des zones voisines s’ouvre au dézoom. Le fond est vérifié par âge et
utilise un repère indépendant. Certains checks sont physiquement dans les
sous-zones du Ranch ou du Lac, qui restent à représenter séparément.

Le Bosquet sacré est accessible depuis les Bois Perdus. Son fond Questfern
est calibré avec des repères physiques et le marqueur de chaque coffre
souterrain pointe vers l’entrée de sa grotte.

Le cache local réutilise les fonds Questfern vérifiés après le premier
téléchargement. Dans les Bois Perdus, les deux checks du Théâtre Mojo pointent
vers la même entrée pour l’âge enfant. Le menu des points superposés permet
de choisir les deux checks avec la souris.

Le suivi de Kokiri a été confirmé par l’utilisateur sur son build. L’import
couvre désormais aussi les Bois Perdus. Le coffre partagé conserve un état
unique et les cinq checks d’événements associés à des acteurs identifiables
utilisent leurs positions dans les Bancs. Le cadeau de Saria reste dans la
liste en attendant une représentation vérifiée.
Le schéma sans icônes est disponible. Une vue aérienne détaillée et la
navigation continue entre zones à la molette restent à valider.

Branche : `dev/kokiri-foundation`.
Upstream : `283d3ec0f161d32e168afac45e502442c1ffb081`.

Terminé : lecture intégrale AGENTS.md, inspection des branches, audit initial des
sept modules prioritaires, licence MIT vérifiée, socle métadonnées/projection/
recherche/filtres et états passifs codé. Huit tests synthétiques passent.

Fichiers ajoutés : README.md, .gitignore, map_oot_rando/{__init__,model,metadata,state}.py,
tests/test_foundation.py et les quatre documents docs demandés. AGENTS.md inchangé.

Limites : aucun NUP disponible, aucune coordonnée réelle vérifiée. Aucun écran,
aucune synchronisation réelle, aucun mode simulation interactif, aucun exécutable.
L'audit initial identifie les points d'intégration mais ne constitue pas une revue
exhaustive du code upstream. Le premier jalon Kokiri Forest n'est pas terminé.

Difficultés identifiées : nom lisible distinct de l'ID ; coordonnées non conservées
par les chemins de sérialisation inspectés ; résumé de connexion upstream textuel ;
nécessité de publier les états sans concurrence avec refresh.

## Reprise

Après vérification du quota court terme et hebdomadaire :
1. Compléter un export local read-only depuis scan_world et joindre checks.json.
2. Ajouter une fenêtre Tkinter : ressources séparées, pan/zoom, sélection/recherche,
   filtres, détails et simulation clairement identifiée.
3. Brancher la publication au propriétaire de TrackerSession après tracker-update,
   sans second lecteur ; formaliser mode de connexion et reset de sauvegarde.
4. Vérifier coordonnées réelles et événements, puis configurer build Windows x64.

Prompt de reprise : « Lis AGENTS.md et docs/PROGRESS.md sur dev/kokiri-foundation.
Le quota permet une nouvelle phase bornée. Continue l'export et la carte Tkinter
Kokiri Forest sans inventer de coordonnées ou de nomenclature de checks. »

# Deuxième checkpoint — interface et simulation

Autorisation : « Go ». PR : https://github.com/Hylieno/Map-oot-rando/pull/1

Ajoutés : gui.py, __main__.py, view.py, simulation.py, tests/test_gui.py,
tests/test_view.py, packaging/launcher.py, .github/workflows/windows.yml.
README et les quatre documents de continuité mis à jour. AGENTS.md inchangé.

Fonctionnel : carte Tkinter, zoom/pan/cadrage, recherche globale et sélection,
détails XYZ, séparation par ressource, filtres, simulation des quatre états et
déconnexion/reconnexion. Import JSON versionné ; aucune coordonnée inventée dans
les données réelles. Les exemples sont explicitement fictifs.

Validation : 14 tests passent, dont 3 tests Tk réellement exécutés ; contrôle
visuel de sélection/recoloration effectué. Le cadrage initial a été corrigé.
Workflow de préversion Windows x64 ajouté ; exécutable pas encore validé sur Windows.

Restent : extraction réelle locale et jointure avec catalogue de seed, intégration
événementielle de TrackerSession sans lecteur concurrent, diagnostic exhaustif des
checks sans position, correspondance âge/étage et validation réelle de Kokiri Forest.
Ce jalon n'est donc toujours pas terminé. Aucune autre zone développée.

Reprise : vérifier le quota puis continuer sur cette branche avec l'export local
read-only et l'intégration au propriétaire de TrackerSession. Examiner d'abord le
résultat du workflow Windows de la PR pour éviter une compilation redondante.

CI Windows confirmée réussie après ce checkpoint :
https://github.com/Hylieno/Map-oot-rando/actions/runs/45064230917
Artifact : https://github.com/Hylieno/Map-oot-rando/actions/runs/45064230917/artifacts/14770488765
Tests Tk Windows et build réussis ; exécutable packagé non lancé manuellement.

# Troisième checkpoint

La grille X/Z suit le zoom et le déplacement. Le nouvel export CLI appelle le
scanner OotrR local, joint le catalogue et produit un JSON lisible dans la carte.
Les checks sans correspondance restent recherchables et sont signalés par l'export.
La validation locale utilise des données synthétiques. L'essai sur NUP et seed
réels et le raccordement des événements TrackerSession restent à faire.
La branche et la PR #1 restent les points de reprise.

Fichiers principaux : export.py, metadata.py, model.py, view.py, gui.py,
tests/test_export.py et tests/test_view.py. La documentation des cinq fichiers
de continuité a été actualisée.

# Import depuis la version portable Windows

Le bouton d’import lit un NUP et un catalogue OotrR locaux en arrière-plan,
puis affiche la carte. Un bouton permet d’enregistrer le JSON pour le rouvrir
sans refaire le scan. Le build embarque le scanner OotrR épinglé et sa licence.
Un test Tk simule le parcours et le workflow vérifie le scanner compilé avec
un fichier invalide. La validation avec les fichiers réels reste à faire.

Le retour du premier import réel a révélé plusieurs placements d’un même check
dans une même ressource. Le modèle conserve les positions distinctes et rassemble
les entrées identiques à l’affichage. Chaque placement partage l’identifiant et
l’état du check. La liste indique les coordonnées pour choisir une variante.

Le fond de Kokiri Forest utilise maintenant les repères calculés par OotrR à
partir du scan local. Les volumes de pièces sont dessinés en rectangles et les
repères ponctuels en losanges. Les checks restent au premier plan et la carte
limite la superposition des libellés. Les anciens JSON restent lisibles avec
la grille. Un nouvel import est requis pour y ajouter les repères.

Le bouton « Ajouter une vue aérienne… » permet d’aligner une image locale vue
de dessus sur trois repères relevés dans le jeu. Le fond et les checks partagent
le zoom et le déplacement. Le JSON conserve l’image et son alignement par
ressource. Une image de référence reste nécessaire pour valider la vue Kokiri.

Le fond Kokiri publié par Field Atlas est proposé depuis sa source sur demande.
L’image SVG reste hébergée par Field Atlas. La carte utilise le calibrage à
trois points et conserve le fond dans le JSON local à l’enregistrement.

Le chargement de Field Atlas aligne désormais le dessin sur au moins quatre
maisons présentes dans la vue. Les centres dessinés sont des repères visuels
et l’ajustement affine est contrôlé sur toutes les maisons appariées. Si les
repères manquent ou divergent, le fond actuel est conservé.

Les couches Static et Dynamic sont réunies dans les vues Enfant et Adulte. Le
fond Field Atlas se charge en arrière-plan à l’ouverture d’une vue sans fond
enregistré. Les checks hors du dessin restent dans la liste et leurs
coordonnées d’origine sont préservées.

La carte lit maintenant progress.sav via TrackerSession et actualise les
statuts au fil des sauvegardes. Le lecteur mémoire reste désactivé. La jointure
prend aussi en charge les anciens IDs avec hash d’acteur et champ de patch.
Le rapport de diagnostic permet de transmettre les coordonnées sans fichier
du jeu, sauvegarde ou image. Validation sur les données de la seed réelle
toujours requise avant de déclarer le prototype final.

Le diagnostic réel a révélé que certains noms de maisons sont décalés par
le classement des pièces dans la vue Enfant. L’alignement utilise les repères
Adulte si les trois entrées communes confirment les mêmes coordonnées.
OotrR est épinglé sur le tag v0.8.0 (générateur 0.12.8) pour correspondre à
la seed testée. Les anciens exports de coordonnées restent compatibles.

Un deuxième niveau de calibrage corrige localement le fond Field Atlas
quand une correspondance fiable existe. Il est vérifié sur le coffre de
l’épée de la seed fournie et sur des tests génériques à plusieurs repères.
Les anciens fonds Field Atlas enregistrés se recalibrent à l’ouverture.

Atlas principal changé vers le fond Kokiri du menu de jeu publié par
Questfern. Projection validée avec la seed réelle et des repères exclus du
calcul. Les backgrounds déjà géoréférencés s’ouvrent par world file.

Le parchemin reste droit et se fond dans le fond uni au dézoom. Les checks
inconnus sont violets, avec un contour clair et un libellé contrasté. La
projection sélectionne le modèle qui prédit le mieux les repères omis.

Le suivi se reconnecte à la réouverture de la seed, sauf après arrêt explicite.
Les checks sans indicateur peuvent être marqués et décochés dans leurs détails.
La collecte réelle en jeu et la synchronisation mémoire restent à valider.

La vue Enfant ou Adulte suit désormais le drapeau d’âge de la sauvegarde,
lorsqu’il est présent. Le choix manuel d’une vue suspend ce suivi.

Le suivi choisit le dernier progress.sav valide dans le dossier sélectionné.
Le mode mémoire utilise maintenant LiveGameData et TrackerSession d’OotrR,
avec repli sur la sauvegarde. Le test avec un jeu réellement lancé reste à faire.
