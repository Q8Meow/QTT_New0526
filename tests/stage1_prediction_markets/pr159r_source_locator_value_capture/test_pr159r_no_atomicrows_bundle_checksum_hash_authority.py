from .helpers import counts


def test_pr159r_no_atomicrows_bundle_checksum_hash_authority(pr159r_artifacts):
    assert counts(pr159r_artifacts)["atomicrows_bundle_checksum_hash_authority_count"] == 0

