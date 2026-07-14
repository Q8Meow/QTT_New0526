from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

try:
    from qtt.computation_control import QKUComputationControlPlaneV1
except ModuleNotFoundError:  # repository-root ``src.qtt`` test/import mode
    from src.qtt.computation_control import QKUComputationControlPlaneV1


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_svc1")

JSONL_FILES = frozenset(
    {
        "service_registry.jsonl",
        "read_model_snapshots.generated.jsonl",
        "read_model_snapshot_index.generated.jsonl",
        "read_model_store_contracts.generated.jsonl",
        "event_stream_contracts.generated.jsonl",
        "owner_action_requests.generated.jsonl",
        "owner_action_receipts.generated.jsonl",
        "action_eligibility.generated.jsonl",
        "action_denied_reasons.generated.jsonl",
        "provider_pending_routes.generated.jsonl",
        "pretrade_view_routes.generated.jsonl",
        "no_trade_explanation_views.generated.jsonl",
        "tca_decomposition_views.generated.jsonl",
        "execution_adjusted_ranking_views.generated.jsonl",
        "qku_formula_compute_route_views.generated.jsonl",
        "agent_workflow_queue_views.generated.jsonl",
        "llm_grounding_route_views.generated.jsonl",
        "quantum_structural_readiness_views.generated.jsonl",
        "owner_ux_semantic_routes.generated.jsonl",
        "owner_chart_manifest.generated.jsonl",
        "owner_widget_manifest.generated.jsonl",
        "agent_operations_views.generated.jsonl",
        "team_workflow_queue_views.generated.jsonl",
        "owner_audit_trail_views.generated.jsonl",
        "execution_live_status_preview_views.generated.jsonl",
        "owner_next_step_routes.generated.jsonl",
        "surface_parity_routes.generated.jsonl",
        "artifact_value_route_map.generated.jsonl",
        "market_venue_expansion_socket_routes.generated.jsonl",
        "downstream_dag_route_views.generated.jsonl",
        "owner_conversation_views.generated.jsonl",
        "owner_plain_english_intent_routes.generated.jsonl",
        "owner_chat_route_previews.generated.jsonl",
        "owner_research_intake_routes.generated.jsonl",
        "owner_trade_intent_routes.generated.jsonl",
        "owner_search_index_routes.generated.jsonl",
        "owner_layout_profile_routes.generated.jsonl",
        "owner_notification_tier_policy.generated.jsonl",
        "owner_stale_data_banner_views.generated.jsonl",
        "mobile_app_shell_contract_views.generated.jsonl",
        "mobile_navigation_contract_views.generated.jsonl",
        "trade_workbench_route_views.generated.jsonl",
        "execution_ladder_stage_views.generated.jsonl",
        "ui_visual_qa_handoff_views.generated.jsonl",
    }
)


@dataclass(frozen=True)
class OwnerDashboardReadModelV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OwnerSessionBoundaryV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class OwnerActionRequestQueueV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OwnerAuditReceiptStreamV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DashboardEventStreamV1:
    rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DashboardAuthBoundary:
    row: dict[str, Any]


@dataclass(frozen=True)
class DashboardSessionPolicy:
    row: dict[str, Any]


@dataclass(frozen=True)
class DashboardReadModelStore:
    rows: tuple[dict[str, Any], ...]


class DashboardSnapshotProvider(DashboardReadModelStore):
    pass


class DashboardEventStreamProvider(DashboardReadModelStore):
    pass


class DashboardActionRequestQueue(DashboardReadModelStore):
    pass


class DashboardAuditReceiptStream(DashboardReadModelStore):
    pass


class OwnerDashboardReadModelSnapshotV1(OwnerDashboardReadModelV1):
    pass


class OwnerActionRequestEnvelopeV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionReceiptEnvelopeV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionEligibilityViewV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionDeniedReasonV1(OwnerActionRequestQueueV1):
    pass


class OwnerActionProviderPendingReasonV1(OwnerActionRequestQueueV1):
    pass


class OwnerSessionPolicyV1(OwnerSessionBoundaryV1):
    pass


class OwnerEventStreamCursorV1(DashboardEventStreamV1):
    pass


class OwnerAuditReceiptCursorV1(OwnerAuditReceiptStreamV1):
    pass


class OwnerDecisionQueueReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentActivityReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerWorkflowQueueReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerReceiptPreviewReadModelV1(OwnerDashboardReadModelV1):
    pass


class OwnerWorkflowQueuePreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentActivityPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerPreTradeDecisionPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerNoTradeExplanationPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerTCADecompositionPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionAdjustedRankingPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerQKUFormulaRoutePreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionLadderPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerQuantumReadinessPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerUXSemanticBundleViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerWidgetManifestViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerChartManifestViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAgentOperationsViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerTeamWorkflowQueueViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerAuditTrailViewV1(OwnerDashboardReadModelV1):
    pass


class OwnerExecutionStatusPreviewV1(OwnerDashboardReadModelV1):
    pass


class OwnerNextStepRouteViewV1(OwnerDashboardReadModelV1):
    pass


class ArtifactValueRouteMapViewV1(OwnerDashboardReadModelV1):
    pass


class MarketVenueExpansionSocketViewV1(OwnerDashboardReadModelV1):
    pass


def _public_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        payload = as_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise TypeError("computation control result does not expose a public mapping")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return tuple(rows)


class DashboardReadModelService:
    def __init__(
        self,
        base_dir: Path | str | None = None,
        *,
        computation_control: QKUComputationControlPlaneV1 | None = None,
    ) -> None:
        root = _repo_root()
        self.base_dir = (Path(base_dir) if base_dir is not None else root / GENERATED_PREFIX).resolve()
        self._cache: dict[str, tuple[dict[str, Any], ...]] = {}
        self._computation_control = computation_control

    def _require_computation_control(self) -> QKUComputationControlPlaneV1:
        if self._computation_control is None:
            raise RuntimeError("no computation control facade was injected")
        return self._computation_control

    def search_computation(
        self,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        result = self._require_computation_control().resolve(
            selector,
            context,
            agent_id=agent_id,
        )
        return _public_payload(result)

    def computation_status(
        self,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        return dict(
            self._require_computation_control().status(
                selector,
                context,
                agent_id=agent_id,
            )
        )

    def explain_computation(
        self,
        receipt_or_selector: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        return dict(
            self._require_computation_control().explain(
                receipt_or_selector,
                context,
                agent_id=agent_id,
            )
        )

    def _path(self, file_name: str) -> Path:
        if file_name not in JSONL_FILES:
            raise KeyError(file_name)
        path = (self.base_dir / file_name).resolve()
        if self.base_dir not in (path, *path.parents):
            raise ValueError(f"SVC1 artifact escapes base directory: {file_name}")
        return path

    def _rows(self, file_name: str) -> tuple[dict[str, Any], ...]:
        if file_name not in self._cache:
            self._cache[file_name] = _read_jsonl(self._path(file_name))
        return self._cache[file_name]

    def _first(self, file_name: str, predicate: Any) -> dict[str, Any]:
        for row in self._rows(file_name):
            if predicate(row):
                return dict(row)
        raise KeyError(file_name)

    def _by_candidate(self, file_name: str, candidate_id: str) -> dict[str, Any]:
        return self._first(file_name, lambda row: row.get("candidate_id") == candidate_id)

    def load_service_manifest(self) -> dict[str, Any]:
        return _read_json((self.base_dir / "service_manifest.json").resolve())

    def list_read_model_snapshots(self) -> tuple[dict[str, Any], ...]:
        return self._rows("read_model_snapshots.generated.jsonl")

    def get_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        return self._first(
            "read_model_snapshots.generated.jsonl",
            lambda row: row.get("snapshot_id") == snapshot_id,
        )

    def list_snapshot_index(self) -> tuple[dict[str, Any], ...]:
        return self._rows("read_model_snapshot_index.generated.jsonl")

    def list_event_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("event_stream_contracts.generated.jsonl")

    def list_action_requests(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_action_requests.generated.jsonl")

    def get_action_eligibility(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "action_eligibility.generated.jsonl",
            lambda row: row.get("action_code") == action_code
            and (candidate_id is None or row.get("candidate_id") == candidate_id),
        )

    def get_action_denied_reason(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "action_denied_reasons.generated.jsonl",
            lambda row: row.get("action_code") == action_code
            and (candidate_id is None or row.get("candidate_id") == candidate_id),
        )

    def get_provider_pending_reason(self, action_code: str, candidate_id: str | None = None) -> dict[str, Any]:
        return self._first(
            "provider_pending_routes.generated.jsonl",
            lambda row: row.get("owner_action_ref_or_gap") == action_code
            or (candidate_id is not None and row.get("candidate_id") == candidate_id),
        )

    def list_action_receipt_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_action_receipts.generated.jsonl")

    def get_pretrade_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("pretrade_view_routes.generated.jsonl", candidate_id)

    def get_no_trade_explanation(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("no_trade_explanation_views.generated.jsonl", candidate_id)

    def get_tca_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("tca_decomposition_views.generated.jsonl", candidate_id)

    def get_execution_adjusted_ranking_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("execution_adjusted_ranking_views.generated.jsonl", candidate_id)

    def get_qku_formula_route_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("qku_formula_compute_route_views.generated.jsonl", candidate_id)

    def get_agent_workflow_preview(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("agent_workflow_queue_views.generated.jsonl", candidate_id)

    def get_llm_grounding_route(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("llm_grounding_route_views.generated.jsonl", candidate_id)

    def get_quantum_readiness_view(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("quantum_structural_readiness_views.generated.jsonl", candidate_id)

    def get_owner_ux_semantic_route(self, surface_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("owner_ux_semantic_routes.generated.jsonl")
        if surface_id is None:
            return rows
        return tuple(row for row in rows if row.get("owner_read_model_section") == surface_id)

    def get_owner_chart_manifest(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_chart_manifest.generated.jsonl")

    def get_owner_widget_manifest(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_widget_manifest.generated.jsonl")

    def get_agent_operations_view(self, agent_role_or_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("agent_operations_views.generated.jsonl")
        if agent_role_or_id is None:
            return rows
        return tuple(
            row
            for row in rows
            if agent_role_or_id in {str(role) for role in row.get("responsible_agent_role_refs", [])}
        )

    def get_team_workflow_queue(self, stage: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("team_workflow_queue_views.generated.jsonl")
        if stage is None:
            return rows
        return tuple(row for row in rows if row.get("current_stage") == stage)

    def get_owner_audit_trail_preview(
        self,
        candidate_id: str | None = None,
        workflow_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = self._rows("owner_audit_trail_views.generated.jsonl")
        return tuple(
            row
            for row in rows
            if (candidate_id is None or row.get("candidate_id") == candidate_id)
            and (workflow_id is None or row.get("workflow_id_or_gap") == workflow_id)
        )

    def get_execution_status_preview(self, candidate_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("execution_live_status_preview_views.generated.jsonl")
        if candidate_id is None:
            return rows
        return tuple(row for row in rows if row.get("candidate_id") == candidate_id)

    def get_owner_next_step_route(
        self,
        action_id: str,
        current_surface_id: str | None = None,
    ) -> dict[str, Any]:
        return self._first(
            "owner_next_step_routes.generated.jsonl",
            lambda row: row.get("action_id") == action_id
            and (current_surface_id is None or row.get("current_surface_id") == current_surface_id),
        )

    def get_surface_parity_routes(self, surface_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("surface_parity_routes.generated.jsonl")
        if surface_id is None:
            return rows
        return tuple(row for row in rows if row.get("target_surface_id_or_gap") == surface_id)

    def get_artifact_value_route_map(self, artifact_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._rows("artifact_value_route_map.generated.jsonl")
        if artifact_id is None:
            return rows
        return tuple(row for row in rows if artifact_id in str(row.get("projection_ref", "")))

    def get_market_venue_expansion_socket(
        self,
        market_family: str | None = None,
        venue_or_platform_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = self._rows("market_venue_expansion_socket_routes.generated.jsonl")
        return tuple(
            row
            for row in rows
            if (market_family is None or row.get("market_family") == market_family)
            and (
                venue_or_platform_id is None
                or row.get("venue_or_platform_id_or_gap") == venue_or_platform_id
            )
        )

    def get_downstream_routes(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(
            row
            for row in self._rows("downstream_dag_route_views.generated.jsonl")
            if row.get("candidate_id") == candidate_id
        )

    def list_owner_conversation_views(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_conversation_views.generated.jsonl")

    def parse_owner_plain_english_intent_preview(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        if "why" in lowered and "no-trade" in lowered:
            intent = "NO_TRADE_EXPLANATION_REQUEST"
        elif "formula" in lowered or "qku" in lowered:
            intent = "FORMULA_EXTRACTION_REQUEST"
        elif "quantum" in lowered:
            intent = "QUANTUM_MAPPING_REQUEST"
        elif "replay" in lowered or "paper" in lowered:
            intent = "REPLAY_PAPER_REQUEST"
        elif "article" in lowered or "research" in lowered or "source" in lowered:
            intent = "RESEARCH_ANALYSIS_REQUEST"
        elif "rank" in lowered or "edge" in lowered or "alpha" in lowered:
            intent = "EDGE_ALPHA_RANKING_REQUEST"
        elif "variable" in lowered or "parameter" in lowered:
            intent = "PARAMETER_TUNING_REQUEST"
        else:
            intent = "TRADE_CHECK_REQUEST"
        row = self._first(
            "owner_plain_english_intent_routes.generated.jsonl",
            lambda candidate: candidate.get("intent_class") == intent,
        )
        preview = dict(row)
        preview["plain_english_text_or_ref"] = text
        preview["parser_runtime"] = "DETERMINISTIC_ROUTE_PREVIEW_NO_LLM_CALL"
        return preview

    def list_owner_chat_route_previews(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_chat_route_previews.generated.jsonl")

    def list_owner_research_intake_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_research_intake_routes.generated.jsonl")

    def list_owner_trade_intent_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_trade_intent_routes.generated.jsonl")

    def list_owner_search_index_routes(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_search_index_routes.generated.jsonl")

    def list_owner_layout_profiles(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_layout_profile_routes.generated.jsonl")

    def list_owner_notification_tier_policy(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_notification_tier_policy.generated.jsonl")

    def list_owner_stale_data_banners(self) -> tuple[dict[str, Any], ...]:
        return self._rows("owner_stale_data_banner_views.generated.jsonl")

    def list_mobile_app_shell_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("mobile_app_shell_contract_views.generated.jsonl")

    def list_mobile_navigation_contracts(self) -> tuple[dict[str, Any], ...]:
        return self._rows("mobile_navigation_contract_views.generated.jsonl")

    def get_trade_workbench_route(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("trade_workbench_route_views.generated.jsonl", candidate_id)

    def get_execution_ladder(self, candidate_id: str) -> dict[str, Any]:
        return self._by_candidate("execution_ladder_stage_views.generated.jsonl", candidate_id)

    def list_ui_visual_qa_handoffs(self) -> tuple[dict[str, Any], ...]:
        return self._rows("ui_visual_qa_handoff_views.generated.jsonl")


class OwnerDashboardAPI(DashboardReadModelService):
    pass


def load_service_manifest(*, base_dir: Path | str | None = None) -> dict[str, Any]:
    return DashboardReadModelService(base_dir).load_service_manifest()


def list_read_model_snapshots(*, base_dir: Path | str | None = None) -> tuple[dict[str, Any], ...]:
    return DashboardReadModelService(base_dir).list_read_model_snapshots()
