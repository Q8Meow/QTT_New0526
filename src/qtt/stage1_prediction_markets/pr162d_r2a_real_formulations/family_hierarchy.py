"""Family/subfamily/variant hierarchy for PR162D-R2A."""

from __future__ import annotations

from typing import Any


def build_family_hierarchy(formulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for record in formulations:
        key = (record["domain_family_key"], record["subfamily_key"], record["variant_key"])
        row = rows.setdefault(
            key,
            {
                "hierarchy_id": f"PR162D_R2A_FAMILY::{key[0]}::{key[1]}::{key[2]}",
                "domain_family_key": key[0],
                "subfamily_key": key[1],
                "variant_key": key[2],
                "formulation_refs": [],
                "raw_mention_refs": [
                    f"docs/master_plan/QTT_MasterPlan_Current.md#normalized::{key[0]}::{key[1]}::{key[2]}"
                ],
                "route_state": "FORMULATION_FIRST_MAPPED",
                "exact_fill_action_refs": [],
                "mapping_attempted_flag": True,
                "formulation_unmapped_flag": False,
                "live_order_authority": False,
            },
        )
        row["formulation_refs"].append(record["formulation_id"])
    return [
        {**row, "formulation_refs": sorted(set(row["formulation_refs"]))}
        for row in sorted(rows.values(), key=lambda item: item["hierarchy_id"])
    ]
