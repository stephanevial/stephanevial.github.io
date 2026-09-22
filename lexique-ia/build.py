#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — la fabrique du site du Petit lexique vivant de l’IA.

    python3 build.py

Lit les fichiers de contenu/, applique les gabarits de gabarit/, écrit les
index.html du site, régénère ../sitemap.xml, llms.txt (ici et à la racine du
sous-domaine) et llms-full.txt.

Quinze pages : les sept principales, et les huit notions données à lire, une
par adresse sous /lexique-ia/livre/. Les notions ne figurent pas dans la
navigation : on y arrive par la page du livre.

Deux exécutions successives produisent des fichiers identiques : aucune date,
aucun compteur, aucun aléa n’entre dans la sortie.

Trois exigences de conversion, contrôlées à chaque exécution et bloquantes :
  1. aucune substitution typographique (l’extension smarty n’est jamais
     chargée) : les apostrophes, guillemets et tirets sortent tels qu’ils sont
     entrés ;
  2. les espaces insécables survivent : ils sont comptés avant et après
     conversion, et le script s’arrête si le compte change ;
  3. les italiques sont des <em>, jamais des <i> : la présence de <i> ou de
     <b> arrête le script.

Le seul endroit à éditer pour corriger un texte est contenu/.
"""
import io
import os
import re
import sys
import unicodedata
from urllib.parse import urljoin

try:
    import markdown
except ImportError:
    sys.exit("Il manque python-markdown :  python3 -m pip install markdown")
try:
    import yaml
except ImportError:
    sys.exit("Il manque PyYAML :  python3 -m pip install pyyaml")

ICI = os.path.dirname(os.path.abspath(__file__))
CONTENU = os.path.join(ICI, "contenu")
GABARIT = os.path.join(ICI, "gabarit")
RACINE = os.path.dirname(ICI)               # la racine du sous-domaine
BASE = "/lexique-ia/"

DOMAINE = "https://web.stephane-vial.net"
NBSP = "\u00a0"   # jamais en littéral : il ne survit pas aux aller-retours de fichier

FEUILLE = ""     # style.css, lue au démarrage, pour les vérifications

AVERTISSEMENT = ("<!-- Fichier généré par build.py. Ne pas modifier à la "
                 "main : éditer contenu/%s.md -->")

# La navigation. Les huit notions n’y figurent pas : on y arrive par la page
# du livre.
MENU = ["accueil", "livre", "fabrique", "declaration", "communique",
        "auteur", "commander"]
# L’entrée composée en bouton dans le menu : celle qui mène à l’achat.
MENU_BOUTON = "commander"
MENU_LIBELLE = {"accueil": "Accueil", "fabrique": "La fabrique",
                "declaration": "La déclaration", "livre": "Le livre",
                "communique": "Le communiqué", "auteur": "L’auteur",
                "commander": "Commander"}

# Le pied, identique sur toutes les pages, reprend le verso de titre du
# manuscrit, mot pour mot pour les ISBN et le dépôt légal. Deux paragraphes :
# l’identification légale, puis le titre et le copyright. Le nom n’y figure
# qu’une fois, comme éditeur.
PIED = [
    ["<strong>Dépôt légal, Bibliothèque et Archives nationales du Québec, 2026</strong>",
     "ISBN 978-2-9825534-0-8 (Imprimé) · ISBN 978-2-9825534-1-5 (ePUB)"],
    ["<strong>Petit lexique vivant de l’intelligence artificielle</strong>",
     "© Stéphane Vial, éditeur · 2026",
     "Les textes de ce site sont sous licence "
     "<a href=\"https://creativecommons.org/licenses/by/4.0/deed.fr\">CC BY 4.0</a>, "
     "sauf mention contraire"],
]

# Le sélecteur de langue existe dans le code et ne sort dans aucune page tant
# que les éditions anglaise et espagnole ne sont pas parues. Un lien masqué
# reste un lien : les robots le suivaient jusqu’à une page introuvable. Il ne
# se supprime pas : il se publie en passant LANGUES_PUBLIEES à True, une fois
# les dossiers en/ et es/ en place.
LANGUES_PUBLIEES = False
LANGUES = [("fr", "Français", ""),
           ("en", "English", "en/"),
           ("es", "Español", "es/")]

ROBOTS = "index, follow, max-snippet:-1, max-image-preview:large"

# Le seul script du site, posé uniquement sur les pages qui portent une
# adresse de courriel. L’adresse est coupée dans le code par un fragment que
# le CSS masque ; le script la recolle à partir des seuls nœuds de texte, en
# ignorant le fragment, et en fait un lien mailto. Sans script, le texte
# reste lisible et copiable : rien n’est perdu. Aucune mesure, aucune requête.
SCRIPT = """  <script>
    document.querySelectorAll(".courriel").forEach(function (e) {
      var t = "";
      e.childNodes.forEach(function (n) { if (n.nodeType === 3) { t += n.textContent; } });
      var a = document.createElement("a");
      a.href = "mailto:" + t;
      a.textContent = t;
      e.replaceWith(a);
    });
  </script>"""

# Le second script, posé uniquement sur les pages qui portent une vidéo : un
# gros bouton de lecture par-dessus la vignette, pour qu’on comprenne qu’il
# faut cliquer. Il s’efface à la lecture et revient, avec la vignette, à la
# fin. Sans script, les commandes du navigateur suffisent. Que des guillemets
# doubles : l’apostrophe droite est interdite dans les pages.
SCRIPT_VIDEO = """  <script>
    document.querySelectorAll(".ecran").forEach(function (e) {
      var v = e.querySelector("video");
      var b = document.createElement("button");
      b.type = "button";
      b.className = "lecture-video";
      b.setAttribute("aria-label", "Lire la vidéo");
      e.appendChild(b);
      b.addEventListener("click", function () { v.play(); });
      v.addEventListener("play", function () { b.hidden = true; });
      v.addEventListener("ended", function () { v.load(); b.hidden = false; });
    });
  </script>"""

# La page de l’auteur. Partout ailleurs sur le site, son nom y mène. Sauf dans
# la ligne « Éditeur » de la notice de l’accueil : « Stéphane Vial, éditeur ·
# Montréal » y nomme la maison, pas la personne.
NOM = re.compile("Stéphane[ \u00a0]Vial"
                 "(?!,[ \u00a0]éditeur[ \u00a0]·[ \u00a0]Montréal)")

# La couverture figure sur toutes les pages : à côté du chapeau sur l’accueil,
# à droite du texte ailleurs, où elle ramène à l’accueil. Son texte de
# remplacement est celui déclaré dans contenu/accueil.md, lu au démarrage.
COUVERTURE_ALT = ""

# Les adresses ont perdu leur article le 8 septembre 2026 : « la-fabrique »
# est devenue « fabrique », « le-livre » est devenue « livre », notions
# comprises. Les anciennes adresses restent servies par une page de renvoi,
# hors sitemap et non indexée, pour qui les aurait notées. Le 19 septembre
# 2026, la page « Contact » est devenue « Acheter » : les liens d’achat en
# tête, le contact presse en bas. Le 20 septembre 2026, « Acheter » est devenue
# « Commander » : les deux anciennes adresses y renvoient.
RENVOIS = {
    "/lexique-ia/contact/": "/lexique-ia/commander/",
    "/lexique-ia/acheter/": "/lexique-ia/commander/",
    "/lexique-ia/la-fabrique/": "/lexique-ia/fabrique/",
    "/lexique-ia/le-livre/": "/lexique-ia/livre/",
}

RENVOI = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Cette page a changé d’adresse</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="%(vers)s">
  <meta http-equiv="refresh" content="0; url=%(vers)s">
</head>
<body>
  <p>Cette page a changé d’adresse : <a href="%(vers)s">%(vers)s</a></p>
</body>
</html>
"""



# ------------------------------------------------------- données structurées

GRAPHE_ACCUEIL = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Book",
      "@id": "https://web.stephane-vial.net/lexique-ia/#livre",
      "name": "Petit lexique vivant de l’intelligence artificielle",
      "inLanguage": "fr",
      "author": { "@id": "https://web.stephane-vial.net/lexique-ia/#auteur" },
      "contributor": {
        "@type": "Person",
        "name": "Marcello Vitali-Rosati",
        "jobTitle": "Professeur titulaire",
        "affiliation": { "@type": "CollegeOrUniversity", "name": "Université de Montréal" }
      },
      "publisher": { "@type": "Organization", "name": "Stéphane Vial, éditeur" },
      "datePublished": "2026-10-06",
      "numberOfPages": 138,
      "genre": "Ouvrage de référence",
      "about": [
        { "@type": "Thing", "name": "Intelligence artificielle" },
        { "@type": "Thing", "name": "Vulgarisation scientifique" }
      ],
      "abstract": "Ouvrage d’initiation à l’intelligence artificielle. Quatre-vingt-onze notions, une page chacune, organisées en huit chapitres. Chaque entrée suit la même structure : une définition, un exemple tiré d’usages ordinaires, et ce qui fait son importance.",
      "url": "https://web.stephane-vial.net/lexique-ia/",
      "workExample": [
        {
          "@type": "Book", "bookFormat": "https://schema.org/Paperback",
          "isbn": "978-2-9825534-0-8", "numberOfPages": 138,
          "inLanguage": "fr", "datePublished": "2026-10-06"
        },
        {
          "@type": "Book", "bookFormat": "https://schema.org/EBook",
          "isbn": "978-2-9825534-1-5",
          "inLanguage": "fr", "datePublished": "2026-10-06"
        }
      ]
    },
    {
      "@type": "Person",
      "@id": "https://web.stephane-vial.net/lexique-ia/#auteur",
      "name": "Stéphane Vial",
      "jobTitle": "Professeur titulaire",
      "affiliation": {
        "@type": "CollegeOrUniversity",
        "name": "Université du Québec à Montréal",
        "department": { "@type": "Organization", "name": "École de design" }
      },
      "url": "https://stephane-vial.net",
      "image": "https://web.stephane-vial.net/lexique-ia/img/portrait-stephane-vial.jpg",
      "knowsAbout": ["Design", "Intelligence artificielle", "Philosophie de la technique"]
    }
  ]
}"""

GRAPHE_PAGE = """{
  "@context": "https://schema.org",
  "@type": "%(type)s",
  "name": "%(nom)s",
  "url": "%(url)s",
  "inLanguage": "fr",
  "author": { "@id": "https://web.stephane-vial.net/lexique-ia/#auteur" },
  "%(relation)s": { "@id": "https://web.stephane-vial.net/lexique-ia/#livre" },
  "isPartOf": { "@type": "WebSite", "url": "https://web.stephane-vial.net/lexique-ia/" }
}"""


# ------------------------------------------------------------------ outils

def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return f.read()


def ecrire(chemin, texte):
    dossier = os.path.dirname(chemin)
    if dossier and not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


def entete_et_corps(texte):
    """Sépare l’en-tête YAML du corps Markdown."""
    if not texte.startswith("---"):
        raise ValueError("en-tête YAML absent")
    fin = texte.index("\n---", 3)
    return yaml.safe_load(texte[3:fin]), texte[fin + 4:].lstrip("\n")


def echapper(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def ancre(titre):
    """Un identifiant stable, tiré du titre. Sans accent, sans ponctuation."""
    t = re.sub(r"<[^>]+>", "", titre)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("’", " ").replace("'", " ")
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t


def poser_les_ancres(html):
    """Donne un identifiant à chaque H2 et H3, pour qu’on puisse pointer une
    section depuis l’extérieur."""
    def remplacer(m):
        return '<h%s id="%s">%s</h%s>' % (m.group(1), ancre(m.group(2)),
                                          m.group(2), m.group(1))
    return re.sub(r"<h([23])>(.*?)</h\1>", remplacer, html, flags=re.S)


def liens_externes(html):
    """Tout lien externe s’ouvre dans une nouvelle fenêtre. Les liens internes
    du site sont relatifs : un href absolu est toujours externe. rel=noopener
    coupe l’accès de la page ouverte à celle qui l’a ouverte."""
    return re.sub(r'<a href="(https?://[^"]+)"',
                  r'<a href="\1" target="_blank" rel="noopener"', html)


def video(meta, prefixe, telechargeable=True):
    """La vidéo que nomme l’en-tête (« video: token », le nom des fichiers de
    video/, sans extension), à la taille d’un reel, et le lien pour
    l’emporter, sauf sur l’accueil où il n’a pas d’utilité. Rien si l’en-tête
    n’en nomme pas."""
    if not meta.get("video"):
        return None
    libelle = meta.get("video_libelle") or "%s, la notion en vidéo" % meta["h1"]
    return (
        '        <figure class="couverture video">\n'
        '          <div class="ecran"><video controls playsinline '
        'preload="none" poster="%(f)s.jpg" width="320" height="569" '
        'aria-label="%(libelle)s">'
        '<source src="%(f)s.mp4" type="video/mp4"></video></div>\n'
        + ('          <figcaption><a href="%(f)s.mp4" download>'
           'Télécharger la vidéo</a></figcaption>\n' if telechargeable else "")
        + '        </figure>') % {"f": "%svideo/%s" % (prefixe, meta["video"]),
                               "libelle": echapper(libelle)}


def portrait(prefixe):
    """Le portrait de l’auteur et son crédit, tels que l’accueil les donne :
    ils ne s’écrivent qu’une fois, dans contenu/accueil.md."""
    corps = entete_et_corps(lire(os.path.join(CONTENU, "accueil.md")))[1]
    m = re.search(r"<figure>\n(.*?)\n</figure>", corps, flags=re.S)
    if not m:
        sys.exit("Le portrait de l’auteur est introuvable dans accueil.md.")
    interieur = m.group(1).replace('="img/', '="%simg/' % prefixe)
    # Sous le crédit, un lien vers l’image en pleine grandeur, celle que le
    # portrait ouvre déjà : il s’ouvre dans un nouvel onglet.
    grande = re.search(r'<a href="([^"]+)"', interieur).group(1)
    interieur = interieur.replace(
        "</figcaption>", '<br><a href="%s" target="_blank" rel="noopener">'
        'Télécharger la photo</a></figcaption>' % grande)
    return ('        <figure class="couverture portrait">\n          %s\n'
            '        </figure>' % interieur.replace("\n", "\n          "))


def cote(meta, prefixe, urls):
    """Ce qui occupe la droite du texte : la vidéo quand l’en-tête en nomme
    une, le portrait sur la page de l’auteur (« cote: portrait »), la
    couverture ailleurs."""
    if meta.get("video"):
        return video(meta, prefixe)
    if meta.get("cote") == "portrait":
        return portrait(prefixe)
    # La couverture ramène à l’accueil, sauf si l’en-tête de la page
    # nomme une autre destination : « couverture_vers: livre » sur la
    # page d’achat, où l’on va plutôt voir ce que le livre contient.
    href = (prefixe + urls[meta["couverture_vers"]][len(BASE):]
            if meta.get("couverture_vers") else prefixe)
    titre = (echapper(meta["couverture_titre"])
             if meta.get("couverture_vers") else "Retour à l’accueil")
    # Sur la page du livre (« couverture_telechargeable: oui »), sous
    # l’image, un lien vers la couverture en haute définition, dans le même
    # corps que « Télécharger la photo » sous le portrait : seuls les mots du
    # lien sont cliquables, le format et le poids suivent entre parenthèses.
    # Le poids se lit sur le fichier à chaque construction, jamais à la main.
    legende = ""
    if meta.get("couverture_telechargeable"):
        fichier = "img/couverture-hd.jpg"
        legende = ('          <figcaption><a href="%s%s" target="_blank" '
                   'rel="noopener">Télécharger la couverture</a> (JPG, %s)'
                   '</figcaption>\n'
                   % (prefixe, fichier,
                      poids(os.path.getsize(os.path.join(ICI, fichier)))))
    return (
        '        <figure class="couverture%s">\n'
        '          <a href="%s" title="%s"><img src="%simg/couverture.jpg" '
        'alt="%s" width="800" height="1280" loading="lazy"></a>\n'
        + legende +
        '        </figure>') % (" telechargeable" if legende else "", href,
                                titre, prefixe, echapper(COUVERTURE_ALT))


def poids(octets):
    """Un poids de fichier tel qu’on l’écrit en français : « 251 Ko »,
    « 1,2 Mo »."""
    if octets < 1000 * 1000:
        return "%d Ko" % round(octets / 1000)
    return ("%.1f Mo" % (octets / 1000 / 1000)).replace(".", ",")


def lier_le_nom(html, cible):
    """Fait du nom de l’auteur un lien vers sa page, partout où il se lit :
    dans le texte seulement, jamais dans un attribut ni dans un lien existant.
    Les sections « Pour citer » sont épargnées : une référence se copie, et
    un lien copié avec elle encombrerait la bibliographie de qui la colle."""
    morceaux = re.split(r"(?=<h2[ >])", html)
    for i, morceau in enumerate(morceaux):
        if morceau.startswith('<h2 id="pour-citer'):
            continue
        dans_un_lien, sortie_ = False, []
        for bout in re.split(r"(<[^>]+>)", morceau):
            if bout.startswith("<"):
                if re.match(r"<a[ >]", bout):
                    dans_un_lien = True
                elif bout.startswith("</a"):
                    dans_un_lien = False
            elif not dans_un_lien:
                bout = NOM.sub(lambda m: '<a href="%s">%s</a>'
                               % (cible, m.group(0)), bout)
            sortie_.append(bout)
        morceaux[i] = "".join(sortie_)
    return "".join(morceaux)


def sortie(url):
    """Le fichier à écrire, et de combien de crans il faut remonter pour
    atteindre la racine du lexique. « /lexique-ia/livre/token/ » donne
    « livre/token/index.html » et « ../../ »."""
    reste = url[len(BASE):].strip("/")
    profondeur = len(reste.split("/")) if reste else 0
    chemin = os.path.join(ICI, *(reste.split("/") if reste else []))
    return os.path.join(chemin, "index.html"), "../" * profondeur


# ------------------------------------------------------------- vérifications

def verifier(nom, corps, contenu, html):
    """Les trois exigences du cahier des charges, plus l’hygiène de balisage.
    Toute anomalie arrête la construction : une page fausse ne se publie pas.

    Le compte d’espaces insécables se fait sur le corps Markdown contre le
    corps converti, et non sur le fichier contre la page : le titre et la
    description sont écrits une fois dans l’en-tête et plusieurs fois dans le
    HTML, ce qui fausserait la comparaison sans rien prouver."""
    ennuis = []

    avant, apres = corps.count(NBSP), contenu.count(NBSP)
    if avant != apres:
        ennuis.append("espaces insécables : %d dans le corps Markdown, %d "
                      "après conversion. La conversion en a mangé ou en a "
                      "ajouté." % (avant, apres))

    for balise in ("<i>", "<i ", "<b>", "<b "):
        if balise in html:
            ennuis.append("balise %s présente : les italiques et les gras "
                          "doivent être des <em> et des <strong>." % balise)

    if len(re.findall(r"<h1[ >]", html)) != 1:
        ennuis.append("il faut exactement un H1 par page, il y en a %d."
                      % len(re.findall(r"<h1[ >]", html)))

    niveaux = [int(n) for n in re.findall(r"<h([1-6])[ >]", html)]
    for i in range(1, len(niveaux)):
        if niveaux[i] > niveaux[i - 1] + 1:
            ennuis.append("saut de niveau de titre : un H%d suit un H%d."
                          % (niveaux[i], niveaux[i - 1]))
            break

    if "épilogue" in html.lower() or "epilogue" in html.lower():
        ennuis.append("le mot « épilogue » figure dans la page. Il ne désigne "
                      "plus rien dans l’ouvrage et ne doit apparaître nulle "
                      "part.")

    if 'class="leurre"' in html and ".leurre { display: none; }" not in FEUILLE:
        ennuis.append("la page emploie le fragment anti-moissonnage mais "
                      "style.css ne le masque plus : l’adresse de contact "
                      "s’afficherait cassée.")

    if "'" in html:
        ennuis.append("apostrophe droite dans la page. Le site emploie "
                      "l’apostrophe courbe partout, comme le livre.")

    for hote in re.findall(r'(?:src|href)="https?://([^/"]+)', html):
        if hote.endswith("stephane-vial.net"):
            continue
        if not re.search(r'<a [^>]*href="https?://%s' % re.escape(hote), html):
            ennuis.append("ressource chargée depuis un tiers : %s. Aucune "
                          "requête ne doit sortir du domaine." % hote)

    if ennuis:
        for e in ennuis:
            sys.stderr.write("  ✗ %s : %s\n" % (nom, e))
        sys.exit("Construction interrompue. Rien n’a été publié.")


# ------------------------------------------------------------- construction

def page_suivante(nom):
    """Le chevron du pied mène à la page suivante du menu ; après la dernière,
    il ramène à l’accueil. Une notion, hors menu, envoie à la page qui suit
    « Le livre », d’où l’on y est arrivé."""
    i = MENU.index(nom) if nom in MENU else MENU.index("livre")
    return MENU[(i + 1) % len(MENU)]


def navigation(prefixe, courante, urls):
    entrees = []
    for nom in MENU:
        # Sur l'accueil, l'entrée qui y renvoie vaudrait href="" : un href
        # vide pointe sur le document courant, requête comprise. « ./ » dit
        # la même chose sans ambiguïté.
        cible = prefixe + urls[nom][len(BASE):] or "./"
        marque = ' aria-current="page"' if nom == courante else ""
        if nom == MENU_BOUTON:
            marque = ' class="bouton"' + marque
        entrees.append('<a href="%s"%s>%s</a>'
                       % (cible, marque, MENU_LIBELLE[nom]))
    return "\n      ".join(entrees)


def selecteur_de_langue(prefixe):
    """Présent dans le code, absent des pages tant que LANGUES_PUBLIEES est
    faux : ni trace visible, ni lien à suivre pour un robot."""
    if not LANGUES_PUBLIEES:
        return ""
    liens = ['<a href="%s%s" lang="%s"%s>%s</a>'
             % (prefixe, chemin, code,
                ' aria-current="true"' if not chemin else "", libelle)
             for code, libelle, chemin in LANGUES]
    return ('<nav class="langues" aria-label="Langue">\n      %s\n'
            '    </nav>' % "\n      ".join(liens))


def folio(meta):
    """Le numéro de page d’une notion, à la suite du chapitre dans le chapeau
    et dans la même graisse : chapitre et page localisent l’entrée ensemble,
    face au terme anglais en italique. Il vient du champ « page » de
    l’en-tête, obligatoire pour une notion."""
    if meta.get("gabarit") != "notion":
        return ""
    if not meta.get("page"):
        sys.exit("%s : il manque le champ « page » dans l’en-tête."
                 % meta["url"])
    return '<span class="folio"> · page %s</span>' % meta["page"]


def construire(nom, fichier, base, gabarits, urls):
    source = lire(fichier)
    meta, corps = entete_et_corps(source)
    adresse = meta["url"]
    cible, prefixe = sortie(adresse)

    # Conversion Markdown. « tables » compose l’état civil de l’ouvrage et ne
    # touche à aucun caractère. Aucune extension de substitution
    # typographique : « smarty » n’est pas chargée, et ne doit jamais l’être.
    # « md_in_html » permet à l’accueil d’envelopper la section de l’auteur
    # dans un <div markdown="1"> pour la composer en deux colonnes.
    md = markdown.Markdown(extensions=["tables", "md_in_html"],
                           output_format="html")
    contenu = poser_les_ancres(md.convert(corps))

    # Les chemins d’images de contenu/ sont relatifs à /lexique-ia/.
    if prefixe:
        contenu = contenu.replace('src="img/', 'src="%simg/' % prefixe)

    gabarit = meta.get("gabarit", "page")
    if gabarit == "accueil":
        # Le chapeau, c’est tout ce qui précède le premier H2. Son premier
        # paragraphe est le seul endroit du site où le corps est plus gros.
        coupe = contenu.find("<h2")
        chapeau, contenu = contenu[:coupe], contenu[coupe:]
        # Le gabarit l’enveloppe dans .entree, à côté de la couverture.
        corps_html = gabarits["accueil"] % {
            "h1": echapper(meta["h1"]),
            "auteur": echapper(meta["auteur"]),
            "attribution": echapper(meta["attribution"]),
            "chapeau": chapeau.strip(),
            "contenu": contenu.strip(),
            # La vidéo d’annonce, ou à défaut la couverture, qui s’ouvre en
            # grand.
            "cote": video(meta, prefixe, telechargeable=False) or (
                '        <figure class="couverture">\n'
                '          <a href="%s" target="_blank" rel="noopener" '
                'title="Ouvrir la couverture en grand"><img src="%s" alt="%s" '
                'width="800" height="1280"></a>\n        </figure>'
                % (meta["couverture_lien"], meta["couverture"],
                   echapper(meta["couverture_alt"]))),
        }
    else:
        corps_html = gabarits["page"] % {
            # La classe dit ce qu'est la page, pas quel gabarit l'a produite :
            # « page » ne veut rien dire dans une feuille de style.
            "classe": "notion" if gabarit == "notion" else "document",
            "h1": echapper(meta["h1"]),
            # Le chapeau passe par le convertisseur, sans extension : il peut
            # porter un italique (le terme anglais d’une notion), rien d’autre.
            "chapeau": ('<p class="chapeau">%s%s</p>' % (re.sub(
                            r"^<p>|</p>$", "",
                            markdown.Markdown(output_format="html")
                            .convert(meta["chapeau"]).strip()), folio(meta))
                        if meta.get("chapeau") else ""),
            "ancre": ' id="texte"' if meta.get("ancre_texte") else "",
            "cote": cote(meta, prefixe, urls),
            "contenu": contenu.strip(),
        }

    # Le nom de l’auteur mène à sa page, sauf sur celle-ci.
    pied = "\n      ".join("<p>%s</p>" % "<br>\n      ".join(g) for g in PIED)
    if nom != "auteur":
        vers = prefixe + urls["auteur"][len(BASE):]
        corps_html, pied = lier_le_nom(corps_html, vers), lier_le_nom(pied, vers)

    url = DOMAINE + adresse
    if nom == "accueil":
        donnees = GRAPHE_ACCUEIL
    else:
        donnees = GRAPHE_PAGE % {
            "type": "DefinedTerm" if gabarit == "notion" else "WebPage",
            "nom": meta["h1"], "url": url,
            "relation": "mainEntity" if nom == "livre" else "inDefinedTermSet"
            if gabarit == "notion" else "about",
        }

    og = [
        ("og:type", meta.get("og_type", "article")),
        ("og:locale", "fr_CA"),
        ("og:title", meta["h1"]),
        ("og:description", meta["description"]),
        ("og:url", url),
        ("og:image", DOMAINE + BASE + "img/couverture.jpg"),
    ]

    page = base % {
        "avertissement": AVERTISSEMENT % os.path.relpath(
            fichier, CONTENU)[:-3],
        "titre": echapper(meta["title"]),
        "description": echapper(meta["description"]),
        "canonique": url,
        "prefixe": prefixe,
        "page": nom,
        "og": "\n  ".join('<meta property="%s" content="%s">'
                          % (k, echapper(v)) for k, v in og),
        "donnees": donnees,
        "robots": ROBOTS,
        "navigation": navigation(prefixe, nom, urls),
        "suivante": prefixe + urls[page_suivante(nom)][len(BASE):] or "./",
        "suivante_libelle": MENU_LIBELLE[page_suivante(nom)],
        "langues": selecteur_de_langue(prefixe),
        "corps": corps_html,
        "pied": pied,
        "script": "\n".join(s for s, signe in ((SCRIPT, 'class="courriel"'),
                                               (SCRIPT_VIDEO, "<video"))
                            if signe in corps_html),
    }

    page = liens_externes(page)
    verifier(nom, corps, contenu, page)
    ecrire(cible, page)
    return os.path.relpath(cible, ICI), adresse


def inventaire():
    """Les fichiers de contenu, dans l’ordre du site : les quatre pages
    principales, puis les huit notions, dans l’ordre des chapitres."""
    pages = [(n, os.path.join(CONTENU, n + ".md")) for n in MENU]
    dossier = os.path.join(CONTENU, "notions")
    if os.path.isdir(dossier):
        notions = []
        for f in sorted(os.listdir(dossier)):
            if not f.endswith(".md"):
                continue
            chemin = os.path.join(dossier, f)
            meta, _ = entete_et_corps(lire(chemin))
            notions.append((meta.get("ordre", 99), f[:-3], chemin))
        pages += [(n, c) for _, n, c in sorted(notions)]
    return pages


# ------------------------------------------------- pour les assistants d’IA

POUR_CITER = "## Pour citer ce texte"


def a_plat(texte):
    """Les fichiers lus par des machines portent des espaces ordinaires : une
    insécable y gêne la recherche d’une expression sans rien apporter."""
    return texte.replace(NBSP, " ").replace(" ", " ")


def section(corps, titre, fichier):
    """Le texte d’une section de niveau 2, sans son titre. Un titre renommé
    dans contenu/ arrête la construction au lieu de vider llms.txt."""
    m = re.search(r"^## %s[ \t]*\n(.*?)(?=^## |\Z)" % re.escape(titre), corps,
                  flags=re.M | re.S)
    if not m:
        sys.exit("llms.txt : la section « %s » est introuvable dans %s."
                 % (titre, fichier))
    return m.group(1).strip()


def en_markdown(corps, adresse):
    """Un corps de contenu/ ramené à du Markdown nu, pour un lecteur qui ne
    rend pas le HTML : liens absolus, plus aucune balise. L’adresse de courriel
    n’est jamais recopiée : elle est coupée exprès sur le site, contre les
    moissonneurs, et reste à lire sur la page d’achat, section « Presse »."""
    t = re.sub(r"<figure>.*?</figure>", "", corps, flags=re.S)
    t = re.sub(r'<span class="courriel">.*?</span>[^<]*</span>',
               "adresse publiée sur %s%scommander/" % (DOMAINE, BASE), t,
               flags=re.S)
    t = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", t, flags=re.S)
    t = re.sub(r"</?em>", "*", t)
    t = re.sub(r"<[^>]+>", "", t)

    def absolu(m):
        cible = m.group(1)
        if re.match(r"[a-z]+:|#", cible):
            return m.group(0)
        return "](%s)" % urljoin(DOMAINE + adresse, cible)
    t = re.sub(r"\]\(([^)\s]+)\)", absolu, t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def chapitres(corps):
    """Les huit chapitres de contenu/livre.md : titre et liste des notions.
    Le compte est contrôlé : le livre en annonce quatre-vingt-onze."""
    sortie_ = []
    for bloc in re.split(r"^### ", corps, flags=re.M)[1:]:
        lignes = [l.strip() for l in bloc.split("\n") if l.strip()]
        notions = [n.strip() for n in lignes[2].split(" · ")]
        sortie_.append((lignes[0], notions))
    total = sum(len(n) for _, n in sortie_)
    if total != 91:
        sys.exit("llms.txt : %d notions relevées dans contenu/livre.md, il en "
                 "faut 91." % total)
    return sortie_


def premiere_phrase(corps, fichier):
    """La première phrase de la définition d’une notion. La description de
    l’en-tête, taillée pour les moteurs, s’arrête au milieu d’une phrase."""
    m = re.search(r"\*\*Définition\*\*\s*\n(.+?)(?:\n\s*\n|\Z)", corps,
                  flags=re.S)
    if not m:
        sys.exit("llms.txt : pas de définition dans %s." % fichier)
    paragraphe = " ".join(m.group(1).split())
    p = re.match(r"(.+?[.!?])(?=\s+[A-ZÀ-ÖØ-Þ«]|$)", paragraphe)
    return p.group(1) if p else paragraphe


def llms(pages):
    """Écrit les deux fichiers destinés aux assistants d’IA.

    llms.txt, la carte : un titre, un résumé en citation, l’état civil de
    l’ouvrage, l’auteur, les 91 notions par chapitre, où se procurer le livre,
    puis des listes de liens commentés (format llms.txt). Il est écrit deux
    fois, à l’identique : dans /lexique-ia/, et à la racine du sous-domaine,
    où les outils le cherchent d’office. Ses liens sont absolus.

    llms-full.txt, le texte intégral des pages, en Markdown nu, à la suite.

    Tout vient de contenu/ : en-têtes et corps. Ne sont écrits ici que les
    intitulés et les phrases de liaison. Les éditions à paraître n’y figurent
    pas."""
    lus = [(nom, fichier) + entete_et_corps(lire(fichier))
           for nom, fichier in pages]
    corps_de = dict((nom, corps) for nom, _, _, corps in lus)
    accueil = entete_et_corps(lire(os.path.join(CONTENU, "accueil.md")))[0]
    racine = DOMAINE + BASE

    principales, notions = [], []
    for nom, fichier, meta, corps in lus:
        if meta.get("gabarit") == "notion":
            chapeau = "%s · page %s" % (
                re.sub(r"\*([^*]+)\*", r"\1", meta.get("chapeau", "")),
                meta["page"])
            notions.append("- [%s](%s): %s. %s"
                           % (meta["h1"], DOMAINE + meta["url"], chapeau,
                              premiere_phrase(corps, fichier)))
        else:
            principales.append("- [%s](%s): %s" % (meta["h1"],
                                                   DOMAINE + meta["url"],
                                                   meta["description"]))

    licence = ("Un livre de %s. %s. ISBN 978-2-9825534-0-8 (imprimé) et "
               "978-2-9825534-1-5 (ePUB). © Stéphane Vial, éditeur, 2026. Les "
               "textes de ce site sont sous licence CC BY 4.0, sauf mention "
               "contraire."
               % (accueil["auteur"], accueil["attribution"].replace(" · ", ". ")))

    # L’état civil : le tableau de l’accueil, une ligne par renseignement.
    ouvrage = []
    for ligne in section(corps_de["accueil"], "L’ouvrage",
                         "accueil.md").split("\n"):
        cases = [c.strip() for c in ligne.strip().strip("|").split("|")]
        if len(cases) == 2 and cases[0].startswith("**"):
            ouvrage.append("- %s : %s" % (cases[0].strip("*"), cases[1]))

    livre = chapitres(corps_de["livre"])
    optionnel = ["- [Plan du site](%s/sitemap.xml): toutes les adresses, au "
                 "format sitemap." % DOMAINE]
    for cible, libelle in re.findall(r'<a href="([^"]+\.pdf)"[^>]*>(.*?)</a>',
                                     corps_de["communique"]):
        optionnel.append("- [%s](%s): le communiqué de parution, mis en page."
                         % (libelle, urljoin(racine + "communique/", cible)))
    optionnel.append("- [Couverture en haute définition](%s): %s."
                     % (racine + accueil["couverture_lien"],
                        accueil["couverture_alt"]))
    portrait = re.search(r'<figure>.*?<a href="([^"]+)".*?<figcaption>(.*?)'
                         r'</figcaption>', corps_de["accueil"], flags=re.S)
    if portrait:
        optionnel.append("- [Portrait de l’auteur en haute définition](%s): %s."
                         % (racine + portrait.group(1), portrait.group(2)))

    carte = a_plat("\n".join([
        "# " + accueil["h1"],
        "",
        "> " + accueil["description"],
        "",
        licence + " Les pages qui portent une section « Pour citer ce texte » "
        "donnent la référence à employer.",
        "",
        "**L’ouvrage**",
        "",
    ] + ouvrage + [
        "",
        "**L’auteur**",
        "",
        en_markdown(section(corps_de["accueil"], "L’auteur", "accueil.md"),
                    BASE),
        "",
        "**Se procurer le livre**",
        "",
        en_markdown(section(corps_de["accueil"], "Se procurer le livre",
                            "accueil.md"), BASE),
        "",
        "**Les 91 notions, en huit chapitres**",
        "",
    ] + ["- **%s** (%d notions) : %s" % (titre, len(liste), " · ".join(liste))
         for titre, liste in livre] + [
        "",
        "## Le livre et son auteur",
        "",
    ] + principales + [
        "",
        "## Huit notions à lire, une par chapitre",
        "",
    ] + notions + [
        "",
        "## Texte intégral",
        "",
        "- [Tout le site en un seul fichier](%sllms-full.txt): le texte des "
        "%d pages, en Markdown, à la suite." % (racine, len(lus)),
        "",
        "## Optional",
        "",
    ] + optionnel + [
        "",
    ]))

    # Le texte intégral. Les titres de chaque page descendent d’un cran, sous
    # le titre de la page.
    blocs = []
    for nom, fichier, meta, corps in lus:
        texte = re.sub(r"^(#{2,5}) ", r"#\1 ",
                       en_markdown(corps, meta["url"]), flags=re.M)
        tete = ["## " + meta["h1"], "", "Adresse : " + DOMAINE + meta["url"]]
        if nom == "accueil":
            tete += ["", "%s · %s" % (meta["auteur"], meta["attribution"])]
        elif meta.get("chapeau"):
            tete += ["", meta["chapeau"] + (" · page %s" % meta["page"]
                                            if meta.get("page") else "")]
        blocs.append("\n".join(tete + ["", texte]))
    integral = a_plat("\n".join([
        "# %s : texte intégral du site" % accueil["h1"],
        "",
        "> " + accueil["description"],
        "",
        licence,
        "",
        "Ce fichier réunit le texte des %d pages du site : les sept pages du "
        "menu, puis les huit notions données à lire, dans l’ordre des "
        "chapitres. La carte commentée du site est dans %sllms.txt."
        % (len(lus), racine),
        "",
        "---",
        "",
        "",
    ]) + "\n\n---\n\n".join(blocs) + "\n")

    ecrire(os.path.join(ICI, "llms.txt"), carte)
    ecrire(os.path.join(RACINE, "llms.txt"), carte)
    ecrire(os.path.join(ICI, "llms-full.txt"), integral)
    return len(principales) + len(notions)


def sitemap(urls):
    """Régénère ../sitemap.xml. Toute adresse déjà présente qui ne relève pas
    de /lexique-ia/ est conservée : ce fichier sert tout le sous-domaine."""
    chemin = os.path.join(RACINE, "sitemap.xml")
    gardees = []
    if os.path.exists(chemin):
        for u in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", lire(chemin)):
            if BASE not in u:
                gardees.append(u)
    toutes = gardees + [DOMAINE + u for u in urls]
    corps = "\n".join("  <url><loc>%s</loc></url>" % echapper(u)
                      for u in toutes)
    ecrire(chemin,
           '<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '%s\n</urlset>\n' % corps)
    return chemin, len(toutes)


def main():
    global FEUILLE
    FEUILLE = lire(os.path.join(ICI, "style.css"))
    base = lire(os.path.join(GABARIT, "base.html"))
    gabarits = {"accueil": lire(os.path.join(GABARIT, "accueil.html")),
                "page": lire(os.path.join(GABARIT, "page.html"))}

    global COUVERTURE_ALT
    COUVERTURE_ALT = entete_et_corps(lire(os.path.join(CONTENU, "accueil.md")))[0]["couverture_alt"]

    # Les liens d’achat figurent deux fois, sur l’accueil et sur la page
    # « Commander » : les deux listes doivent rester les mêmes.
    boutiques = [sorted(set(re.findall(r"https://www\.amazon\.[a-z.]+/(?:[^\s\"()]*/)?dp/\w+",
                                       lire(os.path.join(CONTENU, f)))))
                 for f in ("accueil.md", "commander.md")]
    if boutiques[0] != boutiques[1]:
        sys.exit("Les liens Amazon de contenu/accueil.md et de "
                 "contenu/commander.md ne sont plus les mêmes : %s"
                 % ", ".join(sorted(set(boutiques[0]) ^ set(boutiques[1]))))

    # La biographie figure deux fois, sur l’accueil et sur la page de
    # l’auteur : les deux textes doivent rester les mêmes, au mot et à
    # l’insécable près. Le découpage en paragraphes n’est pas comparé : la
    # page de l’auteur en fait un de plus que l’accueil.
    def biographie(texte):
        t = re.sub(r"<figure>.*?</figure>|</?div[^>]*>", "", texte, flags=re.S)
        return re.sub(r"[ \n]+", " ", t).strip()
    accueil_md = entete_et_corps(lire(os.path.join(CONTENU, "accueil.md")))[1]
    auteur_md = entete_et_corps(lire(os.path.join(CONTENU, "auteur.md")))[1]
    if biographie(section(accueil_md, "L’auteur", "accueil.md")) != biographie(auteur_md):
        sys.exit("La biographie de contenu/auteur.md n’est plus celle de la "
                 "section « L’auteur » de contenu/accueil.md : corriger les "
                 "deux.")

    pages = inventaire()
    urls = {}
    for nom, fichier in pages:
        meta, _ = entete_et_corps(lire(fichier))
        urls[nom] = meta["url"]

    liste = []
    for nom, fichier in pages:
        cible, url = construire(nom, fichier, base, gabarits, urls)
        liste.append(url)
        print("  ✓ %-34s %s" % (cible, url))


    # Les pages de renvoi depuis les anciennes adresses.
    for u in liste:
        for ancien, nouveau in RENVOIS.items():
            if u.startswith(nouveau):
                vieux = ancien + u[len(nouveau):]
                cible, _ = sortie(vieux)
                ecrire(cible, RENVOI % {"vers": DOMAINE + u})
                print("  → %-34s renvoie vers %s" % (os.path.relpath(cible, ICI), u))

    chemin, n = sitemap(liste)
    print("  ✓ %-34s %d adresses" % (os.path.relpath(chemin, ICI), n))
    n = llms(pages)
    for f in ("llms.txt", "../llms.txt", "llms-full.txt"):
        print("  ✓ %-34s %d pages" % (f, n))
    print("\n%d pages construites. Aucune requête ne sort du domaine."
          % len(liste))


if __name__ == "__main__":
    main()
