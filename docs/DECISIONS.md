# Décisions

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
