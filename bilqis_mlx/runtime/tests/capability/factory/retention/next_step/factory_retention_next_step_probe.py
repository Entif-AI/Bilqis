"""Clean-process CPU destination for the source-qualified B13.2 witness."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv) -> int:
    import mlx.core as mx

    mx.set_default_device(mx.cpu)
    from ..factory_retention_live_support import live_factory_context
    from .factory_retention_next_step_state import natural_next_selection
    from .factory_retention_next_step_witness import run_cold_destination

    if len(argv) == 5 and argv[1] == "natural":
        run_dir, root, source = map(Path, argv[2:])
        source_context, _ = live_factory_context(root, source)
        print(json.dumps(natural_next_selection(run_dir, source_context), sort_keys=True))
        return 0
    if len(argv) != 6:
        raise SystemExit(
            "usage: factory_retention_next_step_probe RUN ROOT SOURCE A01 REFERENCE")
    run_dir, root, source, artifact, reference = map(Path, argv[1:])
    source_context, _ = live_factory_context(root, source)
    result = run_cold_destination(run_dir, source_context, artifact, reference)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
