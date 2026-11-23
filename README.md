# Map-oot-rando

Compagnon de carte local pour OotrR avec Kokiri Forest et les Bois Perdus.

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
- Choisir Enfant ou Adulte. Les couches Static et Dynamic sont réunies. La hauteur Y est dans les détails.
- **Vers les Bois Perdus** et **Retour à Kokiri** changent de zone en gardant l’âge affiché et le suivi de la partie.
  Réimporter le NUP et le `checks.json` pour ajouter les Bois Perdus à une carte enregistrée plus ancienne.
- Filtres de catégorie/statut ; décocher « Récupéré » pour masquer les checks gris.
- En simulation, sélectionner un check puis changer son statut ou la connexion.
  En déconnexion, l'affichage conserve le dernier état ; la reconnexion publie les
  changements simulés en attente.

## Fonds de carte

Le fond par défaut est la [carte de Kokiri publiée par Questfern](https://questfern.com/oot/guides/interactive-map/?area=kokiri).
L’application la charge depuis sa source et vérifie la projection avant de
l’afficher. **Fond de carte** permet de choisir Field Atlas, un fond local ou
le schéma. **Enregistrer la carte…** permet de rouvrir le fond hors ligne.

Les Bois Perdus s’ouvrent sur un schéma sans icônes d’objet préimprimées.
Les entrées et les checks positionnés utilisent les coordonnées des ressources locales.

Pour une image locale, l’application lit automatiquement un fichier de coordonnées
`.wld`, `.pgw` ou `.jgw` de même nom s’il utilise le repère X/Z du jeu. Une image
sans coordonnées peut être calibrée manuellement à l’aide de trois repères.
Les nouveaux diagnostics d’import listent les noms des ressources de capture
candidates dans le conteneur local, sans inclure leur contenu.

Les checks hors du fond restent consultables dans la liste. Sélectionner
leur entrée affiche leur position réelle, et la case **Afficher les checks
hors du fond** permet de les afficher ensemble.

## Suivre la partie

Clique sur **Choisir le dossier de sauvegardes…** et indique le dossier qui
contient les sauvegardes de ton jeu. L’application cherche dans les sous-dossiers
et suit le `progress.sav` le plus récent que le moteur OotrR 0.8.0 reconnaît
comme appartenant à la seed. Si tu as rouvert un JSON sans profil local,
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

Préversion compilée : [télécharger l'artifact Windows x64](https://github.com/Hylieno/Map-oot-rando/actions/runs/45098305166/artifacts/14784062487)
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
