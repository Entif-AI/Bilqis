"""#1273 source qualification is paid once before prepared Factory reuse."""
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.factory_training_bridge import _prepared_source_inputs


def test_direct_factory_path_binds_rows_before_heavy_source_preparation():
    rows = ({"id": "row:one", "capability": "cap"},)
    authority = object()
    events = []

    class Context:
        def bind_rows(self, supplied, *, seed, capability, each):
            assert supplied == rows
            assert (seed, capability, each) == (17, "cap", 1)
            events.append("bind")
            return authority

    def prepare(_context, _authenticated, supplied, **kwargs):
        assert supplied == rows
        assert kwargs["source_authority"] is authority
        events.append("prepare")
        return "adapter", "manifest", "profile", ("source-row",)

    with patch(
            "bilqis_mlx.runtime.factory_training_bridge._prepare_factory_source_rows",
            side_effect=prepare), patch(
                "bilqis_mlx.runtime.priority_source_materialization._prepare_model_sources",
                return_value=(("model-source",), ("config",))) as model_sources:
        result = _prepared_source_inputs(
            None, Context(), SimpleNamespace(), rows,
            capability="cap", source_seed=17, source_each=1)

    assert events == ["bind", "prepare"]
    model_sources.assert_called_once()
    assert result == (
        authority, "adapter", "manifest", "profile", ("source-row",),
        ("model-source",), None, None)
