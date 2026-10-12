# Every incorrect or unstable Kev decision

Exact prompts, all original choices, both distributions, and source-based explanations follow. Labels preserve candidate identity; the separately recorded order is what Kev saw.

<a id="f01-simple"></a>
## F01-SIMPLE

**Failure categories:** Configuration, Affiliation, order sensitivity.

**Source:** [2.3](https://www.ithkuil.net/newithkuil_02_morpho-phonology.htm), [3.1](https://www.ithkuil.net/newithkuil_03_morphology.htm), [3.2.3](https://www.ithkuil.net/newithkuil_03_morphology.htm), [3.6](https://www.ithkuil.net/newithkuil_03_morphology.htm).

**Why the gold follows:** DSS supplies two similar separate members; COA supplies distinct complementary functions. (source-derived).

### F01-SIMPLE

**Exact prompt**

```text
A pair consists of two physically separate, similar members. Their individual functions are distinct but complementary and together serve one unified role. Which segmented New Ithkuil Slot-VI semantic bundle best matches?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F01-SIMPLE.A`) | COA(-r-) + DSS(-c-) | 0.3687 | 0.8596 |
| B (`F01-SIMPLE.B`) | ASO(-l-) + DSS(-c-) | 0.2058 | 0.0637 |
| C (`F01-SIMPLE.C`) | COA(-r-) + DDS(-ţs-) | 0.3801 | 0.0628 |
| D (`F01-SIMPLE.D`) | VAR(-ř-) + DSS(-c-) | 0.0455 | 0.0139 |

**Gold:** A. **Kev canonical:** C. **Kev permuted:** A.
**Canonical order:** F01-SIMPLE.A, F01-SIMPLE.B, F01-SIMPLE.C, F01-SIMPLE.D.
**Permuted order:** F01-SIMPLE.D, F01-SIMPLE.A, F01-SIMPLE.B, F01-SIMPLE.C.
**Probability movement:** gold ΔP +0.4909; total variation distance 0.4909.

<a id="f03-medium"></a>
## F03-MEDIUM

**Failure categories:** root/stem.

**Source:** [2.4.3](https://www.ithkuil.net/newithkuil_02_morpho-phonology.htm), [2.4.4](https://www.ithkuil.net/newithkuil_02_morpho-phonology.htm).

**Why the gold follows:** The -edn- Stem 2 designation/reference identity survives the OBJ Specification in edni. (source-explicit).

### F03-MEDIUM

**Exact prompt**

```text
For the form edni, which root/stem identity supplies the lexical-semantic core before other morphology is interpreted?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F03-MEDIUM.A`) | -DN-, Stem 1: name | 0.6917 | 0.5123 |
| B (`F03-MEDIUM.B`) | -DN-, Stem 2: designation/reference | 0.1629 | 0.2542 |
| C (`F03-MEDIUM.C`) | -DN-, Stem 3: label | 0.0635 | 0.0773 |
| D (`F03-MEDIUM.D`) | -DN-, Stem Zero: deliberately undifferentiated calling/reference concept | 0.0819 | 0.1562 |

**Gold:** B. **Kev canonical:** A. **Kev permuted:** A.
**Canonical order:** F03-MEDIUM.A, F03-MEDIUM.B, F03-MEDIUM.C, F03-MEDIUM.D.
**Permuted order:** F03-MEDIUM.D, F03-MEDIUM.A, F03-MEDIUM.B, F03-MEDIUM.C.
**Probability movement:** gold ΔP +0.0913; total variation distance 0.1794.

<a id="f10-simple"></a>
## F10-SIMPLE

**Failure categories:** Configuration, Affiliation, reconstruction.

**Source:** [3.1](https://www.ithkuil.net/newithkuil_03_morphology.htm), [3.2.3](https://www.ithkuil.net/newithkuil_03_morphology.htm), [3.6](https://www.ithkuil.net/newithkuil_03_morphology.htm).

**Why the gold follows:** Two table-derived decisions determine the explicitly frozen COA + DSS bundle. (source-derived).

**Sequence target:** a complementary pair of similar, physically separate members.

### F10-SIMPLE.S1

**Exact prompt**

```text
Which Configuration?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F10-SIMPLE.S1.A`) | DPX | 0.2736 | 0.3642 |
| B (`F10-SIMPLE.S1.B`) | DSS | 0.2460 | 0.2609 |
| C (`F10-SIMPLE.S1.C`) | DSC | 0.2436 | 0.2171 |
| D (`F10-SIMPLE.S1.D`) | DDS | 0.2367 | 0.1578 |

**Gold:** B. **Kev canonical:** A. **Kev permuted:** A.
**Canonical order:** F10-SIMPLE.S1.A, F10-SIMPLE.S1.B, F10-SIMPLE.S1.C, F10-SIMPLE.S1.D.
**Permuted order:** F10-SIMPLE.S1.D, F10-SIMPLE.S1.A, F10-SIMPLE.S1.B, F10-SIMPLE.S1.C.
**Probability movement:** gold ΔP +0.0149; total variation distance 0.1055.

**Canonical and paired-permutation input path:**

```json
{
  "target": "a complementary pair of similar, physically separate members.",
  "fixed_predicate": null,
  "selected_path": []
}
```

<a id="f10-medium"></a>
## F10-MEDIUM

**Failure categories:** Configuration, Affiliation, holistic composition, reconstruction, order sensitivity.

**Source:** [3.1](https://www.ithkuil.net/newithkuil_03_morphology.htm), [3.2.3](https://www.ithkuil.net/newithkuil_03_morphology.htm).

**Why the gold follows:** The toolset example explicitly supplies MDS, COA and čverţa. (source-derived).

**Sequence target:** TOOLSET.

### F10-MEDIUM.S2

**Exact prompt**

```text
Which Affiliation?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F10-MEDIUM.S2.A`) | CSL | 0.3164 | 0.2782 |
| B (`F10-MEDIUM.S2.B`) | ASO | 0.2251 | 0.2398 |
| C (`F10-MEDIUM.S2.C`) | COA | 0.2709 | 0.3027 |
| D (`F10-MEDIUM.S2.D`) | VAR | 0.1876 | 0.1793 |

**Gold:** C. **Kev canonical:** A. **Kev permuted:** C.
**Canonical order:** F10-MEDIUM.S2.A, F10-MEDIUM.S2.B, F10-MEDIUM.S2.C, F10-MEDIUM.S2.D.
**Permuted order:** F10-MEDIUM.S2.D, F10-MEDIUM.S2.A, F10-MEDIUM.S2.B, F10-MEDIUM.S2.C.
**Probability movement:** gold ΔP +0.0318; total variation distance 0.0465.

**Canonical and paired-permutation input path:**

```json
{
  "target": "TOOLSET.",
  "fixed_predicate": null,
  "selected_path": [
    {
      "decision_id": "F10-MEDIUM.S1",
      "candidate_id": "F10-MEDIUM.S1.C",
      "description": "MDS"
    }
  ]
}
```

<a id="f10-hard"></a>
## F10-HARD

**Failure categories:** semantic role, case morphology, holistic composition, reconstruction, order sensitivity.

**Source:** [4.2.2](https://www.ithkuil.net/newithkuil_04_case.htm), [4.2.3](https://www.ithkuil.net/newithkuil_04_case.htm), [4.2.7](https://www.ithkuil.net/newithkuil_04_case.htm), [4.2.10](https://www.ithkuil.net/newithkuil_04_case.htm).

**Why the gold follows:** The worked sentence explicitly supplies child ERG, leg ABS, rock INS and the matching complete form. (source-derived).

**Sequence target:** “The child intentionally hit their leg with a rock.”

**Scoring interpretation:** final gold A remains the fixed target answer. With the recorded wrong IND + LOC + INS path, choice B is path-consistent. The final prompt refers to that path, so score target correctness and path consistency separately; both recorded paths fail joint target correctness.

### F10-HARD.S1

**Exact prompt**

```text
child case?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F10-HARD.S1.A`) | ERG | 0.2341 | 0.2396 |
| B (`F10-HARD.S1.B`) | IND | 0.4581 | 0.4419 |
| C (`F10-HARD.S1.C`) | ABS | 0.1801 | 0.2027 |
| D (`F10-HARD.S1.D`) | EFF | 0.1278 | 0.1158 |

**Gold:** A. **Kev canonical:** B. **Kev permuted:** B.
**Canonical order:** F10-HARD.S1.A, F10-HARD.S1.B, F10-HARD.S1.C, F10-HARD.S1.D.
**Permuted order:** F10-HARD.S1.D, F10-HARD.S1.A, F10-HARD.S1.B, F10-HARD.S1.C.
**Probability movement:** gold ΔP +0.0055; total variation distance 0.0281.

**Canonical and paired-permutation input path:**

```json
{
  "target": "“The child intentionally hit their leg with a rock.”",
  "fixed_predicate": "Weţdosmá",
  "selected_path": []
}
```

### F10-HARD.S2

**Exact prompt**

```text
leg case?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F10-HARD.S2.A`) | ABS | 0.1720 | 0.2266 |
| B (`F10-HARD.S2.B`) | THM | 0.2827 | 0.2369 |
| C (`F10-HARD.S2.C`) | LOC | 0.4434 | 0.4446 |
| D (`F10-HARD.S2.D`) | DAT | 0.1019 | 0.0919 |

**Gold:** A. **Kev canonical:** C. **Kev permuted:** C.
**Canonical order:** F10-HARD.S2.A, F10-HARD.S2.B, F10-HARD.S2.C, F10-HARD.S2.D.
**Permuted order:** F10-HARD.S2.D, F10-HARD.S2.A, F10-HARD.S2.B, F10-HARD.S2.C.
**Probability movement:** gold ΔP +0.0546; total variation distance 0.0558.

**Canonical and paired-permutation input path:**

```json
{
  "target": "“The child intentionally hit their leg with a rock.”",
  "fixed_predicate": "Weţdosmá",
  "selected_path": [
    {
      "decision_id": "F10-HARD.S1",
      "candidate_id": "F10-HARD.S1.B",
      "description": "IND"
    }
  ]
}
```

### F10-HARD.S4

**Exact prompt**

```text
Choose the source-backed complete sentence consistent with the selected path.
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F10-HARD.S4.A`) | Weţdosmá welo šnaliothe aggwilä. | 0.5074 | 0.3673 |
| B (`F10-HARD.S4.B`) | Weţdosmá welu šnali’othia aggwilä. | 0.2807 | 0.3859 |
| C (`F10-HARD.S4.C`) | Weţdosmá wele šnali’othia aggwilä. | 0.1607 | 0.1031 |
| D (`F10-HARD.S4.D`) | Weţdosmá welu aggwilä. | 0.0512 | 0.1437 |

**Gold:** A. **Kev canonical:** A. **Kev permuted:** B.
**Canonical order:** F10-HARD.S4.A, F10-HARD.S4.B, F10-HARD.S4.C, F10-HARD.S4.D.
**Permuted order:** F10-HARD.S4.D, F10-HARD.S4.A, F10-HARD.S4.B, F10-HARD.S4.C.
**Probability movement:** gold ΔP -0.1401; total variation distance 0.1977.

**Canonical and paired-permutation input path:**

```json
{
  "target": "“The child intentionally hit their leg with a rock.”",
  "fixed_predicate": "Weţdosmá",
  "selected_path": [
    {
      "decision_id": "F10-HARD.S1",
      "candidate_id": "F10-HARD.S1.B",
      "description": "IND"
    },
    {
      "decision_id": "F10-HARD.S2",
      "candidate_id": "F10-HARD.S2.C",
      "description": "LOC"
    },
    {
      "decision_id": "F10-HARD.S3",
      "candidate_id": "F10-HARD.S3.A",
      "description": "INS"
    }
  ]
}
```

<a id="f12-medium"></a>
## F12-MEDIUM

**Failure categories:** Configuration, uncertainty/clarification.

**Source:** [3.1](https://www.ithkuil.net/newithkuil_03_morphology.htm).

**Why the gold follows:** Reconstructed insufficiency follows because group gives multiplicity while exact Configuration also requires similarity and separability. (source-derived).

### F12-MEDIUM

**Exact prompt**

```text
English gloss: “a group of cats.”
Which exact Configuration should be selected?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F12-MEDIUM.A`) | MSS | 0.3423 | 0.4098 |
| B (`F12-MEDIUM.B`) | MSC | 0.2637 | 0.2340 |
| C (`F12-MEDIUM.C`) | MDS | 0.1363 | 0.1758 |
| D (`F12-MEDIUM.D`) | CLARIFY / INSUFFICIENT | 0.2576 | 0.1804 |

**Gold:** D. **Kev canonical:** A. **Kev permuted:** A.
**Canonical order:** F12-MEDIUM.A, F12-MEDIUM.B, F12-MEDIUM.C, F12-MEDIUM.D.
**Permuted order:** F12-MEDIUM.D, F12-MEDIUM.A, F12-MEDIUM.B, F12-MEDIUM.C.
**Probability movement:** gold ΔP -0.0772; total variation distance 0.1069.

<a id="f12-hard"></a>
## F12-HARD

**Failure categories:** semantic role, case morphology, uncertainty/clarification.

**Source:** [4.2.6](https://www.ithkuil.net/newithkuil_04_case.htm), [4.2.7](https://www.ithkuil.net/newithkuil_04_case.htm), [4.2.10](https://www.ithkuil.net/newithkuil_04_case.htm).

**Why the gold follows:** Reconstructed insufficiency follows because the source distinguishes direct ERG causation from EFF causal-chain initiation and the prompt omits that distinction. (source-derived).

### F12-HARD

**Exact prompt**

```text
“The child caused the clown to become angry.”
The description does NOT state whether the child directly acted on the clown or merely initiated an intermediate causal chain that resulted in the clown's anger.
Which case should be selected for the child?
```

| Candidate | Exact description | P canonical | P permuted |
|---|---|---:|---:|
| A (`F12-HARD.A`) | ERG | 0.0764 | 0.0888 |
| B (`F12-HARD.B`) | EFF | 0.6945 | 0.7345 |
| C (`F12-HARD.C`) | IND | 0.0391 | 0.0320 |
| D (`F12-HARD.D`) | CLARIFY / INSUFFICIENT | 0.1900 | 0.1447 |

**Gold:** D. **Kev canonical:** B. **Kev permuted:** B.
**Canonical order:** F12-HARD.A, F12-HARD.B, F12-HARD.C, F12-HARD.D.
**Permuted order:** F12-HARD.D, F12-HARD.A, F12-HARD.B, F12-HARD.C.
**Probability movement:** gold ΔP -0.0453; total variation distance 0.0524.
