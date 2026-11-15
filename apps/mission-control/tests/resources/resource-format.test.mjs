import test from 'node:test';
import assert from 'node:assert/strict';
import {bytes} from '../../renderer/resources/resource-format.mjs';
import {RESOURCE_MESSAGES} from '../../renderer/resources/resource-messages.mjs';
import {createTranslator} from '../../renderer/foundation/i18n.mjs';
test('small nonzero byte readings and overages do not round into zero',()=>{
 const t=createTranslator({messages:RESOURCE_MESSAGES});
 assert.equal(bytes(t,1),'1 bytes');assert.equal(bytes(t,-1),'-1 bytes');
 assert.equal(bytes(t,0),'0 bytes');assert.equal(bytes(t,1024**2),'1.0 MiB');
});
