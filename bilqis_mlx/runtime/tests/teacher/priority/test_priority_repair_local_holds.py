"""#1393 repair-only priority options hold locally instead of stopping teaching."""
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.runtime.tests.teacher.priority.test_priority_execution import (
    HeldOffer,
    Offer,
    Visit,
    lawful,
    priority,
)


@dataclass(frozen=True)
class _Epoch:
    current_json: str = "{}"


def _option(stable_id, action_kind, capability):
    return SimpleNamespace(
        stable_id=stable_id,
        action_kind=action_kind,
        eligible_since=7,
        downstream_unlocks=2,
        context=SimpleNamespace(capability_id=capability, scope="scope"),
    )


def _select(priority, options, offers, **kwargs):
    frontier = SimpleNamespace(
        evidence=tuple((option.stable_id, "evidence") for option in options))
    parent = SimpleNamespace(
        retained_state="student",
        run_identity=SimpleNamespace(digest="run", run_seed=5),
        generation=4,
    )
    cache = SimpleNamespace(accepted_manifest_sha256="manifest")
    school = SimpleNamespace(
        stage="MAIN", current_student=SimpleNamespace(sha256="student-id"))
    qualified = SimpleNamespace(
        ranked=SimpleNamespace(
            ordered=tuple(options),
            tiers=tuple((option.stable_id, index + 1) for index, option in enumerate(options)),
        ),
        offers=tuple(offers),
        holds=(),
    )
    identity = SimpleNamespace(to_record=lambda: {"visit": 1})
    ready = lawful(*(option.context.capability_id for option in options))
    with patch.object(priority, "_accepted_parent", return_value=(parent, cache)), \
         patch.object(priority, "_c03_projection", return_value=SimpleNamespace(teacher_state={})), \
         patch.object(priority, "restore_teacher_lineage", return_value=_Epoch()), \
         patch.object(priority, "candidate_identity_digest", return_value="student-id"), \
         patch.object(priority, "_teacher", return_value={}), \
         patch.object(priority, "contract_digest", return_value="epoch-digest"), \
         patch.object(priority, "salience_priority_features", return_value={}), \
         patch.object(priority, "requalify_priority", return_value=qualified), \
         patch.object(priority, "_grade", return_value="g"), \
         patch.object(priority, "select_visit_policy", return_value=("k", {"lr": 0.5}, {})), \
         patch.object(priority, "_selection_projection", return_value=SimpleNamespace(teacher_state={})), \
         patch.object(priority, "derive_teacher_visit_identity", return_value=identity), \
         patch.object(priority, "record_teacher_visit_identity", return_value="recorded"), \
         patch.object(priority, "_issue_bound_visit", return_value=Visit(identity)):
        return priority.select_accepted_priority_visit(
            "/run", SimpleNamespace(release=None), frontier, None, None,
            tuple(offers), None, school, None, None,
            program=None, now=1, lawful_frontier=ready, **kwargs)


@pytest.mark.parametrize(
    ("action_kind", "reason"),
    ((1, "CORRECTION_ACTION_REQUIRED"),
     (2, "PROCEDURE_REPAIR_ACTION_REQUIRED")),
)
def test_repair_option_holds_locally_when_later_teaching_is_available(
        priority, action_kind, reason):
    repair = _option("repair", action_kind, "repair-cap")
    teach = _option("teach", 3, "teach-cap")
    result = _select(priority, (repair, teach), (("teach", Offer()),))
    assert result.status == "TEACHER_SELECTED"
    assert result.option_id == "teach"
    assert result.holds == (("repair", reason),)


def test_repair_only_frontier_remains_action_required(priority):
    repair = _option("repair", priority.ActionKind.CORRECTION, "repair-cap")
    result = _select(priority, (repair,), ())
    assert result.status == "ACTION_REQUIRED"
    assert result.option_id == "repair"
    assert result.holds == (("repair", "CORRECTION_ACTION_REQUIRED"),)


def test_source_hold_still_skips_to_later_teaching(priority):
    stale = _option("stale", 3, "stale-cap")
    teach = _option("teach", 3, "teach-cap")
    result = _select(
        priority, (stale, teach), (("stale", HeldOffer()), ("teach", Offer())))
    assert result.status == "TEACHER_SELECTED"
    assert result.option_id == "teach"
    assert result.holds == (("stale", "SOURCE_OFFER_HELD"),)


@pytest.mark.parametrize("has_peer", (True, False))
def test_resource_hold_skips_only_exhausted_target(priority, has_peer):
    failed = _option("failed", 3, "failed-cap")
    options = (failed,)
    offers = (("failed", Offer()),)
    if has_peer:
        options += (_option("peer", 3, "peer-cap"),)
        offers += (("peer", Offer()),)
    result = _select(
        priority, options, offers, resource_holds=frozenset({"failed-cap"}))
    assert result.holds == (("failed", "BAMF_C08_OOM_EXHAUSTED"),)
    if has_peer:
        assert result.status == "TEACHER_SELECTED"
        assert result.option_id == "peer"
    else:
        assert result.status == "NO_ADMISSIBLE_TEACHING"
