#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_en.py — le mini-site de l’édition anglaise, dans en/.

    python3 build_en.py        (build.py l’appelle aussi à la fin de sa construction)

Trois pages au menu : Home, The author, Order. Trois autres atteintes depuis
l’accueil seulement : un extrait (Hallucination), The Making of This Book,
Statement on the Use of AI. Sources dans contenu/en/. Gabarits, feuille de
style, fontes et scripts : ceux du site français, sans copie.

Volontairement minimal : pas de vidéo, pas de communiqué, pas de llms.txt. Les
ventes anglaises viennent de la recherche d’Amazon ; ce site sert de carte de
visite et de preuve (la fabrique, la déclaration, un extrait).

Les textes tirés du livre (extrait, fabrique, déclaration) sont ceux du
manuscrit anglais révisé, mot pour mot : ils ne se retouchent pas ici.
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
# Vide : la page « Order » annonce la date sans lien. Ne jamais le deviner.
ASIN = ""
BOUTIQUES = [("United States", "Amazon.com", "https://www.amazon.com/dp/%s"),
             ("Canada", "Amazon.ca", "https://www.amazon.ca/dp/%s"),
             ("United Kingdom", "Amazon.co.uk", "https://www.amazon.co.uk/dp/%s")]

MENU = [("home", "Home"), ("author", "The author"), ("order", "Order")]
HORS_MENU = ["hallucination", "making-of", "statement"]

PIED = [
    ["<strong>Dépôt légal, Bibliothèque et Archives nationales du Québec, 2026</strong>",
     "ISBN 978-2-9825534-2-2 (Print) · ISBN 978-2-9825534-3-9 (ePUB)"],
    ["<strong>A Living Lexicon of Artificial Intelligence</strong>",
     "© Stéphane Vial, 2026",
     "Texts on this site are licensed under "
     "<a href=\"https://creativecommons.org/licenses/by/4.0/\">CC BY 4.0</a>, "
     "unless otherwise noted"],
]

GRAPHE = """{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "A Living Lexicon of Artificial Intelligence",
  "inLanguage": "en",
  "author": {"@type": "Person", "name": "Stéphane Vial", "url": "https://stephane-vial.net"},
  "isbn": "9782982553422",
  "datePublished": "2026-10-13",
  "numberOfPages": 138,
  "translationOfWork": {"@type": "Book", "name": "Petit lexique vivant de l’intelligence artificielle", "inLanguage": "fr", "url": "https://web.stephane-vial.net/lexique-ia/"},
  "url": "https://web.stephane-vial.net/lexique-ia/en/"
}"""

GRAPHE_PAGE = """{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "%(nom)s",
  "inLanguage": "en",
  "url": "%(url)s",
  "isPartOf": {"@type": "WebSite", "url": "https://web.stephane-vial.net/lexique-ia/en/"}
}"""


def boutiques():
    if not ASIN:
        return ("Order links will be posted here on publication day, "
                "October 13, 2026.")
    return "\n".join('- **%s**  \n  <a href="%s" class="commander">Order on %s</a>'
                     % (pays, lien % ASIN, nom) for pays, nom, lien in BOUTIQUES)


def couverture(racine, href, titre, alt, paresseuse=True):
    return ('        <figure class="couverture">\n'
            '          <a href="%s"%s title="%s"><img src="%simg/cover-en.jpg" '
            'alt="%s" width="800" height="1280"%s></a>\n        </figure>'
            % (href, ' target="_blank" rel="noopener"' if href.endswith(".jpg") else "",
               titre, racine, fr.echapper(alt),
               ' loading="lazy"' if paresseuse else ""))


def portrait(racine):
    return ('        <figure class="couverture portrait">\n'
            '          <a href="%(r)simg/portrait-stephane-vial-hd.jpg" target="_blank" '
            'rel="noopener" title="Open the portrait in high definition">'
            '<img src="%(r)simg/portrait-stephane-vial.jpg" alt="Stéphane Vial, Full '
            'Professor at the School of Design of the Université du Québec à '
            'Montréal"></a>\n'
            '          <figcaption>© Justine Latour for UQAM</figcaption>\n'
            '        </figure>' % {"r": racine})


def construire(nom, base, gabarits, alt):
    meta, corps = fr.entete_et_corps(fr.lire(os.path.join(CONTENU, nom + ".md")))
    adresse = meta["url"]
    reste = adresse[len(BASE):].strip("/")
    en = "../" if reste else ""          # vers l’accueil anglais
    racine = en + "../"                  # vers /lexique-ia/ : style, images, fontes
    cible = os.path.join(ICI, "en", reste, "index.html")

    if nom == "order":
        corps = corps % {"boutiques": boutiques()}
    md = markdown.Markdown(extensions=["tables", "md_in_html"], output_format="html")
    contenu = fr.poser_les_ancres(md.convert(corps))

    if nom == "home":
        coupe = contenu.find("<h2")
        corps_html = gabarits["accueil"] % {
            "h1": fr.echapper(meta["h1"]),
            "auteur": '<a href="author/">%s</a>' % fr.echapper(meta["auteur"]),
            "attribution": fr.echapper(meta["attribution"]),
            "chapeau": contenu[:coupe].strip(),
            "contenu": contenu[coupe:].strip(),
            "cote": couverture(racine, racine + "img/cover-en-hd.jpg",
                               "Open the cover at full size", alt, paresseuse=False),
        }
    else:
        corps_html = gabarits["page"] % {
            "classe": "notion" if nom == "hallucination" else "document",
            "h1": fr.echapper(meta["h1"]),
            "chapeau": '<p class="chapeau">%s</p>' % fr.echapper(meta["chapeau"]),
            "ancre": "",
            "cote": (portrait(racine) if meta.get("cote") == "portrait"
                     else couverture(racine, en or "./", "Back to the home page", alt)),
            "contenu": contenu.strip(),
        }

    noms = [n for n, _ in MENU]
    liens = []
    for n, libelle in MENU:
        href = en + ("" if n == "home" else n + "/") or "./"
        marque = ' aria-current="page"' if n == nom else ""
        if n == "order":
            marque = ' class="bouton"' + marque
        liens.append('<a href="%s"%s>%s</a>' % (href, marque, libelle))
    # La seule passerelle vers l’édition originale : un lien au bout du menu.
    liens.append('<a href="%s" lang="fr" hreflang="fr">Français</a>' % racine)
    suivante = noms[(noms.index(nom) + 1) % len(noms)] if nom in noms else "home"

    url = fr.DOMAINE + adresse
    og = [("og:type", "book" if nom == "home" else "article"),
          ("og:locale", "en_CA"), ("og:title", meta["h1"]),
          ("og:description", meta["description"]), ("og:url", url),
          ("og:image", fr.DOMAINE + "/lexique-ia/img/cover-en.jpg")]
    page = base % {
        "avertissement": ("<!-- Fichier généré par build_en.py. Ne pas modifier à "
                          "la main : éditer contenu/en/%s.md -->" % nom),
        "titre": fr.echapper(meta["title"]),
        "description": fr.echapper(meta["description"]),
        "canonique": url,
        "prefixe": racine,
        "page": "accueil" if nom == "home" else nom,
        "og": "\n  ".join('<meta property="%s" content="%s">' % (k, fr.echapper(v))
                          for k, v in og)
              + ('\n  <link rel="alternate" hreflang="fr" href="%s/lexique-ia/">'
                 '\n  <link rel="alternate" hreflang="en" href="%s">'
                 % (fr.DOMAINE, url) if nom == "home" else ""),
        "donnees": GRAPHE if nom == "home" else GRAPHE_PAGE % {
            "nom": meta["h1"], "url": url},
        "robots": fr.ROBOTS,
        "navigation": "\n      ".join(liens),
        "suivante": en + ("" if suivante == "home" else suivante + "/") or "./",
        "suivante_libelle": dict(MENU)[suivante],
        "langues": "",
        "corps": corps_html,
        "pied": "\n      ".join("<p>%s</p>" % "<br>\n      ".join(g) for g in PIED),
        "script": fr.SCRIPT if 'class="courriel"' in corps_html else "",
    }
    page = (page.replace('<html lang="fr">', '<html lang="en">')
                .replace("Aller au contenu", "Skip to content")
                .replace('aria-label="Sections du site"', 'aria-label="Site sections"')
                .replace('aria-label="Page suivante : ', 'aria-label="Next page: '))
    page = fr.liens_externes(page)
    if "'" in re.sub(r"<script.*?</script>", "", page, flags=re.S):
        sys.exit("en/%s : une apostrophe droite s’est glissée dans la page." % nom)
    fr.ecrire(cible, page)
    return adresse


def sitemap(adresses):
    """Ajoute les adresses anglaises à ../sitemap.xml, que build.py vient de
    régénérer sans elles."""
    chemin = os.path.join(fr.RACINE, "sitemap.xml")
    texte = fr.lire(chemin)
    manquantes = [a for a in adresses if fr.DOMAINE + a + "</loc>" not in texte]
    ajout = "".join("  <url><loc>%s</loc></url>\n" % (fr.DOMAINE + a) for a in manquantes)
    fr.ecrire(chemin, texte.replace("</urlset>", ajout + "</urlset>"))


def main():
    base = fr.lire(os.path.join(fr.GABARIT, "base.html"))
    gabarits = {"accueil": fr.lire(os.path.join(fr.GABARIT, "accueil.html")),
                "page": fr.lire(os.path.join(fr.GABARIT, "page.html"))}
    alt = fr.entete_et_corps(fr.lire(os.path.join(CONTENU, "home.md")))[0]["couverture_alt"]
    adresses = []
    for nom in [n for n, _ in MENU] + HORS_MENU:
        adresses.append(construire(nom, base, gabarits, alt))
        print("  ✓ en  %s" % adresses[-1])
    sitemap(adresses)
    print("%d pages anglaises construites.%s" % (
        len(adresses), "" if ASIN else "  ⚠ ASIN anglais vide : page Order sans lien d’achat."))


if __name__ == "__main__":
    main()
