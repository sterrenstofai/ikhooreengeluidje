"""Foto's van instrumenten en apparaten van Wikimedia Commons.

Draait in een GitHub Action: Commons blokkeert vaak gewone machines (429).
Per sleutel uit data/foto_bronnen.json: de afbeelding (P18) van het Wikidata-item,
of het bestand dat je zelf hebt gekozen. Alleen vrije licenties (publiek domein,
CC0, CC BY, CC BY-SA). Schrijft site/fotos/<sleutel>.webp en site/data/fotos.json
met maker en licentie, die op de site bij de foto staan.

Elke foto moet je daarna zelf bekijken: P18 is niet altijd een goede foto van
het instrument. Een slechte vervang je met 'bestand' in foto_bronnen.json.
"""
import html, io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
UA = "ikhooreengeluidje/0.1 ( https://ikhooreengeluidje.nl )"
VRIJ = re.compile(r"^(public domain|pd|cc0|cc[ -]by(-sa)?[ -]?\d|cc[ -]by(-sa)?$)", re.I)

def haal(url, ruw=False):
    for poging in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                time.sleep(1.0)
                return r.read() if ruw else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) or e.code >= 500:
                time.sleep(int(e.headers.get("retry-after", 10 * (poging + 1))) + 1); continue
            raise
    raise RuntimeError(url)

def p18(labels):
    waarden = " ".join('"%s"@en' % l for l in labels)
    q = f"""SELECT ?label ?img (COUNT(?site) AS ?n) WHERE {{ VALUES ?label {{ {waarden} }} ?item rdfs:label ?label ; wdt:P18 ?img .
            OPTIONAL {{ ?site schema:about ?item }} }} GROUP BY ?label ?img"""
    rijen = haal("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))["results"]["bindings"]
    # eerst de volgorde van de labels, dan het bekendste item
    rijen.sort(key=lambda r: (labels.index(r["label"]["value"]), -int(r["n"]["value"])))
    return urllib.parse.unquote(rijen[0]["img"]["value"].rsplit("/", 1)[-1]) if rijen else None

def info(bestand):
    d = haal("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": 2, "titles": "File:" + bestand,
        "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1000}))
    ii = d["query"]["pages"][0]["imageinfo"][0]
    m = ii.get("extmetadata", {})
    tekst = lambda k: html.unescape(re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", ""))).strip().split("\n")[0].strip()
    return {"bestand": bestand, "thumb": ii.get("thumburl") or ii["url"], "pagina": ii["descriptionurl"],
            "licentie": tekst("LicenseShortName"), "maker": tekst("Artist")[:120] or "onbekend"}

def main():
    bronnen = {k: v for k, v in json.loads((ROOT / "data" / "foto_bronnen.json").read_text()).items() if not k.startswith("_")}
    doel = ROOT / "site" / "fotos"; doel.mkdir(parents=True, exist_ok=True)
    pad = ROOT / "site" / "data" / "fotos.json"
    oud = json.loads(pad.read_text()) if pad.exists() else {}
    uit, missers = {}, []
    for k, b in bronnen.items():
        naam = k.replace("apparaat:", "")
        try:
            bestand = b.get("bestand") or p18(b["en"])
            if not bestand:
                missers.append(f"{k}: geen afbeelding in Wikidata"); continue
            if k in oud and oud[k]["bestand"] == bestand and (doel / f"{naam}.webp").exists():
                uit[k] = oud[k]; continue
            i = info(bestand)
            if not VRIJ.search(i["licentie"]):
                missers.append(f"{k}: licentie '{i['licentie']}' van {bestand}"); continue
            beeld = Image.open(io.BytesIO(haal(i["thumb"], ruw=True))).convert("RGB")
            beeld.thumbnail((1000, 1000))
            beeld.save(doel / f"{naam}.webp", "WEBP", quality=82)
            uit[k] = {**{x: i[x] for x in ("bestand", "pagina", "licentie", "maker")}, "pad": f"/fotos/{naam}.webp",
                      "breed": beeld.width, "hoog": beeld.height}
            print(k, "->", bestand, i["licentie"])
        except Exception as e:
            missers.append(f"{k}: {e}")
    pad.write_text(json.dumps(uit, ensure_ascii=False, indent=1))
    print(f"\n{len(uit)} foto's. Niet gelukt:", *missers, sep="\n  ")

if __name__ == "__main__":
    main()
