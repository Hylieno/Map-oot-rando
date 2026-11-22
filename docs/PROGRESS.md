# Checkpoint — 22 novembre 2026

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
