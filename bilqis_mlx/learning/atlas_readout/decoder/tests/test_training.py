"""A real backward pass through source-active feedback and typed heads."""
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
import mlx.core as mx
import bilqis_mlx.learning.atlas_readout.decoder.prediction as prediction
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_readout import (
    predict_typed, answer_loss, AnswerPlan, DecisionOutput, ControlAction, DecisionKind,
    DecisionSpec,
)
from bilqis_mlx.learning.atlas_readout.decoder.tests.helpers import case
from bilqis_mlx.learning.atlas_readout.decoder.tests.test_prediction import role_plan
from bilqis_mlx.learning.atlas_readout.decoder.prediction import (
    attest_issued_output, attest_issued_outputs, issued_output,
)
from bilqis_mlx.learning.atlas_readout.decoder.replay import predict_typed_replay
from bilqis_mlx.runtime.autodiff_trace import defer_host_tensor_validation


class DecoderTrainingTests(unittest.TestCase):
    def test_trace_replay_pending_receipt_is_not_evidence_authority(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        baseline=predict_typed(memory,context,plan,semantics,params)
        with defer_host_tensor_validation():
            replay=predict_typed_replay(
                memory,context,plan,semantics,params,baseline)
            self.assertTrue(issued_output(replay))
            self.assertFalse(attest_issued_output(replay))
        self.assertFalse(issued_output(replay))
        self.assertTrue(attest_issued_output(replay))
        self.assertTrue(issued_output(replay))

    def test_route_only_deferred_issuance_reuses_frozen_meaning_without_deepcopy(self):
        _memory,_context,base_plan,_semantics,_params=case()
        decision=DecisionSpec(
            'op',None,0,DecisionKind.OPERATOR,('op.a','op.b'))
        plan=AnswerPlan(
            'answer.cognitive-route/v1',base_plan.input_prefix_end,(decision,),None,
            base_plan.snapshot,base_plan.source_span,base_plan.generation_binding)
        output=prediction.ModelOutput(
            plan,(prediction.DecisionLogits(
                'op',DecisionKind.OPERATOR,('op.a','op.b'),
                mx.array((0.25,0.75),dtype=mx.float32)),),
            (DecisionOutput('op','op.b'),),prediction.DecodeStatus.COMPLETE,
            prediction.ExecutionMode.INFERENCE,None,False)
        with patch.object(prediction,'deepcopy',wraps=prediction.deepcopy) as copied:
            issued=prediction._issue_output(
                output,fingerprint=False,freeze_meaning=False)
        self.assertIs(issued,output)
        self.assertEqual(copied.call_count,0)
        self.assertFalse(issued_output(output))
        self.assertTrue(attest_issued_output(output))
        self.assertTrue(issued_output(output))

    def test_trace_replay_batch_attestation_fingerprints_all_outputs_once(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        baseline=predict_typed(memory,context,plan,semantics,params)
        with defer_host_tensor_validation():
            outputs=tuple(predict_typed_replay(
                memory,context,plan,semantics,params,baseline) for _ in range(2))
        with patch.object(
                prediction,'_batched_logit_fingerprints',
                wraps=prediction._batched_logit_fingerprints) as fingerprints:
            self.assertTrue(attest_issued_outputs(outputs))
        self.assertEqual(fingerprints.call_count,1)
        self.assertTrue(all(issued_output(output) for output in outputs))

    def test_trace_replay_nonfinite_logits_fail_post_trace_attestation(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        baseline=predict_typed(memory,context,plan,semantics,params)
        decision_logits=prediction.decision_logits

        def nonfinite_logits(*args,**kwargs):
            candidates,logits=decision_logits(*args,**kwargs)
            return candidates,mx.full(logits.shape,float('nan'),dtype=mx.float32)

        with defer_host_tensor_validation():
            with patch.object(prediction,'decision_logits',side_effect=nonfinite_logits):
                replay=predict_typed_replay(
                    memory,context,plan,semantics,params,baseline)
                self.assertTrue(issued_output(replay))
        with self.assertRaises(BilqisError):
            attest_issued_output(replay)

    def test_trace_replay_preserves_inference_conditioned_gradient(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        baseline=predict_typed(memory,context,plan,semantics,params)
        value_spec=next(item for item in plan.decisions if item.decision_id=='value')
        role_spec=next(item for item in plan.decisions if item.decision_id=='role')
        predicted=next(
            item.value for item in baseline.committed
            if item.decision_id=='value')
        opposite=next(value for value in value_spec.legal_values if value!=predicted)
        targets=(
            DecisionOutput('control',ControlAction.EMIT_VALUE),
            DecisionOutput('value',opposite),
            DecisionOutput('role',role_spec.legal_values[0]),
            DecisionOutput('end',ControlAction.END_FRAME),
        )
        mask={target.decision_id:True for target in targets}

        for parameter in ('readout.feedback','readout.role_query'):
            with self.subTest(parameter=parameter):
                def inference_objective(value):
                    current={**params,parameter:value}
                    output=predict_typed(memory,context,plan,semantics,current)
                    return answer_loss(output,targets,mask).total

                def replay_objective(value):
                    current={**params,parameter:value}
                    with defer_host_tensor_validation():
                        output=predict_typed_replay(
                            memory,context,plan,semantics,current,baseline)
                        return answer_loss(output,targets,mask).total

                old_loss,old_gradient=mx.value_and_grad(inference_objective)(
                    params[parameter])
                new_loss,new_gradient=mx.value_and_grad(replay_objective)(
                    params[parameter])
                mx.eval(old_loss,old_gradient,new_loss,new_gradient)
                np.testing.assert_allclose(
                    np.asarray(new_loss),np.asarray(old_loss),
                    rtol=1e-6,atol=1e-7)
                np.testing.assert_allclose(
                    np.asarray(new_gradient),np.asarray(old_gradient),
                    rtol=1e-5,atol=1e-6)

    def test_trace_replay_never_argmaxes_or_fingerprints(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        baseline=predict_typed(memory,context,plan,semantics,params)
        with defer_host_tensor_validation():
            with (patch(
                    'bilqis_mlx.learning.atlas_readout.decoder.prediction._logit_fingerprint',
                    side_effect=AssertionError('fingerprint entered replay trace')),
                  patch(
                    'bilqis_mlx.learning.atlas_readout.decoder.prediction.mx.argmax',
                    side_effect=AssertionError('argmax entered replay trace'))):
                output=predict_typed_replay(
                    memory,context,plan,semantics,params,baseline)
        self.assertEqual(output.committed,baseline.committed)
        self.assertEqual(output.status,baseline.status)

    def test_trace_sparse_supervision_advances_singleton_ancestors_without_argmax(self):
        memory,context,plan,semantics,params=case()
        target=DecisionOutput('value',plan.decisions[1].legal_values[0])
        with defer_host_tensor_validation():
            with patch(
                    'bilqis_mlx.learning.atlas_readout.decoder.prediction.mx.argmax',
                    side_effect=AssertionError('singleton ancestor used argmax')):
                output=predict_typed(
                    memory,context,plan,semantics,params,(target,),trace=True)
        self.assertFalse(output.fallback_requested)
        self.assertEqual(
            tuple(item.decision_id for item in output.committed),
            ('control','value','end'))
        self.assertEqual(next(
            item.value for item in output.committed if item.decision_id=='value'),
            target.value)

    def test_trace_unlabelled_ambiguous_ancestor_never_reaches_descendant_target(self):
        memory,context,plan,semantics,params=case()
        ambiguous=replace(
            plan.decisions[0],
            legal_values=(ControlAction.EMIT_VALUE, ControlAction.EMIT_UNKNOWN))
        changed=replace(plan,decisions=(ambiguous,*plan.decisions[1:]))
        target=DecisionOutput('value',changed.decisions[1].legal_values[0])
        with defer_host_tensor_validation():
            with patch(
                    'bilqis_mlx.learning.atlas_readout.decoder.prediction.mx.argmax',
                    side_effect=AssertionError('ambiguous ancestor used argmax')):
                output=predict_typed(
                    memory,context,changed,semantics,params,(target,),trace=True)
        self.assertTrue(output.fallback_requested)
        self.assertNotIn('value', {item.decision_id for item in output.decisions})

    def test_trace_training_avoids_logit_fingerprints_and_argmax_readback(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        targets=tuple(DecisionOutput(item.decision_id,item.legal_values[0])
                      for item in plan.decisions)
        mask={target.decision_id:True for target in targets}

        def objective(hidden):
            with defer_host_tensor_validation():
                with (patch(
                        'bilqis_mlx.learning.atlas_readout.decoder.prediction._logit_fingerprint',
                        side_effect=AssertionError('logit fingerprint entered trace')),
                      patch('bilqis_mlx.learning.atlas_readout.decoder.prediction.mx.argmax',
                            side_effect=AssertionError('argmax readback entered trace'))):
                    output=predict_typed(
                        replace(memory,hidden=hidden),context,plan,semantics,params,
                        targets,trace=True)
                    return answer_loss(output,targets,mask).total

        gradient=mx.grad(objective)(memory.hidden)
        self.assertEqual(gradient.shape,memory.hidden.shape)
        self.assertTrue(bool(mx.all(mx.isfinite(gradient))))

    def test_executed_heads_feedback_identity_and_hidden_receive_gradients(self):
        memory,context,plan,semantics,params=case();plan=role_plan(plan)
        plan=replace(plan,decisions=(replace(plan.decisions[0],
            legal_values=(ControlAction.EMIT_VALUE,ControlAction.EMIT_UNKNOWN)),*plan.decisions[1:]))
        targets=(DecisionOutput('control',ControlAction.EMIT_VALUE),
                 DecisionOutput('value',plan.decisions[1].legal_values[0]),
                 DecisionOutput('role',plan.decisions[2].legal_values[0]),
                 DecisionOutput('end',ControlAction.END_FRAME))
        def objective(tree):
            parameters,hidden=tree
            active=replace(semantics,banks=(replace(semantics.banks[0],
                              weights=parameters['identity.bank.0']),))
            output=predict_typed(replace(memory,hidden=hidden),context,plan,active,parameters,targets)
            return answer_loss(output,targets,{t.decision_id:True for t in targets}).total
        gradients,hidden_gradient=mx.grad(objective)((params,memory.hidden))
        for name in ('identity.bank.0','features.role','readout.control','readout.control_bias',
                     'readout.role_query','readout.feedback','readout.query','readout.key',
                     'readout.value','readout.output','readout.state_norm','readout.output_norm'):
            with self.subTest(parameter=name):
                self.assertTrue(bool(mx.all(mx.isfinite(gradients[name]))))
                self.assertGreater(float(mx.sum(mx.abs(gradients[name]))),0)
        self.assertGreater(float(mx.sum(mx.abs(hidden_gradient[:5]))),0)
        np.testing.assert_array_equal(np.asarray(hidden_gradient[5:]),0)
        self.assertEqual(float(mx.sum(mx.abs(gradients['identity.bank.0'][0]))),0)
