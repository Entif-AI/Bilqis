import test from 'node:test';
import assert from 'node:assert/strict';
import { referenceResourceState } from '../../renderer/resources/resource-model.mjs';
import { renderResourceMarkup, bindResourceInteractions } from '../../renderer/resources/resource-view.mjs';
import { RESOURCE_MESSAGES } from '../../renderer/resources/resource-messages.mjs';

test('resource presentation has unique hooks and translates and escapes copy', () => {
  const messages = { 'en-US': { ...RESOURCE_MESSAGES['en-US'], 'resource.title': '<Budget>' } };
  const html = renderResourceMarkup(referenceResourceState(), { messages });
  assert.match(html, /&lt;Budget&gt;/);
  const ids = [...html.matchAll(/data-test-id="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size);
  assert.match(html, /<details/);
});

test('blank input does not request generation zero and inspection carries raw identities', () => {
  let submit, click, inspected, requested;
  const sample = { id: 'sample:<1>', exactRefs: ['source:<x>&'] };
  const form = { addEventListener: (_, cb) => { submit = cb; }, elements: { generation: { value: '  ' } } };
  const button = { dataset: { resourceInspect: sample.id }, addEventListener: (_, cb) => { click = cb; } };
  const host = { __resourceState: { current: { timeline: [sample] } }, querySelectorAll: () => [button], querySelector: () => form };
  bindResourceInteractions(host, { onInspect: value => { inspected = value; }, onCompare: value => { requested = value; } });
  submit({ preventDefault() {}, currentTarget: form });
  assert.equal(requested, undefined);
  click();
  assert.equal(inspected.details['Accepted ref 1'], 'source:<x>&');
});

test('signed overage and request state remain explicit', () => {
  const state = referenceResourceState();
  const profile = { ...state.current, memoryDecomposition: [{ id: 'other', state: 'PRESENT', value: 49 * 1024 ** 3 }] };
  const html = renderResourceMarkup({ current: profile, comparison: null, comparisonState: 'LOADING', comparisonGeneration: 0 });
  assert.match(html, /Category overage/);
  assert.match(html, /-1\.0 GiB/);
  assert.match(html, /Requested generation 0: LOADING/);
  const failure = renderResourceMarkup({ current: profile, comparison: null, comparisonState: 'UNAVAILABLE', comparisonGeneration: 7 });
  assert.match(failure, /Requested generation 7: UNAVAILABLE/);
});

test('comparison accepts zero and rejects malformed or unsafe generation', () => {
  let submit;
  const calls = [];
  const form = { elements: { generation: { value: '' } }, addEventListener: (_, cb) => { submit = cb; } };
  const host = { querySelectorAll: () => [], querySelector: () => form };
  bindResourceInteractions(host, { onCompare: value => calls.push(value) });
  for (const value of [' ', '-1', '1.5', '1e2', '9007199254740992', '0', ' 42 ']) {
    form.elements.generation.value = value;
    submit({ preventDefault() {}, currentTarget: form });
  }
  assert.deepEqual(calls, [0, 42]);
});

test('page state, timestamp units, named table scrollers and value templates are exposed', () => {
  const state = referenceResourceState();
  const messages = { 'en-US': { ...RESOURCE_MESSAGES['en-US'], 'resource.format.percent': '{value} pct', 'resource.format.money': 'USD {value}' } };
  const profile = { ...state.current, pageState: 'PARTIAL', aggregate: { ...state.current.aggregate, monetaryCost: { state: 'PRESENT', value: 2, units: 'USD' } } };
  const html = renderResourceMarkup({ ...state, current: profile }, { messages });
  assert.match(html, /data-test-id="resources-page-state"[^>]*>.*PARTIAL/s);
  assert.match(html, /Unix seconds/);
  assert.match(html, /tabindex="0" role="region" aria-label="Memory decomposition"/);
  assert.match(html, /73\.0 pct/);
  assert.match(html, /USD 2\.00/);
});

test('typed references stay separate even when identities contain commas', () => {
  let click, inspected;
  const sample = { id: 'sample', exactRefGroups: { source: ['s:a,b', 's:c'], evidence: ['e:a'], receipt: ['r:a'] } };
  const button = { dataset: { resourceInspect: sample.id }, addEventListener: (_, cb) => { click = cb; } };
  bindResourceInteractions({ __resourceState: { current: { timeline: [sample] } }, querySelectorAll: () => [button], querySelector: () => null }, { onInspect: value => { inspected = value; } });
  click();
  assert.equal(inspected.details['Source ref 1'], 's:a,b');
  assert.equal(inspected.details['Source ref 2'], 's:c');
  assert.equal(inspected.details['Evidence ref 1'], 'e:a');
  assert.equal(inspected.details['Receipt ref 1'], 'r:a');
});

test('unsafe generation gets localized recovery feedback', () => {
  let submit, validity, reported = false;
  const input = { value: '9007199254740992', setCustomValidity: text => { validity = text; }, reportValidity: () => { reported = true; } };
  const form = { elements: { generation: input }, addEventListener: (_, cb) => { submit = cb; } };
  bindResourceInteractions({ querySelectorAll: () => [], querySelector: () => form }, {});
  submit({ preventDefault() {}, currentTarget: form });
  assert.equal(validity, 'Enter a whole generation from 0 to 9007199254740991.');
  assert.equal(reported, true);
});

test('all analytical tables expose stable identity-column measurement hooks', () => {
  const html = renderResourceMarkup(referenceResourceState());
  const hooks = [...html.matchAll(/data-test-id="(resources-(?:decomposition|compute|length|timeline|comparison)-identity)"/g)];
  assert.equal(hooks.length, 5);
  assert.equal(new Set(hooks.map(match => match[1])).size, 5);
});
