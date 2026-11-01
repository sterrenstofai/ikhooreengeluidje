"""Maakt korte klankjes per instrument uit de University of Iowa Musical Instrument Samples.

Die opnames zijn vrij te gebruiken, zonder beperkingen (theremin.music.uiowa.edu/MIS.html).
Per instrument: losse noten achter elkaar (do-mi-sol), uit losse opnames of uit een toonladder geknipt.
Schrijft site/klanken/<sleutel>.mp3 en site/data/klanken.json. Vraagt ffmpeg.
Gebruik: python3 scripts/klanken_maken.py [sleutel ...]
"""
import json, subprocess, sys, tempfile, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASIS = "https://theremin.music.uiowa.edu/sound files/"
UA = "ikhooreengeluidje/0.1 ( https://ikhooreengeluidje.nl )"
LADDER_S, NOOT_S, LAATSTE_S, STUK_S = 4.2, 0.75, 1.6, 2.5

def haal(pad, doel):
    url = urllib.parse.quote(BASIS + pad, safe=":/")
    for poging in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120) as r:
                doel.write_bytes(r.read())
            return
        except OSError as e:
            print("  opnieuw:", e, file=sys.stderr)
            __import__("time").sleep(5 * (poging + 1))
    raise RuntimeError(url)

def knip(bron, doel, duur):
    """Stilte aan het begin eraf, inkorten, zacht uitfaden, mono 44,1 kHz."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bron), "-af",
                    f"silenceremove=start_periods=1:start_threshold=-50dB,atrim=0:{duur},afade=t=out:st={max(0, duur - 0.25)}:d=0.25",
                    "-ac", "1", "-ar", "44100", str(doel)], check=True)

def inzetten(bron):
    """Begintijden van de noten in een toonladder: waar het volume na een stille stukje weer omhoog schiet."""
    import numpy as np
    ruw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(bron), "-ac", "1", "-ar", "22050", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(ruw, np.float32)
    raam = 441  # 20 ms
    rms = np.sqrt(np.mean(x[: len(x) // raam * raam].reshape(-1, raam) ** 2, axis=1)) + 1e-9
    db = 20 * np.log10(rms / rms.max())
    tijden, stil = [], 999
    for k, v in enumerate(db):
        if v < -45:
            stil += 1
        elif v > -30 and stil >= 8:  # minstens 0,16 s stil geweest
            tijden.append(k * raam / 22050)
            stil = 0
        elif v >= -45:
            stil = 0 if v > -30 else stil
    return tijden

def knip_vanaf(bron, doel, start, duur):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, start - 0.02):.3f}", "-t", f"{duur}", "-i", str(bron), "-af",
                    f"afade=t=out:st={max(0, duur - 0.25)}:d=0.25", "-ac", "1", "-ar", "44100", str(doel)], check=True)

def main():
    bronnen = {k: v for k, v in json.loads((ROOT / "data" / "klanken_bronnen.json").read_text()).items() if not k.startswith("_")}
    alleen = sys.argv[1:]
    uitmap = ROOT / "site" / "klanken"; uitmap.mkdir(parents=True, exist_ok=True)
    pad = ROOT / "site" / "data" / "klanken.json"
    lijst = json.loads(pad.read_text()) if pad.exists() else {}
    for k, b in bronnen.items():
        if alleen and k not in alleen:
            continue
        print(k, file=sys.stderr)
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            delen = []
            if "noten" in b:
                for i, p in enumerate(b["noten"]):
                    haal(p, t / f"r{i}.aif")
                    knip(t / f"r{i}.aif", t / f"d{i}.wav", LAATSTE_S if i == len(b["noten"]) - 1 else NOOT_S)
                    delen.append(t / f"d{i}.wav")
                bron = [BASIS + p for p in b["noten"]]
            elif "ladder" in b:
                # chromatische toonladder: noot 1, 5 en 8 zijn do, mi en sol
                haal(b["ladder"], t / "r.aif")
                tijden = inzetten(t / "r.aif")
                kies = [i for i in (0, 4, 7) if i < len(tijden)] or [0]
                for j, i in enumerate(kies):
                    knip_vanaf(t / "r.aif", t / f"d{j}.wav", tijden[i], LAATSTE_S if j == len(kies) - 1 else NOOT_S)
                    delen.append(t / f"d{j}.wav")
                bron = [BASIS + b["ladder"]]
            else:
                haal(b["stuk"], t / "r.aif")
                knip(t / "r.aif", t / "d.wav", STUK_S)
                delen.append(t / "d.wav")
                bron = [BASIS + b["stuk"]]
            (t / "lijst.txt").write_text("".join(f"file '{d}'\n" for d in delen))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(t / "lijst.txt"),
                            "-af", "loudnorm=I=-18:TP=-1.5", "-ar", "44100", "-ac", "1", "-b:a", "96k", str(uitmap / f"{k}.mp3")], check=True)
        duur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(uitmap / f"{k}.mp3")],
                                    capture_output=True, text=True).stdout)
        lijst[k] = {"pad": f"/klanken/{k}.mp3", "duur": round(duur, 1), "bron": "University of Iowa Musical Instrument Samples",
                    "bron_url": "https://theremin.music.uiowa.edu/MIS.html", "bestanden": bron}
    pad.write_text(json.dumps(lijst, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
