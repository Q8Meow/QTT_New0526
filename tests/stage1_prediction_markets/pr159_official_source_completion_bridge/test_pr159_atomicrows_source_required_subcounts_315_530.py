from collections import Counter

from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import atomicrows_records, master_report


def test_pr159_atomicrows_source_required_subcounts_315_530():
    counts = Counter(record["source_requirement_class"] for record in atomicrows_records())
    assert counts["PUBLIC_EXTERNAL_SOURCE_REQUIRED"] == 315
    assert counts["PARAMETER_RANGE_SOURCE_REQUIRED"] == 530
    assert master_report()["public_external_source_required_count"] == 315
    assert master_report()["parameter_range_source_required_count"] == 530

