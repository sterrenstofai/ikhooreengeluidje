"""Haalt per nummer uit data/kern.json de ruwe gegevens op en zet ze in data/ruw/<slug>.json.

- MusicBrainz: de opname met de meeste relaties (zoeken op titel, en via het album),
  met credits, samples en ISRC's.
- Discogs: de release met de meeste credits (hoofdrelease plus de oudste versies).
- iTunes: de preview (alleen de link, geen audio).

Bestaande bestanden worden overgeslagen, tenzij je --opnieuw meegeeft (of slugs noemt).
"""
import json, re, sys
from pathlib import Path
from bronnen import mb, discogs, itunes

ROOT = Path(__file__).resolve().parent.parent
RUW = ROOT / "data" / "ruw"
SLECHT = re.compile(r"live|remix|mix\b|edit|demo|instrumental|a ?cappella|karaoke|version|cover|session|rehearsal|take", re.I)
INC = "artist-rels+recording-rels+work-rels+releases+isrcs+artist-credits"

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("&", "and"))

# ---------- MusicBrainz ----------

def mb_kandidaten(n):
    titel, artiest = n.get("zoektitel", n["titel"]), n.get("zoekartiest", n["artiest"])
    q = f'recording:"{titel}" AND artist:"{artiest}"'
    alle = {}
    for extra in ([f' AND release:"{n["album"]}"'] if n.get("album") else []) + [""]:
        for r in (mb("recording", query=q + extra, limit=60) or {}).get("recordings", []):
            alle.setdefault(r["id"], r)
    goed = [r for r in alle.values() if not SLECHT.search(r.get("disambiguation", "")) and norm(r["title"]).startswith(norm(titel)[:12])]
    goed.sort(key=lambda r: -len(r.get("releases", [])))
    ids = [r["id"] for r in goed[:6]]
    # via het album: de opname op de oorspronkelijke release
    if n.get("album"):
        rels = (mb("release", query=f'release:"{n["album"]}" AND artist:"{artiest}" AND status:official', limit=10) or {}).get("releases", [])
        for r in [r for r in rels if norm(r["title"]) == norm(n["album"])][:3]:
            rel = mb("release/" + r["id"], inc="recordings")
            for m in rel.get("media", []):
                for t in m.get("tracks", []):
                    if norm(t["title"]).startswith(norm(titel)[:12]):
                        ids.append(t["recording"]["id"])
    return list(dict.fromkeys(ids))

def mb_opname(n):
    if n.get("mb"):
        return mb("recording/" + n["mb"], inc=INC)
    beste = None
    for rid in mb_kandidaten(n):
        rec = mb("recording/" + rid, inc=INC)
        if rec and (not beste or len(rec.get("relations", [])) > len(beste.get("relations", []))):
            beste = rec
    return beste

def mb_werk(rec):
    for r in rec.get("relations", []):
        if r.get("target-type") == "work":
            return mb("work/" + r["work"]["id"], inc="work-rels+artist-rels+url-rels")
    return None

def mb_klassiek(n):
    w = (mb("work", query=f'work:"{n["titel"]}" AND artist:"{n["artiest"]}"', limit=3) or {}).get("works", [])
    return mb("work/" + w[0]["id"], inc="artist-rels+url-rels+work-rels") if w else None

def sample_artiesten(rec):
    """Vult bij samples de artiest in (die staat niet in de relatie zelf)."""
    for r in rec.get("relations", []):
        if r["type"] == "samples material" and r.get("recording") and not r["recording"].get("artist-credit"):
            o = mb("recording/" + r["recording"]["id"], inc="artist-credits+releases")
            if o:
                r["recording"]["artist-credit"] = o.get("artist-credit", [])
                r["recording"]["first-release-date"] = o.get("first-release-date")
                r["recording"]["releases_n"] = len(o.get("releases", []))

# ---------- Discogs ----------

def discogs_release(n):
    if n.get("klassiek"):
        return None
    if n.get("discogs_master"):
        master = discogs(f"masters/{n['discogs_master']}")
    else:
        zoek = n.get("album") or n.get("zoektitel", n["titel"])
        q = {"artist": n.get("zoekartiest", n["artiest"]), "release_title": zoek, "type": "master"}
        res = (discogs("database/search?" + __import__("urllib.parse").parse.urlencode(q)) or {}).get("results", [])
        if not res:
            return None
        res.sort(key=lambda r: (norm(zoek) != norm(r["title"].split(" - ", 1)[-1]), int(r.get("year") or 9999)))
        master = discogs(res[0]["resource_url"])
    versies = (discogs(f"masters/{master['id']}/versions?per_page=50&sort=released&sort_order=asc") or {}).get("versions", [])
    beste, score = None, -1
    for rid in dict.fromkeys([master["main_release"]] + [v["id"] for v in versies[:6]]):
        r = discogs(f"releases/{rid}")
        if not r:
            continue
        s = len(r.get("extraartists", [])) + sum(len(t.get("extraartists", [])) for t in r.get("tracklist", []))
        if s > score:
            beste, score = r, s
    return beste

# ---------- iTunes ----------

def itunes_preview(n):
    term = f'{n.get("zoekartiest", n["artiest"])} {n.get("zoektitel", n["titel"])}' if not n.get("klassiek") else "Ravel Boléro"
    res = (itunes(term=term, entity="song", limit=25, country="NL") or {}).get("results", [])
    titel = norm(n.get("zoektitel", n["titel"]))[:10]
    art = norm(n.get("zoekartiest", n["artiest"]))[:6]
    def score(r):
        t = r.get("trackName", "")
        return (
            not norm(t).startswith(titel),
            not (art in norm(r.get("artistName", "")) or n.get("klassiek")),
            bool(SLECHT.search(t)) or bool(re.search(r"live|karaoke|tribute|cover", r.get("collectionName", ""), re.I)),
            not (n.get("album") and norm(n["album"])[:8] in norm(r.get("collectionName", ""))),
            r.get("releaseDate", "9999"),
        )
    res = [r for r in res if r.get("previewUrl")]
    if not res:
        return None
    r = sorted(res, key=score)[0]
    if not norm(r.get("trackName", "")).startswith(titel):
        return None
    return {k: r.get(k) for k in ("trackId", "trackName", "artistName", "collectionName", "releaseDate", "previewUrl", "trackViewUrl", "artworkUrl100", "trackTimeMillis")}

def main():
    kern = json.loads((ROOT / "data" / "kern.json").read_text())
    opnieuw = "--opnieuw" in sys.argv
    alleen = [a for a in sys.argv[1:] if not a.startswith("--")]
    RUW.mkdir(parents=True, exist_ok=True)
    for n in kern:
        doel = RUW / f"{n['slug']}.json"
        if alleen and n["slug"] not in alleen:
            continue
        if doel.exists() and not opnieuw and not alleen:
            continue
        print(n["slug"], file=sys.stderr)
        uit = {"kern": n}
        if n.get("klassiek"):
            uit["mb_werk"] = mb_klassiek(n)
        else:
            rec = mb_opname(n)
            if rec:
                sample_artiesten(rec)
            uit["mb"] = rec
            uit["mb_werk"] = mb_werk(rec) if rec else None
        uit["discogs"] = discogs_release(n)
        uit["itunes"] = itunes_preview(n)
        doel.write_text(json.dumps(uit, ensure_ascii=False))

if __name__ == "__main__":
    main()
