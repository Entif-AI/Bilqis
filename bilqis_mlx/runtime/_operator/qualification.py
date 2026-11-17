"""One preflight/launch surface for finite, manifest-bound Factory qualification."""
from __future__ import annotations

import argparse
import importlib.util
from dataclasses import asdict
import json
import subprocess
from pathlib import Path

from .qualification_manifest import validate, require, QualificationStatus
from .model_topology import ModelTopologySpec


def operator_options(prepared):
    manifest = prepared.manifest
    budget = manifest['budget']
    return dict(resume=False, model_topology=ModelTopologySpec.from_record(prepared.arm['topology']),
        minutes=budget['minutes'], max_visits=budget['max_visits'],
        steps_per_visit=budget['steps_per_visit'], batch_size=budget['batch_size'],
        reserve_gib=manifest['policy']['value']['reserve_gib'],
        source_prefetch_workers=manifest['policy']['value']['source_prefetch_workers'],
        retention_enabled=True, numeric_staircase=False, full_grade_b=True,
        autonomous_curriculum=False, boolean_association_bridge=False, qualification=prepared)


def preflight(manifest, arm, expected_digest, *, root):
    prepared = validate(manifest, arm, implementation_root=root, expected_digest=expected_digest)
    refs = prepared.manifest['implementation'].get('component_refs', {})
    if refs:
        try:
            observed = subprocess.check_output(['git', '-C', str(root), 'ls-remote', 'origin', *refs.values()], text=True)
        except subprocess.CalledProcessError:
            require(False, 'COMPONENT_REMOTE_UNAVAILABLE')
        current = {line.split()[1]: line.split()[0] for line in observed.splitlines()}
        require(all(current.get(ref) == prepared.manifest['implementation']['components'][key]
                    for key, ref in refs.items()), 'COMPONENT_SUPERSEDED')
    from ..curriculum.promotion import PROMOTION_MEAN_FLOOR
    require(prepared.manifest['evaluation']['criterion'] == {
        'numerator': PROMOTION_MEAN_FLOOR.numerator, 'denominator': PROMOTION_MEAN_FLOOR.denominator,
        'aggregation': 'ARITHMETIC_MEAN_OF_CAPABILITY_ACCURACIES',
        'acquisition': 'STRICTLY_GREATER', 'post_acquisition': 'GREATER_OR_EQUAL'}, 'PROFICIENCY_RULE')
    require(prepared.manifest['policy']['value']['retention_settings'] == _settings(), 'RETENTION_POLICY')
    from .disk import headroom_snapshot
    disk = headroom_snapshot(Path(root), required_bytes=prepared.manifest['budget']['checkpoint_estimate_bytes'],
        reserve_gib=prepared.manifest['policy']['value']['reserve_gib'])
    require(disk['sufficient'], 'DISK_RESERVE')
    return prepared


def _settings():
    from ..learning.learning_experiment import Settings
    return asdict(Settings())


def execute(path, arm, expected_digest, *, root, human_run=False, dry_run=False):
    prepared = preflight(path, arm, expected_digest, root=root)
    report = {'schema': 'bilqis.factory.qualification-preflight/v1',
        'manifest_sha256': prepared.manifest['digest'], 'arm': arm,
        'status': QualificationStatus.READY,
        'neural_authority': False, 'actual_optimizer_updates': 0,
        'run_dir': prepared.arm['run_dir'], 'topology': prepared.arm['topology'],
        'budget': prepared.manifest['budget'], 'numeric_maximum': prepared.manifest['numeric_maximum']}
    if dry_run or not human_run:
        return report
    from .operating_loop import operate
    from .qualification_results import evaluate_finished_arm
    source = prepared.manifest['source']
    result = operate(Path(prepared.arm['run_dir']), Path(source['root']),
        Path(source['checkpoint']), Path(source['manifest']), **operator_options(prepared))
    return {**result, 'qualification': evaluate_finished_arm(prepared)}


def advance_frozen_boundary(mx, root, receipt, course, grade_a, source,
                            parameters, optimizer, graph, release, school, source_manifest):
    """Use normal profile admission for the next prequalified workload prefix."""
    from .admission import _read_executable_factory_release_artifact
    from .release_adoption import _adopt_executable_profile
    frozen = receipt['qualification']['allowed_releases']
    require(release.release_sha256 in frozen, 'FROZEN_RELEASE_DRIFT')
    index = frozen.index(release.release_sha256)
    if index == len(frozen) - 1:
        return parameters, optimizer, graph, receipt, course, False
    successor = _read_executable_factory_release_artifact(root, {
        'factory_release_sha256': frozen[index + 1],
        'factory_release_file': 'factory-releases/' + frozen[index + 1] + '.json'})
    debt = school.stage == 'AWAITING_NEXT_GRADE_WITH_DEBT'
    if debt:
        from .exam_execution import _measure_debt_admission_boundary
        receipt = _measure_debt_admission_boundary(mx, root, receipt, source_manifest,
            course, source, parameters, graph)
    receipt, course, _, _ = _adopt_executable_profile(root, receipt, grade_a, source,
        graph, successor.profile, compiled_successor=successor, allow_mastery_debt=debt)
    return parameters, optimizer, graph, receipt, course, True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--arm', required=True)
    parser.add_argument('--expected-digest', required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--human-run', action='store_true')
    args = parser.parse_args(argv)
    root = Path(importlib.util.find_spec("bilqis_mlx").origin).parent.parent
    try:
        result = execute(args.manifest, args.arm, args.expected_digest, root=root,
                         human_run=args.human_run, dry_run=args.dry_run)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': QualificationStatus.NOT_READY, 'error': str(error),
            'detail': dict(getattr(error, 'context', {})),
            'neural_authority_requested': bool(args.human_run and not args.dry_run),
            'actual_optimizer_updates': 'NOT_MEASURED' if args.human_run and not args.dry_run else 0}))
        return 2
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
