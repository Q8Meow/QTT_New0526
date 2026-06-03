from .pr162d_test_support import assert_no_qtt_digest_authority


def test_pr162d_no_qtt_sha_freeze_hash_checksum_authority():
    assert_no_qtt_digest_authority()
