"""The full designed fifty-grade spiral, distinct from compiler availability.

A grade introduces a game mechanic, not a permission gate. Earlier mechanics
return in current examples, and the next two grades can supply only truthfully
compiled, source-verified preview lessons. Never invent linguistic gold just
because a grade title exists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

SCHEMA = "bilqis.skill-tree/v1"
SOURCES = {
    "math": "https://github.com/Entif-AI/Bilqis/issues/108",
    "grammar": "https://www.ithkuil.net/",
    "lexicon": "https://ithkuil.net/New_Ithkuil_Lexicon.pdf",
}

# Grade title, causal mechanic or manipulation, source-ready lesson selector.
# A null/empty compiler means: designed curriculum, NOT executable gold.
_DESIGN = [
    ("Boolean states", "Differentiate TRUE, FALSE and observable counterexample", "micro:0"),
    ("Negation and conjunction", "Invert a truth state; distinguish AND from OR", "micro:0"),
    ("Boolean compositions", "Reason through nested implications and XOR", "micro:0"),
    ("Typed entities and direction", "Reverse directed PARENT/CHILD while preserving identity", "micro:1"),
    ("Equality and relation structure", "Track identity, non-identity and symmetric vs directed relations", "micro:1"),
    ("Existential quantification", "Find witnesses rather than memorized output labels", "micro:2"),
    ("Universal quantification", "Distinguish every case from a single witness or counterexample", "micro:2"),
    ("Relational composition", "Infer two-hop relationships with scoped variables", "micro:2"),
    ("Rules and entailment", "Separate premises and derived conclusions from asserted content", "micro:3"),
    ("Evidence and interpretations", "Distinguish unknown, false, true, conflict and ambiguity", "micro:4"),
    ("Set membership and subset", "Change an element's membership without changing type", "development:5:set-"),
    ("Set operations", "Combine membership with intersection and directed difference", "development:5:set-"),
    ("Function domains and inverses", "Distinguish directed mapping input/output and invertibility", "development:5:function-"),
    ("Function composition", "Preserve order through multi-step partial function application", "development:5:function-"),
    ("Directed graphs and reachability", "Separate adjacency from directed transitive paths", "development:5:graph-"),
    ("Provenance and ancestry", "Separate transitive derivation from mere proof-premise dependency", "development:6:provenance-ancestry"),
    ("Proof dependency and supersession", "Separate DEPENDS_ON from historical replacement", "lineage"),
    ("Current versus historical evidence", "Remove superseded contributions while preserving audit history", "development:6:current-evidence"),
    ("Integers, order and equality", "Represent number identities, sign, magnitude and ordering", "math:19"),
    ("Arithmetic and inverses", "Compose addition, subtraction, multiplication and division", "math:20"),
    ("Algebraic identities", "Distinguish equivalence from surface order or shape", "math:21"),
    ("Mixed logical/mathematical proof", "Apply distributivity and numerical conditions in an explicit derivation", "math:22"),
    # Grammatical stages align with New Ithkuil (2023), NOT the earlier 2011 grammar.
    ("Phonological distinctions", "Hear and encode permissible phoneme/stress contrasts", None),
    ("Root, stem and specification", "Separate abstract roots from stem and specification meanings", None),
    ("Formative slot structure", "Construct parseable morphological slot boundaries and dependencies", None),
    ("Configuration and affiliation", "Distinguish number/arrangement from functional relationships", None),
    ("Perspective, extension, essence", "Control semantic scope, portion, and representational essence", None),
    ("Case roles and relations", "Contrast agent, patient, instrument and recipient in minimal pairs", None),
    ("Mood, illocution and validation", "Separate truth, communicative act and evidential warrant", None),
    ("Valence, phase, aspect and modality", "Compose participant structure and event-time distinctions", None),
    ("Affixes and degree semantics", "Infer meaning changes from scoped derivational affordances", None),
    ("Adjuncts, referentials and deixis", "Bind discourse references while preserving typed scope", None),
    ("Syntax and semantic scope", "Distinguish role-binding from word order and attachment", None),
    ("Surface realization and parsing", "Encode and decode canonical formatives without meaning drift", None),
    ("Full grammatical composition", "Produce and parse multiclause semantics with independently verified scope", None),
    # Lexical grades are meaning-organized, and root coverage is sourced; no fake glosses.
    ("Core grammatical roots", "Bind names, reference and copular semantics to root/stem senses", None),
    ("Tools and common actions", "Differentiate action, instrument, result and patient", None),
    ("Space, motion and time", "Compose spatial and temporal lexical relations", None),
    ("Perception and sensation", "Differentiate observer, sensory modality, property and experience", None),
    ("Cognition and affect", "Compose belief, uncertainty, experience and emotional perspective", None),
    ("Kinship and social roles", "Infer reciprocal and role-specific interpersonal relations", None),
    ("Quantity and mathematical lexemes", "Map New Ithkuil number roots onto preserved arithmetic semantics", None),
    ("Matter, materials and processes", "Distinguish material taxonomies and state change", None),
    ("Bodies, health and biology", "Resolve organism, bodily part, process and condition roots", None),
    ("Animals, life and ecology", "Organize taxonomy, behavior, habitat and relational predicates", None),
    ("Plants and natural-world taxa", "Compose class, species, growth and ecological relations", None),
    ("Artifacts, technology and culture", "Differentiate process, tool, constructed object and use", None),
    ("Abstract relations and qualities", "Distinguish degrees, roles, perspectives and causal properties", None),
    ("Stem/specification semantic networks", "Revisit a root across stems and specifications; resist false synonymy", None),
    ("Full lexicon and grammar spiral", "Express novel connected situations by combining the entire verified skill tree", None),
]

@dataclass(frozen=True)
class Grade:
    number: int
    id: str
    domain: str
    title: str
    mechanic: str
    prerequisites: tuple[str, ...]
    rehearsal: tuple[str, ...]
    foreshadows: tuple[str, ...]
    compiler: str | None
    source_locator: str

    @property
    def ready(self):
        return self.compiler is not None


def skill_tree() -> tuple[Grade, ...]:
    result = []
    for i, (title, mechanic, compiler) in enumerate(_DESIGN, start=1):
        domain = "logic_math" if i <= 22 else "ithkuil_grammar" if i <= 35 else "ithkuil_lexicon"
        code = f"G{i:02d}"
        # The dependency chain is never a mastery stop; earlier skills are
        # revisited cyclically and later ones may be previewed semantically.
        prerequisites = (f"G{i-1:02d}",) if i > 1 else ()
        rehearsal = tuple(dict.fromkeys(
            f"G{k:02d}" for k in (i-1, i-2, i-5, i-8) if k >= 1))
        foreshadows = tuple(f"G{k:02d}" for k in (i+1, i+2) if k <= 50)
        source = SOURCES["math" if i <= 22 else "grammar" if i <= 35 else "lexicon"]
        result.append(Grade(i,code,domain,title,mechanic,prerequisites,
                            rehearsal,foreshadows,compiler,source))
    validate(tuple(result))
    return tuple(result)


def validate(grades: tuple[Grade, ...]):
    if len(grades) != 50 or [g.number for g in grades] != list(range(1,51)):
        raise ValueError("FIFTY_GRADE_CARDINALITY_OR_ORDER_CHANGED")
    if [sum(g.domain == domain for g in grades) for domain in
        ("logic_math","ithkuil_grammar","ithkuil_lexicon")] != [22,13,15]:
        raise ValueError("GRADE_DOMAIN_ALLOCATION_MISMATCH")
    for g in grades:
        if g.id != f"G{g.number:02d}" or not g.title or not g.mechanic:
            raise ValueError("INVALID_GRADE_CONCEPT_IDENTITY")
        if any(int(s[1:]) >= g.number for s in g.prerequisites+g.rehearsal):
            raise ValueError("BACKWARD_PREREQUISITE_MUST_PRECEDE_INTRODUCTION")
        if any(int(s[1:]) not in (g.number+1,g.number+2) for s in g.foreshadows):
            raise ValueError("PREVIEW_BEYOND_NEXT_TWO_GRADES")
    if len({g.id for g in grades}) != 50:
        raise ValueError("DUPLICATE_GRADE_IDENTITY")


def manifest():
    grades=skill_tree()
    return {"schema":SCHEMA, "mode":"DEVELOPMENT_FIRST_NO_MASTERY_STOP",
            "grade_counts":{"logic_math":22,"ithkuil_grammar":13,"ithkuil_lexicon":15},
            "ready_generators":sum(g.ready for g in grades),
            "designed_not_yet_compiled":sum(not g.ready for g in grades),
            "behavior":"Repeated G01->G50 spirals; prior rehearsal + meaning-based current examples + bounded previews; accumulate student and teacher state. Unimplemented grades are explicit blockers, never fake tasks.",
            "grades":[{**asdict(g),"prerequisites":list(g.prerequisites),
                        "rehearsal":list(g.rehearsal),
                        "foreshadows":list(g.foreshadows),"ready":g.ready}
                       for g in grades]}


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",type=Path)
    args=parser.parse_args()
    content=json.dumps(manifest(),ensure_ascii=False,indent=2)+"\n"
    if args.write:
        args.write.parent.mkdir(parents=True,exist_ok=True)
        args.write.write_text(content)
    else:
        print(content)


if __name__=="__main__":
    main()
