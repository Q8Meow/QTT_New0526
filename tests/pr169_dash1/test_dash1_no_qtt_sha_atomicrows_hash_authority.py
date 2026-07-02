from tests.pr169_dash1.conftest import json_doc, registry


def test_no_qtt_sha_or_atomicrows_hash_authority_created() -> None:
    report = json_doc("owner_dashboard_authority_boundary.report.json")
    assert report["QTT_SHA_or_QTT_generated_SHA_files"] is False
    assert report["AtomicRows_hash_SHA_authority"] is False
    for row in registry():
        assert row["qtt_sha_policy"] == "No QTT SHA/hash authority."
        assert row["atomicrows_sha_policy"] == "No AtomicRows bundle hash/SHA authority."
