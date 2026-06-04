from __future__ import annotations


def test_pr162r_a_pr162r_adapter_input_pack_created(summary, records):
    pack = records("PR162R_A_PR162RAdapterRerunInputPack.report.json")
    assert len(pack) == summary["replay_adapter_input_pack_count"]
    assert len(pack) == summary["candidate_source_count"]
    assert all(row["adapter_execution_performed_flag"] is False for row in pack)
