# Décisions

- Bois Perdus. Les boutons et les repères de passage relient des vues distinctes.
  Le schéma utilise les repères du jeu. Les icônes et la canopée de la capture
  Questfern masquent le détail nécessaire pour valider une carte de terrain.
- Plaine d’Hyrule. Le fond Questfern fonctionne avec cinq repères et un arbre
  de contrôle. La validation du fond est indépendante du contenu de la seed.
- Bosquet sacré. Les entrées de grotte viennent des acteurs physiques
  correspondants. Les coordonnées en sous-sol restent accessibles dans les détails.
- Cocorico. Les fonds Field Atlas sans icônes sont validés sur six repères
  physiques. Les placements adultes sont séparés par variante de scène.

- Python sans dépendance pour le socle ; Tkinter prévu, cohérent avec OotrR.
- Ne pas développer une seconde logique d'accessibilité ni un lecteur mémoire.
- Réutiliser une session existante ; l'intégration événementielle reste à coder.
- Identifiant interne et nom affiché distincts ; aucun nom de check présumé réel.
- Métadonnées v1 avec révision upstream et provenance explicites. La provenance
  déclarée n'est pas une preuve cryptographique d'origine ; l'export réel doit
  être produit localement à partir d'un scan validé.
- Tests synthétiques exclusivement à ce stade. Aucun fichier propriétaire distribué.
- Pas de workflow de build Windows avant application fonctionnelle.
- Phase bornée audit + socle : quota Plus non observable. Vérification utilisateur
  requise avant une nouvelle phase importante, conformément à AGENTS.md.

- Deuxième phase autorisée par « Go » : interface et simulation testées.
- Le mode par défaut est explicitement synthétique ; aucun décor présenté comme
  la vraie forêt. Les noms de démonstration commencent par SIMULATED.
- Packaging Windows de préversion configuré maintenant que l'interface fonctionne ;
  portable en dossier pour réduire la complexité et sans publication de Release.

- Utiliser une grille cotée comme fond du schéma. Une image nécessiterait une
  source utilisable et un alignement vérifié pour chaque ressource.
- Utiliser le scanner de la copie OotrR locale et conserver les IDs du catalogue
  de seed. L'export crée uniquement un nouveau fichier JSON.

Le marquage manuel est limité aux checks sans indicateur de collecte et
l’interface l’identifie séparément. L’application retient les chemins localement
après une première lecture réussie. Un arrêt explicite désactive la reprise.

Le profil mémorise le répertoire choisi et suit le fichier lisible le plus
récent de la seed. Le lecteur mémoire OotrR est proposé en option et reste
en lecture seule. La carte utilise une sauvegarde correspondante comme
base et revient au fichier quand la mémoire ne convient pas.
