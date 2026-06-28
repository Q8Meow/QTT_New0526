from ._helpers import ART_DIR, all_jsonl_rows, read_json


def test_no_mutation_no_sha_no_live_authority_flags_across_rows() -> None:
    for row in all_jsonl_rows():
        assert row.get("formula_mutation_flag", False) is False
        assert row.get("qku_mutation_flag", False) is False
        assert row.get("global_ban_flag", False) is False
        assert row.get("live_authority_flag") is False
        assert row.get("qtt_sha_authority_flag") is False
        assert row.get("atomicrows_sha_ref_flag") is False

    text = "\n".join(path.read_text(encoding="utf-8") for path in ART_DIR.glob("*") if path.is_file())
    assert "AtomicRows.bundle.sha256" not in text
    assert ".sha256" not in text

    receipt = read_json("run_receipt.report.json")
    for key in ("formula_mutation_count", "qku_mutation_count", "qtt_sha_authority_count"):
        assert receipt[key] == 0
