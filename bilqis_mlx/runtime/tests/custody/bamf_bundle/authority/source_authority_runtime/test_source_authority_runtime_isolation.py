"""Accepted-run custody for opaque C09 source authority."""
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.atlas_revalidation import (
    SourceAuthorityRegistry,
    SourceAuthorityRuntime,
    require_source_authority_runtime,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, derive_successor_bundle,
    load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle import publish_bamf_generation
from bilqis_mlx.runtime.bamf_bundle.records import canonical
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state,
    acceptance,
    candidate,
    parent_state,
    publish_candidate,
    shape_patch,
)
from bilqis_mlx.semantics.context_eligibility import SourceFrontier
from bilqis_mlx.semantics.tests.core.test_atlas_export_clearance import (
    REGISTRY,
    _receipt,
    _selection,
)



class SourceAuthorityRuntimeCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, run_dir=None, *, generation=0, parent=None, state=None):
        run_dir = self.run if run_dir is None else Path(run_dir)
        source = candidate(parent_state())
        if state is not None or generation or parent is not None:
            source = candidate(
                parent_state() if state is None else state,
                generation=generation,
                parent=parent,
            )
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_candidate(run_dir, source)
        return source, pointer

    @staticmethod
    def registry_record(registry):
        return {
            "schema_version": registry.schema_version,
            "keys": [
                {
                    "owner_id": key.owner_id,
                    "public_key_hex": key.public_key_hex,
                    "schema_version": key.schema_version,
                    "allowed_scopes": [
                        {
                            "kind": scope.kind.value,
                            "key_prefix": scope.key_prefix,
                            "schema_version": scope.schema_version,
                        }
                        for scope in key.allowed_scopes
                    ],
                }
                for key in registry.keys
            ],
        }

    def test_bound_cache_rechecks_current_host_registry_before_authority_use(self):
        self.publish()
        drift = SourceAuthorityRegistry((replace(
            REGISTRY.keys[0], owner_id="source:drift"),))
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
            authority = AcceptedRuntimeHost(self.run).source_authority()
        from bilqis_mlx.runtime.bamf_bundle import source_authority_custody as custody
        with shape_patch(), patch.object(
                custody, "read_host_system_source_authority_registry", return_value=drift), \
                self.assertRaises(BilqisError):
            require_source_authority_runtime(authority, cache)

    def test_run_local_legacy_sidecar_cannot_override_host_bound_authority(self):
        self.publish()
        from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
            provision_source_authority_registry,
        )
        drift = SourceAuthorityRegistry((replace(
            REGISTRY.keys[0], owner_id="source:legacy-drift"),))
        provision_source_authority_registry(self.run, drift)
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
            self.assertEqual(cache.source_authority_registry_sha256, REGISTRY.digest)
            authority = AcceptedRuntimeHost(self.run).source_authority()
            self.assertIs(require_source_authority_runtime(authority, cache), authority)

    def test_foreign_same_registry_capability_rejects_against_other_run_cache(self):
        other = self.root / "other-run"
        self.publish()
        self.publish(other)
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
            foreign_cache = bind_accepted_execution_cache(other)
            authority = AcceptedRuntimeHost(self.run).source_authority()
            with self.assertRaises(BilqisError):
                require_source_authority_runtime(authority, foreign_cache)
        with shape_patch():
            self.assertIs(require_source_authority_runtime(authority, cache), authority)

    def test_stale_generation_capability_rejects_after_accepted_advance(self):
        _source, pointer = self.publish()
        with shape_patch():
            old_cache = bind_accepted_execution_cache(self.run)
            authority = AcceptedRuntimeHost(self.run).source_authority()
        successor_state = accepted_state(parent_state())
        self.publish(
            generation=1, parent=pointer["manifest_sha256"], state=successor_state)
        with shape_patch():
            with self.assertRaises(BilqisError):
                require_source_authority_runtime(authority, old_cache)
            current_cache = bind_accepted_execution_cache(self.run)
            with self.assertRaises(BilqisError):
                require_source_authority_runtime(authority, current_cache)

    def test_cache_install_cannot_race_past_accepted_pointer_advance(self):
        from bilqis_mlx.runtime.bamf_bundle import accepted_runtime

        _source, pointer = self.publish()
        with shape_patch():
            accepted = load_accepted_generation(self.run)
        successor_state = accepted_state(
            accepted.retained_state,
            extents=accepted.extents,
            spec=accepted.topology,
        )
        successor = derive_successor_bundle(
            accepted,
            successor_state,
            parent_manifest_sha256=pointer["manifest_sha256"],
            delivery_events=({"event": "FIXTURE_ACCEPTED"},),
        )
        entered = Event()
        release = Event()
        original = accepted_runtime._accepted_source_authority_registry

        def paused_registry(run_dir, student):
            registry = original(run_dir, student)
            entered.set()
            self.assertTrue(release.wait(5))
            return registry

        with shape_patch(), patch.object(
                mlx_checkpoint, "assert_headroom"), patch.object(
                accepted_runtime, "_accepted_source_authority_registry",
                side_effect=paused_registry), ThreadPoolExecutor(max_workers=1) as pool:
            bind_future = pool.submit(bind_accepted_execution_cache, self.run)
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaises(BilqisError) as rejected:
                    publish_candidate(self.run, successor)
                self.assertEqual(
                    rejected.exception.context["reason"],
                    "BAMF_POINTER_WRITER_ACTIVE",
                )
            finally:
                release.set()
            old_cache = bind_future.result(timeout=5)
            publish_candidate(self.run, successor)

        with shape_patch(), self.assertRaises(BilqisError) as caught:
            from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
                require_accepted_execution_cache,
            )
            require_accepted_execution_cache(old_cache)
        self.assertEqual(caught.exception.context["reason"], "B13_EXECUTION_CACHE_STALE")

    def test_caller_cannot_construct_or_forge_source_authority_runtime(self):
        self.publish()
        with shape_patch():
            cache = bind_accepted_execution_cache(self.run)
        with shape_patch():
            with self.assertRaises(BilqisError):
                require_source_authority_runtime(REGISTRY, cache)
            with self.assertRaises(BilqisError):
                SourceAuthorityRuntime()
            forged = object.__new__(SourceAuthorityRuntime)
            with self.assertRaises(BilqisError):
                require_source_authority_runtime(forged, cache)
