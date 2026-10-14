# Bilqis

Bilqis is Entif AI's experimental work on finite-world semantics and developmental learning. The public repository currently ships a **bounded reference implementation**, not a trained golden student or an active neural-training campaign.

The historical [v0.1.0 source release](https://github.com/Entif-AI/Bilqis/releases/tag/v0.1.0) is a software milestone. The earlier [v0.0.0 research archive](https://github.com/Entif-AI/Bilqis/releases/tag/v0.0.0) preserves the original experiment code, logs, checkpoints committed to Git, and tests under their original names.

## Run the current reference

Use Python 3.13. Install the published CPU dependencies in a separate virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python -m unittest discover -s tests -v
```

Run an isolated, small reference experiment:

```sh
python -m bilqis_ref.run --config configs/smoke-bilqis-ternary.json --out runs/bilqis-ternary-smoke
```

The smoke run creates local output under `runs/`, which Git ignores. It tests reference behavior; it is not the current Bilqis student and cannot establish learning efficacy or golden qualification.

## Source map

| Path | Purpose |
| --- | --- |
| `bilqis_ref/` | Finite-world semantics, codecs, reference student, teacher rules, evaluation, and decision/navigation fixtures |
| `abi/`, `schemas/`, `configs/` | Versioned reference input and data contracts |
| `fixtures/`, `references/`, `prompts/` | Small reproducible inputs and source-rights records |
| `tests/` | Current reference behavior, checkpoints, provenance, and validation tests |
| `docs/reference/` | Architecture, token ABI, testing boundaries, and research limitations |
| `docs/PROVENANCE.md` | Original source import and precise provenance |
| `docs/RELEASE_HISTORY.md` | Exact historical paths and retrieval instructions |

Older School50 generations, the U-series experiments, formal and alpha prototypes, generated training evidence, and their original tests are stored at the historical `v0.0.0` tag. They are not required for the current reference checkout. See [release history](docs/RELEASE_HISTORY.md) to recover them without changing this tree.

The next neural golden-student release is separately gated by [golden-release requirements](docs/GOLDEN_RELEASE_GATE.md). A valid release must identify one fully qualified FP32 checkpoint with its own AdamW state and a complete approved current-capability examination. An earlier source tag, a high historical score, or a mixed candidate snapshot cannot substitute.

## Research scope and rights

The reference models use synthetic, typed semantic worlds and restricted answer heads. They are not a general-purpose language model, a complete New Ithkuil implementation, or proof of better sample efficiency. Read the [architecture](docs/reference/ARCHITECTURE.md), [semantic and token ABI](docs/reference/SEMANTIC_AND_TOKEN_ABIS.md), and [replication limitations](docs/reference/REPLICATION_GAP_MATRIX.md) before interpreting results.

Bilqis is not an official New Ithkuil project. Public source access does not itself grant reuse rights. No repository-wide license has been declared; [issue #35](https://github.com/Entif-AI/Bilqis/issues/35) tracks the licensing decision.

For changes, follow [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).
