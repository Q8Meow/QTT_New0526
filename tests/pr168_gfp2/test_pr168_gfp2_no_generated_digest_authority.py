from tests.pr168_gfp2.pr168_gfp2_test_support import root
from tools.pr168_gfp2_constants import REQUIRED_REPORTS


def test_no_qtt_sha_or_atomicrows_hash_authority() -> None:
    for name in REQUIRED_REPORTS:
        report = root(name)
        assert report["qku_sha_or_atomicrows_hash_authority_flag"] is False
        assert report["qtt_sha_or_atomicrows_hash_authority_flag"] is False
