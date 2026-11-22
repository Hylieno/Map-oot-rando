# Validation

Commande exécutée sous Linux avec Python :
`python -m unittest discover -s tests -v` — **8 tests réussis**.

Couverture : identifiant/label, projection X/Z et conservation Y, coordonnées
invalides/non finies, version et provenance, doublons, variantes par ressource,
positions manquantes, recherche insensible à la casse, catégories et statuts,
adaptation des états upstream par doublure, priorité completed, états inconnus,
snapshots, déconnexion/reconnexion, rollback, changement de seed et isolation
simulation/réel. Aucune dépendance upstream exécutée.

Non testé : scanner sur NUP réel, noms et positions réels, sauvegarde réelle,
mémoire du jeu, événements de l'interface OotrR, rendu graphique et Windows.
Les coordonnées (10,20,-30) du test sont fictives et explicitement synthétiques.

À ajouter : intégration avec la révision OotrR épinglée, catalogue de seed,
changement de sauvegarde dans l'adaptateur événementiel, interactions Tkinter,
validation réelle des axes/ressources et packaging Windows x64.

## Deuxième checkpoint

14 tests réussis sous Linux, dont 3 tests d'intégration Tk exécutés sur le bureau
partagé avec Python 3.12/Tk 9. Les tentatives initiales sans accès à l'écran ont
ignoré ces 3 tests ; la suite finale les a effectivement exécutés.

Ajouts : zoom ancré, cadrage et point dégénéré, simulation déconnectée/reconnectée,
recherche/sélection inter-ressources, recoloration immédiate du canvas, masquage des
récupérés, affichage des coordonnées absentes et isolation lors de l'import.
Un défaut de cadrage avant le premier Configure a été reproduit visuellement,
corrigé et couvert par assertion sur l'étendue des marqueurs après démarrage.

Contrôle manuel sur bureau Linux : lancement, cadrage, sélection d'un marqueur
et passage du vert au gris via « Récupéré », avec détails et horodatage mis à jour.
Workflow Windows configuré ; résultat à vérifier dans GitHub Actions. Pas de test
avec le vrai jeu ou de validation d'exécutable Windows à ce checkpoint.

Résultat CI confirmé : Windows portable preview, run 45064230917, commit
6928125049cc0941fda9599f06eb0578487e67a2 : tests Tk obligatoires, compilation
PyInstaller et upload tous réussis. Artifact 14770488765, 11 660 575 octets.
L'exécutable produit n'a pas été lancé manuellement : les tests exécutent les
sources sous Windows, puis le packaging est vérifié par le succès du build.

## Troisième checkpoint

14 tests passent localement sur 17 découverts. Les trois tests Tk sont ignorés
dans l'environnement sans écran. Les ajouts couvrent la jointure catalogue,
la recherche par alias, les checks sans position, le lancement de l'export CLI
avec scanner simulé, la protection contre l'écrasement et le repère de la grille.
L'appel au scanner avec un NUP réel reste à tester.

Les 17 tests, dont ceux de Tkinter, et la compilation portable réussissent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45065577348).

Le parcours d’import Tk utilise un résultat synthétique. Le workflow Windows
lance aussi l’exécutable compilé et vérifie que le parseur OotrR embarqué
rejette un fichier de test invalide. Aucun NUP réel utilisé.

Les 18 tests et le lancement du scanner compilé réussissent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45066737154).

Régression d’import reproduite avec deux positions distinctes pour le même
check dans la même ressource. Le test couvre l’export, la jointure au catalogue,
la relecture JSON, la projection et le statut partagé. La nouvelle version
reste à essayer avec le NUP qui a déclenché le signalement.

Les 19 tests et la vérification de l’exécutable compilé passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45067415834).
