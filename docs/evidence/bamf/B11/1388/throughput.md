# Issue #1388 four-row B11 throughput witness

## Scope

Issue #1388 reduces residual cost in the existing 12-layer BAMF B11/C08 training path. It does not change model topology, source authority, targets, optimizer semantics, candidate custody, or the one-vectorized-launch policy.

The measured hotspot was post-gradient route evidence construction. The vectorized route kernel already computed the model-owned logits and causal trajectory. The old post-gradient path decoded each row again, fingerprinted each decision separately, and deep-copied the same frozen route plan and Atlas snapshot for every issued output.

The repair reuses the exact materialized vector-route logits and trajectory. It batches trajectory extraction and logit fingerprinting, then issues route-only evidence against the already-frozen `AnswerPlan` without copying that immutable semantic graph. Non-route outputs retain the existing copy-and-attest path.

## Environment and workload

- Baseline Git SHA: `7c074d05c042855e6064312d582155e3e14c6430`
- Feature branch: `codex/1388-b11-mlx-throughput-20261118`
- Host: `m3-ultra` / Apple M3 Ultra
- Python: 3.14.3
- MLX / MLX Metal: 0.32.4 / 0.32.4
- NumPy: 2.5.4
- Factory capability: `B.COMPOSITE`
- Source seed: `37129`
- Logical rows: 4
- Compiled positions: 52 (`14, 14, 12, 12`)
- Gradient launches: 1
- Vectorized microbatches: 1
- Scalar fallback rows: 0
- Pinned A01 bundle: `5f8fba20ecc0adebf39c3b663fdffa4f766e780915197f09d116713042a479e7`

All runs were disposable. They did not open or mutate the accepted learner. Long-running measurements ran detached over SSH on `m3-ultra` and disabled MLX's free-buffer cache for the full candidate-step comparison.

## Focused B11 comparison

Five measured samples followed one warm-up on each implementation. Both sides used the same four Factory rows, topology, artifact, hardware, and MLX version.

| Metric, median | Baseline | Candidate | Change |
| --- | ---: | ---: | ---: |
| B11 autodiff + evidence wall | 4.3083 s | 2.2896 s | **-46.9%** |
| Four-row logical-batch wrapper wall | 7.7017 s | 5.5865 s | **-27.5%** |
| Post-gradient row evidence | 2.6491 s | 0.3889 s | **-85.3%** |
| B11 preflight | 0.2019 s | 0.2016 s | -0.1% |
| MLX eval calls in instrumented B11 path | 16 | 5 | -68.8% |
| Materialization barriers | 1 | 1 | unchanged |
| Gradient launches | 1 | 1 | unchanged |
| Scalar fallback rows | 0 | 0 | unchanged |

The candidate exceeds the issue's initial 20% B11 target. The differentiated graph-build slice did not become the source of the speedup. The gain came from removing repeated evidence work after the gradient graph had already produced the exact route logits and choices.

## Full disposable candidate-step comparison

Three independent full candidate steps were run from fresh temporary generation-zero runs on each implementation. The MLX cache limit was zero. The median captures source compilation, currentness binding, B11/C08, optimizer admission, and the candidate-step owner.

| Metric, median | Baseline | Candidate | Change |
| --- | ---: | ---: | ---: |
| Candidate step wall | 36.7616 s | 33.6231 s | **-8.5%** |
| B11 autodiff + evidence | 5.5190 s | 3.0611 s | **-44.5%** |
| C08 logical batch | 7.1942 s | 4.5986 s | **-36.1%** |
| Pre-neural source compile | 21.2050 s | 20.8353 s | -1.7% |
| Peak MLX memory | 6.229 GB | 6.227 GB | effectively unchanged |
| MLX cache memory at completion | 0 B | 0 B | unchanged |
| Provider redraws inside B11 | 0 | 0 | unchanged |
| Atlas reloads inside B11 | 0 | 0 | unchanged |
| Optimizer updates | 1 | 1 | unchanged |

The full-step gain is smaller because source compilation dominates this disposable cold-path fixture and is outside #1388. The issue-owned B11/C08 cost falls materially without moving equivalent cost into source preparation or optimizer admission.

## Semantic and custody invariants

The route fast path uses only fully supervised, route-compatible microbatches. It preserves the model-derived causal trajectory and uses supervision only for loss. Ambiguous and non-route cases keep the existing safe path.

Focused regressions compare vectorized loss and gradients against the scalar FP32 reference and compare committed typed route outputs. Batch attestation still fingerprints every issued decision from its exact FP32 logits, but one host transfer serves the complete microbatch. The optimized no-copy issuance is restricted to route-only outputs whose plan, decisions, candidates, and committed values are immutable route semantics.

The production-path witness retains one four-row gradient launch, zero scalar fallback, zero source redraw inside B11, and one optimizer update. Temporary runs are discarded after measurement, so no benchmark changes accepted state.

## Remaining cost

After this repair, the focused B11 median is about 2.29 seconds. Graph construction is now the largest measured B11 component at roughly 1.7 seconds. That is the cheapest architecture-preserving next lever if later throughput work is warranted. #1388 does not precommit to MLX graph compilation or caching because this repair already exceeds the requested target without adding a new runtime cache or parameter identity.

## Verification classification

Post-checkpoint verification on `m3-ultra` at feature SHA
`83c9e03b0254a45c401729aacb8ff5a2a748d81c` produced these current results:

- changed-path decoder/microbatch/trajectory suite: **15 passed**, one unrelated skip;
- broader Factory execution + Factory microbatch suite: **16 passed**, 11 environment-dependent skips;
- participation, motif-gradient, source-adapter, candidate-custody and execution-binder integrity suite: **39 passed**, six environment-dependent skips;
- the same broader Factory suite also passes on untouched unified baseline
  `7c074d05c042855e6064312d582155e3e14c6430` with the same 11 skips.

One additional refinement-kernel test fails before reaching #1388 on both candidate and untouched baseline because the installed MLX 0.32.4 runtime exposes no `mx.flip`. Candidate and baseline both report the same `AttributeError` in
`test_batched_refinement_matches_scalar_zero_one_two_pass_rows`; the remaining 39 integrity tests pass on the candidate. This is pre-existing environment/test compatibility debt, not a candidate regression.

The scalar-vs-vector B11 parity test proves one `mx.value_and_grad` launch for four rows, identical committed typed outputs, FP32-equivalent mean loss, and FP32-equivalent gradients for every returned parameter. The production-path witness used the real four-row `B.COMPOSITE` workload described above.
