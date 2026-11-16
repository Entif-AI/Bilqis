"""Run the BAMF CP01 service independently of any GUI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bilqis_mlx.paths import active_run_dir
from bilqis_mlx.mission_control.projection import MissionControlProjection
from bilqis_mlx.control_plane.native_source import native_query_catalog

from .discovery import discover_learner
from .service import ControlPlaneService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local BAMF control plane.")
    parser.add_argument("--run-dir", type=Path, default=active_run_dir())
    parser.add_argument("--socket", type=Path)
    parser.add_argument("--projection-db", type=Path,
                        help="Optional disposable CP06 index for bounded queries")
    return parser


def _default_socket(run_dir: Path) -> Path:
    run_dir = Path(run_dir).expanduser().resolve()
    return run_dir.parent / f".{run_dir.name}.control-plane.sock"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    socket_path = args.socket or _default_socket(args.run_dir)
    query_source = (
        (lambda: MissionControlProjection(args.projection_db).catalog())
        if args.projection_db is not None
        else (lambda: native_query_catalog(args.run_dir))
    )
    service = ControlPlaneService(
        args.run_dir, socket_path, query_source=query_source)
    print(json.dumps({
        "schema": "bilqis.bamf.control-plane.started/v1",
        "service": service.identity.to_record(),
        "learner": discover_learner(service.run_dir).to_record(),
    }, sort_keys=True), flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        service.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
