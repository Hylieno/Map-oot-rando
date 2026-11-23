# Validation

Les deux scènes publiques du Temple de la Forêt contiennent les 25 checks
du catalogue. Les 23 marqueurs hors arène tombent sur les plans ou à un
pixel du dessin, sur des fonds de 700 pixels de large. Le test d’étage
couvre la vigne de l’entrée, le balcon de la cour, la salle tournante,
l’arène et le coffre de la clé du boss. Le scan du NUP complet reste à
contrôler pour le donjon.

Les deux scènes publiques de l’Arbre Mojo ont permis de positionner les
25 checks du catalogue. Les 19 marqueurs hors arène tombent sur le dessin
ou à moins de quatre pixels du contour pour des fonds de 700 pixels de
large. Les six checks de la salle 10 sont affichés dans l’arène. Les tests
vérifient l’usage du numéro de salle, la navigation depuis Kokiri et
l’affichage du plan du hall sans check. Le scan du NUP complet reste à
contrôler pour ce donjon.

Les deux scènes publiques de Jabu-Jabu contiennent les 21 checks du
catalogue de référence. Le recoupement place 2 checks au rez-de-chaussée,
7 au sous-sol, 4 à l’étage et 8 dans l’arène. Hors arène, 12 marqueurs
tombent sur le dessin de leur étage. Le coffre de la carte est à 17 pixels
du contour sur le fond du sous-sol de 700 pixels de large. Ses coordonnées
et son numéro de salle sont conservés. Les tests couvrent la réouverture
des métadonnées et le passage depuis la Fontaine enfant.

La Caverne de glace a été recoupée avec les deux scènes publiques et les
14 IDs du catalogue. Tous les placements sont dans le fond Field Atlas.
Sur l’image de 650 pixels de large, 13 marqueurs tombent sur le dessin
et le coffre de la salle 8 en est à 3 pixels. Le test Tk vérifie la vue
unique et le passage par la Fontaine adulte.


À la Fontaine Zora, les quatre ressources publiques et le catalogue
donnent 29 checks positionnés, avec 9 emplacements enfant et 22 adulte.
Chaque fond inclut l’entrée du Domaine. Le test d’alignement vérifie
la différence d’origine entre les deux fonds, et la navigation Tk
vérifie l’aller-retour entre la Fontaine et le Domaine. Les données
du NUP complet restent à contrôler pour les zones Zora.

Le Domaine Zora a été recoupé avec six ressources publiques et les 26 IDs
du catalogue. La boutique utilise les positions de rayon renvoyées par
OotrR. Le point de plongeon et le roi fournissent les deux repères
d’événement. Les deux variantes adultes partagent les mêmes passages.
Le test synthétique conserve un placement distinct tout en regroupant les
doublons des deux scènes adultes.

La rivière Zora a été recoupée sur les quatre scènes publiques du jeu.
Les 54 identifiants du catalogue sont positionnés dans le fond Field Atlas,
avec 40 placements enfant et 39 adulte. Dans chaque vue, le coffre et les
trois pots enterrés apparaissent à l’entrée de leur grotte. Les tests
vérifient les deux entrées du coffre, le point des grenouilles côté enfant
et le passage avec la plaine. Le scan du NUP complet reste à valider pour
cette zone.

Les tests Tk couvrent le dézoom vers la carte générale, la navigation par âge,
les raccourcis des Bois Perdus dans les deux sens et le suivi de Link avec ou
sans changement automatique de zone. Les tests du lecteur de Link couvrent
une image mémoire synthétique relocalisée, une transition sans changement
des flags de check, une structure inconnue et une seed différente.
Les projections Field Atlas de la plaine, du Bosquet sacré et de la rivière
Zora ont été recoupées avec les passages des scènes publiques.
Une session Tk a chargé les vrais fonds et l’illustration d’Hyrule. Le
lecteur direct de Link reste à valider dans une partie réelle sur émulateur.

Le catalogue de référence du Temple du Feu compte 40 checks. Les deux scènes
publiques et les résolveurs de placement en retrouvent 40, dont Volvagia et
son cœur. Les 38 autres marqueurs tombent sur le dessin de leur étage ou à
un pixel de celui-ci, sur des images de 700 pixels de large. Le troisième
étage, sans check dans cette seed, a été contrôlé sur trois repères physiques
et reste accessible. Le test Tk vérifie le passage depuis le cratère,
le filtrage par niveau et le retour à l’âge d’origine. Le NUP complet
et la mémoire en jeu n’ont pas été utilisés pour cette validation.

Le cratère du Péril a été recoupé avec les 37 IDs du catalogue. Le scan
local sans packs d’acteurs en a positionné cinq, dont les deux coffres
souterrains et la Grande Fée. Le fond est vérifié aux deux âges avec un
écart de 11 pixels sur la corniche sud sur 650 pixels de large. Le test Tk
vérifie que la liaison avec le Village Goron arrive au rez-de-chaussée.

Le recoupement de la caverne Dodongo avec le catalogue a retrouvé 30 IDs.
Le scan local sans packs d’acteurs en a positionné 19, dont les deux checks
de l’arène. L’erreur sur les repères indépendants est d’environ 8 pixels
au rez-de-chaussée et 1,3 à l’étage sur des fonds de 700 pixels de large.
Le test Tk vérifie la navigation entre les étages et le retour à l’âge suivi.

Les quatre ressources du Village Goron ont été recoupées avec les 52 IDs
du catalogue. Le scan local sans packs d’acteurs a positionné 19 IDs.
La galerie est, exclue du calcul d’alignement, est à 4,2 pixels du repère
projeté dans les deux vues de 650 × 695 pixels. Le test Tk vérifie le
filtrage par étage et sa conservation lors d’un changement d’âge.

Les quatre ressources publiques du mont du Péril contiennent les acteurs
correspondant à 29 des 31 IDs du catalogue local. Les deux vues ont les
quatre passages attendus. Ce recoupement vérifie les identifiants physiques
et les repères, avant le scan du NUP complet.
Les deux âges passent le contrôle du fond Field Atlas à l’entrée de la
caverne Dodongo, avec un écart de 6,4 pixels sur l’image de 650 × 1 603.
Le rapprochement des acteurs situe les six rubis de la grotte à Y ≈ 58,
sous la surface du sentier. Le test de projection rejette une entrée décalée.

Les fonds du cimetière ont passé le recalage automatique pour les deux âges.
Deux repères indépendants de l’ajustement valident l’alignement. Le test Tk
vérifie le filtrage de surface et l’ouverture d’un check souterrain par recherche.

À Cocorico, le catalogue local compte 76 IDs, dont 36 positionnés lors du
recoupement avec les six placements publics seuls. Le reste peut dépendre
des packs du NUP ou de correspondances d’événements. Les trois vues ont
passé le recalage Field Atlas et le contrôle indépendant du moulin
(écart d’environ 11 pixels sur un fond de 650 pixels de large). Les tests
vérifient la séparation des variantes et le passage à la vue sélectionnée
par le snapshot, y compris au retour vers une sauvegarde antérieure.

Les quatre Bancs publics de la plaine d’Hyrule ont permis de retrouver les
125 IDs du catalogue local. Une partie des positions dépend des packs
d’acteurs du NUP. Le recalage sur six repères, dont un exclu de l’ajustement,
donne un écart maximal de 15 pixels sur l’image source de 1 400 × 1 075 pour
les deux âges. Le test Tk du passage entre zones vérifie aussi l’aperçu au dézoom.

Au Bosquet sacré, l’alignement contrôlé à l’aide des placements publics
présente un écart maximal de 4,6 pixels sur 300 × 1 080, aux deux âges.
Le test de métadonnées vérifie la conservation de la position d’un coffre
et l’association de l’accès à la bonne ressource d’âge.

Les tests couvrent la réutilisation hors ligne du cache, le rejet d’un cache
endommagé, le choix entre deux marqueurs superposés et les deux récompenses
du Théâtre Mojo associées à l’entrée dans la vue Enfant.

L’import des Bois Perdus a été recoupé avec le catalogue réel et les
[placements publics](https://github.com/MrCheeze/oot-switch2-tools/tree/c9027ee50e7efd36cc3109d5990f170b7f0b4611/Banc/LostWood).
Les 13 IDs de la seed ont été retrouvés, dont neuf associés à des coordonnées
par ce recoupement. Le hash du rocher correspond aux deux âges dans les
Bancs publics. Sa lecture par le scanner complet nécessite le pack d’acteur
du NUP. Les tests Tk couvrent le changement de zone, le suivi d’âge, le
cloisonnement des listes et l’état du coffre commun. Cette vérification
ne couvre pas une session réelle dans les Bois Perdus.

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

Le marquage est testé sur deux sauvegardes binaires indépendantes avec OotrR,
avec refus sur un check suivi et sur une sauvegarde étrangère. Les quatre IDs
sans indicateur de la seed fournie se marquent et se décochent sur une sauvegarde
synthétique liée à cette seed. Le fichier de sauvegarde est inchangé.

Une sauvegarde binaire synthétique vérifie le passage enfant/adulte et un
rafraîchissement sans modification. Un test Tk vérifie le basculement et
le maintien du choix manuel. Le workflow ouvre aussi la fenêtre de
l’exécutable compilé et sélectionne puis marque un check simulé.

Les 48 tests Windows passent. Le job vérifie aussi le chargement du moteur
OotrR et ouvre la fenêtre de l’exécutable avant d’y sélectionner et marquer
un check simulé. [Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45097335491).

Le choix de dossier, l’exclusion d’un fichier étranger ou incomplet et le
changement de fichier le plus récent sont testés. Des snapshots mémoire
synthétiques traversent le vrai moteur OotrR et vérifient l’actualisation
avant sauvegarde, le repli partiel des coffres, la mauvaise seed et
la déconnexion. Aucun processus de jeu n’a été attaché pendant ces tests.

Les 51 tests et le build portable passent sur
[Windows CI](https://github.com/Hylieno/Map-oot-rando/actions/runs/45098305166).
Avec les métadonnées de la seed fournie, les 86 indicateurs ont également été
vérifiés via une mémoire synthétique au-dessus d’une sauvegarde non collectée.
