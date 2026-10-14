# Bilqis

Bilqis is Entif AI's experimental developmental semantic-learning research project. It investigates whether explicit, typed semantic representations can support reusable relational and compositional competence with fewer training resources than less structured representations.

**Status:** Research software, not a proven language model, published golden checkpoint, complete New Ithkuil implementation, or demonstrated efficiency result. The repository's first archived historical snapshot is [`v0.0.0`](https://github.com/Entif-AI/Bilqis/releases/tag/v0.0.0). Later engineering work remains experimental until its own source and qualification evidence are published.

## Start here

- **Reproduce the current source:** install the requirements and run the engineering tests below. The tests establish implementation behavior, not learning efficacy.
- **Understand the architecture:** start with [`docs/reference/ARCHITECTURE.md`](docs/reference/ARCHITECTURE.md), [`docs/reference/SEMANTIC_AND_TOKEN_ABIS.md`](docs/reference/SEMANTIC_AND_TOKEN_ABIS.md), and [`docs/PROVENANCE.md`](docs/PROVENANCE.md). Some reference contracts describe independent historical prototypes rather than a single unified trained learner.
- **Understand the research claims and their limits:** read [`docs/research/preregistration.md`](docs/research/preregistration.md) and [`docs/reference/REPLICATION_GAP_MATRIX.md`](docs/reference/REPLICATION_GAP_MATRIX.md).
- **Find earlier experiments:** use the [release and experiment history](docs/RELEASE_HISTORY.md). Original pilot documentation, validation traces, and evidence remain at the immutable historical tag instead of forming an ever-growing set of current top-level guides.
- **Contribute:** see [`CONTRIBUTING.md`](CONTRIBUTING.md) and the repository issue tracker. Experiments and regressions should identify their model, lesson/assessment revision, data, source and checkpoint provenance.

## What's in the repository?

The code includes independent research implementations of finite-world semantics (`bilqis_ref/`), typed micro-world learning (`bilqis_micro/`), logical composition (`bilqis_logic/`), formal Boolean foundations (`bilqis_formal/`), developmental training (`bilqis_development/` and `bilqis_school/`), and later experimental adapters. They are **not** automatically compatible checkpoints, collectively validated curricula, or a single published production trainer.

Relevant stable inputs live in `abi/`, `configs/`, `schemas/`, `fixtures/`, and `references/`. The default checkout retains historical evidence needed by bundled verification tests. Other experiment outputs are recovered from the immutable [`v0.0.0` tag](docs/RELEASE_HISTORY.md), not bundled with current `main`.

## Quick start

Python 3.13 and an environment with CPU PyTorch are recommended for the reference tests. Use a separate virtual environment; local `.venv*` files are not part of releases.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python -m unittest discover -s tests -v
```

The reference implementation also supports a tiny smoke check:

```sh
python -m bilqis_ref.run --config configs/smoke-bilqis-ternary.json --out runs/bilqis-ternary-smoke
```

This is an engineering lineage check, **not** evidence of scientific generalization or a qualifying 100%-mastery milestone.

## Research and provenance

Bilqis takes inspiration from selected distinctions in New Ithkuil but is not New Ithkuil, does not claim official status, and does not implement its complete morphology, phonology or lexicon. Its independent formal oracles, experimental teachers, and assessment protocols are intended to distinguish what a model learns from what the generator declares correct.

The initial public reference was extracted from the ETR-2026-05 Stage 2 research package. See [`docs/CP0008_IMPORT_MANIFEST.json`](docs/CP0008_IMPORT_MANIFEST.json) for imported-source identities. The related research paper, *Prepaying Semantics: Bilqis as a Developmental Substrate for Representation-Efficient Relational and Compositional Learning*, has a [public research page](https://entif.ai/tags/research/2026/09/12/prepaying-semantics/).

The program explicitly accepts null results. Neither a passing unit test nor success on exposed teaching examples establishes sample efficiency, transfer, or mastery on an independent assessment.

## Versions and release history

Releases and source revisions are distinct from neural-training curriculum revisions. The [`v0.0.0` prerelease](https://github.com/Entif-AI/Bilqis/releases/tag/v0.0.0) is an archaeological snapshot of the public research history, **not** a certified golden student. Future qualified model milestones require same-checkpoint assessment receipts, full model and optimizer provenance, reviewed source, and a release tied to a verified commit on `main`.

See [`docs/RELEASE_HISTORY.md`](docs/RELEASE_HISTORY.md) for original experiment names and how to recover their files. We retain those names as historical identities rather than cosmetically renumbering them.

## License

A repository-wide license has not yet been declared. Redistribution and source rights must not be inferred from public visibility. See [issue #35](https://github.com/Entif-AI/Bilqis/issues/35) for the licensing work.
