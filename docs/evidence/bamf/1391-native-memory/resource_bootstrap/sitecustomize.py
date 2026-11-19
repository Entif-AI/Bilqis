"""Apply the test resource policy when Python first imports MLX core."""

import atexit
from importlib.machinery import PathFinder
import sys


class BoundedMlxFinder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if fullname != "mlx.core":
            return None
        spec = super().find_spec(fullname, path, target)
        if spec is None or spec.loader is None:
            return spec
        load_core = spec.loader.exec_module

        def configure_after_load(mx):
            load_core(mx)
            from bilqis_mlx.runtime.mlx_memory import training_memory_policy

            mx.set_memory_limit(8 * 1024 ** 3)
            policy = training_memory_policy(mx)
            policy.__enter__()
            atexit.register(policy.__exit__, None, None, None)

        spec.loader.exec_module = configure_after_load
        return spec


sys.meta_path.insert(sys.meta_path.index(PathFinder), BoundedMlxFinder)
