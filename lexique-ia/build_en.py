#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_en.py — le site de l’édition anglaise, dans en/ : le site français
entier, page pour page, mutatis mutandis.

    python3 build.py           (construit le français, puis appelle ce script)
    python3 build_en.py        (l’anglais seul)

Sept pages au menu (Home, The book, The making, The statement, Press release,
The author, Order) et huit extraits sous book/, comme le site français.
Chaque page reprend la mise en page de sa page française : mêmes gabarits,
même feuille de style, mêmes sections dans le même ordre. Changent : la
langue, la couverture, la couleur (le fond de la couverture anglaise, posé
par style.css sur html[lang="en"]), les boutiques (pays anglophones d’abord)
et, seule vraie différence de contenu, les extraits : ils portent la
couverture, pas de vidéo. La vidéo d’annonce en version anglaise reste sur
l’accueil.

Sources dans contenu/en/. Les textes tirés du livre (extraits, chapitres,
fabrique, déclaration) sont ceux du manuscrit anglais révisé, mot pour mot :
ils ne se retouchent pas ici.

Écrit aussi en/llms.txt et en/llms-full.txt, et ajoute les adresses anglaises
à ../sitemap.xml.
"""
import os
import re
import sys

import markdown

import build as fr

ICI = fr.ICI
CONTENU = os.path.join(fr.CONTENU, "en")
BASE = "/lexique-ia/en/"

# L’ASIN de l’édition anglaise, tel qu’Amazon l’affiche sur la fiche du livre.
# Vide : les pages annoncent la date sans lien d’achat. Ne jamais le deviner.
ASIN = "B0HLWQDMZX"   # donné par Stéphane le 4 octobre 2026 (liens amazon.com/dp/…)
# Les quatre boutiques des pays anglophones, en boutons ; les autres en ligne.
BOUTIQUES = [("United States", "Amazon.com", "https://www.amazon.com/dp/%s"),
             ("United Kingdom", "Amazon.co.uk", "https://www.amazon.co.uk/dp/%s"),
             ("Canada", "Amazon.ca", "https://www.amazon.ca/dp/%s"),
             ("Australia", "Amazon.com.au", "https://www.amazon.com.au/dp/%s")]
AUTRES = ["amazon.de", "amazon.fr", "amazon.es", "amazon.it", "amazon.nl",
          "amazon.co.jp", "amazon.com.br", "amazon.com.mx", "amazon.in"]

# Les pages, dans l’ordre du menu : nom anglais (celui du fichier de
# contenu/en/), libellé du menu, et nom de la page française miroir, qui sert
# aussi d’attribut data-page : la feuille de style compose « livre » et
# « commander » d’après lui.
MENU = [("home", "Home", "accueil"), ("book", "The book", "livre"),
        ("making-of", "The making", "fabrique"),
        ("statement", "The statement", "declaration"),
        ("press-release", "Press release", "communique"),
        ("author", "The author", "auteur"), ("order", "Order", "commander")]
LIBELLE = dict((n, l) for n, l, _ in MENU)
MIROIR = dict((n, f) for n, _, f in MENU)
# Les huit extraits et leur notion française.
EXTRAITS = {"artificial-intelligence": "intelligence-artificielle",
            "neuron": "neurone", "machine-learning": "apprentissage-automatique",
            "natural-language-processing": "traitement-du-langage-naturel",
            "token": "token", "hallucination": "hallucination",
            "recommender-system": "systeme-de-recommandation",
            "agentic-ai": "ia-agentique"}
# L’adresse de la page française miroir, sous /lexique-ia/ : le lien « FR » du
# menu y mène. build.py porte la table inverse (VERS_ANGLAIS).
VERS_FRANCAIS = {"home": "", "book": "livre/", "making-of": "fabrique/",
                 "statement": "declaration/", "press-release": "communique/",
                 "author": "auteur/", "order": "commander/"}
VERS_FRANCAIS.update((e, "livre/%s/" % f) for e, f in EXTRAITS.items())

# L’extrait a d’abord été publié à en/hallucination/, le 4 octobre 2026.
RENVOIS = {"hallucination/": "book/hallucination/"}
RENVOI = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>This page has moved</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="%(vers)s">
  <meta http-equiv="refresh" content="0; url=%(vers)s">
</head>
<body>
  <p>This page has moved: <a href="%(vers)s">%(vers)s</a></p>
</body>
</html>
"""

IDENTIFIANTS = {"three-things-to-read-on-this-site": "trois-choses-a-lire-sur-ce-site",
                "the-author": "l-auteur", "order-the-book": "se-procurer-le-livre",
                "the-book": "l-ouvrage"}

COUVERTURE = "img/cover-en.jpg"
COUVERTURE_HD = "img/cover-en-hd.jpg"
CITER = "how-to-cite-this-text"

PIED = [
    ["<strong>Dépôt légal, Bibliothèque et Archives nationales du Québec, 2026</strong>",
     "ISBN 978-2-9825534-2-2 (Print) · ISBN 978-2-9825534-3-9 (ePUB)"],
    ["<strong>A Living Lexicon of Artificial Intelligence</strong>",
     "© Stéphane Vial, publisher · 2026",
     "Texts on this site are licensed under "
     "<a href=\"https://creativecommons.org/licenses/by/4.0/\">CC BY 4.0</a>, "
     "unless otherwise noted"],
]

GRAPHE_ACCUEIL = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Book",
      "@id": "https://web.stephane-vial.net/lexique-ia/en/#book",
      "name": "A Living Lexicon of Artificial Intelligence",
      "inLanguage": "en",
      "author": { "@id": "https://web.stephane-vial.net/lexique-ia/en/#author" },
      "contributor": {
        "@type": "Person",
        "name": "Marcello Vitali-Rosati",
        "jobTitle": "Full Professor",
        "affiliation": { "@type": "CollegeOrUniversity", "name": "Université de Montréal" }
      },
      "publisher": { "@type": "Organization", "name": "Stéphane Vial, publisher" },
      "datePublished": "2026-10-13",
      "numberOfPages": 138,
      "genre": "Reference work",
      "about": [
        { "@type": "Thing", "name": "Artificial intelligence" },
        { "@type": "Thing", "name": "Popular science" }
      ],
      "abstract": "An introduction to artificial intelligence. Ninety-one concepts, organized into eight chapters. Each entry follows the same structure: a definition, a concrete example, and a reflection on why it matters.",
      "url": "https://web.stephane-vial.net/lexique-ia/en/",
      "translationOfWork": { "@id": "https://web.stephane-vial.net/lexique-ia/#livre" },
      "workExample": [
        {
          "@type": "Book", "bookFormat": "https://schema.org/Paperback",
          "isbn": "978-2-9825534-2-2", "numberOfPages": 138,
          "inLanguage": "en", "datePublished": "2026-10-13"
        },
        {
          "@type": "Book", "bookFormat": "https://schema.org/EBook",
          "isbn": "978-2-9825534-3-9",
          "inLanguage": "en", "datePublished": "2026-10-13"
        }
      ]
    },
    {
      "@type": "Person",
      "@id": "https://web.stephane-vial.net/lexique-ia/en/#author",
      "name": "Stéphane Vial",
      "jobTitle": "Full Professor",
      "affiliation": {
        "@type": "CollegeOrUniversity",
        "name": "Université du Québec à Montréal",
        "department": { "@type": "Organization", "name": "School of Design" }
      },
      "url": "https://stephane-vial.net",
      "image": "https://web.stephane-vial.net/lexique-ia/img/portrait-stephane-vial.jpg",
      "knowsAbout": ["Design", "Artificial intelligence", "Philosophy of technology"]
    }
  ]
}"""

GRAPHE_PAGE = """{
  "@context": "https://schema.org",
  "@type": "%(type)s",
  "name": "%(nom)s",
  "url": "%(url)s",
  "inLanguage": "en",
  "author": { "@id": "https://web.stephane-vial.net/lexique-ia/en/#author" },
  "%(relation)s": { "@id": "https://web.stephane-vial.net/lexique-ia/en/#book" },
  "isPartOf": { "@type": "WebSite", "url": "https://web.stephane-vial.net/lexique-ia/en/" }
}"""

# Le nom de l’auteur mène à sa page, sauf dans la ligne « Publisher » de la
# notice, qui nomme la maison : même règle que sur le site français.
NOM = re.compile("Stéphane[  ]Vial(?!,[  ]publisher)")


def boutiques():
    if not ASIN:
        return ("Order links will be posted here on publication day, "
                "October 13, 2026.")
    return "\n".join('- **%s**  \n  <a href="%s" class="commander">Order on %s</a>'
                     % (pays, lien % ASIN, nom) for pays, nom, lien in BOUTIQUES)


def autres():
    """Les autres boutiques, en une ligne, comme sur le site français."""
    if not ASIN:
        return ""
    return "The book is also available on: %s." % " · ".join(
        "[%s](https://www.%s/dp/%s)" % (b, b, ASIN) for b in AUTRES)


def chemin_de(nom):
    return os.path.join(CONTENU, "entries" if nom in EXTRAITS else "", nom + ".md")


def source(nom):
    """L’en-tête et le corps d’une page, liens d’achat posés."""
    meta, corps = fr.entete_et_corps(fr.lire(chemin_de(nom)))
    for cle, valeur in (
            ("boutiques", boutiques()), ("autres", autres()),
            ("autres_liste", "- **Other countries**  \n  " + autres() if ASIN else ""),
            ("diffusion", " · ".join("[%s](%s)" % (n.lower(), l % ASIN)
                                     for _, n, l in BOUTIQUES) if ASIN else "Amazon")):
        corps = corps.replace("%%(%s)s" % cle, valeur)
    return meta, corps


def poids(chemin):
    octets = os.path.getsize(os.path.join(ICI, chemin))
    if octets < 1000 * 1000:
        return "%d KB" % round(octets / 1000)
    return "%.1f MB" % (octets / 1000 / 1000)


def legende(racine):
    return ('<figcaption><a href="%s%s" target="_blank" rel="noopener">'
            'Download the cover</a> (JPG, %s)</figcaption>\n'
            % (racine, COUVERTURE_HD, poids(COUVERTURE_HD)))


def cote(meta, racine, en, alt):
    """La droite du texte : le portrait sur la page de l’auteur, la couverture
    ailleurs. Elle ramène à l’accueil, mène à la page du livre depuis « Order »,
    et s’ouvre en grand, avec son lien de téléchargement, là où la page
    française la donne à télécharger. Jamais de vidéo sur un extrait."""
    if meta.get("cote") == "portrait":
        return portrait(racine)
    telechargeable = bool(meta.get("couverture_telechargeable"))
    if telechargeable:
        href, titre = racine + COUVERTURE_HD, "Open the cover at full size"
    elif meta.get("couverture_vers"):
        href, titre = en + meta["couverture_vers"] + "/", fr.echapper(meta["couverture_titre"])
    else:
        href, titre = en or "./", "Back to the home page"
    return ('        <figure class="couverture%s">\n'
            '          <a href="%s"%s title="%s"><img src="%s%s" alt="%s" '
            'width="800" height="1280" loading="lazy"></a>\n%s        </figure>'
            % (" telechargeable" if telechargeable else "", href,
               ' target="_blank" rel="noopener"' if telechargeable else "",
               titre, racine, COUVERTURE, fr.echapper(alt),
               "          " + legende(racine) if telechargeable else ""))


def couverture_de_l_ouvrage(contenu, racine, alt):
    """La couverture en regard du tableau « The book », comme sur l’accueil
    français, avec son lien de téléchargement."""
    figure = (
        '<div class="ouvrage">\n'
        '<figure class="couverture telechargeable">\n'
        '  <a href="%(r)s%(hd)s" target="_blank" rel="noopener" '
        'title="Open the cover at full size"><img src="%(r)s%(c)s" '
        'alt="%(alt)s" width="800" height="1280" loading="lazy"></a>\n'
        '%(legende)s</figure>\n'
        % {"r": racine, "hd": COUVERTURE_HD, "c": COUVERTURE,
           "alt": fr.echapper(alt), "legende": legende(racine)})
    nouveau, n = re.subn(r'(<h2 id="l-ouvrage">[^\n]*</h2>\n)(<table>.*?</table>)',
                         lambda m: m.group(1) + figure + m.group(2) + "\n</div>",
                         contenu, count=1, flags=re.S)
    if n != 1:
        sys.exit("en : le tableau « The book » est introuvable sur l’accueil.")
    return nouveau


def portrait(racine):
    """Le portrait et son crédit, tels que l’accueil anglais les donne."""
    corps = source("home")[1]
    m = re.search(r"<figure>\n(.*?)\n</figure>", corps, flags=re.S)
    if not m:
        sys.exit("en : le portrait de l’auteur est introuvable dans home.md.")
    interieur = m.group(1).replace('="img/', '="%simg/' % racine)
    grande = re.search(r'<a href="([^"]+)"', interieur).group(1)
    interieur = interieur.replace(
        "</figcaption>", '<br><a href="%s" target="_blank" rel="noopener">'
        'Download the photo</a></figcaption>' % grande)
    return ('        <figure class="couverture portrait">\n          %s\n'
            '        </figure>' % interieur.replace("\n", "\n          "))


def lier_le_nom(html, cible):
    """Comme sur le site français : le nom mène à la page de l’auteur, dans le
    texte seulement, et jamais dans la section « How to cite this text »."""
    morceaux = re.split(r"(?=<h2[ >])", html)
    for i, morceau in enumerate(morceaux):
        if morceau.startswith('<h2 id="%s' % CITER):
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


def construire(nom, base, gabarits, alt):
    meta, corps = source(nom)
    adresse = meta["url"]
    reste = adresse[len(BASE):].strip("/")
    en = "../" * len(reste.split("/")) if reste else ""   # vers l’accueil anglais
    racine = en + "../"                  # vers /lexique-ia/ : style, images, vidéo
    cible = os.path.join(ICI, "en", reste, "index.html")

    md = markdown.Markdown(extensions=["tables", "md_in_html"], output_format="html")
    contenu = fr.poser_les_ancres(md.convert(corps))
    contenu = contenu.replace('src="img/', 'src="%simg/' % racine) \
                     .replace('href="img/', 'href="%simg/' % racine)

    if nom == "home":
        # La feuille de style compose les sections de l’accueil d’après les
        # identifiants de leurs titres français : l’accueil anglais les
        # reprend tels quels, invisibles, pour hériter de la même mise en page.
        for anglais, francais in IDENTIFIANTS.items():
            if 'id="%s"' % anglais not in contenu:
                sys.exit("en : la section « %s » est introuvable sur l’accueil." % anglais)
            contenu = contenu.replace('id="%s"' % anglais, 'id="%s"' % francais)
        coupe = contenu.find("<h2")
        chapeau, contenu = contenu[:coupe], contenu[coupe:]
        contenu = couverture_de_l_ouvrage(contenu, racine, alt)
        corps_html = gabarits["accueil"] % {
            "h1": fr.echapper(meta["h1"]),
            "auteur": fr.echapper(meta["auteur"]),
            "attribution": fr.echapper(meta["attribution"]),
            "chapeau": chapeau.strip(),
            "contenu": contenu.strip(),
            "cote": fr.video(meta, racine, telechargeable=False),
        }
    else:
        notion = nom in EXTRAITS
        corps_html = gabarits["page"] % {
            "classe": "notion" if notion else "document",
            "h1": fr.echapper(meta["h1"]),
            "chapeau": '<p class="chapeau">%s%s</p>' % (
                fr.echapper(meta["chapeau"]),
                '<span class="folio"> · page %s</span>' % meta["page"]
                if meta.get("page") else ""),
            "ancre": ' id="texte"' if meta.get("ancre_texte") else "",
            "cote": cote(meta, racine, en, alt),
            "contenu": contenu.strip(),
        }

    pied = "\n      ".join("<p>%s</p>" % "<br>\n      ".join(g) for g in PIED)
    if nom != "author":
        corps_html = lier_le_nom(corps_html, en + "author/")
        pied = lier_le_nom(pied, en + "author/")

    noms = [n for n, _, _ in MENU]
    liens = []
    for n in noms:
        href = en + ("" if n == "home" else n + "/") or "./"
        marque = ' aria-current="page"' if n == nom else ""
        if n == "order":
            marque = ' class="bouton"' + marque
        liens.append('<a href="%s"%s>%s</a>' % (href, marque, LIBELLE[n]))
    # La bascule de langue, au bout du menu : vers la page française miroir.
    liens.append('<a href="%s%s" lang="fr" hreflang="fr" title="Version française">FR</a>'
                 % (racine, VERS_FRANCAIS[nom]))
    # Le chevron du pied : la page suivante du menu ; un extrait envoie à la
    # page qui suit « The book », comme sur le site français.
    i = noms.index(nom) if nom in noms else noms.index("book")
    suivante = noms[(i + 1) % len(noms)]

    url = fr.DOMAINE + adresse
    og = [("og:type", "book" if nom == "home" else
           "profile" if nom == "author" else "article"),
          ("og:locale", "en_CA"), ("og:title", meta["h1"]),
          ("og:description", meta["description"]), ("og:url", url),
          ("og:image", fr.DOMAINE + "/lexique-ia/" + COUVERTURE)]
    page = base % {
        "avertissement": ("<!-- Fichier généré par build_en.py. Ne pas modifier à "
                          "la main : éditer contenu/en/%s.md -->" % nom),
        "titre": fr.echapper(meta["title"]),
        "description": fr.echapper(meta["description"]),
        "canonique": url,
        "prefixe": racine,
        "page": MIROIR.get(nom) or EXTRAITS[nom],
        "og": "\n  ".join('<meta property="%s" content="%s">' % (k, fr.echapper(v))
                          for k, v in og)
              + '\n  <link rel="alternate" hreflang="en" href="%s">'
                '\n  <link rel="alternate" hreflang="fr" href="%s/lexique-ia/%s">'
                % (url, fr.DOMAINE, VERS_FRANCAIS[nom]),
        "donnees": GRAPHE_ACCUEIL if nom == "home" else GRAPHE_PAGE % {
            "type": "DefinedTerm" if nom in EXTRAITS else "WebPage",
            "nom": meta["h1"], "url": url,
            "relation": "mainEntity" if nom == "book" else
            "inDefinedTermSet" if nom in EXTRAITS else "about"},
        "robots": fr.ROBOTS,
        "navigation": "\n      ".join(liens),
        "suivante": en + ("" if suivante == "home" else suivante + "/") or "./",
        "suivante_libelle": LIBELLE[suivante],
        "langues": "",
        "corps": corps_html,
        "pied": pied,
        "script": "\n".join(s for s, signe in (
            (fr.SCRIPT, 'class="courriel"'),
            (fr.SCRIPT_VIDEO.replace("Lire la vidéo", "Play the video"), "<video"))
            if signe in corps_html),
    }
    page = (page.replace('<html lang="fr">', '<html lang="en">')
                .replace("Aller au contenu", "Skip to content")
                .replace('aria-label="Sections du site"', 'aria-label="Site sections"')
                .replace('aria-label="Page suivante : ', 'aria-label="Next page: ')
                .replace('href="%sfavicon.svg"' % racine,
                         'href="%sfavicon-en.svg"' % racine))
    page = fr.liens_externes(page)
    if "'" in page:
        sys.exit("en/%s : une apostrophe droite s’est glissée dans la page." % nom)
    if len(re.findall(r"<h1[ >]", page)) != 1:
        sys.exit("en/%s : il faut exactement un H1 par page." % nom)
    fr.ecrire(cible, page)
    return adresse


# ------------------------------------------------- pour les assistants d’IA

def en_markdown(corps, adresse):
    """Le corps d’une page en Markdown nu, liens absolus : la fonction du site
    français, dont la phrase qui remplace l’adresse de courriel est traduite."""
    t = fr.en_markdown(corps, adresse)
    return re.sub(r"adresse publiée sur \S+", "address published at %s%sorder/"
                  % (fr.DOMAINE, BASE), t)


def llms():
    """en/llms.txt, la carte commentée du site anglais, et en/llms-full.txt,
    le texte de ses six pages. Même plan que les fichiers français."""
    racine = fr.DOMAINE + BASE
    lus = [(nom,) + source(nom) for nom in pages()]
    accueil, corps_accueil = lus[0][1], lus[0][2]
    corps_de = dict((nom, corps) for nom, _, corps in lus)

    licence = ("A book by %s. %s. ISBN 978-2-9825534-2-2 (print) and "
               "978-2-9825534-3-9 (ePUB). Translated from the French; "
               "translation revised by Alexia Moyer. © Stéphane Vial, "
               "publisher, 2026. Texts on this site are licensed under CC BY "
               "4.0, unless otherwise noted."
               % (accueil["auteur"], accueil["attribution"].replace(" · ", ". ")))

    ouvrage = []
    for ligne in fr.section(corps_accueil, "The book", "en/home.md").split("\n"):
        cases = [c.strip() for c in ligne.strip().strip("|").split("|")]
        if len(cases) == 2 and cases[0].startswith("**"):
            ouvrage.append("- %s: %s" % (cases[0].strip("*"), cases[1]))

    # Les huit chapitres de book.md : titre et liste des notions, compte contrôlé.
    livre = []
    for bloc in re.split(r"^### ", corps_de["book"], flags=re.M)[1:]:
        lignes = [l.strip() for l in bloc.split("\n") if l.strip()]
        livre.append((lignes[0], [n.strip() for n in lignes[2].split(" · ")]))
    if sum(len(n) for _, n in livre) != 91:
        sys.exit("en/llms.txt : il faut 91 notions dans contenu/en/book.md.")

    principales, extrait = [], []
    for nom, meta, corps in lus:
        if nom in EXTRAITS:
            definition = re.search(r"\*\*Definition\*\*\s*\n(.+?)(?:\n\s*\n|\Z)",
                                   corps, flags=re.S).group(1)
            phrase = re.match(r"(.+?[.!?])(?=\s+[A-Z]|$)", " ".join(definition.split()))
            extrait.append("- [%s](%s): %s · page %s. %s"
                           % (meta["h1"], fr.DOMAINE + meta["url"], meta["chapeau"],
                              meta["page"], phrase.group(1) if phrase else definition))
        else:
            principales.append("- [%s](%s): %s" % (meta["h1"], fr.DOMAINE + meta["url"],
                                                   meta["description"]))

    carte = fr.a_plat("\n".join([
        "# " + accueil["h1"],
        "",
        "> " + accueil["description"],
        "",
        licence + " Pages that carry a “How to cite this text” section give "
        "the reference to use.",
        "",
        "**The book**",
        "",
    ] + ouvrage + [
        "",
        "**The author**",
        "",
        en_markdown(fr.section(corps_accueil, "The author", "en/home.md"), BASE),
        "",
        "**Order the book**",
        "",
        en_markdown(fr.section(corps_accueil, "Order the book", "en/home.md"), BASE),
        "",
        "**The 91 concepts, in eight chapters**",
        "",
    ] + ["- **%s** (%d concepts): %s" % (titre, len(liste), " · ".join(liste))
         for titre, liste in livre] + [
        "",
        "## The book and its author",
        "",
    ] + principales + [
        "",
        "## Eight entries to read, one per chapter",
        "",
    ] + extrait + [
        "",
        "## Full text",
        "",
        "- [The whole site in a single file](%sllms-full.txt): the text of its "
        "%d pages, in Markdown." % (racine, len(lus)),
        "",
        "## Optional",
        "",
        "- [Sitemap](%s/sitemap.xml): every address, in sitemap format." % fr.DOMAINE,
        "- [Cover in high definition](%s/lexique-ia/%s): %s."
        % (fr.DOMAINE, COUVERTURE_HD, accueil["couverture_alt"]),
        "- [Original French edition](%s/lexique-ia/llms.txt): Petit lexique "
        "vivant de l’intelligence artificielle, the map of the French site."
        % fr.DOMAINE,
        "",
    ]))

    blocs = []
    for nom, meta, corps in lus:
        texte = re.sub(r"^(#{2,5}) ", r"#\1 ", en_markdown(corps, meta["url"]),
                       flags=re.M)
        tete = ["## " + meta["h1"], "", "Address: " + fr.DOMAINE + meta["url"]]
        if nom == "home":
            tete += ["", "%s · %s" % (meta["auteur"], meta["attribution"])]
        elif meta.get("chapeau"):
            tete += ["", meta["chapeau"] + (" · page %s" % meta["page"]
                                            if meta.get("page") else "")]
        blocs.append("\n".join(tete + ["", texte]))
    integral = fr.a_plat("\n".join([
        "# %s: full text of the site" % accueil["h1"],
        "",
        "> " + accueil["description"],
        "",
        licence,
        "",
        "This file gathers the text of the %d pages of the site: the seven "
        "pages of the menu, then the eight entries to read, in chapter "
        "order. The annotated map of the site is at %sllms.txt."
        % (len(lus), racine),
        "",
        "---",
        "",
        "",
    ]) + "\n\n---\n\n".join(blocs) + "\n")

    fr.ecrire(os.path.join(ICI, "en", "llms.txt"), carte)
    fr.ecrire(os.path.join(ICI, "en", "llms-full.txt"), integral)


def sitemap(adresses):
    """Ajoute les adresses anglaises à ../sitemap.xml, que build.py vient de
    régénérer sans elles."""
    chemin = os.path.join(fr.RACINE, "sitemap.xml")
    texte = fr.lire(chemin)
    manquantes = [a for a in adresses if fr.DOMAINE + a + "</loc>" not in texte]
    ajout = "".join("  <url><loc>%s</loc></url>\n" % (fr.DOMAINE + a) for a in manquantes)
    fr.ecrire(chemin, texte.replace("</urlset>", ajout + "</urlset>"))


def pages():
    """Les sept pages du menu, puis les huit extraits dans l’ordre des chapitres."""
    extraits = sorted(EXTRAITS, key=lambda e: fr.entete_et_corps(
        fr.lire(chemin_de(e)))[0]["ordre"])
    return [n for n, _, _ in MENU] + extraits


def main():
    base = fr.lire(os.path.join(fr.GABARIT, "base.html"))
    gabarits = {"accueil": fr.lire(os.path.join(fr.GABARIT, "accueil.html")),
                "page": fr.lire(os.path.join(fr.GABARIT, "page.html"))}
    alt = source("home")[0]["couverture_alt"]
    adresses = []
    for nom in pages():
        adresses.append(construire(nom, base, gabarits, alt))
        print("  ✓ en  %s" % adresses[-1])
    for ancien, nouveau in RENVOIS.items():
        fr.ecrire(os.path.join(ICI, "en", ancien, "index.html"),
                  RENVOI % {"vers": fr.DOMAINE + BASE + nouveau})
        print("  → en/%s renvoie vers en/%s" % (ancien, nouveau))
    sitemap(adresses)
    llms()
    print("  ✓ en/llms.txt, en/llms-full.txt")
    print("%d pages anglaises construites.%s" % (
        len(adresses), "" if ASIN else "  ⚠ ASIN anglais vide : pas de lien d’achat."))


if __name__ == "__main__":
    main()
