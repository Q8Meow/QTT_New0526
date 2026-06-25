#!/usr/bin/env python3
"""Legacy semantic supersession mapping for PR168-RP5B."""

from __future__ import annotations

from typing import Any


MAPPINGS: tuple[tuple[str, str, str, str], ...] = (
    ("FORMULA_REPAIR", "formula repair", "FORMULA_EXECUTION_ADAPTER_OR_INPUT_BINDING", "canonical formula mutation or profit-forcing repair permission"),
    ("QKU_REPAIR", "QKU repair", "QKU_EXECUTION_ROUTE_OR_TRADE_PLAN_BINDING", "canonical QKU mutation or permanent QKU defect label"),
    ("NEGATIVE_FORMULA", "negative formula", "CONDITION_SCOPED_NEGATIVE_OUTCOME_MEMORY", "global formula ban or permanent negative truth"),
    ("NO_TRADE_DOMINATED_FORMULA", "no-trade dominated formula", "NO_TRADE_ADVISED_FOR_THIS_CONTEXT_ONLY", "global or permanent no-trade dominance or replay exclusion"),
    ("UNSELECTED_FORMULA", "unselected formula", "NOT_SELECTED_IN_THIS_CONTEXT_ONLY", "global non-selection or permanent formula blocker"),
    ("FAILED_FORMULA", "failed formula", "FORMULA_STACK_OR_ORDER_PLAN_FAILED_UNDER_CONTEXT", "permanent formula failure or mutation mandate"),
    ("NON_COMPUTABLE_FORMULA", "non-computable formula", "PRESERVED_NEEDS_EXECUTION_CONTRACT", "permanent non-computability or library exclusion"),
    ("SOURCE_TRUTH", "source truth", "SOURCE_PROVENANCE_OR_AUTHORITY_BOUNDARY_LABEL_ONLY", "source-truth authority or live decision authority"),
    ("CHAMPION_LIVE_CANDIDATE", "champion/live candidate", "AUTHORITY_BOUNDARY_LABEL_ONLY_UNTIL_LAUNCH_GATES", "champion, live, source-truth, or order authority"),
)


def build_semantic_supersession_rows(wrong_term_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs_by_text: dict[str, list[str]] = {}
    for row in wrong_term_rows:
        text = str(row.get("term_text_or_regex", "")).lower()
        refs_by_text.setdefault(text, []).append(str(row.get("term_id", "")))
    rows: list[dict[str, Any]] = []
    for index, (family, term, interpretation, forbidden) in enumerate(MAPPINGS, start=1):
        refs = refs_by_text.get(term.lower(), [])
        if not refs and "/" in term:
            refs = [ref for key, values in refs_by_text.items() if any(part in key for part in term.lower().split("/")) for ref in values]
        rows.append(
            {
                "row_id": f"RP5B_SEMANTIC_SUPERSESSION_{index:04d}",
                "legacy_term_family": family,
                "legacy_term": term,
                "canonical_future_interpretation": interpretation,
                "forbidden_old_interpretation": forbidden,
                "allowed_future_consumers": [
                    "ActiveArtifactRegistryV1",
                    "LegacySemanticSupersessionV1",
                    "PR168_RP5C_IMMUTABLE_LIBRARY_RECLAIM",
                    "PR168_RP5D_REPLAY_PAPER_EXECUTABILITY",
                ],
                "validator_rule_required": "NoRawLegacyDecisionAuthority must reject direct trading authority from this legacy term.",
                "example_rp5a_refs": refs[:5] or ["PR168_RP5A_WrongConceptTermIndex"],
            }
        )
    return rows
