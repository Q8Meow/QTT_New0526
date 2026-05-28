from .helpers import no_authority_records


def test_pr159r_selection_readiness_update_metadata_only(pr159r_artifacts):
    assert pr159r_artifacts["selection"]["record_count"] == 869
    assert no_authority_records(pr159r_artifacts["selection"])

