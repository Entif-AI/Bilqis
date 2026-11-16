# Bilqis documentation map

This directory is organized by **authority and purpose**, not by the date a file happened to be written.

## Start here

- New to the repository: read the [root README](../README.md).
- Setting up or operating Bilqis: use the [setup and operator guide](operations/OPERATOR_GUIDE.md).
- Recovering from a hard stop: use the [Bilqis Operator Field Manual](operations/OPERATOR_FIELD_MANUAL.md).
- Contributing code: read [CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS.md](../AGENTS.md).
- Looking for normative behavior: use [specifications/](specifications/) and compatible [architecture/](architecture/).

The curriculum architecture did not originate with SPEC-0001. Earlier roadmaps, issues, registries, source records, and architectural work already required typed semantics, prerequisite-aware generated curriculum, independent source/oracle evidence, compositional reuse, and a reusable factory. SPEC-0001 consolidates those pre-existing requirements into an enforceable runtime-cutover contract. The historical failure was repeated implementation drift from that authority plus insufficient structural enforcement.

## Current authority

- [specifications/](specifications/) contains numbered normative repository specifications. Start with [0001_GENERATIVE_CURRICULUM_FACTORY.md](specifications/0001_GENERATIVE_CURRICULUM_FACTORY.md). [0004_TYPED_ERROR_CONTROL_PLANE.md](specifications/0004_TYPED_ERROR_CONTROL_PLANE.md) governs operator-visible failures, recovery and the error-debt migration. [0005_FACTORY_MICROSPEC_WORKSTACK.md](specifications/0005_FACTORY_MICROSPEC_WORKSTACK.md) governs issue #150 leaf decomposition and sequential execution. The hard runtime rule is **no factory release, no grade**.
- [tasks/](tasks/) contains numbered execution packets. [0001_IMPLEMENT_GENERATIVE_CURRICULUM_FACTORY.md](tasks/0001_IMPLEMENT_GENERATIVE_CURRICULUM_FACTORY.md) is the broad implementation/verification contract for SPEC-0001. [0003_FACTORY_CLOSURE_CODEX_RUN_PROTOCOL.md](tasks/0003_FACTORY_CLOSURE_CODEX_RUN_PROTOCOL.md) is the sequential issue #150 executor protocol; its companion JSON file is the machine-readable dependency workstack.
- [architecture/](architecture/) contains current architectural explanations that remain compatible with the numbered specifications. Architecture documents do not outrank a numbered spec or external governing authority.
- [operations/](operations/) contains current operator/repository procedures. The [setup and operator guide](operations/OPERATOR_GUIDE.md) is the canonical human workflow; the [Bilqis Operator Field Manual](operations/OPERATOR_FIELD_MANUAL.md) is the hard-stop recovery reference. Older BAMF runbooks remain deeper contract references and may contain issue-era status language. Operational instructions do not redefine curriculum semantics.

## Evidence and provenance

The [2026-10-21 main integration and runtime ownership record](evidence/development/ISSUE352_INTEGRATION_20261021.md) maps the trainer facade to its service owners and records size/debt dispositions.

- [evidence/](evidence/) contains observations, experiment receipts, diagnostics, grade evidence, and development qualification artifacts. Evidence can prove or falsify a claim; it does not become policy merely by existing.
- [provenance/](provenance/) contains source manifests, registry snapshots, adjudication records, review dossiers, source audits, and derivative requirement companions. These artifacts preserve what an implementation was grounded in. They are not duplicate canonical specifications.

## History

- [history/](history/) contains superseded proposals, archived migration sketches, old work packets, and pre-canonical documentation retained for forensic and historical use.
- Material in history/ may explain why the current system looks the way it does, but it must not be used to reopen a settled current contract without newer authority.

## Repository rules

Only this README belongs at the docs/ root. New normative specifications go in specifications/; execution prompts go in tasks/; current architecture, operations, evidence, provenance, and superseded material go in their corresponding directories.

Move documents with git mv so history remains inspectable. Do not create compatibility copies after a move. Repair callers and links instead. Do not delete forensic evidence simply to make the tree prettier.

Unit and contract tests belong beside the package that owns their invariant. The top-level tests/ directory is reserved for genuine integration, system, compatibility, and disposable end-to-end proofs.
