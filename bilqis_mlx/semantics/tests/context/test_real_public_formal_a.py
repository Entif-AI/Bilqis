"""Behavior tests split from their shared fixture owner."""
from __future__ import annotations
from dataclasses import replace
import unittest
from unittest.mock import patch
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.semantics.context_eligibility import PUBLIC_FORMAL, ApprovedContextProjection, C09ContextInvalidation, ContextEligibility, ContextHold, ContextMember, ContextTransition, ContextPolicy, EligibleContext, SourceFrontier, SourceGrant, TaskScope, check_context_eligibility, frame_evidence_digest, member_evidence_digest, project_context, transition_context
from bilqis_mlx.semantics.frame_adapters import public_formal_context
from bilqis_mlx.semantics.frame_adapters.public_formal import (
    _public_formal_context_from_verified_row,
)
from bilqis_mlx.b11_observation import source_replay_observation
from bilqis_mlx.semantics.frame_schema import ConceptRef, FrameSchema, RoleOccurrence, RoleSpec, SourceSpan, make_frame_instance
from bilqis_mlx.semantics.tests.test_context_eligibility import RELEASE, PRINCIPAL, TENANT, REGION, SCOPE, _frame, _case, ContextEligibilityTests

class ContextEligibilityTests2(ContextEligibilityTests):
    def _source_cases(self):
        from bilqis_mlx.grade_a_probe import read_sources
        from bilqis_mlx.live_grade_c import draw as draw_numeric_rows, registry_graph
        from bilqis_mlx.source_adapters.school import (
            A_ORACLE, B_ORACLE, C_ORACLE, live_source_registry,
        )
        from bilqis_mlx.semantics.tests.frame_adapters.helpers import _snapshot
        from pathlib import Path

        root = Path(__file__).resolve().parents[4]
        source_root = root / "vendor/legacy-v16"
        _, _, micro_graph, _, _ = read_sources(source_root)
        numeric_graph = registry_graph()
        registry = live_source_registry()
        snapshot = _snapshot()
        task = TaskScope(
            PRINCIPAL, TENANT, "TRAINING", snapshot.release_sha256,
            REGION, SCOPE, observed_frontier=3, effective_time=5,
            causal_prefix_end=30,
        )
        policy = ContextPolicy(
            "synthetic:policy", 1, 1,
            ("TRAINING",), (PUBLIC_FORMAL,), (REGION,), (SCOPE,),
            (PUBLIC_FORMAL,),
            ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
            tuple((PUBLIC_FORMAL,) * count for count in range(3, 25)),
        )
        source_frontier = SourceFrontier(1, 1, ())
        a = registry.require(
            "bilqis_mlx.grade_a_probe.make_record", A_ORACLE)
        a_row = a.draw(
            source_root=source_root, graph=micro_graph, course=None,
            capability="A.IDENTITY", seed=31, each=2)[0]
        b = registry.require(
            "bilqis_mlx.live_grade_b.draw_connectives", B_ORACLE)
        b_row = b.draw(
            source_root=source_root, graph=micro_graph, course=None,
            capability="B.AND", seed=31, each=4)[0]
        c = registry.require(
            "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
        c_row = next(row for row in draw_numeric_rows(
            numeric_graph, seed=19, maximum=3)
            if row["capability"] == "C.ADD")
        return source_root, snapshot, task, policy, source_frontier, (
            (a, a_row, micro_graph, 31, 2, None),
            (b, b_row, micro_graph, 31, 4, None),
            (c, c_row, numeric_graph, 19, 12, {"numbers": ("0", "1", "2", "3")}),
        )

    def test_real_public_formal_a_b_c_source_constructors(self):
        source_root, snapshot, task, policy, source_frontier, cases = self._source_cases()
        for adapter, row, graph, seed, each, profile in cases:
            with self.subTest(adapter=adapter.descriptor.adapter_id):
                result = public_formal_context(
                    adapter, row, snapshot, source_root=source_root,
                    graph=graph,
                    task_scope=task, source_frontier=source_frontier,
                    policy=policy, source_seed=seed, source_each=each,
                    source_profile_parameters=profile,
                )
                self.assertIsInstance(result, tuple)
                projection, admitted = result
                self.assertIsInstance(projection, ApprovedContextProjection)
                self.assertTrue(projection.attention_handles)
                self.assertTrue(all(
                    handle.startswith("public-formal:")
                    for _, handle in projection.attention_handles))
                self.assertTrue(all(
                    envelope.frame.source_span == SourceSpan(0, len(row["tokens"]))
                    for envelope in projection.envelopes))
                self.assertEqual(
                    project_context(projection.envelopes, task, admitted, policy),
                    projection)
                self.assertEqual(
                    public_formal_context(
                        adapter, row, snapshot, source_root=source_root,
                        graph=graph,
                        task_scope=task, source_frontier=admitted, policy=policy,
                        source_seed=seed, source_each=each,
                        source_profile_parameters=profile),
                    result)
                with self.assertRaises(TypeError):
                    public_formal_context(
                        adapter, row, snapshot, source_root=source_root,
                        graph=graph, source_span=SourceSpan(0, 1),
                        task_scope=task, source_frontier=admitted,
                        policy=policy, source_seed=seed, source_each=each,
                        source_profile_parameters=profile)
                spoofed_identity = dict(row)
                spoofed_identity["id"] = "f" * 64
                spoofed_identity["source_id"] = "f" * 64
                with self.assertRaises(BilqisError) as caught:
                    public_formal_context(
                        adapter, spoofed_identity, snapshot,
                        source_root=source_root, graph=graph,
                        task_scope=task, source_frontier=source_frontier,
                        policy=policy, source_seed=seed, source_each=each,
                        source_profile_parameters=profile)
                self.assertEqual(
                    caught.exception.context["reason"],
                    "BAMF_CONTEXT_PUBLIC_FORMAL_ROW_IDENTITY_UNVERIFIED")

    def test_prequalified_public_formal_projection_avoids_provider_replay(self):
        source_root, snapshot, task, policy, frontier, cases = self._source_cases()
        adapter, row, graph, seed, each, profile = cases[0]
        expected = public_formal_context(
            adapter, row, snapshot, source_root=source_root, graph=graph,
            task_scope=task, source_frontier=frontier, policy=policy,
            source_seed=seed, source_each=each,
            source_profile_parameters=profile)
        with source_replay_observation() as observed:
            actual = _public_formal_context_from_verified_row(
                adapter, row, snapshot, source_root=source_root, graph=graph,
                task_scope=task, source_frontier=frontier, policy=policy)
        self.assertEqual(actual, expected)
        self.assertEqual(observed, {
            "provider_draws": 0, "provider_checks": 0, "atlas_reloads": 0})

    def test_public_formal_forged_source_owner_and_fields_are_rejected(self):
        source_root, snapshot, task, policy, source_frontier, cases = self._source_cases()
        a, a_row, micro_graph, _, _, _ = cases[0]
        forged = dict(a_row)
        forged["gold"] = "source-tampered"
        with self.assertRaises(BilqisError):
            public_formal_context(
                a, forged, snapshot, source_root=source_root,
                graph=micro_graph,
                task_scope=task, source_frontier=source_frontier,
                policy=policy, source_seed=31, source_each=2)
        forged_adapter = replace(a, check=lambda *args, **kwargs: True)
        with self.assertRaises(BilqisError) as caught:
            public_formal_context(
                forged_adapter, forged, snapshot, source_root=source_root,
                graph=micro_graph, task_scope=task,
                source_frontier=source_frontier, policy=policy,
                source_seed=31, source_each=2)
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_CONTEXT_PUBLIC_FORMAL_ADAPTER_UNTRUSTED")
        with self.assertRaises(BilqisError):
            public_formal_context(
                a, a_row, snapshot, source_root=source_root,
                graph=micro_graph,
                task_scope=replace(task, semantic_release="b" * 64),
                source_frontier=source_frontier, policy=policy,
                source_seed=31, source_each=2)
        with self.assertRaises(BilqisError):
            public_formal_context(
                a, a_row, snapshot, source_root="synthetic:unverified",
                graph=micro_graph, task_scope=task,
                source_frontier=source_frontier, policy=policy,
                source_seed=31, source_each=2)
        spoofed = dict(a_row)
        spoofed["source_id"] = "f" * 64
        spoofed["id"] = "f" * 64
        with self.assertRaises(BilqisError) as caught:
            public_formal_context(
                a, spoofed, snapshot, source_root=source_root,
                graph=micro_graph, task_scope=task,
                source_frontier=source_frontier, policy=policy,
                source_seed=31, source_each=2)
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_CONTEXT_PUBLIC_FORMAL_ROW_IDENTITY_UNVERIFIED")

    def test_public_formal_future_prefix_never_mints_handles(self):
        from bilqis_mlx.grade_a_probe import read_sources
        from bilqis_mlx.source_adapters.school import A_ORACLE, live_source_registry
        from bilqis_mlx.semantics.tests.frame_adapters.helpers import _snapshot
        from pathlib import Path
        source_root = Path(__file__).resolve().parents[4] / "vendor/legacy-v16"
        micro_graph = read_sources(source_root)[2]
        adapter = live_source_registry().require(
            "bilqis_mlx.grade_a_probe.make_record", A_ORACLE)
        row = adapter.draw(
            source_root=source_root, graph=micro_graph, course=None,
            capability="A.IDENTITY", seed=31, each=2)[0]
        self.assertGreater(len(row["tokens"]), 10)
        task = TaskScope(
            PRINCIPAL, TENANT, "TRAINING", _snapshot().release_sha256,
            REGION, SCOPE, 3, 5, 10)
        _, _, frontier, policy = _case(count=1)
        result = public_formal_context(
            adapter, row, _snapshot(), source_root=source_root,
            graph=micro_graph,
            task_scope=task, source_frontier=SourceFrontier(1, 1, ()),
            policy=policy, source_seed=31, source_each=2)
        self.assertIsInstance(result, ContextHold)
        self.assertIn("BAMF_CONTEXT_INVISIBLE_PREFIX", result.reason_codes)

    def test_public_formal_full_set_is_order_invariant_but_members_keep_order(self):
        frames, task, frontier, policy = _case(count=3, two_roles=True)
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            first = check_context_eligibility(frames, task, frontier, policy)
            reversed_order = check_context_eligibility(
                tuple(reversed(frames)), task, frontier, policy)
        self.assertIsInstance(first, EligibleContext)
        self.assertEqual(first.digest, reversed_order.digest)
        self.assertEqual(first.frames, reversed_order.frames)
        self.assertEqual(
            first.frames[0].member_handles,
            ("source:member:0:subject", "source:member:0:object"),
        )
        self.assertEqual(first.allowed_join_classes, (PUBLIC_FORMAL,))
        self.assertEqual(len(first.frames), 3)

    def test_individually_allowed_frames_cannot_bypass_forbidden_pair_join(self):
        frames, task, frontier, policy = _case()
        policy = replace(policy, allowed_join_pairs=())
        for frame in frames:
            self.assertIsInstance(
                check_context_eligibility((frame,), task, frontier, policy),
                EligibleContext,
            )
        result = check_context_eligibility(frames, task, frontier, policy)
        self.assertIsInstance(result, ContextHold)
        self.assertIn("BAMF_CONTEXT_FORBIDDEN_JOIN", result.reason_codes)
        self.assertEqual(
            result.source_handles, ("source:frame:0", "source:frame:1"))
        self.assertFalse(hasattr(result, "frames"))
