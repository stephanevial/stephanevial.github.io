#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — la fabrique du site du Petit lexique vivant de l'IA.

    python3 build.py

Lit les quatre fichiers de contenu/, applique les gabarits de gabarit/, écrit
les quatre index.html du site et régénère ../sitemap.xml.

Deux exécutions successives produisent des fichiers identiques : aucune date,
aucun compteur, aucun aléa n'entre dans la sortie.

Trois exigences de conversion, contrôlées à chaque exécution et bloquantes :
  1. aucune substitution typographique (l'extension smarty n'est jamais
     chargée) : les apostrophes, guillemets et tirets sortent tels qu'ils sont
     entrés ;
  2. les espaces insécables survivent : ils sont comptés avant et après
     conversion, et le script s'arrête si le compte change ;
  3. les italiques sont des <em>, jamais des <i> : la présence de <i> ou de
     <b> arrête le script.

Le seul fichier à éditer pour corriger un texte est contenu/<page>.md.
"""
import io
import os
import re
import sys
import unicodedata

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

DOMAINE = "https://web.stephane-vial.net"
NBSP = " "

AVERTISSEMENT = ("<!-- Fichier généré par build.py. Ne pas modifier à la "
                 "main : éditer contenu/%s.md -->")

# Les quatre pages, dans l'ordre du site. Le nom du fichier de contenu, le
# dossier de sortie, et le libellé de navigation.
PAGES = [
    ("accueil",     "",             "Le lexique"),
    ("la-fabrique", "la-fabrique",  "La fabrique"),
    ("declaration", "declaration",  "La déclaration"),
    ("le-livre",    "le-livre",     "Le livre"),
]

PIED = [
    "Petit lexique vivant de l'intelligence artificielle · Stéphane Vial · "
    "6 octobre 2026",
    "ISBN 978-2-9825534-0-8",
    "© Stéphane Vial, 2026 · "
    "<a href=\"https://stephane-vial.net\">stephane-vial.net</a>",
]

# Le sélecteur de langue existe dans le code et reste masqué jusqu'au
# 17 novembre 2026, date de parution des éditions anglaise et espagnole.
# Il ne se supprime pas : il se démasque en retirant l'attribut hidden.
LANGUES = [("fr", "Français", ""),
           ("en", "English", "en/"),
           ("es", "Español", "es/")]


# ------------------------------------------------------- données structurées

GRAPHE_ACCUEIL = """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Book",
      "@id": "https://web.stephane-vial.net/lexique-ia/#livre",
      "name": "Petit lexique vivant de l'intelligence artificielle",
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
      "abstract": "Ouvrage d'initiation à l'intelligence artificielle. Quatre-vingt-onze notions, une page chacune, organisées en huit chapitres. Chaque entrée suit la même structure : une définition, un exemple tiré d'usages ordinaires, et ce qui fait son importance.",
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
  "@type": "WebPage",
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
    """Sépare l'en-tête YAML du corps Markdown."""
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
    """Donne un identifiant à chaque H2 et H3, pour qu'on puisse pointer une
    section ou une notion depuis l'extérieur."""
    def remplacer(m):
        return '<h%s id="%s">%s</h%s>' % (m.group(1), ancre(m.group(2)),
                                          m.group(2), m.group(1))
    return re.sub(r"<h([23])>(.*?)</h\1>", remplacer, html, flags=re.S)


# ------------------------------------------------------------- vérifications

def verifier(nom, source, html):
    """Les trois exigences du cahier des charges, plus l'hygiène de balisage.
    Toute anomalie arrête la construction : une page fausse ne se publie pas."""
    ennuis = []

    avant, apres = source.count(NBSP), html.count(NBSP)
    if avant != apres:
        ennuis.append("espaces insécables : %d dans la source, %d dans la "
                      "page. La conversion en a mangé ou en a ajouté."
                      % (avant, apres))

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
                      "plus rien dans l'ouvrage et ne doit apparaître nulle "
                      "part.")

    for hote in re.findall(r'(?:src|href)="https?://([^/"]+)', html):
        if hote.endswith("stephane-vial.net"):
            continue
        if not re.search(r'<a [^>]*href="https?://%s' % re.escape(hote), html):
            ennuis.append("ressource chargée depuis un tiers : %s. Aucune "
                          "requête ne doit sortir du domaine." % hote)

    if ennuis:
        for e in ennuis:
            sys.stderr.write("  ✗ %s : %s\n" % (nom, e))
        sys.exit("Construction interrompue. Rien n'a été publié.")


# ------------------------------------------------------------- construction

def navigation(prefixe, courante):
    entrees = []
    for nom, dossier, libelle in PAGES:
        cible = prefixe + (dossier + "/" if dossier else "")
        if nom == courante:
            entrees.append('<a href="%s" aria-current="page">%s</a>'
                           % (cible, libelle))
        else:
            entrees.append('<a href="%s">%s</a>' % (cible, libelle))
    return "\n      ".join(entrees)


def selecteur_de_langue(prefixe):
    """Présent dans le code, masqué jusqu'au 17 novembre 2026. Il ne laisse ni
    trace visible ni espace vide : hidden le retire du flux et du lecteur
    d'écran. Pour le démasquer, retirer l'attribut hidden."""
    liens = ['<a href="%s%s" lang="%s"%s>%s</a>'
             % (prefixe, chemin, code, ' aria-current="true"' if not chemin
                else "", libelle)
             for code, libelle, chemin in LANGUES]
    return ('<nav class="langues" hidden aria-label="Langue">\n      %s\n'
            '    </nav>' % "\n      ".join(liens))


def construire(nom, dossier, base, gabarits):
    source = lire(os.path.join(CONTENU, nom + ".md"))
    meta, corps = entete_et_corps(source)

    prefixe = "" if not dossier else "../"

    # Conversion Markdown. Aucune extension de substitution typographique :
    # « smarty » n'est pas chargée, et ne doit jamais l'être.
    md = markdown.Markdown(extensions=[], output_format="html")
    contenu = poser_les_ancres(md.convert(corps))

    # Les chemins d'images de contenu/ sont relatifs à /lexique-ia/ ; sur une
    # page en sous-dossier, il faut remonter d'un cran.
    if prefixe:
        contenu = contenu.replace('src="img/', 'src="%simg/' % prefixe)

    if meta.get("gabarit") == "accueil":
        # Le chapeau, c'est tout ce qui précède le premier H2. Son premier
        # paragraphe est le seul endroit du site où le corps est plus gros.
        coupe = contenu.find("<h2")
        chapeau, contenu = contenu[:coupe], contenu[coupe:]
        chapeau = chapeau.replace("<p>", '<p class="accroche">', 1)
        corps_html = gabarits["accueil"] % {
            "h1": echapper(meta["h1"]),
            "attribution": echapper(meta["attribution"]),
            "chapeau": chapeau.strip(),
            "contenu": contenu.strip(),
        }
    else:
        ancre_texte = ' id="texte"' if meta.get("ancre_texte") else ""
        chapeau = ('<p class="chapeau">%s</p>' % echapper(meta["chapeau"])
                   if meta.get("chapeau") else "")
        corps_html = gabarits["page"] % {
            "h1": echapper(meta["h1"]),
            "chapeau": chapeau,
            "ancre": ancre_texte,
            "contenu": contenu.strip(),
        }

    url = DOMAINE + meta["url"]
    if nom == "accueil":
        donnees = GRAPHE_ACCUEIL
    else:
        donnees = GRAPHE_PAGE % {
            "nom": meta["h1"], "url": url,
            "relation": "mainEntity" if nom == "le-livre" else "about",
        }

    og = [
        ('og:type', meta.get("og_type", "article")),
        ('og:locale', 'fr_CA'),
        ('og:title', meta["h1"]),
        ('og:description', meta["description"]),
        ('og:url', url),
        ('og:image', DOMAINE + "/lexique-ia/img/couverture.jpg"),
    ]

    page = base % {
        "avertissement": AVERTISSEMENT % nom,
        "titre": echapper(meta["title"]),
        "description": echapper(meta["description"]),
        "canonique": url,
        "prefixe": prefixe,
        "page": nom,
        "og": "\n  ".join('<meta property="%s" content="%s">'
                          % (k, echapper(v)) for k, v in og),
        "donnees": donnees,
        "navigation": navigation(prefixe, nom),
        "langues": selecteur_de_langue(prefixe),
        "corps": corps_html,
        "pied": "<br>\n      ".join(PIED),
    }

    verifier(nom, source, page)

    cible = os.path.join(ICI, dossier, "index.html") if dossier \
        else os.path.join(ICI, "index.html")
    ecrire(cible, page)
    return os.path.relpath(cible, ICI), meta["url"]


def sitemap(urls):
    """Régénère ../sitemap.xml. Toute adresse déjà présente qui ne relève pas
    de /lexique-ia/ est conservée : ce fichier sert tout le sous-domaine."""
    chemin = os.path.join(RACINE, "sitemap.xml")
    gardees = []
    if os.path.exists(chemin):
        for u in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", lire(chemin)):
            if "/lexique-ia/" not in u:
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
    base = lire(os.path.join(GABARIT, "base.html"))
    gabarits = {"accueil": lire(os.path.join(GABARIT, "accueil.html")),
                "page": lire(os.path.join(GABARIT, "page.html"))}

    urls = []
    for nom, dossier, _ in PAGES:
        cible, url = construire(nom, dossier, base, gabarits)
        urls.append(url)
        print("  ✓ %-24s %s" % (cible, url))

    chemin, n = sitemap(urls)
    print("  ✓ %-24s %d adresses"
          % (os.path.relpath(chemin, ICI), n))
    print("\nQuatre pages construites. Aucune requête ne sort du domaine.")


if __name__ == "__main__":
    main()
