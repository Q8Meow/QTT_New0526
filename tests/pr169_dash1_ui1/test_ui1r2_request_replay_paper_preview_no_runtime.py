from tests.pr169_dash1_ui1.r2_contract_assertions import assert_next_step_route, assert_no_runtime_authority


def test_ui1r2_request_replay_paper_preview_no_runtime() -> None:
    assert_next_step_route("NEXT_STEP_REQUEST_REPLAY_PREVIEW", "route-preview", "ReplayRequestPreviewV1")
    assert_next_step_route("NEXT_STEP_REQUEST_PAPER_PREVIEW", "route-preview", "PaperRequestPreviewV1")
    assert_no_runtime_authority()
