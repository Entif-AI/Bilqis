# Bilqis MLX

Bilqis MLX is an Apple Silicon-native cognitive learner and training system built around MLX. It combines a source-grounded semantic substrate, a generative curriculum Factory, a continually extensible neural learner, retention-aware training, durable checkpoint custody, a local control plane, and the Mission Control desktop interface.

The current system is the **BAMF-0.2 owner-operated alpha**. It is designed to learn source-qualified capabilities while preserving accepted knowledge and exact optimizer lineage. The repository is public; model weights, optimizer state, source-authority material, and live run data are not stored in Git.

If you want to run the software rather than study its architecture, start with the [setup and operator guide](docs/operations/OPERATOR_GUIDE.md).

## What is in this repository

The repository contains the model and the local learning system around it:

- **BAMF neural learner:** MLX model code, typed semantic inputs, role-aware frame encoding, memory, readout, plasticity, and optimizer state.
- **Semantic and curriculum Factory:** source-qualified semantics, prerequisite-aware curriculum construction, generated lessons and assessments, and release/admission contracts.
- **Teacher and retention system:** candidate teaching, whole-student retention checks, rollback, capability evidence, and checkpoint publication.
- **Durable custody:** immutable generation manifests, matching model and AdamW state, accepted pointers, source identities, and recovery evidence.
- **Control plane:** a local service that exposes bounded status, query, event, and operator-command surfaces without giving the GUI filesystem or process privileges.
- **Mission Control:** an Electron desktop cockpit for inspection and owner-authorized trainer operations.
- **Historical compatibility:** frozen predecessor code and source-oracle material under vendor/legacy-v16. New development belongs in bilqis_mlx.

The architectural contract is [BAMF-0.2](docs/architecture/BAMF_0_2.md). Numbered specifications under [docs/specifications](docs/specifications/) own normative behavior.

## What runs today

BAMF-0.2 currently supports:

- neural-inert create and resume preflight;
- creation of accepted generation zero on a correctly provisioned host;
- human-authorized persistent training and cold resume;
- source/admission validation and retained candidate publication;
- read-only dashboard and diagnostic inspection;
- a local control plane with bounded command execution;
- Mission Control views for live state, evidence, resources, curriculum, lineage, and operator actions;
- owner-authorized launch/resume, safe Stop, checkpoint verification, bounded command logs, and recovery through the accepted checkpoint path.

Actual neural optimizer updates are deliberately human-initiated. The CLI requires --human-run for mutating operation. Mission Control requires a reviewed authorization phrase before it submits a mutating command.

The native training baseline is a single Apple Silicon Mac. Portable tests and many read-only tools run elsewhere, but MLX training is not a Linux or x86 runtime target.

**FOUNDATION_EVIDENCE_POLICY_ACTIVE:** Foundation-stage acceptance currently permits teacher-forced acquisition, exact taught recall, and taught-composition replication. Novelty and generalization are measured diagnostics, not current advancement gates; a future fixed generalization gate requires explicit human admission. The machine-readable policy is [developmental_evidence_policy.json](docs/specifications/developmental_evidence_policy.json).

## Requirements

For the current native operator environment:

- macOS 14 or newer on Apple Silicon;
- Python 3.11 or newer. Python 3.14 is the current known-good native environment;
- Node.js 22.12 or newer and npm;
- Git;
- enough local storage for immutable model and optimizer checkpoints. The trainer protects a 100 GiB disk reserve by default.

The repository package declares the portable Python base. Native training also needs MLX and NumPy. The following environment is tested against the current BAMF lifecycle:

~~~bash
git clone https://github.com/Entif-AI/Bilqis-MLX.git
cd Bilqis-MLX

python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]' \
  mlx==0.32.4 mlx-metal==0.32.4 numpy==2.5.4 pyshacl==0.40.1

npm ci
~~~

Sanity-check the install without starting a learner:

~~~bash
python -m bilqis_mlx.cli train --help
python -m bilqis_mlx.control_plane --help
npm run mission-control:test
npm run mission-control:security:test
~~~

For the complete setup matrix, including what a bare clone can and cannot provision, see [Setup and operation](docs/operations/OPERATOR_GUIDE.md).

## Quick start

First determine whether the target is new or already contains an accepted BAMF lineage.

For a **new** target, use an absolute path such as:

~~~bash
export RUN_DIR="$HOME/Code/bilqis-mlx-runs/aspirant"
~~~

Do not use `--resume`, start CP01, or launch Mission Control yet. A fresh-lineage `--dry-run` is only a neural-inert preflight and intentionally does not create `RUN_DIR`. Follow [Creating a new BAMF lineage](docs/operations/OPERATOR_GUIDE.md#creating-a-new-bamf-lineage), then continue here only after `RUN_DIR/bamf-state.json` exists.

For an **existing accepted** BAMF run, use the exact run directory. A dry-run resume is neural-inert:

~~~bash
export RUN_DIR=/absolute/path/to/bamf-run

npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
npm run status -- --run-dir "$RUN_DIR"
npm run dashboard -- --run-dir "$RUN_DIR" --once --atlas-details
~~~

Do not hand-edit checkpoint state to bypass a failed preflight. The accepted generation, model, AdamW state, source identities, and receipts are one custody chain.

## Launch Mission Control

Mission Control talks to the local Python control plane over a Unix socket. These commands assume `RUN_DIR/bamf-state.json` already exists. A pointerless fresh target reports `learner-unavailable`; create generation zero first.

Start the control plane for the accepted run:

~~~bash
export RUN_DIR=/absolute/path/to/bamf-run
export BILQIS_CONTROL_PLANE_SOCKET="$(dirname "$RUN_DIR")/.$(basename "$RUN_DIR").control-plane.sock"

python -m bilqis_mlx.control_plane \
  --run-dir "$RUN_DIR" \
  --socket "$BILQIS_CONTROL_PLANE_SOCKET"
~~~

Leave that terminal running. In a second terminal, activate the same Python environment and launch the desktop app:

~~~bash
cd /path/to/Bilqis-MLX
source .venv/bin/activate
export RUN_DIR=/absolute/path/to/bamf-run
export BILQIS_CONTROL_PLANE_SOCKET="$(dirname "$RUN_DIR")/.$(basename "$RUN_DIR").control-plane.sock"

npm run mission-control
~~~

Mission Control can inspect the run without neural updates. Mutating actions remain behind preview and explicit human authorization. The [operator guide](docs/operations/OPERATOR_GUIDE.md) walks through Resume, Owner Launch, Stop, checkpoint verification, logs, and recovery.

## Human training boundary

For an already accepted BAMF lineage, a conservative first owner session is:

~~~bash
npm run train -- --human-run --resume --run-dir "$RUN_DIR" \
  --minutes 90 --reserve-gib 100 --max-visits 1
~~~

The current CLI requires `--human-run` as an explicit operator confirmation before mutating training. It is not authentication or a security boundary. `--max-visits 1` is a useful first-session bound, not a permanent training policy. Do not lower the 100 GiB reserve simply to keep a run alive.

A terminal-launched run stops through its normal interrupt path with Ctrl-C. A run launched through Mission Control should use **Stop** in Operate so the control plane can bind the interrupt to the exact accepted operation.

## A clean clone is not a production authority bootstrap

A clean clone is sufficient for development, portable verification, read-only tools, Mission Control, and operation of an accepted run whose custody is already present.

It is **not** sufficient to mint a new production BAMF lineage from empty disk. Fresh generation-zero creation consumes:

- an already accepted source run at the canonical active-run location;
- an admitted, source-pinned Atlas release manifest and its pinned artifact;
- a host-provisioned source-authority registry at
  <account-home>/.entif-ai/bilqis/source-authority-registry.json;
- the matching signer when the selected authority path requires one.

The runtime intentionally reads and validates those authority files but does not create or repair them. If the host has not been provisioned, stop at neural-inert inspection and testing rather than fabricating substitutes.

See [Creating a new BAMF lineage](docs/operations/OPERATOR_GUIDE.md#creating-a-new-bamf-lineage) for the provisioned-host workflow.

## Runtime data

By default, mutable run data lives under runs/ and is ignored by Git.

| Path | Purpose |
| --- | --- |
| bilqis_mlx/ | Active implementation |
| configs/ | Versioned runtime configuration, including the BAMF topology |
| lib/ithkuil/ | Imported New Ithkuil semantic source corpus and tooling |
| apps/mission-control/ | Electron Mission Control application |
| runs/ | Local model, AdamW, generation, event, teacher, and run state |
| vendor/legacy-v16/ | Frozen predecessor implementation and source-oracle compatibility material |
| docs/ | Specifications, architecture, operations, evidence, provenance, tasks, and history |

BILQIS_STORAGE_ROOT changes the default run root. Model bundles and optimizer state must never be committed to Git.

## Where to read next

- **Set up and operate Bilqis:** [Operator guide](docs/operations/OPERATOR_GUIDE.md)
- **Recover from a hard stop:** [Operator Field Manual](docs/operations/OPERATOR_FIELD_MANUAL.md)
- **Look up an error:** python -m bilqis_mlx.cli explain CODE and the [Error Field Manual](docs/operations/ERROR_FIELD_MANUAL.md)
- **Exact BAMF CLI semantics:** [BAMF-0.2 runbook](docs/operations/BAMF_0_2_RUNBOOK.md)
- **Architecture:** [BAMF-0.2](docs/architecture/BAMF_0_2.md)
- **Normative specifications:** [docs/specifications](docs/specifications/)
- **Documentation map:** [docs/README.md](docs/README.md)
- **Contributing and development:** [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md)
- **Architecture decisions:** [ADR.md](ADR.md)

The former integration-trunk README is preserved at
[docs/history/README_PRE_HUMAN_FRONT_DOOR_20261114.md](docs/history/README_PRE_HUMAN_FRONT_DOOR_20261114.md).
Current development and agent governance remains in AGENTS.md, ADR.md, numbered specifications, tasks, and live issue authority rather than in this landing page.

## Development guardrails

Repository structure rules remain binding even though this README is no longer the full agent-governance ledger. If ordinary work encounters a project-authored code file over the **>360** trigger, preserve the active task in **@Entif Work Stack** and refactor the production file and companion tests to **<240** before resuming. If an encountered directory reaches the **>=18** direct-code-file trigger, reorganize that directory to **<=12** direct code files. The full interruption contract and authority live in [AGENTS.md](AGENTS.md).

## Development

Common neural-inert checks:

~~~bash
npm run quality:check
npm run mission-control:test
npm run mission-control:security:test
npm run release:check
~~~

Full native MLX verification requires Apple Silicon. See [CONTRIBUTING.md](CONTRIBUTING.md) before changing runtime or training behavior.
