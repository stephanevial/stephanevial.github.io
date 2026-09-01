---
url: /lexique-ia/le-livre/token/
title: "Token : définition et exemple | Stéphane Vial"
description: "En intelligence artificielle, un token (ou « jeton ») est la plus petite unité de texte que les modèles de langage manipulent."
h1: "Token"
gabarit: notion
ordre: 5
og_type: article
---

*Token* · chapitre 5 · page 83

**Définition**  
En intelligence artificielle, un *token* (ou « jeton ») est la plus petite unité de texte que les modèles de langage manipulent. Il peut s’agir d’un mot entier, d’un fragment de mot, d’un signe de ponctuation ou d’un espace, selon le découpage propre à chaque modèle. Plutôt que de lire des phrases continues, le modèle reçoit une suite ordonnée de *tokens*, chacun converti en représentation numérique avant d’entrer dans les calculs. Les modèles génératifs produisent également leurs réponses *token* par *token*, dans un enchaînement probabiliste extrêmement rapide.

**Exemple**  
La phrase *Bonjour tout le monde !* pourrait être découpée en cinq *tokens* : *Bonjour* + *tout* + *le* + *monde* + *!*. Certains mots peuvent être divisés davantage : *tokenisation* deviendrait par exemple *token* + *isation*. Dans les applications, comme ChatGPT, Claude ou Gemini, qui utilisent des grands modèles de langage, chaque question envoyée et chaque réponse générée sont comptabilisées en *tokens*. C’est ce calcul qui détermine les limites de longueur d’une conversation, la vitesse de traitement et souvent le coût d’utilisation.

**Importance**  
Le *token* est l’unité de base du fonctionnement des modèles de langage. La fenêtre de contexte est elle aussi exprimée en nombre de *tokens*, non en nombre de mots. Cette logique a des effets concrets : un même texte ne compte pas le même nombre de *tokens* selon la langue. Les coûts d’utilisation des modèles sont d’ailleurs généralement calculés en fonction du nombre de *tokens* traités, en entrée comme en sortie. Comprendre ce qu’est un *token* permet donc de mieux saisir comment une IA « lit » et génère du texte, mais aussi pourquoi certaines requêtes coûtent plus cher en calcul et en énergie.

<p class="renvoi">Une des quatre-vingt-onze notions du <a href="../">Petit lexique vivant de l’intelligence artificielle</a>, dans son texte intégral, telle qu’elle est imprimée page 83 de l’ouvrage.</p>
