// Schermafbeeldingen op zes breedtes, met controle op horizontaal scrollen en fouten in de console.
// Gebruik: node tests/schermen.js [basis-url] [uitmap]
const { chromium } = require("playwright");
const BASIS = process.argv[2] || "http://localhost:8765";
const UIT = process.argv[3] || "schermen";
const BREEDTES = [360, 390, 768, 1024, 1366, 1920];
const PAGINAS = [
  ["home", "/"],
  ["nummer", "/nummer/in-the-air-tonight"],
  ["nummer-samples", "/nummer/juicy", "Samples"],
  ["nummer-geluid", "/nummer/billie-jean", "Geluidsbeeld"],
  ["instrumenten", "/instrumenten"],
  ["hoe", "/hoe-dit-werkt"],
  ["kinderen", "/kinderen"],
];
(async () => {
  require("fs").mkdirSync(UIT, { recursive: true });
  const browser = await chromium.launch({ proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: "localhost,127.0.0.1" } : undefined });
  let problemen = 0;
  for (const b of BREEDTES) {
    const page = await browser.newPage({ viewport: { width: b, height: b < 800 ? 780 : 900 }, ignoreHTTPSErrors: true });
    const fouten = [];
    page.on("pageerror", (e) => fouten.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
    for (const [naam, pad, tab] of PAGINAS) {
      await page.goto(BASIS + pad, { waitUntil: "networkidle" });
      if (tab) { await page.getByRole("tab", { name: tab }).click(); await page.waitForTimeout(tab === "Geluidsbeeld" ? 4000 : 300); }
      const breed = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      if (breed > 0) { problemen++; console.log(`  ${b}px ${naam}: ${breed}px horizontaal scrollen`); }
      await page.screenshot({ path: `${UIT}/${naam}-${b}.png`, fullPage: false });
    }
    for (const f of new Set(fouten)) { problemen++; console.log(`  ${b}px fout: ${f.slice(0, 200)}`); }
    await page.close();
  }
  await browser.close();
  console.log(problemen ? `${problemen} problemen` : "geen problemen");
})();
