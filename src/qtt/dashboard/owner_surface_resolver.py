"""Single resolver API for PR169-DASH1 owner dashboard consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .owner_action_registry import OwnerActionRegistry
from .owner_surface_models import read_json, read_jsonl
from .owner_surface_registry import OwnerDashboardSurfaceRegistry


class OwnerSurfaceResolver:
    """Resolve dashboard features, actions, panels, routes, and chart contracts.

    The resolver reads the canonical registry plus known generated projections by
    filename. It does not glob generated JSONL files or build another registry.
    """

    def __init__(self, base_dir: Path | str = "docs/master_plan/generated/pr169_dash1") -> None:
        self.base_dir = Path(base_dir)
        self.registry = OwnerDashboardSurfaceRegistry.load(self.base_dir)
        self.actions = OwnerActionRegistry.default()
        self._cache: dict[str, list[dict[str, Any]]] = {}

    def _jsonl(self, file_name: str) -> list[dict[str, Any]]:
        if file_name not in self._cache:
            self._cache[file_name] = read_jsonl(self.base_dir / file_name)
        return self._cache[file_name]

    def get_owner_dashboard_packet(self, context: Any | None = None) -> dict[str, Any]:
        return self._jsonl("owner_dashboard_packet.generated.jsonl")[0]

    def get_decision_queue(self, context: Any | None = None) -> list[dict[str, Any]]:
        return self._jsonl("owner_decision_queue.generated.jsonl")

    def get_actionable_card(self, card_id: str) -> dict[str, Any]:
        for row in self._jsonl("owner_actionable_card.generated.jsonl"):
            if row["card_id"] == card_id:
                return row
        raise KeyError(card_id)

    def get_surface_feature(self, feature_id: str) -> dict[str, Any]:
        return self.registry.get(feature_id)

    def get_panel_features(self, panel_id: str) -> list[dict[str, Any]]:
        return self.registry.panel_features(panel_id)

    def get_action_code(self, action_code: str) -> dict[str, Any]:
        for row in self._jsonl("owner_action_registry.generated.jsonl"):
            if row["action_code"] == action_code:
                return row
        return self.actions.get(action_code)

    def get_agent_routes(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_agent_route_projection.generated.jsonl") if row["feature_id"] == feature_id]

    def get_telegram_projection(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_telegram_projection.generated.jsonl") if row["feature_id"] == feature_id]

    def get_downstream_routes(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_downstream_route_projection.generated.jsonl") if row["feature_id"] == feature_id]

    def get_source_workflow(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_source_panel_contract.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_live_cash_private_display_slot(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_live_cash_private_display_contract.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_shadow_mode_display_slot(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_shadow_mode_display_contract.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_reasoning_brain_view(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_reasoning_brain_view_contract.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_edge_alpha_capture_view(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_edge_alpha_capture_view.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_qku_formula_candidate_routes(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_qku_formula_candidate_route_view.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_quantum_structural_readiness_view(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_quantum_structural_readiness_view.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_institutional_metric_refs(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_institutional_metric_view.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_chart_contract(self, chart_id: str) -> dict[str, Any]:
        for row in self._jsonl("owner_chart_surface_contract.generated.jsonl"):
            if row["chart_id"] == chart_id:
                return row
        for row in self._jsonl("owner_interactive_chart_registry.generated.jsonl"):
            if row["chart_id"] == chart_id or row["chart_family"] == chart_id:
                return row
        raise KeyError(chart_id)

    def get_data_value_routes(self, feature_id: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self._jsonl("owner_data_value_route_map.generated.jsonl")
            if any(str(ref).endswith(f"::{feature_id}") for ref in row.get("owner_surface_registry_refs", []))
        ]

    def get_execution_authority_ladder(self, feature_id: str) -> list[dict[str, Any]]:
        return [row for row in self._jsonl("owner_execution_authority_ladder_view.generated.jsonl") if row["registry_row_ref"].endswith(f"::{feature_id}")]

    def get_manifest(self) -> dict[str, Any]:
        return read_json(self.base_dir / "owner_dashboard_registry_manifest.json")
