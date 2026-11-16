"""Signed row-specific labels preserve other heads and never enter inference."""
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.salience_auxiliaries import RowSalienceBinding, attach_salience_labels
from bilqis_mlx.runtime.tests.test_atlas_training_adapter import AtlasTrainingAdapterTest
from bilqis_mlx.runtime.atlas_training_adapter import execute_with_backend
from bilqis_mlx.runtime.atlas_training_contracts import _reissue_training_batch
from bilqis_mlx.learning.atlas_salience import derive_salience, verify_salience_inputs
from bilqis_mlx.learning.salience_contracts import AuthoritySnapshot, Metric
from bilqis_mlx.learning.tests.test_atlas_salience import _CONTEXT, _REGISTRY, _policy, _fact, _signed
from bilqis_mlx.runtime.atlas_revalidation import SourceAuthorityRegistry, SourceAuthorityScope
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind

_REGISTRY = SourceAuthorityRegistry((replace(_REGISTRY.keys[0], allowed_scopes=tuple(sorted(
    (*_REGISTRY.keys[0].allowed_scopes, SourceAuthorityScope(DependencyKind.ARTIFACT, "salience-row:")),
    key=lambda scope: (scope.kind.value, scope.key_prefix)))),))


class SalienceAuxiliaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = AtlasTrainingAdapterTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.model_generation = "d" * 64
        rows = self.fixture.context.draw_rows(seed=17, capability='Z.C0', each=2)
        self.batch = self.fixture.compile(rows)
        source_family_id = self.batch.rows[0].provenance.source_family_id
        context = replace(_CONTEXT, capability_id='Z.C0',
                          source_family_id=source_family_id,
                          semantic_release=self.batch.release_sha256,
                          generation_digest=self.batch.generation_binding)
        self.snapshot = AuthoritySnapshot((context,), 100, _REGISTRY)
        policy = _signed(replace(_policy(), semantic_release=context.semantic_release,
                                 source_family_ids=(source_family_id,)))
        self.evidence = derive_salience(verify_salience_inputs(
            (_fact(Metric.DECLARED_IMPACT, 2, policy, context=context),
             _fact(Metric.BLOCKED_COUNT, 0, policy, context=context)), policy, self.snapshot, context))

    def binding(self, row=None, evidence=None):
        return _signed(RowSalienceBinding.for_row(
            self.batch, row or self.batch.rows[0], evidence or self.evidence,
            source_owner='fixture:salience-owner', signature_hex='0' * 128))

    def test_mask_missing_and_preserve_existing_heads_and_other_rows(self):
        first, second = self.batch.rows
        first = replace(first, auxiliaries=(('role', 'subject', 'SOURCE', 'fixture-role-receipt'),))
        second = replace(second, auxiliaries=(('epistemic_state', 1, 'SOURCE', 'fixture-epistemic-receipt'),))
        batch = _reissue_training_batch(self.batch, rows=(first, second))
        def verify_existing(row_id, name, value, regime, receipt):
            return (row_id, name, value, regime, receipt) in (
                (first.provenance.row_id, *first.auxiliaries[0]),
                (second.provenance.row_id, *second.auxiliaries[0]))
        labelled = attach_salience_labels(batch, self.fixture.context,
            ((self.binding(), self.evidence),), self.snapshot, verify_existing=verify_existing)
        labels = {row[0]: row[1:] for row in labelled.rows[0].auxiliaries}
        self.assertEqual(labels['impact'][:2], (2, 'SOURCE'))
        self.assertEqual(labels['exigency'][:2], (1, 'OUTCOME'))
        self.assertNotIn('novelty', labels)
        self.assertEqual(labels['role'], ('subject', 'SOURCE', 'fixture-role-receipt'))
        self.assertEqual(labelled.rows[1], second)
        self.assertEqual(labelled.rows[0].target, first.target)
        observed = execute_with_backend(labelled, self.fixture.context, object(),
            generation_binding=self.batch.generation_binding, training=False,
            model_backend=lambda topology: 'fixture-B11', invoke=lambda backend, inputs, targets: (inputs, targets))
        self.assertEqual(observed, (tuple(row.model_input for row in self.batch.rows), None))

    def test_cross_row_generation_and_signature_substitution_fail_closed(self):
        binding = self.binding()
        for bad in (replace(binding, row_id=self.batch.rows[1].provenance.row_id),
                    _signed(replace(binding, row_id=self.batch.rows[1].provenance.row_id)),
                    _signed(replace(binding, generation_binding='8' * 64))):
            with self.assertRaises(BilqisError):
                attach_salience_labels(self.batch, self.fixture.context, ((bad, self.evidence),),
                                       self.snapshot, verify_existing=lambda *args: False)

    def test_explicit_unknown_is_label_zero_and_unverified_old_labels_fail(self):
        basis = self.evidence.basis
        evidence = derive_salience(verify_salience_inputs(
            (*basis.facts, _fact(Metric.NOVELTY_UNKNOWN, 0, basis.policy, context=basis.context)),
            basis.policy, self.snapshot, basis.context))
        labelled = attach_salience_labels(self.batch, self.fixture.context,
            ((self.binding(evidence=evidence), evidence),), self.snapshot, verify_existing=lambda *args: False)
        self.assertEqual(dict((row[0], row[1]) for row in labelled.rows[0].auxiliaries)['novelty'], 0)
        with self.assertRaises(BilqisError):
            attach_salience_labels(labelled, self.fixture.context, (), self.snapshot,
                                   verify_existing=lambda *args: False)
