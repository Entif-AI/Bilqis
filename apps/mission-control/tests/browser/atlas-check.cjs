const { chromium } = require(process.env.BILQIS_PLAYWRIGHT_MODULE || 'playwright');
const { execFileSync } = require('node:child_process');
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '../../../..');
const baseRef = process.env.BILQIS_ATLAS_BASE_REF || 'dada27e8b1776e0fb7917c61bd8df141a210f93a';
const { assetPathForRendererRequest } = require('../../electron/shell/renderer-protocol.cjs');
const baseline = {
  js: execFileSync('git', ['show', `${baseRef}:apps/mission-control/renderer/atlas/semantic-atlas.mjs`], { cwd: root, encoding: 'utf8' }),
  css: execFileSync('git', ['show', `${baseRef}:apps/mission-control/renderer/atlas/semantic-atlas.css`], { cwd: root, encoding: 'utf8' }),
};
const server = http.createServer((req, res) => {
  if (req.url === '/baseline/semantic-atlas.mjs') { res.setHeader('Content-Type', 'text/javascript'); res.end(baseline.js); return; }
  if (req.url === '/baseline/semantic-atlas.css') { res.setHeader('Content-Type', 'text/css'); res.end(baseline.css); return; }
  const prefix = '/apps/mission-control/renderer';
  const asset = req.url.startsWith(prefix + '/') ? assetPathForRendererRequest('bamf-mc://app' + req.url.slice(prefix.length), path.join(root, 'apps/mission-control/renderer')) : null;
  if (req.url !== '/' && !asset) { res.statusCode = 404; res.end(); return; }
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><html lang="en"><head><title>Atlas fixture</title><link rel="stylesheet" href="/apps/mission-control/renderer/visual-tokens.css"><link rel="stylesheet" href="/apps/mission-control/renderer/components.css"><link id="atlas-css" rel="stylesheet" href="/apps/mission-control/renderer/atlas/semantic-atlas.css"></head><body style="display:block;padding:32px"><main data-test-id="fixture-host"></main></body></html>');
    return;
  }
  try { res.setHeader('Content-Type', asset.endsWith('.css') ? 'text/css' : 'text/javascript'); res.end(fs.readFileSync(asset)); } catch { res.statusCode = 404; res.end(); }
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  fs.mkdirSync('output/playwright/1133', { recursive: true });
  await page.evaluate(async () => {
    document.querySelector('#atlas-css').href = '/baseline/semantic-atlas.css';
    const atlas = await import('/baseline/semantic-atlas.mjs');
    const pageOf = (records, total = records.length) => ({ schema: atlas.QUERY_PAGE_SCHEMA, accepted: true, state: total ? 'PRESENT' : 'EMPTY', records, markers: [], links: [], total_matches: total });
    const release = '1'.repeat(64), semantic = 'https://example.test/id/sense/very-long-semantic-identity-for-before-after-evidence';
    const overview = { summary: pageOf([{ schema_version: atlas.SUMMARY_SCHEMA, active_concepts: { value: 742 }, source_eligible: { value: 801 }, source_held: { value: 17 } }]), banks: pageOf([{ schema_version: atlas.BANK_SCHEMA, bank: 0, row_capacity: 8192, allocated_rows: 500, active_rows: 482, masked_rows: 18, recently_exercised_rows: 41, requalification_affected_rows: 3 }]), held: pageOf([], 0), similarities: pageOf([], 29) };
    const selection = { concept: { schema_version: atlas.CONCEPT_SCHEMA, semantic_id: semantic, kind: 'sense', atlas_release_sha256: release, source_loci: ['Source locus A'], relations: [], abi_index: 1, abi_bank: 0, abi_row: 1, capability_ids: ['B.IFF'], frame_schema_refs: ['frame:relation/v2'] }, state: { schema_version: atlas.STATE_SCHEMA, semantic_id: semantic, admission_state: 'ACTIVE', newly_admitted: false, recently_exercised: true, requalification_affected: false }, held: null, similarities: [] };
    document.querySelector('[data-test-id="fixture-host"]').innerHTML = atlas.renderAtlasMarkup({ status: 'ready', overview, selection, lens: 'canonical', selectedBank: 0 });
  });
  await page.screenshot({ path: 'output/playwright/1133/before-dark.png', fullPage: true });
  const { atlasJourney } = await import(path.join(root, 'apps/mission-control/tests/browser/atlas-journey.mjs'));
  await page.evaluate(() => { document.querySelector('#atlas-css').href = '/apps/mission-control/renderer/atlas/semantic-atlas.css'; document.querySelector('[data-test-id="fixture-host"]').innerHTML = ''; });
  const result = await atlasJourney(page);
  const axePath = process.env.BILQIS_AXE_MODULE;
  if (axePath) await page.addScriptTag({ path: require.resolve(axePath) });
  result.variants = [];
  for (const [theme, density, width] of [['dark', 'comfortable', 1440], ['light', 'compact', 1440], ['dark', 'comfortable', 390], ['light', 'compact', 320]]) {
    await page.evaluate(([nextTheme, nextDensity]) => { document.documentElement.dataset.theme = nextTheme; document.documentElement.dataset.density = nextDensity; }, [theme, density]);
    await page.setViewportSize({ width, height: 1100 });
    const reflow = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth > innerWidth, width: document.documentElement.scrollWidth, viewport: innerWidth }));
    const overflow = reflow.overflow;
    if (overflow) throw new Error(`ATLAS_REFLOW:${width}:${JSON.stringify(reflow)}`);
    const violations = axePath ? await page.evaluate(async () => (await axe.run('[data-test-id="atlas-view"]', { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] } })).violations.map(({ id, impact, nodes }) => ({ id, impact, count: nodes.length }))) : null;
    if (violations?.length) throw new Error(JSON.stringify(violations));
    result.variants.push({ theme, density, width, overflow, violations });
    await page.screenshot({ path: `output/playwright/1133/after-${theme}-${density}-${width}.png`, fullPage: true });
  }
  await page.evaluate(() => { document.documentElement.dir = 'rtl'; document.querySelector('[data-test-id="atlas-view"]').style.cssText = 'line-height:1.5;letter-spacing:.12em;word-spacing:.16em'; });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const spacingOverflow = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > innerWidth,
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
    offenders: [...document.querySelectorAll('[data-test-id^="atlas-"]')].map(element => {
      const rect = element.getBoundingClientRect();
      return { tag: element.tagName, className: element.className, testId: element.dataset.testId, left: rect.left, right: rect.right, width: rect.width };
    }).filter(item => item.left < -1 || item.right > innerWidth + 1).slice(0, 12),
  }));
  if (spacingOverflow.overflow) throw new Error(`ATLAS_RTL_TEXT_SPACING_REFLOW:${JSON.stringify(spacingOverflow)}`);
  result.rtlTextSpacingReducedMotion = true;
  await page.screenshot({ path: 'output/playwright/1133/after-rtl-text-spacing-320.png', fullPage: true });
  fs.writeFileSync('output/playwright/1133/browser-result.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
  await browser.close(); server.close();
})().catch(error => { console.error(error); server.close(); process.exit(1); });
