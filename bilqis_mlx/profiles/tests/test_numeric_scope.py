"""Numeric scope filtering must honor the source codec's list input contract."""
import unittest
from unittest.mock import patch

from bilqis_mlx.profiles.catalog import numeric_row_in_scope, partition_numeric_scope
from bilqis_mlx.semantics.numeric import calculate, number
from bilqis_mlx.source_adapters.numeric import decode, encode


class NumericScopeTests(unittest.TestCase):
    def test_in_scope_number_decodes_from_the_source_list(self):
        row = {"record": {"symbols": encode(number(3))}}
        self.assertTrue(numeric_row_in_scope(row, 3))
        self.assertFalse(numeric_row_in_scope(row, 2))

    def test_partition_checks_each_immutable_row_once(self):
        rows = ({"id": "inside"}, {"id": "outside"})
        with patch(
                "bilqis_mlx.profiles.catalog.numeric_row_in_scope",
                side_effect=(True, False)) as in_scope:
            active, deferred = partition_numeric_scope(rows, 3)
        self.assertEqual(active, [rows[0]])
        self.assertEqual(deferred, [rows[1]])
        self.assertEqual(in_scope.call_count, len(rows))

    def test_scope_requirement_reuses_identical_semantic_symbols(self):
        row = {"record": {"symbols": encode(calculate("ADD", number(2), number(3)))}}
        with patch("bilqis_mlx.profiles.catalog.decode", wraps=decode) as decoder:
            self.assertFalse(numeric_row_in_scope(row, 4))
            self.assertTrue(numeric_row_in_scope(row, 5))
            self.assertTrue(numeric_row_in_scope(row, 6))
        self.assertEqual(decoder.call_count, 1)


class NumericEntryProfileTests(unittest.TestCase):
    def test_canonical_numeric_scope_runs_from_four_through_ten(self):
        from bilqis_mlx.profiles.catalog import numeric_scope_bounds

        self.assertEqual(numeric_scope_bounds(), (4, 10))

    def test_b_to_c_entry_uses_four_to_ten_independent_of_legacy_flag(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from bilqis_mlx.profiles.catalog import (
            CatalogProfileTransition, next_school_transition)

        release = SimpleNamespace(
            execution_plan=SimpleNamespace(grades=(
                SimpleNamespace(grade_id='A'), SimpleNamespace(grade_id='B'))),
            curriculum=SimpleNamespace(grades=(
                SimpleNamespace(grade_id='A'), SimpleNamespace(grade_id='B'),
                SimpleNamespace(grade_id='C'))))
        base = CatalogProfileTransition(profile=object(), graph={'fixture': True})
        for legacy_flag in (False, True):
            with self.subTest(legacy_flag=legacy_flag), patch(
                    'bilqis_mlx.profiles.catalog.numeric_entry_transition',
                    return_value=base) as entry:
                transition = next_school_transition(
                    release, {}, full_boolean=False,
                    numeric_staircase=legacy_flag)
                self.assertEqual(transition.numeric_scope_final_maximum, 10)
                self.assertEqual(entry.call_args.kwargs['maximum'], 4)

    def test_numeric_entry_preserves_introduced_boolean_slice_without_mastery_gate(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
        from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
        from bilqis_mlx.profiles.catalog import numeric_entry_transition

        profile = CurriculumProfile('test/not-and', (
            GradeProfile('B', enabled_capabilities=('B.NOT', 'B.AND')),
            GradeProfile('C', enabled_capabilities=()),))
        release = Mock(spec=ExecutableFactoryRelease)
        release.profile = profile
        release.execution_plan = SimpleNamespace(grades=('A', 'B'))
        numeric_ids = ('C.COUNT', 'C.NUMBER', 'C.SUCCESSOR', 'C.ADD', 'C.SUB', 'C.MUL', 'C.DIV')
        release.curriculum = SimpleNamespace(grades=(None, None, SimpleNamespace(grade_id='C',
            capabilities=tuple(SimpleNamespace(capability_id=cap) for cap in numeric_ids))))
        with patch('bilqis_mlx.profiles.catalog.expanded_graph', return_value={'fixture': True}):
            transition = numeric_entry_transition(release, {}, full_boolean=False)
        grades = {grade.grade_id: grade for grade in transition.profile.grades}
        self.assertEqual(grades['B'], profile.grades[0])
        self.assertEqual(grades['C'].enabled_capabilities, numeric_ids)
        self.assertEqual(dict(grades['C'].capabilities[0].provider_parameters)['numbers'],
                         ('0', '1', '2', '3', '4'))
        self.assertEqual(transition.numeric_scope_final_maximum, 10)

    def test_numeric_scope_advances_exactly_one_root_and_stops_at_ten(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease
        from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
        from bilqis_mlx.factory.model import ProviderDimensionPolicy, SourceAdapter
        from bilqis_mlx.profiles.catalog import next_numeric_scope_profile

        numeric_ids = ('C.COUNT', 'C.NUMBER', 'C.SUCCESSOR', 'C.ADD',
                       'C.SUB', 'C.MUL', 'C.DIV')
        release = Mock(spec=ExecutableFactoryRelease)
        release.profile = CurriculumProfile('school/test/numeric-0-4', (
            GradeProfile('A', enabled_capabilities=('A.IDENTITY',)),
            GradeProfile('B', enabled_capabilities=('B.AND',)),
            GradeProfile('C', enabled_capabilities=numeric_ids),))
        release.execution_plan = SimpleNamespace(
            grades=(SimpleNamespace(grade_id='A'), SimpleNamespace(grade_id='B'),
                    SimpleNamespace(grade_id='C')),
            capabilities=(SimpleNamespace(
                capability_id='C.COUNT', grade_id='C', provider_id='source.finite-numeric/v2',
                provider_parameters=(('numbers', tuple(str(i) for i in range(5))),),
                answer_families=(SimpleNamespace(
                    kind='numeric_active', values=tuple(str(i) for i in range(5))),)),))
        release.source_adapters = (SourceAdapter(
            'source.finite-numeric/v2', 'fixture.numeric/v1', ('fixture.oracle/v1',),
            'd' * 64,
            profile_dimensions=(('numbers', tuple(str(i) for i in range(11))),)),)
        release.provider_dimension_policies = (ProviderDimensionPolicy(
            provider_id='source.finite-numeric/v2', dimension_id='numeric-root',
            parameter_name='numbers', progression_values=tuple(str(i) for i in range(4, 11)),
            selection_mode='CANONICAL_PREFIX', step_mode='ADJACENT',
            advance_trigger='DEVELOPMENTAL_BOUNDARY', terminal_value='10',
            source_constraint='SAME_PROVIDER_BINDING',
            admission_constraint='EXISTING_CAPABILITY_PROFILE',
            telemetry_projection='INTROOT', answer_family_kind='numeric_active',
            changes_source_projection=True, changes_assessment_scope=True,
            changes_answer_domain=True),)
        release.curriculum = SimpleNamespace(grades=(
            SimpleNamespace(grade_id='A', capabilities=()),
            SimpleNamespace(grade_id='B', capabilities=()),
            SimpleNamespace(grade_id='C', capabilities=tuple(
                SimpleNamespace(capability_id=cap) for cap in numeric_ids)),),
            capability_map={'C.COUNT': SimpleNamespace(answer_families=(
                SimpleNamespace(kind='numeric_active'),))})

        next_profile = next_numeric_scope_profile(release, final_maximum=10)
        self.assertTrue(next_profile.profile_id.endswith('/numeric-0-5'))
        c_grade = next(g for g in next_profile.grades if g.grade_id == 'C')
        self.assertEqual(
            dict(c_grade.capabilities[0].answer_family_values)['numeric_active'],
            ('0', '1', '2', '3', '4', '5'))

        release.execution_plan.capabilities = (SimpleNamespace(
            capability_id='C.COUNT', grade_id='C', provider_id='source.finite-numeric/v2',
            provider_parameters=(('numbers', tuple(str(i) for i in range(11))),),
            answer_families=(SimpleNamespace(
                kind='numeric_active', values=tuple(str(i) for i in range(11))),)),)
        self.assertIsNone(next_numeric_scope_profile(release, final_maximum=10))


if __name__ == "__main__":
    unittest.main()
