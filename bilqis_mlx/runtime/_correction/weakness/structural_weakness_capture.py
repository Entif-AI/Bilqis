"""Compile and currentness-check provider-owned R13 weakness classes."""
from __future__ import annotations

from bilqis_mlx.factory._model.weakness import WeaknessClassId, classify_weakness
from .structural_weakness_contracts import (
    EVIDENCE_SCHEMA, SHA256_LENGTH, _digest, _invalid,
    issue_weakness_context, validate_weakness_evidence,
)


def _selected_rows(payload: dict, capability: str) -> tuple[dict, ...]:
    objects = payload.get("source_objects")
    rows = []
    if not isinstance(objects, dict):
        _invalid("BAMF_WEAKNESS_CANDIDATE_EVIDENCE_INVALID")
    for step in payload.get("steps", ()):
        for position in step.get("positions", ()):
            if "selected_option" not in position.get("roles", ()):
                continue
            row = objects.get(position.get("row"))
            if isinstance(row, dict) and row.get("capability") == capability:
                rows.append(row)
    return tuple(rows)


def _provider_for_context(source_context, capability: str):
    from bilqis_mlx.factory.generation_compat import runtime_adapter_for_release

    execution = source_context.execution_for(capability)
    adapter = runtime_adapter_for_release(
        source_context.source_root, source_context.graph, source_context.release,
        source_context.source_registry, execution,
        drift_code="BAMF_WEAKNESS_PROVIDER_DRIFT")
    admitted = next((
        item for item in source_context.release.source_adapters
        if item.adapter_id == execution.provider_id
    ), None)
    if admitted is None:
        _invalid("BAMF_WEAKNESS_PROVIDER_UNADMITTED")
    return execution, adapter, admitted


def _source_context_matches(context: dict, source_context, capability: str) -> bool:
    from dataclasses import asdict
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext
    from bilqis_mlx.runtime.state import _fingerprint

    if source_context.release.release_sha256 != context["factory_release_sha256"]:
        return False
    binding = source_context.release.source_bindings.by_capability.get(capability)
    if binding is None or _fingerprint(asdict(binding)) != context["source_binding_sha256"]:
        return False
    if isinstance(source_context, SourceExecutionContext) and source_context.run_dir is not None:
        source_context.require_accepted_runtime(source_context.run_dir)
    return True


def derive_rejected_weaknesses(
        run_dir, source_context, selection, candidate_evidence: dict, *,
        rejection_reason: str, outcome_sha256: str,
) -> tuple[dict, ...]:
    """Compile provider-declared classes from one validated rejected horizon."""
    from bilqis_mlx.runtime.bamf_operator.evidence_validation import (
        read_candidate_horizon_evidence,
    )
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext

    if not isinstance(source_context, SourceExecutionContext):
        return ()
    context = issue_weakness_context(selection)
    capability = context["capability_id"]
    if source_context.release.release_sha256 != context["factory_release_sha256"]:
        _invalid("BAMF_WEAKNESS_RELEASE_DRIFT")
    payload = read_candidate_horizon_evidence(run_dir, candidate_evidence)
    if (payload.get("proposal", {}).get("how_context")
            != selection.metadata.get("how_context")):
        _invalid("BAMF_WEAKNESS_CANDIDATE_EVIDENCE_DRIFT")
    execution, adapter, admitted = _provider_for_context(
        source_context, capability)
    if admitted.weakness_classifier_id is None:
        return ()
    classes = {}
    for row in _selected_rows(payload, capability):
        if adapter.check(
                row, source_root=source_context.source_root,
                graph=source_context.graph,
                course=source_context.release.curriculum) is not True:
            _invalid("BAMF_WEAKNESS_SOURCE_VALIDATION_FAILED")
        weakness = classify_weakness(
            adapter, execution, row, provider_descriptor=admitted)
        if weakness is not None:
            classes[weakness.class_sha256] = weakness
    candidate_sha256 = candidate_evidence.get("object", {}).get("sha256")
    if (classes and (not isinstance(candidate_sha256, str)
                     or len(candidate_sha256) != SHA256_LENGTH
                     or not isinstance(outcome_sha256, str)
                     or len(outcome_sha256) != SHA256_LENGTH
                     or not isinstance(rejection_reason, str)
                     or not rejection_reason)):
        _invalid("BAMF_WEAKNESS_EVIDENCE_PROVENANCE_INVALID")
    result = []
    for weakness in sorted(classes.values(), key=lambda item: item.class_sha256):
        record = {
            "schema": EVIDENCE_SCHEMA,
            "state": "UNRESOLVED",
            "freshness": "FRESH_EQUIVALENT_REQUIRED",
            "capability_id": capability,
            "weakness_class": weakness.to_record(),
            "context": context,
            "candidate_evidence_sha256": candidate_sha256,
            "outcome_sha256": outcome_sha256,
            "retention_reason": rejection_reason,
        }
        record["weakness_evidence_sha256"] = _digest(record)
        result.append(record)
    return tuple(result)


def weakness_is_current(wrapper: dict, source_context, selection) -> bool:
    record = wrapper.get("weakness") if isinstance(wrapper, dict) else None
    if not isinstance(record, dict):
        return False
    validate_weakness_evidence(record)
    current = issue_weakness_context(selection)
    if record["context"] != current:
        return False
    weakness = WeaknessClassId.from_record(record["weakness_class"])
    capability = record["capability_id"]
    if not _source_context_matches(current, source_context, capability):
        return False
    try:
        execution, adapter, admitted = _provider_for_context(
            source_context, capability)
    except ValueError:
        return False
    return (
        execution.provider_id == weakness.provider_id
        and execution.provider_implementation_sha256
        == weakness.provider_implementation_sha256
        and admitted.weakness_classifier_id == weakness.classifier_id
        and admitted.weakness_classifier_sha256 == weakness.classifier_sha256
        and adapter.descriptor.weakness_classifier_id == weakness.classifier_id
        and adapter.descriptor.weakness_classifier_sha256
        == weakness.classifier_sha256
        and callable(adapter.weakness_classifier)
    )


__all__ = ("derive_rejected_weaknesses", "weakness_is_current")
