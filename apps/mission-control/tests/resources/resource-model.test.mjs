import test from 'node:test';
import assert from 'node:assert/strict';
import {decomposition} from '../../renderer/resources/resource-model.mjs';
import {referenceResourceState} from '../../renderer/resources/resource-fixture-state.mjs';
const metric = (value) => ({state:'PRESENT',value});
function profile(aggregate, categories) {
  return {aggregate:{unifiedMemoryUsed:aggregate},memoryDecomposition:categories};
}
test('complete reconciliation requires all category values and exact aggregate agreement', () => {
  const result=decomposition(profile(metric(10),[metric(10),{state:'UNAVAILABLE',value:null}]));
  assert.equal(result.complete,false);
  assert.equal(result.reconciliationState,'PARTIAL');
  assert.equal(result.remainder,0);
});
test('category overage remains signed and partial rather than complete', () => {
  const result=decomposition(profile(metric(10),[metric(12)]));
  assert.equal(result.remainder,-2);
  assert.equal(result.complete,false);
  assert.equal(result.reconciliationState,'PARTIAL');
});
test('zero is complete only with explicit measured zero categories', () => {
  const result=decomposition(profile(metric(0),[metric(0)]));
  assert.equal(result.remainder,0);
  assert.equal(result.complete,true);
  assert.equal(result.reconciliationState,'COMPLETE');
});
test('unavailable or nonfinite aggregate does not acquire a numeric remainder', () => {
  for(const aggregate of [{state:'UNAVAILABLE',value:null},metric(Infinity)]) {
    const result=decomposition(profile(aggregate,[metric(1)]));
    assert.equal(result.remainder,null);
    assert.equal(result.complete,false);
    assert.equal(result.reconciliationState,'UNAVAILABLE');
  }
});
test('fixture unknown category and remainder remain explicit', () => {
  const result=decomposition(referenceResourceState().current);
  assert.equal(result.remainder,8*1024**3);
  assert.equal(result.reconciliationState,'PARTIAL');
});
test('live samples retain individual reference identities and known reference kinds',async()=>{
  const {resourceProfileFromPage}=await import('../../renderer/resources/resource-model.mjs');
  const profile=resourceProfileFromPage({accepted:true,state:'PRESENT',records:[{
    schema_version:'bilqis.bamf.mission-control.resource-sample/v1',
    meta:{record_id:'r',source_refs:['source:a,b','source:c'],evidence_refs:['evidence:a'],receipt_refs:['receipt:a']},
  }]},{});
  assert.deepEqual(profile.timeline[0].exactRefGroups,{source:['source:a,b','source:c'],evidence:['evidence:a'],receipt:['receipt:a']});
});
