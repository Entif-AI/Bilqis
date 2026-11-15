const { chromium } = require(process.env.BILQIS_PLAYWRIGHT_MODULE || 'playwright');
const { execFileSync } = require('node:child_process');
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '../../../..');
const baseRef = process.env.BILQIS_MODEL_BASE_REF || '490e86e1a284fd03c3824e0bce656d658df0052c';
const { assetPathForRendererRequest } = require('../../electron/shell/renderer-protocol.cjs');
const framePages = JSON.parse(fs.readFileSync(path.join(root, 'apps/mission-control/fixtures/frame-inspections-v1.json'), 'utf8'));
const baseline = Object.fromEntries(['neural-view.mjs', 'neural-model.mjs', 'neural-fixture.mjs'].map(name => [name,
  execFileSync('git', ['show', `${baseRef}:apps/mission-control/renderer/neural/${name}`], { cwd: root, encoding: 'utf8' })]));
baseline['neural.css'] = execFileSync('git', ['show', `${baseRef}:apps/mission-control/renderer/neural/neural.css`], { cwd: root, encoding: 'utf8' });

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/baseline/neural/')) {
    const name = req.url.split('/').at(-1), source = baseline[name];
    if (!source) { res.statusCode = 404; res.end(); return; }
    res.setHeader('Content-Type', name.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(source); return;
  }
  const prefix = '/apps/mission-control/renderer';
  const asset = req.url.startsWith(prefix + '/') ? assetPathForRendererRequest('bamf-mc://app' + req.url.slice(prefix.length), path.join(root, 'apps/mission-control/renderer')) : null;
  if (req.url !== '/' && !asset) { res.statusCode = 404; res.end(); return; }
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html lang="en"><head><title>Model fixture</title><link rel="stylesheet" href="/apps/mission-control/renderer/visual-tokens.css"><link rel="stylesheet" href="/apps/mission-control/renderer/components.css"><link id="neural-css" rel="stylesheet" href="/apps/mission-control/renderer/neural/neural.css"><link rel="stylesheet" href="/apps/mission-control/renderer/frame-explorer.css"></head><body style="display:block;padding:32px"><nav class="model-nav" aria-label="Model sections" data-test-id="shell-model-subnav"><button type="button" aria-pressed="true" data-test-id="shell-model-neural">Neural Runtime</button><button type="button" aria-pressed="false" data-test-id="shell-model-frames">Frame Compiler Explorer</button></nav><main data-test-id="fixture-host"></main></body></html>');
    return;
  }
  try { res.setHeader('Content-Type', asset.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(fs.readFileSync(asset)); } catch { res.statusCode = 404; res.end(); }
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  fs.mkdirSync('output/playwright/1134', { recursive: true });
  await page.evaluate(async () => {
    document.querySelector('#neural-css').href = '/baseline/neural/neural.css';
    const neural = await import('/baseline/neural/neural-view.mjs');
    neural.renderNeuralView(document.querySelector('[data-test-id="fixture-host"]'), () => {});
  });
  await page.screenshot({ path: 'output/playwright/1134/before-dark.png', fullPage: true });

  const { modelJourney } = await import(path.join(root, 'apps/mission-control/tests/browser/model-journey.mjs'));
  await page.evaluate(() => { document.querySelector('#neural-css').href = '/apps/mission-control/renderer/neural/neural.css'; document.querySelector('[data-test-id="fixture-host"]').innerHTML = ''; });
  const result = await modelJourney(page, framePages);
  const axePath = process.env.BILQIS_AXE_MODULE;
  if (axePath) await page.addScriptTag({ path: require.resolve(axePath) });
  result.variants = [];

  async function inspectSurface(surface, theme, density, width, suffix) {
    await page.evaluate(([nextTheme, nextDensity, nextSurface]) => {
      document.documentElement.dataset.theme = nextTheme; document.documentElement.dataset.density = nextDensity; document.documentElement.dir = 'ltr';
      document.querySelector('[data-test-id="shell-model-neural"]').setAttribute('aria-pressed', String(nextSurface === 'neural'));
      document.querySelector('[data-test-id="shell-model-frames"]').setAttribute('aria-pressed', String(nextSurface === 'frame'));
    }, [theme, density, surface]);
    await page.setViewportSize({ width, height: 1100 });
    if (surface === 'neural') await page.evaluate(() => window.mountNeural('current'));
    else {
      await page.evaluate(async pages => {
        const frame = await import('/apps/mission-control/renderer/frames/frame-explorer.mjs');
        const root = document.querySelector('[data-test-id="fixture-host"]');
        root.innerHTML = '<section data-test-id="model-frame-workspace-host"></section>';
        frame.mountFrameExplorer(root.firstElementChild, { querySnapshot: request => Promise.resolve(structuredClone(pages.find(item => item.request.generation === request.generation))), context: { runId: 'fixture-run', generation: 7, mode: 'LIVE', freshness: 'FRESH' }, selectedId: null, onContext() {}, onSelection() {} });
      }, framePages);
      await page.locator('[data-test-id="model-frame-result-set"]').waitFor();
      await page.locator('[data-test-id="model-frame-example"]').selectOption({ index: 1 });
      await page.locator('[data-test-id="model-frame-selected-metrics"]').waitFor();
    }
    const reflow = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth > innerWidth, width: document.documentElement.scrollWidth, viewport: innerWidth }));
    if (reflow.overflow) throw new Error(`MODEL_REFLOW:${surface}:${width}:${JSON.stringify(reflow)}`);
    const selector = surface === 'neural' ? '[data-test-id="model-neural-workspace"]' : '[data-test-id="model-frame-workspace"]';
    const violations = axePath ? await page.evaluate(async selector => (await axe.run(selector, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] } })).violations.map(({ id, impact, nodes }) => ({ id, impact, count: nodes.length })), selector) : null;
    if (violations?.length) throw new Error(`MODEL_AXE:${surface}:${JSON.stringify(violations)}`);
    result.variants.push({ surface, theme, density, width, overflow: reflow.overflow, violations });
    await page.screenshot({ path: `output/playwright/1134/after-${surface}-${suffix}.png`, fullPage: true });
  }

  for (const [theme, density, width, suffix] of [['dark', 'comfortable', 1440, 'dark-comfortable-1440'], ['light', 'compact', 1440, 'light-compact-1440'], ['dark', 'comfortable', 390, 'dark-comfortable-390'], ['light', 'compact', 320, 'light-compact-320']]) {
    await inspectSurface('neural', theme, density, width, suffix);
    await inspectSurface('frame', theme, density, width, suffix);
  }

  await page.setViewportSize({ width: 320, height: 1100 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const surface of ['neural', 'frame']) {
    if (surface === 'neural') {
      await page.evaluate(() => window.mountNeural('current'));
    } else {
      await page.evaluate(async pages => {
        const frame = await import('/apps/mission-control/renderer/frames/frame-explorer.mjs');
        const root = document.querySelector('[data-test-id="fixture-host"]');
        root.innerHTML = '<section data-test-id="model-frame-workspace-host"></section>';
        frame.mountFrameExplorer(root.firstElementChild, { querySnapshot: request => Promise.resolve(structuredClone(pages.find(item => item.request.generation === request.generation))), context: { runId: 'fixture-run', generation: 7, mode: 'LIVE', freshness: 'FRESH' }, selectedId: null, onContext() {}, onSelection() {} });
      }, framePages);
      await page.locator('[data-test-id="model-frame-result-set"]').waitFor();
      await page.locator('[data-test-id="model-frame-example"]').selectOption({ index: 1 });
      await page.locator('[data-test-id="model-frame-selected-metrics"]').waitFor();
    }
    await page.evaluate(surface => {
      document.documentElement.dir = 'rtl';
      const id = surface === 'neural' ? 'model-neural-workspace' : 'model-frame-workspace';
      const node = document.querySelector(`[data-test-id="${id}"]`);
      node.style.cssText = 'line-height:1.5;letter-spacing:.12em;word-spacing:.16em';
    }, surface);
    const spacing = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > innerWidth,
      width: document.documentElement.scrollWidth,
      viewport: innerWidth,
      boxes: [...document.querySelectorAll('[data-test-id^="model-"]')].map(element => {
        const rect = element.getBoundingClientRect();
        return { tag: element.tagName, className: element.className, testId: element.dataset?.testId, left: rect.left, right: rect.right, width: rect.width, scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
      }),
      offenders: [...document.querySelectorAll('[data-test-id^="model-"]')].map(element => {
        const rect = element.getBoundingClientRect();
        return { tag: element.tagName, className: element.className, testId: element.dataset.testId, left: rect.left, right: rect.right, width: rect.width };
      }).filter(item => item.left < -1 || item.right > innerWidth + 1).slice(0, 16),
    }));
    if (spacing.overflow) throw new Error(`MODEL_RTL_TEXT_SPACING_REFLOW:${surface}:${JSON.stringify(spacing)}`);
    await page.screenshot({ path: `output/playwright/1134/after-${surface}-rtl-text-spacing-320.png`, fullPage: true });
  }
  result.rtlTextSpacingReducedMotion = true;
  fs.writeFileSync('output/playwright/1134/browser-result.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
  await browser.close(); server.close();
})().catch(error => { console.error(error); server.close(); process.exit(1); });
