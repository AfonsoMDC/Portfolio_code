"""Bouwt de hele website uit sjablonen/ en teksten/. Gebruik: python3 bron/bouw.py

Elke pagina wordt in drie talen geschreven: nl in de hoofdmap, en/ en fr/ in submappen.
Een ontbrekende tekstsleutel of een ontbrekend beeld stopt de bouw met een foutmelding.
"""
import html
import json
import re
from pathlib import Path

from PIL import Image

import gegevens as g

WORTEL = Path(__file__).parent.parent
SJABLONEN = Path(__file__).parent / "sjablonen"
NAAM = "Afonso Matos da Cruz"
LANDCODES = {"nl": "nl_BE", "en": "en_GB", "fr": "fr_BE"}


# ---------- Teksten en sjablonen ----------
def laad_teksten():
    alle = {taal: json.loads((Path(__file__).parent / "teksten" / f"{taal}.json").read_text(encoding="utf8"))
            for taal in g.TALEN}
    for taal in g.TALEN:
        ontbreekt = set(alle["nl"]) - set(alle[taal])
        assert not ontbreekt, f"{taal}.json mist sleutels: {sorted(ontbreekt)[:5]}. Draai eerst bron/vertaal.py"
    return alle


def veilig(tekst):
    """Maakt tekst veilig voor HTML, maar laat <br>, <em> en de decoratieve pil-beelden staan."""
    veilig_tekst = html.escape(tekst, quote=False)
    veilig_tekst = re.sub(r"&lt;(/?(?:br|em))&gt;", r"<\1>", veilig_tekst)
    return re.sub(r'&lt;i class="(pil-\w+)"&gt;&lt;/i&gt;', r'<i class="\1"></i>', veilig_tekst)


def vul(sjabloon_naam, waarden):
    """Vult {{sleutel}} in een sjabloon, ook in ingevoegde blokken, tot er niets meer te vullen is."""
    tekst = (SJABLONEN / f"{sjabloon_naam}.html").read_text(encoding="utf8")
    for _ in range(5):
        tekst = re.sub(r"\{\{([\w.\-]+)\}\}", lambda m: waarden[m.group(1)], tekst)
        if "{{" not in tekst:
            return tekst
    raise ValueError(f"Sjabloon {sjabloon_naam} bevat nog onvolledige placeholders")


# ---------- Adressen ----------
def url(taal, pad=""):
    voorvoegsel = "" if taal == "nl" else f"/{taal}"
    return f"{voorvoegsel}/{pad}"


# ---------- Beelden ----------
maten = {}


def maat(map, naam, formaat):
    sleutel = (map, naam, formaat)
    if sleutel not in maten:
        with Image.open(WORTEL / f"afbeeldingen/{map}/{naam}-{formaat}.webp") as beeld:
            maten[sleutel] = beeld.size
    return maten[sleutel]


def beeld(tekst, map, naam, sizes, laden="lazy"):
    klein, groot = maat(map, naam, "klein"), maat(map, naam, "groot")
    bron = f"/afbeeldingen/{map}/{naam}"
    return (f'<img src="{bron}-klein.webp" srcset="{bron}-klein.webp {klein[0]}w, {bron}-groot.webp {groot[0]}w" '
            f'sizes="{sizes}" width="{klein[0]}" height="{klein[1]}" alt="{html.escape(tekst[f"alt.{map}/{naam}"])}" '
            f'loading="{laden}" decoding="async">')


def vergroting_gegevens(tekst, lijst):
    return html.escape(json.dumps([{"src": f"/afbeeldingen/{m}/{n}-groot.webp", "alt": tekst[f"alt.{m}/{n}"]}
                                   for m, n in lijst], ensure_ascii=False), quote=True)


def nummer(i):
    return f"{i:02d}"


# ---------- Bouwstenen ----------
def kader(tekst, lijst, titel="", uitleg="", start=0, sizes="50vw"):
    """Een kader met één beeld dat bij een klik alle beelden van de lijst groot toont."""
    map, naam = lijst[start]
    return (f'<a class="kader" href="/afbeeldingen/{map}/{naam}-groot.webp" data-start="{start}" '
            f'data-beelden="{vergroting_gegevens(tekst, lijst)}" data-titel="{html.escape(titel)}" '
            f'data-tekst="{html.escape(uitleg)}">{beeld(tekst, map, naam, sizes)}</a>')


def rij(nr, titel, soort, adres, voorbeeld, mini, extra=""):
    """Een regel in een lijst: nummer, titel, soort en een klein beeld. Bij hover verschijnt een voorbeeld."""
    return (f'<a class="rij" href="{adres}" data-voorbeeld="{voorbeeld}" {extra}><span class="nr">{nummer(nr)}</span>'
            f'<span class="titel">{veilig(titel)}</span><span class="soort">{veilig(soort)}</span>'
            f'<span class="mini"><img src="{mini}" width="120" height="120" alt="" loading="lazy" decoding="async"></span></a>')


def rij_werk(tekst, nr, wid, lijst):
    map, naam = lijst[0]
    titel, uitleg = tekst[f"werk.{wid}.titel"], tekst[f"werk.{wid}.tekst"]
    aantal = f" · {len(lijst)} {tekst['werk.rij_beelden']}" if len(lijst) > 1 else ""
    extra = (f'data-beelden="{vergroting_gegevens(tekst, lijst)}" data-titel="{html.escape(titel)}" '
             f'data-tekst="{html.escape(uitleg)}"')
    return rij(nr, titel, tekst[f"werk.{wid}.soort"] + aantal, f"/afbeeldingen/{map}/{naam}-groot.webp",
               f"/afbeeldingen/{map}/{naam}-klein.webp", f"/afbeeldingen/{map}/{naam}-klein.webp", extra)


def rij_project(taal, tekst, nr, pid):
    omslag = f"/afbeeldingen/omslag/{pid}.webp"
    return rij(nr, tekst[f"project.{pid}.titel"], tekst[f"project.{pid}.ondertitel"],
               url(taal, f"project/{pid}/"), omslag, omslag)


def video(tekst, naam, titel, onderschrift=""):
    return (f'<figure class="film"><video controls preload="none" poster="/afbeeldingen/film/{naam}.webp" '
            f'aria-label="{html.escape(titel)}"><source src="/video/{naam}.mp4" type="video/mp4">'
            f'{veilig(tekst["film.geen_video"])}</video>{onderschrift}</figure>')


def vierkant(tekst, map, naam, adres):
    return f'<a class="vierkant" href="{adres}">{beeld(tekst, map, naam, "(min-width: 900px) 16vw, 33vw")}</a>'


# ---------- Blokken per pagina ----------
def blok_start(taal, tekst):
    projecten = "".join(rij_project(taal, tekst, i, pid) for i, (pid, _) in enumerate(g.PROJECTEN, 1))
    fotos = "".join(vierkant(tekst, "fotografie", f"straat-{i:02d}", url(taal, "fotografie/"))
                    for i in (24, 10, 21, 12, 25, 7))
    films = "".join(f'<a class="vierkant breed" href="{url(taal, "film/")}"><img src="/afbeeldingen/film/{fid}.webp" '
                    f'alt="{html.escape(tekst[f"film.{fid}.titel"])}" loading="lazy"></a>'
                    for fid, _ in g.FILMS)
    opleiding = "".join(f'<li><span>{veilig(tekst[f"over.opleiding_{i}_jaar"])}</span>{veilig(tekst[f"over.opleiding_{i}"])}</li>'
                        for i in (1, 2, 3))
    cv_taal = "nl" if taal == "nl" else "en"  # er is geen Franse cv: Frans verwijst naar de Engelse
    return {"start_projecten": projecten, "start_fotos": fotos, "start_films": films, "opleiding_lijst": opleiding,
            "over_foto": beeld(tekst, "algemeen", "aan-het-werk", "(min-width: 900px) 33vw, 100vw"),
            "cv_url": f"/cv/cv-afonso-matos-da-cruz-{cv_taal}.pdf"}


def blok_werk(taal, tekst):
    vakken = [("projecten", "".join(rij_project(taal, tekst, i, pid) for i, (pid, _) in enumerate(g.PROJECTEN, 1)))]
    for vak, werken in g.VAKKEN:
        vakken.append((vak, "".join(rij_werk(tekst, i, wid, lijst) for i, (wid, lijst) in enumerate(werken, 1))))
    return "".join(
        f'<section class="vak raster"><div class="vakkop"><span class="nr">{nummer(i)}</span><h2>{veilig(tekst[f"werk.vak_{vak}"])}</h2>'
        f'<p>{veilig(tekst[f"werk.vak_{vak}_tekst"])}</p></div><div class="lijst">{rijen}</div></section>'
        for i, (vak, rijen) in enumerate(vakken, 1))


def blok_gegevens(tekst, pid, aantal):
    rijen = [("project.label_soort", tekst["project.soort_school"]),
             ("project.label_school", f'{tekst["project.school_dbsdw"]} · {tekst[f"project.{pid}.klas"]}')]
    if f"project.{pid}.wanneer" in tekst:
        rijen.append(("project.label_wanneer", tekst[f"project.{pid}.wanneer"]))
    rijen += [("project.label_onderdelen", str(aantal)), ("project.label_gemaakt", tekst[f"project.{pid}.gemaakt"])]
    return "".join(f'<div><dt>{veilig(tekst[k])}</dt><dd>{veilig(w)}</dd></div>' for k, w in rijen)


def blok_onderdelen(tekst, pid):
    resultaat = []
    for i, (oid, lijst, film) in enumerate(dict(g.PROJECTEN)[pid], 1):
        sleutel = f"project.{pid}.{oid}"
        titel, uitleg = tekst[f"{sleutel}.titel"], tekst[f"{sleutel}.tekst"]
        media = "".join(kader(tekst, lijst, titel, uitleg, start=n) for n in range(len(lijst)))
        if film:
            media += video(tekst, film, tekst[f"film.{film}.titel"])
        soort = "twee" if len(lijst) + bool(film) == 2 else "een"
        resultaat.append(f'<section class="onderdeel raster"><span class="nr">{nummer(i)}</span><h3>{veilig(titel)}</h3>'
                         f'<p>{veilig(uitleg)}</p><div class="media {soort}">{media}</div></section>')
    return "".join(resultaat)


def blok_films(taal, tekst):
    lijst = []
    for i, (fid, pid) in enumerate(g.FILMS, 1):
        onderschrift = (f'<figcaption><span class="nr">{nummer(i)}</span><b>{veilig(tekst[f"film.{fid}.titel"])}</b>'
                        f'<p>{veilig(tekst[f"film.{fid}.tekst"])}</p>'
                        f'<p class="klein">{veilig(tekst["film.duur"])} {tekst[f"film.{fid}.duur"]} · '
                        f'<a class="tekstlink" href="{url(taal, f"project/{pid}/")}">{veilig(tekst[f"project.{pid}.titel"])}</a></p></figcaption>')
        lijst.append(video(tekst, fid, tekst[f"film.{fid}.titel"], onderschrift))
    return "".join(lijst)


def blok_fotos(tekst):
    fotos = [("fotografie", f"straat-{i:02d}") for i in range(1, g.AANTAL_FOTOS + 1)]
    return "".join(kader(tekst, fotos, start=i, sizes="(min-width: 900px) 25vw, 50vw") for i in range(len(fotos)))


# ---------- Pagina's ----------
def menu(taal, tekst, actief):
    items = [("werk/", "nav.werk"), ("fotografie/", "nav.fotografie"), ("film/", "nav.film"),
             ("#over", "nav.over"), ("#contact", "nav.contact")]
    schakels = []
    for i, (pad, sleutel) in enumerate(items, 1):
        adres = url(taal) + pad if pad.startswith("#") else url(taal, pad)
        huidig = ' aria-current="page"' if pad == actief else ""
        schakels.append(f'<a href="{adres}"{huidig}><span>{nummer(i)}</span> {veilig(tekst[sleutel])}</a>')
    return "".join(schakels)


def taalkeuze(taal, pad):
    return "".join(f'<a href="{url(t, pad)}" hreflang="{t}" lang="{t}"'
                   f'{" aria-current=\"true\"" if t == taal else ""}>{t.upper()}</a>' for t in g.TALEN)


def hreflang(pad):
    regels = [f'<link rel="alternate" hreflang="{t}" href="{g.DOMEIN}{url(t, pad)}">' for t in g.TALEN]
    regels.append(f'<link rel="alternate" hreflang="x-default" href="{g.DOMEIN}{url("nl", pad)}">')
    return "\n".join(regels)


def json_ld(gegevens):
    return f'<script type="application/ld+json">{json.dumps(gegevens, ensure_ascii=False)}</script>'


def persoon(tekst):
    return {"@type": "Person", "@id": f"{g.DOMEIN}/#afonso", "name": NAAM, "url": g.DOMEIN + "/",
            "description": tekst["start.beschrijving"], "sameAs": [g.INSTAGRAM],
            "address": {"@type": "PostalAddress", "addressLocality": "Gent", "addressCountry": "BE"}}


def schrijf_pagina(taal, tekst, pad, sjabloon, titel, beschrijving, blokken, actief=None, scripts=(), lichtbak=False,
                   donker=False, gestructureerd=None):
    waarden = {sleutel: veilig(waarde) for sleutel, waarde in tekst.items()}
    waarden.update(blokken)
    waarden.update({
        "taal": taal, "landcode": LANDCODES[taal], "domein": g.DOMEIN, "thema": "donker" if donker else "licht",
        "paginatitel": html.escape(titel), "paginabeschrijving": html.escape(beschrijving),
        "canoniek": g.DOMEIN + url(taal, pad), "hreflang": hreflang(pad),
        "start_url": url(taal), "werk_url": url(taal, "werk/"), "fotografie_url": url(taal, "fotografie/"),
        "film_url": url(taal, "film/"), "privacy_url": url(taal, "privacy/"),
        "menu": menu(taal, tekst, actief), "taalkeuze": taalkeuze(taal, pad),
        "email": g.EMAIL, "instagram": g.INSTAGRAM, "formulier_adres": g.FORMULIER_ADRES, "youtube": g.YOUTUBE_FILM,
        "gestructureerde_gegevens": json_ld(gestructureerd) if gestructureerd else "",
        "scripts": "".join(f'<script src="/javascript/{s}.js" defer></script>' for s in ("klok", *scripts)),
    })
    waarden["inhoud"] = vul(sjabloon, waarden)
    waarden["vergroting"] = vul("vergroting", waarden) if lichtbak else ""
    uitvoer = WORTEL / url(taal, pad).strip("/")
    if not pad.endswith(".html"):
        uitvoer = uitvoer / "index.html"
    uitvoer.parent.mkdir(parents=True, exist_ok=True)
    uitvoer.write_text(vul("basis", waarden), encoding="utf8")


def bouw_taal(taal, tekst):
    schrijf_pagina(taal, tekst, "", "start", tekst["start.titel"], tekst["start.beschrijving"],
                   blok_start(taal, tekst), scripts=["voorbeeld", "formulier"],
                   gestructureerd={"@context": "https://schema.org", "@graph": [persoon(tekst)]})
    schrijf_pagina(taal, tekst, "werk/", "werk", tekst["werk.titel"], tekst["werk.beschrijving"],
                   {"vakken": blok_werk(taal, tekst)}, actief="werk/", scripts=["voorbeeld", "vergroting"], lichtbak=True)
    ids = [pid for pid, _ in g.PROJECTEN]
    for volgorde, pid in enumerate(ids, 1):
        volgend = ids[volgorde % len(ids)]
        aantal = len(dict(g.PROJECTEN)[pid])
        schrijf_pagina(taal, tekst, f"project/{pid}/", "project", f'{tekst[f"project.{pid}.titel"]} — {NAAM}',
                       tekst[f"project.{pid}.beschrijving"], {
            "projecttitel": veilig(tekst[f"project.{pid}.titel"]),
            "projectondertitel": veilig(tekst[f"project.{pid}.ondertitel"]),
            "projectintro": veilig(tekst[f"project.{pid}.intro"]),
            "casenummer": f'{tekst["project.case"]} {nummer(volgorde)} / {nummer(len(ids))}',
            "project_gegevens": blok_gegevens(tekst, pid, aantal),
            "onderdelen": blok_onderdelen(tekst, pid),
            "volgend_url": url(taal, f"project/{volgend}/"), "volgend_titel": veilig(tekst[f"project.{volgend}.titel"]),
        }, actief="werk/", scripts=["vergroting"], lichtbak=True,
            gestructureerd={"@context": "https://schema.org", "@type": "CreativeWork",
                            "name": tekst[f"project.{pid}.titel"], "description": tekst[f"project.{pid}.beschrijving"],
                            "url": g.DOMEIN + url(taal, f"project/{pid}/"), "inLanguage": taal,
                            "image": f"{g.DOMEIN}/afbeeldingen/omslag/{pid}.webp",
                            "author": {"@id": f"{g.DOMEIN}/#afonso"}})
    schrijf_pagina(taal, tekst, "fotografie/", "fotografie", tekst["fotografie.titel"], tekst["fotografie.beschrijving"],
                   {"foto_kaders": blok_fotos(tekst)}, actief="fotografie/", scripts=["vergroting"], lichtbak=True, donker=True)
    schrijf_pagina(taal, tekst, "film/", "film", tekst["film.titel"], tekst["film.beschrijving"],
                   {"film_lijst": blok_films(taal, tekst)}, actief="film/", donker=True)
    schrijf_pagina(taal, tekst, "privacy/", "privacy", tekst["privacy.titel"], tekst["privacy.beschrijving"], {})
    schrijf_pagina(taal, tekst, "404.html", "fout", tekst["fout.titel"], tekst["fout.beschrijving"], {})


def schrijf_sitemap():
    paden = ["", "werk/", *[f"project/{p}/" for p, _ in g.PROJECTEN], "fotografie/", "film/", "privacy/"]
    regels = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for pad in paden:
        for taal in g.TALEN:
            regels.append(f"<url><loc>{g.DOMEIN}{url(taal, pad)}</loc>")
            regels += [f'<xhtml:link rel="alternate" hreflang="{t}" href="{g.DOMEIN}{url(t, pad)}"/>' for t in g.TALEN]
            regels.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{g.DOMEIN}{url("nl", pad)}"/></url>')
    regels.append("</urlset>")
    (WORTEL / "sitemap.xml").write_text("\n".join(regels), encoding="utf8")


def main():
    teksten = laad_teksten()
    for taal in g.TALEN:
        bouw_taal(taal, teksten[taal])
    schrijf_sitemap()
    print("Klaar: 3 talen gebouwd.")


if __name__ == "__main__":
    main()
