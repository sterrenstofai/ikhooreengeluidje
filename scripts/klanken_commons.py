"""Klanken van Wikimedia Commons voor instrumenten die niet in de Iowa-collectie zitten
(drumstel, basgitaar, synthesizer, drumcomputer). Draait in een GitHub Action, omdat Commons
vaak gewone machines blokkeert.

Per sleutel uit data/klanken_commons.json: zoek geluidsbestanden, alleen vrije licenties
(publiek domein, CC0, CC BY, CC BY-SA), het liefst korter dan een minuut. Het eerste bestand
wordt een klankje van ongeveer vijf seconden in site/klanken/<sleutel>.mp3. Alle kandidaten
komen in data/klanken_kandidaten.json, zodat je een betere kunt kiezen met 'bestand'.
Vraagt ffmpeg.
"""
import html, json, re, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "ikhooreengeluidje/0.1 ( https://ikhooreengeluidje.nl )"
API = "https://commons.wikimedia.org/w/api.php"
VRIJ = re.compile(r"^(public domain|pd|cc0|cc[ -]by(-sa)?[ -]?\d|cc[ -]by(-sa)?$)", re.I)
DUUR = 5.0

def haal(url, ruw=False):
    for poging in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90) as r:
                time.sleep(1.0)
                return r.read() if ruw else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) or e.code >= 500:
                time.sleep(int(e.headers.get("retry-after", 10 * (poging + 1))) + 1); continue
            raise
    raise RuntimeError(url)

def api(**p):
    return haal(API + "?" + urllib.parse.urlencode({"format": "json", "formatversion": 2, **p}))

def tekst(m, k):
    return html.unescape(re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", ""))).strip().split("\n")[0].strip()

def info(titels):
    d = api(action="query", titles="|".join(titels), prop="imageinfo", iiprop="url|extmetadata|mediatype|metadata|size")
    uit = []
    for p in d["query"]["pages"]:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mediatype") != "AUDIO":
            continue
        m = ii.get("extmetadata", {})
        lengte = next((x["value"] for x in ii.get("metadata") or [] if x["name"] in ("length", "playtime_seconds")), None)
        uit.append({"bestand": p["title"].removeprefix("File:"), "url": ii["url"], "pagina": ii["descriptionurl"],
                    "licentie": tekst(m, "LicenseShortName"), "maker": maker_van(tekst(m, "Artist")[:120]),
                    "omschrijving": tekst(m, "ImageDescription")[:200], "lengte": float(lengte) if lengte else None})
    return uit

def zoek(termen):
    gezien, uit = set(), []
    for t in termen:
        d = api(action="query", list="search", srsearch=f"filetype:audio {t}", srnamespace=6, srlimit=15)
        titels = [r["title"] for r in d["query"]["search"] if r["title"] not in gezien]
        gezien.update(titels)
        if titels:
            uit += info(titels)
    # geen uitspraakbestanden (Lingua Libre, LL-...) en geen MIDI: dat zijn geen opnames van het instrument
    vrij = [k for k in uit if VRIJ.search(k["licentie"]) and not k["bestand"].startswith("LL-") and not k["bestand"].lower().endswith((".mid", ".midi"))]
    vrij.sort(key=lambda k: (k["lengte"] is None, (k["lengte"] or 0) > 60, k["lengte"] or 0))
    return vrij

def maker_van(t):
    """Commons zegt soms alleen 'No machine-readable author provided'; de naam staat dan op de bestandspagina."""
    return "maker: zie de bestandspagina" if not t or t.lower().startswith("no machine-readable") else t

def main():
    bronnen = {k: v for k, v in json.loads((ROOT / "data" / "klanken_commons.json").read_text()).items() if not k.startswith("_")}
    alleen = sys.argv[1:]
    pad = ROOT / "site" / "data" / "klanken.json"
    lijst = json.loads(pad.read_text()) if pad.exists() else {}
    kpad = ROOT / "data" / "klanken_kandidaten.json"
    kandidaten = json.loads(kpad.read_text()) if kpad.exists() else {}
    for k, b in bronnen.items():
        if alleen and k not in alleen:
            continue
        try:
            if b.get("bestand"):
                keus = info(["File:" + b["bestand"]])[0]
            else:
                lijstje = zoek(b["zoek"])
                kandidaten[k] = lijstje[:12]
                if not lijstje:
                    print(k, ": niets gevonden"); continue
                keus = lijstje[0]
            with tempfile.TemporaryDirectory() as t:
                bron = Path(t) / "bron"
                bron.write_bytes(haal(keus["url"], ruw=True))
                start = b.get("start", 0)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(bron), "-af",
                                f"silenceremove=start_periods=1:start_threshold=-45dB,atrim=0:{DUUR},afade=t=out:st={DUUR - 0.4}:d=0.4,loudnorm=I=-18:TP=-1.5",
                                "-ac", "1", "-ar", "44100", "-b:a", "96k", str(ROOT / "site" / "klanken" / f"{k}.mp3")], check=True)
            lijst[k] = {"pad": f"/klanken/{k}.mp3", "duur": DUUR, "bron": "Wikimedia Commons", "bron_url": keus["pagina"],
                        "bestand": keus["bestand"], "licentie": keus["licentie"], "maker": keus["maker"]}
            print(k, "->", keus["bestand"], keus["licentie"], keus["lengte"])
        except Exception as e:
            print(k, ": mislukt,", e)
    pad.write_text(json.dumps(lijst, ensure_ascii=False, indent=1))
    kpad.write_text(json.dumps(kandidaten, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
