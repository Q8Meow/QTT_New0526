from .helpers import no_authority_records


def test_pr159r_selection_readiness_update_metadata_only(pr159r_artifacts):
    assert pr159r_artifacts["selection"]["record_count"] == 869
    assert no_authority_records(pr159r_artifacts["selection"])
    # All four update consumers share this exact declared confirmation schema.
    from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c

    complete = dict(c.NO_AUTHORITY_CONFIRMATION)
    assert no_authority_records({"records": [{"no_authority_confirmation": complete}]})
    # Emptiness remains the caller's separate record-count responsibility.
    assert no_authority_records({"records": []})
    assert not no_authority_records({"records": [{}]})
    assert not no_authority_records({"records": [{"no_authority_confirmation": {}}]})
    for field in complete:
        partial = dict(complete)
        del partial[field]
        assert not no_authority_records({"records": [{"no_authority_confirmation": partial}]})
        for invalid in (True, 0, None, "false"):
            changed = dict(complete)
            changed[field] = invalid
            assert not no_authority_records({"records": [{"no_authority_confirmation": changed}]})
    extra = dict(complete, unrecognized_authority=False)
    assert not no_authority_records({"records": [{"no_authority_confirmation": extra}]})
    for malformed in (None, [], False, "false"):
        assert not no_authority_records({"records": [{"no_authority_confirmation": malformed}]})
    assert not no_authority_records({"records": [{"no_authority_confirmation": complete}, {}]})

