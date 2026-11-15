import test from 'node:test';
import assert from 'node:assert/strict';
import {createResourceController} from '../../renderer/resources/resource-controller.mjs';
const host=()=>({hidden:false,innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null});
const context=(generation=7)=>({runId:'run-test',generation,mode:'LIVE'});
const page=(value)=>({accepted:true,state:'PRESENT',records:[{
  schema_version:'bilqis.bamf.mission-control.resource-sample/v1',meta:{record_id:`resource:${value}`},
  memory_used_bytes:{state:'PRESENT',value,units:'bytes'},
}]});
function deferred(){let resolve; const promise=new Promise(r=>{resolve=r;});return {promise,resolve};}
test('older context response cannot replace the newly activated context',async()=>{
  const first=deferred();let count=0;
  const controller=createResourceController({query:()=>++count===1?first.promise:Promise.resolve(page(9))});
  const pending=controller.activate(context(),{target:host()});
  await controller.activate(context(9),{target:host()});
  first.resolve(page(7));await pending;
  assert.equal(controller.currentState().current.aggregate.unifiedMemoryUsed.value,9);
  assert.equal(controller.currentState().current.generation,9);
});
test('latest exact comparison request wins even when earlier request finishes later',async()=>{
  const slow=deferred();
  const controller=createResourceController({query:r=>r.generation===5?slow.promise:Promise.resolve(page(r.generation??7))});
  await controller.activate(context(),{target:host()});
  const pending=controller.loadComparison(5);
  await controller.loadComparison(6);
  slow.resolve(page(5));await pending;
  assert.equal(controller.currentState().comparison.generation,6);
  assert.equal(controller.currentState().comparisonGeneration,6);
});
test('failed comparison retains the requested identity and rejects invalid direct requests',async()=>{
  const controller=createResourceController({query:r=>r.mode==='historical'?Promise.reject(Error('offline')):Promise.resolve(page(7))});
  await controller.activate(context(),{target:host()});
  await controller.loadComparison(5);
  assert.equal(controller.currentState().comparisonState,'UNAVAILABLE');
  assert.equal(controller.currentState().comparisonGeneration,5);
  await assert.rejects(controller.loadComparison(-1),/GUI15_HISTORICAL_GENERATION_REQUIRED/);
});
test('deactivation invalidates pending current responses and prevents subscriptions',async()=>{
  const wait=deferred();let subscriptions=0;
  const controller=createResourceController({query:()=>wait.promise,subscribeEvents:()=>{subscriptions++;return ()=>{};}});
  const pending=controller.activate(context(),{target:host()});
  await controller.deactivate();wait.resolve(page(7));await pending;
  assert.equal(subscriptions,0);
});
test('accepted empty historical query keeps identity without inventing a comparison profile',async()=>{
  const controller=createResourceController({query:r=>Promise.resolve(r.mode==='historical'?{accepted:true,state:'EMPTY',records:[]}:page(7))});
  await controller.activate(context(),{target:host()});await controller.loadComparison(4);
  assert.equal(controller.currentState().comparison,null);
  assert.equal(controller.currentState().comparisonState,'EMPTY');
  assert.equal(controller.currentState().comparisonGeneration,4);
});
