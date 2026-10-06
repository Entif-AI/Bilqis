"""Reproduce the owned #65 diagnostic corpus, without consulting a scorer."""
from .semantics import World, Entity, oracle, independent_oracle, LABELS, LABEL_NAMES
from .teacher import TeacherState, STAGE_NAMES, PREREQUISITES

VERSION = 'bilqis-decision-fixture-0.1.0'


def build_fixture():
    items = []
    def add(identity, state, question, options, label, owner, origin):
        items.append({'id': identity, 'state': state, 'question': question,
                      'options': [{'id': k, 'description': v} for k, v in options],
                      'label': label, 'split': 'DEV', 'provenance': {
                          'source': f'https://github.com/Entif-AI/Bilqis/issues/{owner}',
                          'rights': 'independently_project_authored', 'label_origin': origin,
                          'contamination': 'public diagnostic authored after model release; training overlap unknown'}})
    options = list(zip(LABEL_NAMES, ['Evidence supports true only.', 'Evidence supports false only.',
                                   'No evidence supports either truth value.', 'Evidence supports both truth values.']))
    for group, reports in enumerate([((1,0),(0,1),(0,0)), ((1,1),(0,0),(1,0)), ((0,1),(1,1),(0,0))]):
        w = World((Entity(0,0,1,2), Entity(1,1,0,1)), ((0,1),), reports)
        queries = [{'op':'EVID','value':i} for i in range(3)] + [{'op':'APL','a':0,'value':1}]
        for index, query in enumerate(queries):
            a = oracle(w,query); b = independent_oracle(w,query)
            if a != b: raise RuntimeError('ORACLE_DISAGREEMENT')
            question = (f'Evaluate {query}. EVID reads the indicated report pair; APL compares actual use to value. '
                        'For report pairs, the first bit supports true and the second supports false. '
                        'An ordinary failed comparison supports false only. Preserve unknown and conflict.')
            add(f'evidence-{group}-{index}', w.obj(), question, options, LABEL_NAMES[LABELS.index(a)], 7,
                'existing recursive-bfs-v1 and independent postorder-closure-v1 oracles agree')
    for index, promoted in enumerate([[],[0],[0,1],[0,1,2],[0,4]]):
        t = TeacherState(promoted=promoted, tranches={'1':2,'2':1})
        state = {'promoted': [STAGE_NAMES[i] for i in promoted], 'tranches':t.tranches,
                 'stage_indices': dict(zip(STAGE_NAMES,range(5))),
                 'prerequisites': {STAGE_NAMES[k]:[STAGE_NAMES[i] for i in v] for k,v in PREREQUISITES.items()}}
        add(f'curriculum-{index}',state,
            'Choose a remaining stage whose prerequisites are promoted. Prefer the fewest already exposed tranches '
            '(missing count means zero), breaking ties by smallest stage index. Do not promote any stage.',
            [(s,f'Propose stage {i}: {s}.') for i,s in enumerate(STAGE_NAMES)]+[('insufficient','Insufficient admissibility evidence.')],
            STAGE_NAMES[t.choose()],16,'existing TeacherState.choose topology policy')
    relation_options = [('taxonomic','Subclass or instance of a class.'),('part_whole','Constituent part of a whole.'),
                        ('causal','Explicit enabling causal relation.'),('temporal','Explicit temporal ordering.'),
                        ('analogy','Declared metaphor or analogy.'),('cooccurrence','Surface co-occurrence without a semantic claim.'),
                        ('other','A different relation family.'),('insufficient','Insufficient evidence for a relation.')]
    relation_map = {'is_a':'taxonomic','part_of':'part_whole','enables':'causal','before':'temporal',
                    'metaphor_of':'analogy','co_occurs':'cooccurrence'}
    definitions = {'is_a':'membership/subclass assertion','part_of':'constituent assertion',
                   'enables':'declared causal enabling assertion','before':'temporal ordering assertion',
                   'metaphor_of':'explicit metaphor assertion','co_occurs':'surface co-occurrence only'}
    for predicate,label in relation_map.items():
        add(f'relation-{predicate}',{'assertion':{'subject':'fixture-a','predicate':predicate,'object':'fixture-b'},
                                    'predicate_definitions':definitions},
            'Classify the explicitly asserted relation. Do not infer additional relations from association.',
            relation_options,label,53,'fixture-local frozen predicate-to-family mapping; no donor lexical claims')
    for identity,state in [('review-ambiguous',{'surface':'bank','context':'unspecified'}),
                           ('review-absent',{'surface':'unlisted relation','assertion':None})]:
        add(identity,state,'Which relation family is established by this evidence?',relation_options,None,53,
            'unlabeled review-only; no model or teacher gold')
    return {'version':VERSION,'authority':'diagnostic subset subordinate to #7/#16/#53; no SYS-01 or gold authority',
            'policy': {'local_probability':0.8,'local_margin':0.2,'confident_wrong_probability':0.8,
                       'ece_min_labeled':100,'qualification_accuracy':0.8,'qualification_min_labeled':20},
            'items':items}
