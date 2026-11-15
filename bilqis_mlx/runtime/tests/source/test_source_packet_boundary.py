"""Every immutable worker packet constructor enforces the same boundary."""
import hashlib
import json
import unittest
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.source_packet_codec import freeze_payload
from bilqis_mlx.runtime.source_prefetch import (
    FORBIDDEN_NESTED_AUTHORITY_KEYS, ImmutableSourcePacket, SCHEMA,
    freeze_source_packet, thaw_source_packet,
)


def record(payload):
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return ImmutableSourcePacket('a' * 64, payload, digest)


class SourcePacketBoundaryTests(unittest.TestCase):
    def test_direct_constructor_rejects_mutable_alias_and_forbidden_authority(self):
        mutable = []
        payload = (('identity', 'a' * 64), ('schema', SCHEMA), ('weights', mutable))
        with self.assertRaises(BilqisError):
            record(payload)

        unsafe = dict(schema=SCHEMA, identity='a' * 64,
            fresh=[{'id': 'row:1', 'model_state': 'forbidden'}], prior=[],
            preservation=[], retention_support=[], teaching_enrichment_rows=[])
        encoded = freeze_payload(unsafe, forbidden_mapping_keys=frozenset())
        with self.assertRaises(BilqisError) as caught:
            record(encoded)
        self.assertEqual(caught.exception.context['reason'],
                         'SOURCE_PREFETCH_FORBIDDEN_AUTHORITY')

    def test_frozen_factory_payload_roundtrips_without_retained_alias(self):
        fresh = [{'source_receipt': {'receipt': 'source-only'}, 'value': [1, 2]}]
        packet = dict(schema=SCHEMA, identity='a' * 64, fresh=fresh, prior=[],
            preservation=[], retention_support=[], teaching_enrichment_rows=[])
        frozen = freeze_source_packet(packet)
        fresh[0]['value'].append(3)
        self.assertEqual(record(frozen.payload), frozen)
        self.assertNotEqual(freeze_source_packet(packet), frozen)

    def test_roundtrip_preserves_empty_mappings_sequences_and_pair_sequences(self):
        packet = dict(schema=SCHEMA, identity='a' * 64, fresh=[{
            'empty_mapping': {}, 'empty_sequence': [],
            'pair_sequence': [['A', 'B']], 'tuple_value': ('A', 'B'),
        }], prior=[], preservation=[], retention_support=[], teaching_enrichment_rows=[])
        self.assertEqual(thaw_source_packet(freeze_source_packet(packet)), packet)
