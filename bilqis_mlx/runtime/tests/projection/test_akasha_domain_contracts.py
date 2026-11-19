"""CT-050 logical Akasha domain/authority conformance."""
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_domains import (
    AkashaDomain,
    DOMAIN_CONTRACTS,
    rebuild_projection_identity,
    require_cross_domain_reference,
    require_current_projection,
    require_domain_operation,
)


class AkashaDomainContractTests(unittest.TestCase):
    def test_all_six_domains_have_one_owner_and_explicit_rebuild_contract(self):
        self.assertEqual(set(DOMAIN_CONTRACTS), set(AkashaDomain))
        self.assertEqual(len(DOMAIN_CONTRACTS), 6)
        for domain, contract in DOMAIN_CONTRACTS.items():
            with self.subTest(domain=domain.value):
                self.assertEqual(contract.domain, domain)
                self.assertTrue(contract.authority_owner)
                self.assertTrue(contract.rebuild_sources)
                self.assertTrue(contract.stable_identity_classes)
                self.assertTrue(contract.exact_identity_classes)
                self.assertEqual(
                    contract.stale_behavior,
                    "reject-stale-or-mismatched-projection-identity")

    def test_every_domain_rebuild_is_deterministic_and_source_bound(self):
        for domain in AkashaDomain:
            with self.subTest(domain=domain.value):
                source = ({"id": domain.value, "revision": "1"},)
                first = rebuild_projection_identity(domain, source)
                second = rebuild_projection_identity(domain, source)
                changed = rebuild_projection_identity(
                    domain, ({"id": domain.value, "revision": "2"},))
                self.assertEqual(first, second)
                self.assertNotEqual(first.source_frontier_sha256,
                                    changed.source_frontier_sha256)
                self.assertNotEqual(first.projection_sha256, changed.projection_sha256)
                self.assertIs(require_current_projection(first, source), first)
                with self.assertRaises(BilqisError):
                    require_current_projection(first, ({"id": domain.value,
                                                        "revision": "2"},))

    def test_illegal_cross_domain_and_wrong_owner_operations_fail_closed(self):
        factory = AkashaDomain.FACTORY_RELEASE_LEDGER
        semantic = AkashaDomain.SEMANTIC_GRAPH
        contract = require_domain_operation(
            factory, "factory-release-authority", "append")
        self.assertEqual(contract.domain, factory)
        with self.assertRaises(BilqisError):
            require_domain_operation(factory, "semantic-release-authority", "append")
        with self.assertRaises(BilqisError):
            require_domain_operation(factory, "factory-release-authority", "overwrite")
        self.assertEqual(
            require_cross_domain_reference(
                factory, semantic,
                stable_identity_class="semantic_rid",
                exact_identity_class="semantic_release_sha256").domain,
            semantic)
        with self.assertRaises(BilqisError):
            require_cross_domain_reference(
                semantic, AkashaDomain.PROGRAM_OPERATIONS,
                stable_identity_class="program_id",
                exact_identity_class="gate_receipt_sha256")


if __name__ == "__main__":
    unittest.main()
