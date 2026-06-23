from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_valid_vs_artificial_classification_exists() -> None:
    assert_recovery1_valid()
    assert all("artificial_negative_flag" in row and "valid_negative_flag" in row for row in rows("valid_vs_artificial"))
