const { chromium } = require(process.env.BILQIS_PLAYWRIGHT_MODULE || "playwright");
const { execFileSync } = require("node:child_process");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../../../..");
const baseRef = process.env.BILQIS_CAPABILITY_BASE_REF || "a68961296b9ae4dc40b8813b2b91fd1633453c73";
const { assetPathForRendererRequest } = require("../../electron/shell/renderer-protocol.cjs");
const fromBase = relative => execFileSync("git", ["show", `${baseRef}:${relative}`], {
  cwd: root, encoding: "utf8",
});
const baseline = {
  app: fromBase("apps/mission-control/renderer/capability/app.mjs")
    .replace('from "./controller.mjs"', 'from "/apps/mission-control/renderer/capability/controller.mjs"')
    .replace('from "./model.mjs"', 'from "/apps/mission-control/renderer/capability/model.mjs"')
    .replace('from "./fixture.mjs"', 'from "/apps/mission-control/renderer/capability/fixture.mjs"')
    .replace('from "./view.mjs"', 'from "/baseline/view.mjs"'),
  view: fromBase("apps/mission-control/renderer/capability/view.mjs")
    .replace('from "./model.mjs"', 'from "/apps/mission-control/renderer/capability/model.mjs"'),
  css: fromBase("apps/mission-control/renderer/capability/dossier.css"),
};

const server = http.createServer((req, res) => {
  if (req.url === "/baseline/app.mjs") {
    res.setHeader("Content-Type", "text/javascript"); res.end(baseline.app); return;
  }
  if (req.url === "/baseline/view.mjs") {
    res.setHeader("Content-Type", "text/javascript"); res.end(baseline.view); return;
  }
  if (req.url === "/baseline/dossier.css") {
    res.setHeader("Content-Type", "text/css"); res.end(baseline.css); return;
  }
  const prefix = "/apps/mission-control/renderer";
  const asset = req.url.startsWith(prefix + "/")
    ? assetPathForRendererRequest("bamf-mc://app" + req.url.slice(prefix.length), path.join(root, "apps/mission-control/renderer"))
    : null;
  if (req.url !== "/" && !asset) { res.statusCode = 404; res.end(); return; }
  if (req.url === "/") {
    res.setHeader("Content-Type", "text/html");
    res.end(`<!doctype html><html lang="en" data-theme="dark" data-density="comfortable"><head>
      <meta charset="utf-8"><title>Capability Explorer fixture</title>
      <link rel="stylesheet" href="/apps/mission-control/renderer/visual-tokens.css">
      <link rel="stylesheet" href="/apps/mission-control/renderer/components.css">
      <link id="capability-css" rel="stylesheet" href="/baseline/dossier.css">
      <style>
        html,body{margin:0;min-width:0;background:var(--canvas);color:var(--text);font-family:Inter,system-ui,sans-serif}
        body{box-sizing:border-box;padding:32px} @media(max-width:480px){body{padding:12px}}
      </style></head><body><main data-test-id="fixture-host"></main></body></html>`);
    return;
  }
  try {
    res.setHeader("Content-Type", asset.endsWith(".css") ? "text/css" : "text/javascript");
    res.end(fs.readFileSync(asset));
  } catch {
    res.statusCode = 404; res.end();
  }
});

async function mount(page, moduleUrl) {
  await page.evaluate(async (url) => {
    const { createCapabilityExplorer } = await import(url);
    const host = document.querySelector('[data-test-id="fixture-host"]');
    host.innerHTML = "";
    window.__openedEvidence = null;
    let state = {
      context: { runId: "fixture:gui05", generation: 3, mode: "HISTORICAL", fixture: true },
      selected: { kind: "capability", id: "B.AND" },
    };
    let explorer;
    const apply = () => explorer.update(state);
    explorer = createCapabilityExplorer({
      host,
      serviceQuery: async () => { throw new Error("CONTROL_PLANE_UNAVAILABLE"); },
      changeLens: (lens, capabilityId) => {
        state = { ...state, context: { ...state.context, ...lens }, selected: { kind: "capability", id: capabilityId } };
        apply();
      },
      openObject: selected => {
        state = { ...state, selected };
        apply();
      },
      openEvidence: selected => { window.__openedEvidence = selected; },
      resolvePins: () => {},
    });
    window.__setCapabilityContext = next => {
      state = { ...state, context: { ...state.context, ...next } };
      apply();
    };
    apply();
  }, moduleUrl);
}

(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const out = path.join(root, "output/playwright/1131");
  fs.mkdirSync(out, { recursive: true });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);

  await mount(page, "/baseline/app.mjs");
  await page.screenshot({ path: path.join(out, "before-dark.png"), fullPage: true });

  await page.evaluate(() => { document.querySelector("#capability-css").href = "/apps/mission-control/renderer/capability/dossier.css"; });
  await mount(page, "/apps/mission-control/renderer/capability/app.mjs");
  await page.locator('[data-test-id="capability-name"]').waitFor();

  const axePath = process.env.BILQIS_AXE_MODULE;
  if (axePath) await page.addScriptTag({ path: require.resolve(axePath) });
  const result = { baseRef, variants: [] };
  for (const [theme, density, width] of [
    ["dark", "comfortable", 1440],
    ["light", "compact", 1440],
    ["dark", "comfortable", 390],
    ["light", "compact", 320],
  ]) {
    await page.evaluate(([nextTheme, nextDensity]) => {
      document.documentElement.dataset.theme = nextTheme;
      document.documentElement.dataset.density = nextDensity;
    }, [theme, density]);
    await page.setViewportSize({ width, height: 1100 });
    const reflow = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > innerWidth,
      width: document.documentElement.scrollWidth,
      viewport: innerWidth,
    }));
    if (reflow.overflow) throw new Error(`CAPABILITY_REFLOW:${width}:${JSON.stringify(reflow)}`);
    const violations = axePath ? await page.evaluate(async () => (
      await axe.run('[data-test-id="capability-view"]', {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"] },
      })
    ).violations.map(({ id, impact, nodes }) => ({
      id, impact, count: nodes.length,
      nodes: nodes.slice(0, 3).map(node => ({ target: node.target, html: node.html })),
    }))) : null;
    if (violations?.length) throw new Error(JSON.stringify(violations));
    result.variants.push({ theme, density, width, overflow: false, violations });
    await page.screenshot({ path: path.join(out, `after-${theme}-${density}-${width}.png`), fullPage: true });
  }

  await page.evaluate(() => window.__setCapabilityContext({ mode: "LIVE", generation: 3, runId: "fixture:gui05", fixture: true }));
  const context = page.locator('[data-test-id="capability-context"]');
  await context.waitFor();
  if (!(await context.innerText()).includes("LIVE")) throw new Error("CAPABILITY_CONTEXT_LIVE_MISSING");
  await page.screenshot({ path: path.join(out, "after-fixture-live-dark.png"), fullPage: true });
  result.fixtureLiveMode = true;
  await page.evaluate(() => window.__setCapabilityContext({ mode: "HISTORICAL", generation: 3, runId: "fixture:gui05", fixture: true }));
  await context.waitFor();
  if (!(await context.innerText()).includes("HISTORICAL")) throw new Error("CAPABILITY_CONTEXT_HISTORICAL_MISSING");

  await page.setViewportSize({ width: 320, height: 1100 });
  await page.evaluate(() => {
    document.documentElement.dir = "rtl";
    document.documentElement.dataset.theme = "dark";
    document.documentElement.dataset.density = "compact";
    document.querySelector('[data-test-id="capability-view"]').style.cssText =
      "line-height:1.5;letter-spacing:.12em;word-spacing:.16em";
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const spacing = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > innerWidth,
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
  }));
  if (spacing.overflow) throw new Error(`CAPABILITY_RTL_TEXT_SPACING_REFLOW:${JSON.stringify(spacing)}`);
  result.rtlTextSpacingReducedMotion = true;
  await page.screenshot({ path: path.join(out, "after-rtl-text-spacing-320.png"), fullPage: true });

  await page.evaluate(() => {
    document.documentElement.dir = "ltr";
    document.documentElement.dataset.theme = "dark";
    document.documentElement.dataset.density = "comfortable";
    document.querySelector('[data-test-id="capability-view"]').style.cssText = "";
  });
  await page.setViewportSize({ width: 1440, height: 1100 });
  const { capabilityJourney } = await import(path.join(root, "apps/mission-control/tests/browser/capability-journey.mjs"));
  result.journey = await capabilityJourney(page);
  await page.screenshot({ path: path.join(out, "after-defensive-unavailable.png"), fullPage: true });
  fs.writeFileSync(path.join(out, "browser-result.json"), JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify(result));
  await browser.close();
  server.close();
})().catch(error => {
  console.error(error);
  server.close();
  process.exit(1);
});
