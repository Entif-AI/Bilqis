"""Native Factory OOM recovery on disposable, source-qualified B13 custody."""

BILQIS_LEAF_GATE_POLICY = "DETACHED_ONLY"

import json
import os
from pathlib import Path
from unittest.mock import patch

import mlx.core as mx
import pytest

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.candidate import step as candidate_step
from bilqis_mlx.runtime.atlas_memory_retry import CandidateMemoryExhausted
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_execution_feature_context, publish_initial_generation,
    record_bamf_rejection,
)
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_operator.session_parts.stop_receipt import (
    read_latest_run_stop_receipt, record_normal_stop_receipt, stop_resource_witness,
)
from bilqis_mlx.runtime.mlx_memory import training_memory_policy
from bilqis_mlx.runtime.tests.capability.factory.owner.bamf_c16_2c_witness_support import (
    SOURCE_SEED, bound_visit,
)
from bilqis_mlx.runtime.tests.capability.factory.retention.retention_throughput_profile import (
    _prepare_run, host_source_authority_patch,
)
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest

from .factory_training_execution_support import draw, observation


CAPABILITY = "B.AND"
MLX_OOM = "[malloc] Unable to allocate 4096 bytes."


@pytest.fixture(scope="module")
def disposable_run(tmp_path_factory):
    path = os.environ.get("BILQIS_A01_ATLAS_BUNDLE")
    if not path or not Path(path).is_dir() or not mx.metal.is_available():
        pytest.skip("Native OOM witness requires pinned A01 and Apple Metal")
    scratch = tmp_path_factory.mktemp("native-oom")
    root = Path.cwd()
    artifact = Path(path)

    def publish_fixture(run_dir, prepared):
        return publish_initial_generation(run_dir, prepared, reserve_gib=0.0)

    previous_device = mx.default_device()
    previous_limit = mx.set_memory_limit(24 * 1024 ** 3)
    mx.set_default_device(mx.gpu)
    try:
        with training_memory_policy(mx), host_source_authority_patch(), patch(
                "bilqis_mlx.runtime.bamf_first_student.publish_initial_generation",
                new=publish_fixture), patch.dict(
                    os.environ, BILQIS_DATA_PLANE=str(scratch / "plane.sqlite3")):
            run_dir, parent, context = _prepare_run(
                scratch, root, (root / "vendor/legacy-v16").resolve(), artifact)
            features = authenticate_bamf_execution_feature_context(
                parent, str(artifact), run_dir)
            feature = persist_feature_manifest(features.features, scratch / "features")
            yield run_dir, parent, context, artifact, feature.path
    finally:
        mx.set_default_device(previous_device)
        mx.set_memory_limit(previous_limit)


def _execute(disposable_run, *, fail_attempts, message, attempts):
    from types import SimpleNamespace

    from bilqis_mlx.runtime.factory_candidate_training import execute_factory_candidate_step

    run_dir, parent, context, artifact, feature_path = disposable_run
    bound, provenance, policy = bound_visit(parent, run_dir, CAPABILITY)
    rows, delivery = draw(SimpleNamespace(context=context), CAPABILITY, SOURCE_SEED, 4)
    _, observed = observation(run_dir, CAPABILITY, rows, SOURCE_SEED)
    gradient = candidate_step.execute_factory_logical_batch

    def inject(parameters, prepared, source_context, snapshot, generation, cache, plan,
               **kwargs):
        attempts.append((prepared, plan, cache.accepted_manifest_sha256))
        if len(attempts) <= fail_attempts:
            raise RuntimeError(message)
        return gradient(parameters, prepared, source_context, snapshot, generation,
                        cache, plan, **kwargs)

    def execute():
        with patch.object(candidate_step, "execute_factory_logical_batch", new=inject):
            return execute_factory_candidate_step(
                run_dir, context, parent, str(artifact), feature_path, rows,
                capability=CAPABILITY, delivery=delivery, requested_count=len(rows),
                source_seed=SOURCE_SEED, source_each=len(rows), optimizer_step_seed=17,
                visit_provenance=provenance, teacher_strategy=policy,
                teacher_hparams=parent.optimizer_hyperparameters, max_norm=1.0,
                observation=observed)

    return execute, bound.identity


def _assert_exact_retry(attempts):
    (first, original, parent), (second, retry, retry_parent) = attempts
    assert first is second
    assert retry_parent == parent
    assert original.groups == ((0, 1, 2, 3),)
    assert retry.groups == ((0, 1), (2, 3))
    for field in ("logical_row_ids", "source_digest", "generation_binding",
                  "optimizer_step_seed"):
        assert getattr(original, field) == getattr(retry, field)


def _assert_parent(run_dir, parent, pointer, identity):
    cold = load_accepted_generation(run_dir)
    assert (run_dir / "bamf-state.json").read_bytes() == pointer
    assert candidate_identity_digest(cold.retained_state) == identity
    assert cold.retained_state.optimizer_step == parent.retained_state.optimizer_step
    assert cold.retained_state.allocations.digest == parent.retained_state.allocations.digest
    assert cold.teacher_state == parent.teacher_state


def test_native_retry_completes_one_provisional_optimizer_transition(disposable_run):
    run_dir, parent, *_ = disposable_run
    pointer = (run_dir / "bamf-state.json").read_bytes()
    identity = candidate_identity_digest(parent.retained_state)
    attempts = []
    execute, _ = _execute(disposable_run, fail_attempts=1, message=MLX_OOM, attempts=attempts)
    step = execute()
    _assert_exact_retry(attempts)
    assert step.transaction.update_steps == 1
    assert len(step.transaction.training_authorities) == 1
    assert step.realized_cost["c08_oom_retries"] == 1
    _assert_parent(run_dir, parent, pointer, identity)


def test_native_exhaustion_is_durable_and_cold_resumes(disposable_run):
    run_dir, parent, *_ = disposable_run
    pointer = (run_dir / "bamf-state.json").read_bytes()
    identity = candidate_identity_digest(parent.retained_state)
    attempts = []
    execute, visit = _execute(disposable_run, fail_attempts=2, message=MLX_OOM, attempts=attempts)
    with pytest.raises(CandidateMemoryExhausted) as error:
        execute()
    _assert_exact_retry(attempts)
    evidence = {
        **error.value.to_record(), "capability": CAPABILITY, "visit_id": visit.visit_id,
        "teacher_visit": visit.to_record(), "selected_policy_key": visit.policy_key,
    }
    record_bamf_rejection(run_dir, parent, evidence)
    record_normal_stop_receipt(
        run_dir, parent, status="RESOURCE_HOLD", minutes=1, max_visits=0,
        steps_per_visit=1, reserve_gib=100, source_prefetch_workers=0,
        visits=0, accepted=0, rejected=0, elapsed_seconds=1.0, admission_status=None,
        admission_advances=0, resource_witness=stop_resource_witness(run_dir, 100))
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    rejections = [event for event in events if event["event"] == "BAMF_CANDIDATE_RESOURCE_REJECTED"]
    assert len(rejections) == 1
    assert rejections[0]["evidence"] == evidence
    stop = read_latest_run_stop_receipt(run_dir)
    assert stop["stop_reason"] == "RESOURCE_HOLD"
    assert stop["safe_resume_available"]
    _assert_parent(run_dir, parent, pointer, identity)


def test_unrelated_runtime_error_is_not_retried(disposable_run):
    attempts = []
    execute, _ = _execute(
        disposable_run, fail_attempts=1, message="source authority is no longer current",
        attempts=attempts)
    with pytest.raises(RuntimeError, match="source authority"):
        execute()
    assert len(attempts) == 1
