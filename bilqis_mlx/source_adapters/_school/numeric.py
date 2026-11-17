"""Finite numeric source construction and obligation witnesses."""
from ...live_grade_c import PLANS
from ...numeric_curriculum import draw_numeric
from ..numeric import (
    check_numeric, classify_numeric_weakness, semantic_footprint,
)

def draw_c(*, source_root, graph, course, capability, seed, each,
           profile_parameters=None):
    parameters = profile_parameters or {}
    if set(parameters) - {"numbers"}:
        raise ValueError("FACTORY_NUMERIC_PROFILE_PARAMETER_UNKNOWN")
    if "numbers" in parameters:
        numbers = tuple(parameters["numbers"])
        if numbers != tuple(str(index) for index in range(len(numbers))):
            raise ValueError("FACTORY_NUMERIC_PROFILE_DOMAIN_INVALID")
        maximum = len(numbers) - 1
    else:
        cap = course.capability_map[capability]
        numeric = next((family for family in cap.answer_families
                        if family.kind == "numeric_active"), None)
        if numeric is None:
            raise ValueError("FACTORY_NUMERIC_CAPABILITY_HAS_NO_ACTIVE_DOMAIN")
        maximum = len(numeric.values) - 1
    return draw_numeric(PLANS, graph, seed=seed, maximum=maximum,
                        capability=capability, each=each)


def witness_numeric_obligation(row, obligation, *, source_root, graph, course):
    """Certify finite-numeric dependency transfer from the source lesson plan."""
    del source_root, graph
    capability = row.get("capability")
    plan = next((item for item in PLANS if item.capability == capability), None)
    if (plan is None or row.get("lesson_id") != plan.lesson_id or
            capability not in course.capability_map):
        raise ValueError("FACTORY_NUMERIC_EVIDENCE_PLAN_DRIFT")
    kind = getattr(getattr(obligation, "kind", None), "value", None)
    if kind == "PREREQUISITE":
        return getattr(obligation, "key", None) in plan.prerequisites
    if kind == "COMPOSITION":
        return getattr(obligation, "key", None) in course.capability_map[
            capability].composed_of
    raise ValueError("FACTORY_NUMERIC_EVIDENCE_KIND_UNSUPPORTED")
