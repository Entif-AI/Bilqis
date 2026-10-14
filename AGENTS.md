# Bilqis public source instructions

Read `README.md`, `docs/PROVENANCE.md` and `docs/RELEASE_HISTORY.md` before modifying the public repository.

The current supported entrypoint is `bilqis_ref`, with the small deterministic reference fixtures and tests in this tree. Earlier School50, U-series, alpha, formal and developmental experiment code, test suites and generated run evidence are historical. Read them at immutable `v0.0.0` instead of reintroducing them to the default checkout without a new supported capability and its tests.

Do not claim that a successful reference smoke test, old release tag, or historical best score proves a golden neural student. The full-state and current-capability criteria are in `docs/GOLDEN_RELEASE_GATE.md`. Do not start neural training or publish any checkpoint on the basis of this source checkout.

Keep original research sources, scientific scope and provenance unchanged in the archival tag. Maintain the current reference ABI and code-to-test behavior. Make changes on feature branches. Run `python3 -m unittest discover -s tests -v` and the repository commit hooks. A public PR must pass the required GitHub checks before review or merge.

Never copy private research checkpoints, hidden curricula, credentials, machine-local state or protected project material into this public tree merely because it is accessible to an agent. Do not create a root `FEATURE_LOG.md`. Current task state belongs in the PR and its verified commit history.
