## Publication posture

public research / proving work

## Workability

EXECUTABLE_LEAF

One bounded outcome: implement and run one frozen, human-authored Kev-4B capability battery over a deliberately small New Ithkuil source packet and return a capability map.

Codex is NOT responsible for inventing the questions, selecting the linguistic curriculum, or deciding what the test should mean. The question set below is the v0.1 fixture contract. Codex should focus on fixture encoding, deterministic mutation/ordering where specified, execution, receipts, and reporting.

## Why this replaces the old qualification question

The existing #65 decision-v1 fixture remains historical evidence, but it is a mixed-capability diagnostic. It asks Kev to execute a project-specific evidence algebra, reproduce a deterministic curriculum-selection policy, and classify explicit relation predicates. Those are legitimate bounded-choice tasks, but they are not the task for which we most urgently want Kev.

This issue asks the narrower and more useful question:

> Can Kev recognize, distinguish, compose, diagnose, and reconstruct semantically meaningful New Ithkuil morphology from a small supplied grammar packet?

Preserve the old receipt byte-for-byte. Do not reinterpret history. This is a new evaluation epoch with a different target capability.

## Governing experiment principle

Hand-author as little trustworthy linguistic gold as practical, then interrogate the hell out of it.

Human attention is expensive. Kev decisions are cheap.

Therefore:
- freeze a small, high-confidence source packet;
- freeze a small set of trusted gold anchors;
- derive many bounded questions, near-misses, reversals, and reconstructions from those anchors;
- retain Kev's full probability vectors;
- report capability by family and difficulty rather than hiding everything behind one aggregate pass/fail score.

The first run must NOT use model-authored test questions. We are testing Kev, not Kev plus Codex's ability to author an Ithkuil exam.

## Frozen source packet v0.1

Use only official NEW Ithkuil material.

### Chapter 2: Morpho-Phonology

Official source:
https://www.ithkuil.net/newithkuil_02_morpho-phonology.htm

For context, the full chapter may be supplied because it is small and explains how words are assembled.

Scored material should concentrate on:
- 2.0: formative / adjunct / referential distinction and agglutinative/synthetic word construction;
- 2.3: formative slot structure and semantic scope of the slots;
- 2.4.1: root as semantic basis;
- 2.4.2: formative as the common noun/verb substrate;
- 2.4.3: stems;
- 2.4.4: Specification.

Important fixture facts:
- Slot II carries Stem + Version;
- Slot III is the main semantic root;
- Slot IV carries Function + Specification + Context;
- Slot VI carries the Configuration/Affiliation/Extension/Perspective/Essence complex;
- Slot IX carries Case or other categories depending on stress;
- root -DN- means NAME / DESIGNATION / LABEL;
- its Stem 1 is name, Stem 2 designation/reference, Stem 3 label, Stem Zero the deliberately underspecified root-level concept;
- Specification values used here are BSC, CTE, CSV, OBJ.

Do not score phonological trivia merely because Chapter 2 contains it.

### Chapter 3: Basic Morphology, selected slice only

Official source:
https://www.ithkuil.net/newithkuil_03_morphology.htm

For v0.1, load and score only:
- 3.1 Configuration;
- 3.2 Affiliation;
- the minimal 3.6 CA-affix ordering context needed to understand how the selected factors compose.

Do NOT throw all of Chapter 3 at the model in this first run.

Configuration facts used by the fixture:
- Plexity: U / D / M;
- Separability: S / C / F;
- Similarity: S / D / F;
- selected CA Configuration forms:
  - DPX = s
  - DSS = c
  - DSC = ks
  - DDS = ţs
  - MSS = t
  - MSC = k
  - MDS = ţ
  - MFS = z
  - DFC = kš

Affiliation facts used by the fixture:
- CSL = null/default: naturally occurring, neutral, or shared function where subjective design is not the distinction;
- ASO = l: members share the same subjective function/state/purpose/benefit;
- COA = r: members have distinct but complementary functions serving a unified whole;
- VAR = ř: members differ in function/state/purpose/benefit in unrelated or conflicting ways.

Source-backed examples used as anchors:
- rrasa = a pair of cats;
- rraca = a pair of similar cats;
- rrata = a group of similar cats;
- anzwuk = similar spherical objects connected/touching;
- čveţa = a bunch of tools;
- čvelţa = a well-designed set of tools;
- čverţa = a toolset;
- čveřţa = a mish-mash of tools.

### Chapter 4: Case Morphology, selected slice only

Official source:
https://www.ithkuil.net/newithkuil_04_case.htm

Load and score:
- 4.1 through 4.1.2: semantic role versus surface position;
- 4.2 through 4.2.10: the nine Transrelative cases and the worked examples.

Do NOT load the rest of Chapter 4 into the first run unless the harness needs a source line already used by one of the frozen worked examples below.

Semantic-role facts used:
- AGENT: deliberate animate initiator of tangible change;
- FORCE: unwilled/inanimate direct cause;
- INSTRUMENT: physical means/tool;
- PATIENT: undergoer of tangible change;
- ENABLER: initiates a causal chain or induces another agent;
- EXPERIENCER: undergoes an unwilled affective/sensory state;
- STIMULUS: trigger of such a state;
- RECIPIENT: intended receiver of transfer/transmission/communication;
- CONTENT: non-participatory referent.

Transrelative case mapping used:
- THM / a = CONTENT;
- INS / ä = INSTRUMENT;
- ABS / e = PATIENT;
- AFF / i = EXPERIENCER;
- STM / ëi = STIMULUS;
- EFF / ö = ENABLER;
- ERG / o = AGENT or FORCE;
- DAT / ü = RECIPIENT;
- IND / u = simultaneous AGENT + PATIENT.

## Gold-anchor inventory

Codex should encode these anchors, not invent replacements.

G-01: Chapter-2 root/stem anchor
- root: -DN-
- root meaning: NAME / DESIGNATION / LABEL
- Stem 1: name
- Stem 2: designation/reference
- Stem 3: label
- Stem Zero: deliberately undifferentiated root-level concept

G-02: Chapter-2 Specification anchor
- BSC = holistic/basic instantiation
- CTE = semantic content/essence/purposeful function
- CSV = realized/formal/constitutive manifestation
- OBJ = salient instrument/object/result/patient as licensed by the stem

G-03: Chapter-3 Configuration anchor
- use the selected Configuration table above.

G-04: Chapter-3 Affiliation anchor
- use CSL / ASO / COA / VAR meanings above.

G-05: Chapter-4 semantic-role anchor
- use the John / key / door distinction:
  John = AGENT, key = INSTRUMENT, door = PATIENT.
- important invariant: semantic role can remain constant even when English syntactic subject/object position changes.

G-06: Chapter-4 transfer/content anchor
- in the source discussion corresponding to “Mary tells the children a story”:
  children = RECIPIENT;
  story = CONTENT.

G-07: Chapter-4 anger minimal-pair anchor
- Wekská welo kšili. = the child directly angers the clown: child ERG, clown AFF.
- Wekská welö kšili. = what the child has started/caused makes the clown angry: child EFF, clown AFF.

G-08: Chapter-4 hit/rock sentence family
Use the official worked forms as the sentence-level gold family:
- Weţdosmá welo šnaliothe aggwilä. = child intentionally hits their leg with a rock; child ERG, leg ABS, rock INS.
- Weţdosmá welu šnali’othia aggwilä. = child hits themself on the leg with a rock; child IND, leg LOC, rock INS.
- Weţdosmá wele šnali’othia aggwilä. = child is/gets hit on the leg with a rock; child ABS, leg LOC, rock INS.
- Weţdosmá welo aggwilä. = child hits something with a rock; child ERG, rock INS.
- Weţdosmá welu aggwilä. = child hits themself with a rock; child IND, rock INS.
- Weţdosmá wele aggwilä. = child is/gets hit with a rock; child ABS, rock INS.

When punctuation/spacing is normalized by fixture encoding, preserve the source form identity in metadata.

## Difficulty contract

SIMPLE:
- one or two semantic distinctions;
- for families 1 and 2, MUST be compositional, not a one-token lookup;
- no complete-sentence translation.

MEDIUM:
- at least three interacting semantic decisions OR a compact source example where one distinction only makes sense in the presence of another;
- should be meaningfully harder than lookup.

HARD:
- sentence-level or multi-step semantic reconstruction;
- families 1 and 2 MUST use complete source-backed sentences;
- no invented Ithkuil sentence may be promoted to gold merely to make the test harder.

## Frozen 36-cell battery v0.1

Candidate IDs must be stable. Candidate order may be permuted by the harness, but the option set and gold identity are frozen.

### FAMILY 1 — English -> New Ithkuil semantic/morphological recognition

#### F01-SIMPLE

Prompt:
A pair consists of two physically separate, similar members. Their individual functions are distinct but complementary and together serve one unified role. Which segmented New Ithkuil Slot-VI semantic bundle best matches?

Options:
A. COA(-r-) + DSS(-c-)
B. ASO(-l-) + DSS(-c-)
C. COA(-r-) + DDS(-ţs-)
D. VAR(-ř-) + DSS(-c-)

Gold: A

Why:
DSS supplies duplex + similar + separate. COA supplies complementary functions.

This is intentionally a novel combination of two source-defined morphemes/features rather than a copied worked example.

#### F01-MEDIUM

Prompt:
Which segmented morphology best fits an entity whose physical realization is foregrounded, which consists of three-or-more physically dissimilar separate members, deliberately organized so the members share the same subjective function?

Options:
A. CSV(-e-) + ASO(-l-) + MDS(-ţ-)
B. CTE(-ä-) + ASO(-l-) + MDS(-ţ-)
C. CSV(-e-) + CSL(null) + MDS(-ţ-)
D. CSV(-e-) + VAR(-ř-) + MDS(-ţ-)

Gold: A

Scored dimensions:
Specification + Affiliation + Configuration.

Do not require phonological fusion into a novel surface word in v0.1. This cell tests semantic composition, not allomorphy.

#### F01-HARD

Prompt:
Which complete New Ithkuil sentence matches: “The child intentionally hit their leg with a rock,” where the child is the direct agent, the leg is the affected patient, and the rock is the instrument?

Options:
A. Weţdosmá welo šnaliothe aggwilä.
B. Weţdosmá welu šnali’othia aggwilä.
C. Weţdosmá wele šnali’othia aggwilä.
D. Weţdosmá welu aggwilä.

Gold: A

### FAMILY 2 — New Ithkuil -> English semantic recognition

#### F02-SIMPLE

Prompt:
What is the best semantic reading of the segmented Slot-VI bundle COA(-r-) + DSC(-ks-)?

Options:
A. A pair of similar connected members whose distinct functions complement one another as a unified whole.
B. A pair of similar connected members that all share the same function.
C. A pair of dissimilar separate members with complementary functions.
D. A pair whose members have unrelated or conflicting functions.

Gold: A

#### F02-MEDIUM

Prompt:
What semantic bundle is best represented by CTE(-ä-) + VAR(-ř-) + MFS(-z-)?

Options:
A. Focus on content/purpose; three-or-more separate members whose similarity is fuzzy/indeterminate and whose purposes/functions differ in unrelated ways.
B. Focus on physical realization; three-or-more similar connected members sharing one designed function.
C. Focus on content/purpose; exactly two dissimilar separate members with complementary functions.
D. Focus on a salient instrument/object; three-or-more fused members with one shared function.

Gold: A

#### F02-HARD

Prompt:
Choose the best English interpretation of:
Weţdosmá welu šnali’othia aggwilä.

Options:
A. The child intentionally hit their leg with a rock.
B. The child hit themself on the leg with a rock.
C. The child was hit on the leg with a rock.
D. The child hit something with a rock.

Gold: B

### FAMILY 3 — Root / stem recovery

#### F03-SIMPLE

Prompt:
In the Chapter-2 example adna, which semantic root underlies the formative?

Options:
A. -DN- : NAME / DESIGNATION / LABEL
B. -KSK- : anger
C. -ŽX- : burn
D. -GGW- : rock/stone

Gold: A

#### F03-MEDIUM

Prompt:
For the form edni, which root/stem identity supplies the lexical-semantic core before other morphology is interpreted?

Options:
A. -DN-, Stem 1: name
B. -DN-, Stem 2: designation/reference
C. -DN-, Stem 3: label
D. -DN-, Stem Zero: deliberately undifferentiated calling/reference concept

Gold: B

#### F03-HARD

Prompt:
In Weţdosmá welo šnaliothe aggwilä., which root/stem is the source-defined predicate for HIT/STRIKE?

Options:
A. -ţd-, Stem 2, the forceful-physical-contact base used for hit/strike
B. -šn-, Stem 1, leg
C. -ggw-, Stem 1 OBJ, rock/stone
D. -žx-, Stem 1, burn

Gold: A

### FAMILY 4 — Semantic-role classification

#### F04-SIMPLE

Prompt:
In “John opened the door with the key,” what is the semantic role of the key?

Options:
A. AGENT
B. FORCE
C. INSTRUMENT
D. PATIENT

Gold: C

#### F04-MEDIUM

Prompt:
In the Chapter-4 semantic analysis corresponding to “Mary tells the children a story,” which role pair is correct?

Options:
A. children = RECIPIENT; story = CONTENT
B. children = PATIENT; story = INSTRUMENT
C. children = EXPERIENCER; story = STIMULUS
D. children = CONTENT; story = RECIPIENT

Gold: A

#### F04-HARD

Prompt:
For “The child intentionally hit their leg with a rock,” choose the correct role assignment.

Options:
A. child = AGENT; leg = PATIENT; rock = INSTRUMENT
B. child = PATIENT; leg = CONTENT; rock = FORCE
C. child = AGENT+PATIENT; leg = LOCATION; rock = INSTRUMENT
D. child = ENABLER; leg = PATIENT; rock = STIMULUS

Gold: A

### FAMILY 5 — Grammatical-feature classification

#### F05-SIMPLE

Prompt:
A group contains three-or-more members; the members are physically similar and physically connected/touching. Which Configuration applies?

Options:
A. MSS
B. MSC
C. MDS
D. DSC

Gold: B

#### F05-MEDIUM

Prompt:
A toolset contains multiple physically dissimilar, separate tools. Each tool has a distinct function, but those functions complement one another in service of the set as a whole. Which selected Chapter-3 feature pair matches?

Options:
A. MDS + COA
B. MDS + ASO
C. MSS + COA
D. MFS + VAR

Gold: A

#### F05-HARD

Prompt:
For the sentence Weţdosmá welo šnaliothe aggwilä., choose the correct grammatical case tuple in participant order child / leg / rock.

Options:
A. ERG / ABS / INS
B. IND / LOC / INS
C. ABS / THM / INS
D. EFF / ABS / STM

Gold: A

### FAMILY 6 — Morpheme / form selection

#### F06-SIMPLE

Prompt:
Which Slot-IX Transrelative case vowel marks ABS / PATIENT?

Options:
A. -a-
B. -ä-
C. -e-
D. -o-

Gold: C

#### F06-MEDIUM

Prompt:
Which Configuration consonantal form marks DFC = duplex / fuzzy / connected?

Options:
A. -ks-
B. -kš-
C. -č-
D. -fs-

Gold: B

#### F06-HARD

Prompt:
Choose the correct Slot-IX case-vowel sequence for AGENT / PATIENT / INSTRUMENT.

Options:
A. -o- / -e- / -ä-
B. -ö- / -e- / -a-
C. -u- / -a- / -ä-
D. -o- / -i- / -ëi-

Gold: A

### FAMILY 7 — Near-miss diagnosis

#### F07-SIMPLE

Prompt:
Target meaning: a group of similar spherical objects touching/connected to one another.
A candidate uses Configuration MSS(-t-) instead of MSC(-k-).
What is the error?

Options:
A. Plexity is wrong: duplex instead of multiplex.
B. Separability is wrong: separate instead of connected.
C. Similarity is wrong: dissimilar instead of similar.
D. Affiliation is wrong: variative instead of coalescent.

Gold: B

#### F07-MEDIUM

Prompt:
Target meaning: TOOLSET, i.e. physically dissimilar separate tools whose distinct functions complement one another.
A candidate uses ASO(-l-) + MDS(-ţ-) instead of COA(-r-) + MDS(-ţ-).
What changed?

Options:
A. The candidate says the members share the same subjective function rather than having distinct complementary functions.
B. The candidate makes the tools physically similar.
C. The candidate makes the tools connected.
D. The candidate changes content/purpose focus into physical-form focus.

Gold: A

#### F07-HARD

Prompt:
Target: Wekská welo kšili. in the source-defined sense “the child angers the clown.”
Candidate: Wekská welö kšili.
What is the minimal semantic error?

Options:
A. ERG changed to EFF, so the child is no longer the direct agent/force but the initiator/enabler of a causal chain.
B. AFF changed to ABS, so the clown becomes a tangible patient.
C. ERG changed to IND, so the child becomes both agent and patient.
D. The lexical root changed from anger to hit.

Gold: A

### FAMILY 8 — Minimal-pair discrimination

#### F08-SIMPLE

Prompt:
What semantic distinction separates rrasa from rraca?

Options:
A. rrasa is a generic pair of cats (DPX); rraca overtly specifies a pair of similar cats (DSS).
B. rrasa is a group of similar cats; rraca is a pair of dissimilar cats.
C. rrasa is a toolset; rraca is a designed set of tools.
D. The forms are semantically identical.

Gold: A

#### F08-MEDIUM

Prompt:
What is the important semantic distinction between čveţa and čverţa?

Options:
A. čveţa is a neutral/natural bunch of tools; čverţa is a toolset whose distinct functions are complementary.
B. čveţa is a toolset; čverţa is a mish-mash.
C. čveţa is a pair of tools; čverţa is a group of similar tools.
D. Only phonology differs; the selected morphology is equivalent.

Gold: A

#### F08-HARD

Prompt:
Compare these source-backed forms:
1. Weţdosmá welo aggwilä.
2. Weţdosmá welu aggwilä.

What changes?

Options:
A. The child changes from ERG direct agent to IND simultaneous agent+patient: “hits something” -> “hits themself,” while the rock remains instrumental.
B. The child changes from ABS patient to ERG agent.
C. The rock changes from INS instrument to THM content.
D. Only word order changes.

Gold: A

### FAMILY 9 — Semantic-equivalence judgment

#### F09-SIMPLE

Prompt:
Compare the role of KEY in:
1. John opened the door with the key.
2. The key opened the door.

At the semantic-role level used by Chapter 4, is KEY equivalent?

Options:
A. Yes: INSTRUMENT in both, despite different English syntactic positions.
B. No: AGENT in sentence 2.
C. No: FORCE in sentence 2.
D. Insufficient: New Ithkuil does not distinguish instruments.

Gold: A

#### F09-MEDIUM

Prompt:
Are “a group of soldiers” and “a troop/platoon” equivalent under the selected Configuration + Affiliation projection?

Options:
A. No. They may share the relevant group Configuration, but the latter adds ASO purposeful/shared-function affiliation.
B. Yes. Affiliation is purely stylistic.
C. Yes. Both are necessarily COA.
D. Insufficient because Chapter 3 never discusses soldier groups.

Gold: A

#### F09-HARD

Prompt:
Are these source-backed expressions semantically equivalent?
1. Weţdosmá wele šnalioth aggwilä.
2. Weţdosmá wele šnali’othia aggwilä.

Options:
A. No. In (1) the leg is THM/content-like referent of the hitting; in (2) the leg is LOC, the site of the hit.
B. Yes. Both merely mean the child gets hit with a rock.
C. No. In (1) the rock is an agent; in (2) it is an instrument.
D. Insufficient because the child case changes.

Gold: A

### FAMILY 10 — Sequential bounded reconstruction

This family is multi-step. Preserve each atomic decision, then let deterministic code assemble or select the final source form.

#### F10-SIMPLE

Target:
a complementary pair of similar, physically separate members.

Step 1 question:
Which Configuration?
Options: DPX / DSS / DSC / DDS
Gold: DSS

Step 2 question:
Which Affiliation?
Options: CSL / ASO / COA / VAR
Gold: COA

Deterministic result:
COA(-r-) + DSS(-c-)

Pass metrics:
- step accuracy;
- joint path accuracy;
- final deterministic bundle correctness.

#### F10-MEDIUM

Target:
TOOLSET.

Step 1:
Which Configuration?
Options: MSS / MSC / MDS / MFS
Gold: MDS

Step 2:
Which Affiliation?
Options: CSL / ASO / COA / VAR
Gold: COA

Step 3:
Which source-backed whole form matches the resulting meaning?
Options: čveţa / čvelţa / čverţa / čveřţa
Gold: čverţa

#### F10-HARD

Target:
“The child intentionally hit their leg with a rock.”

Fixed predicate:
Weţdosmá

Step 1:
child case?
Options: ERG / IND / ABS / EFF
Gold: ERG

Step 2:
leg case?
Options: ABS / THM / LOC / DAT
Gold: ABS

Step 3:
rock case?
Options: INS / STM / THM / ERG
Gold: INS

Step 4:
Choose the source-backed complete sentence consistent with the selected path.
Options: use the same four sentences as F01-HARD.
Gold: Weţdosmá welo šnaliothe aggwilä.

Record intermediate wrong-path/right-final cases separately. A correct final answer must not retroactively validate a wrong semantic decision.

### FAMILY 11 — Complete-expression validation

#### F11-SIMPLE

Prompt:
Intended meaning: deliberately organized group of similar, physically separate members that share the same subjective function.
Candidate bundle: ASO(-l-) + MSS(-t-).
Is it compatible?

Options:
A. Yes, for the selected Configuration + Affiliation dimensions.
B. No: MSS means physically connected.
C. No: ASO means complementary but distinct functions.
D. Insufficient because no Perspective is supplied.

Gold: A

The question is explicitly limited to the selected dimensions; do not require unscored morphology.

#### F11-MEDIUM

Prompt:
Intended meaning: TOOLSET, where physically dissimilar separate tools have distinct complementary functions.
Candidate: čvelţa.
What is the disposition?

Options:
A. Mismatch: source uses this as a well-designed set of tools; ASO shared-function/design is not the COA complementary-function relation required for TOOLSET.
B. Valid exact match for TOOLSET.
C. Mismatch only because the tools are physically connected.
D. Insufficient because the root is not a tool root.

Gold: A

#### F11-HARD

Prompt:
Intended meaning: “The child hit themself on the leg with a rock.”
Candidate:
Weţdosmá welo šnaliothe aggwilä.

Options:
A. Mismatch. Candidate encodes child ERG + leg ABS: the child intentionally hits their leg as patient, not child IND + leg LOC self-targeting.
B. Exact match.
C. Mismatch only because the rock is not instrumental.
D. Insufficient because the predicate is unknown.

Gold: A

### FAMILY 12 — Insufficient-evidence / clarification behavior

#### F12-SIMPLE

Prompt:
“Mary ____ the children.”
Without knowing the predicate or event semantics, which semantic role/case should Mary receive?

Options:
A. ERG / AGENT
B. AFF / EXPERIENCER
C. EFF / ENABLER
D. CLARIFY / INSUFFICIENT

Gold: D

Why:
Chapter 4 explicitly demonstrates that English subject position does not determine semantic role.

#### F12-MEDIUM

Prompt:
English gloss: “a group of cats.”
Which exact Configuration should be selected?

Options:
A. MSS
B. MSC
C. MDS
D. CLARIFY / INSUFFICIENT

Gold: D

Why:
“group” supplies multiplicity but does not specify enough about member similarity and separability to choose one exact multiplex Configuration.

#### F12-HARD

Prompt:
“The child caused the clown to become angry.”
The description does NOT state whether the child directly acted on the clown or merely initiated an intermediate causal chain that resulted in the clown's anger.
Which case should be selected for the child?

Options:
A. ERG
B. EFF
C. IND
D. CLARIFY / INSUFFICIENT

Gold: D

Why:
The selected Chapter-4 examples distinguish direct ERG causation from EFF enablement/causal-chain initiation. The English sentence as supplied underdetermines that distinction.

## Fixture encoding requirements

Encode the 36 canonical cells in a machine-readable fixture.

Each cell must include:
- fixture version;
- cell id;
- family 1-12;
- difficulty SIMPLE / MEDIUM / HARD;
- source chapter/section locator(s);
- exact prompt;
- stable options with stable candidate IDs;
- gold candidate ID;
- rationale;
- semantic dimensions under test;
- gold anchor IDs consumed;
- whether the item is source-exact, source-derived composition, or controlled mutation;
- whether the item permits candidate permutation;
- optional sequence step index and parent sequence ID.

No model should author or silently rewrite the v0.1 prompts/options/gold during execution.

## Candidate-order robustness

Run at least:
- canonical order;
- one deterministic permutation of every permutable option set.

Report:
- exact selection stability;
- correctness stability;
- probability-distribution delta when available.

Do not treat an order-sensitive correct answer as fully robust.

## Engine scope

Primary:
- Kev-4B through the #65-qualified MLX/loopback path.

Optional, only if trivial after Kev:
- SemIf baseline;
- generative comparator.

Do not let secondary engines delay the Kev run.

Do not fine-tune Kev before this first battery. First establish the raw capability map.

## Token ABI / semantic ABI boundary

Do NOT route these questions through abi/token-abi.json and do NOT treat its 512 token IDs as New Ithkuil semantic coordinates.

That token ABI belongs to the older finite-world learner/token-renaming experiment. Its reserved rows are empty embedding allocation, not a hidden Ithkuil ontology.

This battery operates over:
- English semantic descriptions;
- official New Ithkuil forms;
- source-defined morphology/case labels;
- explicit battery-local candidate IDs.

Where #7/#8 already have canonical identities, references may be recorded. Where they do not, fixture-local IDs are correct. #77 must not invent permanent Bilqis ABI semantics by accident.

## Evidence output

For every Kev decision preserve:
- exact cell/step id;
- exact context packet identity/hash;
- exact prompt;
- option IDs and descriptions;
- option order;
- gold;
- selected;
- full probability vector;
- margin;
- correct/incorrect;
- route/review disposition;
- model/runtime identity;
- prompt/state hash;
- latency;
- warm/cache state where available.

For sequences preserve:
- every atomic decision;
- final deterministic assembly/selection;
- atomic correctness;
- final correctness;
- joint correctness.

## Reporting

Do not collapse the battery into one red or green stamp.

Report:
1. each of the 36 canonical cells;
2. accuracy by family;
3. accuracy by difficulty;
4. Chapter-2 root/stem/Specification accuracy;
5. Chapter-3 Configuration accuracy;
6. Chapter-3 Affiliation accuracy;
7. Chapter-4 semantic-role accuracy;
8. Chapter-4 case/morpheme accuracy;
9. forward vs reverse recognition;
10. near-miss diagnosis;
11. sequential atomic / final / joint correctness;
12. insufficiency/clarification correctness;
13. candidate-order stability;
14. confusion matrix over the selected semantic distinctions;
15. latency and decision throughput.

A top-line aggregate may be displayed for orientation only.

The final human-readable result must answer:
- what Kev can already do reliably;
- which morphology/semantic-role distinctions it confuses;
- whether failures are concentrated in composition, surface form, role assignment, or uncertainty handling;
- whether the next cheap intervention should be a prompt/interface adjustment, a larger Kev model, a deterministic scaffold, or targeted fine-tuning.

## Explicit non-goals for #77

Do NOT:
- train the Bilqis student;
- write the permanent Bilqis semantic ABI;
- populate the old 512-row token ABI with Ithkuil;
- have Codex generate additional linguistic questions;
- introduce a Qwen-generated adaptive question curriculum into this run;
- fine-tune Kev before the raw v0.1 battery;
- load all of Chapters 3 or 4 merely because they exist.

## Future horizon captured, not implemented here

If this hand-curated battery works, a later work item may build a deterministic curriculum sampler:

official grammar HTML
-> section parser
-> bounded source-fragment pool
-> deterministic weighted sampling based on prior capability/confusion state
-> local question-author model
-> validation/human-ratification gate
-> frozen next evaluation epoch

That future system should be able to:
- continue including high-strength concepts occasionally as context/retention probes;
- overweight weak/confused distinctions;
- deliberately combine strong and weak concepts;
- preserve source provenance;
- produce immutable per-epoch fixtures before evaluating the student.

A later larger local model (for example a 27B-class local model) may be fine-tuned specifically for high-quality Ithkuil exercise generation, but that is deliberately outside this first Kev qualification.

## Acceptance criteria

- [ ] Frozen source packet uses official NEW Ithkuil Chapter 2, selected Chapter 3 §§3.1-3.2, and selected Chapter 4 §§4.1-4.2.10.
- [ ] Full Chapter 2 may be context, but phonological trivia is not scored merely because it is present.
- [ ] The 36 cells above are encoded without model-authored rewriting.
- [ ] F01-SIMPLE and F02-SIMPLE remain compositional two-feature/morpheme tasks.
- [ ] F01-HARD and F02-HARD are complete source-backed sentence tasks.
- [ ] Source-derived novel combinations remain segmented unless a surface realization is independently validated.
- [ ] Near-misses mutate one controlled semantic dimension whenever possible.
- [ ] Kev-4B runs all canonical cells plus one deterministic candidate-order permutation.
- [ ] Every probability vector and selection is retained.
- [ ] Sequential intermediate correctness is separate from final correctness.
- [ ] Results are reported by capability family and semantic dimension.
- [ ] Token ABI is not used as a fake Ithkuil ontology.
- [ ] Codex authors no new linguistic gold in this epoch.
- [ ] The run ends with a concrete recommendation for the next Kev/Bilqis step.

## Dependencies and boundaries

Depends on:
- #65 for the working Kev-4B local harness/runtime;
- #35 for any redistribution posture affecting committed donor excerpts.

Coordinates with:
- #8 donor grammar mapping;
- #7 semantic ABI;
- #53 grammar/lexical bootstrap;
- #71 semantic navigation.

#7/#8/#53 do not need to be complete for fixture-local proving work. Results from #77 may inform them, but #77 does not redefine their authority.

Parent roadmap: #5.
