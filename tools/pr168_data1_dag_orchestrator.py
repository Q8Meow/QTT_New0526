#!/usr/bin/env python3
"""DAG orchestration rows for DATA1 pipeline artifacts."""

from __future__ import annotations

from tools.pr168_data1_config import authority_flags, route_defaults


def build_dag_nodes(artifact_refs: list[str], now_utc: str) -> list[dict[str, object]]:
    node_specs = [
        ("online_source_docs", "source_discovery", ["endpoint_contract_registry"]),
        ("endpoint_contract_registry", "endpoint_registry", ["historical_full_book_availability_audit"]),
        ("historical_full_book_availability_audit", "availability_audit", ["current_snapshots", "historical_data", "forward_l2_capture"]),
        ("current_snapshots", "snapshot_jsonl", ["normalized_feature_rows"]),
        ("historical_data", "history_jsonl", ["normalized_feature_rows"]),
        ("forward_l2_capture", "forward_l2_jsonl", ["normalized_feature_rows"]),
        ("normalized_feature_rows", "feature_registry", ["data_readiness_classification"]),
        ("data_readiness_classification", "classification", ["gfp2r_handoff", "rp2_batch", "rank2_batch"]),
        ("gfp2r_handoff", "downstream_handoff", ["PR168-GFP2R"]),
        ("rp2_batch", "downstream_handoff", ["PR168-RP2"]),
        ("rank2_batch", "downstream_handoff", ["PR168-RANK2"]),
    ]
    rows = []
    for index, (node_id, node_type, downstream_refs) in enumerate(node_specs, start=1):
        upstream_refs = [] if index == 1 else [node_specs[index - 2][0]]
        rows.append(
            {
                "node_id": node_id,
                "node_type": node_type,
                "artifact_path_or_data_ref": artifact_refs[min(index - 1, len(artifact_refs) - 1)] if artifact_refs else node_id,
                "upstream_refs": upstream_refs,
                "downstream_refs": downstream_refs,
                "downstream_prs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
                "value_type": "fetched_data_or_computed_feature_or_action_route",
                "evidence_tier": "OFFICIAL_PUBLIC_API_OR_ACTIONABLE_GAP",
                "authority_class": "PUBLIC_READ_ONLY_DATA_ACQUISITION_CANDIDATE",
                "validation_refs": ["tools/pr168_data1_validator.py"],
                "test_refs": ["tests/pr168_data1"],
                "no_orphan_status": "NO_ORPHAN_ROUTED",
                "terminal_by_nature_flag": node_id.startswith("PR168-"),
                "terminal_reason_code": None,
                "repair_route_if_gap": "OPERATOR_ACTION_MATRIX",
                "created_at_utc": now_utc,
                **route_defaults("governance"),
                **authority_flags(),
            }
        )
    return rows
