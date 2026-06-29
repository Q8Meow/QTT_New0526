from ._helpers import assert_rows_have_contract, read_json


def test_no_orphan_proofs_cover_artifacts_and_qkus() -> None:
    artifacts = assert_rows_have_contract("orph_art.jsonl")
    qkus = assert_rows_have_contract("orph_qku.jsonl")
    receipt = read_json("run_receipt.report.json")

    assert all(row["orphan_flag"] is False for row in artifacts)
    assert all(row["orphan_flag"] is False for row in qkus)
    assert receipt["orphan_artifact_count"] == 0
    assert receipt["orphan_qku_count"] == 0
    assert receipt["orphan_formula_count"] == 0

