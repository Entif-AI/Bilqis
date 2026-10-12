# Bilqis: autonomous, development-first spiral school

The goal is a more capable continuing student, not repeated scratch-model
attribution experiments. Incorrect answers are evidence for new practice,
not automatic rejection of the learner or rollback of its neural history.

## The fifty-grade skill tree

See SKILL_TREE_50.json for the canonical executable design:

- G01-G22: twenty-two grades of logic, mathematics and typed relationships.
- G23-G35: thirteen grades of official 2023 New Ithkuil grammar.
- G36-G50: fifteen grades of official New Ithkuil lexical semantics.

Every grade has a mechanic, its prerequisite, older concepts for rehearsal
and forward previews of the next two grades. Grade progression is
developmental, not a requirement to ace an exam before proceeding. The
student traverses successive increasing-grade spirals.

Twenty-two logic/math grades can actually compile trustworthy lessons,
using existing finite-world semantics plus new small-integer arithmetic
(numbers 0-100; ADD/SUB/MUL/MOD/EQ/LT/LE, exact truth labels). The
machine ABI grows append-only from 113 learned identities to 222 without
changing existing model weights, optimizer moments or semantic token IDs.

G23-G50 are DESIGNED ONLY, not language-capable exercises: the full
source-backed grammar and lexicon compiler does not exist. The teacher
skips these with explicit reporting, or the --require-full50 flag causes
a fail-fast error before any gradient. This is not a completed 50-grade
New Ithkuil training epoch.

## Autonomous teacher

The student has one continuous neural history. The teacher separately
retains per-grade and cross-grade strategy outcome statistics. It chooses
between strategy vectors, mutates one whitelisted setting after every
third grade, and reuses what it discovers across repeated spirals. The
operational strategy budget is 512 candidates. This is a safety ceiling,
not a target; the teacher may continue creating candidates while novel
one-knob variants remain available.

Whitelisted variables: earlier-grade example count, two-grade foresight
example count, question depth, semantic contrast frequency, learning rate,
and the strength of previous-model distillation. Each 32-example batch
contains actually compiled new, old and future examples. Oracle truth
is never replaced or invented by the teaching policy.

The reward uses practical accuracy change on small developmental probes
plus earlier-grade health. These probes are reused for feedback, and
therefore are not independent scientific tests. Low scores inform future
lessons; they do not freeze or restart the student.

After every completed grade, the runner saves the model, AdamW optimizer,
fixed semantic graph, exact optimizer step, teacher policy statistics,
complete per-grade ledger, and a new atomic state pointer. The next
invocation reopens that exact checkpoint. A crash within a grade can lose
the unsaved part of that grade but not completed grade checkpoints.

## Model capacity

The school preserves the previously learned U7F student at step 13,848.
An independently tested migration expanded it from 362,976 parameters
to 10,743,936; width 96 to 384, attention heads 6 to 24, transformer
blocks 3 to 6. Existing learned representations are replicated and new
residual blocks initially act as identities, with transferred optimizer
moments and unchanged step count. All answers matched on 256 real old
and new questions with maximum logit error below 0.000014.
Capacity is now larger; this itself does not confer language competence.

The architecture still has only a 96-token input context and a classifier
head for five Boolean/evidence states. Teaching full Ithkuil utterance
production requires more than vocabulary: a versioned longer-context,
sequence-generating objective must reuse or distill the already learned
semantic representations.

## Local continuous operation

Start from the new isolated school repository worktree. First initialize
only while the externally custodied U7F active checkpoint is available.
Then the system resumes from its own latest checkpoint on every invocation.

Observe exact state:

    python3 -m bilqis_school.engine --status

Run a long bounded Apple-Metal training session, resuming existing state:

    caffeinate -i python3 -m bilqis_school.engine --device mps --minutes 360 --max-updates 1000000 --block 64 --max-run-gib 32

For an operator-visible development run, prefer a smaller bounded session with
human-readable progress and a stagnation stop:

    caffeinate -i python3 -m bilqis_school.engine --device mps --minutes 90 --grade-visits 16 --max-updates 1000000 --block 64 --max-run-gib 32 --progress-format human --patience-minutes 60 --progress-window 8 --min-repeat-improvement 0.01 --graceful-interrupt --prune-checkpoints --keep-recent-checkpoints 8 --keep-pass-checkpoints 4 --candidate-grade-gate --candidate-max-attempts 3 --candidate-clear-reward 0.05 --candidate-sentinel-per-grade 8 --consolidate-grade-champions --consolidation-weight 0.15

The runner prints one line after every durable grade checkpoint. It includes
the fixed-probe score before and after that lesson, change versus the previous
visit to the same grade, rolling repeated-grade improvement, mean change
across the guarded earlier skills, teacher reward, strategy count and
mutations, elapsed time, and the current no-improvement clock. The final
summary also reports mean repeated-grade change and counts of improved,
unchanged and regressed repeated grades for the call.

At the end of every complete executable G01-G22 spiral, the runner also
evaluates the single resulting checkpoint on all twenty-two fixed probes at
once and prints a PASS REPORT. That report includes mean and median probe
score, mean and median grade improvement versus the previous pass, mean and
median improvement versus the untouched School50 starting checkpoint,
the number of grades at or above 90%, the number at 100%, the remaining mean
gap to 100%, and the highest/lowest scoring grades. Existing runs recover the
true step-13,848 starting checkpoint when it is still present rather than
fabricating a baseline from staggered in-pass observations.

The grade-visits option is an explicit durable stop point. The
patience-minutes option stops only after there are at least progress-window
same-grade comparisons and that rolling trend has failed to reach
min-repeat-improvement for the requested time. A value of 0.01 means one
percentage point. All stops occur after a completed grade checkpoint, so the
next invocation resumes the same model and optimizer.

With graceful-interrupt enabled, the first Ctrl+C requests a stop instead of
raising KeyboardInterrupt. If a grade is in progress, the runner finishes it,
writes the new checkpoint and atomic state pointer, then exits with
STOPPED_BY_GRACEFUL_INTERRUPT. If the runner is between grades, it exits
immediately from the already-durable boundary. A second Ctrl+C preserves the
ordinary emergency behavior and aborts immediately.

For optional pass-level regression protection, add:

    --rollback-regressed-pass --pass-regression-threshold 0.01

The teacher still tolerates ordinary grade and pass wobble, but the rollback
anchor is a retained champion checkpoint rather than merely the most recent
pass that escaped rejection. A pass rolls back when its simultaneous
twenty-two-grade mean probe score is at least one percentage point below that
champion. Median and per-grade counts remain diagnostic instead of masking
asymmetric aggregate damage. A pass that stays within tolerance may continue
as the live student, but it replaces the champion only when its mean probe
score actually exceeds the champion. When rollback occurs, the student model
and AdamW state resume from the champion while teacher strategy statistics and
rejected-pass evidence remain durable.

Run-level headline learning metrics follow the surviving student lineage.
If a completed pass is rolled back, its repeat/immediate/retention deltas no
longer contribute to repeat_improved_this_call, repeat_regressed_this_call,
repeat_unchanged_this_call, mean_repeat_delta_this_call,
mean_immediate_delta_this_call, mean_old_delta_this_call, rolling repeat
trend, or the patience clock. The attempted pass remains available under
attempted_run_metrics and rejected_run_metrics, and its teacher rewards and
strategy observations remain durable. In other words: discarded neural
weights do not masquerade as progress of the current model, but the teacher
still remembers what happened.

With candidate-grade-gate enabled, a grade lesson is no longer allowed to
write directly into the production student merely because its optimizer ran.
Each teaching strategy starts from the current durable student+AdamW state and
trains a candidate branch. A clearly negative teacher reward rejects that
branch immediately. Positive or ambiguous local outcomes are checked against
a fixed all-compiled-grades sentinel using continuous cross-entropy,
correct-class probability and logit margin in addition to accuracy. A local
win can therefore be vetoed when it damages the broader curriculum.

Promoted candidates become the new student and receive a durable checkpoint.
Rejected candidates are discarded by reloading the unchanged live checkpoint,
but their teacher reward, strategy, losses, probe outcomes and sentinel
evidence remain in candidate_ledger so the teacher learns from the attempt.
The teacher may try up to candidate-max-attempts strategies for the grade.
If none demonstrates enough benefit, the grade advances with no student or
AdamW change instead of forcing an unproven lesson into the learner. Attempted
optimizer work is tracked separately from promoted student optimizer work.

Local and holistic champions are intentionally separate. Each G01-G22 keeps
one recoverable personal-best checkpoint using a dedicated 48-example
grade-champion panel that is distinct from both the 24-example teaching probe
and the cross-grade sentinel. The live progress line reports the promoted
checkpoint's score versus that grade's prior personal best, and checkpoint
retention pins every current grade champion. A grade champion is a benchmark
and archive, not the parent for the next lesson: rewinding to G07's historic
best merely to teach G07 again could silently discard later gains in the other
grades and their AdamW history.

The pass champion remains a separate whole-student concept. It is selected by
simultaneous all-22 evaluation and is the rollback anchor for broad regression.
Thus a checkpoint can be the best G11 student ever seen without being the best
overall student, and a holistic champion can be slightly below a historical
personal best on several individual grades.

To test whether those local optima combine constructively without touching the
live learner, run:

    python3 -m bilqis_school.engine --run-dir <RUN> --device cpu --evaluate-grade-champion-soup

This creates an inference-only grade-weighted model soup in memory by averaging
the model weights referenced by the 22 personal-best checkpoints and evaluates
it against the single holistic pass champion. A checkpoint that champions
multiple grades receives corresponding grade weight in the average. AdamW
moments are never averaged or attached to the soup, and the command never
changes state.json or the live checkpoint pointer.

To distill a winning soup back into the continuing student without replacing
its optimizer lineage, add:

    --candidate-grade-gate --consolidate-grade-champions --consolidation-weight 0.15

The current live student remains the parent because it owns the legitimate
AdamW history. The grade-champion soup is frozen for the whole invocation and
acts only as a second logits teacher. On each training row, soup KL is applied
only when the soup itself predicts the oracle gold label correctly; wrong soup
answers receive no distillation weight. The ordinary parent-retention KL and
supervised cross-entropy remain active.

Soup-guided candidate updates still face the ordinary per-grade candidate gate.
Any candidate otherwise eligible for promotion then receives a stronger
simultaneous 24-example x 22-grade confirmation. It must produce a positive
mean all-grade accuracy delta amounting to at least one net additional correct
answer across that 528-example panel, and may not lose two or more answers on
any single grade. A failure restores the exact pre-candidate model+AdamW state
while preserving teacher evidence. Candidate ledger records include the frozen
soup manifest digest, distillation strength, trusted-row coverage, consensus
KL and the full-school confirmation receipt. The pass champion remains the
separate final rollback anchor at the end of the complete G01-G22 pass.

Long-running development should also enable bounded checkpoint retention:

    --prune-checkpoints --keep-recent-checkpoints 8 --keep-pass-checkpoints 4

Pruning runs only after a durable state pointer exists. It always preserves
the current live checkpoint, the untouched School50 starting checkpoint, the
accepted pass checkpoint used by rollback protection, and both sides of any
recorded function-preserving architecture migration. It additionally keeps
the requested rolling tail of recent grade checkpoints and recent G22
pass-end checkpoints. Older binary checkpoints are deleted, but their grade
ledger, teacher statistics, pass reports, hashes and rollback history remain
in state.json. Existing oversized runs are migrated/report-initialized before
the first pruning pass, so the starting baseline and accepted pass are known
before any historical checkpoint can become eligible for deletion.

Run a short CPU session:

    python3 -m bilqis_school.engine --device cpu --minutes 10 --max-updates 100000 --block 32

Explicitly test whether all fifty grades have source-backed compilers
(expected failure until G23-G50 are implemented):

    python3 -m bilqis_school.engine --require-full50 --minutes 1

Promoted student updates create a new checkpoint under ignored
runs/school50-continuous-v1; rejected/no-update candidate lessons do not
create redundant student binaries. With 10.7 million trainable parameters
and full AdamW moments, long runs can still consume substantial storage.
When --prune-checkpoints is enabled, redundant history is removed according
to the protected retention set above. The generated-checkpoint quota still
stops cleanly at a grade boundary before new writes reach the cap, with a
separate 512 MiB free
volume reserve. Increase --max-run-gib only after confirming available
space; design and explicitly authorize a rolling checkpoint-retention
policy if running unattended for many hours. It must never destroy the
independently custodied learner.

The model parameters are not in public Git and their absence is a hard
error, not a license to create a randomly initialized replacement student.
The checked-in ACTIVE_SCHOOL_POINTER.json identifies the working live state
under the ignored run directory. After a school run exists, it supersedes
the old U7F ACTIVE_LEARNER.json as the active school pointer. U7F remains
a preserved source ancestor. An absent school run directory in a new
checkout is a missing learning artifact, not permission to pretend the
latest student is still at step 13,848.

## Ithkuil truth and provenance

The official current 2023 New Ithkuil source is https://www.ithkuil.net/.
The existing source map in references/ithkuil-grammar-source-map.csv
separates implemented subsets, specifications, deferred concepts and
source questions. The 36-cell human-authored diagnostic fixture is NOT
a complete Ithkuil lexicon or grammar and must not be relabeled as one.

The official New Ithkuil lexicon has thousands of roots, roots have
multiple stems, and morphological Specification changes interpretation.
A root spelling or English gloss is not a complete, validated semantic
target. Source version, stem, interpretation, scopes, negative examples,
and accepted compositional operations are required before a grade may
give it to the neural student as supervised gold. Raw New Ithkuil source
publication rights remain unresolved in the repository rights register;
the implementation must not publish a bulk verbatim harvested lexicon.

The practical next milestone is to compile the first real New Ithkuil
grammar grades with typed semantic ASTs and source-verified minimal pairs,
then ingest root lexemes under a verified source/rights pipeline. Expand
learned token identity without deleting old acquired representations.
Only then can all fifty grades run rather than just G01-G22.
