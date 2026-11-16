"""Salience evidence preserves exact C02 rights and context dependencies."""
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
from bilqis_mlx.runtime.tests.model.test_salience_auxiliaries import SalienceAuxiliaryTests
from bilqis_mlx.learning.tests.test_atlas_salience import _signed
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef


class SalienceEvidenceOwnerTests(unittest.TestCase):
    def setUp(self):
        self.fixture = SalienceAuxiliaryTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        row = self.fixture.batch.rows[0]
        self.records = ((self.fixture.binding(), self.fixture.evidence),)
        self.dependencies = ((row.provenance.row_id, row.provenance.immediate_dependencies),)

    def owner(self):
        return SalienceEvidenceArtifactOwner(self.records, self.dependencies)

    def test_closed_graph_and_exact_source_context_dependencies(self):
        owner = self.owner()
        node = owner.require()
        self.assertEqual(node.kind.value, 'SALIENCE_EVIDENCE')
        self.assertEqual((node.impact, node.exigency), (2, 3))
        ids = {item.artifact_id for item in owner.index.nodes}
        for item in owner.index.nodes:
            for dependency in item.immediate_dependencies:
                if dependency.kind is DependencyKind.ARTIFACT:
                    self.assertIn(dependency.key, ids)
            self.assertTrue(set(self.dependencies[0][1]) <= set(item.immediate_dependencies))
        self.assertEqual(node.content_digest, self.owner().require().content_digest)

    def test_source_rights_revocation_holds_prepared_labels(self):
        owner = self.owner()
        right = next(ref for ref in self.dependencies[0][1] if ref.kind is DependencyKind.RIGHTS)
        owner.require()
        owner.apply_correction(_event(right), AUTHORITY)
        with self.assertRaises(BilqisError) as caught:
            owner.require()
        self.assertEqual(caught.exception.context['reason'], 'BAMF_C09_ARTIFACT_HELD')

    def test_divergent_fact_identity_fails_before_graph_publication(self):
        evidence = self.fixture.evidence
        fact = _signed(replace(evidence.basis.facts[0], source_receipt_sha256='8' * 64))
        changed = replace(evidence, basis=replace(evidence.basis, facts=(fact, *evidence.basis.facts[1:])))
        with self.assertRaises(BilqisError):
            SalienceEvidenceArtifactOwner((*self.records, (self.fixture.binding(evidence=changed), changed)), self.dependencies)

    def test_context_dependency_comes_from_exact_c02_prefix(self):
        context = DependencyRef(DependencyKind.TIME, 'time:asof:context:' + '7' * 64)
        row_id, dependencies = self.dependencies[0]
        owner = SalienceEvidenceArtifactOwner(self.records, ((row_id, tuple(sorted((*dependencies, context)))),))
        self.assertEqual(len(owner.index.direct_dependents(context)), len(owner.index.nodes))
