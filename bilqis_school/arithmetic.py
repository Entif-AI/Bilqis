"""Exact small-integer mathematics for the existing Boolean-answer student.

This is a real executable new domain, not an English-only exercise label.
The student's input is symbolic prefix notation; it never contains a target
answer. Independent interpreters agree before each row is accepted.
"""
from __future__ import annotations

import random

from bilqis_logic.kernel import digest
from bilqis_micro.graph import append_catalog

VERSION = "bilqis.school.math/v1"
MAX_NUMBER = 100
OPS = {
    "ADD": 2, "SUB": 2, "MUL": 2, "MOD": 2,
    "EQ": 2, "LT": 2, "LE": 2,
}


def atom(number: int):
    if not isinstance(number, int) or not 0 <= number <= MAX_NUMBER:
        raise ValueError("NUMBER_OUTSIDE_MATH_ABI")
    return {"kind":"number","value":number}


def operation(name: str, *args):
    if name not in OPS or len(args) != OPS[name]:
        raise ValueError("MATH_OPERATOR_ARITY")
    return {"kind":"op","name":name,"args":list(args)}


def evaluate(expression):
    if expression["kind"] == "number":
        return expression["value"]
    a, b = (evaluate(q) for q in expression["args"])
    name = expression["name"]
    if name == "ADD":return a+b
    if name == "SUB":return a-b
    if name == "MUL":return a*b
    if name == "MOD":return a % b if b else 0
    if name == "EQ":return a==b
    if name == "LT":return a<b
    if name == "LE":return a<=b
    raise ValueError("UNKNOWN_MATH_OPERATION")


def independent_evaluate(expression):
    stack = [(expression,False)]
    values = []
    while stack:
        node,ready=stack.pop()
        if node["kind"]=="number":
            values.append(node["value"])
            continue
        if not ready:
            stack.append((node,True))
            for child in reversed(node["args"]):
                stack.append((child,False))
            continue
        b=values.pop();a=values.pop()
        op=node["name"]
        if op=="ADD":value=sum((a,b))
        elif op=="SUB":value=a+(-b)
        elif op=="MUL":
            value=0
            for _ in range(b):value+=a
        elif op=="MOD":value=(a-(a//b)*b) if b else 0
        elif op=="EQ":value=not(a!=b)
        elif op=="LT":value=(b-a)>0
        elif op=="LE":value=(b-a)>=0
        else:raise ValueError("UNKNOWN_MATH_OPERATION")
        values.append(value)
    if len(values)!=1:raise ValueError("MALFORMED_MATH_AST")
    return values[0]


def verify(expression):
    if evaluate(expression) != independent_evaluate(expression):
        raise ValueError("MATH_INDEPENDENT_ORACLE_MISMATCH")
    return True


def row(expression, grade):
    verify(expression)
    truth = evaluate(expression)
    if type(truth) is not bool:
        raise ValueError("MATH_LESSON_NOT_BOOLEAN")
    record={"task":VERSION,"expression":expression}
    return {"id":digest(record),"input":record,"gold":"TRUE" if truth else "FALSE",
            "stage":grade-1,"family":f"math:G{grade:02d}"}


def _term(rng, grade):
    x,y,z=(rng.randint(0,9) for _ in range(3))
    if grade==19:return atom(x)
    if grade==20:
        k=rng.choice(("ADD","SUB","MUL","MOD"))
        return operation(k,atom(x),atom(y if k!="MOD" else max(1,y)))
    if grade==21:
        k=rng.choice(("ADD","MUL","SUB"))
        return operation(k,atom(x),atom(y))
    if grade==22:
        k=rng.choice(("ADD","MUL","SUB"))
        return operation("ADD",operation(k,atom(x),atom(y)),atom(z))
    raise ValueError("UNIMPLEMENTED_MATH_GRADE")


def lesson(grade: int, rng, *, correct=None, depth=1):
    if grade not in (19,20,21,22):
        raise ValueError("MATH_GRADE_NOT_IMPLEMENTED")
    if correct is None:correct=bool(rng.randrange(2))
    if grade==19:
        left=atom(rng.randint(0,99));v=evaluate(left)
        k=rng.choice(("EQ","LT","LE"))
        if k=="EQ":right=atom(v if correct else ((v+1) % 100))
        elif k=="LT":right=atom(min(100,v+1) if correct else max(0,v-1))
        else:right=atom(v if correct else max(0,v-1))
        # Cannot construct TRUE for LT(max) or FALSE for LE(0) inside ABI;
        # resample instead of changing an oracle label.
        if evaluate(operation(k,left,right)) != correct:
            return lesson(grade,rng,correct=correct,depth=depth)
        return row(operation(k,left,right),grade)
    if grade==21:
        left=_term(rng,grade)
        lhs=left["args"]
        if correct and left["name"] in ("ADD","MUL"):
            right=operation(left["name"],lhs[1],lhs[0])
        elif correct:
            right=operation("ADD",lhs[0],operation("SUB",atom(0),lhs[1]))
        else:
            right=operation("ADD",lhs[0],atom((evaluate(lhs[1])+1)%100))
        if (evaluate(left)==evaluate(right)) != correct:
            return lesson(grade,rng,correct=correct,depth=depth)
        return row(operation("EQ",left,right),grade)
    left=_term(rng,grade)
    if depth>=2 and grade==20:
        # A related change in the same small number world increases depth.
        left=operation("ADD",left,atom(rng.randint(0,3)))
    target=evaluate(left)
    delta=0 if correct else rng.choice((-2,-1,1,2))
    if not 0<=target+delta<=MAX_NUMBER:
        return lesson(grade,rng,correct=correct,depth=depth)
    test=operation("EQ",left,atom(target+delta))
    if evaluate(test)!=correct:
        return lesson(grade,rng,correct=correct,depth=depth)
    return row(test,grade)


def encode(record, token_to_id):
    if record.get("task") != VERSION:
        raise ValueError("NOT_A_SCHOOL_MATH_RECORD")
    def recur(node):
        if node["kind"]=="number":
            return [token_to_id["school.number."+str(node["value"])]]
        return [token_to_id["school.op."+node["name"]]] + [
            token for child in node["args"] for token in recur(child)]
    ids=[token_to_id["school.syntax.math"]]+recur(record["expression"])+[
        token_to_id["syntax.end"]]
    if len(ids)>96:
        raise ValueError("MATH_RECORD_CONTEXT_OVERFLOW")
    return ids


def extend_graph(graph):
    nodes = [{"id":"school.syntax.math","family":"syntax","subtype":"math-school",
              "signature":"Syntax","arity":0,"stage":19,"edges":[]}]
    for name,arity in OPS.items():
        nodes.append({"id":"school.op."+name,"family":"mathematics","subtype":name,
                      "signature":"Number*Number->Boolean" if name in ("EQ","LT","LE")
                      else "Number*Number->Number",
                      "arity":arity,"stage":19,"edges":[
                          {"kind":"prerequisite","target":"micro.compare.EQ"}]})
    for number in range(MAX_NUMBER+1):
        nodes.append({"id":"school.number."+str(number),"family":"integer",
                      "subtype":"magnitude-"+str(number),"signature":"Number",
                      "arity":0,"stage":19,"edges":[
                          {"kind":"ordinal_predecessor","target":"school.number."+str(number-1)}
                      ] if number else []})
    if "school.syntax.math" in graph["tokens"]:
        raise ValueError("NUMBER_ABI_ALREADY_EXPANDED")
    return append_catalog(graph,nodes)
