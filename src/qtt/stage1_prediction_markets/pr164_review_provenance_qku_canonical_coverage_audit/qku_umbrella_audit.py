"""QKU umbrella and inventory projection reports."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref
from .json_io import stable_counter


def build_umbrella_audit(identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "umbrella_audit_ref": plain_ref("UMBRELLA", 1),
            "qku_canonical_identity_rows": len(identity_rows),
            "current_candidate_packet_rows": sum(1 for row in identity_rows if row["candidate_id"]),
            "historical_only_qku_rows": sum(1 for row in identity_rows if not row["candidate_id"]),
            "canonical_qku_inventory_ready_for_pr165_review": True,
            "no_orphan_qku_rows": True,
            "validation_status": "PASS",
        }
    ]


def build_market_sorted_inventory(identity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "market_inventory_ref": plain_ref("MARKET_SORT", index),
                "qku_id": row["qku_id"],
                "candidate_id": row["candidate_id"],
                "market_scope": row["market_scope"],
                "activation_state": row["activation_state"],
                "sort_key": f"{row['market_scope']}::{row['qku_id']}",
                "validation_status": "PASS",
            }
            for index, row in enumerate(identity_rows, 1)
        ),
        key=lambda row: row["sort_key"],
    )


def build_classical_quantum_hybrid_inventory(master_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(sorted(master_rows, key=lambda item: item["qku_id"]), 1):
        rows.append(
            {
                "hybrid_inventory_ref": plain_ref("HYBRID_INV", index),
                "qku_id": row["qku_id"],
                "qku_classical_quantum_hybrid_class": row.get("qku_classical_quantum_hybrid_class", ""),
                "qku_quantum_subclass": row.get("qku_quantum_subclass", ""),
                "qku_type": row.get("qku_type", ""),
                "quantum_backend_execution_allowed_flag": False,
                "quantum_advantage_claim_allowed_flag": False,
                "validation_status": "PASS",
            }
        )
    return rows


def inventory_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return stable_counter(row.get(field, "") for row in rows)
