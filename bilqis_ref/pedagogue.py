"""Proposal boundary and replay interface. No paid or network call occurs in the reference runner."""
from __future__ import annotations
import json,hashlib
from pathlib import Path

ALLOWED_FIELDS={"request_sha256","stage","seed_offset","focus","rationale"}
FOCI={"contrast","rehearsal","distractors","scope"}

def request(stage:int,aggregate_errors:dict,contract_sha256:str)->dict:
    # No raw sealed cases, family code, private identifiers or target answers are admitted.
    if not all(type(k) is str and type(v) is int and v>=0 for k,v in aggregate_errors.items()):raise ValueError("aggregate errors")
    return {"role":"non_authoritative_pedagogue","stage":stage,"aggregate_errors":aggregate_errors,
            "contract_sha256":contract_sha256,"allowed_output":sorted(ALLOWED_FIELDS),"prohibited":"gold answers; sealed artifacts; promotion decisions"}

def accept(proposal:dict,request_sha256:str,eligible_stages:list[int])->dict:
    if set(proposal)!=ALLOWED_FIELDS:raise ValueError("PROPOSAL_KEYS: gold labels and executable code forbidden")
    if proposal["request_sha256"]!=request_sha256:raise ValueError("PROPOSAL_REQUEST_ID")
    if type(proposal["stage"]) is not int or proposal["stage"] not in eligible_stages:raise ValueError("PROPOSAL_STAGE")
    if type(proposal["seed_offset"]) is not int or not 0<=proposal["seed_offset"]<=100000:raise ValueError("PROPOSAL_SEED")
    if proposal["focus"] not in FOCI:raise ValueError("PROPOSAL_FOCUS")
    if type(proposal["rationale"]) is not str or len(proposal["rationale"])>2000:raise ValueError("PROPOSAL_RATIONALE")
    return proposal.copy()

def replay(path:Path,expected_sha256:str,request_sha256:str,eligible:list[int])->dict:
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError("REPLAY_HASH")
    return accept(json.loads(raw),request_sha256,eligible)
