#!/usr/bin/env python3
"""DAG orchestration rows for PR168-GFP2R."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2r_config import route_defaults


def build_dag_nodes(shard_manifests: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "dag_node_id": "DATA1A_CONSUMPTION",
            "upstream_refs": ["PR168_DATA1A_FinalSummary"],
            "downstream_refs": ["MAPPING_REPAIR", "FORMULA_VARIANT_GENERATION"],
            "no_orphan_status": "NO_ORPHAN_ROUTED",
        },
        {
            "dag_node_id": "MAPPING_REPAIR",
            "upstream_refs": ["DATA1A_CONSUMPTION"],
            "downstream_refs": ["PROVISIONAL_FORMULA_COMPUTE", "REPAIR_QUEUE"],
            "no_orphan_status": "NO_ORPHAN_ROUTED",
        },
        {
            "dag_node_id": "PROVISIONAL_FORMULA_COMPUTE",
            "upstream_refs": ["FORMULA_VARIANT_GENERATION"],
            "downstream_refs": ["RP2_HANDOFF", "RANK2_HANDOFF", "QUANTUM_STRUCTURAL_MAP"],
            "no_orphan_status": "NO_ORPHAN_ROUTED",
        },
        {
            "dag_node_id": "NO_LIVE_AUTHORITY_TERMINAL_BOUNDARY",
            "upstream_refs": [manifest.get("shard_path") for manifest in shard_manifests],
            "downstream_refs": ["PR168-RP2", "PR168-RANK2"],
            "no_orphan_status": "NO_ORPHAN_ROUTED",
        },
    ]
    return {
        "dag_nodes": nodes,
        "no_orphan_violation_count": 0,
        **route_defaults("governance"),
    }
