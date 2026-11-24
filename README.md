# Map-oot-rando

Compagnon de carte local pour OotrR avec Kokiri Forest, les Bois Perdus, le Bosquet sacré, la plaine d’Hyrule, Cocorico, le cimetière, le mont du Péril, le Village Goron, la caverne Dodongo, le cratère du Péril et le Temple du Feu.

La simulation utilise des positions fictives.
L’import local lit les coordonnées de la seed et le suivi lit les états d’OotrR
depuis une sauvegarde. Les checks sans correspondance certaine restent dans la liste.

## Lancer localement

Python avec Tkinter pour le lancement depuis les sources :

```sh
python -m pip install -r requirements.txt
python -m map_oot_rando
```

Sur Windows x64, installer Python avec Tcl/Tk, ouvrir un terminal dans le dépôt
et exécuter cette commande. La validation locale a été faite sous Linux, pas Windows.

- Molette : zoom ; glisser sur le fond : déplacement ; « Ajuster la vue » : cadrage.
- Recherche par nom ou ID, puis Entrée ou sélection dans la liste pour centrer.
- Si plusieurs marqueurs se recouvrent, cliquer sur leur point commun ouvre la liste des checks.
- Utilise les boutons **Enfant** et **Adulte** à côté du sélecteur de zone. Les couches Static et Dynamic sont réunies.
- Dézoome jusqu’à la **Carte d’Hyrule** ou ouvre-la avec le bouton. Les zones disponibles sont cliquables.
  Les repères de passage relient directement les cartes locales.
- Réimporte le NUP et le `checks.json` si une ancienne carte enregistrée ne contient pas les nouveaux passages.
- Filtres de catégorie/statut ; décocher « Récupéré » pour masquer les checks gris.
- En simulation, sélectionner un check puis changer son statut ou la connexion.
  En déconnexion, l'affichage conserve le dernier état ; la reconnexion publie les
  changements simulés en attente.

## Fonds de carte

Les plans Field Atlas se chargent automatiquement. Les fonds téléchargés sont conservés pour
les prochaines ouvertures hors ligne. Un ancien fond Questfern ou personnalisé est écarté
à l’ouverture de la carte. Les vues sans plan publié conservent un schéma dans la même palette.
L’illustration générale est celle de Nintendúo, publiée par Field Atlas et également
utilisée par Ocarina Atlas. [Field Atlas](https://oot.gousse.cool/) · [Ocarina Atlas](https://github.com/antonioalvromero/Ocarina-Atlas)

Sur la carte d’Hyrule, les repères avec une flèche ouvrent un menu.
Quand la fenêtre est étroite, le menu **Zones voisines** regroupe les
destinations qui figurent habituellement dans la barre de la carte.
Kokiri donne accès au village, au pont et au Monde des rêves. La
Citadelle donne accès au Temple du Temps et à la Chambre des Sages.
Les boutons Enfant et Adulte permettent de choisir l’âge avant
d’ouvrir une zone. Survole un repère pour lire son nom en haut de la carte.
Si tu réimportes la même seed, l’application garde ta vue lorsqu’elle
est encore disponible, ainsi que ton choix de suivre ou non l’âge sauvegardé.
Les derniers états connus restent affichés pendant la reconnexion,
même si la sauvegarde suivie est brièvement en cours d’écriture.
La barre de suivi indique la date de la dernière synchronisation.

Dans les Bois Perdus, le tracé doré indique le chemin normal de Kokiri au Bosquet
sacré. Les passages de cette route indiquent où Link apparaît à chaque entrée.
Le plan inclut aussi la branche ouest et ses checks près du pont.
Depuis la plaine d’Hyrule, l’entrée de la forêt ouvre la vue du pont de
Kokiri. Le coffre souterrain des pestes Mojo est indiqué à sa bouche de
grotte dans le village. Les marqueurs de passage ouvrent le Village Goron
et la rivière Zora. Leurs passages permettent aussi de revenir aux Bois
Perdus. L’anneau doré indique où Link apparaît pour ces raccourcis.
Au Village Goron, la carte indique les deux arrivées prévues par le jeu.
Si un check et un passage se superposent, clique sur leurs marqueurs
pour choisir le check ou la destination. La rivière Zora est reliée
à la plaine d’Hyrule et affiche ses checks enfant et adulte. Le coffre et les pots
en grotte sont indiqués à leur entrée en surface. Le Domaine Zora se rejoint
depuis la rivière. Ses checks incluent les rayons de la boutique et le mini-jeu
de plongeon. Les variantes adultes partagent la même vue. Le Domaine donne
accès à la Fontaine Zora, avec un plan Field Atlas par âge et un repère de
passage pour les checks derrière la paroi. La Caverne de glace est
reliée à la vue adulte de la Fontaine et possède son propre plan.
Enfant, la Fontaine mène au ventre de Jabu-Jabu. Les trois niveaux ont
leurs plans Field Atlas. Barinade, son cœur et les pots de sa salle ont une
vue schématique dédiée. Depuis la forêt Kokiri, l’Arbre Mojo propose cinq
plans, dont celui du hall d’entrée, et une vue dédiée à l’arène de Gohma.
Depuis le Bosquet sacré, le Temple de la Forêt propose aussi cinq plans
Field Atlas et l’arène de Ganon spectral. Depuis Cocorico, le Puits possède
deux plans et conserve l’âge de la vue au retour vers le village.
Le Temple de l’Ombre se rejoint depuis le cimetière. Ses quatre niveaux
et l’arène de Bongo Bongo sont accessibles dans le sélecteur d’étage.
Les deux récompenses du Théâtre Mojo partagent un marqueur à l’entrée.
Au Bosquet sacré, les deux coffres enfouis sont repérés par l’accès à leur
grotte. Les détails conservent les coordonnées XYZ du coffre.
Cocorico utilise les [fonds sans icônes de Field Atlas](https://oot.gousse.cool/kakariko-village).
Les vues adulte et après l’incendie utilisent la même image avec leurs propres checks.
Le [cimetière](https://oot.gousse.cool/graveyard) a aussi un fond Field Atlas.
**Souterrains** ouvre les checks enfouis dans une vue schématique. La recherche
indique la destination des checks situés dans une autre vue. Sélectionne
un résultat pour centrer son marqueur, même si le fond se charge ensuite.
Le mont du Péril est accessible depuis Cocorico. Le fond
[Field Atlas du sentier](https://oot.gousse.cool/death-mountain-trail) est
aligné pour les deux âges. **Souterrains** ouvre les checks en grotte.
Depuis le mont du Péril, le [Village Goron](https://oot.gousse.cool/goron-city)
propose quatre galeries et une grotte. Le sélecteur d’étage limite les marqueurs
au niveau affiché. La grotte utilise un schéma.
La [caverne Dodongo](https://oot.gousse.cool/dodongos-cavern) est accessible
depuis le mont du Péril. Le rez-de-chaussée et l’étage ont leurs propres
fonds. L’arène du boss utilise un schéma et affiche séparément le boss et son cœur.
Le [cratère du Péril](https://oot.gousse.cool/death-mountain-crater) relie
le mont du Péril au rez-de-chaussée du Village Goron. Le vendeur Mojo
figure sur la carte enfant. Les checks sous la surface sont accessibles
via **Souterrains**.
Le cratère mène au Temple du Feu. Les cinq niveaux utilisent les plans
Field Atlas et le sélecteur d’étage. Volvagia et son cœur ont une vue
schématique séparée. [Plans du Temple du Feu](https://oot.gousse.cool/fire-temple)

Les checks hors du fond restent consultables dans la liste. Sélectionner
leur entrée affiche leur position réelle, et la case **Afficher les checks
hors du fond** permet de les afficher ensemble.

La Citadelle d’Hyrule se rejoint depuis la plaine. Les deux âges ont un
plan distinct. Les jeux, les boutiques et la maison du garde reprennent
les positions du jeu. Enfant, la Citadelle mène au Château d’Hyrule.
Un plan représente les abords. La lettre de Zelda et les caisses de la
cour ont leur propre vue schématique.
Adulte, la Citadelle mène aux abords du Château de Ganon. Le sélecteur
du château donne aussi accès à la vue schématique de l’effondrement,
où se trouvent les quatre pots du catalogue.
L’entrée des abords ouvre l’intérieur. Le sélecteur d’étage permet de
passer des six épreuves à la tour et à la salle de Ganondorf. Ces vues
utilisent les repères du jeu sur des schémas. Réimporte le jeu et la seed
pour ajouter ces vues à une carte enregistrée auparavant.

La plaine donne aussi accès à la Vallée Gerudo dans les deux âges. Le
fond Field Atlas se charge automatiquement et les checks en grotte
apparaissent à leur entrée, avec les coordonnées de l’objet dans les détails.
Depuis la vallée adulte, le passage ouest mène à la Forteresse Gerudo.
Les deux récompenses du tir à l’arc sont associées à l’organisatrice et
la carte Gerudo peut apparaître près de chaque cellule.
Le Centre d’entraînement est accessible depuis la forteresse. Un schéma
reprend les salles du jeu et le sélecteur permet d’afficher la passerelle
au-dessus du labyrinthe.
La porte au nord-ouest de la forteresse mène au Désert hanté. Sa vue
schématique montre les ruines, les checks et le trajet tracé par le guide
dans la scène du jeu.
Le passage ouest du Désert hanté mène au Colosse du désert aux deux
âges. Le fond Field Atlas se charge automatiquement. Le coffre
souterrain apparaît à l’entrée de sa grotte.
Le Colosse donne accès au Temple de l’Esprit par l’entrée principale
et les deux passages des mains. Un anneau doré indique où Link apparaît
après chaque passage, dans les deux sens. Le temple affiche quatre fonds
Field Atlas et un schéma de l’arène de Twinrova.

Le lac Hylia possède son fond Field Atlas. On y accède depuis la
plaine et la Vallée Gerudo aux deux âges, ou depuis le Domaine Zora
avec Link enfant. Le suivi peut passer de la plaine au lac pendant
que le jeu conserve la même scène chargée.
Le passage immergé du lac ouvre le Temple de l’Eau au deuxième étage
avec Link adulte. Les quatre plans Field Atlas couvrent aussi la salle
de Morpha, au nord du rez-de-chaussée. Le suivi de Link affiche ce plan
dès le couloir d’accès à Morpha.
Lors de l’import, les coffres et les Skulltulas indexés dans la table
des étages du jeu s’affichent sur leur plan Field Atlas correspondant.

Le Temple du Temps se rejoint depuis la Citadelle aux deux âges.
Sur la carte du temple, le piédestal de l’épée ouvre la Chambre des
Sages. Le repère au centre de la plateforme permet de revenir au temple.
Dans la forêt Kokiri, le lit de Link mène à la carte du Monde des rêves.
Au musée, le repère de l’organisateur propose le retour à Kokiri
ou la salle intermédiaire du défi des boss.
Les dix coffres du défi partagent un point. Un clic sur le marqueur
permet de choisir le coffre voulu.

Le ranch Lon Lon se rejoint depuis la plaine aux deux âges. Le jeu
des poules de Talon apparaît dans la vue enfant. Le suivi de Link
bascule entre le ranch et la plaine au franchissement du portail.

## Suivre la partie

Coche **Afficher la position de Link**. Cette option active **Mémoire du jeu**
et réutilise la connexion OotrR de la seed. **Suivre Link entre les zones**
ouvre sa nouvelle zone à chaque changement de scène ou d’âge. Tu peux
décocher le suivi de zone en gardant le marqueur. Si le jeu s’arrête ou
que la seed active est différente, le marqueur disparaît.

Clique sur **Choisir le dossier de sauvegardes…** et indique le dossier qui
contient les sauvegardes de ton jeu. L’application cherche dans les sous-dossiers
et suit le `progress.sav` le plus récent que le moteur OotrR 0.8.0 reconnaît
comme appartenant à la seed. Si ce fichier devient temporairement illisible,
la carte garde le dernier état vérifié et attend le prochain cycle de lecture.
Si tu as rouvert un JSON sans profil local,
choisis aussi le `checks.json` du dossier complet de cette seed.

Coche **Mémoire du jeu** pour activer le lecteur OotrR dans la carte. Si tu
utilises déjà le suivi mémoire dans le tracker OotrR séparé, arrête-le d’abord.
La carte a besoin d’une première sauvegarde de la seed pour rattacher la
partie. Le bandeau indique quand la mémoire est utilisée et si les coffres
dépendent encore du fichier. Si le jeu s’arrête ou que la partie active ne
correspond pas, la carte revient à la sauvegarde reconnue. Le lecteur reste
en lecture seule.

Le dossier est mémorisé localement après validation. **Arrêter le suivi**
désactive la reprise. Les checks sans indicateur se marquent dans leurs
détails. Les marques restent séparées par fichier et par seed.
**Suivre l’âge sauvegardé** sélectionne la vue Enfant ou Adulte lorsque
l’information est disponible dans la mémoire ou le fichier. Le choix
manuel d’une vue suspend le changement.
À Cocorico, ce réglage sélectionne aussi la variante adulte confirmée par
la sauvegarde ou la mémoire. Le menu de zone permet de choisir la variante
après l’incendie quand le suivi ne fournit pas cet état.

**Diagnostic de la carte…** exporte les IDs et les coordonnées pour vérifier une
seed. Pour les fonds Field Atlas déjà chargés, il indique quels marqueurs se
projettent en dehors de l’image ou loin du trait. Le rapport exclut l’image,
l’identifiant de seed et la sauvegarde.

## Métadonnées locales

Le bouton « Ouvrir métadonnées » ou `python -m map_oot_rando carte.json` charge
le format v1 validé par `model.load_metadata`. Les positions absentes restent
recherchables sans marqueur. Les données `ootrr-scan` s'ouvrent déconnectées,
avec des statuts inconnus ; les commandes de simulation sont masquées.

`metadata.export_scan` consomme les groupes de coffres et sources supplémentaires
déjà étiquetés par `oot_rando.game.extra_sources.scan_world`. Il ne lit pas directement
un NUP. La commande d'export ci-dessous utilise le scanner de l'installation OotrR locale.
Ne pas commiter de ressources du jeu ni présenter une fixture comme réelle.

## Tests et Windows portable

```sh
python -m unittest discover -s tests -v
```

Sans écran, les tests Tk sont ignorés explicitement. Définir
`MAP_REQUIRE_DISPLAY=1` pour exiger leur exécution (utilisé dans le workflow).

Le workflow **Windows portable preview** exécute les tests pour chaque mise à
jour pertinente de la PR. Un lancement manuel ou un commit de jalon dont le
message se termine par `[preview]` construit aussi le dossier portable x64.
Après une compilation réussie, télécharger l'artifact
`Map-oot-rando-windows-x64-preview`, tout extraire et lancer `Map-oot-rando.exe`.
Il s'exécute sur les modifications pertinentes de PR ou manuellement une fois
le workflow disponible sur la branche par défaut. Aucune Release publiée.
Un build réussi ne constitue pas une validation avec le jeu.

Voir [architecture](docs/ARCHITECTURE.md), [progression](docs/PROGRESS.md),
[décisions](docs/DECISIONS.md) et [tests](docs/TESTING.md).

La [liste des builds Windows x64](https://github.com/Hylieno/Map-oot-rando/actions/workflows/windows.yml)
donne accès aux artefacts des exécutions réussies. Connexion GitHub requise et
rétention de 14 jours.

## Importer sa seed dans la version portable Windows

Extraire le ZIP et ouvrir `Map-oot-rando.exe`. Cliquer sur **Importer mon jeu et ma seed…**,
puis choisir le NUP du jeu mis à jour et le `checks.json` du dossier de la seed OotrR.
La carte se charge à la fin du scan local. **Enregistrer la carte…** permet de
garder un JSON réutilisable via **Ouvrir métadonnées…**. Python et le scanner
OotrR sont inclus dans le build portable.

## Exporter les points d'une seed OotrR en ligne de commande

Dans une copie locale du [dépôt OotrR](https://github.com/Mozencaz/OotrR), sélectionner
la révision `eb6682704f7589b5a0c07ac0e49d89fef4108545`. Installer ses dépendances
dans votre environnement Python avec `python -m pip install -r /chemin/vers/OotrR/requirements.txt`.

Depuis ce dépôt, lancer la commande avec le NUP local contenant le jeu et sa mise
à jour, et le `checks.json` du dossier de la seed générée avec cette version d'OotrR.

```sh
python -m map_oot_rando.export --ootrr "OotrR" --nup "jeu.nup" --checks "seed/checks.json" --output "kokiri.json"
python -m map_oot_rando kokiri.json
```

L'exporteur crée un nouveau fichier et lit le jeu et le catalogue localement.
La carte dessine les pièces et repères trouvés par OotrR dans le repère X/Z.
Une vue sans repères affiche la grille, y compris les anciens JSON. Pour les
ajouter à une carte existante, refaire l’import du NUP et du catalogue. Les checks de Kokiri Forest qui ne
correspondent pas à une position du scan restent recherchables dans la liste.
Les positions importées et les statuts en direct restent à valider avec le jeu.
