import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../../..");
const rendererRoot = path.join(repoRoot, "apps/mission-control/renderer");
const baseRef = process.env.BILQIS_MEMORY_BASE_REF ?? "origin/codex/bamf-unified-base-20261028";
const outputRoot = path.resolve(repoRoot, process.env.BILQIS_MEMORY_EVIDENCE_DIR ?? "output/browser/1135");
const chromePath = process.env.BILQIS_CHROME_PATH ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function harnessHtml() {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Memory visual harness</title></head><body><main data-test-id="fixture-host"></main><pre data-test-id="browser-result" hidden></pre><script type="module">
const q=new URLSearchParams(location.search),source=q.get("source")==="baseline"?"baseline":"current",prefix=source==="baseline"?"/baseline/apps/mission-control/renderer":"/current/apps/mission-control/renderer";
for(const css of ["visual-tokens.css","shell.css","components.css","memory/memory.css"]){const link=document.createElement("link");link.rel="stylesheet";link.href=\`\${prefix}/\${css}\`;document.head.append(link)}
document.documentElement.dataset.theme=q.get("theme")||"dark";document.documentElement.dataset.density=q.get("density")||"comfortable";if(q.get("rtl")==="1")document.documentElement.dir="rtl";
document.body.style.cssText="display:block;padding:32px;box-sizing:border-box;";if(q.get("spacing")==="1")document.body.style.cssText+="line-height:1.5;letter-spacing:.12em;word-spacing:.16em;";
const{renderMemoryView}=await import(\`\${prefix}/memory/memory-view.mjs\`),context=q.get("historical")==="missing"?{runId:"fixture-run",generation:1,mode:"HISTORICAL"}:null;renderMemoryView(document.querySelector('[data-test-id="fixture-host"]'),()=>{},null,context);
await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const ids=[...document.querySelectorAll('[data-test-id^="memory-"]')].map(el=>el.dataset.testId),interactive=[...document.querySelectorAll('[data-test-id^="memory-"]')].filter(el=>["BUTTON","SELECT","SUMMARY","A"].includes(el.tagName)).map(el=>{const r=el.getBoundingClientRect();return{tag:el.tagName,w:r.width,h:r.height,text:(el.textContent||"").trim().slice(0,80)}});
const result={source,theme:document.documentElement.dataset.theme,density:document.documentElement.dataset.density,rtl:document.documentElement.dir==="rtl",documentOverflow:document.documentElement.scrollWidth>innerWidth,scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,duplicateTestIds:ids.filter((v,i)=>ids.indexOf(v)!==i),details:[...document.querySelectorAll('[data-test-id^="memory-"]')].filter(el=>el.tagName==="DETAILS").map(d=>({testId:d.dataset.testId||null,open:d.open})),historicalUnavailable:!!document.querySelector('[data-test-id="memory-historical-unavailable"]'),currentSummary:!!document.querySelector('[data-test-id="memory-summary"]'),tables:["memory-atlas-table-wrap","memory-compare-table-wrap"].map(id=>document.querySelector(\`[data-test-id="\${id}"]\`)).filter(Boolean).map(el=>({scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,localOverflow:el.scrollWidth>el.clientWidth})),minInteractive:interactive.length?{w:Math.min(...interactive.map(x=>x.w)),h:Math.min(...interactive.map(x=>x.h))}:null,smallInteractive:interactive.filter(x=>x.w<24||x.h<24)};
document.querySelector('[data-test-id="browser-result"]').textContent=JSON.stringify(result);</script></body></html>`;
}

function contentType(file) {
  if (file.endsWith(".mjs") || file.endsWith(".js")) return "text/javascript";
  if (file.endsWith(".css")) return "text/css";
  if (file.endsWith(".html")) return "text/html";
  return "application/octet-stream";
}

async function assetFor(urlPath) {
  if (urlPath === "/harness.html") return { body: harnessHtml(), type: "text/html" };
  for (const source of ["current", "baseline"]) {
    const prefix = `/${source}/apps/mission-control/renderer/`;
    if (!urlPath.startsWith(prefix)) continue;
    const relative = urlPath.slice(`/${source}/`.length);
    if (relative.includes("..")) return null;
    if (source === "baseline") {
      try { return { body: execFileSync("git", ["show", `${baseRef}:${relative}`], { cwd: repoRoot }), type: contentType(relative) }; } catch { return null; }
    }
    const file = path.resolve(repoRoot, relative);
    if (!file.startsWith(rendererRoot + path.sep)) return null;
    try { return { body: await readFile(file), type: contentType(file) }; } catch { return null; }
  }
  return null;
}

async function startServer() {
  const server = createServer(async (req, res) => {
    const asset = await assetFor(new URL(req.url, "http://127.0.0.1").pathname);
    if (!asset) { res.writeHead(404).end("not found"); return; }
    res.writeHead(200, { "content-type": asset.type }); res.end(asset.body);
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  return { server, origin: `http://127.0.0.1:${server.address().port}` };
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function runChrome(url, width, height, screenshotPath, reduced = false) {
  const profile = `/private/tmp/bilqis-memory-cdp-${process.pid}-${Math.random().toString(16).slice(2)}`;
  await mkdir(profile, { recursive: true });
  const chrome = spawn(chromePath, ["--headless=new", "--disable-gpu", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: "ignore" });
  let port;
  for (let i = 0; i < 100; i++) {
    try { port = Number((await readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]); break; } catch { await sleep(50); }
  }
  assert.ok(port, "Chrome CDP port unavailable");
  const target = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: "PUT" }).then(response => response.json());
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.addEventListener("open", resolve, { once: true }); ws.addEventListener("error", reject, { once: true }); });
  let seq = 0; const pending = new Map();
  ws.addEventListener("message", event => {
    const message = JSON.parse(event.data), waiter = pending.get(message.id);
    if (!waiter) return;
    pending.delete(message.id); message.error ? waiter.reject(new Error(JSON.stringify(message.error))) : waiter.resolve(message.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false, screenWidth: width, screenHeight: height });
  if (reduced) await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await send("Page.navigate", { url });
  let result;
  for (let i = 0; i < 100; i++) {
    await sleep(50);
    const observed = await send("Runtime.evaluate", { expression: `document.querySelector('[data-test-id="browser-result"]')?.textContent||""`, returnByValue: true });
    if (observed.result.value) { result = JSON.parse(observed.result.value); break; }
  }
  assert.ok(result, "Memory browser result timed out");
  const metrics = await send("Page.getLayoutMetrics"), content = metrics.cssContentSize ?? metrics.contentSize;
  const screenshot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, fromSurface: true, clip: { x: 0, y: 0, width: Math.ceil(content.width), height: Math.ceil(content.height), scale: 1 } });
  await writeFile(screenshotPath, Buffer.from(screenshot.data, "base64"));
  ws.close(); chrome.kill("SIGTERM"); await sleep(100); await rm(profile, { recursive: true, force: true });
  return { ...result, requestedViewport: { width, height }, screenshot: path.relative(repoRoot, screenshotPath), contentSize: { width: content.width, height: content.height } };
}

const variants = [
  ["before-dark-comfortable-1440.png", "source=baseline&theme=dark&density=comfortable", 1440, false],
  ["after-dark-comfortable-1440.png", "source=current&theme=dark&density=comfortable", 1440, false],
  ["after-light-compact-1440.png", "source=current&theme=light&density=compact", 1440, false],
  ["after-dark-comfortable-390.png", "source=current&theme=dark&density=comfortable", 390, false],
  ["after-light-compact-320.png", "source=current&theme=light&density=compact", 320, false],
  ["after-rtl-text-spacing-reduced-motion-320.png", "source=current&theme=dark&density=comfortable&rtl=1&spacing=1", 320, true],
  ["after-historical-unavailable-320.png", "source=current&theme=dark&density=comfortable&historical=missing", 320, false],
];

await mkdir(outputRoot, { recursive: true });
const { server, origin } = await startServer();
try {
  const results = [];
  for (const [name, query, width, reduced] of variants) results.push(await runChrome(`${origin}/harness.html?${query}`, width, 1000, path.join(outputRoot, name), reduced));
  const current = results.filter(item => item.source === "current");
  assert.ok(current.every(item => !item.documentOverflow), "Memory document overflow");
  assert.ok(current.every(item => item.duplicateTestIds.length === 0), "Duplicate Memory test hooks");
  assert.ok(current.every(item => item.smallInteractive.length === 0), "Memory target below 24px");
  assert.ok(current.filter(item => !item.historicalUnavailable).every(item => item.details.every(detail => !detail.open)), "Progressive disclosures opened by default");
  assert.ok(current.filter(item => item.requestedViewport.width <= 390 && !item.historicalUnavailable).every(item => item.tables.every(table => table.localOverflow)), "Wide Memory data escaped local scrollers");
  const historical = current.find(item => item.historicalUnavailable);
  assert.ok(historical && !historical.currentSummary, "Historical unavailable state blended current memory");
  await writeFile(path.join(outputRoot, "browser-result.json"), JSON.stringify({ baseRef, variants: results }, null, 2) + "\n");
  console.log(`MEMORY_BROWSER_CHECK_OK variants=${results.length} base=${baseRef}`);
} finally {
  await new Promise(resolve => server.close(resolve));
}
