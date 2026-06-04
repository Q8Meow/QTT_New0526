from __future__ import annotations


def test_pr162r_a_no_result_packets_created(summary, records):
    adapter = records("PR162R_A_PR162RAdapterRerunInputPack.report.json")
    assert summary["result_packet_created_count"] == 0
    assert all(row["result_packet_created_flag"] is False for row in adapter)
