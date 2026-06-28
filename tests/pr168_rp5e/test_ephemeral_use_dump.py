from ._helpers import TMP_RUN_DIR, read_jsonl


def test_ephemeral_temp_manifest_and_dump_receipt_exist() -> None:
    manifest = read_jsonl("tmp_manifest.jsonl")[0]
    dump = read_jsonl("dump_rec.jsonl")[0]

    assert TMP_RUN_DIR.exists()
    assert (TMP_RUN_DIR / "manifest.json").exists()
    assert manifest["persistent_full_cartesian_grid_flag"] is False
    assert dump["full_cartesian_grid_written_flag"] is False
    assert dump["retained_topk_preview_rows"] == len(read_jsonl("topk.jsonl"))
