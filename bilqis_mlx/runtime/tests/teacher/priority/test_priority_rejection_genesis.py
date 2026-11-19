"""Selected-teacher lineage at generation-zero rehearsal."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime import priority_rejection_replay as rejection_replay
from bilqis_mlx.runtime.tests.teacher.priority.rejection_projection_support import _cache


@pytest.mark.parametrize("prebootstrap", [True, False])
def test_weakness_rehearsal_uses_selected_teacher_after_genesis_bootstrap(
        monkeypatch, prebootstrap):
    """Generation-zero teacher custody is bootstrapped in the selected visit."""
    from bilqis_mlx.learning.tests.teaching.test_teacher_lineage import TeacherLineageTests

    _teacher, _adaptation, projection = TeacherLineageTests().initialize()
    genesis = {
        "schema": "bilqis.mlx.bamf-teacher-state/v1",
        "teacher_identity": "f" * 64,
        "teacher_epoch": 0,
        "next_seed": 42,
        "cursor": "GENESIS",
    }
    parent = SimpleNamespace(
        teacher_state=genesis if prebootstrap else projection.teacher_state)
    selected = SimpleNamespace(visit=SimpleNamespace(
        identity=SimpleNamespace(capability_id="C.ADD"), projection=projection))
    monkeypatch.setattr(
        rejection_replay, "_current_projection",
        lambda *_: SimpleNamespace(weaknesses_view=lambda: ()))

    assert rejection_replay.current_structural_weaknesses(
        "/run", parent, _cache(), object(), selected) == ()
    if prebootstrap:
        assert "c03_lineage" not in parent.teacher_state


def test_weakness_rehearsal_rejects_invalid_selected_teacher_lineage(monkeypatch):
    from bilqis_mlx.learning.tests.teaching.test_teacher_lineage import TeacherLineageTests

    _teacher, _adaptation, projection = TeacherLineageTests().initialize()
    invalid_teacher = deepcopy(projection.teacher_state)
    invalid_teacher["c03_lineage"]["current_teacher_sha256"] = "0" * 64
    selected = SimpleNamespace(visit=SimpleNamespace(
        identity=SimpleNamespace(capability_id="C.ADD"),
        projection=SimpleNamespace(teacher_state=invalid_teacher)))
    monkeypatch.setattr(
        rejection_replay, "_current_projection",
        lambda *_: SimpleNamespace(weaknesses_view=lambda: ()))

    with pytest.raises(BilqisError) as failure:
        rejection_replay.current_structural_weaknesses(
            "/run", SimpleNamespace(teacher_state=projection.teacher_state),
            _cache(), object(), selected)
    assert failure.value.context["reason"] == "TEACHER_LINEAGE_INVALID"
