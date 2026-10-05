# Bilqis

Bilqis is an experimental semantic-representation and developmental-learning research program from Entif AI. The project tests whether an explicit, Ithkuil-derived semantic substrate can reduce the data, parameter, compute, or developmental cost required for a bounded learner to acquire reusable relational and compositional competence.

This repository currently contains the **initial finite-world reference implementation** extracted from the ETR-2026-05 Stage 2 research package (`CP0008-20260912T115723Z-FULL.zip`, report package v0.4.7). It is an engineering reference, not a completed efficacy trial, a trained Bilqis language model, or a full implementation of New Ithkuil.


## Why the name Bilqis?

The name is deliberate, but it is not part of the scientific treatment and carries no evidentiary weight for the representation hypothesis.

**Bilqis** is the name used in later Islamic exegetical and literary tradition for the ruler commonly recognized as the Queen of Sheba. The Hebrew Bible leaves the Queen of Sheba's personal name unstated, the New Testament refers to a Queen of the South, and Ethiopian tradition preserves the name Makeda. Those traditions are distinct. The useful correspondence is that a recognizable referent persists across different names, narratives, and representational surfaces while provenance remains necessary to say which tradition asserted what.

The narrative adds a second resonance. The Queen of Sheba is remembered for testing Solomon's wisdom with difficult questions. In the Qur'anic account of the ruler of Sheba, messages cross political boundaries, counsel mediates decisions, signs require interpretation, a throne moves between contexts, and a glass surface is initially perceived as water. The Qur'an itself does not name the ruler Bilqis. That name comes through later tradition. For a project concerned with representation, interpretation, ambiguity, and semantic continuity, that distinction is part of the point.

The former project name tied the work too closely to its donor language and invited the wrong inference: that this project is simply "machine Ithkuil" or an official New Ithkuil variant. Bilqis gives the experimental object its own identity. New Ithkuil remains a major donor of candidate semantic factors, but those factors remain subject to controls, decomposition, supplementation, rejection, and falsification.

The name also rhymes with the wider Rosetta program. Rosetta is concerned with corresponding meaning across different representations without requiring those representations to become identical. Bilqis names a figure whose identity has crossed languages, traditions, names, and retellings while still requiring provenance to preserve what each source actually says. The metaphor is useful. The experiment still has to earn every scientific claim.

## What is here

- `bilqis_ref/` — finite-world semantics, independent oracle pair, codecs, small transformer student, teacher policy, checkpoint/recovery, sealing, evaluation, and constrained pedagogue adapter.
- `abi/` — token ABI and grammar-prerequisite graph used by the reference package.
- `configs/` — smoke, reference-scale, and system-design configurations.
- `schemas/` — JSON Schemas for semantic objects, run configs, and results.
- `tests/` — 29 engineering tests covering formal semantics, codecs, token symmetry, restart identity, teacher boundaries, sealing, and related invariants.
- `docs/reference/` — architecture, semantic/token contracts, Ithkuil primitive map, split/sealing rules, teacher boundaries, checkpoint lineage, and reproducibility gaps.
- `docs/research/` — the current SYS-01 preregistration and attribution/control plans from the Stage 2 package.
- `references/` — the source-grounded New Ithkuil grammar map used during the Stage 2 research pass.

The research roadmap lives in [issue #5](https://github.com/entif-ai/bilqis/issues/5). The repository bootstrap and reproducibility work is tracked in [issue #6](https://github.com/entif-ai/bilqis/issues/6).

## Scientific status

The reference implementation has passed its delivered engineering suite and tiny smoke runs. The larger integrated SYS-01 scientific trial has **not** been run. In particular, this repository does not yet establish that Bilqis improves sample efficiency, compute efficiency, transfer, natural-language learning, or low-precision training.

The first scientific program deliberately separates:

1. the integrated systems effect;
2. representation-specific effects;
3. adaptive curriculum effects;
4. generic factorization effects;
5. tokenizer and sequence-length economics;
6. precision/ternary interactions; and
7. later natural-language transfer.

A generic typed representation is allowed to match or beat Bilqis. A null result is a valid result.

## Quick start

The observed Stage 2 environment was Python 3.13.5 with CPU PyTorch 2.10.0, NumPy 2.3.5, SciPy 1.17.0, and jsonschema 4.26.0.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python -m unittest discover -s tests -v
```

The delivered suite should report 29 passing tests.

Run a tiny engineering lineage:

```sh
python -m bilqis_ref.run \
  --config configs/smoke-bilqis-ternary.json \
  --out runs/bilqis-ternary-smoke
```

Run the corresponding controlled-language arm:

```sh
python -m bilqis_ref.run \
  --config configs/smoke-cnl-ternary.json \
  --out runs/cnl-ternary-smoke
```

These are execution checks, not scientific confirmation.

## Reference model boundary

The implemented student is a small causal decoder-only transformer with a four-answer supervised readout: `TRUE`, `FALSE`, `UNKNOWN`, and `CONFLICT`. The reference-scale configuration contains 2,828,736 trainable parameters. The ternary branch is W1.58A8-style forward emulation over FP32 master weights, not a packed low-bit kernel.

The current Bilqis codec is a machine-oriented, lossless finite-world representation informed by selected New Ithkuil distinctions. **Bilqis is not New Ithkuil and is not presented as an official variant of it.** The codec is not valid surface New Ithkuil and does not claim to implement the language's complete morphology, phonology, lexicon, or writing system.

## Truth boundary

The developmental pedagogue is deliberately non-authoritative. It may propose curriculum choices within a bounded schema, but it does not define gold answers or certify mastery. Formal world generation and the independent oracle pair determine truth for the current synthetic domain.

The guiding rule is:

> LLM proposes; formal machinery disposes.

## Source provenance

The initial import is a public projection of the reference implementation from the ETR-2026-05 Stage 2 CP0008 package. Generated smoke results, binary checkpoints, local custodian material, private production ledgers, and unrelated publication-production artifacts are intentionally not imported into this repository.

See [`docs/PROVENANCE.md`](docs/PROVENANCE.md) for the extraction boundary, [`docs/CP0008_IMPORT_MANIFEST.json`](docs/CP0008_IMPORT_MANIFEST.json) for machine-readable source/repository identities of the core imported files, and [`docs/reference/REPLICATION_GAP_MATRIX.md`](docs/reference/REPLICATION_GAP_MATRIX.md) for what remains unvalidated.

## Research publication

The companion working paper is:

**Prepaying Semantics: Bilqis as a Developmental Substrate for Representation-Efficient Relational and Compositional Learning**  
ETR-2026-05, v0.5.0.

Public research page: https://entif.ai/tags/research/2026/09/12/prepaying-semantics/

## Issues and participation

The issue tracker is intentionally part of the research method. It contains the planned semantic ABI work, grammar mapping, generator/oracle construction, dataset audits, teacher controls, SYS-01 plan lock, attribution experiments, replication, and release work.

Start with:

- [#5 — first developmental-training program and SYS-01 roadmap](https://github.com/entif-ai/bilqis/issues/5)
- [#7 — semantic ABI and canonical AST](https://github.com/entif-ai/bilqis/issues/7)
- [#13 — independent truth oracle](https://github.com/entif-ai/bilqis/issues/13)
- [#22 — SYS-01 preregistration and plan lock](https://github.com/entif-ai/bilqis/issues/22)
- [#27 — generic typed-IR control](https://github.com/entif-ai/bilqis/issues/27)

## License

No repository-wide license is declared by this bootstrap commit. Source and redistribution policy is tracked in [issue #35](https://github.com/entif-ai/bilqis/issues/35). Do not infer rights beyond those granted by applicable source licenses or explicit project releases.
