"""Prefrozen token-only cue baseline; no oracle, evaluator, or learned weights."""
from collections import defaultdict
import torch
from .decision_features import control, token_manifest
from .decision_navigation import candidate_tokens, oracle_trace, state_tokens
from .semantics import sid

VERSION='decision-explicit-cue-baseline-0.1.0'
TOKENS=token_manifest()['tokens']


def cue_choice(state,candidates):
    """Copy only explicit availability, binding, orientation and update cues."""
    mode=TOKENS[state[1]].rsplit(':',1)[-1]
    reserved={'ambiguous':'clarify','missing':'insufficient','unsupported':'abstain','outside':'other'}.get(mode)
    if reserved:
        return next(i for i,c in enumerate(candidates) if c[1]==TOKENS.index(control(reserved)))
    kind=TOKENS[state[2]].rsplit(':',1)[-1]
    if kind=='bind':
        match=lambda c: c[1]==state[2] and c[2:]==state[-2:]
    elif kind=='orient':
        query=TOKENS.index(sid('query'))
        suffix=state[len(state)-1-state[::-1].index(query):]
        match=lambda c: c[1]==state[2] and c[c.index(query):]==suffix
    elif kind in ('add','remove'):
        match=lambda c: c[1]==state[2] and c[2:]==state[-8:]
    else:
        return None
    return next((i for i,c in enumerate(candidates) if match(c)),None)


class CueBaseline(torch.nn.Module):
    """Fits the scorer interface solely to reuse the independent rollout grader."""
    def forward(self,state_ids,state_lengths,candidate_ids,candidate_lengths,candidate_mask):
        scores=torch.zeros(candidate_mask.shape)
        for i in range(len(state_ids)):
            state=state_ids[i,:int(state_lengths[i])].tolist()
            candidates=[candidate_ids[i,j,:int(length)].tolist() for j,length in enumerate(candidate_lengths[i]) if candidate_mask[i,j]]
            chosen=cue_choice(state,candidates)
            if chosen is None:
                chosen=next(j for j,c in enumerate(candidates) if c[1]==TOKENS.index(control('abstain')))
            scores[i,chosen]=1.
        return scores.masked_fill(~candidate_mask,float('-inf'))


def audit(episodes):
    counts=defaultdict(lambda:{'steps':0,'copyable':0,'copy_correct':0})
    for e in episodes:
        rows,_=oracle_trace(e)
        for row in rows:
            p=row['panel']; candidates=p['candidates']
            chosen=cue_choice(state_tokens(row['state']),[candidate_tokens(c) for c in candidates])
            count=counts[e['split']+'/'+p['focus_kind']]
            count['steps']+=1
            if chosen is not None:
                count['copyable']+=1; count['copy_correct']+=candidates[chosen]['candidate_id']==row['gold_id']
    return {'version':VERSION,'inputs':'exact student token tensors only; no gold, fixture IDs, or evaluator in baseline inference',
            'classification':{'bind':'explicit entity instruction; copy alignment, not inferred binding',
                'orient':'explicit grounded query roles; canonical role alignment, not discovering a relationship',
                'add/remove':'explicit fact update; copy alignment followed by validator',
                'reserved':'availability marker directly selects reserved action',
                'read':'compute evidence truth for selected relation; result is not copied by this baseline',
                'fold':'apply four-valued logical operator to observed operands; result is not copied by this baseline'},
            'oracle_state_transition_counts':dict(counts),
            'limits':'Instruction-following accuracy is not independently learned reasoning. This baseline abstains when copying cannot determine a choice; it is not a complete rule solver.'}
