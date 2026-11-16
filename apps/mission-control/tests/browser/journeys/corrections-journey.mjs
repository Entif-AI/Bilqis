export async function correctionsJourney(page) {
  const hook = id => page.locator(`[data-test-id="${id}"]`);
  const group = prefix => page.locator(`[data-test-id^="${prefix}"]`);
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  await page.evaluate(async () => {
    const { CORRECTION_FIXTURE_SUPPORT } = await import('/apps/mission-control/renderer/corrections/corrections-fixture.mjs');
    const { bindCorrectionsInteractions, renderCorrectionsMarkup } = await import('/apps/mission-control/renderer/corrections/corrections-view.mjs');
    const { renderInspector } = await import('/apps/mission-control/renderer/foundation/renderer-ui.mjs');
    const { openEvidence, openSelectionOwner } = await import('/apps/mission-control/renderer/shell-state.mjs');
    window.routing = { openEvidence, openSelectionOwner };
    window.mount = (mode = 'LIVE', untagged = false) => {
      window.fixtureState = {
        view: 'corrections',
        selected: untagged ? { kind: 'correction', id: 'capability:C.SUCCESSOR', fixtureBacked: true } : null,
        inspectorOpen: untagged,
        context: { mode, runId: 'fixture-shell-run', generation: 7, fixture: true },
      };
      window.defense = { historical: mode === 'HISTORICAL' };
      const host = document.querySelector('[data-test-id="fixture-host"]');
      window.render = () => {
        host.innerHTML = renderCorrectionsMarkup(CORRECTION_FIXTURE_SUPPORT.projection, {
          messages: CORRECTION_FIXTURE_SUPPORT.messages,
          fixtureNotice: CORRECTION_FIXTURE_SUPPORT.notice,
        });
        bindCorrectionsInteractions(host, CORRECTION_FIXTURE_SUPPORT.projection, {
          onInspect: (id, node) => {
            window.fixtureState = { ...window.fixtureState, selected: {
              kind: 'correction', id, fixtureBacked: true,
              details: { 'Artifact class': node.kind, 'Impact state': node.state, 'Evidence references': node.evidenceRefs },
            }, inspectorOpen: true };
            renderInspector(window.fixtureState, window.defense);
          },
          onReference: (ref, kind) => {
            window.fixtureState = { ...window.fixtureState, selected: {
              kind: 'correction', id: ref, fixtureBacked: true,
              details: { 'Exact reference': ref, 'Reference type': kind === 'receipt' ? 'Receipt' : 'Evidence reference' },
            }, inspectorOpen: true };
            renderInspector(window.fixtureState, window.defense);
          },
        });
        renderInspector(window.fixtureState, window.defense);
      };
      window.render();
    };
    window.mount();
  });
  check(await group('corrections-impact-row-').count() === 8, 'all eight affected identities in equivalent table');
  check((await hook('corrections-fixture-notice').innerText()).includes('REFERENCE FIXTURES'), 'fixture boundary leads');
  await hook('corrections-tab-impact').click();
  await hook('corrections-graph-toggle').focus(); await page.keyboard.press('Enter');
  check(await hook('corrections-graph').evaluate(element => element.open), 'graph keyboard disclosure');
  check(await group('corrections-graph-edge-').count() === 7, 'all explicit dependency edges');
  const endpoints = await group('corrections-graph-endpoint-').evaluateAll(items => items.map(item => ({ text: item.textContent, html: item.outerHTML })));
  const expected = await page.evaluate(async () => { const { CORRECTION_FIXTURE } = await import('/apps/mission-control/renderer/corrections/corrections-fixture.mjs'); return CORRECTION_FIXTURE.nodes; });
  for (const node of expected) check(endpoints.some(endpoint => endpoint.text.includes(node.id) && endpoint.text.includes(node.kind) && endpoint.html.includes(`data-correction-state="${node.state}"`)), 'graph endpoint identity/kind/state ' + node.id);
  await group('corrections-graph-from-').first().focus(); await page.keyboard.press('Enter');
  check(await hook('corrections-graph').evaluate(element => element.open), 'native graph disclosure survives inspection');
  check((await hook('fixture-inspector-title').innerText()) === 'source:numeric-registry:r9', 'graph inspection selects exact artifact');
  check((await hook('fixture-inspector-summary').innerText()).includes('Reference fixture'), 'shared inspector keeps fixture provenance visible');
  await hook('corrections-tab-queue').click();
  await group('corrections-custody-toggle-').first().click();
  check((await hook('corrections-queue-table').innerText()).includes('3'.repeat(64)), 'checkpoint one action away');
  check((await hook('corrections-queue-table').innerText()).includes('Receipt pending'), 'absence stays pending');
  await hook('corrections-tab-history').click();
  await group('corrections-history-receipt-').first().click();
  check((await hook('fixture-inspector-title').innerText()) === 'receipt:correction-numeric-r8-r9', 'history receipt exact local inspection');
  check(await page.evaluate(() => window.fixtureState.selected.details['Reference type']) === 'Receipt', 'receipt callback type retained');
  const history = await hook('corrections-history').innerText();
  check(history.indexOf('44238') < history.indexOf('44239'), 'append-only chronology retains recorded order');
  for (const id of ['generation:44238', 'cache:successor:r8', 'capability:C.SUCCESSOR', 'motif:' + 'c'.repeat(64)]) check(history.includes(id), 'full history preserves ' + id);
  await hook('corrections-tab-impact').click();
  check(await hook('corrections-graph').evaluate(element => element.open), 'disclosure state survives tab changes');
  check((await hook('fixture-inspector-title').innerText()) === 'receipt:correction-numeric-r8-r9', 'selected reference survives tab changes');
  check(await page.evaluate(() => {
    const ids = [...document.querySelectorAll('[data-test-id]')].map(element => element.dataset.testId);
    return ids.length === new Set(ids).size;
  }), 'every rendered test hook unique');
  await page.evaluate(() => window.mount());
  return { passed: true, claims: ['four peer tabs', 'selection persistence', 'disclosure persistence', 'explicit graph/table parity', 'keyboard inspection', 'custody disclosure', 'exact receipt inspection', 'complete chronological history', 'unique hooks'] };
}
