"""Real-owner planning and signed fixture inputs for the C06 Studio witness."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.curriculum.scheduler import start_new
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.atlas_frontier import PlannerBudget, _build_snapshot
from bilqis_mlx.factory.atlas_frontier_closure import resolve_frontier_closure
from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_validation import has_unrequested_ready, current_obligations
from bilqis_mlx.factory.atlas_frontier_selection import ranked_frontier_target, select_frontier_delta_for_projection
from bilqis_mlx.factory.atlas_frontier_selection_validation import TargetDeltaProjection, catalog_digest, obligation_signature
from bilqis_mlx.factory.candidate_frontier import load_candidate_frontier
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.factory.skos_curriculum import LearnedFrontier, SOURCE_FAMILY_ADAPTERS, compile_semantic_curriculum
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import _rights
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_salience import derive_salience, verify_salience_inputs
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.salience_contracts import ActionKind, AttentionOption, AuthoritySnapshot, Metric
from bilqis_mlx.learning.salience_history import SalienceHistory
from bilqis_mlx.learning.salience_teacher import AttentionFrontier
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.tests.test_atlas_salience import _CONTEXT, _fact, _policy, _signed
from bilqis_mlx.learning.tests.test_salience_history import _window_policy
from bilqis_mlx.runtime.accepted_priority_visit import select_accepted_priority_visit
from bilqis_mlx.runtime.accepted_teacher_custody import _c03_projection
from bilqis_mlx.runtime.priority_qualification import PriorityPlanningInput
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import adaptation, selection_teacher
from bilqis_mlx.semantics.domains import contract_digest


def _current_candidate_frontier(root, output):
    """Build A08 into disposable custody before loading its provenance-bound view."""
    builder = root / 'lib/ithkuil/src/build_curriculum_frontier.py'
    subprocess.run(
        [sys.executable, str(builder)], check=True, capture_output=True, text=True,
        env={**os.environ, 'BILQIS_CURRICULUM_FRONTIER_OUT': str(output)},
    )
    return load_candidate_frontier(
        output, root / 'lib/ithkuil/_data/csv',
        expected_builder_sha256=hashlib.sha256(builder.read_bytes()).hexdigest())


def planning(selection, factory, run_dir):
    """Run A08/A09 owners; fixture rights are planning inputs only."""
    root = Path.cwd()
    frontier = _current_candidate_frontier(root, Path(run_dir) / 'candidate-frontier')
    learned = LearnedFrontier(selection.release_sha256)
    candidate = compile_semantic_curriculum(selection, SOURCE_FAMILY_ADAPTERS, learned)
    source_frontier, policy = _rights()
    factory.admission.verify(factory.release)
    snapshot = _build_snapshot(candidate, source_frontier, policy, budget=PlannerBudget(9, 16, 1000),
        candidate_frontier_sha256=frontier.release_sha256,
        admitted_release_sha256=factory.release.release_sha256,
        admission_receipt_sha256=contract_digest(factory.admission))
    closure = resolve_frontier_closure(snapshot, candidate.census)
    chosen = projection = None
    if has_unrequested_ready(closure, (), current_obligations(closure)):
        semantic, rows = ranked_frontier_target(snapshot, closure)
        capabilities, introduced = candidate_realizations.project_realized_target(semantic, factory.release)
        draft = TargetDeltaProjection(semantic, obligation_signature(rows), factory.release.release_sha256,
            factory.release.semantic_catalog_sha256, capabilities, introduced,
            catalog_digest(factory.release.semantic_catalog + introduced), '0' * 64)
        projection = replace(draft, projection_sha256=draft.expected_digest())
        chosen = select_frontier_delta_for_projection(snapshot, closure, factory.release, projection)
    progress = plan_frontier_progress(snapshot, closure, chosen,
        current_release=factory.release if chosen is not None else None, selected_projection=projection)
    return PriorityPlanningInput(progress, closure, chosen, projection)


def select(run_dir, source_context, parent, offer, plan, registry):
    """Use the C03 bootstrap and selector with signed fixture evidence."""
    legacy, adaptation_record = {'teacher': selection_teacher()}, adaptation()
    projection = _c03_projection(parent, legacy_receipt=legacy, adaptation=adaptation_record,
                                  prior_region='fixture-legacy-region')
    epoch = restore_teacher_lineage(projection.teacher_state)
    cap = offer.capability_id
    context = replace(_CONTEXT, semantic_release=offer.release_sha256,
        generation_digest=offer.generation_binding, capability_id=cap,
        source_family_id=offer.source_family_id, source_binding_digest=offer.source_binding_digest,
        teacher_epoch_digest=contract_digest(epoch))
    snapshot = AuthoritySnapshot((context,), 100, registry)
    policy = _signed(replace(_policy(), semantic_release=context.semantic_release,
                             source_family_ids=(context.source_family_id,)))
    facts = (_fact(Metric.DECLARED_IMPACT, 2, policy, context=context),
             _fact(Metric.BLOCKED_COUNT, 0, policy, context=context))
    evidence = derive_salience(verify_salience_inputs(facts, policy, snapshot, context))
    option = _signed(AttentionOption('c06-teaching', context, evidence.basis.digest(),
        ActionKind.TEACHING, 80, True, True, True, True, 0, False, False,
        'fixture:salience-owner', '0' * 128))
    frontier = AttentionFrontier((option,), ((option.stable_id, evidence),), snapshot)
    window_policy = _signed(replace(_window_policy(policy), semantic_release=context.semantic_release))
    history = SalienceHistory(window_policy, ())
    program = schedule_program_from_executable_release(source_context.release)
    # start_new activates the admitted program's full grade roster; its first
    # queue starts in the first grade. Priority selection checks active grades.
    school = start_new(program, Checkpoint(candidate_identity_digest(parent.retained_state),
                                           'bundles/fixture', 0, True))
    grades = tuple(grade.id for grade in program.grades
                   if any(item.id == cap for item in grade.capabilities))
    if len(grades) != 1 or grades[0] not in school.active_grades:
        raise AssertionError('fixture capability is not in one active admitted grade')
    lawful_frontier = SimpleNamespace(
        ready_capability_ids=(cap,),
        _planning_generation=offer._planning_generation,
    )
    with patch(
            'bilqis_mlx.runtime.lawful_teaching_frontier.'
            'require_bound_lawful_teaching_frontier',
            return_value=lawful_frontier), patch(
            'bilqis_mlx.runtime.lawful_teaching_frontier.'
            'require_current_lawful_teaching_frontier',
            return_value=lawful_frontier):
        return select_accepted_priority_visit(
            run_dir, source_context, frontier, history, plan,
            ((option.stable_id, offer),), historical_teacher_policy, school,
            random.Random(379), Settings(), program=program, now=100,
            lawful_frontier=lawful_frontier,
            legacy_receipt=legacy, adaptation=adaptation_record,
            prior_region='fixture-legacy-region')
