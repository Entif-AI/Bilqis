# U7B: bounded teacher policy and cumulative continuation

This independently versioned alternative starts from PR #111's exact U6 weights and AdamW at step 13,400. Historical U7 run-01 remains frozen and untrained. One U7B learner receives 256 updates, with exact 12/4/8/8 batches. No new student identities, geometry, pretrained transfer, helper qualification campaign, merge or SYS-01 acceptance is implied.

The future-run integration point is `bilqis_teacher.policy.load_policy()`: load `bilqis.developmental-teacher/1.0.0`, resolve novelty before retrieval, validate exact DEV feedback, generate typed candidates through `bilqis_teacher.grammar.exercises()`, and admit compiled lessons through the source/type/independent-oracle boundary. The JSON contract records mandatory A/B/C closeout destinations; a completed research run additionally requires saved canonical readback receipts.

Source definitions and leaf query generators remain authored in #80/#84/#85 and the inherited Python registry. The grammar enumerates their products with three prerequisite reasoning arms, generates single-factor counterfactuals and checks both arms' influence. Kev selects among valid grammar productions; it does not invent definitions or issue gold. Per-family metrics on later DEV and untouched final worlds measure acquisition; they do not assign causal teaching utility to a selected option without a control.

The matched teacher battery contains eight source-grounded cells, two option orders and three context renderings: 48 native requests. Candidate identities and formal expectations remain fixed. A common generic task instruction is present in all modes; explanatory context and candidate descriptions vary. Canonical annotations are teacher-side typed metadata, not additional student semantic IDs. The two sequence steps use explicit independently validated intermediate state; report atomic and joint results. This is a small supplied battery, with authored test targets and generated hard alternatives, not an independent general-language benchmark.

Combined input earns selection only with at least two additional correct paired decisions versus each simpler mode, without reduced clarification or sequence success. Otherwise choose the more accurate simpler mode, with canonical on a tie. Curriculum choices have no handpicked pedagogical gold. Low-margin, error and review choices retain broad valid reservoirs and are counted as fallback, rather than silently replacing them with a preferred exercise.

Run from the repository root with the established Torch interpreter:

```
python -m bilqis_u7b.run freeze-battery
python -m bilqis_u7b.run qualify
python -m bilqis_u7b.run freeze
python -m bilqis_u7b.run train
python -m bilqis_u7b.run evaluate
python -m bilqis_u7b.run replay
```

Each output is exclusive-create and immutable. A partial/failed run is evidence; use a distinct successor identity rather than overwrite it. Replay uses archived native decisions, repeats all gradients and checks exact weights, optimizer moments, exposures, losses and predictions. It performs no new native helper inference.

TRAIN pools exclude predecessor TRAIN/DEV identities for newly generated rows, all historical evaluation identities, the frozen U7 cohort and U7B final worlds. Current-stage rehearsal uses unchanged U6 TRAIN with every historical evaluation row removed. Weak feedback accepts exact inherited varied/composite DEV identities only. The executor never receives fresh final cases; final scoring occurs once after training. Final generation shares the canonical generators and grammar with training, so exact-world holdout is not an independent generator-family or confirmatory scientific seal.

Focused proof: `python -m unittest discover -s tests -p 'test_teacher*.py' -v`, `python -m unittest discover -s tests -p test_u7b.py -v`, and inherited `test_spiral.py`. Avoid a full local verification sweep. Evidence and actual outcomes are under `docs/evidence/u7b/`.
