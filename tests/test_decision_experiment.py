import unittest
import torch
from bilqis_alpha.decision_experiment import eligible, pack, exposure_identity, summarize, check_frozen


class ExperimentTest(unittest.TestCase):
    def test_prerequisite_eligibility_and_exact_multiset(self):
        blocks=[{'block_id':'B00','prerequisites':[],'batches':[[0,1]]},
                {'block_id':'B01','prerequisites':[0],'batches':[[1,2]]}]
        self.assertEqual(eligible(blocks,[]),['B00'])
        self.assertEqual(eligible(blocks,['B00']),['B01'])
        self.assertEqual(exposure_identity(blocks,['B00','B01']),exposure_identity(blocks,['B01','B00']))
    def test_pack_never_passes_gold_ids_to_forward(self):
        rows=[{'state_tokens':[1,2],'candidate_tokens':[[1],[2,3]],'candidate_ids':['a','b'],'gold_id':'b'},
              {'state_tokens':[2],'candidate_tokens':[[3]],'candidate_ids':['c'],'gold_id':'c'}]
        tensors=pack(rows)
        self.assertEqual(len(tensors),5)
        self.assertEqual(tensors[-1].tolist(),[[True,True],[True,False]])
        self.assertTrue(all(isinstance(x,torch.Tensor) for x in tensors))
    def test_correct_terminal_is_not_complete_path(self):
        row={'family':'orientation','path_correct':False,'final_correct':True,'truth_correct':True,
             'evidence_preserved':True,'steps':[{'kind':'orient','correct':False,'valid':True}],
             'expected_status':'resolved','expected_outcome':'TRUE','outcome':'TRUE','status':'resolved'}
        score=summarize([row])
        self.assertEqual(score['path_correct'],0)
        self.assertEqual(score['final_correct'],1)
        self.assertEqual(score['orientation']['correct'],0)
    def test_frozen_manifest_detects_tamper(self):
        from bilqis_alpha.semantics import digest
        data={'a':1}; manifest={'dataset_sha256':digest(data)}
        check_frozen(data,manifest)
        with self.assertRaises(ValueError): check_frozen({'a':2},manifest)

    def test_valid_replacement_checkpoint_is_not_prepared_initial_state(self):
        from dataclasses import asdict
        from bilqis_ref.model import state_hash
        from bilqis_alpha.decision_student import initialize
        from bilqis_alpha.decision_experiment import validate_initial, VERSION
        model,init=initialize()
        metadata={'epoch':VERSION,'dataset_sha256':'frozen-data'}
        manifest={'initial_state_sha256':state_hash(model),'initializer':init,'config':asdict(model.config),'dataset_sha256':'frozen-data'}
        payload={'initializer':init,'metadata':metadata}
        validate_initial(model,payload,manifest)
        replacement,_=initialize(seed=203)
        with self.assertRaises(ValueError): validate_initial(replacement,payload,manifest)

    def test_replay_rejects_truncated_and_changed_semantic_steps(self):
        import copy
        from bilqis_alpha.decision_experiment import compare_neural_replay
        step={'state_sha256':'state','panel':{'panel_id':'panel'},
              'neural':{'choice':'a','candidate_ids':['a','b'],'logits':[1.,0.], 'probabilities':[.7,.3]}}
        row={'path_correct':True,'status':'resolved','outcome':'TRUE','steps':[step]}
        compare_neural_replay(row,copy.deepcopy(row))
        truncated=copy.deepcopy(row); truncated['steps']=[]
        with self.assertRaisesRegex(ValueError,'STEP_COUNT'): compare_neural_replay(row,truncated)
        for field in ('choice','candidate_ids'):
            tampered=copy.deepcopy(row); tampered['steps'][0]['neural'][field]='changed'
            with self.assertRaisesRegex(ValueError,'IDENTITY'): compare_neural_replay(row,tampered)
        tampered=copy.deepcopy(row); tampered['steps'][0]['state_sha256']='changed'
        with self.assertRaisesRegex(ValueError,'IDENTITY'): compare_neural_replay(row,tampered)

    def test_qualified_eg2_command_and_identity_are_bound(self):
        from bilqis_alpha.decision_experiment import eg2_command, validate_eg2_replay
        receipt={'model':{'path':'/model','file_sha256':{'weights':'hash'},'backend':'native MLX'},
                 'runtime':{'executable':'/qualified/env/bin/python'}}
        command=eg2_command(receipt,'input.json','output.json')
        self.assertEqual(command[0],'/qualified/env/bin/python')
        self.assertEqual(command[-1],'/model')
        validate_eg2_replay(receipt,receipt)
        for section,key in (('runtime','executable'),('model','path'),('model','file_sha256')):
            import copy
            changed=copy.deepcopy(receipt); changed[section][key]='replacement'
            with self.assertRaisesRegex(ValueError,'EG2_RUNTIME_DRIFT'): validate_eg2_replay(changed,receipt)

    def test_checkpoint_file_binding_precedes_replay(self):
        import tempfile
        from pathlib import Path
        from bilqis_alpha.decision_experiment import verified_arm, file_hash
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory); path=run/'fixed.pt'; path.write_bytes(b'original')
            paired={'arms':{'fixed':{'checkpoint_sha256':file_hash(path)}}}
            path.write_bytes(b'replacement')
            with self.assertRaisesRegex(ValueError,'CHECKPOINT_TAMPER'): verified_arm(run,paired,'fixed',{})

    def test_paired_checkpoint_epoch_and_dataset_metadata_must_match(self):
        import tempfile
        from pathlib import Path
        from dataclasses import asdict
        from bilqis_ref.model import state_hash
        from bilqis_alpha.decision_student import initialize, save_checkpoint
        from bilqis_alpha.decision_experiment import verified_arm, file_hash, VERSION
        model,init=initialize()
        manifest={'dataset_sha256':'frozen','config':asdict(model.config),'initializer':init}
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)
            metadata={'epoch':VERSION,'arm':'fixed','order':['B00'],'dataset_sha256':'frozen'}
            for field in ('epoch','dataset_sha256'):
                changed=dict(metadata); changed[field]='other-epoch'
                save_checkpoint(run/'fixed.pt',model,init,changed)
                paired={'version':VERSION,'dataset_sha256':'frozen','arms':{'fixed':{
                    'checkpoint_sha256':file_hash(run/'fixed.pt'),'final_state_sha256':state_hash(model),'order':['B00']}}}
                with self.assertRaisesRegex(ValueError,'PAIRED_CHECKPOINT_BINDING'):
                    verified_arm(run,paired,'fixed',manifest)

    def test_evaluation_inputs_reject_post_training_retrieval_mutation(self):
        import tempfile
        from pathlib import Path
        from bilqis_alpha.decision_experiment import qualified_inputs, write, file_hash, VERSION
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory); manifest={'dataset_sha256':'frozen'}
            write(run/'retrieval.json',{'model':'actual'})
            write(run/'qualification.json',{'version':VERSION,'dataset_sha256':'frozen',
                'disposition':'ENGINES_VERIFIED','retrieval_sha256':file_hash(run/'retrieval.json')})
            (run/'retrieval.json').write_text('{"model":"replacement"}')
            with self.assertRaisesRegex(ValueError,'RETRIEVAL_TAMPER'): qualified_inputs(run,manifest)
