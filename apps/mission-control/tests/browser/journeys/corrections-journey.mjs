export async function correctionsJourney(page) {
  const hook = id=>page.locator(`[data-test-id="${id}"]`);
  const group = prefix=>page.locator(`[data-test-id^="${prefix}"]`);
  const check = (condition,message)=>{if(!condition)throw new Error(message);};
  await page.evaluate(async()=>{
    const {renderCurrentView}=await import('/apps/mission-control/renderer/foundation/current-view.mjs');
    const {renderInspector}=await import('/apps/mission-control/renderer/foundation/renderer-ui.mjs');
    const {openEvidence,openSelectionOwner}=await import('/apps/mission-control/renderer/shell-state.mjs');
    window.routing={openEvidence,openSelectionOwner};
    window.mount=(mode='LIVE',untagged=false)=>{
      window.fixtureState={view:'corrections',selected:untagged?{kind:'correction',id:'capability:C.SUCCESSOR'}:null,
        inspectorOpen:untagged,context:{mode,runId:'fixture-shell-run',generation:7}};
      window.defense={historical:mode==='HISTORICAL'};
      window.render=()=>{
        renderCurrentView(window.fixtureState,window.defense,selected=>{
          window.fixtureState={...window.fixtureState,selected,inspectorOpen:true};window.render();
        },{});
        renderInspector(window.fixtureState,window.defense);
      };
      window.render();
    };
    window.mount();
  });
  check(await group('corrections-impact-row-').count()===8,'all eight affected identities in equivalent table');
  check((await hook('corrections-fixture-notice').innerText()).includes('not a live or reconstructed snapshot'),'fixture boundary leads');
  await hook('corrections-graph-toggle').focus();await page.keyboard.press('Enter');
  check(await hook('corrections-graph').evaluate(e=>e.open),'graph keyboard disclosure');
  check(await group('corrections-graph-edge-').count()===7,'all explicit dependency edges');
  const endpoints=await group('corrections-graph-endpoint-').evaluateAll(items=>items.map(item=>({text:item.textContent,html:item.outerHTML})));
  const expected=await page.evaluate(async()=>{const {CORRECTION_FIXTURE}=await import('/apps/mission-control/renderer/corrections/corrections-fixture.mjs');return CORRECTION_FIXTURE.nodes;});
  for(const node of expected) check(endpoints.some(endpoint=>endpoint.text.includes(node.id) && endpoint.text.includes(node.kind) && endpoint.html.includes(`data-correction-state="${node.state}"`)),'graph endpoint identity/kind/state '+node.id);
  await group('corrections-graph-from-').first().focus();await page.keyboard.press('Enter');
  check(await hook('corrections-graph').evaluate(e=>e.open),'native graph disclosure survives inspector repaint');
  check((await hook('fixture-inspector-title').innerText())==='source:numeric-registry:r9','graph inspection selects exact artifact');
  check(await hook('inspector-open-owner').isDisabled() && await hook('inspector-open-evidence').isDisabled(),'unproven fixture routes disabled');
  await group('corrections-custody-toggle-').first().click();
  check((await hook('corrections-queue-table').innerText()).includes('3'.repeat(64)),'checkpoint one action away');
  check((await hook('corrections-queue-table').innerText()).includes('No receipt · Not requalified'),'absence not completion');
  await group('corrections-history-receipt-').first().click();
  check((await hook('fixture-inspector-title').innerText())==='receipt:correction-numeric-r8-r9','history receipt exact local inspection');
  check(await page.evaluate(()=>window.fixtureState.selected.details['Reference type'])==='Receipt','receipt callback type retained');
  await group('corrections-artifact-ref-').first().click();
  check(await page.evaluate(()=>window.fixtureState.selected.details['Reference type'])==='Evidence reference','reference callback type retained');
  const history=await hook('corrections-history').innerText();
  check(history.indexOf('44238')<history.indexOf('44239'),'append-only chronology retains recorded order');
  for(const id of ['generation:44238','cache:successor:r8','capability:C.SUCCESSOR','motif:'+'c'.repeat(64)]) check(history.includes(id),'full history preserves '+id);
  for(const mode of ['LIVE','HISTORICAL']){
    for(const untagged of [false,true]){
      await page.evaluate(({mode,untagged})=>window.mount(mode,untagged),{mode,untagged});
      if(!untagged) await group('corrections-artifact-').first().click();
      const inspector=await hook('fixture-inspector-summary').innerText();
      check(inspector.includes('Fixture projection · not live or reconstructed evidence'),'truthful inspector '+mode);
      check(!inspector.includes('Verified prior evidence'),'fixture never promoted by historical lens');
      check(await hook('inspector-open-owner').isDisabled() && await hook('inspector-open-evidence').isDisabled(),'bounded fixture routes '+mode);
      check(await page.evaluate(()=>window.routing.openEvidence(window.fixtureState)===window.fixtureState && window.routing.openSelectionOwner(window.fixtureState)===window.fixtureState),'non-UI route guards '+mode);
      check((await hook('corrections-fixture-notice').innerText()).includes('not a live'),'fixture posture after rehydrated selection');
    }
  }
  check(await page.evaluate(()=>{
    const ids=[...document.querySelectorAll('[data-test-id]')].map(e=>e.dataset.testId);
    return ids.length===new Set(ids).size;
  }),'every rendered test hook unique');
  await page.evaluate(()=>window.mount());
  return {passed:true,claims:['explicit graph/table parity','keyboard inspection','custody disclosure','exact receipt inspection','complete chronological history','fixture custody across live/historical/reloaded selections','guarded owner/evidence routes','unique hooks']};
}
