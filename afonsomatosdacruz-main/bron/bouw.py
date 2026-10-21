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
    """Maakt tekst veilig voor HTML, maar laat <br> en <em> staan."""
    return re.sub(r"&lt;(/?(?:br|em))&gt;", r"<\1>", html.escape(tekst, quote=False))


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


def bestandsmaat(pad):
    """Breedte en hoogte van een los beeld, bijvoorbeeld 'omslag/smak.webp'."""
    if pad not in maten:
        with Image.open(WORTEL / f"afbeeldingen/{pad}") as bestand:
            maten[pad] = bestand.size
    return maten[pad]


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
def kader(tekst, lijst, titel="", uitleg="", start=0, sizes="50vw", laden="lazy"):
    """Een kader met één beeld dat bij een klik alle beelden van de lijst groot toont."""
    map, naam = lijst[start]
    return (f'<a class="kader" href="/afbeeldingen/{map}/{naam}-groot.webp" data-start="{start}" '
            f'data-beelden="{vergroting_gegevens(tekst, lijst)}" data-titel="{html.escape(titel)}" '
            f'data-tekst="{html.escape(uitleg)}" aria-haspopup="dialog">{beeld(tekst, map, naam, sizes, laden)}</a>')


def los_beeld(pad, alt="", laden="lazy"):
    """Een beeld zonder klein/groot-paar, zoals een omslag of filmstill. Breedte en hoogte komen uit het bestand."""
    breedte, hoogte = bestandsmaat(pad)
    return (f'<img src="/afbeeldingen/{pad}" width="{breedte}" height="{hoogte}" alt="{html.escape(alt)}" '
            f'loading="{laden}" decoding="async">')


def rij(nr, titel, soort, adres, mini, actie, extra=""):
    """Een regel in een lijst: nummer, titel, soort, een klein beeld en wat er gebeurt bij een klik.
    Bij hover verschijnt op een scherm met muis een groter voorbeeld (data-voorbeeld)."""
    breedte, hoogte = bestandsmaat(mini)
    return (f'<a class="rij" href="{adres}" data-voorbeeld="/afbeeldingen/{mini}" {extra}><span class="nr">{nummer(nr)}</span>'
            f'<span class="rij-tekst"><span class="titel">{veilig(titel)}</span><span class="soort">{veilig(soort)}</span></span>'
            f'<span class="rij-actie">{veilig(actie)}</span>'
            f'<span class="mini"><img src="/afbeeldingen/{mini}" width="{breedte}" height="{hoogte}" alt="" loading="lazy" decoding="async"></span></a>')


def rij_werk(tekst, nr, wid, lijst):
    map, naam = lijst[0]
    titel, uitleg = tekst[f"werk.{wid}.titel"], tekst[f"werk.{wid}.tekst"]
    aantal = f" · {len(lijst)} {tekst['werk.rij_beelden']}" if len(lijst) > 1 else ""
    extra = (f'data-beelden="{vergroting_gegevens(tekst, lijst)}" data-titel="{html.escape(titel)}" '
             f'data-tekst="{html.escape(uitleg)}" aria-haspopup="dialog"')
    return rij(nr, titel, tekst[f"werk.{wid}.soort"] + aantal, f"/afbeeldingen/{map}/{naam}-groot.webp",
               f"{map}/{naam}-klein.webp", f'{tekst["werk.bekijk"]} ↗', extra)


def rij_project(taal, tekst, nr, pid):
    return rij(nr, tekst[f"project.{pid}.titel"], tekst[f"project.{pid}.ondertitel"],
               url(taal, f"project/{pid}/"), f"omslag/{pid}.webp", f'{tekst["werk.bekijk_project"]} →')


def verhouding(lijst, film):
    """Breedte gedeeld door hoogte van het eerste beeld of, zonder beeld, van de filmstill."""
    breedte, hoogte = maat(*lijst[0], "klein") if lijst else bestandsmaat(f"film/{film}.webp")
    return breedte / hoogte


def video(tekst, naam, titel, onderschrift=""):
    """Een film met posterbeeld. Er wordt niets geladen voor iemand op afspelen klikt."""
    breedte, hoogte = bestandsmaat(f"film/{naam}.webp")
    soort = "staand" if breedte < hoogte else "breed"
    return (f'<figure class="film film-{soort}"><video controls preload="none" playsinline poster="/afbeeldingen/film/{naam}.webp" '
            f'width="{breedte}" height="{hoogte}" style="aspect-ratio: {breedte} / {hoogte}" aria-label="{html.escape(titel)}">'
            f'<source src="/video/{naam}.mp4" type="video/mp4">{veilig(tekst["film.geen_video"])}</video>{onderschrift}</figure>')


# ---------- Blokken per pagina ----------
def kaart_project(taal, tekst, nr, pid):
    """Een project op de startpagina: groot beeld, titel en een duidelijke link naar de hele case."""
    aantal = len(dict(g.PROJECTEN)[pid])
    meta = f'{tekst["project.soort_school"]} · {aantal} {tekst["project.label_onderdelen"].lower()}'
    return (f'<a class="case case-{pid}" href="{url(taal, f"project/{pid}/")}">'
            f'<div class="case-beeld">{los_beeld(f"omslag/{pid}.webp")}</div>'
            f'<div class="case-tekst"><span class="nr">{nummer(nr)}</span><h3>{veilig(tekst[f"project.{pid}.titel"])}</h3>'
            f'<p class="ondertitel">{veilig(tekst[f"project.{pid}.ondertitel"])}</p><p class="meta">{veilig(meta)}</p>'
            f'<span class="pijl">{veilig(tekst["start.project_bekijken"])} →</span></div></a>')


def blok_start(taal, tekst):
    projecten = "".join(kaart_project(taal, tekst, i, pid) for i, (pid, _) in enumerate(g.PROJECTEN, 1))
    fotos = "".join(f'<a class="foto-link start-foto-{n}" href="{url(taal, "fotografie/")}">'
                    f'{beeld(tekst, "fotografie", f"straat-{i:02d}", "(min-width: 900px) 45vw, 90vw")}</a>'
                    for n, i in enumerate(g.FOTOS_START, 1))
    films = "".join(f'<a class="film-link start-film-{n}" href="{url(taal, "film/")}">{los_beeld(f"film/{fid}.webp")}'
                    f'<span class="bijschrift"><span class="nr">{nummer(n)}</span>{veilig(tekst[f"film.{fid}.titel"])}'
                    f'<span class="klein">{tekst[f"film.{fid}.duur"]}</span></span></a>'
                    for n, (fid, _) in enumerate(g.FILMS, 1))
    opleiding = "".join(f'<li><span>{veilig(tekst[f"over.opleiding_{i}_jaar"])}</span>{veilig(tekst[f"over.opleiding_{i}"])}</li>'
                        for i in (1, 2, 3))
    cv_taal = "nl" if taal == "nl" else "en"  # er is geen Franse cv: Frans verwijst naar de Engelse
    return {"start_projecten": projecten, "start_fotos": fotos, "start_films": films, "opleiding_lijst": opleiding,
            "over_foto": beeld(tekst, "algemeen", "aan-het-werk", "(min-width: 900px) 45vw, 100vw"),
            "cv_url": f"/cv/cv-afonso-matos-da-cruz-{cv_taal}.pdf"}


def blok_werk(taal, tekst):
    vakken = [("projecten", "".join(rij_project(taal, tekst, i, pid) for i, (pid, _) in enumerate(g.PROJECTEN, 1)))]
    for vak, werken in g.VAKKEN:
        vakken.append((vak, "".join(rij_werk(tekst, i, wid, lijst) for i, (wid, lijst) in enumerate(werken, 1))))
    sprong = "".join(f'<a href="#vak-{vak}"><span class="nr">{nummer(i)}</span> {veilig(tekst[f"werk.vak_{vak}"])}</a>'
                     for i, (vak, _) in enumerate(vakken, 1))
    secties = "".join(
        f'<section id="vak-{vak}" class="vak raster"><div class="vakkop"><span class="nr">{nummer(i)}</span><h2>{veilig(tekst[f"werk.vak_{vak}"])}</h2>'
        f'<p>{veilig(tekst[f"werk.vak_{vak}_tekst"])}</p></div><div class="lijst">{rijen}</div></section>'
        for i, (vak, rijen) in enumerate(vakken, 1))
    return {"vakken": secties, "werk_sprong": sprong}


def blok_gegevens(tekst, pid, aantal):
    rijen = [("project.label_soort", tekst["project.soort_school"]),
             ("project.label_school", f'{tekst["project.school_dbsdw"]} · {tekst[f"project.{pid}.klas"]}')]
    if f"project.{pid}.wanneer" in tekst:
        rijen.append(("project.label_wanneer", tekst[f"project.{pid}.wanneer"]))
    rijen += [("project.label_onderdelen", str(aantal)), ("project.label_gemaakt", tekst[f"project.{pid}.gemaakt"])]
    return "".join(f'<div><dt>{veilig(tekst[k])}</dt><dd>{veilig(w)}</dd></div>' for k, w in rijen)


def blok_opening(tekst, pid):
    return los_beeld(f"omslag/{pid}.webp", tekst[f"alt.omslag/{pid}"], laden="eager")


def blok_onderdelen(tekst, pid):
    resultaat = []
    for i, (oid, lijst, film) in enumerate(dict(g.PROJECTEN)[pid], 1):
        sleutel = f"project.{pid}.{oid}"
        titel, uitleg = tekst[f"{sleutel}.titel"], tekst[f"{sleutel}.tekst"]
        if len(lijst) + bool(film) > 1:
            soort, sizes = "twee", "(min-width: 900px) 45vw, 100vw"
        elif verhouding(lijst, film) < 0.9:
            soort, sizes = "staand", "(min-width: 900px) 50vw, 100vw"
        else:
            soort, sizes = "breed", "(min-width: 900px) 85vw, 100vw"
        media = "".join(kader(tekst, lijst, titel, uitleg, start=n, sizes=sizes) for n in range(len(lijst)))
        if film:
            media += video(tekst, film, tekst[f"film.{film}.titel"])
        resultaat.append(f'<section class="onderdeel raster {soort}"><span class="nr">{nummer(i)}</span><h3>{veilig(titel)}</h3>'
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
    fotos = [("fotografie", f"straat-{i:02d}") for i in g.FOTOS]
    totaal = nummer(len(fotos))
    return "".join(
        f'<figure class="foto foto-{n}">{kader(tekst, fotos, start=n, sizes="(min-width: 900px) 50vw, 100vw", laden="eager" if n == 0 else "lazy")}'
        f'<figcaption class="meta"><span class="nr">{nummer(n + 1)}</span> / {totaal}</figcaption></figure>'
        for n in range(len(fotos)))


# ---------- Pagina's ----------
def menu(taal, tekst, actief):
    items = [("werk/", "nav.werk"), ("fotografie/", "nav.fotografie"), ("film/", "nav.film"),
             ("#over", "nav.over"), ("#contact", "nav.contact")]
    schakels = []
    for i, (pad, sleutel) in enumerate(items, 1):
        adres = url(taal) + pad if pad.startswith("#") else url(taal, pad)
        huidig = ' aria-current="page"' if pad == actief else ""
        schakels.append(f'<a href="{adres}"{huidig}><span class="nr">{nummer(i)}</span> {veilig(tekst[sleutel])}</a>')
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
                   gestructureerd=None):
    waarden = {sleutel: veilig(waarde) for sleutel, waarde in tekst.items()}
    waarden.update(blokken)
    waarden.update({
        "taal": taal, "landcode": LANDCODES[taal], "domein": g.DOMEIN,
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
                   blok_werk(taal, tekst), actief="werk/", scripts=["voorbeeld", "vergroting"], lichtbak=True)
    ids = [pid for pid, _ in g.PROJECTEN]
    for volgorde, pid in enumerate(ids, 1):
        volgend = ids[volgorde % len(ids)]
        aantal = len(dict(g.PROJECTEN)[pid])
        schrijf_pagina(taal, tekst, f"project/{pid}/", "project", f'{tekst[f"project.{pid}.titel"]} — {NAAM}',
                       tekst[f"project.{pid}.beschrijving"], {
            "project_id": pid, "project_opening": blok_opening(tekst, pid),
            "projecttitel": veilig(tekst[f"project.{pid}.titel"]),
            "projectondertitel": veilig(tekst[f"project.{pid}.ondertitel"]),
            "projectintro": veilig(tekst[f"project.{pid}.intro"]),
            "casenummer": f'{veilig(tekst["project.case"])} <span class="nr">{nummer(volgorde)}</span> / {nummer(len(ids))}',
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
                   {"foto_kaders": blok_fotos(tekst)}, actief="fotografie/", scripts=["vergroting"], lichtbak=True)
    schrijf_pagina(taal, tekst, "film/", "film", tekst["film.titel"], tekst["film.beschrijving"],
                   {"film_lijst": blok_films(taal, tekst)}, actief="film/")
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
