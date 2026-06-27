from ._helpers import read_jsonl


def test_clean_room_default_candidates_are_non_authority_calibration_inputs() -> None:
    defaults = read_jsonl("default_cand.jsonl")
    queue = read_jsonl("calib_queue.jsonl")

    assert defaults
    for row in defaults:
        assert row["clean_room_flag"] is True
        assert row["nda_or_confidential_input_flag"] is False
        assert row["improper_access_flag"] is False
        assert row["proprietary_claim_flag"] is False
        assert row["replay_paper_verification_required"] is True
        assert row["live_authority_flag"] is False

    assert {row["parameter_name"] for row in defaults} == {
        row["parameter_name"] for row in queue
    }
