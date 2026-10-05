# Developmental teacher and model-assistance routing

## Authority layers

The world generator defines a candidate world under a frozen finite specification. Two deterministic oracle implementations must agree on its answer before admission. The scheduler decides which already authorized skill family to expose. The student consumes only encoded semantics and receives the formal target as the supervised loss. A language-model pedagogue may propose an eligible stage and seed offset. It cannot certify a target, write executable generator code, revise the ontology, grant promotion, or inspect sealed material.

This is the operational meaning of 'LLM proposes; formal machinery disposes'. An attractive explanation is not an oracle. A valid signature is not truth. A high teacher confidence score is not a mastery observation.

## Actual stage machine

Stages are identity (0), configuration (1), purpose/use (2), composition (3), and evidence composition (4). The topology is 0 before 1, 2 and 4; both 1 and 2 before 3. At each tranche boundary the topology scheduler chooses an eligible unpromoted stage with the fewest completed tranches, breaking ties by stage ID. The difficulty control ignores prerequisite eligibility but retains the same tie-breaker. Once all stages are promoted, stage 3 is revisited. One in four batch positions rehearses prior promoted stages when such stages exist.

Promotion requires the current stage's 95% Wilson lower bound to reach 0.90, all previously promoted stages' lower bounds to remain at least 0.85, and current-stage DEV transfer accuracy to reach 0.75. Transfer uses entity-order reversal and, for composed stages, deeper queries. These are engineering decision thresholds, not repeated-testing-adjusted scientific confidence statements. Reusing DEV data can overfit development decisions. The independently held, fixed-milestone SEALED evaluation is what protects the later confirmatory estimate.

Failure of a competence criterion leaves the stage unpromoted and records remediation or budget exhaustion. Failure of a data/oracle/integrity check enters a hold. No validation-loss value can override those decisions. The global exposure cap terminates the run even if the teacher keeps proposing the same weak skill. Report the unresolved stage and all spent exposures; do not drop stalled students from the comparison.

## Pedagogue replay interface

`prompts/local-pedagogue-system.txt` is the fixed role instruction. A request contains the current stage, aggregate development errors, a contract digest and the allowed output fields. An accepted response contains exactly `request_sha256`, `stage`, `seed_offset`, `focus` and `rationale`. The stage must be eligible; the seed offset must be 0..100000; focus belongs to contrast, rehearsal, distractors or scope; rationale is at most 2,000 characters. The formal generator still chooses and checks each actual example. In this ABI, focus and rationale are audit metadata only. They are not inserted into the learner stream and do not secretly change a loss or truth function.

The runner optionally accepts an immutable assistance replay JSON through `config.assistance.replay_path` and `replay_sha256`. Entries are keyed by the exact request hash and include `proposal`, `model_identity_sha256` and `route_ledger_id`. A missing request produces `pending_teacher_request.json` and stops that student at its last intact checkpoint. A changed replay hash or missing model identity is a hard error. Resume requires the applicable original config identity; extending a replay constitutes an explicit child config/lineage, not an invisible edit under the same hash. For a fully prerecorded main trial, prepare the adaptive interaction through the approved live adapter or use a content-addressed event store rather than changing a single frozen replay file. The delivered append-only event-store adapter supports adaptive requests. `python -m bilqis_ref.assistance` fills one pending request from a separately operated loopback-only OpenAI-compatible local service, binds model identity and raw-response hashes, and refuses duplicate event writes. Student resumption rechecks previously consumed event hashes. Interface, replay and endpoint-rejection tests passed. No actual Qwen service or weights were run in this production session.

A local Qwen-class model is the preferred pedagogue class in the source policy. This package does not invent a downloaded checkpoint, hardware fit or model revision. Before intervention-plane use, the operator must choose and record the actual local weight files, upstream revision, tokenizer files, inference-engine build, chat template, decoding settings, context limit and quantization recipe. Both SYS arms receive the same model identity, prompt policy, maximum request count, decoding policy and opportunity to affect the curriculum. Adaptive responses may differ because the students differ; that difference belongs to the system treatment and must be logged. A later representation-only attribution branch replays a common fixed exposure sequence instead.

## Research plane versus intervention plane

This production run's literature, writing, code construction and internal adversarial analysis belong to the research plane. They were performed with GPT-6 Astra Pro assistance and local deterministic tooling. No intervention-plane local model was run. Do not charge this research assistance as though it were replicated student training, and do not hide it when estimating total program cost.

The routing ladder is formal code/oracle, then local routine model, then approved inexpensive reproducible API, then stronger hosted reasoning, then frontier research assistance. Complexity and disclosure are separate axes. Private or sealed material cannot be routed externally merely because the task is easy or the provider is cheap. No new paid API calls are authorized here.

Each consequential routed operation records a route ID, plane, task, complexity/disclosure class, provider/model version if exposed, prompt/input/output hashes, acceptance criterion, execution time, token use when available, marginal cost or explicit unavailable status, escalation reason and condition impact. Unknown usage is null, not zero. Current research-plane records identify subscription-bundled assistance without pretending to know metered inference tokens or economic cost.

## Declassification and substitutions

Only approved TRAIN and DEV material may enter teacher requests. SEALED examples, generator-family implementations, outputs and failure clusters remain with the custodian before the permitted opening. Once a milestone is opened, its results may be interpreted but not used to repair the same lineage and claim the reopened milestone as untouched evidence. A provider/model substitution after lock requires an amendment and a new affected confirmatory epoch. Match by exact identity, not a marketing family name.
