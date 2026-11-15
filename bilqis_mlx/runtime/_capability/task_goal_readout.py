"""B10 route decisions for bounded C04 TaskGoal holes."""
from __future__ import annotations

from dataclasses import replace

from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, DecisionKind, DecisionSpec, ExecutionMode, ModelOutput,
)
from bilqis_mlx.learning.atlas_readout.plan import ROUTE_MODALITY
from bilqis_mlx.semantics.frame_schema import SourceSpan
from bilqis_mlx.learning.atlas_readout.decoder.prediction import issued_output
from bilqis_mlx.runtime.atlas_model import BamfCompiledBatch, forward_bamf
from bilqis_mlx.runtime.cognitive_solver import NeuralProposal, NeuralRequest
from bilqis_mlx.semantics.cognitive_dag import DAGNode, TaskGoal
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid
from .factory_task_authority import (
    FactoryTaskAuthority, bind_factory_task_compiled_batch,
)
from .refinement_request import refinement_request_disposition


def _operator_id(node: DAGNode) -> str:
    return f"route.{node.node_id}.operator"


def _operand_id(node: DAGNode, index: int) -> str:
    return f"route.{node.node_id}.operand.{index}"


def task_goal_route_decisions(goal: TaskGoal) -> tuple[DecisionSpec, ...]:
    """Lower only declared DAG holes into bounded B10 decisions."""
    if type(goal) is not TaskGoal:
        _invalid("BAMF_C04_TASK_GOAL_ROUTE_INPUT_INVALID")
    result = []
    prior = ()
    for node in goal.expression_or_holes.nodes:
        if node.operator_id is None:
            operator_id = _operator_id(node)
            result.append(DecisionSpec(
                operator_id, None, 0, DecisionKind.OPERATOR,
                node.candidate_operator_ids, prior,
            ))
            prior = (operator_id,)
        for index, (fixed, candidates) in enumerate(zip(
                node.operands, node.candidate_operand_refs)):
            if fixed is not None:
                continue
            decision_id = _operand_id(node, index)
            result.append(DecisionSpec(
                decision_id, None, index, DecisionKind.OPERAND,
                tuple(ref.identity for ref in candidates), prior,
            ))
            prior = (decision_id,)
    return tuple(result)


def augment_answer_plan_for_task_goal(
    plan: AnswerPlan, goal: TaskGoal,
) -> AnswerPlan:
    """Place route selection before the ordinary source-owned answer plan."""
    if type(plan) is not AnswerPlan or type(goal) is not TaskGoal:
        _invalid("BAMF_C04_TASK_GOAL_PLAN_INPUT_INVALID")
    request = refinement_request_disposition(goal)
    route = task_goal_route_decisions(goal)
    if not route:
        return replace(plan, refinement_request=request)
    route_ids = tuple(item.decision_id for item in route)
    if len(route) + len(plan.decisions) > plan.maximum_decisions:
        _invalid("BAMF_C04_TASK_GOAL_ROUTE_BUDGET_EXCEEDED")
    ordinary = tuple(replace(
        decision,
        depends_on=tuple(dict.fromkeys((*route_ids, *decision.depends_on))),
    ) for decision in plan.decisions)
    return replace(
        plan, decisions=(*route, *ordinary), refinement_request=request)


def task_goal_route_plan(goal: TaskGoal, compiled_batch, snapshot, generation_binding):
    """Build a route-only B10 plan over the exact compiled source prefix."""
    route = task_goal_route_decisions(goal)
    if not route:
        _invalid("BAMF_C04_TASK_GOAL_ROUTE_REQUIRED")
    compiled = compiled_batch.compiled.compiled.rows[0]
    return AnswerPlan(
        ROUTE_MODALITY, len(compiled.positions), route, None, snapshot,
        SourceSpan(0, 0), generation_binding,
        refinement_request=refinement_request_disposition(goal),
    )


def task_goal_training_targets(goal: TaskGoal, resolved: TaskGoal):
    """Project one source-resolved goal onto the exact B10 route decisions."""
    if (type(goal) is not TaskGoal or type(resolved) is not TaskGoal
            or goal.goal_id != resolved.goal_id
            or goal.semantic_release != resolved.semantic_release
            or goal.scope != resolved.scope):
        _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
    route = task_goal_route_decisions(goal)
    original = {node.node_id: node for node in goal.expression_or_holes.nodes}
    solved = {node.node_id: node for node in resolved.expression_or_holes.nodes}
    if set(original) != set(solved) or not route:
        _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
    values = {}
    for node_id, node in original.items():
        target = solved[node_id]
        if node.operator_id is None:
            if (target.operator_id not in node.candidate_operator_ids
                    or target.candidate_operator_ids):
                _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
            values[_operator_id(node)] = target.operator_id
        elif target.operator_id != node.operator_id:
            _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
        for index, (fixed, candidates) in enumerate(zip(
                node.operands, node.candidate_operand_refs)):
            resolved_operand = target.operands[index]
            if fixed is None:
                identities = tuple(ref.identity for ref in candidates)
                if (resolved_operand is None
                        or resolved_operand.identity not in identities):
                    _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
                values[_operand_id(node, index)] = resolved_operand.identity
            elif resolved_operand != fixed:
                _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
    if set(values) != {item.decision_id for item in route}:
        _invalid("BAMF_C04_TASK_GOAL_TRAINING_TARGET_INVALID")
    from bilqis_mlx.learning.atlas_readout import DecisionOutput
    return (
        tuple(DecisionOutput(item.decision_id, values[item.decision_id])
              for item in route),
        {item.decision_id: True for item in route},
    )


def proposal_from_task_goal_output(
    goal: TaskGoal,
    request: NeuralRequest,
    output: ModelOutput,
) -> NeuralProposal:
    """Turn one live B10 route choice into the exact C04 proposal it selected."""
    if (type(goal) is not TaskGoal or type(request) is not NeuralRequest
            or type(output) is not ModelOutput or not issued_output(output)):
        _invalid("BAMF_C04_TASK_GOAL_ROUTE_OUTPUT_INVALID")
    route = task_goal_route_decisions(goal)
    route_ids = {item.decision_id for item in route}
    committed = {item.decision_id: item.value for item in output.committed
                 if item.decision_id in route_ids}
    if set(committed) != route_ids:
        _invalid("BAMF_C04_TASK_GOAL_ROUTE_INCOMPLETE")
    nodes = []
    for node in goal.expression_or_holes.nodes:
        if node.operator_id is not None and all(
                operand is not None for operand in node.operands):
            nodes.append(node)
            continue
        operator = (node.operator_id if node.operator_id is not None
                    else committed[_operator_id(node)])
        operands = list(node.operands)
        for index, (fixed, candidates) in enumerate(zip(
                node.operands, node.candidate_operand_refs)):
            if fixed is not None:
                continue
            selected = committed[_operand_id(node, index)]
            matches = tuple(ref for ref in candidates if ref.identity == selected)
            if len(matches) != 1:
                _invalid("BAMF_C04_TASK_GOAL_OPERAND_SELECTION_INVALID")
            operands[index] = matches[0]
        nodes.append(replace(
            node, operator_id=operator, operands=tuple(operands),
            candidate_operator_ids=(), candidate_operand_refs=(), constraints=(),
        ))
    proposal_goal = replace(
        goal,
        expression_or_holes=replace(goal.expression_or_holes, nodes=tuple(nodes)),
    )
    receipt = contract_digest({
        "schema": "bilqis.mlx.b10-task-goal-route/v1",
        "goal": contract_digest(goal),
        "request": request,
        "plan": output.plan,
        "route": tuple((key, committed[key]) for key in sorted(committed)),
    })
    return NeuralProposal(
        proposal_goal, request.source_binding_digest,
        request.generation_digest, request.unresolved_signature, receipt,
    )


def b11_task_goal_proposer(
    parameters,
    compiled_batch: BamfCompiledBatch,
    plan: AnswerPlan,
    authority: FactoryTaskAuthority,
    *,
    accepted_cache=None,
    execution_binding=None,
):
    """Close C04's neural seam over one exact Factory-owned B11 source row."""
    if (type(compiled_batch) is not BamfCompiledBatch
            or type(plan) is not AnswerPlan
            or type(authority) is not FactoryTaskAuthority):
        _invalid("BAMF_C04_B11_TASK_PROPOSER_AUTHORITY_REQUIRED")
    authority.__post_init__()
    compiled_batch.__post_init__()
    training = compiled_batch.training_authority
    training_mismatch = (
        (training is None) != (authority.training_authority_sha256 is None)
        or (training is not None and (
            training.digest != authority.training_authority_sha256
            or training.generation_binding != authority.generation_binding
            or training.delivery_capability != authority.capability_id
            or training.source_row_id != authority.source_row_id)))
    if (training_mismatch or plan.generation_binding != authority.generation_binding):
        _invalid("BAMF_C04_B11_TASK_PROPOSER_CUSTODY_MISMATCH")
    expected_refinement_request = refinement_request_disposition(authority.goal)
    if plan.refinement_request != expected_refinement_request:
        _invalid("BAMF_C04_B11_TASK_REFINEMENT_REQUEST_MISMATCH")
    if plan.route_only:
        if plan.decisions != task_goal_route_decisions(authority.goal):
            _invalid("BAMF_C04_B11_TASK_ROUTE_PLAN_MISMATCH")
        routed_plan = plan
    else:
        routed_plan = augment_answer_plan_for_task_goal(plan, authority.goal)
    owned_batch = bind_factory_task_compiled_batch(compiled_batch, authority)

    def propose(request: NeuralRequest):
        if (type(request) is not NeuralRequest
                or request.goal_id != authority.goal.goal_id
                or request.source_binding_digest != authority.source_binding_sha256
                or request.generation_digest != authority.generation_binding
                or request.allowed_operator_ids != authority.goal.allowed_operator_ids):
            _invalid("BAMF_C04_B11_TASK_REQUEST_MISMATCH")
        output = forward_bamf(
            parameters, owned_batch, routed_plan,
            ExecutionMode.INFERENCE, accepted_cache,
            execution_binding=execution_binding,
        )
        return proposal_from_task_goal_output(authority.goal, request, output)

    return propose


__all__ = (
    "augment_answer_plan_for_task_goal",
    "b11_task_goal_proposer",
    "proposal_from_task_goal_output",
    "task_goal_route_plan",
    "task_goal_route_decisions",
    "task_goal_training_targets",
)
