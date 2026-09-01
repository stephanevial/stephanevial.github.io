# fontes/

Archivo, la fonte de la couverture, auto-hébergée. Sous licence SIL Open Font
License 1.1, dont le texte intégral est dans `OFL.txt` : la licence exige
qu'elle accompagne les fichiers, elle ne se retire pas.

| Fichier | Poids | Ce qu'il contient |
|---|---|---|
| `archivo-variable.woff2` | 57 Ko | le romain, **variable** : `wght` 400 à 700, `wdth` 62 à 125 ramené à 62-100 |
| `archivo-italique.woff2` | 15 Ko | l'italique, **statique**, `wdth` 100 et `wght` 400 |

## Pourquoi ces deux fichiers-là, et pas d'autres

**Le romain reste variable** parce que le titrage se règle à `wdth 68`, la
valeur exacte du titre imprimé, et qu'on ne l'atteint que par
`font-variation-settings: "wdth" 68`. `font-stretch` seul ne suffit pas.

**L'italique est statique** parce qu'il n'apparaît jamais en titrage : il ne
sert qu'au fil du texte, à `wdth 100`. Lui garder l'axe de largeur coûtait
88 Ko pour rien.

**Les plages sont restreintes** à ce que le site emploie réellement. La fonte
complète pesait 193 Ko à elle seule, au-dessus du budget de 150 Ko par page du
§7 du cahier des charges. Restreinte, elle en pèse 72.

## Comment elles ont été fabriquées

Sources récupérées dans le dépôt Google Fonts, `ofl/archivo/`. **Le dépôt sert
à obtenir le fichier, jamais à le servir au visiteur** : le site ne fait aucune
requête vers `fonts.googleapis.com`, et c'est une exigence non négociable du
§7. Une page qui déclare ne rien mesurer ne peut pas envoyer son lecteur chez
un tiers à chaque visite.

```
U="U+0020-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,\
U+2000-206F,U+2074,U+20AC,U+2122,U+2190-2193,U+2212,U+2215,U+FEFF,U+FFFD"

python3 -m fontTools.varLib.instancer "Archivo[wdth,wght].ttf" \
        wght=400:700 wdth=62:100 -o r.ttf
python3 -m fontTools.subset r.ttf --unicodes="$U" --layout-features='*' \
        --flavor=woff2 --output-file=archivo-variable.woff2

python3 -m fontTools.varLib.instancer "Archivo-Italic[wdth,wght].ttf" \
        wdth=100 wght=400 -o i.ttf
python3 -m fontTools.subset i.ttf --unicodes="$U" --layout-features='*' \
        --flavor=woff2 --output-file=archivo-italique.woff2
```

Le jeu de caractères couvre le français, l'anglais et l'espagnol, plus la
ponctuation typographique dont le site a besoin : guillemets français,
apostrophe courbe, points de suspension, point médian, et la flèche `→` des
renvois de bas de page. Les éditions anglaise et espagnole n'auront rien à
refaire ici.

`fonttools` a besoin de `brotli` pour écrire du WOFF2.
