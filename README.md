# Map-oot-rando

Compagnon de carte local pour OotrR, première zone : Kokiri Forest.

**État : socle Python testé, pas encore d'application graphique utilisable.**
Aucune coordonnée réelle livrée, aucun test avec le jeu, aucun build Windows.
`KF_rock_1` est uniquement un exemple : son existence n'est pas présumée.

Python 3.10+ ; aucune dépendance pour ce premier checkpoint :

```sh
python -m unittest discover -s tests -v
```

Le module `metadata.export_scan` consomme les groupes de coffres et sources
supplémentaires déjà étiquetés par `oot_rando.game.extra_sources.scan_world`.
Il ne lit pas directement un NUP et ne remplace pas le scanner OotrR.
Les ressources du jeu restent locales et ne doivent pas être commitées.

Voir [architecture](docs/ARCHITECTURE.md), [progression](docs/PROGRESS.md),
[décisions](docs/DECISIONS.md) et [tests](docs/TESTING.md).
