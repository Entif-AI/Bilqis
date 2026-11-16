"""Three source-qualified Ithkuil senses share a finite before/after event adapter.

This models observed occurrence, inactive-to-active commencement and active-to-
inactive termination. It does not realize morphology, causation or origination.
Catalog additions remain neural-inert proposals until the BAMF admission owner
accepts them; this module owns only source semantics, generation and checking.
"""
from dataclasses import replace
from pathlib import Path
import random

from ..curriculum import AnswerFamily, BINARY
from ..factory.adapters import RegisteredSourceAdapter
from ..factory.model import SourceAdapter
from ..factory.curriculum_definition import CapabilitySpec, CapabilitySourceBinding, GradeSpec
from ..factory.executable_release import compile_executable_factory_release
from ..factory.execution import CurriculumProfile
from ..semantics.core import Apply, Operation, Signature, literal
from ..factory.verification import (
    EVENT_FRAME_ORACLE as ORACLE, event_frame_answer as independent_answer,
)
from ..factory.semantic_contrast.teaching import (
    OPTION_ID as SEMANTIC_CONTRAST_OPTION,
    check_contrast_row,
    contrast_semantic_footprint,
    enrich_contrasts,
)
from ..vocabulary_growth import digest
from .event_authority import (
    SEMANTIC_IDS, SOURCE_SPECS, SPECS, SYMBOLS, atlas_semantic_id,
    provider_implementation_digest, source_contract_digest, source_invalid as _source_invalid,
    source_senses, _verify_source_row,
)
from .event_staging import (
    capability_definition, event_grade_id, expanded_graph, projected_graph, stage_capability,
)

DIALECT = 'bilqis.finite-event-frame/v1'
GENERATOR = 'bilqis.ithkuil-event-frame-constructor/v1'
ADAPTER_ID = 'source.ithkuil-event-frames/v1'
ROOT = Path(__file__).resolve().parents[3]
_BALANCE_MODULUS = 2


TRUE, FALSE = 'cogal.value.true', 'cogal.value.false'


def expression(graph, capability, before, after):
    symbol = SYMBOLS[capability]
    operation = Operation(graph['tokens'].index(symbol), symbol,
        Signature(('Boolean','Boolean'),'Boolean'), graph['row_contract_sha256'][symbol])
    return Apply(operation, (literal(before,'Boolean'), literal(after,'Boolean')), 'Boolean', None)


def evaluate(node):
    before, after = (arg.value for arg in node.arguments)
    cap = next(cap for cap, symbol in SYMBOLS.items() if node.operator.symbol == symbol)
    if cap == 'D.EVENT_OCCURRENCE':
        return after
    if cap == 'D.COMMENCEMENT':
        return not before and after
    return before and not after


def encode(record):
    symbols = ['micro.syntax.world', 'development.syntax.events']
    for name, before, after in record['events']:
        symbols.extend(('development.Event.'+name, TRUE if before else FALSE,
                        TRUE if after else FALSE))
    return [*symbols, 'micro.syntax.query', SYMBOLS[record['capability']],
            'development.Event.'+record['query'], 'syntax.end']


def draw(source_root, graph, *, seed, each=12, capability, **_):
    source_senses()
    if capability not in SPECS or type(each) is not int or each < 1:
        raise ValueError('EVENT_FRAME_INVALID_DRAW')
    rng = random.Random(digest((GENERATOR, seed, capability)))
    ids = {token:i for i,token in enumerate(graph['tokens'])}
    rows, seen = [], set()
    while len(rows) < each:
        names = rng.sample(['E0','E1','E2','E3'],4)
        events = [[name, bool(rng.getrandbits(1)), bool(rng.getrandbits(1))] for name in names]
        query = rng.choice(names)
        record = dict(task=DIALECT, events=events, query=query, capability=capability)
        selected = next(e for e in events if e[0]==query)
        gold = evaluate(expression(graph,capability,*selected[1:]))
        if gold != (len(rows) % _BALANCE_MODULUS == 0):
            continue
        identity = digest(record)
        if identity in seen:
            continue
        seen.add(identity)
        rows.append(dict(id=identity,source_id=identity,capability=capability,
            answer_kind='binary',gold='TRUE' if gold else 'FALSE',record=record,
            tokens=[ids[s] for s in encode(record)],root=SYMBOLS[capability],
            generator=GENERATOR,oracle=ORACLE,source_sense_id=SPECS[capability][0]))
    return tuple(rows)


def check(row, *, graph, **_):
    if row.get('generator') == SEMANTIC_CONTRAST_OPTION:
        return check_contrast_row(row, graph=graph)
    try:
        record = row['record']; cap = record['capability']
        return (row['gold']==independent_answer(record) and
            row['id']==row['source_id']==digest(record) and
            row['capability']==cap and row['source_sense_id']==SPECS[cap][0] and
            row['root']==SYMBOLS[cap] and row['generator']==GENERATOR and
            row['oracle']==ORACLE and row['answer_kind']=='binary' and
            all(type(i) is int and 0 <= i < len(graph['tokens']) for i in row['tokens']) and
            [graph['tokens'][i] for i in row['tokens']]==encode(record))
    except (KeyError,TypeError,ValueError,IndexError):
        return False


def semantic_footprint(row):
    if row.get('generator') == SEMANTIC_CONTRAST_OPTION:
        return contrast_semantic_footprint(row)
    root = row.get('root')
    if not isinstance(root, str) or not root:
        from ..errors import ErrorBus, SCHOOL
        ErrorBus.raise_(
            SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID,
            reason='EVENT_FRAME_SEMANTIC_FOOTPRINT_INVALID',
        )
    return (root,)


def witness_obligation(row, obligation, **kw):
    return (check(row, **kw)
            and row.get('generator') == GENERATOR
            and obligation.key in SPECS[row['capability']][1])


def registered_adapter():
    return RegisteredSourceAdapter(SourceAdapter(ADAPTER_ID,
        GENERATOR,(ORACLE,),provider_implementation_digest(),
        variation_axes=('event-identity','before-state','after-state','fact-order','fresh-seed'),
        teaching_option_ids=(SEMANTIC_CONTRAST_OPTION,)),
        draw,check,
        witness=witness_obligation,
        enrich=enrich_contrasts,
        semantic_footprint=semantic_footprint)


def compile_tranche(current, graph, *, source_root, source_registry, answer_registry):
    """Compile the three source-qualified event capabilities without admitting them."""
    sources = source_senses()
    caps = tuple(CapabilitySpec(cap,'finite-event-frame',(SYMBOLS[cap],),(SYMBOLS[cap],),
        prerequisites,(),(AnswerFamily('binary',BINARY),))
        for cap,(_,prerequisites) in SPECS.items())
    grade = GradeSpec(event_grade_id(current.curriculum),caps,tuple((cap,12) for cap in SPECS),
        tuple((cap,) for cap in SPECS))
    curriculum = replace(current.curriculum,grades=(*current.curriculum.grades,grade))
    bindings = replace(current.source_bindings,bindings=(*current.source_bindings.bindings,
        *(CapabilitySourceBinding(cap,'ithkuil:sense/'+sense+'@sha256:'+sources[cap]['source_text_sha256'],
            GENERATOR,ORACLE) for cap,(sense,_) in SPECS.items())))
    return compile_executable_factory_release(curriculum,bindings,
        CurriculumProfile('bamf/event-frames/v1',grades=current.profile.grades),
        source_registry,answer_registry,source_root=source_root,graph=graph,
        verification_seed=2026110703,predecessor=current)
