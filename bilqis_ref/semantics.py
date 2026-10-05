"""Finite worlds and a two-bit evidence algebra; all identifiers are local ABI IDs."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib, json, random

ABI = "bilqis-finite-world-0.1.0"
LABELS = ((1,0),(0,1),(0,0),(1,1))
LABEL_NAMES = ("TRUE","FALSE","UNKNOWN","CONFLICT")
OPS = ("EQ","SIZE","SAME","CONNECTED","APL","PUR","EVID","NOT","AND","OR")

@dataclass(frozen=True)
class Entity:
    id: int
    color: int
    intended: int
    actual: int

@dataclass(frozen=True)
class World:
    entities: tuple[Entity,...]
    edges: tuple[tuple[int,int],...]
    reports: tuple[tuple[int,int],...]

    def obj(self) -> dict:
        return {"entities":[asdict(e) for e in self.entities],
                "edges":[list(e) for e in self.edges],
                "reports":[list(r) for r in self.reports]}

    @classmethod
    def from_obj(cls, d: dict) -> World:
        if set(d) != {"entities","edges","reports"}: raise ValueError("world keys")
        w=cls(tuple(Entity(**e) for e in d["entities"]),
              tuple(tuple(e) for e in d["edges"]),tuple(tuple(r) for r in d["reports"]))
        validate_world(w);return w

def canonical(x: Any) -> bytes:
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()

def digest(x: Any) -> str:return hashlib.sha256(canonical(x)).hexdigest()

def exact_int(x: Any, low: int, high: int) -> bool:
    return type(x) is int and low<=x<=high

def validate_world(w: World) -> None:
    n=len(w.entities)
    if not 2<=n<=6 or any(type(e.id) is not int for e in w.entities) or tuple(e.id for e in w.entities)!=tuple(range(n)):
        raise ValueError("entity identity/order")
    if any(not exact_int(v,0,2) for e in w.entities for v in (e.color,e.intended,e.actual)):
        raise ValueError("entity field outside finite domain")
    if tuple(sorted(set(w.edges))) != w.edges: raise ValueError("edge canonicality")
    if any(len(e)!=2 or not all(exact_int(x,0,n-1) for x in e) or e[0]>=e[1] for e in w.edges):
        raise ValueError("edge domain")
    if len(w.reports)!=3 or any(len(r)!=2 or not all(exact_int(x,0,1) for x in r) for r in w.reports):
        raise ValueError("report evidence bits")

def validate_query(q: dict, n: int, depth: int=0) -> None:
    if depth>4 or not isinstance(q,dict):raise ValueError("query nesting/type")
    op=q.get("op")
    shapes={"EQ":{"op","a","b"},"SIZE":{"op","group","value"},
            "SAME":{"op","group"},"CONNECTED":{"op","group"},
            "APL":{"op","a","value"},"PUR":{"op","a","value"},
            "EVID":{"op","value"},"NOT":{"op","args"},"AND":{"op","args"},"OR":{"op","args"}}
    if op not in shapes or set(q)!=shapes[op]: raise ValueError("query operator/keys")
    for k in ("a","b"):
        if k in q and not exact_int(q[k],0,n-1):raise ValueError("query entity reference")
    if "group" in q:
        g=q["group"]
        if not isinstance(g,list) or not g or any(not exact_int(x,0,n-1) for x in g) or g!=sorted(set(g)):
            raise ValueError("group must be canonical nonempty subset")
    if "value" in q and not exact_int(q["value"],0,6 if op=="SIZE" else 2):raise ValueError("query value")
    if "args" in q:
        if not isinstance(q["args"],list) or len(q["args"]) != (1 if op=="NOT" else 2):raise ValueError("arity")
        for c in q["args"]:validate_query(c,n,depth+1)

def truth(b: bool) -> tuple[int,int]:return (int(b),int(not b))

def oracle(w: World,q: dict) -> tuple[int,int]:
    """Reference A: recursive AST evaluation, BFS connectivity."""
    op=q["op"]
    if op=="NOT":
        t,f=oracle(w,q["args"][0]);return f,t
    if op in ("AND","OR"):
        t,f=oracle(w,q["args"][0]);u,v=oracle(w,q["args"][1])
        return (t&u,f|v) if op=="AND" else (t|u,f&v)
    if op=="EQ":return truth(q["a"]==q["b"])
    if op=="SIZE":return truth(len(q["group"])==q["value"])
    if op=="SAME":return truth(len({w.entities[i].color for i in q["group"]})==1)
    if op in ("APL","PUR"):
        e=w.entities[q["a"]];return truth((e.actual if op=="APL" else e.intended)==q["value"])
    if op=="EVID":return w.reports[q["value"]]
    if op=="CONNECTED":
        group=set(q["group"]);seen={min(group)};front=list(seen)
        while front:
            a=front.pop()
            for u,v in w.edges:
                b=v if a==u else u if a==v else None
                if b in group and b not in seen:seen.add(b);front.append(b)
        return truth(seen==group)
    raise ValueError(op)

def independent_oracle(w: World,q: dict) -> tuple[int,int]:
    """Reference B: iterative postorder, Boolean reachability matrix; no A calls."""
    n=len(w.entities);reach=[[i==j for j in range(n)] for i in range(n)]
    colors={e.id:e.color for e in w.entities};uses={e.id:e.actual for e in w.entities};purposes={e.id:e.intended for e in w.entities}
    todo=[(q,False)];vals=[]
    while todo:
        x,done=todo.pop();op=x["op"]
        if op in ("NOT","AND","OR") and not done:
            todo.append((x,True));todo.extend((c,False) for c in reversed(x["args"]));continue
        if op=="NOT":a=vals.pop();vals.append((a[1],a[0]));continue
        if op in ("AND","OR"):
            b=vals.pop();a=vals.pop()
            if op=="AND":vals.append((int(bool(a[0]) and bool(b[0])),int(bool(a[1]) or bool(b[1]))))
            else:vals.append((int(bool(a[0]) or bool(b[0])),int(bool(a[1]) and bool(b[1]))))
            continue
        if op=="EVID":vals.append(tuple(w.reports[x["value"]]));continue
        if op=="EQ":z=x["a"]==x["b"]
        elif op=="SIZE":z=sum(1 for _ in x["group"])==x["value"]
        elif op=="SAME":z=all(colors[a]==colors[b] for a in x["group"] for b in x["group"])
        elif op=="APL":z=uses[x["a"]]==x["value"]
        elif op=="PUR":z=purposes[x["a"]]==x["value"]
        elif op=="CONNECTED":
            g=x["group"];r=[row[:] for row in reach]
            for a,b in w.edges:
                if a in g and b in g:r[a][b]=r[b][a]=True
            for k in g:
                for a in g:
                    for b in g:r[a][b]=r[a][b] or (r[a][k] and r[k][b])
            z=all(r[a][b] for a in g for b in g)
        else:raise ValueError(op)
        vals.append((int(z),int(not z)))
    if len(vals)!=1:raise ValueError("postorder stack")
    return vals[0]

def make_world(r: random.Random, family: str) -> World:
    n=6;entities=tuple(Entity(i,r.randrange(3),r.randrange(3),r.randrange(3)) for i in range(n))
    if family=="iid":edges=[(i,j) for i in range(n) for j in range(i+1,n) if r.random()<0.35]
    elif family=="cycle":
        order=r.sample(range(n),n);edges=sorted({tuple(sorted((order[i],order[(i+1)%n]))) for i in range(n)})
        if r.random()<0.5:edges.pop(r.randrange(len(edges)))
    elif family=="blocks":
        order=r.sample(range(n),n);cut=r.randrange(2,n-1);groups=[order[:cut],order[cut:]]
        edges=sorted({tuple(sorted((a,b))) for g in groups for a in g for b in g if a!=b})
    else:raise ValueError("unknown generator family")
    reports=tuple((r.randrange(2),r.randrange(2)) for _ in range(3))
    w=World(entities,tuple(edges),reports);validate_world(w);return w

def atom(r: random.Random, stage: int) -> dict:
    if stage==0:return {"op":"EQ","a":r.randrange(6),"b":r.randrange(6)}
    if stage==1:
        op=r.choice(("SIZE","SAME","CONNECTED"));g=sorted(r.sample(range(6),r.randrange(1,7)));q={"op":op,"group":g}
        if op=="SIZE":q["value"]=r.randrange(1,7)
        return q
    if stage==2:return {"op":r.choice(("APL","PUR")),"a":r.randrange(6),"value":r.randrange(3)}
    if stage==4:return {"op":"EVID","value":r.randrange(3)}
    return atom(r,r.choice((0,1,2)))

def make_query(r: random.Random,stage: int, depth: int=2) -> dict:
    if stage in (0,1,2):return atom(r,stage)
    if depth==0:return atom(r,4 if stage==4 else r.choice((0,1,2)))
    op=r.choice(("NOT","AND","OR"));return {"op":op,"args":[make_query(r,stage,depth-1) for _ in range(1 if op=="NOT" else 2)]}

def example(seed: int, family: str, stage: int, index: int, split: str="TRAIN",depth: int=2) -> dict:
    """Balanced by answer class with bounded rejection; nonce IDs never encode answers."""
    if split not in ("TRAIN","DEV","SEALED"):raise ValueError("split")
    target=LABELS[index%(4 if stage==4 else 2)]
    for attempt in range(10000):
        s=int(hashlib.sha256(f"{ABI}|{seed}|{family}|{stage}|{index}|{split}|{attempt}".encode()).hexdigest()[:16],16)
        r=random.Random(s);w=make_world(r,family);q=make_query(r,stage,depth);validate_query(q,6)
        a=oracle(w,q);b=independent_oracle(w,q)
        if a!=b:raise RuntimeError("ORACLE_DISAGREEMENT: quarantine, never accept")
        if a==target:
            semantic={"abi":ABI,"world":w.obj(),"query":q}
            return {"semantic":semantic,"label":LABEL_NAMES[LABELS.index(a)],"semantic_sha256":digest(semantic),
                    "provenance":{"seed":seed,"family":family,"stage":stage,"index":index,"split":split,"attempt":attempt,
                                  "oracle_a":"recursive-bfs-v1","oracle_b":"postorder-closure-v1","agreed":True}}
    raise RuntimeError("GENERATOR_REJECTION_LIMIT")


def counterfactual_witness(w:World,q:dict)->dict|None:
    """Return one legal world-only intervention that changes the answer, or None.
    Exhausts one-field changes, individual edges and report bits; it does not certify
    that a function is constant under every multi-field intervention when None.
    """
    import copy
    before=oracle(w,q);base=w.obj()
    for i in range(len(w.entities)):
        for field in ("color","intended","actual"):
            for value in range(3):
                if value==base["entities"][i][field]:continue
                obj=copy.deepcopy(base);obj["entities"][i][field]=value;after=oracle(World.from_obj(obj),q)
                if after!=before:return {"kind":"entity_field","entity":i,"field":field,"value":value,"after":list(after)}
    for i in range(len(w.entities)):
        for j in range(i+1,len(w.entities)):
            obj=copy.deepcopy(base);edges={tuple(e) for e in obj["edges"]}
            if (i,j) in edges:edges.remove((i,j))
            else:edges.add((i,j))
            obj["edges"]=[list(e) for e in sorted(edges)];after=oracle(World.from_obj(obj),q)
            if after!=before:return {"kind":"edge_toggle","edge":[i,j],"after":list(after)}
    for i in range(3):
        for j in range(2):
            obj=copy.deepcopy(base);obj["reports"][i][j]^=1;after=oracle(World.from_obj(obj),q)
            if after!=before:return {"kind":"report_bit","report":i,"bit":j,"after":list(after)}
    return None


def apply_counterfactual(w:World,witness:dict)->World:
    import copy
    obj=copy.deepcopy(w.obj());kind=witness["kind"]
    if kind=="entity_field":obj["entities"][witness["entity"]][witness["field"]]=witness["value"]
    elif kind=="edge_toggle":
        edges={tuple(x) for x in obj["edges"]};e=tuple(witness["edge"])
        if e in edges:edges.remove(e)
        else:edges.add(e)
        obj["edges"]=[list(e) for e in sorted(edges)]
    elif kind=="report_bit":obj["reports"][witness["report"]][witness["bit"]]^=1
    else:raise ValueError("counterfactual kind")
    return World.from_obj(obj)
