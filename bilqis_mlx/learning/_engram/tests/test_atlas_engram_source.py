"""B07.1 source-qualified motif preparation tests."""
import inspect
import os
from pathlib import Path
import unittest
from dataclasses import replace
from unittest import TestCase

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_engram import MotifBudget
from bilqis_mlx.learning.atlas_engram_source import (
    ApprovedMotifCandidate, prepare_source_qualified_motifs,
)
from bilqis_mlx.learning._engram.atlas_engram_source_context import (
    qualify_prepared_source_motif_context, qualify_source_motif_context,
)
from bilqis_mlx.b11_observation import source_replay_observation
from bilqis_mlx.learning.atlas_candidate import CandidateState, begin_candidate
from bilqis_mlx.learning.atlas_plasticity import IdentityRowAge, PlasticityPolicy
from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextPolicy, SourceFrontier, TaskScope,
)

REAL_BUNDLE = "5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7"
REAL_RELEASE = "58e0c281b5da18b9b7e6c803709b29eeeb0a88f16b06f48de692808e2fb88306"
REAL_SOURCE_BUNDLE = "f1c89c1d1bcd72695c81f8e777d0fbbdf446e92cb27132bebf1cd6873ec689ec"


@unittest.skipUnless(
    os.environ.get("BILQIS_ATLAS_REAL_ARTIFACT"),
    "real repo-pinned A01 artifact supplied at source turn-in",
)
class SourceQualifiedMotifTests(TestCase):
    def _case(self, grade="A"):
        from bilqis_mlx.grade_a_probe import read_sources
        from bilqis_mlx.live_grade_c import draw as draw_numeric_rows, registry_graph
        from bilqis_mlx.source_adapters.school import (
            A_ORACLE, B_ORACLE, C_ORACLE, live_source_registry,
        )

        selection = AtlasArtifactSelection(
            os.environ["BILQIS_ATLAS_REAL_ARTIFACT"],
            REAL_BUNDLE, REAL_RELEASE, REAL_SOURCE_BUNDLE,
        )
        source_root = Path(__file__).resolve().parents[4] / "vendor/legacy-v16"
        micro_graph = read_sources(source_root)[2]
        registry = live_source_registry()
        if grade == "A":
            graph = micro_graph
            adapter = registry.require(
                "bilqis_mlx.grade_a_probe.make_record", A_ORACLE)
            seed, each, profile = 31, 2, None
            row = adapter.draw(
                source_root=source_root, graph=graph, course=None,
                capability="A.IDENTITY", seed=seed, each=each)[0]
        elif grade == "B":
            graph = micro_graph
            adapter = registry.require(
                "bilqis_mlx.live_grade_b.draw_connectives", B_ORACLE)
            seed, each, profile = 31, 4, None
            row = adapter.draw(
                source_root=source_root, graph=graph, course=None,
                capability="B.AND", seed=seed, each=each)[0]
        elif grade == "C":
            graph = registry_graph()
            adapter = registry.require(
                "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
            seed, each = 19, 12
            profile = {"numbers": ("0", "1", "2", "3")}
            row = next(item for item in draw_numeric_rows(
                graph, seed=seed, maximum=3) if item["capability"] == "C.ADD")
        else:
            raise AssertionError(grade)
        task = TaskScope(
            "synthetic:principal", "synthetic:tenant", "TRAINING",
            REAL_RELEASE, "synthetic:region", "synthetic:public", 3, 5, 30)
        policy = ContextPolicy(
            "synthetic:policy", 1, 1, ("TRAINING",), (PUBLIC_FORMAL,),
            ("synthetic:region",), ("synthetic:public",), (PUBLIC_FORMAL,),
            ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
            tuple((PUBLIC_FORMAL,) * count for count in range(3, 25)))
        return selection, source_root, graph, adapter, row, task, policy, seed, each, profile

    def _prepare(self, *, grade="A", frontier=None, graph=None, selection=None,
                 row=None, budget=None):
        (actual_selection, source_root, actual_graph, adapter, actual_row,
         task, policy, seed, each, profile) = self._case(grade)
        return prepare_source_qualified_motifs(
            adapter, actual_row if row is None else row,
            actual_selection if selection is None else selection,
            source_root=source_root, graph=actual_graph if graph is None else graph,
            task_scope=task,
            source_frontier=SourceFrontier(1, 1, ()) if frontier is None else frontier,
            policy=policy, source_seed=seed, source_each=each,
            source_profile_parameters=profile,
            budget=MotifBudget(64) if budget is None else budget,
        )

    def test_production_api_has_no_caller_schema_snapshot_or_grant_surface(self):
        import bilqis_mlx.learning.atlas_engram_source as source_module

        parameters = inspect.signature(prepare_source_qualified_motifs).parameters
        for forbidden in (
            "envelopes", "schemas", "snapshot", "source_authorities", "grants",
            "prior_pending", "prior_observed_uses", "parent", "retained_state",
        ):
            self.assertNotIn(forbidden, parameters)
        self.assertFalse(hasattr(source_module, "_probe_approved_motifs"))
        self.assertFalse(hasattr(source_module, "_issue_approved_motif_candidate"))
        self.assertFalse(hasattr(source_module, "_APPROVED_ISSUER"))
        self.assertNotIn("frames", inspect.signature(begin_candidate).parameters)

    def test_approved_candidate_requires_exact_owner_issued_candidate_identity(self):
        approved, _frontier = self._prepare()
        original = approved.candidate
        same_value_copy = replace(original)
        self.assertEqual(same_value_copy.digest, original.digest)
        self.assertIsNot(same_value_copy, original)
        object.__setattr__(approved, "candidate", same_value_copy)
        with self.assertRaises(BilqisError):
            approved.__post_init__()
        object.__setattr__(approved, "candidate", original)
        approved.__post_init__()

    def test_source_candidate_cannot_launder_history_into_retention(self):
        name = "identity.bank.0"
        values = mx.array([[.5, -.25]], dtype=mx.float32)
        optimizer = AdamWStateTree(
            {name: values}, {name: mx.zeros_like(values)},
            {name: mx.zeros_like(values)},
            {name: mx.array([0], dtype=mx.uint64)},
        )
        approved, _frontier = self._prepare()
        with self.assertRaises(BilqisError):
            CandidateState(
                optimizer, PlasticityPolicy("ADAPTIVE", 0, (IdentityRowAge(0, 0, 0),)),
                approved.candidate.proposed, 0,
            )

    def test_real_source_replay_qualifies_pinned_schema_and_owner_grants(self):
        for grade in ("A", "B", "C"):
            with self.subTest(grade=grade):
                result = self._prepare(grade=grade)
                self.assertIsInstance(result, tuple)
                candidate, frontier = result
                self.assertIsInstance(candidate, ApprovedMotifCandidate)
                self.assertIsInstance(frontier, SourceFrontier)
                kinds = tuple(slot.key.kind for slot in candidate.candidate.view.plan.allocated)
                self.assertIn("STRUCTURAL", kinds)
                self.assertIn("EXACT", kinds)
                first_exact = kinds.index("EXACT")
                self.assertTrue(all(kind == "STRUCTURAL" for kind in kinds[:first_exact]))
                self.assertTrue(all(kind == "EXACT" for kind in kinds[first_exact:]))
                self.assertEqual(candidate.candidate.view.plan.allocated[0].key.semantic_release, REAL_RELEASE)
                self.assertTrue(frontier.grants)

    def test_approved_digest_and_frontier_replay_the_same_source_owner_projection(self):
        from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot
        from bilqis_mlx.semantics.frame_adapters import public_formal_context

        (selection, source_root, graph, adapter, row, task, policy,
         seed, each, profile) = self._case()
        candidate, frontier = self._prepare()
        replayed = public_formal_context(
            adapter, row, load_pinned_atlas_snapshot(selection),
            source_root=source_root, graph=graph, task_scope=task,
            source_frontier=frontier, policy=policy, source_seed=seed,
            source_each=each, source_profile_parameters=profile)
        self.assertIsInstance(replayed, tuple)
        projection, replayed_frontier = replayed
        self.assertEqual(projection.digest, candidate.approved_context_digest)
        self.assertEqual(replayed_frontier, frontier)

    def test_prepared_motif_context_matches_cold_replay_without_provider_draw(self):
        from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot
        from bilqis_mlx.semantics.frame_adapters import public_formal_context
        from bilqis_mlx.semantics.frame_adapters.public_formal_schema_rights import (
            issue_source_schema_rights_authority, source_schema_rights_frontier,
        )

        (selection, source_root, graph, adapter, row, task, policy,
         seed, each, profile) = self._case()
        snapshot = load_pinned_atlas_snapshot(selection)
        owner_frontier = source_schema_rights_frontier(
            issue_source_schema_rights_authority(selection))
        prepared_projection, prepared_frontier = public_formal_context(
            adapter, row, snapshot, source_root=source_root, graph=graph,
            task_scope=task, source_frontier=owner_frontier, policy=policy,
            source_seed=seed, source_each=each,
            source_profile_parameters=profile)
        cold = qualify_source_motif_context(
            adapter, row, selection, source_root=source_root, graph=graph,
            task_scope=task, source_frontier=owner_frontier, policy=policy,
            source_seed=seed, source_each=each,
            source_profile_parameters=profile, snapshot=snapshot)
        with source_replay_observation() as observed:
            prepared = qualify_prepared_source_motif_context(
                adapter, prepared_projection, prepared_frontier, selection,
                source_root=source_root, graph=graph, task_scope=task,
                source_frontier=owner_frontier, policy=policy, snapshot=snapshot)
        self.assertEqual(prepared, cold)
        self.assertEqual(observed, {
            "provider_draws": 0, "provider_checks": 0, "atlas_reloads": 0})

    def test_source_replay_rejects_tampered_row_and_graph(self):
        selection, _, graph, _, row, *_ = self._case()
        forged_row = dict(row)
        forged_row["gold"] = "caller:forged"
        forged_graph = dict(graph)
        forged_graph["tokens"] = list(reversed(graph["tokens"]))
        for changed in ({"row": forged_row}, {"graph": forged_graph}):
            with self.subTest(changed=tuple(changed)), self.assertRaises(BilqisError):
                self._prepare(selection=selection, **changed)

    def test_source_replay_rejects_row_proxy_that_reads_as_another_draw(self):
        (selection, source_root, graph, adapter, row, _task, _policy,
         seed, each, _profile) = self._case()
        shadow = adapter.draw(
            source_root=source_root, graph=graph, course=None,
            capability=row["capability"], seed=seed + 1, each=each)[0]

        class ShadowRow(dict):
            def __init__(self, baseline, visible):
                super().__init__(baseline)
                self.visible = visible

            def get(self, key, default=None):
                return self.visible.get(key, default)

            def __getitem__(self, key):
                return self.visible[key]

        self.assertNotEqual(row, shadow)
        with self.assertRaises(BilqisError):
            self._prepare(selection=selection, row=ShadowRow(row, shadow))

    def test_revoked_issued_grant_is_not_silently_reissued(self):
        _, frontier = self._prepare()
        revoked = replace(frontier, grants=tuple(
            replace(grant, revoked=True) if index == 0 else grant
            for index, grant in enumerate(frontier.grants)))
        with self.assertRaises(BilqisError):
            self._prepare(frontier=revoked)

    def test_forged_schema_grant_cannot_replace_owner_evidence(self):
        _, frontier = self._prepare()
        schema_index = next(
            index for index, grant in enumerate(frontier.grants)
            if grant.source_handle.startswith("source:motif-schema:"))
        forged = replace(frontier, grants=tuple(
            replace(grant, evidence_digest="f" * 64)
            if index == schema_index else grant
            for index, grant in enumerate(frontier.grants)))
        with self.assertRaises(BilqisError):
            self._prepare(frontier=forged)

    def test_wrong_atlas_release_fails_before_preparation(self):
        selection, *_ = self._case()
        with self.assertRaises(BilqisError):
            self._prepare(selection=replace(selection, release_sha256="0" * 64))
