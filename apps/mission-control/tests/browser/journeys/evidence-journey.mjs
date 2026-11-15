// Run against a static repository-root server; all application locators use hooks.
export async function evidenceJourney(page, { modulePath = "/apps/mission-control/renderer/evidence/evidence-view.mjs" } = {}) {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const hook = (id) => page.locator(`[data-test-id="${id}"]`);
  // Intentional groups of record results and selected-record target actions.
  const recordButtons = () => page.locator('[data-test-id^="evidence-record-result-"]');
  const waitText = (id, text) => page.waitForFunction(({id, text}) =>
    document.querySelector(`[data-test-id="${id}"]`)?.textContent.includes(text), {id, text});
  await page.evaluate(async (modulePath) => {
    window.evidenceModule = await import(modulePath);
    window.makeRecord = (id) => ({schema_version: "receipt/v1", meta: {
      record_id: id, authority: "MEASURED", coverage: "COMPLETE", run: {run_id: "fixture-run", generation: 7},
      source_refs: ["source:exact"], evidence_refs: ["evidence:exact"], receipt_refs: [],
    }, valid: false, absent: null, long_value: "long-exact-identity:" + "z".repeat(300)});
    window.a = window.makeRecord("receipt:a"); window.b = window.makeRecord("receipt:b");
    window.reply = (request, overrides = {}) => ({accepted:true, state:"PRESENT", coverage:"COMPLETE", returned:1,total_matches:2,
      records:[],links:[],markers:[],next_cursor:null,truncated:false,request,...overrides});
    window.mount = (initial = null) => {
      window.evidenceModule.deactivateEvidenceView();
      window.requests = []; window.returnedOrigin = false;
      const api = {query: request => new Promise((resolve, reject) => window.requests.push({request,resolve,reject}))};
      window.evidenceModule.renderEvidenceView(document.querySelector('[data-test-id="fixture-host"]'), api,
        {mode:"HISTORICAL",runId:"fixture-run",generation:7}, initial, null, ()=>window.returnedOrigin=true,
        {view:"capability",selected:{kind:"capability",id:"B.AND"},context:{mode:"HISTORICAL",runId:"fixture-run",generation:7}});
    };
    window.resolveRequest = (index, overrides) => window.requests[index].resolve(window.reply(window.requests[index].request,overrides));
    window.mount();
    window.resolveRequest(0,{records:[window.a],next_cursor:"next:1",truncated:true});
  }, modulePath);
  await recordButtons().first().waitFor();
  // Pagination must complete even when selection begins in the meantime.
  await hook("evidence-more").click();
  await recordButtons().first().click();
  await page.evaluate(()=>window.resolveRequest(1,{records:[window.b]}));
  await waitText("evidence-query-status", "State:");
  check(!(await hook("evidence-query-status").innerText()).includes("Awaiting"), "selection cannot strand page loading");
  check(await recordButtons().count() === 2, "next page appends after selection");
  check(await hook("evidence-results-heading").evaluate(e=>e === document.activeElement) === false, "completion preserves explicit selected-heading focus");
  // An unsent selector, identity and caret survive a related-record response.
  await hook("evidence-query-kind").selectOption("source");
  await hook("evidence-query-value").fill("unsubmitted-exact-reference");
  await hook("evidence-query-value").evaluate(e=>{e.focus();e.setSelectionRange(3,8);});
  await hook("evidence-metadata").evaluate(e=>e.open=true);
  await page.evaluate(()=>window.resolveRequest(2,{links:[],returned:0,total_matches:0}));
  await hook("evidence-selected-links-status").waitFor();
  check(await hook("evidence-query-kind").inputValue() === "source", "unsent query kind preserved");
  check(await hook("evidence-query-value").inputValue() === "unsubmitted-exact-reference", "unsent query value preserved");
  check(await hook("evidence-query-value").evaluate(e=>e === document.activeElement && e.selectionStart===3 && e.selectionEnd===8), "query focus and selection preserved");
  check(await hook("evidence-metadata").evaluate(e=>e.open), "disclosure preserved on async completion");
  await hook("evidence-mode-raw").focus(); await page.keyboard.press("Enter");
  check(await hook("evidence-mode-raw").evaluate(e=>e===document.activeElement), "raw mode retains keyboard focus");
  const raw = JSON.parse(await hook("evidence-raw-payload").innerText());
  check(raw.valid === false && raw.absent === null && raw.meta.record_id === "receipt:a", "literal raw payload parity");
  await hook("evidence-mode-readable").click();
  await hook("evidence-return").click();
  check(await page.evaluate(()=>window.returnedOrigin), "explicit origin return callback");

  // Exact-link traversal and reference search keep their different request families.
  await page.evaluate(()=>{
    window.mount({kind:"evidence",id:"receipt:a"});
    window.resolveRequest(0,{records:[window.a]});
  });
  await hook("evidence-detail-heading").waitFor();
  await page.evaluate(()=>window.resolveRequest(1,{links:[{relation:"supports",source_record_id:"receipt:a",target_ref:"receipt:b",target_record_id:"receipt:b"}]}));
  await page.locator('[data-test-id^="evidence-selected-open-"]').click();
  check(await page.evaluate(()=>window.requests[2].request.record_id)==="receipt:b", "traversal requests exact target");
  await page.evaluate(()=>window.resolveRequest(2,{records:[window.b]}));
  await waitText("evidence-detail-heading", "receipt:b");
  await page.evaluate(()=>window.resolveRequest(3,{links:[],returned:0,total_matches:0}));
  await page.locator('[data-test-id^="evidence-ref-source-"]').click();
  check(await page.evaluate(()=>window.requests[4].request.family)==="reference", "provenance action uses reference family");
  check(await hook("evidence-query-value").inputValue()==="source:exact", "reference search resets query intentionally");
  await page.evaluate(()=>window.resolveRequest(4,{records:[],returned:0,total_matches:0,state:"EMPTY"}));
  await hook("evidence-results-empty").waitFor();

  // Bootstrap hydration cannot replace a newer explicit selection's links.
  await page.evaluate(()=>{
    window.mount({kind:"evidence",id:"receipt:a"});
    window.resolveRequest(0,{records:[window.a,window.b]});
  });
  await recordButtons().nth(1).waitFor();
  await recordButtons().nth(1).click();
  await page.evaluate(()=>{
    window.resolveRequest(2,{links:[{relation:"new-b-link",source_record_id:"receipt:b",target_ref:"external:b"}]});
    window.resolveRequest(1,{links:[{relation:"old-a-link",source_record_id:"receipt:a",target_ref:"external:a"}]});
  });
  await waitText("evidence-related", "new-b-link");
  check(!(await hook("evidence-related").innerText()).includes("old-a-link"), "stale bootstrap links rejected");
  // A fresh query also invalidates pending selection hydration.
  await recordButtons().first().click();
  await hook("evidence-query-value").fill("receipt:fresh");
  await hook("evidence-query-submit").click();
  await page.evaluate(()=>{
    window.resolveRequest(3,{links:[{relation:"stale-after-search",source_record_id:"receipt:a",target_ref:"external:old"}]});
    window.resolveRequest(4,{records:[window.makeRecord("receipt:fresh")]});
  });
  await recordButtons().first().waitFor();
  check(!(await hook("evidence-workspace").innerText()).includes("stale-after-search"), "fresh query invalidates selection work");
  check((await hook("evidence-detail").innerText()).includes("Select a record") && await hook("evidence-detail-heading").count() === 0, "fresh search clears selection");

  // New user intent supersedes a deep-link bootstrap that has not returned.
  await page.evaluate(()=>window.mount({kind:"evidence",id:"receipt:a"}));
  await hook("evidence-query-value").fill("new-reference");
  await hook("evidence-query-submit").click();
  await page.evaluate(()=>window.resolveRequest(1,{records:[window.a,window.b]}));
  await recordButtons().nth(1).waitFor();
  check(await hook("evidence-detail-heading").count()===0, "fresh query clears bootstrap pending record");
  check(await page.evaluate(()=>window.requests.length)===2, "fresh query must not hydrate old pending identity");
  await page.evaluate(()=>window.resolveRequest(0,{records:[window.a]}));

  // A failed next page retains evidence and cursor; retry is explicit.
  await page.evaluate(()=>{window.mount();window.resolveRequest(0,{records:[window.a],next_cursor:"next:1"});});
  await hook("evidence-more").waitFor(); await hook("evidence-more").click();
  await page.evaluate(()=>window.requests[1].reject(new Error("QUERY_UNAVAILABLE")));
  await hook("evidence-query-error").waitFor();
  check(await recordButtons().count()===1, "page failure preserves prior result");
  check(await hook("evidence-more").isEnabled(), "page failure permits bounded retry");
  await hook("evidence-more").click();
  await page.evaluate(()=>window.resolveRequest(2,{records:[window.b]}));
  await recordButtons().nth(1).waitFor();
  check(await hook("evidence-results-heading").evaluate(e=>e===document.activeElement), "removed pagination control yields focus to results");

  // Loading, degraded, empty, denied, disconnected and traversal failure stay distinct.
  for (const state of ["EMPTY","PARTIAL","STALE","MISSING","DENIED","UNAVAILABLE","UNKNOWN"]) {
    await page.evaluate(state=>{window.mount();window.resolveRequest(0,{state,coverage:state==="EMPTY"?"COMPLETE":"UNKNOWN",records:[],returned:0,total_matches:0,
      markers:state==="PARTIAL"?[{schema_version:"partial/v1",meta:{record_id:"marker:1"},missing_fields:["grader_receipt"]}]:[]});},state);
    await waitText("evidence-query-status", `State: ${state}`);
    if(state==="PARTIAL") check((await hook("evidence-omissions").innerText()).includes("grader_receipt"), "missing evidence named");
  }
  await page.evaluate(()=>{window.mount();window.requests[0].reject(new TypeError("api.query is not a function"));});
  await hook("evidence-query-error").waitFor();
  await hook("evidence-query-error-toggle").click();
  check((await hook("evidence-query-error").innerText()).includes("disconnected"), "disconnection explicit");
  await page.evaluate(()=>{window.mount({kind:"evidence",id:"receipt:a"});window.resolveRequest(0,{records:[window.a]});});
  await hook("evidence-detail-heading").waitFor();
  await page.evaluate(()=>window.requests[1].reject(new Error("QUERY_DENIED")));
  await hook("evidence-traversal-error").waitFor();
  await hook("evidence-mode-raw").click();
  check((await hook("evidence-traversal-error").innerText()).includes("QUERY_DENIED"), "raw mode retains traversal failure");
  return {passed: true, claims: ["pagination-selection concurrency", "draft/caret/disclosure custody", "bootstrap cancellation", "fresh-query cancellation", "exact traversal/reference", "raw parity", "origin callback", "pagination recovery/focus", "defensive states"]};
}
