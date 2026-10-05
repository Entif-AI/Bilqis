# Semantic and token ABI contracts

## Identity and canonical bytes

The semantic ABI is `bilqis-finite-world-0.1.0`, an experimental package-local identifier. It is not a Rosetta Core type or a New Ithkuil version. A semantic example has exactly `abi`, `world`, and `query`. Gold labels and provenance live outside that object. Canonical JSON uses sorted keys, ASCII escaping, no insignificant whitespace and no NaN/Infinity. SHA-256 of those bytes identifies the semantic object. This canonicalizer is explicitly limited to the integer/string/list/object domain used here; it is not a universal semantic equivalence algorithm.

The world contains `entities`, `edges`, and `reports`. There are two through six entities, but current generators use exactly six. Entity IDs are consecutive exact integers starting at zero; booleans are rejected even though Python treats bool as an int subtype. Each entity has `color`, `intended` and `actual`, each in 0..2. These are synthetic category IDs, not physical quantities, calibrated utility, donor roots or truth values. All fields are mandatory.

Edges are unique sorted undirected pairs with the smaller endpoint first. Self-edges and dangling references are invalid. `reports` contains exactly three ordered pairs of evidence bits. The pair `(1,0)` denotes positive support without negative support, `(0,1)` negative support without positive support, `(0,0)` neither, and `(1,1)` both. Their answer names are TRUE, FALSE, UNKNOWN and CONFLICT. These are formal evidential states in this world, not probability estimates or mental states.

## Query grammar and type rules

EQ(a,b) tests entity-ID equality. SIZE(group,value) tests cardinality. SAME(group) tests color uniformity. CONNECTED(group) tests connectivity of the induced subgraph, not reachability through excluded entities. A singleton group is connected and uniform. APL(a,value) tests current use; PUR(a,value) tests intended purpose. EVID(value) returns one report's evidence pair. NOT takes one child; AND and OR take exactly two ordered children. Every group is nonempty, sorted and duplicate-free. Maximum AST depth is four under the implementation's zero-based validator.

For evidence pairs `(t,f)` and `(u,v)`, NOT swaps the bits. AND returns `(t & u, f | v)`; OR returns `(t | u, f & v)`. Classical world predicates return only TRUE or FALSE; evidence queries can return all four states. Truth-functional composition does not encode discourse Mood, Illocution or the donor's Validation category. Those would be separate schema extensions.

The primary oracle is recursive and uses breadth-first connectivity. The second implementation is iterative postorder and uses transitive closure. Accepted generated examples require agreement. Their implementation diversity catches some bugs; it does not make their authors or specifications epistemically independent. Formal validation must run before either evaluator receives outside data. Unknown operators, missing fields, extra answer fields, bad arity, excess depth and invalid references are fatal example errors, not silently coerced cases.

## Codec and token contracts

The token ABI is `bilqis-token-0.1.0`. `token-abi.json` lists all 512 rows and the exact permutation control. IDs 0..6 are PAD, BOS, TRUE, FALSE, UNKNOWN, CONFLICT and EOS respectively. Remaining rows encode operators, fields, delimiters, finite integer symbols, controlled-language words and reserved slots. Every model allocates all 512 rows at genesis. A stage may expose fewer symbols, but parameter count does not grow with stage vocabulary. No pretrained tokenizer or embeddings are used.

Bilqis serialization is an explicit world section plus a parenthesized query. CNL serialization uses a closed controlled-English rendering of exactly the same object. It is not unconstrained English or a pretrained natural-language capability. The decoder accepts only the declared grammar. No codec inserts a gold answer, an acceptance/rejection attempt number, a split ID, or a provenance hash into learner tokens.

The `isomorphic` condition applies a fixed bijection to non-special token IDs. All operators, fields and values preserve their roles under decoding. Its scientific purpose is a symmetry null, not a structure-destroying intervention. To obtain pathwise equality, permute embedding rows with the same mapping, preserve the special output rows, and transform any associated optimizer state. The unit test does this and checks two optimizer updates. Independent random initializations give distributional, not pathwise, symmetry.

The `mixed` condition applies the invertible map `(color,intended) -> (color+intended, color+2*intended) mod 3` to each entity's two coordinates. The inverse is `(2*u-v, v-u) mod 3`. Each encoded coordinate depends on both original coordinates, unlike an independent relabeling of each factor. Length, token inventory and information are preserved; accessibility of a single original coordinate changes. This intervention still changes useful factor alignment, and it must not be described as a pure surface rename. All nine pairs round-trip.

Reverse-entity traversal changes serialization order only; entity IDs preserve bindings. Query operands retain their explicit scope. Structural equality after decode is the acceptance condition. Token count is recorded per actual sequence; PAD does not count as semantic exposure but padded execution cost still belongs in learner runtime/FLOPs accounting.

## ABI changes

Adding an operator, changing a default, reordering token IDs, widening a domain, changing canonicalization or changing evidence semantics requires a new ABI version and new dataset/code hashes. Extending only comments does not alter semantics but still changes the code artifact hash. An operator cannot continue a confirmatory lineage under a changed ABI while retaining its original identity. Export the old checkpoint, open a child experimental branch and rerun the applicable red fixtures.
