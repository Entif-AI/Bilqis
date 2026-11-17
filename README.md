<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Entif-AI/Bilqis-MLX/refs/heads/main/docs/architecture/assets/Bilqis_Regal_Banner.png">
    <img src="https://raw.githubusercontent.com/Entif-AI/Bilqis-MLX/refs/heads/main/docs/architecture/assets/Bilqis_Regal_Banner.png" alt="Bilqis Neuro-Symbolic AI Model: Prepaying Semantics is Cheaper">
  </picture>
</p>

# Bilqis: A Novel Neuro-Symbolic AI Model Trained at Compositional Learning via a Semantic Pasigraphy Substrate

<p>Read the research paper behind this work here: <br /><a href="https://entif.ai/tags/research/2026/09/11/prepaying-semantics/" target="_blank">Prepaying Semantics is Cheaper</a></p>

Bilqis MLX is an Apple Silicon-native cognitive learner and training system built around MLX. It combines a source-grounded semantic substrate, a generative curriculum Factory, a continually extensible neural learner, retention-aware training, durable checkpoint custody, a local control plane, and the Model Forensics desktop interface.

The current system is the **BAMF-0.2 owner-operated alpha**. It is designed to learn source-qualified capabilities while preserving accepted knowledge and exact optimizer lineage. The repository is public; model weights, optimizer state, source-authority material, and live run data are not stored in Git.

If you want to run the software rather than study its architecture, start with the [setup and operator guide](docs/operations/OPERATOR_GUIDE.md).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Entif-AI/Bilqis-MLX/refs/heads/main/docs/architecture/mission-control-design/Bilqis%20Mission%20Control%20Dashboard.png">
    <img src="https://raw.githubusercontent.com/Entif-AI/Bilqis-MLX/refs/heads/main/docs/architecture/mission-control-design/Bilqis%20Mission%20Control%20Dashboard.png" alt="Bilqis Model Forensics Dashboard, displaying an active neurosymbolic training run.">
  </picture>
</p>

## What is in this repository

The repository contains the model and the local learning system around it:

- **BAMF neural learner:** MLX model code, typed semantic inputs, role-aware frame encoding, memory, readout, plasticity, and optimizer state.
- **Semantic and curriculum Factory:** source-qualified semantics, prerequisite-aware curriculum construction, generated lessons and assessments, and release/admission contracts.
- **Teacher and retention system:** candidate teaching, whole-student retention checks, rollback, capability evidence, and checkpoint publication.
- **Durable custody:** immutable generation manifests, matching model and AdamW state, accepted pointers, source identities, and recovery evidence.
- **Control plane:** a local service that exposes bounded status, query, event, and operator-command surfaces without giving the GUI filesystem or process privileges.
- **Model Forensics:** an Electron desktop cockpit for inspection and owner-authorized trainer operations.
- **Historical compatibility:** frozen predecessor code and source-oracle material under vendor/legacy-v16. New development belongs in bilqis_mlx.

The architectural contract is [BAMF-0.2](docs/architecture/BAMF_0_2.md), including `ADR-BAMF02-004` for the functional recursive Factory. Numbered specifications under [docs/specifications](docs/specifications/) own normative behavior.

## What runs today

BAMF-0.2 currently supports:

- neural-inert create and resume preflight;
- creation of accepted generation zero on a correctly provisioned host;
- human-authorized persistent training and cold resume;
- source/admission validation and retained candidate publication;
- read-only dashboard and diagnostic inspection;
- a local control plane with bounded command execution;
- Model Forensics views for live state, evidence, resources, curriculum, lineage, and operator actions;
- owner-authorized launch/resume, safe Stop, checkpoint verification, bounded command logs, and recovery through the accepted checkpoint path.

Actual neural optimizer updates are deliberately human-initiated. The CLI requires --human-run for mutating operation. Model Forensics requires a reviewed authorization phrase before it submits a mutating command.

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
npm run bamf:test
npm run bamf:security:test
~~~

For the complete setup matrix, including what a bare clone can and cannot provision, see [Setup and operation](docs/operations/OPERATOR_GUIDE.md).

## Quick start

First determine whether the target is new or already contains an accepted BAMF lineage.

For a **new** target, use an absolute path such as:

~~~bash
export RUN_DIR="$HOME/Code/bilqis-mlx-runs/aspirant"
~~~

Do not use `--resume`, start CP01, or launch Model Forensics yet. A fresh-lineage `--dry-run` is only a neural-inert preflight and intentionally does not create `RUN_DIR`. Follow [Creating a new BAMF lineage](docs/operations/OPERATOR_GUIDE.md#creating-a-new-bamf-lineage), then continue here only after `RUN_DIR/bamf-state.json` exists.

For an **existing accepted** BAMF run, use the exact run directory. A dry-run resume is neural-inert:

~~~bash
export RUN_DIR=/absolute/path/to/bamf-run

npm run train -- --dry-run --resume --run-dir "$RUN_DIR"
npm run status -- --run-dir "$RUN_DIR"
npm run dashboard -- --run-dir "$RUN_DIR" --once --atlas-details
~~~

Do not hand-edit checkpoint state to bypass a failed preflight. The accepted generation, model, AdamW state, source identities, and receipts are one custody chain.

## Launch Bilqis Model Forensics (BAMF)

Model Forensics talks to the local Python control plane over a Unix socket. These commands assume `RUN_DIR/bamf-state.json` already exists. A pointerless fresh target reports `learner-unavailable`; create generation zero first.

Model Forensics automatically discovers an active human BAMF trainer and owns
the local CP01 service for that run. For the common case, start or resume the
trainer and launch Model Forensics from the same checkout:

~~~bash
npm run bamf
~~~

If Bilqis Model Forensics is already open when a trainer starts, it retries discovery
and reattaches automatically. `RUN_DIR` remains useful when opening BAMF for a
specific inactive run; `BILQIS_CONTROL_PLANE_SOCKET` is an advanced explicit
override rather than a routine startup requirement.

Bilqis Model Forensics can inspect the run without neural updates.
Mutating actions remain behind preview and explicit human authorization.
The [operator guide](docs/operations/OPERATOR_GUIDE.md) walks through Resume,
Owner Launch, Stop, checkpoint verification, logs, and recovery.

## Championship and retention safeguards

**Reject-only retention canary (ADR-145):** A long candidate may spend a calibrated intermediate rung scoring the same source-oracled target probe used by final retention. Until its independent shadow history qualifies, that signal is telemetry only. Once qualified, a no-gain target canary may stop the remaining disposable candidate steps, but it cannot author a retention result: the stopped candidate must still be rejected by the ordinary target-first retention evaluator on that same authoritative target scope. Passing the canary means only that training may continue. Every candidate that reaches its configured horizon still runs the full applicable peer/protected/fixed/replay/frontier proof before any promotion or custody transfer.

**Capability championships:** Titles are capability-local, grade-isolated and defended, not historical high-water trophies. After a title field is cleared, an empty capability slot stays vacant until one checkpoint scores **strictly above 90%** on that capability; use exact integer comparison `10 * correct > 9 * total`, so 11/12 qualifies and 10/12 does not. Subthreshold measurements remain score/provenance evidence only: they do not mint a live role or pin a whole checkpoint solely for championship. Once the capability crosses that threshold it may earn championship custody and source-gold-gated teaching influence without waiting for full graduation of its grade. Its first defense battery is exactly the questions it got right on that threshold-crossing exam. A later contender that improves the current same-grade comparison or reaches the capability ceiling earns one lifetime title fight against that incumbent checkpoint for that capability; both checkpoints infer again, and cached model answers never decide the belt. The same checkpoint pair never rematches for that capability. A successful takeover may trigger one non-recursive same-grade sweep for sibling title fights. **Championship custody is active-title-only:** after an ordinary championship change, any old checkpoint that owns no active capability title is released from championship custody, and archived title history does not pin its weights. **Introducing new semantics is stronger: it clears the entire championship epoch. No prior champion role, soup, or championship checkpoint custody survives the boundary.** Other independent custody roles, such as the causal current student or explicit recovery state, may still keep shared bytes until those separate obligations end. Quarantine of another capability does not suppress a complete source-valid title challenge. Full grade graduation remains separate. See [`SPEC-0002`](docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md).

**Champion and soup teaching scope:** Each active capability role that has crossed the strict >90% championship threshold contributes one direct source-gold-gated advisory vote in its permitted teaching geography; a shared checkpoint may be inferred once but still contributes one vote per qualifying role. Subthreshold measurements contribute no role vote and no soup ingredient. Frozen grade soups are a separate aggregate adviser built only from threshold-qualified active roles, using full base votes in their own grade and the existing diluted foreign-grade voice. All such authority is valid only inside one unchanged holistic school identity. A change to the admitted course/question inventory, semantic graph, model parameter-shape geometry or executable factory release archives and clears **all** active champions and soups before further advice or title defense; the causal student+own AdamW and immutable historical receipts remain intact.

**BAMF foundation retention correction (ADR-142):** Admission is curriculum authority, not proof of an earned retention baseline. A capability first becomes protected after retained learning targeting that capability; its first retained measurement establishes the baseline. A brand-new admitted capability therefore has no pre-earned veto over the first learning update. Foundation tradeoffs use one-vote-per-capability normalized quadratic mastery debt, `(1-a)^2`, rather than a fixed raw-answer loss allowance: raw losses may trade only when the affected measured scope has positive mastery-debt utility. This is distinct from championship authority and from full-grade graduation.

When a comparable full-school examination includes B.OR and B.XOR, candidate screening also replays their 24 source-oracled, truth-balanced fixed-cohort questions. Any newly wrong answer on these already-correct compositions rejects the trial, without evaluating all school capabilities. Teacher feedback still records the rejection. The dashboard's **LESSON%** column measures fresh instructional examples; cumulative qualification is reported separately under **GRADES & MASTERY**.

## Human training boundary

For an already accepted BAMF lineage, a conservative first owner session is:

~~~bash
npm run train -- --human-run --resume --run-dir "$RUN_DIR" \
  --minutes 90 --reserve-gib 100 --max-visits 1
~~~

The current CLI requires `--human-run` as an explicit operator confirmation before mutating training. It is not authentication or a security boundary. `--max-visits 1` is a useful first-session bound, not a permanent training policy. Do not lower the 100 GiB reserve simply to keep a run alive.

A terminal-launched run stops through its normal interrupt path with Ctrl-C. A run launched through Model Forensics should use **Stop** in Operate so the control plane can bind the interrupt to the exact accepted operation.

## A clean clone is not a production authority bootstrap

A clean clone is sufficient for development, portable verification, read-only tools, Model Forensics, and operation of an accepted run whose custody is already present.

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
| apps/mission-control/ | Electron Model Forensics application |
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
npm run bamf:test
npm run bamf:security:test
npm run release:check
~~~

Full native MLX verification requires Apple Silicon. See [CONTRIBUTING.md](CONTRIBUTING.md) before changing runtime or training behavior.
