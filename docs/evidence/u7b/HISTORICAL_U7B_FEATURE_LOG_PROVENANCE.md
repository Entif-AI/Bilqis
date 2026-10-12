# U7B historical worklog preservation

The adjacent `HISTORICAL_U7B_FEATURE_LOG.md` is the exact, unedited
`FEATURE_LOG.md` from U7B's pre-integration draft head
`3441a622a9028a49ce535143b4cad2db4fc92545`.

- Git object identity: `8125c82ece1a253f38464e054a265e18f644274b`
- Source read: `git show 3441a622a9028a49ce535143b4cad2db4fc92545:FEATURE_LOG.md`
- Preserved copy SHA-256: `bc0d46b5027accc7c5e84b4ba72b8822962a7774af112f203dc675fbd7578b53`

U7B was originally constructed against an older, divergent version of
the stacked U6 branch. The current U6 parent (#111, head
`280b4df6228d9c942e941b7f78c669cb55813647`) already carries a
**different** root `FEATURE_LOG.md` from the earlier Alpha work
(Git blob `61e092e0fdc7f8db39bc9bc056fcdc40817f4466`). That Alpha
content is also present in `main` at this integration point.

The parent-sync merge **retains the parent/root Alpha blob unchanged**.
The historical U7B text remains available in both this source-exact
copy and the original U7B parent commit. Its factual decisions are also
referenced from the U7B public PR, accepted/failed evidence artifacts and
canonical outreach/ledger closeout links. It is *not* a current shared
working log or a new requirements authority.

Future feature progress belongs in issue-scoped checkpoints or other
authorized durable research records, not by competing writes to a
tracked root `FEATURE_LOG.md`.
