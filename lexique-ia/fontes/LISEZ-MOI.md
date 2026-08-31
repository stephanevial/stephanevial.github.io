# fontes/

Vide pour l'instant, et c'est voulu.

La séance 1 ne porte aucune direction artistique : `style.css` s'appuie sur la
pile de fontes du système, donc aucun fichier n'est chargé et aucune requête ne
sort du domaine.

En séance 2, ce dossier recevra **Archivo variable, en WOFF2 sous-ensemblé**,
la fonte de la couverture. Deux points qui ne se négocient pas :

- la fonte est **auto-hébergée ici**, jamais appelée depuis `fonts.googleapis.com`.
  Le dépôt Google Fonts sert à récupérer le fichier source, pas à le servir au
  visiteur : une page qui déclare ne rien mesurer ne peut pas envoyer le lecteur
  chez un tiers à chaque visite (cahier des charges, §7) ;
- le titrage se règle par `font-variation-settings: "wdth" 68`, la valeur exacte
  du titre imprimé. `font-stretch` seul ne suffit pas.

Les fontes statiques d'origine sont dans
`~/Cowork/20_UQAM/livres-publis/petit-lexique-ia/production/02-couverture/systeme/fontes/`.
La variable se récupère et se convertit avec `fonttools`.
