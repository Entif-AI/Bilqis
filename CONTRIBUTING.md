# Contributing to Bilqis MLX

This is the public source repository for a human-operated MLX student and teacher project. Source changes, disposable tests and read-only inspection are allowed. Only the human operator starts or resumes training the real student. Protected source-authority material, model bundles and actual training state do not belong in Git.

## One canonical checkout

Work in `~/Code/bilqis-mlx`. The root `bilqis_mlx/` owns active software. The pinned `vendor/legacy-v16/` contains immutable historical source code needed by the teacher and source oracles. All new development belongs in `bilqis_mlx/`, never in the vendor directory.

Ignored `runs/`, `vendor/legacy-v16/runs/`, `.local/`, and `data/` store mutable local data. `BILQIS_STORAGE_ROOT` explicitly relocates the active run root. Do not use an unstaged checkout or an external sibling repository as an implicit runtime dependency.

## Changes and commits

Use Conventional Commit subjects: `feat(scope): …`, `fix(scope): …`, `docs: …`, `test: …`, `refactor: …`, `perf: …`, `ci: …`, `build: …`, or `chore: …`. Breaking changes use `!` and a corresponding migration note. Each commit should leave independently verifiable code. `python3 -B scripts/maintenance/release_version.py --validate-subject 'fix(training): preserve custody'` checks the syntax.

Run `python3 -B -m unittest discover -s tests -q` on Apple Silicon for the full MLX-dependent suite, plus `npm run quality:check` and `npm run release:check`. The portable GitHub CI intentionally does not create neural updates, download the human student, or claim Linux MLX parity.

## Release discipline

Tag releases with immutable annotated SemVer tags `vMAJOR.MINOR.PATCH`. Python and npm project versions must agree, and `CHANGELOG.md` must include a dated version section. Run `npm run release:check` before tagging. Verify the release tag points at the same reviewed commit on `main`. `.github/workflows/release.yml` checks the tag and publishes GitHub Release notes derived from the checked-in changelog.

Never re-tag a release after publication. Use another patch version to correct an error. Experimental checkpoint scores and best-of-history markers are not claims of qualified neural performance.
