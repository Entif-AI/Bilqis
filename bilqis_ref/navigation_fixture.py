"""#69 fixture-local semantic subset, explicitly subordinate to #7/#10/#27/#44."""
import copy
import json
from .semantics import canonical, digest

VERSION='bilqis-navigation-fixture-0.1.0'
FAMILIES=('exact_shallow','deep_composition','clarified_ambiguity','persistent_ambiguity',
          'outside_panel','absent_object','compositional_reuse','rare_discriminative_cue',
          'equivalent_alternate_order','capability_mismatch')


def resolve_object(corpus, identity, seen=()):
    if identity in seen or identity not in corpus['objects']:raise ValueError('REFERENCE_CYCLE_OR_MISSING')
    def expand(value):
        if isinstance(value,dict):
            if set(value)=={'ref'}:return resolve_object(corpus,value['ref'],(*seen,identity))
            return {k:expand(v) for k,v in value.items()}
        if isinstance(value,list):return [expand(v) for v in value]
        return value
    result=expand(corpus['objects'][identity])
    if digest(result)!=identity:raise ValueError('SEMANTIC_IDENTITY')
    return result


def build_corpus():
    objects={}
    def obj(value):
        def expand(v):
            if isinstance(v,dict):
                if set(v)=={'ref'}:return resolve_object({'objects':objects},v['ref'])
                return {k:expand(x) for k,x in v.items()}
            if isinstance(v,list):return [expand(x) for x in v]
            return v
        identity=digest(expand(value));objects[identity]=value;return identity
    red=obj({'kind':'tool','color':'red','purpose':'cutting','quantity':'single','evidence':'observed'})
    blue=obj({'kind':'tool','color':'blue','purpose':'cutting','quantity':'single','evidence':'observed'})
    container=obj({'kind':'container','color':'red','purpose':'holding','quantity':'single','evidence':'reported'})
    holding=obj({'kind':'tool','color':'red','purpose':'holding','quantity':'single','evidence':'observed'})
    group=obj({'kind':'composition','configuration':'ordered_pair','scope':'joint','evidence':'observed',
               'members':[{'ref':red},{'ref':blue}]})
    reverse=obj({'kind':'composition','configuration':'ordered_pair','scope':'joint','evidence':'reported',
                 'members':[{'ref':blue},{'ref':red}]})
    root=[red,blue,container];ambiguous=[red,holding];composed=[group,reverse]
    cases=[]
    def add(family,pool,path,hints,status='resolved',target=red,clarification=None,deeper=None,refs=None,capabilities=None,cue=None):
        cases.append({'id':'nav-'+family,'family':family,'scopes':{'root':pool,'deeper':deeper or pool},
                      'initial_live':pool,'factor_path':path,'hints':hints,
                      'evidence_schedule':[clarification] if clarification else [],
                      'resolved_refs':refs or [],'capabilities':capabilities or path,
                      'surface_cue':cue,'legal_neighborhoods':'values of the next factor among live objects; reserved routes stay explicit',
                      'expected_terminal':{'status':status,'object_id':target if status=='resolved' else None},
                      'provenance':['https://github.com/Entif-AI/Bilqis/issues/'+str(i) for i in [7,10,27,44,69]]})
    add(FAMILIES[0],root,['kind','color'],{'kind':'tool','color':'red'})
    add(FAMILIES[1],composed,['kind','configuration','scope','evidence'],
        {'kind':'composition','configuration':'ordered_pair','scope':'joint','evidence':'observed'},target=group)
    add(FAMILIES[2],ambiguous,['kind','color','purpose'],{'kind':'tool','color':'red'},clarification={'purpose':'cutting'})
    add(FAMILIES[3],ambiguous,['kind','color','purpose'],{'kind':'tool','color':'red'},status='ambiguous')
    add(FAMILIES[4],[red,blue],['kind','color'],{'kind':'container','color':'red'},target=container,deeper=root)
    add(FAMILIES[5],root,['kind'],{'kind':'novel_unlisted_kind'},status='absent')
    add(FAMILIES[6],composed,['kind','configuration','scope','evidence'],
        {'kind':'composition','configuration':'ordered_pair','scope':'joint','evidence':'observed'},target=group,refs=[red,blue])
    add(FAMILIES[7],ambiguous,['kind','color','purpose'],{'kind':'tool','color':'red','purpose':'cutting'},
        cue='holding holding holding holding; the explicit rare distinction is purpose=cutting')
    add(FAMILIES[8],root,['kind','color'],{'color':'red','kind':'tool'})
    add(FAMILIES[9],ambiguous,['kind','color','purpose'],{'kind':'tool','color':'red','purpose':'cutting'},
        status='unsupported',capabilities=['kind','color'])
    return {'version':VERSION,'authority':{'subset':'fixture-local typed factors and references',
            'subordinate_to_issues':[7,10,27,44,69],'official_rosetta_authority':False,
            'compatibility':'Does not extend or reinterpret bilqis-finite-world-0.1.0. No full #7 ABI claim.'},
            'objects':objects,'cases':cases,'optional_dependencies':{'53':'no donor lexical material used',
            '67':'no learned sparse address machinery','59':'no adjacent-resolution interoperability claim',
            'Akasha':'not required for synthetic corpus'},
            'control_scope':'Factor-list versus named-field serialization of the same prototype. No donor-specific learning claim.'}


def context(corpus,case,hints=None):
    closure=set(x for scope in case['scopes'].values() for x in scope)
    def references(value):
        if isinstance(value,dict):
            if set(value)=={'ref'}:
                identity=value['ref']
                if identity not in closure:
                    closure.add(identity);references(corpus['objects'][identity])
            else:
                for v in value.values():references(v)
        elif isinstance(value,list):
            for v in value:references(v)
    for identity in list(closure):references(corpus['objects'][identity])
    ids=sorted(closure)
    for identity in ids:resolve_object(corpus,identity)
    return {'abi':corpus['version'],'objects':{i:corpus['objects'][i] for i in ids},
            'hints':copy.deepcopy(case['hints'] if hints is None else hints),'capabilities':case['capabilities'],
            'resolved_refs':case['resolved_refs'],'surface_cue':case['surface_cue']}


def render(corpus,case,representation,hints=None):
    value=context(corpus,case,hints)
    if representation=='bilqis':value={'fixture_abi':corpus['version'],'factors':[[k,value[k]] for k in sorted(value)]}
    elif representation!='typed':raise ValueError('NAVIGATION_REPRESENTATION')
    return canonical(value).decode()


def decode(surface,representation):
    value=json.loads(surface)
    if representation=='bilqis':
        if set(value)!={'fixture_abi','factors'}:raise ValueError('FACTOR_ENVELOPE')
        pairs=value['factors']
        if any(not isinstance(p,list) or len(p)!=2 or not isinstance(p[0],str) for p in pairs):raise ValueError('FACTOR_SHAPE')
        if len({p[0] for p in pairs})!=len(pairs):raise ValueError('DUPLICATE_FACTOR')
        result=dict(pairs)
        if result.get('abi')!=value['fixture_abi']:raise ValueError('FACTOR_ABI')
        return result
    if representation!='typed':raise ValueError('NAVIGATION_REPRESENTATION')
    return value
