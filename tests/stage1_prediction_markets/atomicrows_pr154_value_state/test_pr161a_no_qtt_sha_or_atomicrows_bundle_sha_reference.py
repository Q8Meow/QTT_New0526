from pathlib import Path

from .pr161a_test_support import REPO_ROOT, report, summary


def test_pr161a_no_forbidden_bundle_digest_or_qtt_integrity_reference_added():
    forbidden_bundle = "AtomicRows.bundle" + ".sha256"
    forbidden_qtt = "QTT-generated " + "SHA"
    changed_paths = [
        *Path(REPO_ROOT, "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state").rglob("*"),
        *Path(REPO_ROOT, "tests/stage1_prediction_markets/atomicrows_pr154_value_state").rglob("*"),
    ]
    for path in changed_paths:
        if path.is_file() and path.suffix in {".py", ".json"}:
            text = path.read_text(encoding="utf-8")
            assert forbidden_bundle not in text
            assert forbidden_qtt not in text
    assert report("forbidden_scan")["records"][0]["finding_count"] == 0
    assert summary()["atomicrows_forbidden_bundle_digest_reference_added_flag"] is False
