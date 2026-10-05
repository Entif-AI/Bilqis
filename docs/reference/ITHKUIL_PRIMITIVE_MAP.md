# New Ithkuil to Bilqis: source dependencies and implementation coverage

This map is a compiler and curriculum plan, not a grammar of New Ithkuil and not evidence of an ML benefit. The official chapters and lexicon establish donor distinctions. `F00` through `F03` are author-defined formal scaffolding. The reference implementation handles a finite, explicitly named subset. The JSON/CSV map in Evidence is authoritative for machine navigation; its dispositions are summarized below.

## Why these first families

Identity and finite sets provide an independently testable semantic foundation. The configuration-inspired family then asks about cardinality, uniformity and connectedness. The use/purpose family asks a different kind of question: what an entity currently serves versus what it was intended to serve. Their separation creates controlled counterfactuals rather than a miscellaneous vocabulary lesson. Logical composition is taught only after its operands are available. Evidence-support composition has a separate truth table and remains separate from illocution, Validation and Mood.

A task borrowed from a donor distinction must preserve the distinction that motivates it, but it need not pretend to implement the entire donor category. `APL` and `PUR` are local predicate mnemonics with a declared finite-world interpretation. The names do not make their implementation a complete case grammar. Likewise, `EQ` is entity-ID equality, not every use of a copula, and `SIZE` is not the language's Perspective category.

## Dependency sequence

E0 fixes IDs, worlds, canonicalization, oracle disagreement policy and negative fixtures. E1 exposes the two first primitive families. E2 introduces traversal contrasts that preserve the AST. E3 adds evidence-support operators. E4 requires explicit frame/scope contracts before admitting case-scope, ordered affixes or evidential metadata. E5 introduces richer event, discourse and referential worlds. E6 expands the lexicon and implements the morpho-phonological codec. E7 may test a script or multimodal surface. This is a selected engineering path, not a claim that pronunciation is unimportant to human Ithkuil speakers.

The reference implementation's teacher DAG is intentionally smaller than this source dependency graph. Stage 0 is identity, stages 1 and 2 are configuration and purpose/use, stage 3 is their composition, and stage 4 is evidence composition. Future grammar edges are not quietly treated as implemented teacher stages.

## Coverage records

### G00: Chapter 3; slot overview

Source: S01. Donor boundary: Root and grammatical morphology contribute distinct semantic material.

Disposition: Separate root identity, feature tuple, relation role and scope in typed AST. Dependencies: F00. Stage: E0. State: SPECIFIED. Acceptance: Reject root/features flattened into one unconstrained text field.

### G01: 3.1 Configuration

Source: S01. Donor boundary: Configuration distinguishes arrangements involving number, similarity and connection.

Disposition: First configuration-inspired family uses cardinality, color uniformity and induced-graph connectivity. These are task choices, not exhaustive donor meanings. Dependencies: F00,F01. Stage: E1. State: IMPLEMENTED_SUBSET. Acceptance: All eight three-node graphs and all nonempty subsets agree between independent evaluators.

### G02: 3.2 Affiliation

Source: S01. Donor boundary: Affiliation concerns functional relationships among members.

Disposition: Keep affiliation separate from cardinality and graph edges. Future world needs jointly specified purposes and role relations. Dependencies: G01,G11. Stage: E4. State: DEFERRED. Acceptance: Same graph with different functional coordination must remain representationally distinguishable.

### G03: 3.3 Perspective

Source: S01. Donor boundary: Monadic, agglomerative, nomic and abstract perspective are not simply singular/plural alternatives.

Disposition: Introduce group-view scope later; do not label the current integer count as Perspective. Dependencies: G01,F02. Stage: E4. State: DEFERRED. Acceptance: A multi-member object can retain monadic treatment; scope tests must cover this.

### G04: 3.4 Extension

Source: S01. Donor boundary: Extension differentiates the portion or phase of a referent under consideration.

Disposition: Require temporal/part structure before mapping extensions into targets. Dependencies: F02,G15. Stage: E5. State: DEFERRED. Acceptance: Snapshot identity is insufficient to prove extension equivalence.

### G05: 3.5 Essence

Source: S01. Donor boundary: Essence distinguishes normal from representative reference.

Disposition: Add explicit referential interpretation, not an ungrounded real/imaginary binary. Dependencies: G03,G22. Stage: E5. State: DEFERRED. Acceptance: Representative relation must bind to a referent with provenance.

### G06: Function, Specification, Context; slots IV/VI

Source: S01. Donor boundary: These categories and the CA complex occupy distinct formative functions.

Disposition: Maintain independent schema namespaces; no ad hoc CA bundle used as an answer token. Dependencies: G00. Stage: E4. State: SPECIFIED. Acceptance: Typed-field confusion and missing-default tests.

### G07: Chapter 4; case categories

Source: S02. Donor boundary: Cases encode relations and roles beyond a single generic edge.

Disposition: Extend Relation with role, source, target and frame; reject implicit nearest-noun binding. Dependencies: F00,F02. Stage: E4. State: SPECIFIED. Acceptance: Round-trip role swaps and arity changes must preserve or reject meaning explicitly.

### G08: 4.4.1 Applicative

Source: S02. Donor boundary: Applicative concerns contextual use rather than inherent intended function.

Disposition: APL(entity,value) compares the finite-world actual-use field. Dependencies: F00. Stage: E1. State: IMPLEMENTED_SUBSET. Acceptance: Change actual use only; PUR result must remain unchanged.

### G09: 4.4.2 Purposive

Source: S02. Donor boundary: Purposive concerns dedicated or intended purpose.

Disposition: PUR(entity,value) compares the separately declared intended-purpose field. Dependencies: F00. Stage: E1. State: IMPLEMENTED_SUBSET. Acceptance: Change intended purpose only; APL result must remain unchanged.

### G10: Case frames and relational cases

Source: S02. Donor boundary: A case label has a relational interpretation within its construction.

Disposition: Compile role-bearing frames before broad lexical expansion; do not treat all cases as interchangeable unary attributes. Dependencies: G07. Stage: E4. State: SPECIFIED. Acceptance: Frame validation must reject dangling role bindings and wrong argument types.

### G11: Chapter 5; Valence

Source: S03. Donor boundary: Valence modifies participation structure.

Disposition: Future event AST needs participants and participation relations before valence teaching. Dependencies: G07,F02. Stage: E5. State: DEFERRED. Acceptance: Swap actor/participant without changing event identity and test expected contrast.

### G12: Chapter 5; Phase/Aspect

Source: S03. Donor boundary: Temporal categories convey event structure.

Disposition: Use finite event traces with an independently executable temporal oracle. Dependencies: F02,G11. Stage: E5. State: DEFERRED. Acceptance: Pointwise labels must not substitute for interval truth.

### G13: Chapter 5; Mood

Source: S03. Donor boundary: Mood distinguishes factuality and presuppositional stance.

Disposition: Separate speaker commitment/presupposition metadata from world truth and probability. Dependencies: G10,G18. Stage: E5. State: SPECIFIED. Acceptance: Changing mood alone must not alter the same world proposition oracle.

### G14: Chapter 5; Case-scope

Source: S03. Donor boundary: Case-scope affects the interpretation of relationships in connected material.

Disposition: Scope becomes explicit AST edges, not undocumented sequence adjacency. Dependencies: G10,F02. Stage: E4. State: SPECIFIED. Acceptance: Nested-frame minimal pairs and dangling-scope rejection.

### G15: Chapter 5; Effect/Level

Source: S03. Donor boundary: Effect and Level are distinct grammatical categories.

Disposition: Do not merge scalar level, participant impact and event phase into a numeric intensity coordinate. Dependencies: G11,G12. Stage: E5. State: DEFERRED. Acceptance: Each coordinate must have a distinct controlled world intervention.

### G16: Chapter 6; Illocution

Source: S42. Donor boundary: Illocution distinguishes communicative acts such as assertion and direction.

Disposition: Attach speech-act type to utterance, not the proposition truth value. Dependencies: G13. Stage: E5. State: SPECIFIED. Acceptance: A directive is not validated as a factual assertion.

### G17: Chapter 6; Validation

Source: S42. Donor boundary: Validation marks evidential basis for assertive material.

Disposition: Represent basis/provenance separately from two-bit evidence support. Observation does not guarantee truth. Dependencies: G16,F03. Stage: E4. State: SPECIFIED. Acceptance: OBS report can be mistaken; no automatic truth promotion.

### G18: Chapter 6 editorial consistency

Source: S42. Donor boundary: The page has an eight-subtype phrase beside nine listed Validation categories and a stray Expectation reference.

Disposition: Use the explicitly enumerated categories for donor notes; do not invent an Expectation field or infer ML structure from editorial inconsistencies. Dependencies: G17. Stage: E0. State: SOURCE_QUESTION. Acceptance: Record source question; future parser fixture waits for reconciliation.

### G19: Chapter 7; slots V and VII

Source: S04. Donor boundary: Affix scope differs by placement relative to the formative complex.

Disposition: Retain ordered scope annotations; syntactically valid reordering is not automatically semantic equivalence. Dependencies: G00,G14. Stage: E4. State: SPECIFIED. Acceptance: Move an affix across scope boundary and require declared interpretation change.

### G20: Chapter 8; adjunct inventory

Source: S05. Donor boundary: Adjunct families include affixual, modular, register, suppletive, mood/case-scope, bias and parsing roles.

Disposition: Create separate node types only as supported by a world/task; no catch-all adjunct string in confirmatory input. Dependencies: G14,G19. Stage: E5. State: SPECIFIED. Acceptance: Unknown adjunct type must fail rather than silently drop.

### G21: Chapter 11; syntax

Source: S06. Donor boundary: Discourse order and grammatical relations are not identical; order is not universally free.

Disposition: Test traversal only where the same explicit AST is preserved. Topic/focus differences must not be mislabeled as order-only controls. Dependencies: G10,G14. Stage: E2. State: IMPLEMENTED_SUBSET. Acceptance: Entity serialization reversal round-trips; ordered query operands remain explicit.

### G22: Chapter 9; referentials

Source: S47. Donor boundary: Referential forms carry reference and associated grammatical distinctions.

Disposition: Use stable entity IDs now; add discourse binding and referential features as a separate extension. Dependencies: F00,G10. Stage: E5. State: DEFERRED. Acceptance: Alpha-renaming of IDs preserves meaning; rebinding does not.

### G23: Chapter 10; concatenation

Source: S48. Donor boundary: Type 1 circumstantial and Type 2 lexicalizing concatenations differ.

Disposition: Do not map both to Boolean AND. Add typed composition operations and full scope contracts before teaching them. Dependencies: G14,G19. Stage: E5. State: DEFERRED. Acceptance: Circumstantial association and lexical gestalt require distinct golden ASTs.

### G24: Chapter 10; carrier

Source: S48. Donor boundary: Carrier constructions support names or other quoted foreign material.

Disposition: Treat carrier payload as opaque quoted data with boundaries and escaping, never executable instructions. Dependencies: G22. Stage: E5. State: SPECIFIED. Acceptance: Quoted operator strings cannot escape to AST evaluation.

### G25: Lexicon v1.0; PDF page index 4, printed page 5

Source: S43. Donor boundary: The copular root is restricted; its notes exclude several uses of English be.

Disposition: Keep identity/equivalence, membership, location, existence and composition separately typed. The reference EQ tests only entity-ID equality. Dependencies: F00,G07. Stage: E0. State: IMPLEMENTED_SUBSET. Acceptance: EQ is not a shortcut for membership or descriptive predication.

### G26: Lexicon cover and root entries

Source: S43. Donor boundary: The official lexicon supplies root/stem meaning and usage constraints.

Disposition: Expand roots only after their required semantic fields and oracle predicates exist; log unresolved sense choices. Dependencies: G00,G10. Stage: E6. State: DEFERRED. Acceptance: Every admitted root maps to typed senses, source location and negative examples.

### G27: Chapter 2; morpho-phonology

Source: S44. Donor boundary: Surface construction has morpho-phonological constraints.

Disposition: Place a reversible linguistic codec after semantic-core verification; semantic ABI does not claim valid Ithkuil spelling. Dependencies: G00,G19,G20. Stage: E6. State: DEFERRED. Acceptance: AST-to-surface-to-AST equivalence plus rejection of illegal allomorphs.

### G28: Chapter 1; phonology

Source: S45. Donor boundary: Phonological inventory and stress participate in surface realization.

Disposition: Keep pronunciation and orthographic surface out of the first causal test. Dependencies: G27. Stage: E6. State: DEFERRED. Acceptance: Stress-sensitive contrasts need dedicated codec fixtures.

### G29: Chapter 13; numbers

Source: S46. Donor boundary: The donor has dedicated number constructions.

Disposition: Current integers 0..6 are ABI numerals, not a claim to implement donor number morphology. Dependencies: F01,G27. Stage: E6. State: DEFERRED. Acceptance: Numeric value round-trip must be separate from donor-form acceptance.

### G30: Chapter 12; writing system

Source: S49. Donor boundary: The writing system is a distinct realization surface.

Disposition: Defer script tokens; a writing-system decoder cannot be assumed to improve learner reasoning. Dependencies: G27,G28. Stage: E7. State: DEFERRED. Acceptance: Raster/vector-to-AST testing is a separate multimodal experiment.

### G31: Appendices

Source: S50. Donor boundary: Appendices provide supplementary tables and material for the language.

Disposition: Consult for each extension; do not import every table as mandatory first-model capacity. Dependencies: G26,G27. Stage: E6. State: SPECIFIED. Acceptance: Every new fixture cites the particular appendix section consulted.

### F00: Finite-world ABI v0.1.0

Source: AUTHOR. Donor boundary: Not a donor-language fact: identity is primitive in the reference world.

Disposition: Entity IDs, typed fields and exact equality. Dependencies: none. Stage: E0. State: IMPLEMENTED. Acceptance: Identity and alpha-renaming; reject Boolean IDs.

### F01: Finite-world ABI v0.1.0

Source: AUTHOR. Donor boundary: Not a donor-language fact: finite-set operations ground toy tasks.

Disposition: Nonempty sets, cardinality, graph reachability and property comparisons. Dependencies: F00. Stage: E0. State: IMPLEMENTED. Acceptance: Independent BFS versus transitive-closure agreement.

### F02: Finite-world ABI v0.1.0

Source: AUTHOR. Donor boundary: Not a donor-language fact: operators compose with explicit typed arguments.

Disposition: Bounded-depth prefix AST; parenthesized reversible codecs. Dependencies: F00,F01. Stage: E0. State: IMPLEMENTED. Acceptance: Arity, depth, type, scope and truncation rejection.

### F03: Finite-world ABI v0.1.0

Source: AUTHOR. Donor boundary: Not a donor-language fact: truth/falsity support uses two bits.

Disposition: UNKNOWN and CONFLICT are distinct; AND/OR/NOT defined by the evidence algebra. Dependencies: F02. Stage: E3. State: IMPLEMENTED. Acceptance: Exhaust all 16 binary evidence pairs and double negation.

## Defaults, omission and future surface fidelity

The reference codecs serialize every entity field and each report bit; omission is invalid. This prevents an undeclared zero value from becoming an accidental semantic default. Future New-Ithkuil-compatible codecs must record the donor default, explicit form, omitted form and context in which the omission is legal. A reversible semantic codec may normalize equivalent explicit/omitted forms only after an equivalence fixture demonstrates that normalization. It must not delete distinctions merely to shorten sequences.

The official lexicon was inspected through browser parsing and selected rendered pages. Its cover and the restricted copular entry were visually checked. A later attempted screenshot of the container-root page failed; the package does not claim visual validation of that table. The complete lexicon is not redistributed here, and source access does not confer a new license.

## Source anomalies and pressure evidence

Chapter 6 contains editorial inconsistencies noted in G18. They are not grounds to discard its clearly enumerated categories or to invent missing fields. Keep them as source questions. A future full parser must carry source-version identity, examples, ambiguity dispositions and acceptance tests. The current formal ABI neither depends on resolving that wording nor silently defines a new donor-language fact.
