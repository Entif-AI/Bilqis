"""Deterministic transcription of the human-authored #77 contract.

Prompts, choices, gold, and supplied rationales are copied from issue bytes.
Source/anchor/dimension memberships are audit metadata, not additional gold.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

VERSION = 'new-ithkuil-kev-v0.1'
CONTEXT_SHA256 = 'c178cd133d051cddcca0eae8a69111b4696418425a6a99c27723786a6af898be'
DIFFICULTIES = ('SIMPLE','MEDIUM','HARD')
# Only source locators, memberships and classifications; no authored questions or answers.
AUDIT = {
 1: [('2.3,3.1,3.2.3,3.6','Configuration,Affiliation','G-03,G-04','source-derived'),
     ('2.4.4,3.1,3.2.2','Specification,Configuration,Affiliation','G-02,G-03,G-04','source-derived'),
     ('4.2.10','semantic role,case morphology,holistic composition','G-08','source-exact')],
 2: [('3.1,3.2.3,3.6','Configuration,Affiliation','G-03,G-04','source-derived'),
     ('2.4.4,3.1,3.2.4','Specification,Configuration,Affiliation','G-02,G-03,G-04','source-derived'),
     ('4.2.10','semantic role,case morphology,holistic composition','G-08','source-exact')],
 3: [('2.4.1,2.4.3,2.4.4','root/stem','G-01','source-exact'),
     ('2.4.3,2.4.4','root/stem','G-01','source-exact'),
     ('4.2.10','root/stem','G-08','source-exact')],
 4: [('4.1.1','semantic role','G-05','source-exact'),
     ('4.1.2','semantic role','G-06','source-exact'),
     ('4.2.10','semantic role','G-08','source-exact')],
 5: [('3.1','Configuration','G-03','source-derived'),
     ('3.1,3.2.3','Configuration,Affiliation','G-03,G-04','source-derived'),
     ('4.2.10','case morphology','G-08','source-exact')],
 6: [('4.2.3','case morphology','G-05','source-exact'),
     ('3.1','Configuration','G-03','source-exact'),
     ('4.2.2,4.2.3,4.2.7','semantic role,case morphology','G-05,G-08','source-derived')],
 7: [('3.1','Configuration','G-03','controlled-mutation'),
     ('3.2.2,3.2.3','Affiliation','G-04','controlled-mutation'),
     ('4.2.6,4.2.7,4.2.10','semantic role,case morphology','G-07','controlled-mutation')],
 8: [('3.1','Configuration','G-03','source-exact'),
     ('3.2.1,3.2.3','Affiliation','G-04','source-exact'),
     ('4.2.9,4.2.10','semantic role,case morphology','G-08','source-exact')],
 9: [('4.1.1','semantic role','G-05','source-derived'),
     ('3.1,3.2.2','Configuration,Affiliation','G-03,G-04','source-exact'),
     ('4.2.1,4.2.10','semantic role,case morphology','G-08','source-exact')],
 10:[('3.1,3.2.3,3.6','Configuration,Affiliation,reconstruction','G-03,G-04','source-derived'),
     ('3.1,3.2.3','Configuration,Affiliation,holistic composition,reconstruction','G-03,G-04','source-derived'),
     ('4.2.2,4.2.3,4.2.7,4.2.10','semantic role,case morphology,holistic composition,reconstruction','G-08','source-derived')],
 11:[('3.1,3.2.2','Configuration,Affiliation','G-03,G-04','source-derived'),
     ('3.2.2,3.2.3','Affiliation,holistic composition','G-04','controlled-mutation'),
     ('4.2.10','semantic role,case morphology,holistic composition','G-08','controlled-mutation')],
 12:[('4.1.1,4.1.2','semantic role,uncertainty/clarification','G-05,G-06','source-derived'),
     ('3.1','Configuration,uncertainty/clarification','G-03','source-derived'),
     ('4.2.6,4.2.7,4.2.10','semantic role,case morphology,uncertainty/clarification','G-07','source-derived')],
}


def metadata(family, difficulty):
    locs, dimensions, anchors, classification = AUDIT[family][DIFFICULTIES.index(difficulty)]
    return {'fixture_version':VERSION, 'family':family, 'difficulty':difficulty,
            'source_locators':[{'chapter':int(s[0]),'section':s} for s in locs.split(',')],
            'semantic_dimensions':dimensions.split(','), 'gold_anchor_ids':anchors.split(','),
            'classification':classification, 'permutation_eligible':True}


def options_from_letters(text, identity):
    matches=list(re.finditer(r'^([A-D])\. (.+?)(?=\n[A-D]\. |\Z)',text,flags=re.M|re.S))
    if len(matches)!=4:raise ValueError('ITHKUIL_OPTION_TRANSCRIPTION')
    return [{'id':identity+'.'+m[1], 'source_candidate_id':m[1], 'description':m[2].strip()} for m in matches]


def compile_issue(body):
    matches=list(re.finditer(r'^#### (F\d{2}-(?:SIMPLE|MEDIUM|HARD))\n\n(.*?)(?=^#### |^### FAMILY |^## Fixture encoding requirements)',body,flags=re.M|re.S))
    cells=[]
    for m in matches:
        identity,source=m[1],m[2].rstrip();family=int(identity[1:3]);difficulty=identity.split('-')[1]
        cell={'id':identity,**metadata(family,difficulty), 'source_issue_fragment':source}
        why=re.search(r'^Why:\n(.+?)(?=\n\n[A-Z]|\Z)',source,flags=re.M|re.S)
        cell.update(rationale=why[1].strip() if why else None,
                    rationale_provenance='verbatim #77 Why' if why else 'not supplied separately in #77; see source-verification.json')
        if family!=10:
            prompt=source.split('Prompt:\n',1)[1].split('\n\nOptions:\n',1)[0]
            choices=source.split('Options:\n',1)[1].split('\n\nGold:',1)[0]
            gold=re.search(r'^Gold: ([A-D])$',source,flags=re.M)
            if not gold:raise ValueError('ITHKUIL_GOLD_TRANSCRIPTION')
            cell.update(prompt=prompt, candidates=options_from_letters(choices,identity),gold_candidate=identity+'.'+gold[1])
        else:
            cell['prompt']=source.split('Target:\n',1)[1].split('\n\n',1)[0]
            fixed=re.search(r'Fixed predicate:\n([^\n]+)',source)
            cell['fixed_predicate']=fixed[1] if fixed else None
            steps=[]
            for sm in re.finditer(r'^Step (\d+)(?: question)?:\n(.+?)(?=\n\nStep |\n\nDeterministic result:|\n\nPass metrics:|\n\nRecord |\Z)',source,flags=re.M|re.S):
                number=int(sm[1]);segment=sm[2]; sid=identity+'.S'+str(number)
                question=segment.split('\nOptions:',1)[0]
                choice_text=segment.split('Options:',1)[1].split('\nGold:',1)[0].strip()
                if choice_text=='use the same four sentences as F01-HARD.':
                    original=next(c for c in cells if c['id']=='F01-HARD')
                    choices=[{**o,'id':sid+'.'+o['source_candidate_id']} for o in original['candidates']]
                else:
                    choices=[{'id':sid+'.'+chr(65+n),'source_candidate_id':chr(65+n),'description':x} for n,x in enumerate(choice_text.split(' / '))]
                gold_text=segment.split('Gold:',1)[1].split('\n',1)[0].strip()
                gold=[o['id'] for o in choices if o['description']==gold_text]
                if len(gold)!=1:raise ValueError('ITHKUIL_SEQUENCE_GOLD')
                steps.append({'id':sid,'sequence_id':identity,'step_number':number,'depends_on':steps[-1]['id'] if steps else None,
                              'prompt':question,'candidates':choices,'gold_candidate':gold[0],'source_gold':gold_text})
            cell['steps']=steps
            result=re.search(r'Deterministic result:\n([^\n]+)',source)
            cell['gold_answer']=result[1] if result else steps[-1]['source_gold']
            cell['gold_path']=[s['gold_candidate'] for s in steps]
        cells.append(cell)
    anchors=body.split('## Gold-anchor inventory\n\n',1)[1].split('## Difficulty contract',1)[0].rstrip()
    fixture={'version':VERSION,'source_issue':'https://github.com/Entif-AI/Bilqis/issues/77',
             'source_issue_body_sha256':hashlib.sha256(body.encode()).hexdigest(),
             'context_packet_sha256':CONTEXT_SHA256,'gold_anchor_inventory_verbatim':anchors,
             'linguistic_authorship':'human-authored #77; deterministic transcription; no model-generated linguistic fields',
             'audit_metadata_status':'source/anchor/dimension memberships are review annotations, not new gold',
             'permutation_seed':77,'cells':cells}
    validate_fixture(fixture)
    return fixture


def decisions(fixture):
    return [(c,d) for c in fixture['cells'] for d in c.get('steps',[c])]


def validate_fixture(fixture):
    expected={f'F{f:02d}-{d}' for f in range(1,13) for d in DIFFICULTIES}
    cells=fixture['cells'];ids=[c['id'] for c in cells]
    if len(ids)!=36 or set(ids)!=expected:raise ValueError('ITHKUIL_36_CELL_IDENTITIES')
    if fixture['context_packet_sha256']!=CONTEXT_SHA256:raise ValueError('ITHKUIL_CONTEXT_IDENTITY')
    for c in cells:
        if c['family']!=int(c['id'][1:3]) or c['difficulty']!=c['id'].split('-')[1]:raise ValueError('ITHKUIL_CELL_METADATA')
        if not c['source_locators'] or not c['gold_anchor_ids']:raise ValueError('ITHKUIL_SOURCE_LOCATORS')
        if c['family']==10:
            n={'SIMPLE':2,'MEDIUM':3,'HARD':4}[c['difficulty']]
            if len(c['steps'])!=n:raise ValueError('ITHKUIL_SEQUENCE_TOPOLOGY')
            for k,s in enumerate(c['steps'],1):
                if (s['id'],s['sequence_id'],s['step_number'],s['depends_on'])!=(c['id']+'.S'+str(k),c['id'],k,c['id']+'.S'+str(k-1) if k>1 else None):raise ValueError('ITHKUIL_SEQUENCE_TOPOLOGY')
    atomic=decisions(fixture)
    if len(atomic)!=42 or len({d['id'] for _,d in atomic})!=42:raise ValueError('ITHKUIL_42_ATOMIC_IDENTITIES')
    for _,d in atomic:
        ids=[o['id'] for o in d['candidates']];descriptions=[o['description'] for o in d['candidates']]
        if len(ids)!=4 or len(set(ids))!=4 or len(set(descriptions))!=4 or ids.count(d['gold_candidate'])!=1 or not d['prompt']:raise ValueError('ITHKUIL_UNIQUE_GOLD_OPTIONS')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--issue',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();fixture=compile_issue(a.issue.read_text())
    if a.output.exists():raise ValueError('Preserve existing fixture; choose a new epoch/output')
    a.output.write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n')
    print('36 canonical cells; 42 atomic decisions; issue transcription frozen')


if __name__=='__main__':main()
