from tests.pr168_rp2._helpers import assert_rp2_valid


def test_no_hash_authority() -> None:
    assert_rp2_valid()
