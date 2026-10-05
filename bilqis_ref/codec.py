"""Lossless finite-world codecs; not surface Ithkuil and not an ordinary-English parser."""
from __future__ import annotations
from .semantics import World, validate_query, ABI
import copy,random

# The full 512-row embedding allocation is frozen even when a stage uses fewer IDs.
SPECIAL=["<PAD>","<BOS>","TRUE","FALSE","UNKNOWN","CONFLICT","<EOS>"]
BASE=["W","O","G","R","Q","END","(",")","EQ","SIZE","SAME","CONNECTED","APL","PUR","EVID","NOT","AND","OR"]
WORDS=["there","are","entities","entity","has","color","intended","purpose","current","use","links","reports","question","end",".",",",":","is","same","as","size","of","group","uniform","connected","used","for","evidence","not","both","either"]
TOKENS=list(dict.fromkeys(SPECIAL+BASE+WORDS+[str(i) for i in range(7)]))
TOKENS += [f"<RESERVED_{i}>" for i in range(len(TOKENS),512)]
TOKEN_TO_ID={t:i for i,t in enumerate(TOKENS)}
CNL_OP={"EQ":["is","same","as"],"SIZE":["size","of","group"],"SAME":["uniform","color","group"],"CONNECTED":["connected","group"],"APL":["used","for"],"PUR":["intended","for"],"EVID":["evidence"],"NOT":["not"],"AND":["both"],"OR":["either"]}

class Cursor:
    def __init__(self,t:list[str]):self.t=t;self.i=0
    def pop(self)->str:
        if self.i>=len(self.t):raise ValueError("truncated codec")
        x=self.t[self.i];self.i+=1;return x
    def expect(self,*x:str)->None:
        for expected in x:
            if self.pop()!=expected:raise ValueError(f"expected {expected}")
    def number(self)->int:
        s=self.pop()
        if s not in [str(i) for i in range(7)]:raise ValueError("number domain")
        return int(s)

def query_tokens(q:dict,cnl:bool)->list[str]:
    op=q["op"];t=["("]+(CNL_OP[op] if cnl else [op])
    if op in ("NOT","AND","OR"):
        for x in q["args"]:t+=query_tokens(x,cnl)
    elif op=="EQ":t += [str(q["a"]),str(q["b"])]
    elif op in ("APL","PUR"):t += [str(q["a"]),str(q["value"])]
    elif op=="EVID":t += [str(q["value"])]
    else:
        t += [str(len(q["group"]))]+list(map(str,q["group"]))
        if op=="SIZE":t += [str(q["value"])]
    return t+[ ")" ]

def parse_query(c:Cursor,cnl:bool)->dict:
    c.expect("(")
    if cnl:
        matches=[op for op,words in CNL_OP.items() if c.t[c.i:c.i+len(words)]==words]
        if len(matches)!=1:raise ValueError("CNL operator prefix")
        op=matches[0];c.i+=len(CNL_OP[op])
    else:op=c.pop()
    q={"op":op}
    if op in ("NOT","AND","OR"):q["args"]=[parse_query(c,cnl) for _ in range(1 if op=="NOT" else 2)]
    elif op=="EQ":q.update(a=c.number(),b=c.number())
    elif op in ("APL","PUR"):q.update(a=c.number(),value=c.number())
    elif op=="EVID":q["value"]=c.number()
    elif op in ("SIZE","SAME","CONNECTED"):
        count=c.number();q["group"]=[c.number() for _ in range(count)]
        if op=="SIZE":q["value"]=c.number()
    else:raise ValueError("operator")
    c.expect(")");return q

def render(semantic:dict, representation:str="bilqis", reverse_entities:bool=False)->list[str]:
    if semantic["abi"]!=ABI:raise ValueError("ABI")
    if representation not in ("bilqis","cnl","isomorphic","mixed"):raise ValueError("representation")
    if set(semantic)!={"abi","world","query"}:raise ValueError("semantic keys: labels/provenance forbidden")
    World.from_obj(semantic["world"]);validate_query(semantic["query"],len(semantic["world"]["entities"]))
    if representation=="mixed":
        semantic=copy.deepcopy(semantic)
        for e in semantic["world"]["entities"]:
            x,y=e["color"],e["intended"];e["color"]=(x+y)%3;e["intended"]=(x+2*y)%3
    cnl=representation=="cnl";w=World.from_obj(semantic["world"]);q=semantic["query"];validate_query(q,len(w.entities))
    t=["<BOS>"]+(["there","are",str(len(w.entities)),"entities","."] if cnl else ["W",str(len(w.entities))])
    for e in (reversed(w.entities) if reverse_entities else w.entities):
        t += (["entity",str(e.id),"has","color",str(e.color),",","intended","purpose",str(e.intended),",","current","use",str(e.actual),"."] if cnl else ["O",str(e.id),str(e.color),str(e.intended),str(e.actual)])
    t += (["links","are"] if cnl else ["G"])+[str(len(w.edges)//7),str(len(w.edges)%7)]
    for a,b in w.edges:t += [str(a),str(b)]
    t += ([".","reports","are"] if cnl else ["R"])
    for a,b in w.reports:t += [str(a),str(b)]
    t += ([".","question",":"] if cnl else ["Q"])+query_tokens(q,cnl)
    t += ["end"] if cnl else ["END"]
    return [TOKENS[PERMUTATION[TOKEN_TO_ID[x]]] for x in t] if representation=="isomorphic" else t

def parse(tokens:list[str],representation:str="bilqis")->dict:
    if representation not in ("bilqis","cnl","isomorphic","mixed"):raise ValueError("representation")
    if representation=="isomorphic":
        try:tokens=[TOKENS[INVERSE_PERMUTATION[TOKEN_TO_ID[x]]] for x in tokens]
        except KeyError as exc:raise ValueError("TOKEN_ABI_OOV") from exc
    cnl=representation=="cnl";c=Cursor(tokens);c.expect("<BOS>")
    if cnl:c.expect("there","are");n=c.number();c.expect("entities",".")
    else:c.expect("W");n=c.number()
    entities=[]
    for _ in range(n):
        if cnl:
            c.expect("entity");i=c.number();c.expect("has","color");color=c.number();c.expect(",","intended","purpose");p=c.number();c.expect(",","current","use");a=c.number();c.expect(".")
        else:c.expect("O");i=c.number();color=c.number();p=c.number();a=c.number()
        entities.append({"id":i,"color":color,"intended":p,"actual":a})
    c.expect(*(["links","are"] if cnl else ["G"]));count=c.number()*7+c.number()
    edges=[[c.number(),c.number()] for _ in range(count)]
    c.expect(*([".","reports","are"] if cnl else ["R"]));reports=[[c.number(),c.number()] for _ in range(3)]
    c.expect(*([".","question",":"] if cnl else ["Q"]));q=parse_query(c,cnl);c.expect("end" if cnl else "END")
    if c.i!=len(c.t):raise ValueError("trailing tokens")
    if representation=="mixed":
        for e in entities:
            u,v=e["color"],e["intended"];e["color"]=(2*u-v)%3;e["intended"]=(v-u)%3
    w=World.from_obj({"entities":sorted(entities,key=lambda e:e["id"]),"edges":edges,"reports":reports});validate_query(q,n)
    return {"abi":ABI,"world":w.obj(),"query":q}

def encode(s:dict,representation:str="bilqis",reverse_entities:bool=False)->list[int]:
    t=render(s,representation,reverse_entities)
    try:return [TOKEN_TO_ID[x] for x in t]
    except KeyError as exc:raise ValueError("TOKEN_ABI_OOV") from exc

def decode(ids:list[int],representation:str="bilqis")->dict:
    if any(type(x) is not int or not 0<=x<512 for x in ids):raise ValueError("token ID")
    return parse([TOKENS[i] for i in ids],representation)

# Fixed special answer/PAD/BOS/EOS IDs; bijectively relabel all remaining symbols.
PERMUTATION=list(range(512));_symbols=list(range(len(SPECIAL),512));random.Random(73191).shuffle(_symbols)
PERMUTATION[len(SPECIAL):]=_symbols
INVERSE_PERMUTATION=[0]*512
for _i,_j in enumerate(PERMUTATION):INVERSE_PERMUTATION[_j]=_i
