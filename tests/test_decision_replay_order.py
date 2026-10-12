import hashlib
import json
import unittest
from unittest.mock import patch


class ReplayOrderTest(unittest.TestCase):
    def test_sorted_json_receipt_preserves_original_request_bytes_and_option_order(self):
        from bilqis_alpha.decision_experiment import archived_request
        payload={'model':'kev-latest','state':'canonical state','questions':{'decision':{
            'type':'choice','instructions':'choose','criteria':{'z':'first','a':'second'}}}}
        serialized=json.dumps(payload,separators=(',',':'),ensure_ascii=True,sort_keys=False)
        trace={'payload':payload,'serialized_request':serialized,
               'request_sha256':hashlib.sha256(serialized.encode()).hexdigest(),'offered_candidate_ids':['z','a']}
        saved=json.loads(json.dumps(trace,sort_keys=True))
        self.assertEqual(list(saved['payload']['questions']['decision']['criteria']),['a','z'])
        restored=archived_request(saved)
        self.assertEqual(list(restored['questions']['decision']['criteria']),['z','a'])
        self.assertEqual(json.dumps(restored,separators=(',',':'),ensure_ascii=True,sort_keys=False),serialized)
        saved['offered_candidate_ids'].reverse()
        with self.assertRaisesRegex(ValueError,'ARCHIVED_REQUEST_BINDING'): archived_request(saved)

    def test_source_amendment_is_bound_to_frozen_revision_and_one_committed_file(self):
        from bilqis_alpha.decision_experiment import amended_source_hash
        path='bilqis_alpha/decision_experiment.py'; new=b'replay repair'
        metadata={'source_commit':'frozen'}
        receipt={'frozen_source_commit':'frozen','old_file_sha256':'old','new_source_commit':'repair',
                 'new_file_sha256':hashlib.sha256(new).hexdigest(),'file':path,
                 'scope':'archived Kev request order and explicit replay-source admission only'}
        with patch('bilqis_alpha.decision_experiment.subprocess.check_output',return_value=new):
            self.assertEqual(amended_source_hash(path,'old',metadata,receipt),receipt['new_file_sha256'])
            for field in ('file','frozen_source_commit','old_file_sha256','scope'):
                changed=dict(receipt); changed[field]='changed'
                with self.assertRaisesRegex(ValueError,'SOURCE_AMENDMENT_BINDING'):
                    amended_source_hash(path,'old',metadata,changed)
