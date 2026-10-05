"""Local-only adaptive assistance events. No call is made unless an operator invokes fill."""
from __future__ import annotations
import argparse,json,hashlib,time,urllib.request,urllib.parse
from pathlib import Path
from .semantics import canonical,digest
from .pedagogue import accept

def read_event(store:Path,request_id:str,identity:str,eligible:list[int])->tuple[dict,str]:
    path=store/(request_id+".json");raw=path.read_bytes();record=json.loads(raw)
    if record["request_sha256"]!=request_id or record["model_identity_sha256"]!=identity:raise ValueError("ASSISTANCE_EVENT_IDENTITY")
    if digest(record["proposal"])!=record["proposal_sha256"]:raise ValueError("ASSISTANCE_EVENT_DIGEST")
    accept(record["proposal"],request_id,eligible);return record,hashlib.sha256(raw).hexdigest()

def fill(request_path:Path,store:Path,identity_path:Path,endpoint:str,system_prompt:Path)->Path:
    u=urllib.parse.urlparse(endpoint)
    if u.scheme!="http" or u.hostname not in ("127.0.0.1","localhost","::1") or u.path!="/v1/chat/completions":raise ValueError("LOCAL_ENDPOINT_ONLY")
    manifest=json.loads(identity_path.read_text());required={"model_id","upstream_revision","weight_manifest_sha256","engine_build","decoding"}
    if not required.issubset(manifest) or any(manifest[k] in (None,"") for k in required):raise ValueError("PIN_LOCAL_MODEL_IDENTITY_FIRST")
    req=json.loads(request_path.read_text());rid=req["request_sha256"];eligible=req["eligible_stages"]
    core={k:v for k,v in req.items() if k not in ("request_sha256","eligible_stages")}
    if digest(core)!=rid:raise ValueError("REQUEST_DIGEST")
    dest=store/(rid+".json");store.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError("append-only event already exists; inspect instead of replaying call")
    identity=hashlib.sha256(identity_path.read_bytes()).hexdigest();params=manifest["decoding"]
    body={"model":manifest["model_id"],"messages":[{"role":"system","content":system_prompt.read_text()},{"role":"user","content":json.dumps(req)}],**params}
    t0=time.perf_counter();request=urllib.request.Request(endpoint,data=canonical(body),headers={"Content-Type":"application/json"},method="POST")
    # Bypass inherited proxy settings: the recipient must remain the explicit local service.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise ValueError("LOCAL_SERVICE_REDIRECT_FORBIDDEN")
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=120) as response:raw=response.read(1000001)
    if len(raw)>1000000:raise ValueError("LOCAL_RESPONSE_TOO_LARGE")
    response=json.loads(raw);text=response["choices"][0]["message"]["content"];proposal=accept(json.loads(text),rid,eligible)
    event={"request_sha256":rid,"model_identity_sha256":identity,"proposal":proposal,"proposal_sha256":digest(proposal),"raw_response_sha256":hashlib.sha256(raw).hexdigest(),"route_ledger_id":"LOCAL-"+rid,"elapsed_seconds":time.perf_counter()-t0,"usage":response.get("usage"),"model_reported":response.get("model"),"endpoint_scope":"loopback only; trusted operator service, not attestation"}
    # Exclusive creation prevents overwriting a successful response on an accidental retry.
    with dest.open("xb") as f:f.write(canonical(event)+b"\n")
    (store/(rid+".response.json")).write_bytes(raw);return dest

def main():
    p=argparse.ArgumentParser();p.add_argument("--request",type=Path,required=True);p.add_argument("--store",type=Path,required=True);p.add_argument("--identity",type=Path,required=True);p.add_argument("--endpoint",default="http://127.0.0.1:8000/v1/chat/completions");p.add_argument("--system-prompt",type=Path,default=Path("prompts/local-pedagogue-system.txt"));a=p.parse_args();print(fill(a.request,a.store,a.identity,a.endpoint,a.system_prompt))
if __name__=="__main__":main()
