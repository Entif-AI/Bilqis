#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${BILQIS_SCHOOL50_RUN_DIR:-${HOME}/Code/bilqis-auto-curriculum50/runs/school50-continuous-v1}"
DEVICE="${BILQIS_SCHOOL50_DEVICE:-mps}"

cd "$ROOT"

case "${1:-}" in
  train)
    exec caffeinate -i python3 -m bilqis_school.engine \
      --run-dir "$RUN_DIR" \
      --device "$DEVICE" \
      --minutes "${BILQIS_SCHOOL50_MINUTES:-60}" \
      --max-updates "${BILQIS_SCHOOL50_MAX_UPDATES:-1000000}" \
      --block "${BILQIS_SCHOOL50_BLOCK:-64}" \
      --max-run-gib "${BILQIS_SCHOOL50_MAX_RUN_GIB:-16}" \
      --progress-format human \
      --patience-minutes "${BILQIS_SCHOOL50_PATIENCE_MINUTES:-20}" \
      --progress-window "${BILQIS_SCHOOL50_PROGRESS_WINDOW:-22}" \
      --min-repeat-improvement "${BILQIS_SCHOOL50_MIN_REPEAT_IMPROVEMENT:-0.01}" \
      --graceful-interrupt \
      --rollback-regressed-pass \
      --pass-regression-threshold "${BILQIS_SCHOOL50_PASS_REGRESSION_THRESHOLD:-0.01}" \
      --prune-checkpoints \
      --keep-recent-checkpoints "${BILQIS_SCHOOL50_KEEP_RECENT:-8}" \
      --keep-pass-checkpoints "${BILQIS_SCHOOL50_KEEP_PASS:-4}" \
      --candidate-grade-gate \
      --candidate-max-attempts "${BILQIS_SCHOOL50_CANDIDATE_ATTEMPTS:-3}" \
      --candidate-clear-reward "${BILQIS_SCHOOL50_CLEAR_REWARD:-0.05}" \
      --candidate-sentinel-per-grade "${BILQIS_SCHOOL50_SENTINEL_PER_GRADE:-8}" \
      --consolidate-grade-champions \
      --consolidation-weight "${BILQIS_SCHOOL50_CONSOLIDATION_WEIGHT:-0.15}"
    ;;

  soup)
    exec python3 -m bilqis_school.engine \
      --run-dir "$RUN_DIR" \
      --device "${BILQIS_SCHOOL50_EVAL_DEVICE:-cpu}" \
      --evaluate-grade-champion-soup
    ;;

  status)
    ps aux | grep '[b]ilqis_school.engine' || true
    python3 - "$RUN_DIR/state.json" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(f"School50 state not found: {path}")

state = json.loads(path.read_text())
accepted = state.get("accepted_pass", {})
champion = state.get("champion_pass", {})
retention = state.get("checkpoint_retention", {})
summary = {
    "run_dir": str(path.parent),
    "spiral_pass": state.get("spiral_pass"),
    "next_grade": state.get("next_grade"),
    "optimizer_step": state.get("optimizer_step"),
    "accepted_pass": accepted.get("pass"),
    "champion_pass": champion.get("pass"),
    "checkpoint": state.get("checkpoint"),
    "teacher_strategies": len(state.get("teacher", {}).get("strategies", {})),
    "checkpoint_files_retained": retention.get("retained_count"),
    "checkpoint_storage_gib": (
        retention.get("retained_bytes") / 1024**3
        if retention.get("retained_bytes") is not None else None
    ),
}
print(json.dumps(summary, indent=2, sort_keys=True))
PY
    ;;

  *)
    echo "usage: $0 {train|status|soup}" >&2
    exit 2
    ;;
esac
