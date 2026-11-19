"""CT-052 immutable FactoryRelease ledger conformance."""
from dataclasses import FrozenInstanceError, replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.curriculum import AnswerFamily, BINARY, Capability, Grade
from bilqis_mlx.factory.release import compile_factory_release
from bilqis_mlx.factory.tests.support import synthetic_release_inputs
from bilqis_mlx.runtime.akasha_factory_ledger import (
    CheckpointLineageView,
    CurriculumCandidateView,
    FactoryLedgerReadModel,
    FactoryLifecycleReceipt,
    FactoryLifecycleState,
    FactoryReleaseView,
    TopologyKnowledge,
    TopologyView,
    rebuild_factory_ledger,
    require_current_factory_ledger,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2


def _releases():
    course, registry = synthetic_release_inputs()
    grade_a = course.grades[0]
    grade_b_caps = tuple(Capability(
        id=f"B.C{i}", difficulty="fixture-b", source_anchor="repo:fixture/source",
        taught_roots=(f"fixture.b.{i}",), examined_roots=(f"fixture.b.{i}",),
        prerequisites=("A.C0",), composed_of=(),
        answer_families=(AnswerFamily("binary", BINARY),),
        lesson_generator="fixture.generator/v1", independent_oracle="fixture.oracle/v1",
    ) for i in range(6))
    grade_b = Grade(
        "B", grade_b_caps, assessment_sha256="e" * 64,
        exam_item_counts=tuple((cap.id, 4) for cap in grade_b_caps))
    course = replace(course, grades=(grade_a, grade_b))
    first = compile_factory_release(course, registry)
    second = compile_factory_release(replace(course, version="fixture.course/v2"), registry)
    return (
        FactoryReleaseView.from_release("factory:fixture:1", first, "a" * 64),
        FactoryReleaseView.from_release("factory:fixture:2", second, "b" * 64),
    )


def _fixture():
    first, second = _releases()
    candidate = CurriculumCandidateView(
        candidate_sha256="c" * 64,
        semantic_release_sha256=first.semantic_release_sha256,
        artifact_receipt_sha256="d" * 64,
        capability_ids=first.capability_ids,
        dependency_edges=first.dependency_edges,
    )
    exact_checkpoint = CheckpointLineageView(
        run_id="run:current",
        checkpoint_lineage_id="lineage:current",
        generation_manifest_sha256="e" * 64,
        checkpoint_sha256="f" * 64,
        checkpoint_receipt_sha256="0" * 64,
        factory_release_sha256=first.factory_release_sha256,
        semantic_release_sha256=first.semantic_release_sha256,
        topology=TopologyView.exact_v2(ModelTopologySpecV2()),
    )
    historical_checkpoint = CheckpointLineageView(
        run_id="run:historical",
        checkpoint_lineage_id="lineage:historical",
        generation_manifest_sha256="1" * 64,
        checkpoint_sha256="2" * 64,
        checkpoint_receipt_sha256="3" * 64,
        factory_release_sha256=second.factory_release_sha256,
        semantic_release_sha256=second.semantic_release_sha256,
        topology=TopologyView.historical_unknown(
            "compatibility.decode_sealed_factory_release_v1"),
    )
    lifecycle = (
        FactoryLifecycleReceipt(
            1, FactoryLifecycleState.CURRICULUM_CANDIDATE, "1" * 64,
            first.semantic_release_sha256, candidate_sha256=candidate.candidate_sha256),
        FactoryLifecycleReceipt(
            2, FactoryLifecycleState.FACTORY_VALIDATED, "2" * 64,
            first.semantic_release_sha256, candidate_sha256=candidate.candidate_sha256),
        FactoryLifecycleReceipt(
            3, FactoryLifecycleState.QUALIFIED, "3" * 64,
            first.semantic_release_sha256, candidate_sha256=candidate.candidate_sha256),
        FactoryLifecycleReceipt(
            4, FactoryLifecycleState.STAGED, "4" * 64,
            first.semantic_release_sha256, candidate_sha256=candidate.candidate_sha256),
        FactoryLifecycleReceipt(
            5, FactoryLifecycleState.ADMITTED, "5" * 64,
            first.semantic_release_sha256,
            candidate_sha256=candidate.candidate_sha256,
            factory_release_sha256=first.factory_release_sha256,
            transition_sha256="a" * 64),
        FactoryLifecycleReceipt(
            6, FactoryLifecycleState.PROMOTED, "6" * 64,
            first.semantic_release_sha256,
            factory_release_sha256=first.factory_release_sha256,
            capability_id="B.C0", checkpoint_sha256=exact_checkpoint.checkpoint_sha256),
        FactoryLifecycleReceipt(
            7, FactoryLifecycleState.DEBT, "7" * 64,
            first.semantic_release_sha256,
            factory_release_sha256=first.factory_release_sha256,
            capability_id="B.C0"),
        FactoryLifecycleReceipt(
            8, FactoryLifecycleState.SUPERSEDED, "8" * 64,
            first.semantic_release_sha256,
            factory_release_sha256=first.factory_release_sha256,
            successor_factory_release_sha256=second.factory_release_sha256,
            transition_sha256="b" * 64),
    )
    return (first, second), (candidate,), lifecycle, (exact_checkpoint, historical_checkpoint)


class AkashaFactoryLedgerTests(unittest.TestCase):
    def test_query_model_exposes_lineage_dependencies_receipts_and_checkpoint_topology(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        projection = rebuild_factory_ledger(releases, candidates, lifecycle, checkpoints)
        read = FactoryLedgerReadModel(projection)
        first, second = releases

        self.assertEqual(read.release(first.factory_release_sha256), first)
        self.assertIn(("B.C0", "A.C0"), read.dependencies(first.factory_release_sha256))
        self.assertEqual(
            tuple(item.state for item in read.lifecycle_for(first.factory_release_sha256)),
            (FactoryLifecycleState.ADMITTED, FactoryLifecycleState.PROMOTED,
             FactoryLifecycleState.DEBT, FactoryLifecycleState.SUPERSEDED))
        self.assertEqual(
            read.lifecycle_for(second.factory_release_sha256)[0].state,
            FactoryLifecycleState.SUPERSEDED)
        current = read.checkpoints_for(first.factory_release_sha256)[0]
        self.assertIs(current.topology.knowledge, TopologyKnowledge.EXACT)
        self.assertEqual(current.topology.layers, 12)
        self.assertEqual(current.topology.query_heads, 16)
        self.assertEqual(current.topology.kv_heads, 8)
        self.assertEqual(current.topology.model_dimension, 768)
        self.assertEqual(current.topology.feed_forward_dimension, 3072)
        self.assertEqual(current.topology.context_length, 1024)
        refs = read.receipt_refs(first.factory_release_sha256)
        self.assertIn(first.artifact_receipt_sha256, refs)
        self.assertIn(current.checkpoint_receipt_sha256, refs)
        self.assertFalse(hasattr(read, "append"))
        self.assertFalse(hasattr(read, "mutate"))

    def test_rebuild_retry_and_projection_deletion_reproduce_identical_state(self):
        args = _fixture()
        first = rebuild_factory_ledger(*args)
        retry = rebuild_factory_ledger(*args)
        self.assertEqual(first, retry)
        identity = first.identity
        del first
        rebuilt = rebuild_factory_ledger(*args)
        self.assertEqual(rebuilt.identity, identity)
        self.assertEqual(rebuilt, retry)

    def test_release_projection_is_frozen_and_manifest_tampering_is_rejected(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        release = releases[0]
        with self.assertRaises(FrozenInstanceError):
            release.course_sha256 = "0" * 64
        with self.assertRaises(BilqisError):
            replace(release, manifest_json=release.manifest_json.replace("A.C0", "A.CX", 1))
        projection = rebuild_factory_ledger(releases, candidates, lifecycle, checkpoints)
        self.assertEqual(
            FactoryLedgerReadModel(projection).release(release.factory_release_sha256).manifest_json,
            release.manifest_json)

    def test_stale_or_mismatched_semantic_and_factory_evidence_fails_closed(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        stale = replace(lifecycle[4], semantic_release_sha256="f" * 64)
        with self.assertRaises(BilqisError):
            rebuild_factory_ledger(releases, candidates, lifecycle[:4] + (stale,) + lifecycle[5:], checkpoints)
        with self.assertRaises(BilqisError):
            rebuild_factory_ledger(releases[:1], candidates, lifecycle, checkpoints[:1])
        with self.assertRaises(BilqisError):
            rebuild_factory_ledger(releases, (), lifecycle, checkpoints)

    def test_lifecycle_ordinals_are_unique_append_only_positions(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        duplicate_position = replace(
            lifecycle[-1], receipt_sha256="9" * 64, ordinal=lifecycle[-2].ordinal)
        with self.assertRaises(BilqisError):
            rebuild_factory_ledger(
                releases, candidates, lifecycle[:-1] + (duplicate_position,), checkpoints)

    def test_projection_currentness_detects_new_canonical_evidence(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        projection = rebuild_factory_ledger(releases, candidates, lifecycle, checkpoints)
        require_current_factory_ledger(
            projection, releases, candidates, lifecycle, checkpoints)
        added = FactoryLifecycleReceipt(
            9, FactoryLifecycleState.DEBT, "9" * 64,
            releases[1].semantic_release_sha256,
            factory_release_sha256=releases[1].factory_release_sha256,
            capability_id="A.C2")
        with self.assertRaises(BilqisError):
            require_current_factory_ledger(
                projection, releases, candidates, lifecycle + (added,), checkpoints)

    def test_historical_checkpoint_does_not_infer_current_topology_defaults(self):
        releases, candidates, lifecycle, checkpoints = _fixture()
        projection = rebuild_factory_ledger(releases, candidates, lifecycle, checkpoints)
        historical = FactoryLedgerReadModel(projection).checkpoints_for(
            releases[1].factory_release_sha256)[0]
        self.assertIs(
            historical.topology.knowledge,
            TopologyKnowledge.HISTORICAL_COMPATIBILITY_REQUIRED)
        self.assertIsNone(historical.topology.topology_digest)
        self.assertIsNone(historical.topology.layers)
        self.assertEqual(
            historical.topology.compatibility_ref,
            "compatibility.decode_sealed_factory_release_v1")

    def test_wrong_domain_owner_cannot_rebuild_projection(self):
        with self.assertRaises(BilqisError):
            rebuild_factory_ledger(*_fixture(), authority_owner="mission-control")


if __name__ == "__main__":
    unittest.main()
