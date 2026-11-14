# Bilqis MLX setup and operator guide

This is the canonical human entrypoint for setting up and operating the current Bilqis MLX BAMF-0.2 system.

Older documents often mix three different jobs. This guide keeps them separate:

1. setting up a developer or inspection clone;
2. operating an existing accepted BAMF learner;
3. creating a new BAMF lineage on a host whose source authority and source lineage have already been provisioned.

That distinction is part of the safety model. A repository clone contains code and public source material. It does not contain live model state, private signing material, or the production source-authority trust root.

## Supported environment

### Native training host

The current BAMF-0.2 native baseline is:

- macOS 14 or newer;
- Apple Silicon;
- Python 3.11 or newer, with Python 3.14 as the current known-good environment;
- Node.js 22.12 or newer;
- Git;
- enough local storage for the trainer's protected reserve plus the next complete model and optimizer checkpoint.

The native environment used by current BAMF verification includes:

~~~text
mlx 0.32.4
mlx-metal 0.32.4
numpy 2.5.4
rdflib 7.6.0
cryptography 50.0.2
pyshacl 0.40.1
~~~

Portable source, semantic, control-plane, GUI, and other neural-inert tests can run without a supported MLX training device. Portable CI is not evidence of Linux MLX-training support.

## Clone and install

From a clean checkout:

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

The editable install supplies the repository's declared Python dependencies. The explicit MLX and NumPy packages supply the current native runtime stack, which is not yet encoded as one package extra.

Verify the command surfaces before touching a run:

~~~bash
python -m bilqis_mlx.cli train --help
python -m bilqis_mlx.control_plane --help
npm run mission-control:test
npm run mission-control:security:test
~~~

These commands do not start neural training.

## Know which setup you have

### Developer or inspection clone

A plain clone can:

- run portable and native tests when its dependencies are installed;
- inspect CLI help and documentation;
- launch Mission Control;
- run a local control plane;
- inspect an accepted run if its run data is available;
- exercise disposable fixtures and neural-inert dry-runs.

It cannot invent missing production custody.

### Existing accepted learner

If you have an accepted BAMF run directory, keep the entire directory intact. Its accepted pointer, generation manifests, model state, AdamW state, source identities, event history, and receipts form one custody chain.

Use that exact run directory for inspection, Mission Control, resume, and recovery.

### New production lineage

A fresh BAMF generation-zero lineage is not a blank-slate installer flow. It additionally requires:

- a readable accepted source run. Pass it explicitly with `--source-run-dir` for a fresh lineage;
- configs/models/bamf-0.2.json;
- an admitted Atlas release manifest whose bundle and release identities match the checked-in source-pin registry;
- the corresponding immutable Atlas artifact available to the runtime;
- the production source-authority registry already provisioned at the fixed ordinary-user Darwin location:
  <account-home>/.entif-ai/bilqis/source-authority-registry.json;
- the matching source-authority signer beside it when the selected authority path requires signing.

The runtime does not provision or repair those authority files. There is currently no supported repository command that turns an arbitrary clone into a new production authority root. Do not copy a registry into a new run directory or manufacture one from test fixtures.

If the host has not been provisioned, use the developer/inspection path and stop before fresh production creation.

## Run and storage locations

Bilqis stores mutable runs outside Git.

The default storage root is:

~~~text
<repository>/runs
~~~

The historical default active/source run fallback is:

~~~text
<repository>/runs/school-mlx-v1
~~~

`BILQIS_STORAGE_ROOT` deliberately relocates that default root. Fresh BAMF creation accepts `--source-run-dir`; use that explicit source path instead of relying on the historical `school-mlx-v1` fallback when the accepted source lives elsewhere.

For ordinary BAMF operation, use an explicit target directory:

~~~bash
export RUN_DIR=/absolute/path/to/bamf-run
~~~

Do not point two live trainers at the same run. Do not copy another model or optimizer over an accepted run to satisfy a guard.

## Inspect an existing run without learning

Always preflight before an owner training session:

~~~bash
npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
~~~

A valid accepted BAMF run reports its saved run identity, topology, Atlas identity, optimizer settings, and admission policy. Dry-run resume performs no neural update.

Capture a read-only operator snapshot:

~~~bash
npm run dashboard -- --run-dir "$RUN_DIR" --once --atlas-details
~~~

Read the BAMF-aware status surface when needed:

~~~bash
npm run status -- --run-dir "$RUN_DIR"
~~~

The npm diagnostics command is retained for the historical state.json/events.jsonl trainer. It is not the BAMF-native inspection path.

For a typed error or stop reason:

~~~bash
python -m bilqis_mlx.cli explain CODE
~~~

If preflight reports a blocker, preserve the run and follow the [Operator Field Manual](OPERATOR_FIELD_MANUAL.md). Do not edit state.json, bamf-state.json, optimizer steps, manifests, or receipts to get around the blocker.

## Start the local control plane

Mission Control does not start CP01 for you. Run the control plane as a separate local process.

Do this only after the target contains an accepted `bamf-state.json`. Starting CP01 against a fresh pointerless directory is safe, but its learner state is `learner-unavailable` and Mission Control has no accepted learner to operate.

Choose an explicit socket so the GUI and service cannot disagree about which run they are using:

~~~bash
export BILQIS_CONTROL_PLANE_SOCKET="$(dirname "$RUN_DIR")/.$(basename "$RUN_DIR").control-plane.sock"

python -m bilqis_mlx.control_plane \
  --run-dir "$RUN_DIR" \
  --socket "$BILQIS_CONTROL_PLANE_SOCKET"
~~~

The service prints a startup record and serves the local Unix socket. Leave it running while Mission Control is open.

Ctrl-C stops the control-plane service. Stopping CP01 does not itself stop or mutate the learner. Likewise, closing or quitting Mission Control disconnects the UI; it does not stop a detached trainer. Stop the trainer first when you intend to end a training session.

## Launch Mission Control

In a second terminal:

~~~bash
cd /path/to/Bilqis-MLX
source .venv/bin/activate

export RUN_DIR=/absolute/path/to/bamf-run
export BILQIS_CONTROL_PLANE_SOCKET="$(dirname "$RUN_DIR")/.$(basename "$RUN_DIR").control-plane.sock"
npm run mission-control
~~~

Mission Control keeps filesystem, subprocess, credentials, and raw control-plane sessions outside the renderer. The renderer receives bounded validated projections.

The major operator surfaces are:

- **Home:** current run state and operator attention;
- **School:** curriculum and capability evidence;
- **Lineage:** accepted generations and recovery forks;
- **Resources:** resource observations;
- **Evidence:** exact receipts and provenance;
- **Operate:** read-only previews and human-authorized commands.

If Mission Control says the control plane is disconnected, first verify that CP01 is still running and that both terminals use the same BILQIS_CONTROL_PLANE_SOCKET.

## Start or resume through Mission Control

Use **Operate**.

For a real mutating Resume:

1. choose **Resume**. Mission Control initially selects the final dry-run posture;
2. run Preflight and inspect the target identity with no neural mutation permitted;
3. turn **Final dry-run** off; this clears the old preview;
4. run Preflight again and confirm that the exact run, generation, topology, and consequence are still the ones you intend;
5. type `AUTHORIZE RESUME`, the exact phrase displayed for that reviewed request;
6. submit once.

Owner Launch follows the same preview, dry-run-off, re-preview, authorization sequence. The authorization text is not a reusable password or global switch. It binds the reviewed request. Stop does not have a dry-run posture: after selecting Stop, review its exact active operation target, type `AUTHORIZE STOP`, and submit once.

When a command is accepted, Operate retains its exact operation identity and can inspect the receipt and bounded command log tail.

**Pause is not implemented.** Use **Stop** for a GUI-launched active trainer. First generation-zero Create is currently a CLI workflow: the production shell requires a healthy accepted learner context before it enables mutation, so a pointerless fresh target cannot yet be created from Mission Control.

Mission Control's safe Stop flow is bound to the active operation retained by the current renderer session. Do not close and reopen Mission Control during a GUI-launched training session and assume Stop ownership will be reconstructed. Reconnect-safe Stop recovery is deferred work.

## Start or resume from the CLI

The CLI equivalent for a conservative first owner session is:

~~~bash
npm run train -- --human-run --resume --run-dir "$RUN_DIR" \
  --minutes 90 --reserve-gib 100 --max-visits 1
~~~

Important controls:

- `--human-run` is the current CLI's explicit operator confirmation for mutation. It is not authentication or a security boundary.
- --minutes 90 bounds the session by wall clock.
- --reserve-gib 100 preserves the production disk floor. Do not reduce it simply to make a run continue.
- --max-visits 1 gives a bounded first session. Later sessions may use another finite choice or rely on time plus disk reserve.

A staged accepted BAMF run can enter the native operator. An atlas-release run first reconciles its accepted admission state before entering the learner. Ambiguous held authority stops before learning.

For a terminal-launched run, Ctrl-C uses the trainer's normal interrupt path.

## Stop safely

### Mission Control launch

Use **Operate → Stop**. Stop is sent only after the control plane rechecks the exact operation, accepted lineage, and recorded trainer process identity. The trainer receives its normal SIGINT boundary.

### CLI launch

Use Ctrl-C in the trainer terminal.

In both cases, the goal is an ordinary interrupted operator exit that leaves the last accepted checkpoint as the resume point. Do not use a hard kill as routine shutdown.

After a stop, run a neural-inert preflight before resuming:

~~~bash
npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
~~~

## Verify the checkpoint and recover

Mission Control exposes a read-only **Checkpoint Verify** action in Operate. It validates the accepted generation without starting the trainer.

The CLI recovery posture is:

~~~bash
npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
npm run dashboard -- --run-dir "$RUN_DIR" --once --atlas-details
~~~

If those checks are clean, resume through Mission Control or the human CLI command.

If a fresh generation-zero create was interrupted before its accepted pointer was installed, do not switch to ordinary resume. The CLI reports BAMF_OPERATOR_INTERRUPTED_GENESIS_REQUIRES_CREATE_RETRY. Repeat the original create command with exactly the same identity, topology, manifest, and optimizer inputs. The generation-zero custody owner decides whether that exact retry can converge safely.

## Creating a new BAMF lineage

Only use this section on a host whose accepted source run, production source authority, and admitted Atlas release have already been provisioned.

Choose the new run identity and exact optimizer parameters:

~~~bash
export SOURCE_RUN=/absolute/path/to/accepted-source-run
export RUN_DIR="$HOME/Code/bilqis-mlx-runs/aspirant"
export ATLAS_MANIFEST=/absolute/path/to/admitted-atlas-release-manifest.json
export BILQIS_ATLAS_ARTIFACT_ROOT=/absolute/path/to/atlas-artifact-root
~~~

`SOURCE_RUN` must be an accepted source learner and `RUN_DIR` must name a different target. Use absolute paths or `$HOME`-anchored paths; do not derive the run path from the current worktree with `../...`. `BILQIS_ATLAS_ARTIFACT_ROOT` must contain the immutable content-addressed Atlas bundle named by the admitted manifest and checked-in source pin.

First run the neural-inert creation preflight:

~~~bash
npm run train -- --dry-run \
  --source-run-dir "$SOURCE_RUN" \
  --model-topology configs/models/bamf-0.2.json \
  --atlas-release-manifest "$ATLAS_MANIFEST" \
  --run-dir "$RUN_DIR" \
  --run-id example-run \
  --run-seed 543 \
  --learning-rate 0.0007 \
  --adam-beta1 0.88 \
  --adam-beta2 0.97 \
  --adam-eps 1e-7 \
  --weight-decay 0.03 \
  --source-prefetch-workers 0
~~~

Expected disposition: `READY_TO_CREATE`, zero neural updates, and no created target directory. This is preflight only. Do not run `status`, `dashboard`, CP01, Mission Control, or `--resume` against the new target yet because no accepted lineage exists.

After reviewing that identity, create generation zero with the same inputs and the explicit human boundary:

~~~bash
npm run train -- --human-run \
  --source-run-dir "$SOURCE_RUN" \
  --model-topology configs/models/bamf-0.2.json \
  --atlas-release-manifest "$ATLAS_MANIFEST" \
  --run-dir "$RUN_DIR" \
  --run-id example-run \
  --run-seed 543 \
  --learning-rate 0.0007 \
  --adam-beta1 0.88 \
  --adam-beta2 0.97 \
  --adam-eps 1e-7 \
  --weight-decay 0.03 \
  --source-prefetch-workers 0
~~~

Creation publishes accepted generation zero at optimizer step 0. It does not by itself perform a learner optimizer update. Confirm the accepted pointer before continuing:

~~~bash
test -f "$RUN_DIR/bamf-state.json"
npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
~~~

Only after those commands succeed should you start CP01, Mission Control, or the persistent `--resume` training command.

The default admission policy is staged. If the lineage must enroll in an atlas-release policy, use the versioned enrollment request described in the [BAMF-0.2 runbook](BAMF_0_2_RUNBOOK.md#preflight-launch-and-resume-boundary). The request file is not source authority by itself.

After creation and any required enrollment, inspect with a dry-run resume before starting persistent learning.

## Observe a session

For one complete read-only snapshot:

~~~bash
npm run dashboard -- --run-dir "$RUN_DIR" --once --atlas-details
~~~

For a following terminal display:

~~~bash
npm run dashboard -- --run-dir "$RUN_DIR" --atlas-details
~~~

Do not infer a learning result from activity alone. Source coverage, staged work, retained optimizer steps, capability gain, debt, mastery, and transfer are separate observations.

Mission Control gives the same operating workflow a graphical surface. When data is missing or stale, the UI should say so rather than convert missing evidence into a healthy zero.

## Storage, checkpoints, and backups

Full model and matching AdamW checkpoints are kept together. Accepted historical state is immutable.

Useful neural-inert storage commands include:

~~~bash
npm run storage:plan
npm run storage:dag-status -- --run-dir "$RUN_DIR"
~~~

When training is stopped, older immutable JSON state may be compacted through the supported storage command:

~~~bash
npm run storage:compact -- --run-dir "$RUN_DIR" --max-files 0
~~~

Do not delete model bundles or optimizer state because disk is low. The trainer has explicit role and custody references that determine what is safe to retire.

Backups should go to a distinct volume and must be verified before any original custody is removed.

## Troubleshooting order

When something fails:

1. preserve the run directory;
2. run neural-inert resume preflight;
3. read the exact error code and failed predicate;
4. run python -m bilqis_mlx.cli explain CODE;
5. consult the [Operator Field Manual](OPERATOR_FIELD_MANUAL.md);
6. inspect the [Error Field Manual](ERROR_FIELD_MANUAL.md) when deeper error inventory is needed;
7. repair the owning boundary, then preflight again before human training.

Do not fix an operator failure by weakening source validation, custody identity, retention, checkpoint matching, or disk reserve.

## Current limitations

The current operator surface intentionally has some sharp edges:

- Native learner execution targets a single Apple Silicon training host.
- Production source-authority provisioning is external to the runtime. A clean clone cannot create that trust root.
- Fresh BAMF creation consumes an already accepted source lineage; it is not a from-scratch bootstrap wizard.
- Mission Control requires the CP01 control-plane process to be started separately.
- Mission Control implements Stop, not Pause. Fresh generation-zero Create is currently CLI-only because the GUI mutation posture requires an accepted learner context.
- GUI Stop ownership is retained for the active GUI operation; reconnect-safe Stop recovery is not yet a complete workflow.
- Multi-user authorization, remote hosting, and generalized production observability are later work.
- Model weights, AdamW state, and live authority material are local artifacts, not downloadable repository contents.

These limitations should be visible before a session starts, not discovered from an error halfway through one.

## Deeper reference

Use these documents when you need the contract behind a procedure:

- [BAMF-0.2 runbook](BAMF_0_2_RUNBOOK.md): exact lifecycle commands and result semantics.
- [BAMF-0.2 first student](BAMF_0_2_FIRST_STUDENT.md): generation-zero and source-authority custody.
- [BAMF-0.2 continuing training](BAMF_0_2_TRAINING.md): source extension and daily observation.
- [Operator Field Manual](OPERATOR_FIELD_MANUAL.md): hard-stop diagnosis and recovery.
- [Error Field Manual](ERROR_FIELD_MANUAL.md): complete operator-visible error catalog.
- [Model topology](MODEL_TOPOLOGY.md): model topology contract.
- [Learning qualification](LEARNING_QUALIFICATION.md): controlled qualification runs.
- [BAMF packages](BAMF_0_2_PACKAGES.md): cognitive package staging and source-rights boundary.
- [Factory teacher observations](FACTORY_TEACHER_OBSERVATIONS.md): teacher observation capture and replay.
- [BAMF-0.2 architecture](../architecture/BAMF_0_2.md): complete system architecture.

For development rules and repository authority, use [AGENTS.md](../../AGENTS.md), [ADR.md](../../ADR.md), and the numbered specifications rather than this operator guide.
