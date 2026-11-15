"""A real backward pass through source-active feedback and typed heads."""
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
import mlx.core as mx
from bilqis_mlx.learning.atlas_readout import (
    predict_typed, answer_loss, DecisionOutput, ControlAction, DecisionKind,
)
from bilqis_mlx.learning.atlas_readout.decoder.tests.helpers import case
from bilqis_mlx.learning.atlas_readout.decoder.tests.test_prediction import role_plan


class DecoderTrainingTests(unittest.TestCase):
    def test_trace_sparse_supervision_advances_singleton_ancestors_without_argmax(self):
        memory,context,plan,semantics,params=case()
        target=DecisionOutput('value',plan.decisions[1].legal_values[0])
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
