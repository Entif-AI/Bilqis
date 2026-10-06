import copy
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from bilqis_ref.ithkuil_fixture import compile_issue, validate_fixture
from bilqis_ref.ithkuil_battery import validate_rows, summarize, compare_orders, render_reports, run_epoch, service_identity
from bilqis_ref.semantics import digest
from bilqis_ref.semantics import canonical
from bilqis_ref.decision import kev_score, permute

ROOT = Path(__file__).resolve().parents[1]
ISSUE = ROOT/'fixtures/new-ithkuil-v0.1.issue.md'


class FrozenBatteryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = compile_issue(ISSUE.read_text())

    def rows(self):
        rows = []
        for cell in self.fixture['cells']:
            for d in cell.get('steps', [cell]):
                candidates = d['candidates']
                rows.append({'decision_id': d['id'], 'cell_id': cell['id'],
                             'selected_id': d['gold_candidate'], 'gold_id': d['gold_candidate'],
                             'candidate_order': [x['id'] for x in candidates], 'candidates': candidates,
                             'probabilities': {x['id']: .7 if x['id']==d['gold_candidate'] else .1 for x in candidates},
                             'question': d['prompt'], 'latency_ms': 10., 'context_packet_sha256': self.fixture['context_packet_sha256'],
                             'runtime_identity': {'model':'jaredpalmer/kev-4b','model_revision':'test-revision'},
                             'sequence_context': {}, 'state_sha256': 'same', 'prompt_or_state_hash':'same', 'warm_state':True})
        return rows

    def test_exact_transcription_and_topology(self):
        validate_fixture(self.fixture)
        self.assertEqual(36, len(self.fixture['cells']))
        self.assertEqual(42, sum(len(c.get('steps',[c])) for c in self.fixture['cells']))
        simple = self.fixture['cells'][0]
        self.assertEqual('COA(-r-) + DSS(-c-)', simple['candidates'][0]['description'])
        self.assertIn('two physically separate, similar members', simple['prompt'])
        medium = next(c for c in self.fixture['cells'] if c['id']=='F03-MEDIUM')
        self.assertTrue(medium['gold_candidate'].endswith('.B'))
        hard = next(c for c in self.fixture['cells'] if c['id']=='F10-HARD')
        self.assertEqual([1,2,3,4], [s['step_number'] for s in hard['steps']])
        self.assertEqual(next(c for c in self.fixture['cells'] if c['id']=='F01-HARD')['candidates'][0]['description'], hard['steps'][3]['candidates'][0]['description'])

    def test_bad_fixture_rejected(self):
        for mutate in [lambda f:f['cells'].pop(),
                       lambda f:f['cells'].__setitem__(1,copy.deepcopy(f['cells'][0])),
                       lambda f:f['cells'][0].__setitem__('gold_candidate','unknown'),
                       lambda f:next(c for c in f['cells'] if c['id']=='F10-HARD')['steps'].pop()]:
            broken=copy.deepcopy(self.fixture); mutate(broken)
            with self.assertRaises(ValueError):validate_fixture(broken)

    def test_complete_probabilities_identity_and_coverage_required(self):
        rows=self.rows();validate_rows(self.fixture,rows)
        for mutate in [lambda r:r.pop(),lambda r:r.append(copy.deepcopy(r[0])),
                       lambda r:r[0]['probabilities'].pop(next(iter(r[0]['probabilities']))),
                       lambda r:r[1]['runtime_identity'].__setitem__('model_revision','other'),
                       lambda r:r[0].__setitem__('context_packet_sha256','other')]:
            broken=copy.deepcopy(rows);mutate(broken)
            with self.assertRaises(ValueError):validate_rows(self.fixture,broken)

    def test_wrong_path_right_final_does_not_pass_joint(self):
        rows=self.rows()
        step=next(r for r in rows if r['decision_id']=='F10-HARD.S1')
        step['selected_id']=step['candidate_order'][1]
        step['probabilities']={k:.7 if k==step['selected_id'] else .1 for k in step['candidate_order']}
        summary=summarize(self.fixture,rows)
        self.assertEqual({'correct':35,'total':36},summary['canonical'])
        self.assertEqual({'correct':41,'total':42},summary['atomic'])
        self.assertEqual({'correct':3,'total':3},summary['sequential']['final'])
        self.assertEqual({'correct':2,'total':3},summary['sequential']['joint'])

    def test_order_comparison_matches_ids_not_positions(self):
        a=self.rows();b=copy.deepcopy(a)
        for row in b:
            row['candidates']=row['candidates'][1:]+row['candidates'][:1]
            row['candidate_order']=[o['id'] for o in row['candidates']]
        value=compare_orders(self.fixture,a,b)
        self.assertEqual(42,value['atomic_unchanged'])
        self.assertEqual(0,value['atomic_changed'])
        b[0]['question']='changed prompt'
        with self.assertRaises(ValueError):compare_orders(self.fixture,a,b)

    def test_report_replay_is_deterministic_and_readable(self):
        rows=self.rows();permuted=copy.deepcopy(rows)
        for row in permuted:
            row['candidates']=row['candidates'][1:]+row['candidates'][:1]
            row['candidate_order']=[o['id'] for o in row['candidates']]
        report=render_reports(self.fixture,rows,permuted)
        self.assertEqual(report,render_reports(self.fixture,rows,permuted))
        self.assertEqual({'RESULTS.md','FAILURES.md','CAPABILITY_MAP.md'},set(report))
        self.assertIn('F10-HARD.S4',report['RESULTS.md'])
        self.assertIn('36 / 36',report['RESULTS.md'])
        self.assertIn('42 / 42',report['RESULTS.md'])

    def test_paired_epoch_preserves_request_states_and_raw_rows(self):
        # Boundary test uses stub context and scorer; no model or linguistic gold is authored.
        import hashlib
        import contextlib
        import io
        from bilqis_ref import ithkuil_battery, ithkuil_fixture
        packet=b'stub source bytes for HTTP boundary test'
        context_hash=hashlib.sha256(packet).hexdigest()
        model={'name':'kev-latest','run':'jaredpalmer/kev-4b@test-revision','base':'test-base','lora':16,
               'backend':'mlx','device':'mps','dtype':'bfloat16','temperature':2.4,'max_state_tokens':65536,
               'truncate_states':False,'prefix_cache':{'size':4,'min_state_tokens':0,'max_tokens':65536}}
        seen={'A':{},'B':{}};current=['A']
        def score(item,endpoint,identity):
            seen[current[0]][item['id']]=copy.deepcopy(item)
            selected=item['options'][0]['id']
            return {'selected_id':selected,'probabilities':{o['id']:.7 if o['id']==selected else .1 for o in item['options']},
                    'runtime_metadata':{'models':model,'native':{'retained':True}},'latency_ms':10.,'warm_state':True,
                    'state_sha256':digest(item['state']),'prompt_or_state_hash':digest(item),
                    'http_candidate_order':[o['id'] for o in item['options']],'request_payload_sha256':digest(item)}
        with tempfile.TemporaryDirectory() as tmp, patch.object(ithkuil_battery,'CONTEXT_SHA256',context_hash), patch.object(ithkuil_fixture,'CONTEXT_SHA256',context_hash), patch.object(ithkuil_battery,'local_json',return_value={'models':[model]}), patch.object(ithkuil_battery,'kev_score',side_effect=score), contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);fixture_path=root/'fixture.json';context=root/'context.md';identity=root/'identity.json'
            fixture=compile_issue(ISSUE.read_text());fixture_path.write_text(json.dumps(fixture));fixture_path.with_suffix('.issue.md').write_text(ISSUE.read_text());context.write_bytes(packet)
            identity.write_text(json.dumps({'model':'jaredpalmer/kev-4b','model_revision':'test-revision','service':service_identity(model)}))
            run_epoch(fixture_path,context,identity,root/'A','A')
            current[0]='B';run_epoch(fixture_path,context,identity,root/'B','B',root/'A/rows.jsonl')
            for key,a in seen['A'].items():
                b=seen['B'][key]
                self.assertEqual(a['state'],b['state']);self.assertEqual(a['question'],b['question'])
                self.assertNotEqual([o['id'] for o in a['options']],[o['id'] for o in b['options']])
                self.assertNotIn('gold',a)
            rows=[json.loads(s) for s in (root/'A/rows.jsonl').read_text().splitlines()]
            self.assertEqual(42,len(rows));self.assertTrue(all(r['runtime_metadata']['native']['retained'] for r in rows))
            with self.assertRaises(FileExistsError):run_epoch(fixture_path,context,identity,root/'A','A')

    def test_native_choice_order_reaches_actual_http_bytes(self):
        import io
        from bilqis_ref import local_http
        model={'run':'jaredpalmer/kev-4b@test-revision','backend':'mlx','prefix_cache':{'hits':0}}
        sent=[]
        class Opener:
            def open(self,request,timeout):
                if request.data is None:return io.BytesIO(json.dumps({'models':[model]}).encode())
                payload=json.loads(request.data);criteria=payload['questions']['decision']['criteria'];sent.append(request.data)
                selected=next(iter(criteria))
                return io.BytesIO(json.dumps({'answers':{'decision':{'choice':selected,'probabilities':{k:.7 if k==selected else .1 for k in criteria}}}}).encode())
        d=self.fixture['cells'][0]
        item={'id':d['id'],'split':'DEV','state':{'z':'last','a':'first'},'question':d['prompt'],'options':d['candidates']}
        identity={'model':'jaredpalmer/kev-4b','model_revision':'test-revision'}
        with patch.object(local_http.urllib.request,'build_opener',return_value=Opener()):
            kev_score(item,'http://127.0.0.1:8008',identity)
            changed=permute(item,77);kev_score(changed,'http://127.0.0.1:8008',identity)
        original={'model':'kev-latest','state':item['state'],'questions':{'decision':{'type':'choice','instructions':item['question'],'criteria':{o['id']:o['description'] for o in item['options']}}}}
        self.assertEqual(canonical(original),sent[0])
        self.assertEqual([o['id'] for o in changed['options']],list(json.loads(sent[1])['questions']['decision']['criteria']))
        self.assertEqual(json.loads(sent[0])['state'],json.loads(sent[1])['state'])


if __name__=='__main__':unittest.main()
