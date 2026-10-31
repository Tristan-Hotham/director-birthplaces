// QA: open index.html at desktop (1280) and phone (390) widths, record console errors, take screenshots to qa/.
// Run from the repo root with a static server on :8817 (python3 -m http.server 8817).
const { chromium } = require("playwright");
const path = require("path");
const OUT = path.join(__dirname, "..", "qa");
// Leaflet is served from a local npm copy (the CDN is not reachable from the build machine); tiles and fonts are skipped.
const LEAF = process.env.LEAFLET_DIST || "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  for (const [name, w, h] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: name === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    const errs = [];
    p.on("console", m => { if (m.type() === "error" && !/arcgisonline|net::ERR|Failed to load resource/.test(m.text())) errs.push(m.text()); });
    p.on("pageerror", e => errs.push("pageerror " + e.message));
    await p.goto("http://localhost:" + (process.env.QA_PORT || 8817) + "/index.html", { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
    await p.waitForTimeout(2500);
    await p.screenshot({ path: `${OUT}/${name}_top.png` });
    const at = async (sel, file) => { const e = await p.$(sel); if (e) { await e.scrollIntoViewIfNeeded(); await p.waitForTimeout(400); await e.screenshot({ path: `${OUT}/${name}_${file}.png` }); } };
    await at("#atlas", "map_all");
    // decade and women
    await p.evaluate(() => { setDec(1930); }); await p.waitForTimeout(600); await at("#atlas", "map_1930");
    await p.click('#gRow .btn[data-g="w"]'); await p.evaluate(() => setDec(2010)); await p.waitForTimeout(600); await at("#atlas", "map_women2010");
    await p.click('#gRow .btn[data-g="all"]'); await p.evaluate(() => setDec(null));
    // search a director
    await p.fill("#q", "Agnès Varda"); await p.waitForTimeout(500); await at(".searchbox", "search");
    await p.keyboard.press("Enter"); await p.waitForTimeout(1500); await at("#atlas", "director");
    // click a hexagon at Paris at world zoom
    await p.evaluate(() => { clearSel(); map.setView([48.8, 2.3], 4); }); await p.waitForTimeout(1200);
    const box = await p.$("#map"); const bb = await box.boundingBox();
    await p.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(800); await at("#atlas", "hex");
    // flows
    await p.evaluate(() => { LY.flows = true; applyLayers(); legend(); map.setView([38, -20], 2); }); await p.waitForTimeout(1200); await at("#atlas", "flows");
    await p.evaluate(() => { LY.flows = false; applyLayers(); legend(); });
    // layers panel
    await p.click(".lyrBtn"); await p.waitForTimeout(300); await at("#map", "layers"); await p.click(".lyrBtn");
    for (const id of ["cityChart", "ctyChart", "stackChart", "riseChart", "flowChart", "usChart", "womenChart", "wcChart", "covChart", "proTable"]) await at("#" + id, id);
    await p.click("#theme"); await p.waitForTimeout(800); await at("#atlas", "dark");
    await p.screenshot({ path: `${OUT}/${name}_full.png`, fullPage: true });
    const over = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    console.log(name, "errors:", JSON.stringify(errs), "horizontal overflow:", over);
    await p.close();
  }
  await b.close();
})();
