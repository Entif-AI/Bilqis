# Public-source contribution and release controls

Bilqis uses [Conventional Commits](https://www.conventionalcommits.org/) as the source of SemVer intent. Every PR to protected `main` must pass the Python reference suite and the Conventional Commit checks. Local Husky hooks are additional developer convenience, not a replacement for server-side checks.

## Git hooks

`npm ci` installs the dev toolchain and, through the `prepare` script, activates Husky for a normal clone. Install Node.js 24 or another compatible active Node version.

- `.husky/pre-commit`: reject staged whitespace errors.
- `.husky/commit-msg`: lint the actual commit message with `@commitlint/config-conventional`. Git has **not yet created the final message at pre-commit time**, so message validation belongs in this later hook.
- `.husky/pre-push`: run the entire Python unittest suite and refuse the push if it fails. Use `npm run test` to run the exact same suite directly.

Examples: `fix: reject mixed-step graduation receipts`, `feat(curriculum): add counted finite-set lessons`, `docs: maintain release archaeology`. A breaking change requires `!` or a `BREAKING CHANGE:` footer.

## Branch protection and continuous integration

The existing `.github/workflows/test.yml` runs the Python suite on every PR and push. `.github/workflows/conventional-commits.yml` validates PR titles and each commit before merging to `main`. Configure `main` branch protection to require a PR and the `unit` and `commit-messages` job contexts; do not permit force pushes or deletion. Release bots must not bypass this PR-only contract to write generated change logs directly.

## Releases and version advancement

[`v0.0.0`](https://github.com/Entif-AI/Bilqis/releases/tag/v0.0.0) is an intentionally archival first snapshot on public `main` commit `a8d1360b75f42a637da5928863ed51c0178ddf21`. It is not a qualified neural milestone.

The [Release Please Action](https://github.com/googleapis/release-please-action) analyzes Conventional Commits merged into `main` since the previous tag and prepares an additional **release PR** containing the next SemVer and the updated root `CHANGELOG.md`. A release tag and GitHub Release are created when that release PR passes review/CI and merges. This extra PR is deliberate: putting the generated changelog in the tagged commit **without** bypassing the PR-only main rule requires the changelog change to be merged normally.

**Review/CI gate:** GitHub changed the behavior of PRs created by
`github-actions[bot]` on June 11, 2026. A PR opened or updated with
`GITHUB_TOKEN` now generates the normal `pull_request` CI runs in an
**approval-required** state. This is a deliberate human security gate, not a
broken test or a signal to bypass protected `main`. A maintainer with write
access must inspect the generated diff (normally only
`.release-please-manifest.json` and `CHANGELOG.md`) and select
**Approve workflows to run** on the PR, or approve the exact pending runs
through GitHub's documented Actions approval endpoint. The two ordinary
`pull_request` CI jobs then run in their original security context on
that PR, and protected `main` requires both passing before the release
PR can merge. GitHub's [bot PR announcement](https://github.blog/changelog/2026-06-11-bot-created-pull-requests-can-run-workflows-if-approved/)
and [GITHUB_TOKEN event contract](https://docs.github.com/en/actions/concepts/security/github_token)
are the controlling sources.

Do not confuse these approval-required CI jobs with explicitly dispatched
`workflow_dispatch` jobs. Dispatch results alone **do not satisfy GitHub's
protected PR checks**, regardless of matching source and/or synthetic
merge-tree hashes. The temporary attestation experiment was removed:
the repository no longer grants a release attestor `checks: write`,
issues synthesized required check runs, or attempts to shortcut user
approval. The Release Please job needs only its scoped
`contents: write`, `pull-requests: write` and `issues: write`
permissions; the default repository Actions token remains read-only.
Repository settings must still allow Actions to create PRs.

An optional future **dedicated limited-scope GitHub App**
`RELEASE_PLEASE_TOKEN` could create release PRs without this manual CI
approval if a separately reviewed policy warrants it. Do not place a
maintainer's broad personal token into repository secrets. The present
design deliberately retains human approval for bot-generated CI and for
merging releases.

A new golden-model release additionally requires one complete same-checkpoint assessment receipt for every current grade/capability, model+its own AdamW checksums, curriculum/ABI identity, and a reviewed scientific manifest. Neither passing CI nor merging a code PR creates an unverified golden checkpoint.

The history index at [`RELEASE_HISTORY.md`](RELEASE_HISTORY.md) links back to exact historical paths even after curating them out of the current checkout.

### Release qualification versus software-source SemVer

The release PR and its two required checks prove repository integration,
not cognitive capability. New neural-model golden milestones need independent
same-checkpoint current-rubric assessments on a fully archived FP32
model + its own AdamW, separate reviewed manifest and immutable model
release evidence. A source SemVer `v0.1.0` or passing unit suite never implies
all 29 Bilqis grade capabilities reached 100%.
