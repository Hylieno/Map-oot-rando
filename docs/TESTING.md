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

Le fond de carte est testé avec des repères synthétiques. Le test couvre la
projection X/Z et la séparation des variantes enfant et adulte. Le test Tk
vérifie l’ordre du fond et des checks ainsi que le changement de ressource.
Le rendu avec un NUP réel reste à confirmer.

La vue aérienne est testée sur une image synthétique. La couverture vérifie la
rotation, le rejet des trois repères alignés, la sauvegarde et la relecture,
le zoom et le déplacement, et le rendu Tk sous les checks pour la bonne ressource.

Les 24 tests et le build Windows passent dans
[GitHub Actions](https://github.com/Hylieno/Map-oot-rando/actions/runs/45068828832).

Le téléchargement et le rendu du fond publié par Field Atlas ont été vérifiés
sous Linux avec le fichier du site. Les tests automatisés rendent un SVG
synthétique hors ligne et vérifient le rejet d’un fichier dont l’empreinte diffère.
L’alignement avec une seed réelle reste à contrôler.

Les 26 tests et le build passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45069291402).

L’alignement automatique est testé avec les positions approximatives lues sur
la capture de la vue adulte. Ce montage vérifie aussi les refus pour manque de
repères ou incohérence. Le rendu final sur le NUP de l’utilisateur reste à vérifier.
Les 27 tests et le build passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45069636229).

La suite vérifie la fusion des couches, le masquage des checks hors du fond
et le chargement automatique du fond via un SVG synthétique. Le test de suivi
fait décoder des sauvegardes binaires synthétiques par le TrackerSession OotrR
épinglé. Il vérifie un déblocage par inventaire, la collecte, la restauration
d’une sauvegarde antérieure, une interruption et le refus d’une autre seed.

Les 32 tests, y compris le suivi OotrR sur sauvegarde synthétique, passent
sur Windows. L’exécutable compilé charge aussi le moteur et le monde de
logique épinglés. [Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45091882761)

L’alignement vérifie la géométrie des vues enfant et adulte à partir de repères
approximatifs lus sur les captures. Il accepte un repère isolé incohérent si
quatre autres concordent, et refuse des repères insuffisants ou incompatibles.
Cette reproduction reste distincte d’une validation avec le diagnostic exact.

Avec les métadonnées d’une seed complète créée par OotrR 0.8.0, le fond se
calibre pour les deux âges. Les 89 IDs du catalogue Kokiri ont des coordonnées,
ainsi qu’un coffre partagé avec Lost Woods. Quatre placements (deux par âge)
sont hors du périmètre du dessin et restent consultables. Le moteur épinglé
reconnaît la signature de logique et les indicateurs des 86 checks suivables
sur ces 90 IDs. Les indicateurs ont été vérifiés avec des sauvegardes binaires
synthétiques et les métadonnées réelles. Le ROMFS, le jeu et la sauvegarde réelle
n’ont pas été utilisés dans ce test.

Les 34 tests et le build portable avec OotrR 0.8.0 réussissent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45093625991).

Le moteur de correction locale a été vérifié avec deux repères séparés et
un repère protégé. Les écarts qui nécessitent une déformation excessive
sont refusés. Sur le fond original et les deux vues de la seed fournie,
la distance image entre le marqueur du coffre de l’épée et le centre de
l’enclos passe de 31,4 à 1,3 pixels à la résolution 1 800 × 996. Cette mesure
compare le centre du marqueur et le motif reconnu dans le raster.
Les 105 placements couverts et les quatre hors du dessin restent identiques.

Sur l’image Questfern 1 400 × 709 et la seed réelle déjà fournie, les six
repères de la projection ont un résidu maximal de 6,0 pixels dans les deux
vues. En retirant chacun à tour de rôle, le plus grand écart est de 16,1 pixels.
La boutique, exclue du calcul, est à 12,3 pixels. Les 105 placements couverts
restent identiques. Reste à vérifier le jeu en direct et les secteurs sans
repère indépendant. Les tests synthétiques couvrent l’amorçage du fond préféré,
le rejet d’un repère indépendant incohérent et la projection d’un world file.

Les 40 tests et le build portable passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45095727521).

La comparaison sur la seed réelle privilégie une projection à échelle unique et
sans cisaillement. L’écart quadratique moyen des repères retirés et de la
boutique indépendante passe de 9,7 à 8,3 pixels. La boutique seule passe de 12,3
à 15,0 pixels. Il s’agit d’un meilleur compromis global, avec les mêmes
105 placements couverts. Les tests vérifient aussi les bords du parchemin et
le centrage d’un marqueur dans le repère de l’image.

Les 43 tests et le build portable passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45096561485).
