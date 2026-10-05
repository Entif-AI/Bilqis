"""Deterministic policy owns promotion. A language model can propose, never certify."""
from __future__ import annotations
import math
from dataclasses import dataclass,field,asdict

STAGE_NAMES=("identity","configuration","purpose-use","composition","evidence")
PREREQUISITES={0:[],1:[0],2:[0],3:[1,2],4:[0]}

def wilson_lower(correct:int,total:int,z:float=1.959963984540054)->float:
    if total<=0 or not 0<=correct<=total:raise ValueError("binomial counts")
    p=correct/total;d=1+z*z/total
    return (p+z*z/(2*total)-z*math.sqrt(p*(1-p)/total+z*z/(4*total*total)))/d

@dataclass
class TeacherState:
    promoted:list[int]=field(default_factory=list)
    tranches:dict[str,int]=field(default_factory=dict)
    last_scores:dict[str,float]=field(default_factory=dict)
    history:list[dict]=field(default_factory=list)
    held:bool=False
    reason:str="genesis"

    def choose(self,policy:str="topology")->int:
        if self.held:raise RuntimeError("TEACHER_HELD")
        remaining=[i for i in range(5) if i not in self.promoted]
        if not remaining:return 3
        if policy=="topology":eligible=[i for i in remaining if all(p in self.promoted for p in PREREQUISITES[i])]
        elif policy=="difficulty":eligible=remaining
        else:raise ValueError("unknown teacher policy")
        if not eligible:raise RuntimeError("CURRICULUM_DEADLOCK")
        # Fixed tie-breaker, then least already-exposed eligible stage.
        return min(eligible,key=lambda i:(self.tranches.get(str(i),0),i))

    def decide(self,stage:int,scores:dict[str,dict],thresholds:dict,integrity_ok:bool)->dict:
        if not integrity_ok:
            self.held=True;self.reason="INTEGRITY_FAILURE";return {"promoted":False,"reason":self.reason}
        curr=scores[str(stage)];mastery=wilson_lower(curr["correct"],curr["n"])>=thresholds["mastery_lower"]
        retention=all(wilson_lower(scores[str(i)]["correct"],scores[str(i)]["n"])>=thresholds["retention_lower"] for i in self.promoted)
        transfer=curr["transfer_correct"]/curr["transfer_n"]>=thresholds["dev_transfer_accuracy"]
        ok=mastery and retention and transfer
        if ok and stage not in self.promoted:self.promoted.append(stage);self.promoted.sort()
        self.tranches[str(stage)]=self.tranches.get(str(stage),0)+1
        self.last_scores={k:v["correct"]/v["n"] for k,v in scores.items()}
        self.reason="PROMOTED" if ok else "REMEDIATE_OR_BUDGET_LIMIT"
        decision={"stage":stage,"mastery":mastery,"retention":retention,"dev_transfer":transfer,"promoted":ok,"reason":self.reason}
        self.history.append(decision);return decision
