from __future__ import annotations


def test_pr162r_a_no_orphan_generated_files(summary, records):
    audit = records("PR162R_A_NoOrphanGeneratedFileAudit.report.json")[0]
    assert summary["orphan_generated_file_count"] == 0
    assert audit["orphan_generated_file_count"] == 0
