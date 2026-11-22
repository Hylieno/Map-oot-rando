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
