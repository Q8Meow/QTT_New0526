from src.qtt.dashboard.owner_surface_models import V4_ROUTE_LABELS
from tests.pr169_dash1.conftest import registry


def test_registry_uses_v4_route_labels_only() -> None:
    legacy_split_labels = {"DASH2", "TG2", "ACCESS1", "EXE1", "REALITY1", "DECISION1", "LLM3", "LLM4", "PLUGIN2"}
    for row in registry():
        assert row["v4_route_label"] in V4_ROUTE_LABELS
        assert row["v4_route_label"] not in legacy_split_labels
