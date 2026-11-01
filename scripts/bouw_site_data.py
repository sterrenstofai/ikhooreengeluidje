"""Maakt site/data/nummers.json en site/data/instrumenten.json uit data/ruw/ en data/handwerk/.

Per nummer: credits per instrument (MusicBrainz en Discogs samen, met de bron erbij),
productie, samples (met de hand en uit MusicBrainz), weetjes en de iTunes-preview.
"""
import json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUW, HAND, UIT = ROOT / "data" / "ruw", ROOT / "data" / "handwerk", ROOT / "site" / "data"

# instrument-sleutel: (Nederlandse naam, lidwoord, groep)
INSTRUMENTEN = {
    "zang": ("zang", "de", "stem"), "achtergrondzang": ("achtergrondzang", "de", "stem"), "rap": ("rap", "de", "stem"),
    "drumstel": ("drumstel", "het", "slagwerk"), "drumcomputer": ("drumcomputer", "de", "elektronisch"),
    "slagwerk": ("slagwerk", "het", "slagwerk"), "handgeklap": ("handgeklap", "het", "slagwerk"),
    "vingerknippen": ("vingerknippen", "het", "slagwerk"), "tamboerijn": ("tamboerijn", "de", "slagwerk"),
    "congas": ("conga's", "de", "slagwerk"), "pauken": ("pauken", "de", "slagwerk"),
    "basgitaar": ("basgitaar", "de", "snaren"), "contrabas": ("contrabas", "de", "snaren"),
    "gitaar": ("gitaar", "de", "snaren"), "elektrische-gitaar": ("elektrische gitaar", "de", "snaren"),
    "akoestische-gitaar": ("akoestische gitaar", "de", "snaren"),
    "viool": ("viool", "de", "snaren"), "altviool": ("altviool", "de", "snaren"), "cello": ("cello", "de", "snaren"),
    "strijkers": ("strijkers", "de", "snaren"), "harp": ("harp", "de", "snaren"),
    "piano": ("piano", "de", "toetsen"), "rhodes": ("Rhodes-piano", "de", "toetsen"),
    "elektrische-piano": ("elektrische piano", "de", "toetsen"), "keyboard": ("keyboard", "het", "toetsen"),
    "orgel": ("orgel", "het", "toetsen"), "clavinet": ("clavinet", "de", "toetsen"),
    "synthesizer": ("synthesizer", "de", "elektronisch"), "sampler": ("sampler", "de", "elektronisch"),
    "vocoder": ("vocoder", "de", "elektronisch"), "talkbox": ("talkbox", "de", "elektronisch"),
    "draaitafel": ("draaitafel", "de", "elektronisch"),
    "trompet": ("trompet", "de", "blazers"), "trombone": ("trombone", "de", "blazers"),
    "saxofoon": ("saxofoon", "de", "blazers"), "altsaxofoon": ("altsaxofoon", "de", "blazers"),
    "tenorsaxofoon": ("tenorsaxofoon", "de", "blazers"), "baritonsaxofoon": ("baritonsaxofoon", "de", "blazers"),
    "blazers": ("blazers", "de", "blazers"), "dwarsfluit": ("dwarsfluit", "de", "blazers"),
    "hoorn": ("hoorn", "de", "blazers"), "klarinet": ("klarinet", "de", "blazers"), "hobo": ("hobo", "de", "blazers"),
    "fagot": ("fagot", "de", "blazers"), "celesta": ("celesta", "de", "toetsen"), "kleine-trom": ("kleine trom", "de", "slagwerk"),
}
NAAR_KEY = {"kleine trom": "kleine-trom", "dwarsfluit": "dwarsfluit", "klarinet": "klarinet", "fagot": "fagot", "hobo": "hobo",
            "trompet": "trompet", "saxofoon": "saxofoon", "hoorn": "hoorn", "celesta": "celesta", "trombone": "trombone",
            "viool": "viool", "altviool": "altviool", "cello": "cello", "contrabas": "contrabas", "harp": "harp", "pauken": "pauken"}

# volgorde telt: het eerste patroon dat past wint
PATRONEN = [
    (r"background|backing|chorus|choir", "achtergrondzang"), (r"\brap", "rap"), (r"vocal|voice|zang", "zang"),
    (r"drum machine", "drumcomputer"), (r"drums? \(drum set\)|^drums$|^drums\b|drum kit", "drumstel"),
    (r"handclap", "handgeklap"), (r"finger snap", "vingerknippen"), (r"tambourine", "tamboerijn"), (r"conga", "congas"),
    (r"timpani", "pauken"), (r"percussion", "slagwerk"),
    (r"double bass|upright bass|contrabass", "contrabas"), (r"bass", "basgitaar"),
    (r"electric guitar|lead guitar|rhythm guitar", "elektrische-gitaar"), (r"acoustic guitar", "akoestische-gitaar"), (r"guitar", "gitaar"),
    (r"viola", "altviool"), (r"violin", "viool"), (r"cello", "cello"), (r"strings", "strijkers"), (r"harp", "harp"),
    (r"rhodes", "rhodes"), (r"wurlitzer|electric piano", "elektrische-piano"), (r"clavinet", "clavinet"),
    (r"organ", "orgel"), (r"piano", "piano"), (r"keyboard", "keyboard"),
    (r"vocoder", "vocoder"), (r"talk ?box", "talkbox"), (r"sampler|emulator", "sampler"), (r"synth|moog", "synthesizer"),
    (r"turntable|scratch", "draaitafel"),
    (r"trumpet|flugelhorn", "trompet"), (r"trombone", "trombone"), (r"alto sax", "altsaxofoon"), (r"tenor sax", "tenorsaxofoon"),
    (r"baritone sax", "baritonsaxofoon"), (r"sax", "saxofoon"), (r"french horn|^horn$", "hoorn"), (r"horns|brass", "blazers"),
    (r"flute", "dwarsfluit"), (r"clarinet", "klarinet"), (r"oboe", "hobo"), (r"bassoon", "fagot"),
]
GEEN_SPEL = re.compile(r"arranged|conductor|leader|contractor|programmed|photograph|preparation|assistance|engineer|producer|mix|written|recorded|design|art|copyist|tuning|technician", re.I)
PRODUCTIE = [(r"producer|produced", "productie"), (r"mix", "mix"), (r"engineer|recorded", "opname"), (r"master", "mastering"),
             (r"arrang|instrument arranger", "arrangement"), (r"programm", "programmeren"), (r"conductor", "dirigent")]

def instrument(rol):
    if GEEN_SPEL.search(rol):
        return None
    for patroon, key in PATRONEN:
        if re.search(patroon, rol, re.I):
            return key
    return None

def schoon(naam):
    return re.sub(r"\s*\(\d+\)$", "", naam).strip()

def kredieten(r):
    """-> {instrument: {naam: set(bronnen)}}, {productierol: set(namen)}"""
    spel, prod = defaultdict(lambda: defaultdict(set)), defaultdict(set)
    rec = r.get("mb") or {}
    for x in rec.get("relations", []):
        if x.get("target-type") != "artist":
            continue
        naam = schoon(x["artist"]["name"])
        if x["type"] == "instrument":
            for a in x.get("attributes", []) or ["instrument"]:
                k = instrument(a)
                if k:
                    spel[k][naam].add("MusicBrainz")
        elif x["type"] == "vocal":
            a = " ".join(x.get("attributes", [])) or "vocal"
            spel[instrument(a) or "zang"][naam].add("MusicBrainz")
        else:
            for patroon, rol in PRODUCTIE:
                if re.search(patroon, x["type"], re.I):
                    prod[rol].add(naam); break
    d = r.get("discogs") or {}
    titel = re.sub(r"[^a-z0-9]", "", r["kern"].get("zoektitel", r["kern"]["titel"]).lower())[:10]
    track = next((t for t in d.get("tracklist", []) if re.sub(r"[^a-z0-9]", "", t.get("title", "").lower()).startswith(titel)), None)
    pos = track["position"] if track else None
    lijst = [(c, "track") for c in (track or {}).get("extraartists", [])]
    for c in d.get("extraartists", []):
        t = c.get("tracks", "")
        if not t or (pos and (pos in [s.strip() for s in re.split(r",|&", t)] or " to " in t)):
            lijst.append((c, "release"))
    for c, _ in lijst:
        naam = schoon(c.get("anv") or c["name"])
        for deel in re.split(r",\s*(?![^\[]*\])", c["role"]):
            k = instrument(deel)
            if k:
                spel[k][naam].add("Discogs")
            else:
                for patroon, rol in PRODUCTIE:
                    if re.search(patroon, deel, re.I) and not re.search(r"photo|design|art|lacquer|a&r", deel, re.I):
                        prod[rol].add(naam); break
    return spel, prod

def artiest(rec):
    return "".join(c["name"] + c.get("joinphrase", "") for c in rec.get("artist-credit", []))

def jaar(s):
    return int(s[:4]) if s and s[:4].isdigit() else None

def main():
    kern = json.loads((ROOT / "data" / "kern.json").read_text())
    slugs = {n["slug"] for n in kern}
    mb_naar_slug = {}
    ruw = {}
    for n in kern:
        p = RUW / f"{n['slug']}.json"
        if p.exists():
            ruw[n["slug"]] = json.loads(p.read_text())
            if ruw[n["slug"]].get("mb"):
                mb_naar_slug[ruw[n["slug"]]["mb"]["id"]] = n["slug"]
    def titelsleutel(t, a):
        return re.sub(r"[^a-z0-9]", "", (a.split(" ")[-1] + t).lower())
    titel_naar_slug = {titelsleutel(n["titel"], n["artiest"]): n["slug"] for n in kern}

    nummers, gebruik = [], defaultdict(list)
    for n in kern:
        r = ruw.get(n["slug"], {"kern": n})
        h = json.loads((HAND / f"{n['slug']}.json").read_text()) if (HAND / f"{n['slug']}.json").exists() else {}
        spel, prod = kredieten(r) if not n.get("klassiek") else ({}, {})
        credits = []
        for k, namen in sorted(spel.items(), key=lambda kv: (list(INSTRUMENTEN).index(kv[0]) if kv[0] in INSTRUMENTEN else 99)):
            nl, lw, groep = INSTRUMENTEN[k]
            credits.append({"key": k, "nl": nl, "wie": [{"naam": a, "bron": sorted(b)} for a, b in sorted(namen.items())]})
            gebruik[k].append(n["slug"])
        for k in [NAAR_KEY[b] for b in h.get("bezetting", []) if b in NAAR_KEY]:
            if not any(c["key"] == k for c in credits):
                credits.append({"key": k, "nl": INSTRUMENTEN[k][0], "wie": [], "bezetting": True})
                gebruik[k].append(n["slug"])
        # samples: eerst de hand, dan MusicBrainz
        erin, door = [], []
        for s in h.get("samples", []):
            item = {"type": s["type"], "wat": s["wat"], "bron": s["bron"], "nagekeken": True}
            if s["van"] in slugs:
                item["slug"] = s["van"]
            else:
                m = re.match(r"(.+?), (.+?)(?: \((\d{4})\))?$", s["van"])
                item.update({"artiest": m.group(1), "titel": m.group(2), "jaar": int(m.group(3)) if m.group(3) else None} if m else {"titel": s["van"]})
            erin.append(item)
        rec = r.get("mb") or {}
        for x in rec.get("relations", []):
            if x["type"] != "samples material" or not x.get("recording"):
                continue
            o = x["recording"]
            item = {"titel": o["title"], "artiest": artiest(o), "jaar": jaar(o.get("first-release-date")), "mb": o["id"],
                    "slug": mb_naar_slug.get(o["id"]) or titel_naar_slug.get(titelsleutel(o["title"], artiest(o) or "x")),
                    "releases": o.get("releases_n", 0)}
            if x["direction"] == "forward":
                if not any((e.get("slug") and e.get("slug") == item["slug"]) or re.sub(r"\W", "", e.get("titel", "").lower()) == re.sub(r"\W", "", o["title"].lower()) for e in erin):
                    erin.append({**item, "type": "sample", "bron": "https://musicbrainz.org/recording/" + rec["id"]})
            else:
                door.append(item)
        # 'gesampled door': uit de kern eerst, dan het meest uitgebrachte; mash-ups van hobbyisten vallen grotendeels weg
        door.sort(key=lambda d: (not d["slug"], -d["releases"]))
        # één keer per nummer, ook als MusicBrainz er meerdere opnames van kent
        gezien, uniek = set(), []
        for d in door:
            sleutel = d["slug"] or re.sub(r"\W", "", (d["artiest"] + d["titel"]).lower())
            if sleutel not in gezien:
                gezien.add(sleutel); uniek.append(d)
        door = uniek
        disc = r.get("discogs") or {}
        it = r.get("itunes")
        nummers.append({
            "slug": n["slug"], "titel": n["titel"], "artiest": n["artiest"], "jaar": n["jaar"], "album": n.get("album"),
            "klassiek": bool(n.get("klassiek")),
            "nagekeken": bool(h),
            "credits": credits,
            "productie": {k: sorted(v) for k, v in prod.items()},
            "apparaten": h.get("apparaten", []), "weetjes": h.get("weetjes", []), "tempo": h.get("tempo"),
            "samples_erin": erin, "gesampled_door": door[:10], "gesampled_door_totaal": len(door),
            "isrc": (rec.get("isrcs") or [None])[0],
            "bronnen": {"musicbrainz": rec.get("id") and "https://musicbrainz.org/recording/" + rec["id"],
                        "musicbrainz_werk": (r.get("mb_werk") or {}).get("id") and "https://musicbrainz.org/work/" + r["mb_werk"]["id"],
                        "discogs": disc.get("uri")},
            "preview": it and {"url": it["previewUrl"], "winkel": it["trackViewUrl"], "hoes": it["artworkUrl100"].replace("100x100bb", "600x600bb"),
                               "hoes_klein": it["artworkUrl100"].replace("100x100bb", "200x200bb"),
                               "van": f'{it["artistName"]}, {it["trackName"]} ({it["collectionName"]})'},
        })
    # 'gesampled door' ook vanuit de hand: als A sample uit B, dan staat A bij B
    per_slug = {x["slug"]: x for x in nummers}
    for x in nummers:
        for s in x["samples_erin"]:
            doel = per_slug.get(s.get("slug"))
            if doel and not any(d.get("slug") == x["slug"] for d in doel["gesampled_door"]):
                doel["gesampled_door"].insert(0, {"titel": x["titel"], "artiest": x["artiest"], "jaar": x["jaar"], "slug": x["slug"], "type": s["type"]})
                doel["gesampled_door_totaal"] = max(doel["gesampled_door_totaal"], len(doel["gesampled_door"]))
    instrumenten = [{"key": k, "nl": nl, "lidwoord": lw, "groep": g, "nummers": sorted(set(gebruik.get(k, [])))}
                    for k, (nl, lw, g) in INSTRUMENTEN.items() if gebruik.get(k)]
    UIT.mkdir(parents=True, exist_ok=True)
    (UIT / "nummers.json").write_text(json.dumps(nummers, ensure_ascii=False, separators=(",", ":")))
    (UIT / "instrumenten.json").write_text(json.dumps(instrumenten, ensure_ascii=False, separators=(",", ":")))
    print(len(nummers), "nummers,", len(instrumenten), "instrumenten,", sum(1 for x in nummers if x["preview"]), "met preview")

if __name__ == "__main__":
    main()
