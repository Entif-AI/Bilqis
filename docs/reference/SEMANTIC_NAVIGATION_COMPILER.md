# Deterministic navigation compiler

The compiler consumes the frozen #69 corpus. `initial`, `panel`, and `apply`
own finite state, admissible candidates, and semantic consequences. A scorer may
select a candidate ID; it cannot supply a delta or invent an object.

Panel identity binds the complete current state and candidate set. Display order
may change while panel and candidate identities stay fixed. Applying an old,
cross-fixture, edited, or unknown panel/candidate fails. States bind the corpus,
revision, bounded evidence schedule, capability profile, and resolved references.

Only explicitly available evidence can support a factor constraint. Missing
distinctions preserve live alternatives and route to clarification or abstention.
Unsupported capabilities remain explicit. A single object resolves only after
the factor path is complete and selected constraints agree with available hints.
Structurally legal wrong interpretations retain their real consequences in
history; they cannot silently resolve a contradictory target.

`other` may traverse the fixture's declared deeper scope; it cannot invent a
continuation. All four reserved routes remain available. Previously resolved
references may omit repeated object payloads only when the receiver already owns
their content-bound bindings. `expand_view` reconstructs the identical view and
validates reference identity; this is deterministic referential compression,
not evidence of model cache reuse or learned sparse addressing.

Tests exercise all ten fixtures under eight display permutations, terminal
ambiguity/absence/capability handling, illegal and stale transitions, retained
wrong-step consequences, and reference parity/payload reduction. Run the full
reference unittest suite. This research prototype changes no Rosetta Core or
existing Bilqis ABI semantics and makes no learned-scorer qualification claim.
