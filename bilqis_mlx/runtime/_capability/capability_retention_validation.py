"""Small structural validators for C05 retention decision records."""


def valid_blocking_score_budget(value) -> bool:
    """Validate (capability, before, after, total, allowed_loss)."""
    if value is None:
        return True
    if not isinstance(value, tuple) or len(value) != 5:
        return False
    capability, before, after, total, allowed = value
    return (
        isinstance(capability, str) and bool(capability)
        and all(type(number) is int for number in (before, after, total, allowed))
        and 0 <= before <= total
        and 0 <= after <= total
        and 0 <= allowed <= total
    )


__all__ = ("valid_blocking_score_budget",)
