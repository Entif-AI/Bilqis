"""C08.4 distributed execution is selectable at the human-started operator boundary."""
from pathlib import Path
import pickle
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.runtime.bamf_operator import session
from bilqis_mlx.runtime.atlas_resources import DistributedRank
from bilqis_mlx.runtime.c08_distributed_executor import (
    DistributedExecutorBinding, configure_mlx_distributed_execution,
)
from bilqis_mlx.runtime.c08_distributed_capsule import (
    PortableSourceContext, issue_distributed_factory_step_capsule,
)


class DistributedResourceModeTests(unittest.TestCase):
    @staticmethod
    def _process(returncode=0, stdout="", stderr=""):
        process = Mock()
        process.returncode = returncode
        process.communicate.return_value = (stdout, stderr)
        return process

    def _binding(self):
        workers = (
            DistributedRank(0, "rank-0", "Apple M3 Ultra"),
            DistributedRank(1, "rank-1", "Apple M2 Ultra"))
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor."
                "require_distributed_backend", return_value="ring"), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor.version",
                    return_value="0.test"):
            return configure_mlx_distributed_execution(
                workers, hosts=("127.0.0.1",), partition_seed=17,
                backend="ring", python_executable="/python",
                working_directory="/repo")

    def test_executor_binding_is_owner_issued_worker_cohort(self):
        workers = (
            DistributedRank(0, "rank-0", "Apple M3 Ultra"),
            DistributedRank(1, "rank-1", "Apple M2 Ultra"))
        with self.assertRaises(Exception):
            DistributedExecutorBinding()
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor."
                "require_distributed_backend", return_value="ring"), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor.version",
                    return_value="0.test"):
            binding = configure_mlx_distributed_execution(
                workers, hosts=("127.0.0.1",), partition_seed=17,
                backend="ring", python_executable="/python",
                working_directory="/repo")
        self.assertEqual(len(binding.profile.workers), 2)
        self.assertEqual(binding.profile.mlx_version, "0.test")
        command = binding._command(
            Path("/tmp/request"), Path("/tmp/response"), "a" * 64)
        self.assertIn("mlx.launch", command)
        self.assertIn("-n", command)
        self.assertIn("2", command)
        self.assertIn("c08_distributed_worker", " ".join(command))

    def test_executor_requires_coordinator_local_rank_zero(self):
        workers = (
            DistributedRank(0, "rank-0", "Apple M3 Ultra"),
            DistributedRank(1, "rank-1", "Apple M2 Ultra"))
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor."
                "require_distributed_backend", return_value="ring"), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor.version",
                    return_value="0.test"):
            with self.assertRaises(Exception):
                configure_mlx_distributed_execution(
                    workers, hosts=("remote.example", "127.0.0.1"),
                    partition_seed=17, backend="ring")

    def test_worker_oom_preserves_native_runtime_error_retry_signal(self):
        binding = self._binding()
        failure = self._process(
            returncode=1, stderr="[malloc] Unable to allocate 4096 bytes.\n")
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor.subprocess.Popen",
                return_value=failure), self.assertRaisesRegex(
                    RuntimeError, "Unable to allocate 4096 bytes"):
            binding._run_capsule({"kind": "collective-probe"})

    def test_non_oom_worker_failure_remains_fail_closed(self):
        binding = self._binding()
        failure = self._process(returncode=1, stderr="rank crashed")
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor.subprocess.Popen",
                return_value=failure), self.assertRaises(Exception) as caught:
            binding._run_capsule({"kind": "collective-probe"})
        self.assertNotIsInstance(caught.exception, RuntimeError)

    def test_worker_cohort_timeout_fails_closed(self):
        binding = self._binding()
        failure = self._process()
        failure.pid = 999999
        failure.communicate.side_effect = subprocess.TimeoutExpired(
            ("mlx.launch",), 1.0)
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor.subprocess.Popen",
                return_value=failure), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor._terminate_cohort"), \
                self.assertRaises(Exception) as caught:
            binding._run_capsule({"kind": "collective-probe"})
        self.assertNotIsInstance(caught.exception, RuntimeError)

    def test_worker_cohort_timeout_must_be_finite(self):
        workers = (
            DistributedRank(0, "rank-0", "Apple M3 Ultra"),
            DistributedRank(1, "rank-1", "Apple M3 Ultra"))
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor."
                "require_distributed_backend", return_value="ring"), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor.version",
                    return_value="0.test"):
            for invalid in (float("inf"), float("nan")):
                with self.subTest(invalid=invalid), self.assertRaises(Exception):
                    configure_mlx_distributed_execution(
                        workers, hosts=("127.0.0.1",), partition_seed=17,
                        backend="ring", worker_timeout_seconds=invalid)

    def test_timeout_terminates_launcher_process_group_children(self):
        with TemporaryDirectory() as root:
            pid_file = Path(root) / "child.pid"
            binding = self._binding()
            object.__setattr__(binding, "working_directory", str(Path.cwd()))
            object.__setattr__(binding, "worker_timeout_seconds", 1.0)
            code = (
                "import pathlib,subprocess,sys,time;"
                "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
                f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid));"
                "time.sleep(60)"
            )
            with patch.object(
                    DistributedExecutorBinding, "_command",
                    return_value=[sys.executable, "-c", code]), \
                    self.assertRaises(Exception):
                binding._run_capsule({"kind": "collective-probe"})
            child_pid = int(pid_file.read_text())
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                probe = subprocess.run(
                    ["ps", "-p", str(child_pid), "-o", "pid="],
                    capture_output=True, text=True)
                if not probe.stdout.strip():
                    break
                time.sleep(0.02)
            self.assertFalse(probe.stdout.strip(), "orphaned rank child survived timeout")

    def test_factory_capsule_strips_process_live_owner_state_before_pickle(self):
        from bilqis_mlx.runtime.training_objective import current_training_objective

        compiled_value = SimpleNamespace(
            compiled="rows", compiler_configs=("config",), features="features",
            extents="extents", source_asts=None, partial_forest_receipts=None)
        active = SimpleNamespace(
            run_id="run", generation=3, active_indices=(1, 2))
        compiled = SimpleNamespace(
            compiled=compiled_value, sources=("source",), feature_schema="schema",
            active_semantic_rows=active)
        provenance = SimpleNamespace(
            row_id="row", source_row_content_sha256="d" * 64, source_id=None,
            capability_id="A.TEST", operation_id=None, teacher_strategy=(),
            requested_count=1, delivered_count=1, rehearsal=None,
            optimizer_step_seed=7, source_family_id=None, episode_id=None,
            immediate_dependencies=(),
            visit=SimpleNamespace(
                to_c03_record=lambda: {"schema": "portable-test"}))
        training_row = SimpleNamespace(
            model_input="input", target="target", native_target=None,
            provenance=provenance, auxiliaries=(), rule_policy=())
        prepared = SimpleNamespace(
            training_batch=SimpleNamespace(
                release_sha256="a" * 64, generation_binding="b" * 64,
                delivered_content_sha256="c" * 64, delivery_capability="A.TEST",
                rows=(training_row,)),
            compiled_rows=(compiled,))
        source_context = SimpleNamespace(
            release="release", graph={"x": 1}, source_root=Path("/source"),
            _execution_by_capability=MappingProxyType({"x": "owner"}))
        cache = SimpleNamespace(unpickleable=MappingProxyType({"x": "cache"}))
        with patch(
                "bilqis_mlx.runtime.c08_distributed_capsule."
                "issue_distributed_execution_cache_witness",
                return_value="portable-witness"):
            capsule = issue_distributed_factory_step_capsule(
                parameters={"p": 1}, prepared=prepared,
                source_context=source_context, feature_snapshot="snapshot",
                generation="b" * 64, cache=cache, resource_plan="plan",
                manifest=SimpleNamespace(
                    training_objective_digest=current_training_objective().digest))
        payload = pickle.dumps(capsule, protocol=5)
        restored = pickle.loads(payload)
        self.assertEqual(restored.cache_witness, "portable-witness")
        self.assertFalse(hasattr(restored.source_context, "_execution_by_capability"))

    def test_portable_source_context_revalidates_remote_implementations(self):
        source_registry = object()
        answer_registry = object()
        context = Mock()
        context.__post_init__ = Mock()
        with patch(
                "bilqis_mlx.runtime.c08_distributed_capsule.live_source_registry",
                return_value=source_registry), patch(
                    "bilqis_mlx.runtime.c08_distributed_capsule.live_answer_registry",
                    return_value=answer_registry), patch(
                        "bilqis_mlx.runtime.c08_distributed_capsule."
                        "verify_current_implementations") as verify, patch(
                            "bilqis_mlx.runtime.c08_distributed_capsule."
                            "SourceExecutionContext", return_value=context):
            result = PortableSourceContext(
                "release", {"graph": 1}, "/source").materialize()
        verify.assert_called_once_with("release", source_registry, answer_registry)
        self.assertIs(result, context)
        context.__post_init__.assert_called_once_with()

    def test_portable_source_context_rejects_remote_implementation_drift(self):
        with patch(
                "bilqis_mlx.runtime.c08_distributed_capsule.live_source_registry",
                return_value=object()), patch(
                    "bilqis_mlx.runtime.c08_distributed_capsule.live_answer_registry",
                    return_value=object()), patch(
                        "bilqis_mlx.runtime.c08_distributed_capsule."
                        "verify_current_implementations",
                        side_effect=RuntimeError("implementation drift")), \
                self.assertRaisesRegex(RuntimeError, "implementation drift"):
            PortableSourceContext(
                "release", {"graph": 1}, "/source").materialize()

    def test_operator_can_derive_profile_from_bound_executor(self):
        workers = (
            DistributedRank(0, "rank-0", "Apple M3 Ultra"),
            DistributedRank(1, "rank-1", "Apple M2 Ultra"))
        with patch(
                "bilqis_mlx.runtime.c08_distributed_executor."
                "require_distributed_backend", return_value="ring"), patch(
                    "bilqis_mlx.runtime.c08_distributed_executor.version",
                    return_value="0.test"):
            binding = configure_mlx_distributed_execution(
                workers, hosts=("127.0.0.1",), partition_seed=17,
                backend="ring")

        def operate_impl(*_args, visit_fn, **_kwargs):
            with patch.object(session, "_visit", return_value="VISIT") as visit:
                visit_fn(Path("/run"), 100.0)
            visit.assert_called_once_with(
                Path("/run"), 100.0, distributed_profile=binding.profile,
                distributed_executor=binding)
            return "RESULT"

        with patch.object(session, "_operate_impl", side_effect=operate_impl):
            self.assertEqual(session.operate_bamf(
                Path("/run"), minutes=1, source_prefetch_workers=0,
                distributed_executor=binding), "RESULT")

    def test_visit_threads_distributed_mode_into_prepared_visit(self):
        profile = object()
        executor = object()
        with patch.object(session, "_visit_impl", return_value="VISIT") as visit_impl, \
                patch.object(session, "prepare_bamf_visit", return_value="PREPARED") as prepare:
            self.assertEqual(
                session._visit(
                    Path("/run"), 100.0, steps_per_visit=1, progress=None,
                    source_prefetch_workers=0, distributed_profile=profile,
                    distributed_executor=executor),
                "VISIT")
            bound_prepare = visit_impl.call_args.kwargs["prepare_visit"]
            self.assertEqual(bound_prepare(Path("/run"), steps_per_visit=1), "PREPARED")
        prepare.assert_called_once_with(
            Path("/run"), steps_per_visit=1,
            distributed_profile=profile, distributed_executor=executor)

    def test_operator_public_mode_binds_visit_function(self):
        profile = object()
        executor = object()

        def operate_impl(*_args, visit_fn, **_kwargs):
            with patch.object(session, "_visit", return_value="VISIT") as visit:
                self.assertEqual(visit_fn(Path("/run"), 100.0), "VISIT")
            visit.assert_called_once_with(
                Path("/run"), 100.0,
                distributed_profile=profile, distributed_executor=executor)
            return "RESULT"

        with patch.object(session, "_operate_impl", side_effect=operate_impl):
            self.assertEqual(
                session.operate_bamf(
                    Path("/run"), minutes=1, source_prefetch_workers=0,
                    distributed_profile=profile, distributed_executor=executor),
                "RESULT")


if __name__ == "__main__":
    unittest.main()
