"""Gedeelde ophaalcode voor MusicBrainz, Discogs en iTunes, met nette pauzes."""
import json, sys, time, urllib.error, urllib.parse, urllib.request

UA = "ikhooreengeluidje/0.1 ( https://ikhooreengeluidje.nl )"
_laatst = {}

def _haal(url, host, pauze, pogingen=5):
    for poging in range(pogingen):
        wacht = _laatst.get(host, 0) + pauze - time.time()
        if wacht > 0:
            time.sleep(wacht)
        _laatst[host] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  {host} {e.code}, opnieuw", file=sys.stderr)
        except Exception as e:
            print(f"  {host} {e}, opnieuw", file=sys.stderr)
        time.sleep(min(60, 5 * 2 ** poging))
    raise RuntimeError(url)

def mb(pad, **params):
    params["fmt"] = "json"
    return _haal("https://musicbrainz.org/ws/2/" + pad + "?" + urllib.parse.urlencode(params), "mb", 1.1)

def discogs(url):
    return _haal(url if url.startswith("http") else "https://api.discogs.com/" + url, "discogs", 2.6)

def itunes(**params):
    """Ongeveer 20 vragen per minuut."""
    return _haal("https://itunes.apple.com/search?" + urllib.parse.urlencode(params), "itunes", 3.5)
