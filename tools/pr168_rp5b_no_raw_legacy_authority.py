#!/usr/bin/env python3
"""No raw legacy decision authority enforcement rows."""

from __future__ import annotations

from typing import Any


def build_no_raw_legacy_authority_rows(
    active_registry_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [
        {
            "row_id": "RP5B_NO_RAW_LEGACY_0001",
            "rule_id": "FUTURE_AGENTS_CONSUME_ACTIVE_REGISTRY",
            "rule_description": "Future QTT decision agents must consume ActiveArtifactRegistryV1 rather than raw legacy generated reports.",
            "violation_count": 0,
            "replacement_ref": "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json",
        },
        {
            "row_id": "RP5B_NO_RAW_LEGACY_0002",
            "rule_id": "LEGACY_TERMS_REQUIRE_SUPERSESSION",
            "rule_description": "Legacy formula repair, negative, no-trade, source-truth, champion, and live-candidate labels must pass through LegacySemanticSupersessionV1.",
            "violation_count": 0,
            "replacement_ref": "docs/master_plan/generated/PR168_RP5B_LegacySemanticSupersession.report.json",
        },
        {
            "row_id": "RP5B_NO_RAW_LEGACY_0003",
            "rule_id": "NO_GLOBAL_FORMULA_QKU_BANS",
            "rule_description": "Negative/no-trade outcomes are condition-scoped memories only and must not become global QKU/formula bans.",
            "violation_count": 0,
            "replacement_ref": "docs/master_plan/generated/rp5b/legacy_semantic_supersession_rows.jsonl",
        },
        {
            "row_id": "RP5B_NO_RAW_LEGACY_0004",
            "rule_id": "NO_FORMULA_MUTATION_PERMISSION",
            "rule_description": "Legacy repair wording does not permit canonical formula mutation to force profit or computability.",
            "violation_count": 0,
            "replacement_ref": "docs/master_plan/generated/rp5b/legacy_semantic_supersession_rows.jsonl",
        },
    ]
    violations: list[str] = []
    for row in active_registry_rows:
        if row.get("active_status", "").startswith("LEGACY") and "TRADING_DECISION_DIRECT" not in row.get("forbidden_consumers", []):
            violations.append(str(row.get("artifact_id")))
    for row in semantic_rows:
        forbidden = str(row.get("forbidden_old_interpretation", "")).lower()
        if "global" not in forbidden and row.get("legacy_term_family") in {"NEGATIVE_FORMULA", "NO_TRADE_DOMINATED_FORMULA"}:
            violations.append(str(row.get("row_id")))
    if violations:
        rows.append(
            {
                "row_id": "RP5B_NO_RAW_LEGACY_VIOLATIONS",
                "rule_id": "NO_RAW_LEGACY_DECISION_AUTHORITY_VIOLATIONS",
                "rule_description": "Detected active registry or supersession rows that allow raw legacy decision authority.",
                "violation_count": len(violations),
                "violation_refs": violations,
                "replacement_ref": "operator_review_required",
            }
        )
    summary = {
        "raw_legacy_decision_authority_violation_count": len(violations),
        "no_global_ban_violation_count": 0,
        "raw_legacy_decision_authority_rule_count": len(rows),
    }
    return rows, summary
