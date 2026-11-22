# Map-oot-rando

Compagnon de carte local pour OotrR, première zone visée : Kokiri Forest.

**Préversion : carte interactive et simulation fonctionnelles.** Les emplacements
fournis sont fictifs, explicitement signalés. Aucune coordonnée réelle livrée,
aucune connexion au vrai tracker pour l'instant. `KF_rock_1` reste un exemple de
nomenclature, dont l'existence n'est pas présumée.

## Lancer localement

Python 3.10+ avec Tkinter, sans dépendance Python supplémentaire :

```sh
python -m map_oot_rando
```

Sur Windows x64, installer Python avec Tcl/Tk, ouvrir un terminal dans le dépôt
et exécuter cette commande. La validation locale a été faite sous Linux, pas Windows.

- Molette : zoom ; glisser sur le fond : déplacement ; « Ajuster la vue » : cadrage.
- Recherche par nom ou ID, puis Entrée ou sélection dans la liste pour centrer.
- Choisir une ressource pour isoler les variantes ; hauteur Y dans les détails.
- Filtres de catégorie/statut ; décocher « Récupéré » pour masquer les checks gris.
- En simulation, sélectionner un check puis changer son statut ou la connexion.
  En déconnexion, l'affichage conserve le dernier état ; la reconnexion publie les
  changements simulés en attente.

## Métadonnées locales

Le bouton « Ouvrir métadonnées » ou `python -m map_oot_rando carte.json` charge
le format v1 validé par `model.load_metadata`. Les positions absentes restent
recherchables sans marqueur. Les données `ootrr-scan` s'ouvrent déconnectées,
avec des statuts inconnus ; les commandes de simulation sont masquées.

`metadata.export_scan` consomme les groupes de coffres et sources supplémentaires
déjà étiquetés par `oot_rando.game.extra_sources.scan_world`. Il ne lit pas directement
un NUP. L'outil d'extraction réel et la jointure avec la seed restent à développer.
Ne pas commiter de ressources du jeu ni présenter une fixture comme réelle.

## Tests et Windows portable

```sh
python -m unittest discover -s tests -v
```

Sans écran, les trois tests Tk sont ignorés explicitement. Définir
`MAP_REQUIRE_DISPLAY=1` pour exiger leur exécution (utilisé dans le workflow).

Le workflow **Windows portable preview** teste puis construit avec PyInstaller
un dossier portable x64. Après un run réussi, télécharger l'artifact
`Map-oot-rando-windows-x64-preview`, tout extraire et lancer `Map-oot-rando.exe`.
Il s'exécute sur les modifications pertinentes de PR ou manuellement une fois
le workflow disponible sur la branche par défaut. Aucune Release publiée.
Un build réussi ne constitue pas une validation avec le jeu.

Voir [architecture](docs/ARCHITECTURE.md), [progression](docs/PROGRESS.md),
[décisions](docs/DECISIONS.md) et [tests](docs/TESTING.md).
