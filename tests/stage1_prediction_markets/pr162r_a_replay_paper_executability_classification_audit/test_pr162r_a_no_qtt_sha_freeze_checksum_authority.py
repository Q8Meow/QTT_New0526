from __future__ import annotations


def test_pr162r_a_no_qtt_sha_freeze_checksum_authority(summary, records):
    audit = records("PR162R_A_NoQttShaFreezeChecksumAuthorityAudit.report.json")[0]
    assert summary["qtt_sha_freeze_checksum_authority_count"] == 0
    assert audit["qtt_sha_freeze_checksum_authority_count"] == 0
