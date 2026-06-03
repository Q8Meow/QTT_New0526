from __future__ import annotations


def test_pr162d_r1_no_qtt_sha_freeze_checksum_authority(records, summary):
    audit = records("PR162D_R1_NoQttShaFreezeChecksumAuthorityAudit.report.json")[0]
    assert summary["qtt_sha_freeze_checksum_authority_count"] == 0
    assert audit["qtt_sha_freeze_checksum_authority_count"] == 0
