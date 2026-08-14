"""Single resolver API for PR169-DASH1 owner dashboard consumers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
if TYPE_CHECKING:
    from ..stage1_prediction_markets.qku_computation_control_plane.existing_owner_projection import (
        ST12GOwnerDashboardEvidenceViewV2,
        ST12GOwnerProjectionResolutionV2,
    )

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


def resolve_st12g_projection_v2(
    svc_resolution: "ST12GOwnerProjectionResolutionV2",
) -> "ST12GOwnerDashboardEvidenceViewV2":
    """Derive DASH1/UI1 solely from the exact SVC1 owner resolution."""

    from ..stage1_prediction_markets.qku_computation_control_plane import (
        existing_owner_projection as st12g,
    )

    if (
        type(svc_resolution) is not st12g.ST12GOwnerProjectionResolutionV2
        or svc_resolution.consumer_id != "SVC1"
        or svc_resolution.consumer_contract_id != "ST12GServiceEvidenceViewV2"
    ):
        raise ContractValidationError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            "DASH1/UI1 accepts only the exact SVC1 owner resolution",
        )
    state = svc_resolution.resolution_state
    if state is st12g.ST12GProjectionResolutionStateV2.CURRENT_READ_ONLY:
        svc_projection = svc_resolution.projection
        if type(svc_projection) is not st12g.ST12GServiceEvidenceViewV2:
            raise ContractValidationError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "current dashboard input must contain the exact SVC1 projection",
            )
        identity = svc_projection.core.handoff_id
        source_projection_id = svc_projection.projection_id
        availability_badge = "CURRENT_CLOSED_EVIDENCE_AVAILABLE"
        stale_banner_state = "CURRENT"
        lineage = st12g.ST12GReferenceCollectionV2(
            state=st12g.ST12GReferenceCollectionStateV2.PRESENT_REFERENCES,
            reference_values=svc_projection.core.source_and_provenance_refs,
        )
    else:
        absence = svc_resolution.absence
        if type(absence) is not st12g.ST12GProjectionAbsenceV2 or absence.state is not state:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "dashboard must preserve the exact SVC1 noncurrent state",
            )
        identity = absence.absence_id
        source_projection_id = "EXPLICIT_ABSENCE"
        availability_badge = (
            "STALE_NO_AUTHORITY"
            if state
            is st12g.ST12GProjectionResolutionStateV2.UNAVAILABLE_STALE_NO_AUTHORITY
            else "BLOCKED_NO_AUTHORITY"
        )
        stale_banner_state = availability_badge
        lineage = st12g.ST12GReferenceCollectionV2(
            state=(
                st12g.ST12GReferenceCollectionStateV2.EXPLICIT_EMPTY_NONCURRENT_NO_SOURCE_LINEAGE
            ),
            reference_values=(),
        )
    return st12g.ST12GOwnerDashboardEvidenceViewV2(
        projection_id=f"ST12G::DASH1_UI1::{identity}",
        contract_version="2.0",
        consumer_id="DASH1_UI1",
        source_svc_resolution_state=state,
        source_svc_projection_id_or_explicit_absence=source_projection_id,
        panel_id="QKU_COMPUTATION_CONTROL_PLANE",
        availability_badge=availability_badge,
        stale_banner_state=stale_banner_state,
        owner_safe_next_action="REVIEW_PROJECTED_EVIDENCE_ONLY",
        direct_f_binding_allowed=False,
        live_control_authority="NONE",
        source_lineage_state=lineage,
        runtime_effect_allowed=False,
        write_authority="NONE",
    )
