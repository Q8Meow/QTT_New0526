from .helpers import forbidden_value_strings


def _contains_forbidden(value, forbidden):
    if isinstance(value, str):
        return value in forbidden
    if isinstance(value, dict):
        return any(_contains_forbidden(child, forbidden) for child in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden(child, forbidden) for child in value)
    return False


def test_pr159r_no_placeholder_values(pr159r_artifacts):
    forbidden = forbidden_value_strings()
    for record in pr159r_artifacts["targets"]["records"]:
        assert not _contains_forbidden(
            record.get("accepted_value_or_range_or_enum_or_metadata"),
            forbidden,
        )
