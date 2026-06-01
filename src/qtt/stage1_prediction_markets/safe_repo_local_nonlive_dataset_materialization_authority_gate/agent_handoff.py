"""PR162A QTT agent dataset handoff bridge."""

from __future__ import annotations

from typing import Any

from . import constants as c


def agent_handoff_records(run_capable_dataset_count: int) -> list[dict[str, Any]]:
    return [
        {
            "record_id": f"PR162A-AGENT-DATASET-HANDOFF-{index:02d}-{agent_id}",
            "created_by_pr": c.PR_ID,
            "authority_class": c.AUTHORITY_CLASS,
            "agent_id": agent_id,
            "reads": _reads(agent_id),
            "validates": [
                "PR162A_DatasetAuthorityGate.report.json",
                "PR162A_DataQualityLeakageAndTimeWindowAudit.report.json",
                "PR162A_ForbiddenAuthorityScan.report.json",
            ],
            "emits": _emits(agent_id),
            "routes": _routes(agent_id),
            "run_capable_dataset_count_visible": run_capable_dataset_count,
            "runtime_agent_execution_created_flag": False,
            "self_authorizing_trading_allowed_flag": False,
            "permission_expansion_created_flag": False,
            "live_write_secret_access_allowed_flag": False,
            "order_routing_allowed_flag": False,
            "blocker_code": "NONE" if run_capable_dataset_count else "PR162A_BLOCKED_NO_SAFE_REPO_LOCAL_DATA",
        }
        for index, agent_id in enumerate(c.AGENT_ROLES, start=1)
    ]


def _reads(agent_id: str) -> list[str]:
    base = ["PR162A_DatasetMaterializationManifest.report.json"]
    if agent_id in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return base + ["PR162A_PR162AdapterRerunReadinessBridge.report.json"]
    if agent_id in {"QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"}:
        return base + ["PR162A_QuantumQKUDatasetFeatureBridge.report.json"]
    if agent_id == "QTT_OWNER_REVIEW_AGENT":
        return base + ["PR162A_FetchPlanAndOwnerMaterializationCommandQueue.report.json"]
    return base


def _emits(agent_id: str) -> list[str]:
    mapping = {
        "QTT_RESEARCH_AGENT": ["dataset_source_candidate_classifications"],
        "QTT_SOURCE_EVIDENCE_AGENT": ["source_evidence_routing_status_only"],
        "QTT_ATOMICROWS_ENRICHMENT_AGENT": ["atomicrows_qku_dataset_mapping_readiness_without_bundle_mutation"],
        "QTT_PARAMETER_STACK_AGENT": ["parameter_stack_data_readiness"],
        "QTT_QUANTUM_ADVISORY_AGENT": ["quantum_feature_readiness_no_backend_execution"],
        "QTT_OPTIMIZER_ARBITRATION_AGENT": ["future_comparator_readiness_no_optimizer_execution"],
        "QTT_REPLAY_AGENT": ["pr162b_pr162r_replay_rerun_readiness_only"],
        "QTT_PAPER_AGENT": ["pr162b_pr162r_paper_rerun_readiness_only"],
        "QTT_OWNER_REVIEW_AGENT": ["owner_review_queue_candidates_only"],
        "QTT_GOVERNANCE_AGENT": ["forbidden_authority_scan_pass_fail"],
        "QTT_EXECUTION_ROUTER_AGENT": ["future_precomputed_input_candidate_no_orders"],
    }
    return mapping.get(agent_id, ["future_gate_readiness_metadata_only"])


def _routes(agent_id: str) -> list[str]:
    if agent_id in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return ["PR162B_RERUN_PR162_WITH_PR162A_DATASETS", "PR162R_RERUN_PR162_WITH_PR162A_DATASETS"]
    if agent_id in {"QTT_SCORING_AGENT", "QTT_RANKING_AGENT"}:
        return ["PR163_BLOCKED_NO_VALIDATED_REAL_NONLIVE_REPLAY_ARTIFACTS"]
    if agent_id == "QTT_EXECUTION_ROUTER_AGENT":
        return ["NO_ORDER_ROUTE_CREATED"]
    return list(c.DOWNSTREAM_PR_ROUTES)
