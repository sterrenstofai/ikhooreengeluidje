# ikhooreengeluidje.nl: werkafspraken

De volledige achtergrond staat in `docs/briefing.md`. Dit zijn de regels die altijd gelden.

- **Eerlijk over wat de site niet weet.** Een schatting staat als schatting op de site. Een gescheiden spoor is geen echte multitrack. Credits uit een database kunnen onvolledig zijn.
- **Geen cookies en geen tracking.** Wat iemand zelf bijhoudt, blijft in de browser van dat apparaat.
- **Auteursrecht:** geen audio van nummers op onze server of in deze repo. Previews alleen streamen (iTunes: met winkelbadge en "provided courtesy of iTunes").
- **Browser-first:** statische site (HTML, CSS, losse ES-modules), live via Netlify, data ververst door GitHub Actions. Strikte CSP. `[hidden] { display: none !important }`.
- **Nederlands**, direct en zonder marketingtoon, in communicatie en sitetekst. Let op "de" of "het" als je namen in zinnen zet.
- **Geen AI-beelden.** Echte foto's en tekeningen uit open collecties (Commons, Met).
- **Externe bronnen** die blokkeren (Wikimedia Commons) ophalen via een GitHub Action.
- **Testen:** Playwright met schermafbeeldingen op 360, 390, 768, 1024, 1366 en 1920 px. Let op horizontaal scrollen en knoppen die over elkaar vallen.
- **Geluid op iOS:** afspelen direct in de tik, zonder `await` ervoor. Gewoon `<audio>`-element.
