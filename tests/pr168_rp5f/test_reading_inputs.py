from ._helpers import assert_nonempty_jsonl


def test_rp5f_reads_required_upstream_chain() -> None:
    rows = assert_nonempty_jsonl("read_rec.jsonl")
    refs = {row["file_ref"] for row in rows}

    assert any("generated/rp5c/" in ref for ref in refs)
    assert any("generated/pr168_vs1/" in ref for ref in refs)
    assert any("generated/pr168_rp5d/" in ref for ref in refs)
    assert any("generated/pr168_rp5e/" in ref for ref in refs)
    assert any("generated/pr168_rp5d_r1/" in ref for ref in refs)
    assert any(row["surface_family"] == "PR165_D2_AGENT_DUTY" for row in rows)
    assert all(row["exists_flag"] for row in rows)
