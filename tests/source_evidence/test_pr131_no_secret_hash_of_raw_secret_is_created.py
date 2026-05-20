from pathlib import Path

from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_secret_hash_of_raw_secret_is_created():
    package_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/qtt/stage1_prediction_markets/credential_readiness").glob("*.py")
    )

    assert "hashlib" not in package_text
    assert support.main_report()["PR131_SECRET_NO_CAPTURE_EVIDENCE"]["raw_secret_hash_created_count"] == 0
    assert support.main_report()["PR131_SECRET_NO_CAPTURE_EVIDENCE"]["secret_like_value_hashed_count"] == 0
