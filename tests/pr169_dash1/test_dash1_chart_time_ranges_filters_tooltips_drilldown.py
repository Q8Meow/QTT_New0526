from src.qtt.dashboard.owner_dashboard_projection_builder import FILTER_DIMENSIONS, TIME_RANGES
from tests.pr169_dash1.conftest import jsonl


def test_charts_have_time_ranges_filters_tooltips_and_drilldown() -> None:
    for row in jsonl("owner_interactive_chart_registry.generated.jsonl"):
        assert set(row["supported_time_ranges"]) == set(TIME_RANGES)
        assert set(FILTER_DIMENSIONS).issubset(set(row["filter_dimensions"]))
        assert row["tooltip_fields"]
        assert row["drilldown_route"].startswith("OwnerSurfaceResolver.")
