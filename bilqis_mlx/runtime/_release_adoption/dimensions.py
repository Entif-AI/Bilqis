"""Runtime policy for adopting Factory-compiled provider-dimension successors."""
from __future__ import annotations

import bilqis_mlx.factory.live_answers as _factory_live_answers
import bilqis_mlx.factory.provider_dimensions as _factory_provider_dimensions
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school


def advance_provider_dimensions(
        run_dir, receipt, grade_a_course, source_root, graph,
        course, release, program, *, adopt_executable_profile):
    """Compile and adopt at most one provider-authorized adjacent scope step."""
    if receipt.get("qualification") is not None:
        return receipt, course, release, program
    current = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    active = _factory_schedule.schedule_program_from_executable_release(current)
    school = _runtime_state._state_from_json(receipt["school"], active)
    if school.stage not in (
            "AWAITING_NEXT_GRADE", "AWAITING_NEXT_GRADE_WITH_DEBT"):
        return receipt, course, release, program
    state = _factory_provider_dimensions.next_automatic_provider_dimension(current)
    if state is None:
        return receipt, course, release, program
    transition = _factory_provider_dimensions.compile_provider_dimension_successor(
        current, state.dimension_id,
        _source_adapters_school.live_source_registry(),
        _factory_live_answers.live_answer_registry(),
        source_root=source_root, graph=graph,
        verification_seed=2026111701)
    if transition is None:
        return receipt, course, release, program
    return adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        transition.profile, compiled_successor=transition.release)


__all__ = ("advance_provider_dimensions",)
