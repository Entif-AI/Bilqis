# Initial reference implementation provenance

## Source checkpoint

This repository bootstrap was prepared from the uploaded research checkpoint:

- archive: `CP0008-20260912T115723Z-FULL.zip`
- archive SHA-256: `d748810a053ab9c4c3bb9f6d91167d71f527f5a801bde0e9a6b412b454d47010`
- contained package: `ETR-2026-05-STAGE2-v0.4.7`
- report: ETR-2026-05
- package version: v0.4.7
- extraction date: 2026-09-12

The imported code and core reference documents originate from the package's `Training/`, `Technical/`, `Experiments/`, and selected `Evidence/` paths.

## Machine-readable import identity

[`CP0008_IMPORT_MANIFEST.json`](CP0008_IMPORT_MANIFEST.json) records source path, repository path, byte count, and source/repository identities for the 29 core files imported from the package's `Training/` reference implementation surface.

After provenance reconciliation against the uploaded archive:

- 26 of the 29 core files are byte-identical to CP0008 after repository path relocation;
- two files differ only by import-time formatting/whitespace normalization (`bilqis_ref/evaluate.py` and `abi/grammar-prerequisite-graph.json`);
- one file, `schemas/config.schema.json`, is an explicit repository patch rather than an unmarked rewrite;
- the manifest records source SHA-256, source Git-blob identity, repository Git-blob identity, byte counts, status, and the reason for every non-exact entry.

The schema patch admits the shipped `reference-3m` profile because CP0008 contains `configs/reference-3m.json` with `"profile": "reference-3m"` while its source schema admitted only `smoke` and `reference`. The repository fixes that internal packaging inconsistency rather than publishing a reference config that its own schema rejects.

Broader documentation imported or adapted from `Technical/`, `Experiments/`, and `Evidence/` is described below but is not represented as byte-identical by the core Training import manifest unless explicitly stated.

## Imported surfaces

The bootstrap imports:

- `Training/bilqis_ref/*.py`
- `Training/tests/*.py`
- `Training/configs/*.json`
- `Training/schemas/*.json`
- `Training/token-abi.json`
- `Training/grammar-prerequisite-graph.json`
- the bounded pedagogue system prompt and candidate pedagogue locator/configuration
- reference architecture/ABI/teacher/split/checkpoint/cost documentation
- selected SYS-01 research-design documents
- the Stage 2 New Ithkuil grammar source map

Paths have been reorganized into repository-native directories. The executable Python reference implementation is source-identical except for a whitespace-only normalization in `bilqis_ref/evaluate.py`; the grammar prerequisite graph is semantically identical JSON with compacted formatting. The one deliberate semantic/core-source deviation is the config-schema compatibility patch documented above.

## Donor-language research boundary

The repository includes independently authored Bilqis/Ithkuil research mappings and source-location records because they are material to inspecting the semantic-substrate hypothesis. Their presence does not imply that Bilqis is an official New Ithkuil variant or that the project has blanket redistribution rights over third-party donor material.

Source, licensing, and redistribution policy remains tracked in issue #35. Any later release of broader donor-derived corpora, copied examples, or lexical material must satisfy that policy separately.

## Intentionally excluded

The public bootstrap does **not** import:

- generated smoke-run result directories
- `.pt` checkpoints or other model binaries
- local engineering seal gold files or custodian-private material
- publication-production work logs and external-persistence state
- private model-assistance route ledgers or raw local-model responses
- machine-specific observed-environment state not needed to run the public reference
- manuscript production artifacts unrelated to running the reference implementation

These exclusions are deliberate. The repository should begin with source, specifications, reproducible fixtures, and research plans rather than historical generated state or materials whose disclosure/authority role differs from the public implementation.

## Verification performed for this import

Before repository publication, the extracted Stage 2 `Training/` tree was executed in the observed compatible environment using:

```sh
python -m unittest discover -s tests -v
```

Result: **29 tests passed**.

The test suite covers formal finite-world semantics, independent-oracle agreement, codec round trips and negative cases, token permutation symmetry, causal padding, checkpoint resume identity, teacher truth boundaries, confirmatory gating, event replay, sealing integrity, and seed-level statistical handling.

The GitHub Actions workflow in this repository runs the same reference suite on pushes and pull requests.

This verification is an engineering import check. It is not an independent scientific replication and does not constitute SYS-01 execution.
