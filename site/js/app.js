import * as G from "./geluid.js";
import { F_LAAG, F_HOOG } from "./geluid.js";

const app = document.getElementById("app");
const TITEL = "ikhooreengeluidje";
let paginaDoeken = [];
let kinderModule = null;

/* ---------- Data ---------- */

let _data = null;
async function data() {
  if (_data) return _data;
  const [nummers, instrumenten, fotos, klanken] = await Promise.all(
    ["/data/nummers.json", "/data/instrumenten.json", "/data/fotos.json", "/data/klanken.json"].map((u) => fetch(u).then((r) => (r.ok ? r.json() : {})).catch(() => ({}))),
  );
  const perSlug = Object.fromEntries(nummers.map((n) => [n.slug, n]));
  const perInstrument = Object.fromEntries(instrumenten.map((i) => [i.key, i]));
  _data = { nummers, instrumenten, perSlug, perInstrument, fotos, klanken };
  return _data;
}

/* ---------- Hulpjes ---------- */

// Foto van een instrument of apparaat, met maker en licentie eronder (verplicht bij CC BY en CC BY-SA)
const APPARAAT_SLEUTEL = (naam) => {
  const n = naam.toLowerCase();
  if (n.includes("cr-78")) return "apparaat:roland-cr-78";
  if (n.includes("prophet")) return "apparaat:prophet-5";
  if (n.includes("linndrum")) return "apparaat:linndrum";
  if (n.includes("tr-808")) return "apparaat:roland-tr-808";
  if (n.includes("dmx")) return "apparaat:oberheim-dmx";
  if (n.includes("moog")) return "apparaat:moog";
  if (n.includes("clavinet")) return "apparaat:hohner-clavinet";
  return null;
};
function foto(D, sleutel, { onderschrift = true, klein = false } = {}) {
  const f = sleutel && D.fotos?.[sleutel];
  if (!f) return "";
  const img = `<img src="${f.pad}" alt="" loading="lazy" width="${f.breed}" height="${f.hoog}">`;
  if (!onderschrift) return `<span class="foto${klein ? " foto-klein" : ""}">${img}</span>`;
  return `<figure class="foto">${img}<figcaption>Foto: ${esc(f.maker.length > 60 ? f.maker.slice(0, 58).trim() + "…" : f.maker)}, <a href="${esc(f.pagina)}" rel="noopener">${esc(f.licentie)}</a>, via Wikimedia Commons</figcaption></figure>`;
}

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const norm = (s) => String(s ?? "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9 ]/g, "");
const bronLink = (url) => {
  if (!url) return "";
  const host = new URL(url).hostname.replace(/^www\.|^en\./, "");
  return `<a class="bron" href="${esc(url)}" rel="noopener">${esc(host)}</a>`;
};
const hoes = (n, klein = false) => n.preview
  ? `<img src="${esc(klein ? n.preview.hoes_klein : n.preview.hoes)}" alt="" loading="lazy" width="${klein ? 200 : 600}" height="${klein ? 200 : 600}" referrerpolicy="no-referrer">`
  : `<span class="hoes-leeg">${esc(n.titel.charAt(0))}</span>`;
const SPEEL_SVG = `<svg viewBox="0 0 44 44" aria-hidden="true"><circle class="ring-bg" cx="22" cy="22" r="20"/><circle class="ring" cx="22" cy="22" r="20"/><path class="ico-pauze" d="M17 15v14M27 15v14"/><path class="ico-speel" d="M18 14l12 8-12 8z"/></svg>`;
const etiket = (t) => `<p class="etiket">${esc(t)}</p>`;
const speelItem = (n) => n.preview && { id: n.slug, titel: n.titel, artiest: n.artiest, url: n.preview.url, hoes: n.preview.hoes };

// Een nummer heeft samples, apparaten of is Nederlandstalig: voor de filterchips
const NL_SLUGS = new Set(["de-bom", "een-beetje-verliefd", "avond", "radar-love"]);
const KENMERKEN = {
  samples: { naam: "Met samples", test: (n) => n.samples_erin.length > 0 },
  gesampled: { naam: "Gesampled", test: (n) => n.gesampled_door.some((d) => d.slug) },
  apparaten: { naam: "Drumcomputers en synths", test: (n) => n.apparaten.length > 0 || n.credits.some((c) => ["drumcomputer", "synthesizer", "sampler", "vocoder"].includes(c.key)) },
  nl: { naam: "Uit Nederland", test: (n) => NL_SLUGS.has(n.slug) },
  klassiek: { naam: "Klassiek", test: (n) => n.klassiek },
};

/* ---------- Router ---------- */

function naar(pad, vervang = false) {
  if (vervang) history.replaceState({}, "", pad); else history.pushState({}, "", pad);
  toon();
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-link]");
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey || a.target) return;
  e.preventDefault();
  naar(a.getAttribute("href"));
});
window.addEventListener("popstate", () => toon());

async function toon() {
  const pad = location.pathname.replace(/\/+$/, "") || "/";
  const D = await data();
  const doe = () => {
    for (const d of paginaDoeken) G.ontkoppelDoek(d);
    paginaDoeken = [];
    document.body.classList.toggle("onder-kop", !pad.startsWith("/nummer/"));
    document.body.classList.toggle("kindermodus", pad === "/kinderen");
    kinderModule?.verlaat();
    if (pad === "/") home(D);
    else if (pad.startsWith("/nummer/")) nummerPagina(D, decodeURIComponent(pad.slice(8)));
    else if (pad === "/nummers") index(D);
    else if (pad === "/instrumenten") instrumentenIndex(D);
    else if (pad.startsWith("/instrument/")) instrumentPagina(D, decodeURIComponent(pad.slice(12)));
    else if (pad === "/kinderen") {
      document.title = `Instrumenten voor kinderen · ${TITEL}`;
      import("./kinderen.js").then((K) => { kinderModule = K; K.kinderPagina(app, D.fotos, D.klanken); });
    }
    else if (pad === "/ontdek") {
      const kies = D.nummers.filter((n) => n.preview);
      return naar(`/nummer/${kies[Math.floor(Math.random() * kies.length)].slug}`, true);
    }
    else nietGevonden();
    window.scrollTo(0, 0);
    app.focus({ preventScroll: true });
    markeerNav(pad);
  };
  if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(doe);
  else doe();
}

function markeerNav(pad) {
  for (const a of document.querySelectorAll(".balk-nav a")) {
    const h = a.getAttribute("href");
    if (h === pad || (h !== "/" && pad.startsWith(h.replace(/s$/, "")))) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  }
}

function nietGevonden() {
  document.title = `Niet gevonden · ${TITEL}`;
  app.innerHTML = `<section class="kolom tekst"><h1>Dat nummer kennen we (nog) niet</h1><p>Misschien staat het er nog niet in. Kijk in de <a href="/nummers" data-link>lijst met nummers</a>.</p></section>`;
}

/* ---------- Kaartjes ---------- */

function kaart(n) {
  const labels = [n.nagekeken ? "nagekeken" : null, n.samples_erin.length ? "samples" : null].filter(Boolean);
  return `<article class="nummer">
    <a class="nummer-hoes" href="/nummer/${n.slug}" data-link aria-hidden="true" tabindex="-1">${hoes(n, true)}</a>
    <div class="nummer-tekst">
      <a class="nummer-titel" href="/nummer/${n.slug}" data-link>${esc(n.titel)}</a>
      <span class="nummer-artiest">${esc(n.artiest)} · ${n.jaar}</span>
      ${labels.length ? `<span class="labels">${labels.map((l) => `<span class="label">${l}</span>`).join("")}</span>` : ""}
    </div>
  </article>`;
}

/* ---------- Home en index ---------- */

function home(D) {
  document.title = `${TITEL} · Hoor hoe een nummer in elkaar zit`;
  const vb = D.perSlug["in-the-air-tonight"];
  app.innerHTML = `
  <section class="held breed">
    ${etiket("Nummers uit elkaar gehaald")}
    <h1>Hoor hoe een nummer <span class="accent">in elkaar</span> zit</h1>
    <p class="held-sub">Welke instrumenten en apparaten erin zitten, wie wat speelt en welk ouder nummer er stiekem in verstopt zit. Met een fragment van 30 seconden om naar te luisteren.</p>
    <div class="held-knoppen">
      <a class="knop-pil knop-accent" href="/ontdek" data-link>Ontdek een nummer</a>
      ${vb ? `<a class="knop-pil" href="/nummer/${vb.slug}" data-link>Begin met ${esc(vb.titel)}</a>` : ""}
    </div>
  </section>
  ${lijst(D, "Alle nummers", true)}`;
  koppelLijst(D);
}

function index(D) {
  document.title = `Alle nummers · ${TITEL}`;
  app.innerHTML = lijst(D, "Alle nummers", false);
  koppelLijst(D);
}

function lijst(D, kop, opHome) {
  return `<section class="blok breed" id="lijst">
    <div class="blok-kop">${opHome ? `<h2>${esc(kop)}</h2>` : `<h1 class="index-kop">${esc(kop)}</h1>`}<span class="mono zacht" data-teller></span></div>
    <div class="index-filters">
      <div class="index-rij"><label class="sr" for="filter">Zoek in de lijst</label><input class="veld" id="filter" type="search" placeholder="Zoek op titel of artiest" autocomplete="off"></div>
      <div class="chips" role="group" aria-label="Filter">${Object.entries(KENMERKEN).map(([k, v]) => `<button class="chip" type="button" data-kenmerk="${k}" aria-pressed="false">${esc(v.naam)}</button>`).join("")}</div>
    </div>
    <div class="raster nummers" data-raster></div>
    <p class="noot zacht">Deze lijst is met de hand gekozen. Bij nummers met het label <span class="label">nagekeken</span> zijn de weetjes en apparaten gecontroleerd, met een bron. Bij de rest komt alles uit MusicBrainz en Discogs. <a href="/hoe-dit-werkt">Hoe dit werkt</a></p>
  </section>`;
}

function koppelLijst(D) {
  const raster = app.querySelector("[data-raster]"), veld = app.querySelector("#filter"), teller = app.querySelector("[data-teller]");
  const aan = new Set();
  const teken = () => {
    const q = norm(veld.value);
    const lijst = D.nummers.filter((n) => (!q || norm(`${n.titel} ${n.artiest}`).includes(q)) && [...aan].every((k) => KENMERKEN[k].test(n)));
    raster.innerHTML = lijst.map(kaart).join("") || `<p class="zacht">Niets gevonden met deze filters.</p>`;
    teller.textContent = `${lijst.length} van ${D.nummers.length}`;
  };
  veld.addEventListener("input", teken);
  for (const b of app.querySelectorAll("[data-kenmerk]")) b.addEventListener("click", () => {
    const k = b.dataset.kenmerk;
    if (aan.has(k)) aan.delete(k); else aan.add(k);
    b.setAttribute("aria-pressed", aan.has(k));
    teken();
  });
  teken();
}

/* ---------- Nummerpagina ---------- */

const TABS = [["sporen", "Sporen"], ["instrumenten", "Instrumenten"], ["samples", "Samples"], ["geluidsbeeld", "Geluidsbeeld"]];

function nummerPagina(D, slug) {
  const n = D.perSlug[slug];
  if (!n) return nietGevonden();
  document.title = `${n.titel} van ${n.artiest} · ${TITEL}`;
  const verwant = verwanteNummers(D, n);
  const prod = n.productie || {};
  const weetjes = [
    ["Artiest", esc(n.artiest)],
    ["Jaar", n.jaar],
    n.album ? ["Album", `<span class="cursief">${esc(n.album)}</span>`] : null,
    prod.productie ? ["Productie", esc(prod.productie.join(", "))] : null,
    ["Status", n.nagekeken ? `<span class="label">nagekeken</span>` : `<span class="label label-zacht">niet nagekeken</span>`],
  ].filter(Boolean);
  const startTab = "instrumenten";
  app.innerHTML = `
  <section class="scherm" data-nummer="${n.slug}">
    <div class="podium">
      ${TABS.map(([k]) => `<div class="podium-paneel paneel-${k}" id="paneel-${k}" role="tabpanel" aria-labelledby="tab-${k}" ${k === startTab ? "" : "hidden"}>${paneel(D, n, k)}</div>`).join("")}
      <div class="weergave" role="tablist" aria-label="Weergave">${TABS.map(([k, t]) => `<button type="button" role="tab" id="tab-${k}" aria-controls="paneel-${k}" aria-selected="${k === startTab}" data-tab="${k}">${t}</button>`).join("")}</div>
    </div>
    <div class="scherm-titel">
      <div class="titel-rij">
        ${n.preview ? `<button class="knop-rond knop-groot" type="button" data-speel aria-label="Speel het fragment van ${esc(n.titel)}">${SPEEL_SVG}</button>` : ""}
        <h1>${esc(n.titel)}</h1>
      </div>
      <dl class="weetjes">${weetjes.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>
    </div>
    <div class="scherm-strook">
      <nav class="strook" aria-label="Verwante nummers">${verwant.map((v) => `<a class="strook-item" href="/nummer/${v.slug}" data-link title="${esc(v.titel)} · ${esc(v.artiest)}"><span class="strook-beeld">${hoes(v, true)}</span><span class="strook-naam">${esc(v.titel)}</span></a>`).join("")}</nav>
      <div class="omgeving stamboom" aria-label="Stamboom van samples">${stamboom(D, n)}</div>
    </div>
  </section>
  ${n.preview ? previewVoet(n) : ""}`;

  for (const b of app.querySelectorAll("[data-tab]")) b.addEventListener("click", () => kiesTab(n, b.dataset.tab));
  for (const b of app.querySelectorAll("[data-speel]")) b.addEventListener("click", () => G.speel(speelItem(n)));
  kiesTab(n, startTab);
}

function kiesTab(n, tab) {
  for (const b of app.querySelectorAll("[data-tab]")) b.setAttribute("aria-selected", b.dataset.tab === tab);
  for (const p of app.querySelectorAll(".podium-paneel")) p.hidden = p.id !== `paneel-${tab}`;
  for (const d of paginaDoeken) G.ontkoppelDoek(d);
  paginaDoeken = [];
  const doek = app.querySelector(`#paneel-${tab} canvas[data-spectro]`);
  if (doek) {
    G.koppelDoek(doek, { modus: "heel", id: n.slug });
    paginaDoeken.push(doek);
    if (n.preview && !G.spectrum(n.slug)) G.maakSpectrum(n.slug, n.preview.url);
  }
}

function paneel(D, n, k) {
  if (k === "instrumenten") return paneelInstrumenten(D, n);
  if (k === "samples") return paneelSamples(D, n);
  if (k === "geluidsbeeld") return paneelGeluidsbeeld(n);
  return paneelSporen(n);
}

function paneelInstrumenten(D, n) {
  const app_ = n.apparaten.map((a) => `<li class="apparaat">${foto(D, APPARAAT_SLEUTEL(a.naam), { onderschrift: false, klein: true })}<span class="apparaat-soort">${esc(a.soort)}</span><strong>${esc(a.naam)}</strong><span>${esc(a.wat)}</span>${bronLink(a.bron)}</li>`).join("");
  const rijen = n.credits.map((c) => {
    const i = D.perInstrument[c.key];
    const wie = c.wie.length
      ? c.wie.map((w) => `<span class="wie">${esc(w.naam)}<small>${w.bron.map((b) => (b === "MusicBrainz" ? "MB" : "D")).join(" ")}</small></span>`).join("")
      : `<span class="zacht">volgens de partituur</span>`;
    return `<li><a class="instr-naam" href="/instrument/${c.key}" data-link>${esc(i ? i.nl : c.nl)}</a><span class="instr-wie">${wie}</span></li>`;
  }).join("");
  const leeg = !n.credits.length && !n.apparaten.length;
  return `<div class="paneel-binnen">
    ${app_ ? `${etiket("Apparaten, met de hand nagekeken")}<ul class="apparaten">${app_}</ul>` : ""}
    ${rijen ? `${etiket("Wie speelt wat")}<ul class="credits">${rijen}</ul>
      <p class="noot zacht">MB = MusicBrainz, D = Discogs. Credits uit een database kunnen onvolledig zijn, en dezelfde muzikant staat soms onder twee namen.</p>` : ""}
    ${leeg ? `<div class="leeg-blok"><p class="leeg-kop">Nog niemand bekend</p><p>MusicBrainz en Discogs weten nog niet wie wat speelt op dit nummer. Bij nieuwe nummers is dat vaak zo: die worden thuis of in een kleine studio gemaakt en de credits komen later, of nooit.</p></div>` : ""}
  </div>`;
}

function sampleRij(D, s, richting) {
  const doel = s.slug && D.perSlug[s.slug];
  const titel = doel ? doel.titel : s.titel, artiest = doel ? doel.artiest : s.artiest, jaar = doel ? doel.jaar : s.jaar;
  const naam = `<strong>${esc(titel)}</strong><span>${esc(artiest || "")}${jaar ? ` · ${jaar}` : ""}</span>`;
  const soort = s.type === "naspelen" ? "nagespeeld" : richting === "erin" ? "sample" : "";
  return `<li class="sample ${doel ? "in-lijst" : ""}">
    ${doel ? `<a class="sample-naam" href="/nummer/${doel.slug}" data-link>${naam}</a>` : `<span class="sample-naam">${naam}</span>`}
    ${soort ? `<span class="label">${soort}</span>` : ""}
    ${s.wat ? `<p>${esc(s.wat)} ${bronLink(s.bron)}</p>` : ""}
  </li>`;
}

function paneelSamples(D, n) {
  const ws = `https://www.whosampled.com/search/?q=${encodeURIComponent(`${n.artiest} ${n.titel}`)}`;
  const door = n.gesampled_door;
  return `<div class="paneel-binnen">
    ${etiket("Wat zit erin")}
    ${n.samples_erin.length ? `<ul class="samples">${n.samples_erin.map((s) => sampleRij(D, s, "erin")).join("")}</ul>`
      : `<p class="leeg-zin">${n.klassiek ? "Een klassiek stuk heeft geen samples." : "Er is geen sample bekend in MusicBrainz."}</p>`}
    ${door.length ? `${etiket("Waar zit het in")}<ul class="samples">${door.map((s) => sampleRij(D, s, "door")).join("")}</ul>
      ${n.gesampled_door_totaal > 10 ? `<p class="noot zacht">De tien bekendste van ${n.gesampled_door_totaal} in MusicBrainz.</p>` : ""}` : ""}
    <p class="noot zacht">"Nagespeeld" betekent: niet geknipt uit de opname, maar opnieuw ingespeeld. De meest complete lijst staat op <a href="${esc(ws)}" rel="noopener">WhoSampled</a>.</p>
  </div>`;
}

function paneelGeluidsbeeld(n) {
  if (!n.preview) return `<div class="paneel-binnen"><p class="leeg-zin">Voor dit nummer is geen fragment gevonden.</p></div>`;
  return `<div class="geluidsbeeld">
    <div class="spectro-vlak spectro-groot">
      <canvas data-spectro aria-label="Spectrogram van het fragment"></canvas>
      <div class="spectro-as" aria-hidden="true">${[[8000, "8 kHz"], [2000, "2 kHz"], [500, "500 Hz"], [100, "100 Hz"]].map(([hz, t]) => `<span style="top:${(100 - (Math.log(hz / F_LAAG) / Math.log(F_HOOG / F_LAAG)) * 100).toFixed(1)}%">${t}</span>`).join("")}</div>
    </div>
    <p class="noot zacht">Het geluidsbeeld van het fragment van 30 seconden: van links naar rechts de tijd, van onder naar boven laag naar hoog. Hoe donkerder, hoe harder. Onderin zitten de bas en de basdrum, in het midden de stem, bovenin de bekkens en hi-hats. Tik erop om naar die plek te springen.</p>
  </div>`;
}

function paneelSporen(n) {
  return `<div class="paneel-binnen">
    ${etiket("Sporen")}
    <p class="sporen-kop">Hier hoor je straks elk instrument apart.</p>
    <p>Dat kan alleen als schatting: een computer probeert de zang, de drums en de bas uit de opname los te halen. Dat werkt goed, maar nooit perfect. Er lekt altijd wat van de rest door.</p>
    <p>Omdat we fragmenten niet mogen bewaren of bewerken, gaat dat straks op een muziekbestand dat je zelf opent, in je eigen browser. Er wordt dan niets geüpload.</p>
    <p class="zacht">Dit onderdeel wordt nu gebouwd.</p>
  </div>`;
}

function previewVoet(n) {
  return `<section class="breed preview-voet">
    <p>Fragment van 30 seconden: ${esc(n.preview.van)}. Provided courtesy of iTunes.</p>
    <a class="knop-pil" href="${esc(n.preview.winkel)}" rel="noopener">Luister het hele nummer in Apple Music</a>
  </section>`;
}

function verwanteNummers(D, n) {
  const uit = new Map();
  const voeg = (s) => { const v = s && D.perSlug[s]; if (v && v.slug !== n.slug) uit.set(v.slug, v); };
  n.samples_erin.forEach((s) => voeg(s.slug));
  n.gesampled_door.forEach((s) => voeg(s.slug));
  D.nummers.filter((x) => x.artiest === n.artiest).forEach((x) => voeg(x.slug));
  // daarna nummers met dezelfde apparaten of instrumenten
  const mijn = new Set(n.credits.map((c) => c.key));
  D.nummers.map((x) => [x, x.credits.filter((c) => mijn.has(c.key) && !["zang", "achtergrondzang"].includes(c.key)).length])
    .sort((a, b) => b[1] - a[1]).slice(0, 14).forEach(([x]) => voeg(x.slug));
  return [...uit.values()].slice(0, 14);
}

// Een kleine stamboom: boven wat erin zit, in het midden dit nummer, onder waar het in zit.
function stamboom(D, n) {
  const boven = n.samples_erin.slice(0, 3), onder = n.gesampled_door.slice(0, 3);
  if (!boven.length && !onder.length) {
    return `<p class="omgeving-label">Stamboom</p><p class="stamboom-leeg">Geen samples bekend</p>`;
  }
  const naam = (s) => { const d = s.slug && D.perSlug[s.slug]; return d ? d.titel : s.titel; };
  const knoop = (s, y, i, aantal) => {
    const x = ((i + 1) / (aantal + 1)) * 100;
    const max = aantal > 2 ? 13 : 18;
    const t = esc(naam(s).length > max ? naam(s).slice(0, max - 1).trim() + "…" : naam(s));
    const dy = (y < 50 ? -8 : 13) + (aantal > 2 && i % 2 ? (y < 50 ? -8 : 8) : 0); // om en om hoger en lager
    const inh = `<circle cx="${x}" cy="${y}" r="3.5"/><text x="${x}" y="${y + dy}">${t}</text>`;
    return { x, svg: s.slug ? `<a href="/nummer/${s.slug}" data-link>${inh}</a>` : inh };
  };
  const b = boven.map((s, i) => knoop(s, 30, i, boven.length)), o = onder.map((s, i) => knoop(s, 72, i, onder.length));
  return `<p class="omgeving-label">Stamboom</p>
  <svg viewBox="0 0 100 100" aria-hidden="true" class="stamboom-svg">
    ${b.map((k) => `<line x1="${k.x}" y1="30" x2="50" y2="51"/>`).join("")}${o.map((k) => `<line x1="50" y1="51" x2="${k.x}" y2="72"/>`).join("")}
    <rect x="38" y="45" width="24" height="12" rx="6" class="stamboom-hier"/>
    ${b.map((k) => k.svg).join("")}${o.map((k) => k.svg).join("")}
  </svg>`;
}

/* ---------- Instrumenten ---------- */

const GROEPEN = { stem: "Stem", slagwerk: "Slagwerk", snaren: "Snaren", toetsen: "Toetsen", blazers: "Blazers", elektronisch: "Elektronisch" };

function instrumentenIndex(D) {
  document.title = `Instrumenten · ${TITEL}`;
  app.innerHTML = `<section class="blok breed">
    <div class="blok-kop"><h1 class="index-kop">Instrumenten</h1><span class="mono zacht">${D.instrumenten.length} in deze nummers</span></div>
    ${Object.entries(GROEPEN).map(([g, naam]) => {
      const lijst = D.instrumenten.filter((i) => i.groep === g);
      return lijst.length ? `<h2 class="tussenkop">${naam}</h2><ul class="instr-lijst">${lijst.map((i) => `<li><a href="/instrument/${i.key}" data-link>${foto(D, i.key, { onderschrift: false, klein: true })}<strong>${esc(i.nl)}</strong><span class="mono zacht">${i.nummers.length} ${i.nummers.length === 1 ? "nummer" : "nummers"}</span></a></li>`).join("")}</ul>` : "";
    }).join("")}
    <p class="noot zacht">Foto's uit Wikimedia Commons, onder een vrije licentie. De maker staat bij de foto op de pagina van elk instrument.</p>
  </section>`;
}

function instrumentPagina(D, key) {
  const i = D.perInstrument[key];
  if (!i) return nietGevonden();
  document.title = `${i.nl} · ${TITEL}`;
  const nummers = i.nummers.map((s) => D.perSlug[s]).filter(Boolean);
  const hoofd = i.nl.charAt(0).toUpperCase() + i.nl.slice(1);
  app.innerHTML = `<section class="blok breed">
    <a class="terug" href="/instrumenten" data-link>← Alle instrumenten</a>
    ${etiket(GROEPEN[i.groep])}
    <h1 class="index-kop">${esc(hoofd)}</h1>
    ${foto(D, key)}
    <p class="held-sub">In ${nummers.length === 1 ? "dit nummer" : `deze ${nummers.length} nummers`} hoor je ${esc(i.lidwoord)} ${esc(i.nl)}.</p>
    <div class="raster nummers">${nummers.map(kaart).join("")}</div>
  </section>`;
}

/* ---------- Kop: zoeken ---------- */

function koppelZoeken() {
  const veld = document.getElementById("zoek"), lijst = document.getElementById("zoek-lijst"), melding = document.querySelector(".zoek-melding");
  let treffers = [], actief = -1;
  const sluit = () => { lijst.hidden = true; veld.setAttribute("aria-expanded", "false"); actief = -1; };
  const kies = (n) => { veld.value = ""; sluit(); melding.textContent = ""; naar(`/nummer/${n.slug}`); };
  veld.addEventListener("input", async () => {
    const D = await data();
    const q = norm(veld.value.trim());
    melding.textContent = "";
    if (!q) return sluit();
    treffers = D.nummers.filter((n) => norm(`${n.titel} ${n.artiest}`).includes(q)).slice(0, 8);
    lijst.innerHTML = treffers.map((n, i) => `<li role="option" id="z-${i}" data-i="${i}">${esc(n.titel)} <span class="zacht">${esc(n.artiest)}</span></li>`).join("");
    lijst.hidden = !treffers.length;
    veld.setAttribute("aria-expanded", String(!!treffers.length));
    if (!treffers.length) melding.textContent = "Dat nummer staat er nog niet in. Zoeken in alle nummers komt in een volgende stap.";
  });
  veld.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      actief = Math.max(0, Math.min(treffers.length - 1, actief + (e.key === "ArrowDown" ? 1 : -1)));
      for (const li of lijst.children) li.setAttribute("aria-selected", li.dataset.i == actief);
      veld.setAttribute("aria-activedescendant", `z-${actief}`);
    } else if (e.key === "Enter" && treffers.length) kies(treffers[Math.max(0, actief)]);
    else if (e.key === "Escape") sluit();
  });
  lijst.addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) kies(treffers[+li.dataset.i]); });
  document.addEventListener("click", (e) => { if (!e.target.closest(".zoek")) sluit(); });
  document.querySelector(".zoek-knop").addEventListener("click", () => { if (treffers.length) kies(treffers[0]); else veld.focus(); });
}

/* ---------- Speler onderaan ---------- */

function koppelSpeler() {
  const speler = document.getElementById("speler");
  const knop = speler.querySelector(".speler-knop"), naam = speler.querySelector(".speler-naam"), beeld = speler.querySelector(".speler-hoes");
  const doek = speler.querySelector(".speler-spectro");
  let vorige = null;
  knop.addEventListener("click", () => { const h = G.huidigeId(); if (h && _data?.perSlug[h]) G.speel(speelItem(_data.perSlug[h])); });
  speler.querySelector(".speler-sluit").addEventListener("click", () => G.stop());
  G.opVerandering(({ huidig, speelt, deel, fout, laadt }) => {
    speler.hidden = !huidig;
    if (!huidig) { vorige = null; return; }
    if (vorige !== huidig.id) {
      vorige = huidig.id;
      naam.textContent = huidig.geheim ? "Wat hoor ik?" : `${huidig.titel} · ${huidig.artiest}`;
      naam.href = huidig.geheim || huidig.eigen ? "#" : `/nummer/${huidig.id}`;
      beeld.src = huidig.geheim || !huidig.hoes ? "data:," : huidig.hoes;
      requestAnimationFrame(() => G.koppelDoek(doek));
    }
    speler.classList.toggle("speler-fout", !!fout);
    if (fout) naam.textContent = fout;
    knop.classList.toggle("speelt", speelt || laadt);
    knop.setAttribute("aria-label", speelt ? "Pauzeer" : "Speel");
    knop.querySelector(".ring").style.strokeDashoffset = 125.7 * (1 - deel);
    for (const b of app.querySelectorAll("[data-speel]")) {
      const dit = b.closest("[data-nummer]")?.dataset.nummer === huidig.id;
      b.classList.toggle("speelt", dit && (speelt || laadt));
      b.querySelector(".ring").style.strokeDashoffset = dit ? 125.7 * (1 - deel) : 125.7;
    }
  });
}

// Tik op het geluidsbeeld: spring naar die plek (en start als het nog niet speelt).
app.addEventListener("click", (e) => {
  const doek = e.target.closest("canvas[data-spectro]");
  if (!doek) return;
  const slug = doek.closest("[data-nummer]")?.dataset.nummer;
  const n = _data?.perSlug[slug];
  const s = G.spectrum(slug);
  if (!n || !s || s.status !== "klaar") return;
  const r = doek.getBoundingClientRect();
  if (!G.isHuidig(slug)) G.speel(speelItem(n));
  G.spring(((e.clientX - r.left) / r.width) * s.duur);
});

koppelZoeken();
koppelSpeler();
toon();
