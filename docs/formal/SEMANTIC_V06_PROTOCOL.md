# Bilqis semantic-neighborhood teaching v0.6: preregistered e9

**Status:** Design and executable protocol. It is a new isolated research
epoch, not a modification, continuation, or rerun of e6/e7/e8. It **cannot be
used to claim #82 Stage A-F acceptance**, language admission, or demonstrated
continual learning. The user authorized semantics-grounded teaching and
bounded performance tests, not silent replacement of Bilqis's learned model.

## Research question and hypotheses

The e8 student sometimes solved new AND questions while its earlier Boolean
or NOT competence deteriorated. More training was not monotonically better.
In e9 we test two separable teaching interventions:

1. **Meaning-first organization:** batching together expressions with the same
   full Boolean function (or its complement) encourages more stable acquisition
   than uniformly shuffled presentations of the exact same examples.
2. **Rehearsal dose:** reserving 16 rather than 8 of each 32-sample batch for
   previously exposed skills reduces forgetting, possibly at the cost of
   slower mastery of the new competency.

The randomized semantic-sham control tests whether clustering itself,
independent of correct semantic group membership, is sufficient. An absent
positive effect, or improvement on TRAIN/DEV that fails sealed transfer or
retention, is a valid negative research outcome.

## Frozen ontology and curricular data

Only `V00.BOOLEAN`, `V01.NOT`, `V02.AND` are enabled. `V01` and `V02` each
depend solely on sealed admission of `V00`; `V02` remains eligible after a
failed `V01` unless previous admitted-skill retention was lost.

`curriculum_v6.py` enumerates exact expression ASTs separately for TRAIN,
DEV and SEALED, then all legal valuations per expression. TRAIN includes
Boolean constants and variables; NOT of variables/constants and double NOT;
AND identity, commutation, annihilator, idempotence and nested conjunction.
DEV uses related formulas over Q/R. SEALED uses separately named formulas over
R/P, includes depth-three conjunctions, and is scored only after stage updates.
Rows are source/role tagged, oracle labeled and identity-disjoint across the
three pools *within e9*. Existing research may have exposed overlapping
simple Boolean shapes historically. Do not claim historical novelty, full
Boolean reasoning, or population-generalized gains.

`signature(expr)` exhaustively evaluates every fixed P/Q/R truth valuation:
the signature is the 8-bit Boolean function vector. `concept_key` identifies
either that function or its complement without collapsing opposite GOLD
answers. This is **teacher-side metadata only**. The student still sees its
unchanged typed v0.3 ABI, a single standalone question ending at `ACT.ANSWER`;
oracle truth remains a separate supervised cross-entropy target. No category
IDs, ontology hints, answer labels, feedback or earlier conversation turns
enter the student context. Gold truth is checked independently. This tests
teacher ordering, not an embedding/auxiliary category-prediction architecture.

The teacher proves several algebraic equivalences via the existing oracle.
Every source record and all models remain separate from earlier epochs.

## Matched arms and controls

Five fixed *new* seeds: **503, 509, 521, 523, 541**. Fresh scratch student
for every seed/arm (identical initialization within seed), AdamW with the
same optimizer settings as e8, 32 rows per update, exactly 320 updates for
every eligible stage, five sequential 64-update blocks. Maximum upper bound:
five seeds × five arms × three stages × 320 = **24,000 updates**; fewer if
prerequisites or prior retention fail.

| Arm | Current / prior per batch | Within-block organization |
| --- | --- | --- |
| `uniform8` | 24 / 8 | Randomly shuffled row placement |
| `semantic8` | 24 / 8 | Grouped by true function/complement key |
| `sham8` | 24 / 8 | Grouped by randomly assigned, false semantic keys |
| `uniform16` | 16 / 16 | Randomly shuffled row placement |
| `semantic16` | 16 / 16 | Grouped by true function/complement key |

The initial stage has no previous skills, hence 32 current rows in all arms.
Within each stage and block, all arms at the same rehearsal dose receive
**identical row-ID multisets**, independently reconstructed from the seed,
stage, block and previously exposed lesson set. Each batch is 16 TRUE + 16
FALSE. Prior-example slots are distributed evenly across previously exposed
competencies. The batch-cohesion metric records actual equivalent/complement
pairs, rather than assuming that grouping occurred or was useful.

The 8-vs-16 contrast changes exposure counts and is reported separately,
never mislabeled as a fixed-example grouping comparison. The sham assignment
is frozen and drawn without DEV or sealed feedback; its exact multiset matches
`uniform8`/`semantic8`. The semantic arm additionally aligns prior-stage
TRAIN cohorts with current-stage TRAIN expressions sharing real equivalence
or negation neighborhoods while preserving its exact fixed block multiset.
Distinct-AST, cross-stage, matched-valuation and declared algebraic-relation
coexposures are measured; duplicate rows do not count as relational witnesses.
This is still minibatch/gradient-order organization, **not** putting prior
examples into the learner's 96-token attention window.

## Assessments and promotion

After each 64-update block, evaluate the current **DEV** and already exposed
previous **DEV** panels, solely for measurements. No arm reads DEV correctness
to choose block count, batch rows or rehearsal dose. Controller therefore
uses no adaptation derived from the small DEV set in this experiment.
For each stage, **first access to its SEALED predictions is after the final
320 optimizer updates**. Earlier admitted competencies' SEALED results are
rechecked separately for retention. The stage promotes only on perfect
current sealed accuracy AND perfect old accepted-skill sealed retention.
If the old accepted skill loses SEALED retention, progression stops. Failure
of the current gate blocks only dependent stages. A current gate or later
sibling gate cannot steer the already executed current stage's examples.

Primary endpoint: each seed/arm's final simultaneous retention of all three
atomic stages. Secondary endpoints: stage-by-stage sealed accuracy, TRUE/FALSE
class accuracy, depth-stratified novel-structure accuracy, both-correct scores
on semantically equivalent held-out expression pairs, progression/skip counts,
old-skill DEV and SEALED retention, update cost and per-seed matched deltas.
If full success is uniformly zero, report measurable intermediate outcomes
without promoting them to full mastery. Three-element grammar and five seeds
cannot support broad statistical or neuroscientific claims.

## Source freeze, execution and replay

`pilot_v6.py` must reject a dirty worktree, reused output, incorrect run path,
changed locked source bytes, untracked protocol/test/source, or source bytes
different from the recorded Git commit. Freeze all executable dependencies,
protocol and tests in one committed source head before the first optimizer
update. Source hash and exact branch SHA appear in immutable preregistration.

Run **once** with no seed substitution, result-driven retrial, extra arm, or
changed cap. Preserve all per-block model+AdamW snapshots, sampled-row order
and multiset hashes, ordinal stage paths, DEV evidence and stage-ending SEALED
evidence. Checkpoint replay reconstructs the deterministic sampler and
recomputes predictions/gates from saved checkpoints. It is not full
floating-point replay of every historical optimizer gradient.

The run directory and model checkpoints remain ignored locally; only
audited aggregate data, the frozen protocol, source digest and bounded
results are archived in a research PR. A successful unit workflow alone
is not evidence of learning efficacy. No branch is merged or #82 closed
merely because this experimental machinery compiles or yields a positive
training/DEV curve.

```sh
python -m unittest discover -s tests -v
python -m bilqis_formal.pilot_v6 --out runs/formal-foundations-20261012-e9-semantic-v06
python -m bilqis_formal.pilot_v6 --out runs/formal-foundations-20261012-e9-semantic-v06 --replay
```
