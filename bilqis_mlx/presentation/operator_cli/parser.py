"""Human operator command arguments."""
from __future__ import annotations
from pathlib import Path
import argparse
import sys
from .settings import DEFAULT_RUN


class _FoundationExplicitStore(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        namespace.bamf_v2_foundation_explicit = True


class _AdmissionPolicyExplicitStore(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        namespace.admission_policy_explicit = True


def _add_boolean_profile_args(parser) -> None:
    boolean_profile = parser.add_mutually_exclusive_group()
    boolean_profile.add_argument(
        '--full-grade-b', dest='full_grade_b', action='store_true',
        help='Use the full canonical Grade B capability set (default).')
    boolean_profile.add_argument(
        '--reduced-grade-b', '--minimal-grade-b', dest='full_grade_b',
        action='store_false',
        help='Explicitly opt into the historical reduced AND/IFF Grade B profile.')
    parser.set_defaults(full_grade_b=True)


def _add_bamf_foundation_args(parser) -> None:
    from bilqis_mlx.runtime.atlas_admission import add_atlas_admission_arguments
    parser.set_defaults(
        bamf_v2_foundation_explicit=False,
        admission_policy_explicit=False,
    )
    add_atlas_admission_arguments(
        parser, admission_policy_action=_AdmissionPolicyExplicitStore)
    parser.add_argument('--atlas-release-manifest', type=Path,
                        help='Pinned Atlas release manifest for a BAMF semantic foundation.')
    parser.add_argument('--source-run-dir', type=Path, action=_FoundationExplicitStore,
                        help='Accepted source learner used to derive a fresh BAMF foundation.')
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model-topology", type=Path,
                        help="Versioned ModelTopologySpec JSON; resume must match saved topology.")
    parser.add_argument("--run-id", type=str, action=_FoundationExplicitStore,
                        help="Operator-selected BAMF lineage ID; required for a fresh v2 foundation.")
    parser.add_argument("--run-seed", type=int, action=_FoundationExplicitStore,
                        help="Operator-selected BAMF initialization seed; required for a fresh v2 foundation.")
    parser.add_argument("--learning-rate", type=float, action=_FoundationExplicitStore,
                        help="Exact BAMF AdamW learning rate; required for a fresh v2 foundation.")
    parser.add_argument("--adam-beta1", type=float, action=_FoundationExplicitStore,
                        help="Exact BAMF AdamW beta1; required for a fresh v2 foundation.")
    parser.add_argument("--adam-beta2", type=float, action=_FoundationExplicitStore,
                        help="Exact BAMF AdamW beta2; required for a fresh v2 foundation.")
    parser.add_argument("--adam-eps", type=float, action=_FoundationExplicitStore,
                        help="Exact BAMF AdamW epsilon; required for a fresh v2 foundation.")
    parser.add_argument("--weight-decay", type=float, action=_FoundationExplicitStore,
                        help="Exact BAMF AdamW weight decay; required for a fresh v2 foundation.")


def _add_training_policy_args(parser) -> None:
    parser.add_argument('--numeric-staircase', action='store_true',
                        help='Warm-start C at 0..3, grow to 6 before MUL/DIV')
    parser.add_argument('--boolean-composite', action='store_true',
                        help='Neural-inertly enroll B.COMPOSITE into the current Grade-B release')
    parser.add_argument('--boolean-idboolops', action='store_true',
                        help='Neural-inertly enroll inverse Boolean primitive identification into Grade B')
    _add_boolean_profile_args(parser)
    retention = parser.add_mutually_exclusive_group()
    retention.add_argument('--no-retention', action='store_true',
                           help='Explicit unprotected legacy teaching (separate independent --run-dir only)')
    retention.add_argument('--experimental-retention', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--retention-probe-each', '--experiment-probe-each',
                        dest='experiment_probe_each', type=int, default=6,
                        help='Source-oracled same-cohort rows per admitted capability')
    parser.add_argument('--retention-mature-max-loss', '--experiment-mature-max-loss',
                        dest='experiment_mature_max_loss', type=int, default=1,
                        help='PROVISIONAL max new wrong answers on any protected capability')
    parser.add_argument('--retention-introduction-extra-loss', '--experiment-introduction-extra-loss',
                        dest='experiment_introduction_extra_loss', type=int, default=2,
                        help='Additional tolerable losses during first acquisition')
    parser.add_argument('--retention-protected-cap-limit', '--experiment-protected-cap-limit',
                        dest='experiment_protected_cap_limit', type=int, default=8,
                        help='Bounded grade-stratified sentinel panel per visit')


def _add_training_execution_args(parser) -> None:
    parser.add_argument("--legacy-code-root", type=Path,
                        help="Explicit pinned predecessor source for an independent worktree")
    parser.add_argument("--champion-checkpoint", type=Path,
                        help="Explicit original checkpoint; the existing source fingerprint still applies")
    parser.add_argument("--verify-source", action="store_true",
                        help="Recheck all 216 candidate records against the pinned source (neural-inert)")
    parser.add_argument(
        "--human-run", action="store_true",
        help=("Explicit operator confirmation for mutating CLI actions; this is not "
              "authentication. BAMF create and "
              "enrollment remain neural-inert, while an accepted BAMF --resume may enter "
              "the persistent BAMF-native learner."))
    parser.add_argument("--autonomous-curriculum", action="store_true",
                        help="After --human-run authorization, autonomously measure, teach, and remeasure factory evidence while preserving the school scheduler")
    parser.add_argument("--issue-349-experiment-root", type=Path,
                        help="Register/enforce this run under issue #349's <=2-run, 100-GB collective experiment custody root")
    parser.add_argument("--minutes", type=int, default=90)
    parser.add_argument("--steps-per-visit", type=int, default=16)
    parser.add_argument("--max-visits", type=int, default=0,
                        help="Optional complete visit cap (default 0: use --minutes and disk reserve)")
    parser.add_argument("--timing-trace", action="store_true",
                        help="Write low-overhead nanosecond timing markers under runs/.timing-traces")
    parser.add_argument("--source-prefetch-workers", type=int, choices=(0, 1, 2), default=2,
                        help="Pure host-side lesson prep workers; 2 workers + main MLX lane = 3 lanes")
    parser.add_argument("--flash-mode", action="store_true",
                        help="Defer expensive assessments while training; stop owing a real assessment")
    parser.add_argument("--source-teaching-enrichment", "--boolean-association-bridge",
                        dest="boolean_association_bridge", action="store_true",
                        help="Add optional source-owned lessons declared by the admitted factory release")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--reserve-gib", type=float, default=100.)
    parser.add_argument("--stagnation-grace-grade", type=str, default=None,
                        help="Human-authorized grade whose stagnation quarantine actuator is temporarily suppressed")
    parser.add_argument("--stagnation-grace-steps", type=int, default=0,
                        help="Retained optimizer-step budget for the persisted stagnation grace")
    parser.add_argument("--admit-next-grade-with-debt", action="store_true",
                        help="Human-authorized one-time next-grade admission after substantial rehabilitation; preserves unresolved prior mastery debt")
    parser.add_argument("--triplets", "--triples", dest="triples", action="store_true",
                        help="Global weakest-three recovery is intrinsic to the new scheduler")


def parse_args(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser=argparse.ArgumentParser(description="Human-facing MLX operator commands; live training still gated by proof.")
    actions=parser.add_subparsers(dest="action",required=True)
    for name in ("status","dashboard","diagnostics","train"):
        p=actions.add_parser(name)
        p.add_argument("--run-dir",type=Path,default=DEFAULT_RUN)
        if name=="train":
            _add_bamf_foundation_args(p)
            _add_training_policy_args(p)
            _add_training_execution_args(p)
    # The npm explain script is an operator contract, not an experimental
    # feature. Register it in the same CLI that npm invokes from this checkout.
    for name in ("explain", "explain-error"):
        explain = actions.add_parser(name)
        explain.add_argument(
            "code", help="Typed error, legacy error, stop reason, or blocker code")
    parsed = parser.parse_args(raw_argv)
    return parsed
