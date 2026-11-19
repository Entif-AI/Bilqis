"""Bounded native MLX update through the public operator memory owner."""
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.runtime.bamf_operator import session


@pytest.mark.parametrize("visit_error", [False, True])
def test_native_arrays_and_adamw_survive_session_policy(tmp_path, visit_error):
    mx = pytest.importorskip("mlx.core")
    import mlx.nn as nn
    import mlx.optimizers as optim
    from mlx.utils import tree_flatten

    previous_memory = mx.set_memory_limit(256 * 1024 ** 2)
    previous_cache = mx.set_cache_limit(4096)
    accepted = nn.Linear(2, 1)
    candidate = nn.Linear(2, 1)
    accepted_adamw = optim.AdamW(learning_rate=0.01)
    candidate_adamw = optim.AdamW(learning_rate=0.01)
    for model, optimizer in ((accepted, accepted_adamw), (candidate, candidate_adamw)):
        optimizer.init(model.trainable_parameters())
        mx.eval(model.parameters(), optimizer.state)
    owners = (accepted, accepted_adamw, candidate, candidate_adamw)

    def arrays():
        return tuple(value for owner in owners for _, value in tree_flatten(
            owner.parameters() if isinstance(owner, nn.Module) else owner.state))

    before = arrays()
    before_values = tuple(value.tolist() for value in before)
    after = []
    after_values = []
    current = SimpleNamespace(
        generation=1, retained_state=SimpleNamespace(optimizer_step=1))

    failure = RuntimeError("native visit failure")

    def visit(*_args, **_kwargs):
        assert mx.set_cache_limit(0) == 0
        assert all(left is right for left, right in zip(before, arrays(), strict=True))
        assert tuple(value.tolist() for value in arrays()) == before_values
        gradients = nn.value_and_grad(
            candidate, lambda model: mx.sum(model(mx.ones((1, 2))) ** 2))(candidate)[1]
        candidate_adamw.update(candidate, gradients)
        mx.eval(candidate.parameters(), candidate_adamw.state)
        after.extend(arrays())
        after_values.extend(value.tolist() for value in after)
        assert float(candidate_adamw.step) == 1
        assert float(accepted_adamw.step) == 0
        if visit_error:
            raise failure
        return "ACCEPTED"

    try:
        with patch.object(session, "_visit", side_effect=visit), patch.object(
                session, "TrainerObservation", lambda *_args: nullcontext(
                    SimpleNamespace(finish=lambda _: None))), patch.object(
                session, "stop_resource_witness", return_value={"sufficient": True}), patch.object(
                session, "record_normal_stop_receipt", return_value="a" * 64), patch.object(
                session, "load_accepted_generation", return_value=current):
            if visit_error:
                with pytest.raises(RuntimeError) as raised:
                    session.operate_bamf(tmp_path, minutes=1, max_visits=1,
                                         steps_per_visit=1, source_prefetch_workers=0)
                assert raised.value is failure
            else:
                result = session.operate_bamf(
                    tmp_path, minutes=1, max_visits=1,
                    steps_per_visit=1, source_prefetch_workers=0)
                assert result.status == "VISIT_LIMIT"
        assert mx.set_cache_limit(4096) == 4096
        assert all(left is right for left, right in zip(after, arrays(), strict=True))
        assert tuple(value.tolist() for value in arrays()) == tuple(after_values)
        assert all(owner is expected for owner, expected in zip(
            owners, (accepted, accepted_adamw, candidate, candidate_adamw), strict=True))
        assert float(candidate_adamw.step) == 1
        assert float(accepted_adamw.step) == 0
    finally:
        mx.clear_cache()
        mx.set_cache_limit(previous_cache)
        mx.set_memory_limit(previous_memory)
