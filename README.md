# Map-oot-rando

Compagnon de carte local pour OotrR, première zone visée : Kokiri Forest.

**Préversion Kokiri Forest.** La simulation utilise des positions fictives.
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
- Choisir Enfant ou Adulte. Les couches Static et Dynamic sont réunies. La hauteur Y est dans les détails.
- Filtres de catégorie/statut ; décocher « Récupéré » pour masquer les checks gris.
- En simulation, sélectionner un check puis changer son statut ou la connexion.
  En déconnexion, l'affichage conserve le dernier état ; la reconnexion publie les
  changements simulés en attente.

## Afficher une vue aérienne

La vue charge automatiquement le [fond Kokiri Forest d’origine](https://oot.gousse.cool/content/maps/7e802ffa8684f3cd.svg)
directement depuis [Field Atlas](https://oot.gousse.cool/kokiri-forest). Une connexion est
nécessaire au premier chargement. L’application aligne le fond automatiquement
si au moins quatre maisons correspondent aux repères. La vue Enfant peut utiliser
les repères Adulte quand les trois entrées partagent le même repère de coordonnées.
**Fond Field Atlas…** permet de réessayer en cas d’échec. Enregistre la carte
pour la rouvrir hors ligne. Les positions sur le dessin
restent approximatives dans les secteurs sans repères. Le fond peut être
recalibré localement autour d’un point vérifié, sans modifier les coordonnées
des checks. Les fonds Field Atlas des anciens JSON se recalibrent à l’ouverture.

**Ajouter une vue aérienne…** permet aussi d’utiliser un PNG ou un JPEG local.

Dans une carte importée, choisis la ressource à afficher puis clique sur
**Ajouter une vue aérienne…**. Sélectionne ton image locale PNG ou JPEG, vue de
dessus. Dans la fenêtre d’alignement, choisis trois repères bien espacés qui
forment un triangle et clique à leur emplacement respectif sur l’image.
**Afficher la carte** superpose les checks à l’image. **Enregistrer la carte…**
conserve l’image et l’alignement dans le JSON, pour cette ressource.

Le jeu et la seed fournissent les coordonnées. Le fond image est fourni
séparément par l’utilisateur. Le schéma reste disponible en retirant le fond.

Les checks hors du dessin restent consultables dans la liste. Sélectionner
leur entrée affiche leur position réelle, et la case **Afficher les checks
hors du fond** permet de les afficher ensemble.

## Suivre une sauvegarde

Dans la version Windows, clique sur **Suivre ma sauvegarde…** et sélectionne le
fichier `progress.sav` associé à ta seed. Si tu as rouvert un JSON enregistré,
l’application demande aussi le `checks.json` du dossier complet de cette seed.
Le build embarque OotrR 0.8.0. OotrR valide que la sauvegarde appartient à la seed. Les états sont actualisés
quand le jeu écrit la sauvegarde. **Arrêter le suivi** conserve le dernier état
affiché. L’application lit la sauvegarde sans la modifier.

**Diagnostic de la carte…** exporte les IDs et les coordonnées pour vérifier une
seed. Le rapport exclut l’image, l’identifiant de seed et la sauvegarde.

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

Le workflow **Windows portable preview** teste puis construit avec PyInstaller
un dossier portable x64. Après un run réussi, télécharger l'artifact
`Map-oot-rando-windows-x64-preview`, tout extraire et lancer `Map-oot-rando.exe`.
Il s'exécute sur les modifications pertinentes de PR ou manuellement une fois
le workflow disponible sur la branche par défaut. Aucune Release publiée.
Un build réussi ne constitue pas une validation avec le jeu.

Voir [architecture](docs/ARCHITECTURE.md), [progression](docs/PROGRESS.md),
[décisions](docs/DECISIONS.md) et [tests](docs/TESTING.md).

Préversion compilée : [télécharger l'artifact Windows x64](https://github.com/Hylieno/Map-oot-rando/actions/runs/45093625991/artifacts/14782711419)
(connexion GitHub requise ; rétention de 14 jours). Tests Tk et build CI réussis ;
exécutable packagé pas encore validé manuellement.

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
