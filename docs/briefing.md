# Nieuw project: nummers ontleden (werktitel)

Briefing om een nieuwe chat mee te starten. Geschreven na het bouwen van **Voggels** (voggels.nl). Wat daar werkte, staat hieronder als uitgangspunt.

## Het idee

Je kiest een nummer, bijvoorbeeld *In the Air Tonight* van Phil Collins, en ziet het uit elkaar gehaald:

- **Welke instrumenten en apparaten** erin zitten. Bij Phil Collins de drumcomputer (Roland CR-78), het gated-reverb-drumgeluid en de Prophet-5.
- **Wie wat speelt**: de credits per instrument.
- **De sporen**: een tijdlijn waarop je per instrument ziet wanneer het speelt, en die je per spoor kunt beluisteren of stilzetten.
- **Bij rap en hiphop: de samples.** Welk ouder nummer zit erin, waar, en hoe is het bewerkt (versneld, geknipt, geloopt)?

En net als bij Voggels: **Onderzoekjes met Fos**. Elke week samen op onderzoek: eerst luisteren op de site, dan zelf aan de slag met muziek, geluid en instrumenten. Fos is 4 jaar.

Werktitels om over na te denken: *Ontleed*, *Sporen*, *Uit elkaar*, *Wat hoor ik?*. De naam en het domein kies ik zelf.

## Harde regels (overgenomen van Voggels)

- **Eerlijk over wat de site niet weet.** Wat geschat is, staat als schatting op de site. Een spoor dat uit een opname is berekend, is geen echte multitrack. Credits uit een database kunnen onvolledig zijn. Er komt een pagina "Hoe dit werkt / wat de site niet kan".
- **Geen cookies en geen tracking.** Wat je zelf bijhoudt (onderzoekjes, favorieten) blijft in de browser van je eigen apparaat.
- **Auteursrecht serieus nemen.** Geen volledige nummers op onze server. Zie "Geluid" hieronder.
- **Browser-first.** Ik werk zonder lokale ontwikkelomgeving. Statische site, live via Netlify, data ververst door GitHub Actions.
- **Communicatie en sitetekst in het Nederlands**, direct en zonder marketingtoon.
- **Geen AI-beelden.** Echte foto's en tekeningen uit open collecties.

## Opbouw en uiterlijk: zoals Voggels

Overnemen uit Voggels (code staat in `sterrenstofai/vogels`):

- **Eén scherm per nummer**: een groot podium in het midden met tabjes (bij Voggels: Plaat / 3D / Zang / Roep), titel en weetjes linksonder, een strook met verwante items onderaan en een klein kaartje rechtsonder.
  - Hier bijvoorbeeld: tabjes **Sporen / Instrumenten / Samples / Geluidsbeeld** (spectrogram).
  - In de strook: andere nummers van hetzelfde album of dezelfde artiest, of nummers die hetzelfde sample gebruiken.
  - In plaats van het kaartje: een kleine "stamboom" van samples (wat zit erin, waar komt het vandaan).
- **Index** van alle nummers en van alle instrumenten, met filterchips en zoeken.
- **Kop**: logo, zoekveld, een mint knop "Ontdek een nummer", en icoontjes voor onderzoekjes, kinderen en index. Op iPad (1000–1700 px) alleen icoontjes, anders raakt het zoekveld klem.
- **Voet**: vier kolommen (Data, Beeld, Geluid, Privacy) en groot het woordmerk.
- **Typografie en kleur** (naar het voorbeeld van aspensearch.com):
  - Letters: Geist en Geist Mono (OFL), zelf gehost.
  - Koppen dun en strak gespatieerd, geen cursief.
  - Kleine labels in Geist Mono, in hoofdletters, met een zwart blokje ervoor.
  - Kleuren: wit `#FFFFFF`, inkt `#232323`, grijs `#F4F4F4`, `#D9D9D9` en `#6E6E6E`, mint `#A1FFCB`.
  - Kleur zit in vlakken, niet in letters. Een accentwoord in een kop krijgt een mint vlak.
  - Altijd een licht thema, ook als het toestel op donker staat.
- **Kinderversie** (`/kinderen`): een grote foto van een instrument, een grote mint knop voor het geluid, en een stem die de naam zegt als je op de foto tikt (Web Speech, Nederlandse stem van het toestel). De eerste keer wijst een kloppend handje aan waar je kunt tikken. Vegen gaat naar het volgende instrument.
- **Onderzoekjes met Fos**:
  - per opdracht "Wat heb je nodig", "Zo doe je het" en een mint blok "En dan naar buiten" (of: "En dan zelf spelen")
  - een voortgangsbalk met zes vakjes
  - een certificaat met naam als A4-PNG, in de browser getekend
  - "Opnieuw beginnen" met een bevestiging; de naam blijft bewaard
- **"Mijn …"**: een plusje om bij te houden wat je zelf hebt ontdekt, met een eigen pagina. Alleen op het apparaat.

## Mogelijke bronnen (eerst controleren in fase 1)

**Credits en instrumenten**
- **MusicBrainz**: open data (de kern is CC0). Kent relaties als "instrument", "vocal", "producer", "engineer" en "samples material". Waarschijnlijk de beste open basis.
- **Wikidata**: aanvulling op instrumenten, artiesten en apparaten, met links naar Wikipedia.
- **Discogs**: veel credits per release. Er is een API en een maandelijkse datadump. Licentie en gebruiksvoorwaarden nakijken.

**Samples**
- **MusicBrainz**: de relatie "samples material". Dekking nog onbekend, dus in fase 1 meten.
- **WhoSampled** is het meest volledig, maar heeft geen open API en de voorwaarden verbieden scrapen. Alleen ernaar linken, niet ophalen.

**Geluid** (het moeilijkste deel, vanwege auteursrecht)
- **Previews van 30 seconden** via de iTunes Search API of de Deezer API. Voorwaarden voor gebruik op een eigen site controleren.
- **Zelf een bestand openen**: de analyse draait dan in de browser en er wordt niets geüpload. Zo kan het spectrogram (zoals bij Voggels), tempo en toonsoort op je eigen muziek.
- **Sporen scheiden** (stem, drums, bas, overig) kan met Demucs (open source). Dat is zwaar.
  - Kan het in de browser (ONNX/WASM)?
  - Of alleen vooraf, voor een kleine vaste set nummers?
  - Een gescheiden spoor is altijd een schatting, en dat zeggen we erbij.
- **Spotify** heeft audio-features en audio-analysis eind 2024 afgesloten voor nieuwe apps. Niet op bouwen, wel nog nakijken.
- **Analyse in de browser**: Meyda (MIT) of Essentia.js. Essentia.js is AGPL, dus de licentie goed bekijken.

**Instrumenten: beeld en losse klanken**
- Beeld:
  - **Metropolitan Museum Open Access**: foto's van muziekinstrumenten, CC0
  - **Wikimedia Commons**: foto's en oude gravures. Let op: Wikimedia blokkeert snel bij veel downloads, dus ophalen via een GitHub Action, net als bij Voggels.
- Losse klanken:
  - **University of Iowa Musical Instrument Samples**: vrij te gebruiken
  - **Freesound** (alleen CC0- en CC BY-klanken)
  - **Philharmonia sound samples**: licentie nakijken

## Lessen uit Voggels

- **Geluid op iOS:** afspelen moet direct in de tik van de gebruiker gebeuren, zonder `await` ervoor. Gebruik mp3 en een gewoon `<audio>`-element. Reken het spectrogram los uit (fetch, dan `decodeAudioData`, dan een FFT). Houd een reservebestand achter de hand als een opname niet laadt.
- **Quiz-modus:** speel geheim af. Dan tonen de spelerbalk en het vergrendelscherm geen naam en geen afbeelding.
- **Grote externe bronnen:** download via GitHub Actions (andere IP-adressen, geen blokkade) en zet het resultaat in de repo. Doe dat op een aparte tak als het alleen tussenresultaten zijn.
- **Data verversen:** een GitHub Action per dag of per maand, die commit naar `main`. Netlify zet het dan vanzelf live.
- **Testen:** Playwright met schermafbeeldingen op 360, 390, 768, 1024, 1366 en 1920 px breed. Kijk ook naar horizontaal scrollen en naar knoppen die over elkaar vallen.
- **Code:** statische HTML, CSS en losse ES-modules. Strikte CSP. `[hidden] { display: none !important }`. View transitions tussen pagina's.
- **Nederlandse tekst:** let op lidwoorden ("de" of "het") als je namen in zinnen zet. Bij Voggels was dat een aparte regel.

## Ideeën voor Onderzoekjes met Fos (4 jaar)

1. **Welk instrument hoor je?** Een geluid, drie foto's, één is goed.
2. **Tik de maat mee.** Op de tafel meetikken met een nummer. De site laat zien of je gelijk loopt.
3. **Potten en pannen.** Thuis een drumstel bouwen van keukenspullen en een beroemde drumpartij naspelen.
4. **Raad het geheime spoor.** Alleen de bas of alleen de drums horen: wat is het voor nummer?
5. **Hoog en laag.** Geluiden sorteren van laag naar hoog, en zingen als een tuba en als een fluit.
6. **Oud geluid in een nieuw liedje.** Een sample horen, en dan het nummer waar het uit komt.

## Fase 1: eerst een datacheck, dan stoppen

Net als bij Voggels: eerst kijken wat er echt aan data is, voordat er iets gebouwd wordt.

- Een testset van ongeveer 10 nummers in verschillende genres, bijvoorbeeld:
  - Phil Collins, *In the Air Tonight*
  - Michael Jackson, *Billie Jean*
  - Daft Punk, *One More Time*
  - een klassieker uit de hiphop met bekende samples
  - een recent rapnummer
  - een Nederlandstalig nummer
  - een klassiek stuk
- Per nummer meten:
  - Hoeveel credits staan er per instrument in MusicBrainz en in Discogs?
  - Zijn er samples bekend in MusicBrainz?
  - Is er een preview van 30 seconden?
  - Is er een foto van de instrumenten met een vrije licentie?
- Een korte proef met spoorscheiding op één preview: hoe klinkt het, en hoe lang duurt het?
- Rapport in het Nederlands. **Daarna stoppen en wachten op mijn akkoord.**

## Open vragen voor mij

- De naam en het domein.
- Mag je ook je eigen muziekbestand openen, met de analyse alleen in de browser?
- Beginnen met een vaste, met de hand gekozen set nummers (beter van kwaliteit), of alles zoekbaar via MusicBrainz (breder, maar wisselend van kwaliteit)?
- Komt de kinderversie hier ook in, met instrumenten in plaats van vogels?
