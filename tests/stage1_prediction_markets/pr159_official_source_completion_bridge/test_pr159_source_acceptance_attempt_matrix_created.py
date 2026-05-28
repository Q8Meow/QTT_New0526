from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import (
    accepted_records,
    attempt_matrix_records,
    master_report,
)


def test_pr159_source_acceptance_attempt_matrix_created():
    records = attempt_matrix_records()
    accepted_ids = {record["accepted_packet_id"] for record in accepted_records()}
    matrix_accepted_ids = {
        record["accepted_packet_ref_or_null"]
        for record in records
        if record["accepted_packet_ref_or_null"] is not None
    }
    assert master_report()["source_acceptance_attempt_matrix_created"] is True
    assert len(records) == 879
    assert matrix_accepted_ids == accepted_ids
    assert all(record["exact_next_action"] for record in records)
    assert all(
        record["acceptance_possible_flag"] is True
        for record in records
        if record["accepted_packet_ref_or_null"] is not None
    )

