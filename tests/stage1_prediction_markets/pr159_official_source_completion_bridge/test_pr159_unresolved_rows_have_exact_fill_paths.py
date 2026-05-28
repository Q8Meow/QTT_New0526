from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import (
    master_report,
    unresolved_records,
)


def test_pr159_unresolved_rows_have_exact_fill_paths():
    assert len(unresolved_records()) == 879 - master_report()["accepted_packet_count"]
    assert all(record["exact_steps_to_fill"] for record in unresolved_records())
    assert all(record["exact_acceptance_criteria"] for record in unresolved_records())
