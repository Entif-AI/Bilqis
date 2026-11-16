"""#1232 selected-offer source materialization reuse witnesses."""
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.priority_source_materialization import (
    PreparedPrioritySourceMaterialization,
    prepare_priority_source_materialization,
)
from bilqis_mlx.runtime.source_execution import SourcePreparationMetrics


class _Owner:
    def __init__(self):
        self.requires = 0

    def require(self, *_args):
        self.requires += 1

    def require_row(self, *_args):
        self.requires += 1

    def require_current(self):
        self.requires += 1


class _Registrar:
    def __init__(self):
        self.registrations = []

    def register(self, kind, owner):
        self.registrations.append((kind, owner))


def test_selected_source_ast_context_and_prefix_materialize_once_per_visit():
    rows = ({"id": "row:one", "capability": "cap", "tokens": [1]},)
    prefix = SimpleNamespace(positions=(1,))
    model_sources = (SimpleNamespace(prefix=prefix),)
    source_rows = (SimpleNamespace(row=rows[0]),)
    feature_owner, packed_owner, source_owner = _Owner(), _Owner(), _Owner()
    b11_source = _Owner()
    registrar = _Registrar()
    authenticated = SimpleNamespace(features="features")
    offer = SimpleNamespace(
        _materialized={},
        _planning_generation=SimpleNamespace(
            _authenticated_features=authenticated,
            _target_registrar=registrar),
        capability_id="cap",
        source_seed=17,
        source_each=1,
        source_authority=object(),
        require_qualified_current=lambda *_args, **_kwargs: rows,
    )
    context = SimpleNamespace(
        _source_preparation_metrics=SourcePreparationMetrics())

    with patch(
            "bilqis_mlx.runtime.factory_training_bridge._prepare_factory_source_rows",
            return_value=("adapter", "manifest", "profile", source_rows)) as prepare, patch(
                "bilqis_mlx.runtime.priority_source_materialization._prepare_model_sources",
                return_value=(model_sources, ("config",))) as compile_sources, patch(
                    "bilqis_mlx.runtime.factory_training_bridge._prepare_b11_source_binding",
                    return_value=b11_source) as prepare_b11, patch(
                    "bilqis_mlx.runtime.factory_training_bridge._motif_planning_input",
                    return_value="motif") as motif, patch(
                        "bilqis_mlx.runtime.priority_source_materialization._owners",
                        return_value=(feature_owner, packed_owner, source_owner)):
        first = prepare_priority_source_materialization(
            offer, context, "parent")
        second = prepare_priority_source_materialization(
            offer, context, "parent")

    assert type(first) is PreparedPrioritySourceMaterialization
    assert second is first
    prepare.assert_called_once()
    assert prepare.call_args.kwargs["source_authority"] is offer.source_authority
    compile_sources.assert_called_once()
    prepare_b11.assert_called_once()
    motif.assert_called_once()
    assert context._source_preparation_metrics.source_context_builds == 1
    assert context._source_preparation_metrics.compiled_source_builds == 1
    assert len(registrar.registrations) == 6
    assert feature_owner.requires == 2
    assert packed_owner.requires == 2
    assert source_owner.requires == 2
    assert b11_source.requires == 2
