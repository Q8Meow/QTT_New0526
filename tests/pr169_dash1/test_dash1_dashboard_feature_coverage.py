from tests.pr169_dash1.conftest import jsonl


def test_all_seeded_20d_dashboard_features_are_covered() -> None:
    rows = jsonl("owner_dashboard_feature_coverage.generated.jsonl")
    assert len(rows) >= 112
    assert {row["coverage_item_number"] for row in rows} >= set(range(1, 113))
    assert all(row["coverage_status"] == "COVERED_BY_REGISTRY_ROW" for row in rows)
