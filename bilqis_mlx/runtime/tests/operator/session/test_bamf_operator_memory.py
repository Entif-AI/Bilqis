"""Native session owns the existing MLX cache policy only under its writer lock."""
from contextlib import contextmanager, ExitStack, nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
from unittest.mock import Mock, patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_operator import session
from bilqis_mlx.runtime.bamf_operator.locking import (
    bamf_operator_lock, bamf_operator_lock_held,
)
from bilqis_mlx.runtime.tests.model.parity.test_mlx_memory import FakeMlx


@pytest.fixture
def native_session(tmp_path):
    mx = FakeMlx(cache_limit=987654)
    mlx = ModuleType("mlx")
    mlx.core = mx
    current = SimpleNamespace(
        generation=4, retained_state=SimpleNamespace(optimizer_step=11))
    observer = lambda *_args: nullcontext(SimpleNamespace(finish=lambda _: None))
    resource = Mock(return_value={"sufficient": True})
    stop = Mock(return_value="a" * 64)
    with ExitStack() as stack:
        stack.enter_context(patch.dict(sys.modules, {"mlx": mlx, "mlx.core": mx}))
        for name, value in (
                ("TrainerObservation", observer),
                ("stop_resource_witness", resource),
                ("record_normal_stop_receipt", stop)):
            stack.enter_context(patch.object(session, name, value))
        stack.enter_context(patch.object(
            session, "load_accepted_generation", return_value=current))
        yield SimpleNamespace(
            root=tmp_path, mx=mx, current=current, resource=resource, stop=stop)


def _operate(state, **kwargs):
    return session.operate_bamf(
        state.root, minutes=1, max_visits=1, steps_per_visit=1,
        source_prefetch_workers=0, **kwargs)


def test_normal_session_covers_adoption_visits_and_stop_without_admission_reentry(
        native_session):
    state = native_session
    candidate_model, candidate_adamw = object(), object()
    accepted_model, accepted_adamw = object(), object()
    identities = (candidate_model, candidate_adamw, accepted_model, accepted_adamw)
    observed = []

    def check(phase):
        assert state.mx.cache_limit == 0
        assert bamf_operator_lock_held(state.root) is True
        assert identities == (
            candidate_model, candidate_adamw, accepted_model, accepted_adamw)
        observed.append(phase)

    def visit(*_args, **_kwargs):
        check("visit")
        return "ACCEPTED"

    def stop(*_args, **_kwargs):
        check("stop")
        return "a" * 64

    state.stop.side_effect = stop
    with patch.object(session, "_visit", side_effect=visit), patch.object(
            session, "_accepted_learning_reentry") as reentry, patch(
            "bilqis_mlx.runtime._release_adoption.native_profile.adopt_profile_release",
            side_effect=lambda *_args, **_kwargs: check("adopt")):
        result = _operate(state, parent_graph={}, profile_release=object())

    assert (result.status, result.visits, result.accepted) == ("VISIT_LIMIT", 1, 1)
    assert observed == ["adopt", "visit", "stop"]
    reentry.assert_not_called()
    assert state.mx.cache_limit == 987654
    assert state.mx.calls == [
        ("set_cache_limit", 0), ("clear_cache",),
        ("clear_cache",), ("set_cache_limit", 987654)]
    assert bamf_operator_lock_held(state.root) is False
    assert state.current.retained_state.optimizer_step == 11


def test_visit_exception_restores_policy_and_prefetch_lifecycle(native_session):
    state = native_session
    lifecycle = []
    failure = RuntimeError("injected visit exception")

    @contextmanager
    def pool(_workers):
        lifecycle.append("start")
        try:
            yield object()
        finally:
            assert state.mx.cache_limit == 987654
            assert bamf_operator_lock_held(state.root) is False
            lifecycle.append("stop")

    def visit(*_args, **_kwargs):
        assert state.mx.cache_limit == 0
        assert bamf_operator_lock_held(state.root) is True
        raise failure

    with patch.object(session, "_visit", side_effect=visit), patch(
            "bilqis_mlx.runtime.source_prefetch.source_prefetch_pool", pool):
        with pytest.raises(RuntimeError) as raised:
            session.operate_bamf(state.root, max_visits=1, source_prefetch_workers=1)
    assert raised.value is failure
    assert lifecycle == ["start", "stop"]
    assert state.mx.cache_limit == 987654
    assert state.mx.calls[-2:] == [("clear_cache",), ("set_cache_limit", 987654)]
    state.stop.assert_not_called()


def test_writer_refusal_does_not_acquire_memory_policy(native_session):
    state = native_session
    with bamf_operator_lock(state.root), pytest.raises(BilqisError) as raised:
        _operate(state)
    assert raised.value.context["reason"] == "BAMF_OPERATOR_ANOTHER_WRITER_ACTIVE"
    assert state.mx.calls == []


def test_invalid_bounds_does_not_acquire_memory_policy(native_session):
    with pytest.raises(BilqisError):
        session.operate_bamf(native_session.root, steps_per_visit=17)
    assert native_session.mx.calls == []


def test_disk_reserve_stop_restores_policy_without_a_visit(native_session):
    state = native_session
    state.resource.return_value = {"sufficient": False}
    with patch.object(session, "_visit") as visit:
        result = _operate(state)
    assert result.status == "DISK_RESERVE_REACHED"
    assert result.visits == 0
    assert state.mx.cache_limit == 987654
    visit.assert_not_called()
