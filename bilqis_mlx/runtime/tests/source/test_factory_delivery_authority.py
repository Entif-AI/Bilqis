from bilqis_mlx.factory.tests.lifecycle.test_teaching import closed_source_fixture
from bilqis_mlx.factory.teaching import optional_teaching_rows
from bilqis_mlx.runtime.source_execution import SourceExecutionContext


def test_grade_z_factory_delivery_authority_binds_direct_and_released_enrichment():
    _, graph, registry, answers, release = closed_source_fixture()
    context = SourceExecutionContext(release, graph, None, registry, answers)
    direct = tuple(context.draw_rows(seed=17, capability="Z.C0", each=2))
    enrichment = optional_teaching_rows(
        None, graph, release, registry, capability="Z.C0", seed=17, enabled=True)
    delivered = (*direct, *enrichment)

    authority = context.bind_delivery_rows(
        delivered, seed=17, capability="Z.C0", direct_each=len(direct))

    assert authority.capability_id == "Z.C0"
    assert authority.each == len(delivered)
    assert context.require_bound_rows(delivered, authority) is authority
