# C05 #1167 design: fixed-school MLX evaluation batching

## Owned outcome

Reduce C05 fixed-school neural backbone executions by evaluating compatible cases in bounded multi-row MLX batches. Preserve C04 `TaskGoal`, source/operator/scope/generation semantics, the scalar complete-solver CPU path, per-case typed results and solver contracts, C05 retention policy, accepted-generation semantics, and evidence attribution.

## Existing execution seam

`evaluate_capabilities()` currently calls `CompleteSolver.evaluate()` once per case. Factory C05 builds each `SolveContext` in `factory_complete_solver()`. When a case reaches C04 neural composition, its proposer calls `forward_bamf()` for one `BamfCompiledBatch`. B01/A05 encoding and the source backbone already support multiple independent rows in one padded tensor, but the public B11 task proposer intentionally binds one source row and one task authority.

The optimization therefore belongs above the unchanged C04 solver semantics and below C05 case iteration: precompute only the issued neural `ModelOutput` for each compatible case with one multi-row backbone execution, then let the ordinary `solve_task()` execute each case independently. The case's neural-proposer closure receives C04's live `NeuralRequest` and mints the `NeuralProposal` only at that point.

## Chosen architecture

1. Extend `CompleteSolver` with an optional immutable `contexts_for: Callable[[tuple[TaskGoal, ...], str], tuple[SolveContext, ...]]` and an `evaluate_cases()` method. Factor the current `evaluate()` body after context lookup into one private/common measurement helper so `solve_task()`, `GenerationBinding`, and solver-contract hashing remain identical for scalar and batched preparation. Existing solvers without `contexts_for` preserve exact scalar `context_for()` behavior. `evaluate_capabilities()` uses `evaluate_cases()` and still constructs the same `Assessment` in cohort order.
2. `factory_complete_solver()` supplies `contexts_for`. It prepares each case through the same existing compilation, task-authority, route-plan, and source-binding functions used by scalar `context_for()`, amortizes only the compatible B11 numerical work, and returns one ordinary `SolveContext` per requested goal in the same order. `CompleteSolver` then measures those contexts through the common scalar measurement helper.
3. Cases are batch-compatible only when all of the following side-effect-free predicates hold after ordinary scalar preparation has already validated source/task/generation custody: same candidate generation, topology/extents/features/active-semantic identity, source feature schema, inference mode, no accepted execution cache, non-empty `task_goal_route_decisions(goal)`, and the Factory-created `SolveContext` has empty `qualified_compositions`, no `deterministic_fallback`, no `local_refiner`, and the ordinary default route registry. Those Factory conditions prove the unresolved TaskGoal must reach NEURAL_COMPOSITION after its exact attempt. A false compatibility predicate or a resource capacity of one selects the existing scalar B11 proposer. **Validation exceptions, source/task/generation/custody drift, producer failures, and shared-execution failures never trigger scalar fallback; they propagate fail-closed exactly as the scalar path would.**
4. For each bounded compatible chunk, combine the already source-validated `CompiledEncoderInput` rows transiently. No reusable compiled-cohort artifact is persisted, so #1168 remains independent. Start one source backbone producer over those rows and complete its 12-layer execution once for the chunk.
   - Each prepared case retains its original single-row `BamfCompiledBatch`, `FactoryTaskAuthority`, route plan, and source row. Before any decode/refinement, call the existing `bind_factory_task_compiled_batch(original_batch, authority)` and retain that returned task-owned single-row batch. The transient multi-row producer is numerical/source custody only; every B11 row decode receives the task-owned single-row batch so `_prediction_local_refinement()` sees the same `task_authority` as scalar `b11_task_goal_proposer()`.
   - The transient producer input is constructed in requested-case order from those single-row inputs: collect `compiled.compiled.rows[0]`; set padded width to the maximum position count in the chunk; construct one `CompiledFrameRows` whose `rows` are those original rows, whose `padded_positions` append `None` to that width, and whose `padding_mask` appends `False` correspondingly.
   - Construct one transient `CompiledEncoderInput` from that `CompiledFrameRows`, the original cases' `compiler_configs[0]`, common `features`, common `extents`, original `source_asts[0]`, and original `partial_forest_receipts[0]`. The `CompiledEncoderInput` constructor therefore creates and validates the shared `PackedFrameArtifactOwner`; do not invent or copy an artifact owner manually.
   - Pass the original cases' `sources[0]` as an ordered tuple to `start_source_backbone_producer()`. Use the first task-owned case's `feature_schema`, `active_semantic_rows`, and `atlas_feature_artifact_owner` only after requiring exact equality of `feature_schema`, `active_semantic_rows`, `compiled.features`, and `compiled.extents` across every case. Call `first.atlas_feature_artifact_owner.require(transient_compiled.features)` before producer construction; pass that same owner to `start_source_backbone_producer()`. No new feature owner is minted for the transient tensor because its features/schema are exactly those already held by the first original task batch. The transient row index is exactly the requested-case index within that chunk; this row index is passed only to shared-producer read/refinement logic and never replaces the case's own source/task identity.
   - Do not call `compile_prefix_rows()` again. Each row was already independently compiled and source-validated by `compile_factory_evaluation_batch()`; the transient object performs padding/stacking only and keeps each original compiled row byte-for-byte/equality-identical.
5. B11 remains the sole owner of row decoding and forward issuance. Refactor `atlas_model_forward.py` so the existing scalar `_forward_bamf_impl()` and C05's shared-producer path both call one B11-owned internal helper, `_decode_bamf_producer_row(backend, params, compiled_batch, answer_plan, producer, final_hidden, row_index, accepted_cache=None)`. The helper revalidates the original single-row `BamfCompiledBatch`, plan, backend, generation, source projection and row custody; requires `producer._compiled.compiled.rows[row_index] == compiled_batch.compiled.compiled.rows[0]`; sets `row_hidden = final_hidden[row_index, :len(original_row.positions)]` so chunk padding can never become salience/readout input; derives `salience_hidden = row_hidden[-1]`; runs prediction-local refinement using the same producer row; constructs `DecoderMemory` from the original row's exact cache identities; calls `predict_typed()`; creates the per-case `_forward_participation()` record; and issues the `ModelOutput` through `_FORWARD_ISSUANCE`. Scalar `_forward_bamf_impl()` calls it with row index zero after its existing one-row producer execution, so scalar behavior and B11 ownership remain unchanged. C05 never calls `_FORWARD_ISSUANCE` or `_forward_participation()` directly.
   - The live multi-row fixture exposed one pre-existing B11 padding mismatch at depth selection: `FrameEncoding.global_seeds` is padded to chunk width, while `FrameEncoding.features` retains each row's natural length. `source_depth_select_with_diagnostics()` currently rejects that lawful mixed-width state before it can construct its numerical feature tensor. Amend the B11 depth selector so each feature-factor row is padded with `None`/zero feature vectors to `encoded.global_seeds.shape[1]` before stacking. Existing non-padding positions retain the current validation and factor vectors; extra padded positions contribute exact zero vectors. Scalar/same-width behavior is unchanged.
6. Cache only each case's already decoder-issued and B11-issued `ModelOutput`, never a `NeuralProposal`. Feed the case through the unchanged C04 `solve_task()` path with a request-validating neural-proposer closure. When `solve_task()` reaches neural composition it creates the authoritative live `NeuralRequest`, including the exact unresolved signature produced by prior exact-DAG evaluation. The closure validates goal/source/generation/operator scope against that request and only then calls `proposal_from_task_goal_output(goal, live_request, cached_output)`. Exact CPU operators, dependency-DAG evaluation, proposal-receipt construction, route accounting, and typed result construction therefore remain authoritative and unchanged.
7. Bound chunk size from the **compiled B11 position count**, not raw Factory token count. Reuse the historical inference envelope numerically: at most the activation work of `24 * 96` positions and the attention work of `24 * 96^2` position-pairs. Let `L` be the maximum `len(compiled_batch.compiled.compiled.rows[0].positions)` in the candidate chunk; when `L > 96`, use scalar execution because that row already exceeds the historical batching envelope. Otherwise capacity is `min(case_count, floor((24*96)/L), floor((24*96^2)/L^2))`, with a minimum of one. Preserve input order and split oversized groups into deterministic consecutive chunks. This is a C05-specific compiled-position policy; do not call the raw-token `inference_batch_rows()` helper because its input metric is wrong for this tensor.
8. Expose evaluation-only launch telemetry from the factory solver so the bounded regression/timing witness can prove reduced backbone executions without making telemetry part of acceptance authority.

## Alternatives considered

### Batch complete C04 solver execution
Rejected. CPU DAG execution is already cheap and semantically ordered per case. Vectorizing it would enlarge C04's authority surface without removing the dominant MLX cost.

### Change `BamfCompiledBatch` to become a multi-task public B11 contract
Rejected. That would alter a shared B11/C04 interface and task-authority assumptions for a C05 throughput leaf. The transient evaluation batch can reuse the lower-level source backbone's existing multi-row support while each public task batch remains one row.

### Cache or reuse compiled cohorts
Rejected for this leaf. Persistent/content-addressed compilation reuse is owned by #1168. #1167 may compose with it later but must independently reduce neural execution count.

### Reuse parent predictions across candidates
Rejected for this leaf. Cross-candidate parent reuse is owned by #1166 and has different invalidation semantics.

## Failure semantics and limits

- A false explicit compatibility predicate or batch capacity of one takes the existing scalar path; it does not change answer or retention semantics.
- Scalar fallback is selected only by explicit compatibility/resource predicates evaluated on already-valid prepared cases. An exception or failed authority/provenance validation is not a compatibility result and MUST propagate.
- Batch execution never combines different generations or candidates.
- A batched row is not usable as a C04 neural proposal until both decoder issuance and B11 forward issuance have been created for that row. Batch execution may share the numerical producer; it may not share one case's participation record with another case.
- No evaluator gold enters neural input or batching keys.
- Ordering is stable: output index must correspond exactly to input case order.
- C05 evidence digests continue to derive from per-case `CapabilityResult` replay records and per-case solver contracts.
- The resource ceiling is deterministic and uses the historical 24-row/96-position envelope as an initial conservative cap, applied to actual compiled-position width. Rows above 96 compiled positions always use the existing scalar path. This cap is not itself proof of current B11 memory safety: verification MUST measure same-device MLX peak memory with `mx.reset_peak_memory()` / `mx.get_peak_memory()` for the largest exercised admissible chunk, record active/cache memory policy, and compare it with the repository's current allocation budget. If the measured chunk exceeds the current allocation budget, reduce the cap and repeat; the checked-in cap is accepted only with that witness. No host-sized allocator or unbounded batch size is introduced.
- Actual human-run training is outside this issue. Verification uses disposable/fixed fixtures only.

## Implementation locations

- Modify `bilqis_mlx/runtime/_capability/capability_evaluation.py`: optional `contexts_for` contract, common scalar measurement helper, and ordered `evaluate_cases()`.
- Modify `bilqis_mlx/runtime/_capability/factory/factory_complete_solver.py`: prepare case execution once and supply bounded factory `contexts_for`.
- Create `bilqis_mlx/runtime/_capability/factory/factory_evaluation_batching.py`: transient row composition, shared-backbone execution, calls into the B11-owned row decoder, chunk/fallback policy, and launch telemetry. It does not mint B11 provenance.
- Modify `bilqis_mlx/runtime/_model/backbone/atlas_model_forward.py`: extract the B11-owned row decode/refinement/participation/issuance helper shared by scalar and C05 batched execution.
- Modify `bilqis_mlx/runtime/_model/backbone/atlas_model_refinement.py`: preserve scalar row-zero behavior while allowing an explicitly supplied producer row index from the B11 row decoder.
- Modify `bilqis_mlx/runtime/_depth/depth_selection.py`: align source feature-factor rows with the encoder's lawful mixed-width padding by zero-padding only positions beyond each row's natural feature count.
- Create `bilqis_mlx/runtime/tests/capability/factory/test_factory_evaluation_batching.py`. It compares scalar and batched typed results, solver contracts, assessment/retention decisions, source/task/generation identity, mixed-width order, >96-position scalar fallback, bounded chunk splitting, and observed shared-backbone execution count.
- Create `docs/evidence/bamf/C05/1167-timing.md` after implementation. Record the exact disposable command/fixture, scalar and batched wall times, launch counts, identical observable result/evidence identities, compiled-position census, `mx.reset_peak_memory()` / `mx.get_peak_memory()` measurements for the largest exercised admissible batch, active/cache/allocation memory context, and machine context.

## Proof obligations

1. Same fixed-school cohort and generation produce byte-equivalent typed answer identities, per-case task digests, solver contracts, assessment digests, and retention decisions under scalar and batch modes.
2. A representative multi-case neural cohort executes fewer source-backbone runs than case count, with at least one chunk containing multiple rows.
3. Mixed or oversized cohorts preserve deterministic order and split/fallback without exceeding the explicit compiled-position activation/attention envelope; a >96-position case executes scalar.
4. Source family, episode, `TaskGoal`, generation, policy, and evidence digests remain unchanged.
5. Existing C04 solver and B11 single-row tests remain green.
6. A bounded real MLX timing witness shows lower fixed-school wall time on the same candidate/cohort while producing identical observable retention output.
7. A same-device current-B11 peak-memory witness proves the largest exercised admissible batch stays within the repository's current MLX allocation budget; if it does not, the cap is reduced until it does.

## Review identity

Design authority: GitHub issue #1167 plus this artifact. Pinned EGM: `b3a35956759bf7f024af2ff061b2e0b44b438e4c`.
