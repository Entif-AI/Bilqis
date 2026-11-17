from contextlib import contextmanager
from dataclasses import replace

from bilqis_mlx.errors import BilqisError

import pytest

from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import (
    compile_executable_factory_release, compile_successor_profile_release,
)
from bilqis_mlx.factory.execution import CapabilityProfile, CurriculumProfile, GradeProfile
from bilqis_mlx.factory.profile_expansion import verify_profile_expansion
from bilqis_mlx.factory.tests.executable_release.support import (
    ReleaseTestSupport, _boolean_answers,
)
from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_boolean_course
from bilqis_mlx.curriculum import BOOLEAN_OPERATORS


@contextmanager
def rejects(reason):
    with pytest.raises(BilqisError) as failure:
        yield
    assert failure.value.context['reason'] == reason


def successor(predecessor, profile, registry, answers, graph):
    return compile_successor_profile_release(
        predecessor, profile, registry, answers, source_root=None, graph=graph,
        verification_seed=17)


class TestProfileExpansion(ReleaseTestSupport):
    def test_invalid_input_is_a_catalogued_error(self):
        with rejects('FACTORY_PROFILE_EXPANSION_RELEASE_REQUIRED'):
            verify_profile_expansion(None, None)

    def test_z_added_capability_and_narrowing(self):
        reduced = compile_executable_factory_release(
            self.curriculum, self.bindings,
            CurriculumProfile('z-reduced', (GradeProfile('Z', ('Z.C0', 'Z.C1')),)),
            self.registry, self.answers, source_root=None, graph=self.graph,
            verification_seed=17)
        full = successor(reduced, CurriculumProfile.full(), self.registry, self.answers, self.graph)
        proof = verify_profile_expansion(reduced, full)
        assert proof.added_capabilities == ('Z.C2', 'Z.C3', 'Z.C4', 'Z.C5')
        assert len(proof.profile_sha256) == len(proof.transition_sha256) == 64
        assert proof == verify_profile_expansion(reduced, full)
        narrowed = successor(full, reduced.profile, self.registry, self.answers, self.graph)
        with rejects('FACTORY_PROFILE_EXPANSION_NARROW_CAPABILITIES'):
            verify_profile_expansion(full, narrowed)

    def test_b_provider_and_answer_domains_widen(self):
        course, registry = _synthetic_boolean_course()
        curriculum, bindings = from_legacy_course(course)
        graph = {'tokens': ['fixture.padding', 'cogal.value.false', 'cogal.value.true',
                            *(f'cogal.operator.{v}' for v in BOOLEAN_OPERATORS)]}
        profile = CurriculumProfile('reduced', (GradeProfile('B',
            enabled_capabilities=('B.AND', 'B.IFF', 'B.COMPOSITE', 'B.IDBOOLOPS'),
            capabilities=(CapabilityProfile('B.COMPOSITE', (('operators', ('AND', 'IFF')),)),
                          CapabilityProfile('B.IDBOOLOPS', (('operators', ('AND', 'IFF')),),
                                            (('boolean_operator', ('AND', 'IFF')),))),),))
        reduced = compile_executable_factory_release(curriculum, bindings, profile, registry,
            _boolean_answers(), source_root=None, graph=graph, verification_seed=17)
        full = successor(reduced, CurriculumProfile.full(), registry, _boolean_answers(), graph)
        assert verify_profile_expansion(reduced, full).added_capabilities
        scope_only = CurriculumProfile('scope-only', (GradeProfile('B', capabilities=(
            CapabilityProfile('B.COMPOSITE', (('operators', ('AND', 'IFF')),)),
        )),))
        narrowed_scope = successor(full, scope_only, registry, _boolean_answers(), graph)
        with rejects('FACTORY_PROFILE_EXPANSION_NARROW_DIMENSION'):
            verify_profile_expansion(full, narrowed_scope)
        answers_only = CurriculumProfile('answers-only', (GradeProfile('B', capabilities=(
            CapabilityProfile('B.IDBOOLOPS', (('operators', ('AND', 'IFF')),),
                              (('boolean_operator', ('AND', 'IFF')),)),
        )),))
        scope_for_answers = CurriculumProfile('scope-for-answers', (GradeProfile('B', capabilities=(
            CapabilityProfile('B.IDBOOLOPS', (('operators', ('AND', 'IFF')),)),
        )),))
        previous_answers = successor(full, scope_for_answers, registry, _boolean_answers(), graph)
        narrowed_answers = successor(previous_answers, answers_only, registry, _boolean_answers(), graph)
        with rejects('FACTORY_PROFILE_EXPANSION_NARROW_ANSWER'):
            verify_profile_expansion(previous_answers, narrowed_answers)
        narrowed = successor(full, profile, registry, _boolean_answers(), graph)
        with rejects('FACTORY_PROFILE_EXPANSION_NARROW_CAPABILITIES'):
            verify_profile_expansion(full, narrowed)

    def test_reject_changed_graph_and_wrong_parent(self):
        initial = self.compile()
        changed_graph = {**self.graph, 'extra': 'changed'}
        changed = successor(initial, CurriculumProfile.full(), self.registry, self.answers, changed_graph)
        with rejects('FACTORY_PROFILE_EXPANSION_GEOMETRY_DRIFT'):
            verify_profile_expansion(initial, changed)
        third = successor(changed, CurriculumProfile.full(), self.registry, self.answers, changed_graph)
        with pytest.raises(ValueError):
            verify_profile_expansion(initial, third)

    def test_reject_forged_delta(self):
        initial = self.compile()
        next_release = successor(initial, CurriculumProfile.full(), self.registry,
                                 self.answers, self.graph)
        forged = replace(next_release, transition=replace(
            next_release.transition, added_capabilities=('Z.C99',)))
        forged = replace(forged, release_sha256=forged.expected_digest())
        with rejects('FACTORY_PROFILE_EXPANSION_TRANSITION_DRIFT'):
            verify_profile_expansion(initial, forged)
