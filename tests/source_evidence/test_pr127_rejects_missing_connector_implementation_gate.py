from tests.source_evidence.pr127_execution_lifecycle_support import (
    main_report,
    rejections_by_state,
)


def test_pr127_rejects_missing_connector_implementation_gate():
    state = "REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE"
    rejection = rejections_by_state()[state][0]

    assert main_report()["missing_connector_implementation_gate_rejection_count"] == 1
    assert rejection["lifecycle_model_candidate_id"] == (
        "PR127_CANDIDATE_MISSING_CONNECTOR_IMPLEMENTATION_GATE"
    )
    assert rejection["rejection_reason_code"] == "CONNECTOR_IMPLEMENTATION_GATE_SUPPORT_NOT_FOUND"
