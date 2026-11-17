from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator._session_execution import execute_horizon


def test_native_horizon_preserves_enrichment_role_into_candidate_delivery():
    direct = ({"id": "direct", "capability": "Z.C0"},)
    enrichment = ({"id": "extra", "capability": "Z.C0"},)
    lesson = NS(direct=direct, enrichment=enrichment, delivered=(*direct, *enrichment))
    observed = []
    candidate_calls = []

    class Lane:
        def __init__(self, *args, **kwargs):
            pass

        def lesson(self, ordinal):
            assert ordinal == 1
            return lesson

    def observation(capture, step, rows, seed, **kwargs):
        observed.append((rows, kwargs.get("enrichment")))
        return NS(capture=capture, step=step, option_rows=rows, seed=seed,
                  enrichment=kwargs.get("enrichment", ()))

    def execute_candidate(*args, **kwargs):
        candidate_calls.append(kwargs)
        return NS(transaction=NS(update_steps=1))

    selection = NS(
        offer=NS(source_seed=17, capability_id="Z.C0"),
        visit=NS(identity=NS(visit_id="v"), projection=NS(teacher_state={})),
    )
    parent = NS(
        teacher_state={}, retained_state=NS(optimizer_step=4),
        optimizer_hyperparameters="hp",
    )
    cache = NS(generation=1, accepted_manifest_sha256="a" * 64)

    with patch("bilqis_mlx.learning.teacher_lineage.instruction_history",
               return_value=("COMPLETE", ())), patch(
            "bilqis_mlx.runtime.priority_rejection_replay.rejection_recency",
            return_value=(None, ())):
        execute_horizon(
            Path("/tmp"), selection, NS(), parent, "atlas", "feature", direct, 1,
            cache, 1, None, 0, None, object(), NS(update=lambda **_: None),
            source_lane_cls=Lane, source_metrics_cls=lambda: object(),
            prepare_evidence_root=lambda _: None, capture_cls=lambda *a, **k: object(),
            delivery_observation_cls=observation, execute_candidate=execute_candidate,
            step_seed=lambda *a: 3, emit_progress=lambda *a: None,
            invalid=lambda reason: (_ for _ in ()).throw(AssertionError(reason)),
            observe_completed_step_fn=lambda *a: None,
        )

    assert observed == [(direct, enrichment)]
    assert candidate_calls[0]["prepared_source_rows"] == direct
    assert candidate_calls[0]["prepared_enrichment_rows"] == enrichment
