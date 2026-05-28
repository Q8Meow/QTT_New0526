from .helpers import counts


def test_pr159r_no_qtt_checksum_freeze_global_digest_authority(pr159r_artifacts):
    assert counts(pr159r_artifacts)["qtt_checksum_freeze_global_digest_authority_count"] == 0

