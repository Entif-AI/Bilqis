"""#1266 non-neural B11 observation aggregation at the C08 boundary."""
from types import SimpleNamespace

from bilqis_mlx.runtime.c08_gradient_accumulation import _add_b11_observation


def test_b11_observation_aggregation_is_pure_host_accounting():
    total = {
        "b11_preflight_wall_seconds": 0.0,
        "b11_autodiff_wall_seconds": 0.0,
        "b11_provider_draw_count": 0,
        "b11_atlas_reload_count": 0,
    }
    execution = SimpleNamespace(_performance_observation={
        "b11_preflight_wall_seconds": 0.2,
        "b11_autodiff_wall_seconds": 0.4,
        "b11_provider_draw_count": 8,
        "b11_atlas_reload_count": 2,
    })

    _add_b11_observation(total, execution)
    _add_b11_observation(total, execution)

    assert total == {
        "b11_preflight_wall_seconds": 0.4,
        "b11_autodiff_wall_seconds": 0.8,
        "b11_provider_draw_count": 16,
        "b11_atlas_reload_count": 4,
    }
