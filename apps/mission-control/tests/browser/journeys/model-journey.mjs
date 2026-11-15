export async function modelJourney(page, framePages) {
  const hook = id => page.locator(`[data-test-id="${id}"]`);
  const check = (condition, message) => { if (!condition) throw new Error(message); };

  await page.evaluate(async () => {
    const neural = await import('/apps/mission-control/renderer/neural/neural-view.mjs');
    window.mountNeural = mode => {
      document.querySelector('[data-test-id="fixture-host"]').innerHTML = neural.renderNeuralMarkup(mode);
    };
    window.mountNeural('current');
  });
  check(await hook('model-neural-workspace').count() === 1, 'neural workspace present');
  check(await hook('model-neural-topology-runtime').count() === 1, 'topology/runtime leads');
  check(await hook('model-neural-ccgqa-table').count() === 1, 'CCGQA analytical table present');
  check(await hook('model-neural-help-topology-trigger').count() === 1, 'topology help present');
  check(await hook('model-neural-help-instrumentation-trigger').count() === 1, 'instrumentation help present');
  check((await hook('model-neural-fixture-posture').innerText()).includes('read-only'), 'fixture posture explicit');
  await hook('model-neural-ccgqa-disclosure').locator('summary').click();
  check((await hook('model-neural-ccgqa-layer-7').innerText()).includes('Mask-invalid violations: 2'), 'invalid evidence remains explicit');
  check(await page.evaluate(() => {
    const ids = [...document.querySelectorAll('[data-test-id^="model-"]')].map(element => element.dataset.testId);
    return ids.length === new Set(ids).size;
  }), 'neural hooks unique');

  await page.evaluate(() => window.mountNeural('historical'));
  for (const id of ['model-neural-ccgqa-unavailable', 'model-neural-attnres-unavailable', 'model-neural-refinement-unavailable']) {
    check(await hook(id).count() === 1, `${id} present`);
  }
  check(!(await hook('model-neural-workspace').innerText()).includes('91.0%'), 'historical view does not synthesize current CCGQA values');

  await page.evaluate(async pages => {
    const frame = await import('/apps/mission-control/renderer/frames/frame-explorer.mjs');
    const root = document.querySelector('[data-test-id="fixture-host"]');
    root.innerHTML = '<section data-test-id="model-frame-workspace-host"></section>';
    window.frameContextLog = [];
    window.frameSelectionLog = [];
    frame.mountFrameExplorer(root.querySelector('[data-test-id="model-frame-workspace-host"]'), {
      querySnapshot: request => Promise.resolve(structuredClone(pages.find(item => item.request.generation === request.generation))),
      context: { runId: 'fixture-run', generation: 7, mode: 'LIVE', freshness: 'FRESH' },
      selectedId: null,
      onContext: (operatorView, mode) => window.frameContextLog.push({ generation: operatorView.meta.run.generation, mode }),
      onSelection: id => window.frameSelectionLog.push(id),
    });
  }, framePages);
  await hook('model-frame-result-set').waitFor();
  check((await hook('model-frame-fixture-posture').innerText()).includes('READ ONLY'), 'frame fixture posture explicit');
  check((await hook('model-frame-coverage').innerText()).includes('3 returned fixture receipts'), 'frame coverage literal');
  check(await hook('model-frame-help-concepts-trigger').count() === 1, 'frame concepts help present');
  check(await hook('model-frame-help-controls-trigger').count() === 1, 'frame controls help present');
  check(await page.locator('[data-source-unix-seconds]').count() >= 2, 'frame source timestamps use shared temporal primitive');
  await hook('model-frame-example').selectOption({ index: 1 });
  await hook('model-frame-selected-metrics').waitFor();
  check(await hook('model-frame-receipt-provenance').evaluate(node => node.open) === false, 'receipt provenance is progressive disclosure');
  await hook('model-frame-receipt-provenance-toggle').click();
  check((await hook('model-frame-receipt-provenance').innerText()).includes('Compiler digest'), 'exact compiler receipt remains accessible');
  check(await hook('model-frame-frontier').count() === 1, 'prediction frontier available');
  check(await page.evaluate(() => {
    const ids = [...document.querySelectorAll('[data-test-id^="model-"]')].map(element => element.dataset.testId);
    return ids.length === new Set(ids).size;
  }), 'frame hooks unique');
  await hook('model-frame-generation').selectOption('6');
  await page.waitForFunction(() => document.querySelector('[data-test-id="model-frame-request-state"]')?.textContent.includes('generation 6'));
  check(await page.evaluate(() => window.frameContextLog.at(-1)?.mode === 'historical'), 'historical frame custody explicit');
  return { passed: true, claims: ['peer workspaces distinct', 'mechanism-first diagnostics', 'fixture posture explicit', 'historical absence stays unavailable', 'frame receipts progressive', 'frame custody exact', 'unique hooks'] };
}
