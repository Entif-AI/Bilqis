const fs = require("fs"); const http = require("http");
const path = require("path"); const crypto = require("crypto");
const repo = path.resolve(__dirname, "../../../.."); const renderer = path.join(repo, "apps/mission-control/renderer");
const out = path.resolve(process.env.BILQIS_CLOSEOUT_OUT || "output/playwright/gui1143");
const playwright = require(process.env.BILQIS_PLAYWRIGHT_MODULE ||
  "/Users/emilie/Code/mission-control/node_modules/playwright");
const axePath = process.env.BILQIS_AXE_MODULE ||
  "/Users/emilie/Code/mission-control/node_modules/axe-core/axe.min.js";
const chrome = process.env.BILQIS_CHROME_PATH ||
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const {
  accessibilityTreeProof,
  expansionProof,
  shellUsabilityProof,
} = require("./shell-usability-journey.cjs");
const operator = JSON.parse(fs.readFileSync(path.join(repo,
  "apps/mission-control/fixtures/operator-view-v1.json"), "utf8"));
const views = [
  "mission-control", "school", "capability", "learning", "atlas", "model", "memory",
  "teacher", "salience", "corrections", "lineage", "resources", "evidence", "operate",
];
const hookPrefixes = [
  "shell-", "nav-", "foundation-", "investigation-", "inspector-", "home-", "school-",
  "curriculum-", "capability-", "learning-", "atlas-", "model-", "memory-", "teacher-",
  "salience-", "corrections-", "lineage-", "resources-", "evidence-", "operate-",
];
const hookSelector = hookPrefixes.map(prefix => `[data-test-id^="${prefix}"]`).join(",");
const mime = { ".html": "text/html", ".mjs": "text/javascript", ".js": "text/javascript",
  ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml" };
const bridge = `window.bamfMissionControl={
connect:async()=>({state:"disconnected"}),
querySnapshot:async q=>{if(q&&q.schemaVersion)return ${JSON.stringify(operator)};
throw new Error("GUI1143_PREVIEW_SERVICE_UNAVAILABLE");}
};`;
function check(condition, message) { if (!condition) throw new Error(message); }
function sha(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}
function server() {
  return http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (url.pathname === "/preview-bridge.mjs") {
      res.writeHead(200, { "Content-Type": "text/javascript" }); res.end(bridge); return;
    }
    if (url.pathname === "/axe.min.js") {
      res.writeHead(200, { "Content-Type": "text/javascript" });
      res.end(fs.readFileSync(axePath)); return;
    }
    let file = path.join(repo, decodeURIComponent(url.pathname));
    if (url.pathname === "/" || url.pathname === "/apps/mission-control/renderer/") {
      file = path.join(renderer, "index.html");
    }
    if (!file.startsWith(repo) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404); res.end("not found"); return;
    }
    let body = fs.readFileSync(file);
    if (file.endsWith("index.html")) {
      body = Buffer.from(body.toString().replace(
        '<script type="module" src="./renderer.mjs">',
        '<script src="/preview-bridge.mjs"></script><script type="module" src="./renderer.mjs">',
      ));
    }
    res.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream" });
    res.end(body);
  });
}
async function reconnect(page) {
  await page.evaluate(() => { window.bamfMissionControl.connect = async () => ({ state: "healthy" }); });
  const reconnect = page.locator('[data-test-id="foundation-reconnect"]');
  if (await reconnect.count()) await reconnect.click();
  await page.locator('[data-test-id="shell-navigation"]').waitFor();
}
async function setDisplay(page, theme, density) {
  await page.evaluate(({ theme, density }) => {
    localStorage.setItem("bilqis.mc.theme", theme);
    localStorage.setItem("bilqis.mc.density", density);
  }, { theme, density });
  await page.reload({ waitUntil: "domcontentloaded" });
  await reconnect(page);
  check(await page.locator('[data-test-id="shell-main-content"]').evaluate((node, expected) =>
    node.ownerDocument.documentElement.dataset.theme === expected, theme), `theme ${theme} applied`);
  check(await page.locator('[data-test-id="shell-main-content"]').evaluate((node, expected) =>
    node.ownerDocument.documentElement.dataset.density === expected, density), `density ${density} applied`);
}
async function navigate(page, view) {
  const nav = page.locator(`[data-test-id="nav-destination-${view}"]`);
  await nav.waitFor();
  check(!await nav.isDisabled(), `${view} navigation is disabled`);
  await nav.click();
  await page.waitForTimeout(100);
  const title = await page.locator('[data-test-id="shell-destination-title"]').innerText();
  check(title.trim().length > 0, `${view} destination title is empty`);
}
async function audit(page, view, label, screenshot) {
  const metrics = await page.evaluate(({ hookSelector }) => {
    const nodes = [...document.querySelectorAll(hookSelector)];
    const ids = nodes.map(node => node.dataset.testId);
    const dupes = [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))];
    const clipped = nodes.filter(node => {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden") return false;
      return node.clientWidth > 0 && node.scrollWidth > node.clientWidth + 1 &&
        ["hidden", "clip"].includes(style.overflowX);
    }).map(node => node.dataset.testId);
    const offscreen = nodes.filter(node => {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden") return false;
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && (rect.right > innerWidth + 1 || rect.left < -1);
    }).map(node => node.dataset.testId);
    return {
      duplicateTestIds: dupes,
      clippedHookIds: clipped,
      offscreenHookIds: offscreen,
      documentOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      scrollWidth: document.documentElement.scrollWidth,
      viewport: innerWidth,
      contextControlDistinct: (() => {
        const trigger = document.querySelector('[data-test-id="shell-system-context-trigger"]');
        if (!trigger) return false;
        return getComputedStyle(trigger).backgroundColor !== getComputedStyle(document.body).backgroundColor;
      })(),
      contextControlCentered: (() => {
        const trigger = document.querySelector('[data-test-id="shell-system-context-trigger"]');
        return Boolean(trigger && getComputedStyle(trigger).alignItems === "center");
      })(),
      navControlDistinct: (() => {
        const button = document.querySelector('[data-test-id^="nav-destination-"]:not(:disabled)');
        const rail = document.querySelector('[data-test-id="shell-rail"]');
        if (!button || !rail) return false;
        return getComputedStyle(button).backgroundColor !== getComputedStyle(rail).backgroundColor;
      })(),
    };
  }, { hookSelector });
  const axe = await page.evaluate(async () => axe.run(document, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
  }));
  const violations = axe.violations.map(item => ({
    id: item.id, impact: item.impact, nodes: item.nodes.map(node => node.target),
  }));
  check(metrics.duplicateTestIds.length === 0, `${view} duplicate test ids: ${metrics.duplicateTestIds}`);
  check(!metrics.documentOverflow,
    `${view} document overflow at ${metrics.viewport}px; offscreen=${metrics.offscreenHookIds.join(",")}`);
  check(metrics.contextControlDistinct, `${view} context trigger merges into canvas surface`);
  check(metrics.contextControlCentered, `${view} context trigger is not vertically centered`);
  check(metrics.navControlDistinct, `${view} navigation control merges into rail surface`);
  check(violations.length === 0, `${view} WCAG violations: ${violations.map(v => v.id)}`);
  let file = null;
  if (screenshot) {
    file = path.join(out, `${label}-${view}.png`);
    await page.screenshot({ path: file, fullPage: true });
  }
  return { view, ...metrics, violations, screenshot: file ? { path: file, sha256: sha(file) } : null };
}
async function keyboardProof(page) {
  await navigate(page, "school");
  const capability = page.locator('[data-test-id="school-matrix-capability-b-and"]');
  await capability.click();
  await page.locator('[data-test-id="investigation-inspector"]').waitFor();
  await page.keyboard.press("Escape");
  await page.waitForFunction(() =>
    document.activeElement?.dataset?.testId === "school-matrix-capability-b-and");
  check(await capability.evaluate(node => node === document.activeElement), "inspector focus did not return");
  await page.keyboard.press("Control+K");
  const palette = page.locator('[data-test-id="shell-command-palette"]');
  check(await palette.evaluate(node => node.open), "command palette did not open from keyboard");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() =>
    !document.querySelector('[data-test-id="shell-command-palette"]')?.open);
  await page.waitForTimeout(20);
  const skip = page.locator('[data-test-id="shell-skip-main"]');
  await skip.focus(); await skip.press("Enter");
  check(await page.locator('[data-test-id="shell-main-content"]').evaluate(node => node === document.activeElement),
    "skip link did not move focus to main content");
  return true;
}
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const srv = server(); await new Promise(resolve => srv.listen(0, "127.0.0.1", resolve));
  const port = srv.address().port;
  const browser = await playwright.chromium.launch({ executablePath: chrome, headless: true });
  const result = { schema: "bilqis.gui1143.closeout-browser/v1", variants: {}, representative: {} };
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    const errors = []; page.on("pageerror", error => errors.push(String(error)));
    await page.goto(`http://127.0.0.1:${port}/apps/mission-control/renderer/`);
    await page.addScriptTag({ url: `http://127.0.0.1:${port}/axe.min.js` }); await reconnect(page);
    for (const [theme, density] of [["dark", "comfortable"], ["dark", "compact"],
      ["light", "comfortable"], ["light", "compact"]]) {
      await setDisplay(page, theme, density);
      await page.addScriptTag({ url: `http://127.0.0.1:${port}/axe.min.js` });
      const key = `${theme}-${density}-desktop`; result.variants[key] = [];
      for (const view of views) {
        await navigate(page, view);
        result.variants[key].push(await audit(page, view, key, theme === "dark" && density === "comfortable"));
      }
    }
    result.representative.keyboard = await keyboardProof(page);
    result.representative.shellUsability = await shellUsabilityProof(
      page, { check, setDisplay, navigate, reconnect });
    result.representative.accessibilityTree = await accessibilityTreeProof(
      page, { check, navigate });
    await page.setViewportSize({ width: 390, height: 844 });
    await setDisplay(page, "light", "compact");
    await page.addScriptTag({ url: `http://127.0.0.1:${port}/axe.min.js` });
    result.variants["light-compact-responsive"] = [];
    for (const view of views) {
      await navigate(page, view);
      result.variants["light-compact-responsive"].push(await audit(page, view,
        "light-compact-responsive", true));
    }
    result.representative.expandedRtl = await expansionProof(page, { check, navigate });
    await page.reload({ waitUntil: "domcontentloaded" }); await reconnect(page);
    await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
    await navigate(page, "school");
    const forced = path.join(out, "forced-colors-reduced-motion-school.png");
    await page.screenshot({ path: forced, fullPage: true });
    result.representative.forcedColorsReducedMotion = { path: forced, sha256: sha(forced) };
    result.representative.pageErrors = errors;
    check(errors.length === 0, `browser page errors: ${errors.join(" | ")}`);
    fs.writeFileSync(path.join(out, "browser-result.json"), JSON.stringify(result, null, 2) + "\n");
    console.log(JSON.stringify({ ok: true, output: out, variants: Object.keys(result.variants),
      screenshots: Object.values(result.variants).flat().filter(row => row.screenshot).length + 1 }));
  } finally {
    await browser.close(); await new Promise(resolve => srv.close(resolve));
  }
})().catch(error => { console.error(error.stack || error); process.exitCode = 1; });
