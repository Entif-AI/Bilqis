"""Content-addressed C05 identities for generation-independent evaluation work."""
from __future__ import annotations

import json

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.semantics.domains import contract_digest

from .factory_compiled_codec import decode_compiled_value, encode_compiled_value


CASE_SCHEMA = "bilqis.mlx.c05-compiled-evaluation-case/v1"
COHORT_SCHEMA = "bilqis.mlx.c05-compiled-evaluation-cohort/v1"
ARTIFACT_SCHEMA = "bilqis.mlx.c05-compiled-evaluation-artifact/v1"
_JSON_SUFFIX_LENGTH = len(".json")
_SHA256_HEX_LENGTH = 64
_SHA256_JSON_FILENAME_LENGTH = _SHA256_HEX_LENGTH + _JSON_SUFFIX_LENGTH
_CASE_FIELDS = (
    "factory_release_sha256", "semantic_catalog_sha256",
    "semantic_release_sha256", "source_artifact_sha256", "source_row_id",
    "source_row_sha256", "source_binding_sha256", "lowerer_sha256",
    "evaluator_policy_sha256", "compiler_sha256", "feature_schema_sha256",
    "compiled_frame_sha256",
    "goal_sha256", "source_family_id", "episode_id",
)
_TEXT_FIELDS = frozenset(("source_row_id", "source_family_id", "episode_id"))


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _sha256(value) -> bool:
    return (isinstance(value, str) and len(value) == _SHA256_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


def compiled_case_identity_record(**values) -> dict:
    """Return the gold-blind immutable identity of one compiled C05 case."""
    if set(values) != set(_CASE_FIELDS):
        _invalid("BAMF_C05_COMPILED_CASE_IDENTITY_FIELDS_INVALID")
    if (any(not isinstance(values[key], str) or not values[key]
            for key in _TEXT_FIELDS)
            or any(not _sha256(values[key])
                   for key in _CASE_FIELDS if key not in _TEXT_FIELDS)):
        _invalid("BAMF_C05_COMPILED_CASE_IDENTITY_INVALID")
    return {"schema": CASE_SCHEMA, **values}


def compiled_case_identity_digest(record: dict) -> str:
    if (not isinstance(record, dict) or record.get("schema") != CASE_SCHEMA
            or set(record) != {"schema", *_CASE_FIELDS}):
        _invalid("BAMF_C05_COMPILED_CASE_IDENTITY_INVALID")
    return contract_digest(record)


def compiled_frame_identity_digest(compiled_rows) -> str:
    """Hash the compiler's own canonical row identities, never packed raw bytes."""
    compiled_rows.__post_init__()
    return contract_digest({
        "schema": compiled_rows.schema_version,
        "row_cache_keys": tuple(row.cache_key for row in compiled_rows.rows),
        "padding_mask": compiled_rows.padding_mask,
    })


def compiled_source_cohort_digest(
        rows, *, generator_version: str, rubric_sha256: str, seed: int) -> str:
    """Bind reusable cohort membership without committing evaluator-private truth."""
    from .factory_task_template import _source_view

    rows = tuple(rows)
    if (not rows or not isinstance(generator_version, str) or not generator_version
            or not _sha256(rubric_sha256) or type(seed) is not int or seed < 0):
        _invalid("BAMF_C05_COMPILED_SOURCE_COHORT_INVALID")
    return contract_digest({
        "schema": "bilqis.mlx.c05-compiled-source-cohort/v1",
        "generator_version": generator_version,
        "rubric_sha256": rubric_sha256,
        "seed": seed,
        "rows": tuple(_source_view(row) for row in rows),
    })


def compiled_cohort_record(
        *, factory_release_sha256: str, semantic_catalog_sha256: str,
        source_cohort_sha256: str, source_seed: int,
        case_records: tuple[dict, ...],
        case_artifacts: tuple[str, ...] | None = None) -> dict:
    if (not all(_sha256(value) for value in (
            factory_release_sha256, semantic_catalog_sha256,
            source_cohort_sha256))
            or type(source_seed) is not int or source_seed < 0
            or not isinstance(case_records, tuple) or not case_records):
        _invalid("BAMF_C05_COMPILED_COHORT_IDENTITY_INVALID")
    cases = tuple(compiled_case_identity_digest(record) for record in case_records)
    artifacts = () if case_artifacts is None else case_artifacts
    if (type(artifacts) is not tuple or any(not _sha256(value) for value in artifacts)
            or artifacts and len(artifacts) != len(cases)):
        _invalid("BAMF_C05_COMPILED_COHORT_ARTIFACTS_INVALID")
    body = {
        "schema": COHORT_SCHEMA,
        "factory_release_sha256": factory_release_sha256,
        "semantic_catalog_sha256": semantic_catalog_sha256,
        "source_cohort_sha256": source_cohort_sha256,
        "source_seed": source_seed,
        "compiled_case_identity": list(case_records),
        "compiled_case_sha256": list(cases),
        "compiled_case_artifact_sha256": list(artifacts),
    }
    return {**body, "compiled_cohort_sha256": contract_digest(body)}


def _template_record(template) -> dict:
    return {
        "goal": encode_compiled_value(template.goal),
        "binding": encode_compiled_value(template.binding),
        "release_sha256": template.release_sha256,
        "capability_id": template.capability_id,
        "source_row_id": template.source_row_id,
        "source_row_sha256": template.source_row_sha256,
        "source_binding_sha256": template.source_binding_sha256,
        "source_family_id": template.source_family_id,
        "episode_id": template.episode_id,
        "lowerer_sha256": template.lowerer_sha256,
    }


def _template_from_record(record: dict):
    from .factory_task_template import FactoryTaskTemplate

    expected = {
        "goal", "binding", "release_sha256", "capability_id", "source_row_id",
        "source_row_sha256", "source_binding_sha256", "source_family_id",
        "episode_id", "lowerer_sha256",
    }
    if not isinstance(record, dict) or set(record) != expected:
        _invalid("BAMF_C05_COMPILED_CACHE_TEMPLATE_INVALID")
    return FactoryTaskTemplate(
        decode_compiled_value(record["goal"]),
        decode_compiled_value(record["binding"]),
        record["release_sha256"], record["capability_id"],
        record["source_row_id"], record["source_row_sha256"],
        record["source_binding_sha256"], record["source_family_id"],
        record["episode_id"], record["lowerer_sha256"])


def compiled_case_artifact_record(compiled_case) -> dict:
    """Serialize only reusable semantic/compiler state, never evaluator truth."""
    compiled_case.__post_init__()
    body = {
        "schema": ARTIFACT_SCHEMA,
        "identity": compiled_case.identity_record,
        "identity_sha256": compiled_case.identity_sha256,
        "compiled_rows": encode_compiled_value(compiled_case.compiled_rows),
        "compiler_configs": encode_compiled_value(compiled_case.compiler_configs),
        "source_asts": encode_compiled_value(compiled_case.source_asts),
        "partial_forest_receipts": encode_compiled_value(
            compiled_case.partial_forest_receipts),
        "task_template": _template_record(compiled_case.task_template),
    }
    return {**body, "artifact_sha256": contract_digest(body)}


def seal_compiled_case(run_dir, compiled_case) -> str:
    """Persist one immutable generation-independent compiled case by content."""
    from ._factory_fixed_school_io import fixed_school_root, read_projection, project_bytes
    from .capability_evaluation import _invalid

    record = compiled_case_artifact_record(compiled_case)
    raw = json.dumps(record, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = record["artifact_sha256"]
    filename = f"{digest}.json"
    with fixed_school_root(run_dir) as (root_fd, _identity):
        existing = read_projection(root_fd, "c05-compiled-cases", filename)
        if existing is None:
            project_bytes(root_fd, "c05-compiled-cases", filename, raw)
        elif existing != raw:
            _invalid("BAMF_C05_COMPILED_CASE_PROJECTION_DRIFT")
        if read_projection(root_fd, "c05-compiled-cases", filename) != raw:
            _invalid("BAMF_C05_COMPILED_CASE_PROJECTION_DRIFT")
    return digest


def _validate_artifact_record(record: dict, artifact_sha256: str) -> None:
    from .capability_evaluation import _invalid

    if (not isinstance(record, dict) or record.get("schema") != ARTIFACT_SCHEMA
            or record.get("artifact_sha256") != artifact_sha256
            or artifact_sha256 != contract_digest({
                key: value for key, value in record.items()
                if key != "artifact_sha256"})
            or record.get("identity_sha256")
            != compiled_case_identity_digest(record.get("identity"))):
        _invalid("BAMF_C05_COMPILED_CASE_ARTIFACT_DRIFT")


def load_compiled_case(run_dir, artifact_sha256: str, identity_sha256: str):
    """Cold-load one content-addressed case and re-run all structural invariants."""
    from ._factory_fixed_school_io import fixed_school_root, read_projection
    from .capability_evaluation import _invalid
    from .factory_evaluation_compiler import CompiledFactoryEvaluationCase

    if not _sha256(artifact_sha256) or not _sha256(identity_sha256):
        _invalid("BAMF_C05_COMPILED_CASE_POINTER_INVALID")
    with fixed_school_root(run_dir) as (root_fd, _identity):
        raw = read_projection(
            root_fd, "c05-compiled-cases", f"{artifact_sha256}.json")
    if raw is None:
        _invalid("BAMF_C05_COMPILED_CASE_ARTIFACT_MISSING")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _invalid("BAMF_C05_COMPILED_CASE_ARTIFACT_DRIFT")
        raise AssertionError
    _validate_artifact_record(record, artifact_sha256)
    if record["identity_sha256"] != identity_sha256:
        _invalid("BAMF_C05_COMPILED_CASE_POINTER_DRIFT")
    identity = record["identity"]
    items = tuple((key, value) for key, value in identity.items() if key != "schema")
    return CompiledFactoryEvaluationCase(
        compiled_rows=decode_compiled_value(record["compiled_rows"]),
        compiler_configs=decode_compiled_value(record["compiler_configs"]),
        source_asts=decode_compiled_value(record["source_asts"]),
        partial_forest_receipts=decode_compiled_value(
            record["partial_forest_receipts"]),
        task_template=_template_from_record(record["task_template"]),
        identity_items=items,
        identity_sha256=identity_sha256)


def seal_compiled_cohort(run_dir, record: dict) -> str:
    """Persist an auditable projection by content digest; never serialize gold."""
    from ._factory_fixed_school_io import fixed_school_root, read_projection, project_bytes
    from .capability_evaluation import _invalid

    if (not isinstance(record, dict) or record.get("schema") != COHORT_SCHEMA
            or record.get("compiled_cohort_sha256") != contract_digest({
                key: value for key, value in record.items()
                if key != "compiled_cohort_sha256"})):
        _invalid("BAMF_C05_COMPILED_COHORT_IDENTITY_INVALID")
    raw = json.dumps(
        record, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = record["compiled_cohort_sha256"]
    filename = f"{digest}.json"
    with fixed_school_root(run_dir) as (root_fd, _identity):
        existing = read_projection(root_fd, "c05-compiled-cohorts", filename)
        if existing is None:
            project_bytes(root_fd, "c05-compiled-cohorts", filename, raw)
        elif existing != raw:
            _invalid("BAMF_C05_COMPILED_COHORT_PROJECTION_DRIFT")
        if read_projection(root_fd, "c05-compiled-cohorts", filename) != raw:
            _invalid("BAMF_C05_COMPILED_COHORT_PROJECTION_DRIFT")
    return digest


def compiled_cohort_candidates(
        run_dir, *, source_cohort_sha256: str, factory_release_sha256: str,
        semantic_catalog_sha256: str, source_seed: int) -> tuple[dict, ...]:
    """Return intact historical manifests for one exact fixed-school source cohort."""
    from ._factory_fixed_school_io import fixed_school_root, projection_names, read_projection
    from .capability_evaluation import _invalid

    if (not all(_sha256(value) for value in (
            source_cohort_sha256, factory_release_sha256, semantic_catalog_sha256))
            or type(source_seed) is not int or source_seed < 0):
        _invalid("BAMF_C05_COMPILED_COHORT_LOOKUP_INVALID")
    records = []
    with fixed_school_root(run_dir) as (root_fd, _identity):
        for name in projection_names(root_fd, "c05-compiled-cohorts"):
            if (len(name) != _SHA256_JSON_FILENAME_LENGTH
                    or not name.endswith(".json")
                    or not _sha256(name[:-_JSON_SUFFIX_LENGTH])):
                continue
            raw = read_projection(root_fd, "c05-compiled-cohorts", name)
            try:
                record = json.loads(raw)
            except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
                _invalid("BAMF_C05_COMPILED_COHORT_PROJECTION_DRIFT")
            digest = record.get("compiled_cohort_sha256")
            if (digest != name[:-_JSON_SUFFIX_LENGTH] or digest != contract_digest({
                    key: value for key, value in record.items()
                    if key != "compiled_cohort_sha256"})):
                _invalid("BAMF_C05_COMPILED_COHORT_PROJECTION_DRIFT")
            if (record.get("source_cohort_sha256") == source_cohort_sha256
                    and record.get("factory_release_sha256") == factory_release_sha256
                    and record.get("semantic_catalog_sha256") == semantic_catalog_sha256
                    and record.get("source_seed") == source_seed):
                records.append(record)
    return tuple(records)


def load_compiled_cohort_cases(run_dir, record: dict):
    """Load all artifacts referenced by one verified cohort manifest."""
    identities = record.get("compiled_case_identity")
    identity_digests = record.get("compiled_case_sha256")
    artifacts = record.get("compiled_case_artifact_sha256")
    if (not isinstance(identities, list) or not isinstance(identity_digests, list)
            or not isinstance(artifacts, list) or not artifacts
            or len(identities) != len(identity_digests) or len(artifacts) != len(identities)
            or any(compiled_case_identity_digest(identity) != digest
                   for identity, digest in zip(identities, identity_digests))):
        from .capability_evaluation import _invalid
        _invalid("BAMF_C05_COMPILED_COHORT_POINTER_DRIFT")
    return tuple(load_compiled_case(run_dir, artifact, identity)
                 for artifact, identity in zip(artifacts, identity_digests))


__all__ = (
    "compiled_case_artifact_record", "compiled_case_identity_digest",
    "compiled_case_identity_record", "compiled_cohort_candidates",
    "compiled_frame_identity_digest",
    "compiled_source_cohort_digest",
    "compiled_cohort_record", "load_compiled_case",
    "load_compiled_cohort_cases", "seal_compiled_case", "seal_compiled_cohort",
)
