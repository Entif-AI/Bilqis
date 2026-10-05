"""Seed-level paired analysis; supplied engineering examples are not SYS evidence."""
from __future__ import annotations
import argparse,itertools,json,math
from pathlib import Path
import numpy as np
from scipy.stats import t

def paired(a:list[float],b:list[float])->dict:
    if len(a)!=len(b) or len(a)<2 or len(a)>20:raise ValueError("2..20 complete paired seeds required")
    if not all(math.isfinite(x) for x in a+b):raise ValueError("nonfinite outcome")
    d=np.asarray(a)-np.asarray(b);n=len(d);mu=float(d.mean());se=float(d.std(ddof=1)/math.sqrt(n));crit=float(t.ppf(.975,n-1))
    observed=abs(mu);extreme=0
    for signs in itertools.product((-1,1),repeat=n):
        if abs(float((d*np.array(signs)).mean()))>=observed-1e-14:extreme+=1
    return {"paired_seeds":n,"mean_difference":mu,"t_interval_95":[mu-crit*se,mu+crit*se],"exact_two_sided_signflip_p":extreme/(2**n),"assumptions":"t interval: independent seed differences, approximate normality; exact signflip: exchangeability under symmetric sharp null; cases are not independent seed replicates"}

def restricted_exposure(steps:list[int|None],cap:int)->dict:
    if cap<=0 or not steps or any(s is not None and not 0<=s<=cap for s in steps):raise ValueError("exposure/cap")
    x=[cap if s is None else s for s in steps];return {"restricted_mean_exposures":sum(x)/len(x),"cap":cap,"censored_fraction":sum(s is None for s in steps)/len(x),"survivor_only_mean_prohibited":True}

def main():
    p=argparse.ArgumentParser();p.add_argument("--pairs",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();d=json.loads(a.pairs.read_text());a.out.write_text(json.dumps(paired(d["B"],d["C"]),indent=2)+"\n")
if __name__=="__main__":main()
