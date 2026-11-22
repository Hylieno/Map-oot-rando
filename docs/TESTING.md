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
