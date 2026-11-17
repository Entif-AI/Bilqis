"""Immutable source policy for truth-pattern and structural replay."""
from dataclasses import dataclass as _dataclass
from typing import Callable as _Callable
from ...curriculum import BOOLEAN_SIGNATURE_OPERAND_COUNT
from ...errors import ErrorBus, SOURCE
from ...grade_b_oracle import _direct_truth, evaluate as grade_b_gold, operand_truth
from ...live_grade_b import _u7c_pattern_counts
from .boolean import BOOLEAN_RUNTIME_SAMPLER

TRUTH_PATTERNS = ((False, False), (False, True), (True, False), (True, True))
_U7C_RUNTIME_SAMPLER = BOOLEAN_RUNTIME_SAMPLER
_DIRECT_BOOLEAN_UNIVERSE = "DIRECT_BOOLEAN_AST"


def _is_direct_u7c_row(row: dict) -> bool:
    record = row.get("record") if isinstance(row, dict) else None
    return (isinstance(record, dict) and record.get("task") == "evaluate" and
            row.get("runtime_sampler") == _U7C_RUNTIME_SAMPLER)


def _preservation_pattern_counts(capability: str, rows, *, each: int) -> dict:
    relevant = [row for row in rows if row.get("capability") == capability]
    if relevant and all(_is_direct_u7c_row(row) for row in relevant):
        try:
            return _u7c_pattern_counts(capability.removeprefix("B."), each)
        except ValueError as exc:
            raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_U7C_PATTERN_CONTRACT_INVALID) from exc
    if any(_is_direct_u7c_row(row) for row in relevant):
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_MIXED_REPRESENTATION)
    return {pattern: 1 for pattern in TRUTH_PATTERNS}


def _replay_operand_pattern(record: dict) -> list[bool]:
    """Recompute OR/XOR operand truth for historical worlds or direct U7C ASTs."""
    if not isinstance(record, dict):
        raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT)
    if record.get("task") == "evaluate":
        expression = record.get("expression")
        query = record.get("query")
        assignments = record.get("assignments")
        if (not isinstance(expression, dict) or expression != query or
                not isinstance(assignments, dict)):
            raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT)
        args = expression.get("args")
        if not isinstance(args, list) or len(args) != BOOLEAN_SIGNATURE_OPERAND_COUNT:
            raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT)
        try:
            return [_direct_truth(arg, assignments) for arg in args]
        except ValueError as exc:
            raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT) from exc
    if record.get("task") == "micro":
        world = record.get("world")
        query = record.get("query")
        args = query.get("args") if isinstance(query, dict) else None
        if not isinstance(world, dict) or not isinstance(args, list) or len(args) != BOOLEAN_SIGNATURE_OPERAND_COUNT:
            raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT)
        try:
            return [operand_truth(world, arg) for arg in args]
        except ValueError as exc:
            raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT) from exc
    raise ErrorBus.legacy_error(SOURCE.REPLAY.REPLAY_ORACLE_OR_COMPOSITION_DRIFT)


def _operand_kind(node: dict) -> str:
    kind = node.get("kind")
    if kind == "compare":
        value = node.get("operator")
    elif kind == "relation":
        value = node.get("name")
    else:
        value = kind
    if not isinstance(value, str) or not value:
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_OPERAND_KIND_INVALID)
    return value


def structural_signature(row: dict) -> tuple:
    """Describe the compositional shape that truth-pattern-only replay misses."""
    capability = row.get("capability")
    raw = row.get("operand_truths")
    record = row.get("record") or {}
    query = record.get("query") or {}
    args = query.get("args")
    universe = (_DIRECT_BOOLEAN_UNIVERSE if _is_direct_u7c_row(row)
                else row.get("universe_size"))
    if (not isinstance(capability, str) or not capability or
            not isinstance(raw, (list, tuple)) or len(raw) != BOOLEAN_SIGNATURE_OPERAND_COUNT or
            any(type(value) is not bool for value in raw) or
            not isinstance(args, list) or len(args) != BOOLEAN_SIGNATURE_OPERAND_COUNT or
            (universe != _DIRECT_BOOLEAN_UNIVERSE and
             (type(universe) is not int or universe < 1))):
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_STRUCTURAL_SIGNATURE_INVALID)
    return (capability, tuple(raw), tuple(_operand_kind(arg) for arg in args),
            universe)


def classify_boolean_connective_weakness(row: dict) -> dict:
    """Provider-owned ADR-091 class for direct Boolean connective structure."""
    capability, truth_pattern, operand_kinds, universe = structural_signature(row)
    del capability
    return {
        "family": "boolean-connective",
        "truth_pattern": list(truth_pattern),
        "operand_kinds": list(operand_kinds),
        "universe": universe,
    }



def _fragile_row_pattern(row):
    raw = row.get("operand_truths")
    if (not isinstance(raw, (list, tuple)) or len(raw) != BOOLEAN_SIGNATURE_OPERAND_COUNT or
            any(type(value) is not bool for value in raw)):
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_OPERAND_PATTERN_INVALID)
    pattern = tuple(raw)
    if pattern not in TRUTH_PATTERNS:
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_SOURCE_GOLD_DRIFT)
    return pattern


def _fragile_eligible(row):
    return (isinstance(row.get("capability"), str) and
            isinstance(row.get("operand_truths"), (list, tuple)) and
            len(row.get("operand_truths")) == BOOLEAN_SIGNATURE_OPERAND_COUNT)


def _fragile_verify_row(row, capability):
    return (row.get("operand_truths") == _replay_operand_pattern(row["record"]) and
            grade_b_gold(row["record"], capability) == row["gold"] and bool(row.get("tokens")))


def _fragile_structural_capability(rows, limit):
    capabilities = {row.get("capability") for row in rows}
    if (len(capabilities) != 1 or limit < len(TRUTH_PATTERNS)
            or limit % BOOLEAN_SIGNATURE_OPERAND_COUNT):
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_U7C_STRUCTURAL_REQUEST_INVALID)
    return next(iter(capabilities))


def _fragile_matching_keys(signature):
    return signature, signature[:3], signature[:2]


@_dataclass(frozen=True)
class _FragileSourcePolicy:
    is_exact: _Callable[[dict], bool]
    pattern_counts: _Callable[..., dict]
    row_pattern: _Callable[[dict], tuple[bool, bool]]
    eligible: _Callable[[dict], bool]
    verify_row: _Callable[[dict, str], bool]
    signature: _Callable[[dict], tuple]
    structural_capability: _Callable[[tuple[dict, ...], int], str]
    matching_keys: _Callable[[tuple], tuple[tuple, ...]]
    answer_values: tuple[str, ...]


_FRAGILE_SOURCE_POLICY = _FragileSourcePolicy(
    _is_direct_u7c_row, _preservation_pattern_counts, _fragile_row_pattern,
    _fragile_eligible, _fragile_verify_row, structural_signature,
    _fragile_structural_capability, _fragile_matching_keys, ("TRUE", "FALSE"))


def fragile_source_policy(selector: str):
    """Resolve the existing source selector to its immutable semantic callbacks."""
    if selector != BOOLEAN_RUNTIME_SAMPLER:
        raise ErrorBus.legacy_error(SOURCE.REPLAY.PRESERVATION_SOURCE_POLICY_UNKNOWN)
    return _FRAGILE_SOURCE_POLICY

_FragileSourcePolicy.__module__ = "bilqis_mlx.source_adapters.school"
