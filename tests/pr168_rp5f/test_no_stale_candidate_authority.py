from ._helpers import assert_rows_have_contract, read_json


def test_no_stale_candidate_authority_exists() -> None:
    rows = assert_rows_have_contract("no_stale_candidate.jsonl")

    assert all(row["paper_live_dryrun_shadow_live_revalidation_required_flag"] for row in rows)
    assert all(row["stale_candidate_authority_flag"] is False for row in rows)
    assert all(row["proof_pass_flag"] is True for row in rows)
    assert read_json("run_receipt.report.json")["stale_candidate_authority_count"] == 0

