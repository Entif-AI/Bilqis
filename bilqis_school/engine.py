"""Durable, one-student, auto-mutating skill-tree training loop.

Thousands of lessons should not require thousands of assistant turns. A
single model+AdamW+semantic graph continues through grades. The teacher
chooses and mutates strategies based on *observed* learning outcomes; weak
or regressed lessons are practice signals, not automatic rollback triggers.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import shutil
import time
import uuid

import torch
from torch.nn import functional as F

from bilqis_active import load_active
from bilqis_development.continuation import load as load_checkpoint
from bilqis_development.continuation import save as save_checkpoint
from bilqis_development.continuation import expand
from bilqis_micro.graph import STATES
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import batch, state_hash
from bilqis_logic.kernel import digest

from .arithmetic import extend_graph
from .grades import skill_tree
from .lessons import TeacherLibrary, compose_batch, encode
from .grow import grow, compare_outputs

VERSION = "bilqis.school.auto-spiral/v1"
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "school50-continuous-v1"
STATE = "state.json"
KNOBS = {
    "old": [4, 8, 12, 16, 20],
    "preview": [0, 2, 4],
    "depth": [1, 2, 3, 4],
    "contrast": [0.0, 0.5, 1.0],
    "lr": [0.00004, 0.00008, 0.00013, 0.0002, 0.0003],
    "distill": [0.0, 0.15, 0.35, 0.65],
}
INITIAL = (
    {"old":12,"preview":2,"depth":2,"contrast":.5,"lr":.00013,"distill":.15},
    {"old":20,"preview":0,"depth":2,"contrast":1.,"lr":.00008,"distill":.65},
    {"old":8,"preview":4,"depth":3,"contrast":1.,"lr":.00020,"distill":.15},
    {"old":16,"preview":2,"depth":1,"contrast":.0,"lr":.00008,"distill":.35},
)
MAX_STRATEGIES = 512
GRADES = skill_tree()


def _read(path):
    return json.loads(Path(path).read_text())


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    with temporary.open("x") as stream:
        json.dump(obj,stream,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary,path)


def _policy_key(policy):
    return hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()[:12]


def _stats():
    return {"trials":0,"reward_sum":0.0,"reward_ema":0.0,"latest":None}


def _teacher():
    return {"strategies":{_policy_key(p):dict(p) for p in INITIAL},
            "global_stats":{_policy_key(p):_stats() for p in INITIAL},
            "grade_stats":{}, "events":0, "mutations":0}


def mutate(teacher, rng):
    """Change ONE permitted knob, record it once, reuse across later grades."""
    if len(teacher["strategies"])>=MAX_STRATEGIES:return None
    viable=[(key,info) for key,info in teacher["global_stats"].items()
            if info["trials"]]
    base=teacher["strategies"][max(viable,key=lambda v:v[1]["reward_ema"])[0]] if viable \
         else rng.choice(list(teacher["strategies"].values()))
    for _ in range(24):
        variant=dict(base)
        field=rng.choice(list(KNOBS))
        candidates=[v for v in KNOBS[field] if v!=variant[field]]
        variant[field]=rng.choice(candidates)
        if variant["old"]+variant["preview"]>24:continue
        identity=_policy_key(variant)
        if identity not in teacher["strategies"]:
            teacher["strategies"][identity]=variant
            teacher["global_stats"][identity]=_stats()
            teacher["mutations"]+=1
            return identity
    return None


def pick(teacher, grade, rng):
    if teacher["events"] and teacher["events"] % 3 == 0:
        mutate(teacher,rng)
    local=teacher["grade_stats"].get(str(grade),{})
    total=teacher["events"]+1
    def rank(item):
        key, policy=item
        info=local.get(key) or teacher["global_stats"][key]
        if info["trials"]==0:
            return 10 + rng.random()
        exploitation=info["reward_sum"]/info["trials"]
        exploration=0.6*math.sqrt(math.log(total+2)/(1+info["trials"]))
        return exploitation+exploration
    return max(teacher["strategies"].items(),key=rank)


def observe(teacher, grade, policy_key, reward):
    if not math.isfinite(reward):
        raise ValueError("NONFINITE_TEACHER_REWARD")
    for entry in (teacher["global_stats"][policy_key],
                  teacher["grade_stats"].setdefault(str(grade),{}).setdefault(policy_key,_stats())):
        entry["trials"]+=1
        entry["reward_sum"]+=reward
        entry["reward_ema"]=reward if entry["latest"] is None else (
            .8*entry["reward_ema"]+.2*reward)
        entry["latest"]=reward
    teacher["events"]+=1


def _checkpoint(run_dir, model, optimizer, graph, metadata):
    destination=run_dir/("student-"+str(metadata["step"])+"-"+uuid.uuid4().hex[:12]+".pt")
    save_checkpoint(destination,model,optimizer,graph,metadata)
    return destination.name, _sha(destination)


def _validate(checkpoint, state):
    path=Path(checkpoint)
    if not path.is_file() or _sha(path)!=state["checkpoint_sha256"]:
        raise ValueError("RUNNER_CURRENT_CHECKPOINT_MISSING_OR_CHANGED")
    model,optimizer,payload=load_checkpoint(path)
    if (state_hash(model)!=state["model_sha256"] or
        optimizer_receipt(optimizer)["steps"]!=[state["optimizer_step"]] or
        len(payload["graph"]["tokens"])!=state["vocab"] or
        digest(payload["graph"])!=state["graph_sha256"]):
        raise ValueError("RUNNER_CANNOT_RECONSTRUCT_CONTINUOUS_STUDENT")
    return model,optimizer,payload


def initialize(out=RUN):
    out=Path(out)
    if out.exists():
        raise FileExistsError("CONTINUING_RUN_ALREADY_INITIALIZED")
    model,optimizer,prior,source=load_active()
    original_step=optimizer_receipt(optimizer)["steps"]
    if original_step != [13848]:
        raise ValueError("WRONG_ACTIVE_LEARNER_FOR_INITIAL_SCHOOL_MIGRATION")
    graph=extend_graph(prior["graph"])
    migration=expand(model,optimizer,prior["graph"],graph)
    if optimizer_receipt(optimizer)["steps"] != original_step:
        raise ValueError("VOCAB_EXPANSION_RESET_OPTIMIZER")
    out.mkdir(parents=True,exist_ok=False)
    name,checksum=_checkpoint(out,model,optimizer,graph,{
        "epoch":VERSION,"step":13848,"parent_checkpoint_sha256":source["checkpoint_sha256"],
        "vocabulary_expansion":migration,
        "no_model_reset":True,"no_optimizer_reset":True,
    })
    state={"version":VERSION,"checkpoint":name,"checkpoint_sha256":checksum,
           "model_sha256":state_hash(model),
           "optimizer_step":13848,"vocab":len(graph["tokens"]),
           "graph_sha256":digest(graph),
           "parent_checkpoint_sha256":source["checkpoint_sha256"],
           "next_grade":1,"spiral_pass":1,"completed_grades":0,
           "completed_updates":0,"teacher":_teacher(),
           "blocked_grade_ids":[g.id for g in GRADES if not g.ready],
           "grade_ledger":[],"last_results":{},
           "no_retention_rollback":True,
           "last_run_wall_seconds":0.0}
    _atomic_json(out/STATE,state)
    return state


def grow_active_school(out=RUN, *, factor=4, layers=6):
    """Grow one stopped student at a durable grade boundary, never restart."""
    out=Path(out)
    state=_read(out/STATE)
    before,optimizer,payload=_validate(out/state["checkpoint"],state)
    if before.config.width*factor>768 or before.config.layers>=layers:
        raise ValueError("MODEL_GROWTH_REQUIRES_NEW_UNREPEATED_CAPACITY")
    larger,larger_optimizer,receipt=grow(before,optimizer,factor=factor,layers=layers)
    lib=TeacherLibrary()
    representative=[]
    for grade in (1,4,8,10,14,17,19,22):
        policy={"old":12,"preview":2,"depth":2,"contrast":1.,
                "lr":.00013,"distill":.35}
        rows,_=compose_batch(lib,grade,policy,payload["graph"],random.Random(grade))
        representative.append(batch([encode(r,payload["graph"]) for r in rows]))
    parity=compare_outputs(before,larger,representative)
    if optimizer_receipt(larger_optimizer)["steps"]!=[state["optimizer_step"]]:
        raise ValueError("MODEL_GROWTH_RESET_ADAMW")
    previous_name,previous_sha=state["checkpoint"],state["checkpoint_sha256"]
    next_name,next_sha=_checkpoint(out,larger,larger_optimizer,payload["graph"],{
        "epoch":VERSION,"step":state["optimizer_step"],
        "migrated_from":previous_name,"migrated_from_sha256":previous_sha,
        "function_preservation_proof":parity,"expansion":receipt})
    # Reopen the *actual* new binary and prove identity before updating the
    # active pointer. Interrupted growth leaves the old pointer authoritative.
    proof={"checkpoint_sha256":next_sha,"optimizer_step":state["optimizer_step"],
           "vocab":state["vocab"],"graph_sha256":state["graph_sha256"],
           "model_sha256":state_hash(larger)}
    reloaded,restored,_=_validate(out/next_name,proof)
    if state_hash(reloaded)!=state_hash(larger):
        raise ValueError("GROWN_CHECKPOINT_READBACK_CHANGED_WEIGHTS")
    state["checkpoint"],state["checkpoint_sha256"]=next_name,next_sha
    state["model_sha256"]=proof["model_sha256"]
    state.setdefault("architecture_history",[]).append({
        "from":previous_name,"from_sha256":previous_sha,
        "to":next_name,"to_sha256":next_sha,
        "step":state["optimizer_step"],"proof":parity,"parameters":receipt})
    _atomic_json(out/STATE,state)
    return {"status":"FUNCTION_PRESERVING_GROWTH_VERIFIED",
            "student_optimizer_step":state["optimizer_step"],
            "old_parameters":receipt["old_parameters"],
            "new_parameters":receipt["new_parameters"],
            "representation_parity":parity,
            "active_checkpoint":str(out/next_name),
            "active_checkpoint_sha256":next_sha}


def _device(model, optimizer, name):
    if name=="mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS_NOT_AVAILABLE")
    if name not in ("cpu","mps"):raise ValueError("UNSUPPORTED_LEARNER_DEVICE")
    model.to(name)
    for data in optimizer.state.values():
        for key,val in data.items():
            if isinstance(val,torch.Tensor):
                data[key]=val.to(name)
    return torch.device(name)


def _scores(model, lib, graph, grade, seed, *, count=24, device="cpu"):
    rng=random.Random(seed)
    rows=[]
    for i in range(count):
        packet=lib.one(grade,rng,depth=2 if i%3 else 3,
                       prefer_composition=i%2==0,
                       truth=bool(i%2) if grade>=19 else None)
        rows.append(packet[i%len(packet)] if isinstance(packet,list) else packet)
    old_training=model.training
    model.eval()
    with torch.no_grad():
        ids,lengths=batch([encode(row,graph) for row in rows],device=device)
        logits=model(ids,lengths)
        predictions=logits.argmax(-1).cpu().tolist()
        correct=sum(STATES[i]==row["gold"] for i,row in zip(predictions,rows))
    if old_training:model.train()
    return correct/count


def _train(model, optimizer, reference, graph, rows, counts, policy, device):
    lengths=[encode(row,graph) for row in rows]
    labels=torch.tensor([STATES.index(r["gold"]) for r in rows],
                        device=device,dtype=torch.long)
    inp,n=batch(lengths,device=device)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    logits=model(inp,n)
    cross=F.cross_entropy(logits,labels)
    retained=counts["old"]
    first_old=counts["current"]
    old_slice=slice(first_old,first_old+retained)
    memory=torch.zeros((),device=device)
    if retained and policy["distill"]>0:
        with torch.no_grad():
            reference.eval()
            old_logits=reference(inp[old_slice],n[old_slice])
        memory=F.kl_div(
            F.log_softmax(logits[old_slice]/1.5,dim=-1),
            F.softmax(old_logits/1.5,dim=-1),
            reduction="batchmean")*(1.5**2)
    loss=cross + policy["distill"]*memory
    if not bool(torch.isfinite(loss)):
        raise ValueError("NONFINITE_CONTINUOUS_LEARNER_LOSS")
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
    optimizer.step()
    return float(loss.detach().cpu())


def _progress_line(progress):
    repeat = progress["repeat_delta"]
    rolling = progress["rolling_repeat_delta"]
    repeat_text = "n/a" if repeat is None else f"{repeat*100:+.1f}pp"
    rolling_text = "n/a" if rolling is None else f"{rolling*100:+.1f}pp"
    patience = ""
    if progress["patience_minutes"] is not None:
        patience = (
            f" | no-gain {progress['minutes_since_measurable_progress']:.1f}"
            f"/{progress['patience_minutes']:.1f}m"
        )
    return (
        f"[{progress['elapsed_minutes']:6.1f}m] pass {progress['pass']} "
        f"{progress['grade']} step {progress['step']} | probe "
        f"{progress['accuracy_before']*100:.1f}%->{progress['accuracy_after']*100:.1f}% "
        f"({progress['immediate_delta']*100:+.1f}pp) | vs prior {repeat_text} "
        f"| rolling{progress['progress_window']} {rolling_text} "
        f"| old avg {progress['old_mean_delta']*100:+.1f}pp "
        f"| reward {progress['reward']:+.4f} "
        f"| teacher {progress['teacher_strategies']}/{MAX_STRATEGIES} strategies/"
        f"{progress['teacher_mutations']} mutations{patience}"
    )


def _stagnation_stop(*, elapsed_seconds, seconds_since_progress,
                     repeat_comparisons, progress_window, patience_minutes):
    if patience_minutes is None or repeat_comparisons < progress_window:
        return False
    patience_seconds=patience_minutes*60
    return (elapsed_seconds >= patience_seconds and
            seconds_since_progress >= patience_seconds)


def _graceful_interrupt_handler(stop_state):
    """First SIGINT requests a durable stop; second preserves emergency abort."""
    def handle(signum, frame):
        if stop_state["requested"]:
            signal.default_int_handler(signum, frame)
        stop_state["requested"]=True
        os.write(
            2,
            b"\nInterrupt requested: finishing the current grade, "
              b"checkpointing, then stopping. Press Ctrl+C again to abort immediately.\n",
        )
    return handle


def run(out=RUN, *, max_updates=1024, max_minutes=4,
        block=32, device="cpu", strict_full50=False,
        max_run_gib=32, max_grade_visits=None,
        patience_minutes=None, progress_window=8,
        min_repeat_improvement=0.01, progress_format="json",
        stop_requested=None):
    if (max_updates < 1 or max_minutes <= 0 or block < 1 or block > 256
        or not 1<=max_run_gib<=500
        or (max_grade_visits is not None and max_grade_visits < 1)
        or (patience_minutes is not None and patience_minutes <= 0)
        or progress_window < 1 or min_repeat_improvement < 0
        or progress_format not in ("json","human")):
        raise ValueError("INVALID_BOUNDED_TRAINING_REQUEST")
    out=Path(out)
    if strict_full50 and any(not g.ready for g in GRADES):
        raise ValueError("FULL_50_NOT_COMPILED: GRAMMAR_AND_LEXICON_NEED_VALIDATED_GENERATORS")
    if not (out/STATE).exists():
        initialize(out)
    state=_read(out/STATE)
    if state["version"] != VERSION:
        raise ValueError("CANNOT_SILENTLY_RESUME_DIFFERENT_SCHOOL_ENGINE")
    model,optimizer,payload=_validate(out/state["checkpoint"],state)
    gpu=_device(model,optimizer,device)
    lib=TeacherLibrary()
    start=time.monotonic()
    consumed=0
    visits_this_call=0
    repeat_deltas=[]
    immediate_deltas=[]
    old_mean_deltas=[]
    last_measurable_progress=start
    paused_for_storage=False
    stopped_for_stagnation=False
    paused_for_visit_limit=False
    stopped_for_interrupt=False
    while (consumed < max_updates and time.monotonic()-start < max_minutes*60
           and (max_grade_visits is None or visits_this_call < max_grade_visits)):
        if stop_requested is not None and stop_requested():
            stopped_for_interrupt=True
            break
        checkpoints = list(out.glob("student-*.pt"))
        storage_bytes = sum(p.stat().st_size for p in checkpoints)
        # Compute bound before beginning the next grade: a new checkpoint
        # may require roughly current-model payload bytes, and a little
        # headroom for atomic writes, file indexes and the run journal.
        recent_bytes=(out/state["checkpoint"]).stat().st_size
        if storage_bytes+recent_bytes*2 >= max_run_gib*1024**3:
            paused_for_storage=True
            break
        grade=state["next_grade"]
        if grade > 50:
            grade=1
            state["next_grade"]=1
            state["spiral_pass"]+=1
        if not lib.ready(grade):
            # An unimplemented skill is NEVER taught using synthetic/fake
            # oracle labels, and it never forces a learner reset or rollback.
            state["next_grade"]+=1
            if state["next_grade"]>50:
                state["next_grade"]=1
                state["spiral_pass"]+=1
            continue
        if shutil.disk_usage(out).free < 512*1024*1024:
            raise OSError("SCHOOL_STORAGE_RESERVE_512MiB_REACHED")
        seed=(state["spiral_pass"]*1000003 + grade*9973 +
              state["completed_grades"]*3)
        rng=random.Random(seed)
        key,policy=pick(state["teacher"],grade,rng)
        steps=min(block,max_updates-consumed)
        if steps < 1:break
        grade_id=f"G{grade:02d}"
        prior_visit=state["last_results"].get(grade_id)
        probe_seed=170003+grade*617
        before=_scores(model,lib,payload["graph"],grade,probe_seed,device=device)
        guards=[g for g in (1,10,13,16,17,19) if g<grade and lib.ready(g)]
        before_old={str(g):_scores(model,lib,payload["graph"],g,170003+g*617,
                                  count=12,device=device) for g in guards}
        anchor=copy.deepcopy(model).eval()
        for p in anchor.parameters():p.requires_grad_(False)
        for group in optimizer.param_groups:group["lr"]=policy["lr"]
        tallies={"current":0,"old":0,"preview":0}
        losses=[]
        for local_step in range(steps):
            rows,counts=compose_batch(lib,grade,policy,payload["graph"],rng)
            if counts["current"] <= 0 or len(rows)!=32:
                raise ValueError("NO_COGNITIVE_GROWTH_SAMPLES")
            loss=_train(model,optimizer,anchor,payload["graph"],rows,counts,policy,gpu)
            losses.append(loss)
            for name,value in counts.items():tallies[name]+=value
        after=_scores(model,lib,payload["graph"],grade,probe_seed,device=device)
        after_old={str(g):_scores(model,lib,payload["graph"],g,170003+g*617,
                                 count=12,device=device) for g in guards}
        old_delta=sum(after_old[k]-before_old[k] for k in before_old)
        old_mean_delta=old_delta/max(1,len(before_old))
        immediate_delta=after-before
        reward=2*immediate_delta+.6*old_mean_delta
        repeat_delta=(None if prior_visit is None
                      else after-prior_visit["after"])
        if repeat_delta is not None:
            repeat_deltas.append(repeat_delta)
        immediate_deltas.append(immediate_delta)
        old_mean_deltas.append(old_mean_delta)
        recent_repeat=repeat_deltas[-progress_window:]
        rolling_repeat_delta=(sum(recent_repeat)/len(recent_repeat)
                              if recent_repeat else None)
        now=time.monotonic()
        if (len(recent_repeat) >= progress_window and
            rolling_repeat_delta >= min_repeat_improvement):
            last_measurable_progress=now
        observe(state["teacher"],grade,key,reward)
        consumed+=steps
        visits_this_call+=1
        state["completed_updates"]+=steps
        state["completed_grades"]+=1
        state["optimizer_step"]+=steps
        if optimizer_receipt(optimizer)["steps"]!=[state["optimizer_step"]]:
            raise ValueError("ADAMW_CONTINUITY_BROKEN")
        record={"spiral_pass":state["spiral_pass"],"grade":grade_id,
                "strategy_id":key,"strategy":policy,
                "before":before,"after":after,"old_before":before_old,
                "old_after":after_old,"reward":round(reward,6),
                "repeat_delta":None if repeat_delta is None else round(repeat_delta,6),
                "old_mean_delta":round(old_mean_delta,6),
                "updates":steps,"loss_first":losses[0],"loss_last":losses[-1],
                "teacher_mutations":state["teacher"]["mutations"],
                "row_exposures":tallies,
                "optimizer_step":state["optimizer_step"]}
        state["grade_ledger"].append(record)
        state["last_results"][f"G{grade:02d}"]=record
        state["next_grade"]=grade+1
        state["model_sha256"]=state_hash(model)
        name,checksum=_checkpoint(out,model,optimizer,payload["graph"],{
            "epoch":VERSION,"step":state["optimizer_step"],
            "last_grade":grade,"spiral_pass":state["spiral_pass"],
            "learning_strategy":policy,"parent_checkpoint_sha256":state["checkpoint_sha256"],
            "one_continuing_student":True})
        state["checkpoint"],state["checkpoint_sha256"]=name,checksum
        state["last_run_wall_seconds"]=round(time.monotonic()-start,3)
        _atomic_json(out/STATE,state)
        elapsed=time.monotonic()-start
        since_progress=elapsed-(last_measurable_progress-start)
        progress={"pass":state["spiral_pass"],"grade":grade_id,
                  "step":state["optimizer_step"],"updates":steps,
                  "strategy":key,
                  "teacher_strategies":len(state["teacher"]["strategies"]),
                  "teacher_mutations":state["teacher"]["mutations"],
                  "accuracy_before":before,"accuracy_after":after,
                  "immediate_delta":immediate_delta,
                  "repeat_delta":repeat_delta,
                  "rolling_repeat_delta":rolling_repeat_delta,
                  "progress_window":progress_window,
                  "reward":round(reward,4),
                  "old_mean_delta":old_mean_delta,
                  "old_delta_sum":old_delta,
                  "elapsed_minutes":elapsed/60,
                  "minutes_since_measurable_progress":since_progress/60,
                  "patience_minutes":patience_minutes,
                  "min_repeat_improvement":min_repeat_improvement}
        if progress_format=="human":
            print(_progress_line(progress),flush=True)
        else:
            print(json.dumps(progress,sort_keys=True),flush=True)
        if stop_requested is not None and stop_requested():
            stopped_for_interrupt=True
            break
        if _stagnation_stop(
                elapsed_seconds=elapsed,
                seconds_since_progress=since_progress,
                repeat_comparisons=len(repeat_deltas),
                progress_window=progress_window,
                patience_minutes=patience_minutes):
            stopped_for_stagnation=True
            break
    if (max_grade_visits is not None and
        visits_this_call >= max_grade_visits and
        not stopped_for_stagnation and not paused_for_storage):
        paused_for_visit_limit=True
    status=("PAUSED_FOR_STORAGE_QUOTA" if paused_for_storage else
            "STOPPED_BY_GRACEFUL_INTERRUPT" if stopped_for_interrupt else
            "STOPPED_NO_MEASURABLE_REPEAT_IMPROVEMENT" if stopped_for_stagnation else
            "PAUSED_AT_REQUESTED_GRADE_VISIT_LIMIT" if paused_for_visit_limit else
            "PAUSED_AT_DURABLE_GRADE_BOUNDARY")
    recent_repeat=repeat_deltas[-progress_window:]
    mean_repeat=(sum(repeat_deltas)/len(repeat_deltas)
                 if repeat_deltas else None)
    mean_immediate=(sum(immediate_deltas)/len(immediate_deltas)
                    if immediate_deltas else None)
    mean_old=(sum(old_mean_deltas)/len(old_mean_deltas)
              if old_mean_deltas else None)
    return {"status":status,
            "checkpoint_quota_gib":max_run_gib,"completed_this_call":consumed,
            "grade_visits_this_call":visits_this_call,
            "repeat_comparisons_this_call":len(repeat_deltas),
            "mean_repeat_delta_this_call":mean_repeat,
            "repeat_improved_this_call":sum(x>0 for x in repeat_deltas),
            "repeat_unchanged_this_call":sum(x==0 for x in repeat_deltas),
            "repeat_regressed_this_call":sum(x<0 for x in repeat_deltas),
            "mean_immediate_delta_this_call":mean_immediate,
            "mean_old_delta_this_call":mean_old,
            "rolling_repeat_delta":(sum(recent_repeat)/len(recent_repeat)
                                    if recent_repeat else None),
            "progress_window":progress_window,
            "min_repeat_improvement":min_repeat_improvement,
            "patience_minutes":patience_minutes,
            "total_school_updates":state["completed_updates"],
            "live_optimizer_step":state["optimizer_step"],
            "completed_grades":state["completed_grades"],
            "spiral_pass":state["spiral_pass"],
            "next_grade":state["next_grade"],
            "teacher_strategies":len(state["teacher"]["strategies"]),
            "teacher_strategy_capacity":MAX_STRATEGIES,
            "observed_teacher_mutations":state["teacher"]["mutations"],
            "compiled_grades":sum(g.ready for g in GRADES),
            "blocked_grades":state["blocked_grade_ids"],
            "latest_checkpoint":str(out/state["checkpoint"])}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",type=Path,default=RUN)
    parser.add_argument("--max-updates",type=int,default=1024)
    parser.add_argument("--minutes",type=float,default=4)
    parser.add_argument("--block",type=int,default=32)
    parser.add_argument("--max-run-gib",type=float,default=32,
                        help="Pause safely before generated checkpoint history exceeds this many GiB.")
    parser.add_argument("--grade-visits",type=int,default=None,
                        help="Pause at a durable boundary after this many completed grade visits.")
    parser.add_argument("--patience-minutes",type=float,default=None,
                        help="Stop if repeated-grade trend shows no measurable improvement for this long.")
    parser.add_argument("--progress-window",type=int,default=8,
                        help="Repeated-grade comparisons used for the rolling improvement trend.")
    parser.add_argument("--min-repeat-improvement",type=float,default=0.01,
                        help="Rolling repeated-grade accuracy gain that resets the patience clock (0.01 = 1 pp).")
    parser.add_argument("--progress-format",choices=("human","json"),default="json",
                        help="Per-grade live progress output.")
    parser.add_argument("--graceful-interrupt",action="store_true",
                        help="First Ctrl+C finishes the current grade and checkpoints before stopping; second Ctrl+C aborts immediately.")
    parser.add_argument("--device",choices=("cpu","mps"),default="cpu")
    parser.add_argument("--grow",action="store_true",
                        help="Function-preserving capacity migration, keeping trained state.")
    parser.add_argument("--require-full50",action="store_true")
    parser.add_argument("--status",action="store_true")
    arguments=parser.parse_args()
    if arguments.grow:
        print(json.dumps(grow_active_school(arguments.run_dir),indent=2,sort_keys=True))
    elif arguments.status:
        result=_read(arguments.run_dir/STATE)
        print(json.dumps({k:v for k,v in result.items()
                          if k not in ("teacher","grade_ledger","last_results")},
                         indent=2,sort_keys=True))
    else:
        stop_state={"requested":False}
        previous_handler=None
        if arguments.graceful_interrupt:
            previous_handler=signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT,_graceful_interrupt_handler(stop_state))
        try:
            result=run(arguments.run_dir,max_updates=arguments.max_updates,
                       max_minutes=arguments.minutes,block=arguments.block,
                       device=arguments.device,strict_full50=arguments.require_full50,
                       max_run_gib=arguments.max_run_gib,
                       max_grade_visits=arguments.grade_visits,
                       patience_minutes=arguments.patience_minutes,
                       progress_window=arguments.progress_window,
                       min_repeat_improvement=arguments.min_repeat_improvement,
                       progress_format=arguments.progress_format,
                       stop_requested=(lambda: stop_state["requested"])
                                      if arguments.graceful_interrupt else None)
        finally:
            if previous_handler is not None:
                signal.signal(signal.SIGINT,previous_handler)
        print(json.dumps(result,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
