"""Lossless immutable encoding for source-prefetch packet values."""
from __future__ import annotations


_MAP = "bilqis.source-packet/map"
_LIST = "bilqis.source-packet/list"
_TUPLE = "bilqis.source-packet/tuple"
_TAGS = frozenset((_MAP, _LIST, _TUPLE))
_TAGGED_VALUE_WIDTH = 2
_MAPPING_ENTRY_WIDTH = 2


class SourcePacketCodecError(ValueError):
    """Internal codec-shape failure translated by the packet owner."""


class SourcePacketForbiddenAuthority(SourcePacketCodecError):
    """Forbidden mutable authority appeared inside a source packet."""


def freeze_value(value, *, forbidden_mapping_keys: frozenset[str]):
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, dict):
        if forbidden_mapping_keys & set(value):
            raise SourcePacketForbiddenAuthority
        if not all(isinstance(key, str) for key in value):
            raise SourcePacketCodecError
        items = tuple(
            (key, freeze_value(value[key], forbidden_mapping_keys=forbidden_mapping_keys))
            for key in sorted(value))
        return (_MAP, items)
    if isinstance(value, list):
        return (_LIST, tuple(
            freeze_value(item, forbidden_mapping_keys=forbidden_mapping_keys)
            for item in value))
    if isinstance(value, tuple):
        return (_TUPLE, tuple(
            freeze_value(item, forbidden_mapping_keys=forbidden_mapping_keys)
            for item in value))
    raise SourcePacketCodecError


def validate_value(value, *, forbidden_mapping_keys: frozenset[str]) -> None:
    if value is None or type(value) in (str, bool, int, float):
        return
    if (not isinstance(value, tuple) or len(value) != _TAGGED_VALUE_WIDTH
            or value[0] not in _TAGS):
        raise SourcePacketCodecError
    tag, payload = value
    if not isinstance(payload, tuple):
        raise SourcePacketCodecError
    if tag == _MAP:
        if any(not isinstance(item, tuple) or len(item) != _MAPPING_ENTRY_WIDTH
               or not isinstance(item[0], str) for item in payload):
            raise SourcePacketCodecError
        keys = tuple(item[0] for item in payload)
        if (len(set(keys)) != len(keys) or tuple(sorted(keys)) != keys
                or forbidden_mapping_keys & set(keys)):
            raise SourcePacketCodecError
        for _, item in payload:
            validate_value(item, forbidden_mapping_keys=forbidden_mapping_keys)
        return
    for item in payload:
        validate_value(item, forbidden_mapping_keys=forbidden_mapping_keys)


def thaw_value(value):
    if value is None or type(value) in (str, bool, int, float):
        return value
    tag, payload = value
    if tag == _MAP:
        return {key: thaw_value(item) for key, item in payload}
    thawed = tuple(thaw_value(item) for item in payload)
    return list(thawed) if tag == _LIST else thawed


def freeze_payload(packet: dict, *, forbidden_mapping_keys: frozenset[str]) -> tuple:
    return tuple((key, freeze_value(packet[key], forbidden_mapping_keys=forbidden_mapping_keys))
                 for key in sorted(packet))


def validate_payload(payload: tuple, *, forbidden_mapping_keys: frozenset[str]) -> None:
    if (not isinstance(payload, tuple)
            or any(not isinstance(item, tuple) or len(item) != _MAPPING_ENTRY_WIDTH
                   or not isinstance(item[0], str) for item in payload)):
        raise SourcePacketCodecError
    keys = tuple(item[0] for item in payload)
    if len(set(keys)) != len(keys) or tuple(sorted(keys)) != keys:
        raise SourcePacketCodecError
    for _, value in payload:
        validate_value(value, forbidden_mapping_keys=forbidden_mapping_keys)


def thaw_payload(payload: tuple) -> dict:
    return {key: thaw_value(value) for key, value in payload}
