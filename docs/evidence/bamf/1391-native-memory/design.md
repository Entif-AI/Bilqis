# Native BAMF training memory ownership — #1391

Issue: https://github.com/Entif-AI/Bilqis-MLX/issues/1391

## Contract

Reuse `bilqis_mlx/runtime/_model/mlx_memory.py::training_memory_policy` for the native `operate_bamf` session. No new cache policy, model topology, source, teacher, retention, custody or publication behavior. No serialized state or migration.

## Implementation plan

1. In `bilqis_mlx/runtime/bamf_operator/session.py`, add a private lazy context factory importing `mlx.core` and the existing memory policy. Pass this factory from `operate_bamf` into `_session_execution.operate`.
2. In `bilqis_mlx/runtime/bamf_operator/_session_execution.py`, add optional `training_memory_context` defaulting to no ownership. Enter its context after the existing source pool and writer lock, before currentness validation/profile adoption. Keep it active through all visits, accepted reentry, publication, stop receipt and final generation read. Exit before releasing writer lock/source pool. Lazy imports occur only after lock acquisition. Existing bounds validation and run-authority binding order remain unchanged.
3. Create `bilqis_mlx/runtime/tests/operator/session/test_bamf_operator_memory.py`. Call real `operate_bamf` with narrow boundary doubles. Verify cache zero during profile adoption, visits, accepted reentry and stop recording; restore prior limit on normal return and injected visit exception. Exercise real writer lock refusal, invalid bounds, resource stop and prefetch cleanup. Track model/optimizer references and values across policy entry/exit. Create companion `test_bamf_operator_memory_native.py` using actual MLX arrays and native AdamW, with one bounded disposable update in the visit, checking accepted and candidate identity/value preservation at exit.

4. Modify the existing portable tests that call `operate_bamf` with visit doubles: operator session rejection continuation/reentry, observed session/publication/championship, source-prefetch, operator routing, release-adoption native profile, and admission atlas v2 human resume. Patch only the private memory context factory to `contextlib.nullcontext` in those test classes, keeping their original lifecycle assertions. Production remains fail-closed when MLX is missing. New policy tests inject fake `mlx.core` through `sys.modules` and exercise the actual existing policy; hardware proof imports real MLX without substitution. No global fake MLX installation.

## Verification

Red focused tests before production edits; green after. Run existing operator session, source-prefetch, resume/publication and memory-policy tests. Then bounded disposable native smoke and leaf/premerge gates. All MLX runners single-worker with cache disabled and applied allocator bound. Long commands run snapshot-isolated and detached over SSH on m3-ultra, with completion desktop notification; no chat polling. Each run must have an estimated bound below two hours.

## Failure and ownership

Visit exceptions propagate unchanged and restore prior cache limit. Lock/bounds refusal never acquires memory ownership. Read-only inspection and non-neural CLI routes do not receive the factory. Existing policy clears only free buffers, preserving live model/AdamW arrays and accepted custody. Disk reserve behavior and one writer remain unchanged.
