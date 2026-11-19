"""#1297 C03/C06 offer construction obeys the learner-relative frontier."""
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.runtime import priority_authority as authority
from bilqis_mlx.runtime.autonomy_state import (
    persist_autonomy_state,
    read_autonomy_state,
)
from bilqis_mlx.runtime.bamf_operator.session import _execution_context
from bilqis_mlx.runtime.foundation_teacher_owner import (
    current_foundation_teacher_projection,
)
from bilqis_mlx.runtime.tests.operator.pre_neural_journey_support import (
    PreNeuralJourneySupport,
    historical_school_release,
    journey_source,
    portable_atlas_snapshot,
    wide_shape_patch,
)


def _source_context(*capability_ids):
    capabilities = tuple(
        SimpleNamespace(capability_id=capability_id)
        for capability_id in capability_ids)
    return SimpleNamespace(
        release=SimpleNamespace(
            execution_plan=SimpleNamespace(capabilities=capabilities)))


def _frontier(*ready, exclusions=()):
    return SimpleNamespace(
        ready_capability_ids=tuple(ready), exclusions=tuple(exclusions))


def _cadence(frontier):
    return SimpleNamespace(
        authorized_capability_ids=frontier.ready_capability_ids,
        phase=SimpleNamespace(value="MAIN"),
        disposition=SimpleNamespace(value="TEACHING"),
    )


def _offer(_context, _parent, _path, *, capability, source_seed, source_each,
           planning_generation):
    return SimpleNamespace(
        capability_id=capability,
        source_seed=source_seed,
        source_each=source_each,
        planning_generation=planning_generation,
    )


def test_all_release_enumeration_cannot_construct_offer_for_held_capability():
    context = _source_context("cap:beta", "cap:alpha")
    planning_generation = object()
    with patch.object(
            authority, "prepare_priority_source_offer",
            side_effect=_offer) as prepare:
        frontier = _frontier("cap:alpha")
        capabilities, offers = authority._priority_offers(
            context, object(), "/atlas", 17, planning_generation,
            frontier, frontier.ready_capability_ids)

    assert tuple(item.capability_id for item in capabilities) == ("cap:alpha",)
    assert tuple(item[0] for item in offers) == ("cap:alpha",)
    assert tuple(call.kwargs["capability"] for call in prepare.call_args_list) == (
        "cap:alpha",)


def test_frontier_reissue_alone_expands_offer_set_without_grade_logic():
    context = _source_context("cap:beta", "cap:alpha")
    planning_generation = object()
    with patch.object(
            authority, "prepare_priority_source_offer",
            side_effect=_offer):
        first_frontier = _frontier("cap:alpha")
        second_frontier = _frontier("cap:alpha", "cap:beta")
        _first_capabilities, first = authority._priority_offers(
            context, object(), "/atlas", 17, planning_generation,
            first_frontier, first_frontier.ready_capability_ids)
        _second_capabilities, second = authority._priority_offers(
            context, object(), "/atlas", 17, planning_generation,
            second_frontier, second_frontier.ready_capability_ids)

    assert tuple(item[0] for item in first) == ("cap:alpha",)
    assert tuple(item[0] for item in second) == ("cap:alpha", "cap:beta")


def test_a09_planning_generation_cannot_expand_offers_without_frontier_reissue():
    context = _source_context("cap:beta", "cap:alpha")
    generations = (object(), object())
    with patch.object(
            authority, "prepare_priority_source_offer",
            side_effect=_offer):
        frontier = _frontier(
            "cap:alpha", exclusions=(("cap:beta", "FUTURE_GENERATED_GRADE"),))
        results = tuple(authority._priority_offers(
            context, object(), "/atlas", 17, generation,
            frontier, frontier.ready_capability_ids)[1]
            for generation in generations)

    assert tuple(tuple(item[0] for item in offers) for offers in results) == (
        ("cap:alpha",), ("cap:alpha",))


def test_frontier_ready_identity_must_exist_in_current_release():
    context = _source_context("cap:alpha")
    with pytest.raises(BilqisError) as failure:
        frontier = _frontier("cap:unknown")
        authority._priority_offers(
            context, object(), "/atlas", 17, object(),
            frontier, frontier.ready_capability_ids)
    assert failure.value.context["reason"] == (
        "BAMF_PRIORITY_LAWFUL_FRONTIER_RELEASE_DRIFT")


def test_cadence_can_only_narrow_lawful_ready_offer_set():
    context = _source_context("cap:alpha", "cap:beta")
    frontier = _frontier("cap:alpha", "cap:beta")
    authorized = ("cap:beta",)
    with patch.object(
            authority, "prepare_priority_source_offer", side_effect=_offer):
        capabilities, offers = authority._priority_offers(
            context, object(), "/atlas", 17, object(), frontier, authorized)
    assert tuple(item.capability_id for item in capabilities) == ("cap:beta",)
    assert tuple(item[0] for item in offers) == ("cap:beta",)


class LawfulPriorityRuntimeTests(PreNeuralJourneySupport, unittest.TestCase):
    def test_accepted_prerequisite_evidence_reissues_frontier_and_expands_offers(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)

        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(
                    snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(
                    self.run)
                projection = current_foundation_teacher_projection(self.run)
                teacher_epoch = restore_teacher_lineage(projection.teacher_state)
                first = authority.issue_foundation_priority_authority(
                    self.run, context, parent, teacher_epoch, atlas_path,
                    teacher_state=projection.teacher_state)

                self.assertEqual(len(first.offers), 14)
                self.assertNotIn("C.COUNT", dict(first.offers))
                held = next(
                    item for item in first.lawful_frontier.capabilities
                    if item.capability_id == "C.COUNT")
                self.assertEqual(
                    {hold.dependency_id for hold in held.holds
                     if hold.code == "PREREQUISITE_EVIDENCE_REQUIRED"},
                    {"A.IDENTITY", "A.MEMBER"})

                plan, ledger = read_autonomy_state(self.run, context.release)
                for prerequisite in ("A.IDENTITY", "A.MEMBER"):
                    for obligation in obligations_for_capability(
                            context.release, prerequisite, plan=plan):
                        ledger = record_evidence(
                            context.release, ledger,
                            EvidenceReceipt(
                                obligation_id=obligation.obligation_id,
                                evidence_id="1297:" + obligation.obligation_id,
                                checkpoint_sha256=(
                                    first.lawful_frontier.
                                    accepted_checkpoint_sha256),
                                optimizer_step=(
                                    first.lawful_frontier.
                                    accepted_optimizer_step),
                                cohort_sha256="d" * 64,
                                specimen_count=obligation.minimum_specimens,
                                passed=True,
                            ),
                            plan=plan,
                            current_checkpoint_sha256=(
                                first.lawful_frontier.
                                accepted_checkpoint_sha256),
                            current_optimizer_step=(
                                first.lawful_frontier.
                                accepted_optimizer_step),
                        )
                persist_autonomy_state(
                    self.run, context.release, plan=plan, ledger=ledger)

                second = authority.issue_foundation_priority_authority(
                    self.run, context, parent, teacher_epoch, atlas_path,
                    teacher_state=projection.teacher_state)
                second_offers = dict(second.offers)
                self.assertEqual(len(second.offers), 13)
                self.assertNotIn("A.IDENTITY", second_offers)
                self.assertNotIn("A.MEMBER", second_offers)
                self.assertIn("C.COUNT", second_offers)
                ready = next(
                    item for item in second.lawful_frontier.capabilities
                    if item.capability_id == "C.COUNT")
                self.assertEqual(ready.disposition.value, "READY")
                self.assertEqual(
                    ready.evidence_complete_prerequisites,
                    ("A.IDENTITY", "A.MEMBER"))
