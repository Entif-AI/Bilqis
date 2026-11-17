"""Boolean source construction, validation and optional teaching choices."""
from ...curriculum import BOOLEAN_OPERATORS
from ...live_grade_b import draw_connectives
from ...boolean_composite import CAPABILITY as B_COMPOSITE_CAPABILITY, draw_composite
from ...boolean_identification import CAPABILITY as B_IDBOOLOPS_CAPABILITY, draw_identification
from ...boolean_association import VERSION as BOOLEAN_ASSOCIATION_OPTION, draw_b_grade_bridges
from ..structure import inspect_boolean_identification, inspect_source_query
BOOLEAN_RUNTIME_SAMPLER = "bilqis.mlx.grade-b-u7c-runtime-sampler/v3"

def check_predicate(row, *, source_root, **_):
    from ...grade_a_oracle import evaluate
    from ...grade_a_probe import read_sources
    micro, development, *_ = read_sources(source_root)
    library = micro if row["record"]["task"] == "micro" else development
    return (evaluate(row["record"], row["capability"]) == row["gold"] and
            list(library.encode(row["record"])) == row["tokens"])


def check_connective(row, *, source_root, graph, **_):
    from ...grade_b_oracle import evaluate
    if row["record"].get("task") == "evaluate":
        from ...live_grade_b import _encode_logic_record, _logic_source
        logic = _logic_source(source_root)
        return (evaluate(row["record"], row["capability"]) == row["gold"] and
                _encode_logic_record(logic, row["record"], graph) == row["tokens"])
    from ...grade_a_probe import read_sources
    micro, *_ = read_sources(source_root)
    return (evaluate(row["record"], row["capability"]) == row["gold"] and
            list(micro.encode(row["record"])) == row["tokens"])


def check_boolean_composite(row, *, source_root, graph, **_):
    from ...boolean_composite_oracle import evaluate
    if row["record"].get("task") == "evaluate":
        from ...live_grade_b import _encode_logic_record, _logic_source
        logic = _logic_source(source_root)
        return (evaluate(row["record"], row["capability"]) == row["gold"] and
                _encode_logic_record(logic, row["record"], graph) == row["tokens"])
    from ...grade_a_probe import read_sources
    micro, *_ = read_sources(source_root)
    return (evaluate(row["record"], row["capability"]) == row["gold"] and
            list(micro.encode(row["record"])) == row["tokens"])


def semantic_footprint(row: dict) -> tuple[str, ...]:
    """Inspect source operations and omit literal/entity/codec representation."""
    record = row["record"]
    if record.get("task") == "identify_boolean_operator":
        from ...boolean_identification_oracle import evaluate
        root = "cogal.operator." + evaluate(record, row["capability"])
        shape = inspect_boolean_identification(record, root)
    else:
        shape = inspect_source_query(record["query"])
    return tuple(dict.fromkeys(shape.rooted_operators))


def classify_boolean_expression_weakness(row: dict) -> dict:
    """Describe composite/inverse Boolean structure without generated row identity."""
    record = row.get("record")
    if not isinstance(record, dict):
        from bilqis_mlx.errors import ErrorBus, FACTORY
        ErrorBus.Raise(
            FACTORY.WEAKNESS.INVALID,
            reason="FACTORY_BOOLEAN_WEAKNESS_RECORD_INVALID")
    if row.get("capability") == B_IDBOOLOPS_CAPABILITY:
        from ...boolean_identification_oracle import evaluate
        root = "cogal.operator." + evaluate(record, row["capability"])
        shape = inspect_boolean_identification(record, root)
        family = "boolean-identification"
    else:
        shape = inspect_source_query(record.get("query"))
        family = "boolean-composite"
    return {
        "family": family,
        "root": shape.root,
        "rooted_operators": list(shape.rooted_operators),
        "semantic_operations": shape.semantic_operations,
        "operator_depth": shape.operator_depth,
        "answer_kind": row.get("answer_kind", "binary"),
    }


def draw_b(*, source_root, graph, course, capability, seed, each):
    del course
    rows = draw_connectives(source_root, graph, seed=seed,
                            capability=capability, each=each)
    return tuple({**row, "runtime_sampler": BOOLEAN_RUNTIME_SAMPLER}
                 for row in rows)


def _boolean_profile_operators(
        profile_parameters, *, capability, scoped_capabilities) -> tuple[str, ...]:
    parameters = profile_parameters or {}
    if set(parameters) - {"operators"}:
        raise ValueError("FACTORY_BOOLEAN_PROFILE_PARAMETER_UNKNOWN")
    if parameters and capability not in scoped_capabilities:
        raise ValueError("FACTORY_BOOLEAN_PROFILE_PARAMETER_SCOPE_DRIFT")
    return tuple(parameters.get("operators", BOOLEAN_OPERATORS))


def draw_b_composite_release(*, source_root, graph, course, capability, seed, each,
                             profile_parameters=None):
    operators = _boolean_profile_operators(
        profile_parameters, capability=capability,
        scoped_capabilities={B_COMPOSITE_CAPABILITY})
    if capability == B_COMPOSITE_CAPABILITY:
        return draw_composite(source_root, graph, seed=seed,
                              capability=capability, each=each,
                              operators=operators)
    return draw_b(source_root=source_root, graph=graph, course=course,
                  capability=capability, seed=seed, each=each)


def check_b_composite_release(row, **kwargs):
    if row.get("capability") == B_COMPOSITE_CAPABILITY:
        return check_boolean_composite(row, **kwargs)
    return check_connective(row, **kwargs)


def draw_b_idboolops_release(*, source_root, graph, course, capability, seed, each,
                             profile_parameters=None):
    operators = _boolean_profile_operators(
        profile_parameters, capability=capability,
        scoped_capabilities={B_COMPOSITE_CAPABILITY, B_IDBOOLOPS_CAPABILITY})
    if capability == B_IDBOOLOPS_CAPABILITY:
        return draw_identification(source_root, graph, seed=seed,
                                   capability=capability, each=each,
                                   operators=operators)
    if capability == B_COMPOSITE_CAPABILITY:
        return draw_composite(source_root, graph, seed=seed,
                              capability=capability, each=each,
                              operators=operators)
    return draw_b(source_root=source_root, graph=graph, course=course,
                  capability=capability, seed=seed, each=each)


def check_b_idboolops_release(row, **kwargs):
    if row.get("capability") == B_IDBOOLOPS_CAPABILITY:
        from ...boolean_identification import encode_record
        from ...boolean_identification_oracle import evaluate
        return (
            evaluate(row["record"], row["capability"]) == row["gold"] and
            encode_record(
                row["record"], kwargs["source_root"], kwargs["graph"]) ==
            row["tokens"])
    if row.get("capability") == B_COMPOSITE_CAPABILITY:
        return check_boolean_composite(row, **kwargs)
    return check_connective(row, **kwargs)


def enrich_boolean(*, source_root, graph, course, capability, seed, option_id):
    if option_id != BOOLEAN_ASSOCIATION_OPTION:
        raise ValueError("FACTORY_UNKNOWN_BOOLEAN_TEACHING_OPTION")
    course.capability_map[capability]
    numeric_caps = [member for member in course.capability_map.values()
                    if any(family.kind == "numeric_active"
                           for family in member.answer_families)]
    if not numeric_caps:
        raise ValueError("BOOLEAN_ASSOCIATION_REQUIRES_NUMERIC_SOURCE_ADAPTER")
    maximum = max(
        len(next(family for family in member.answer_families
                 if family.kind == "numeric_active").values) - 1
        for member in numeric_caps)
    return draw_b_grade_bridges(
        source_root, graph, seed=seed, maximum=maximum,
        per_source=4, capability=capability)
