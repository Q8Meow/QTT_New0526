from __future__ import annotations

from collections import Counter

from tools.pr168_map3_config import MANDATORY_FORMULA_FAMILIES, ONLINE_SCOUT_ROWS, common_route


def build_family_matrix_rows() -> list[dict]:
    counts = Counter(row["formula_family_candidate"] for row in ONLINE_SCOUT_ROWS)
    rows = []
    for family in MANDATORY_FORMULA_FAMILIES:
        covered = counts.get(family, 0) > 0
        row = {
            "formula_family_matrix_row_id": f"FAM_{family.upper()}",
            "formula_family": family,
            "coverage_state": "COVERED" if covered else "EXACT_GAP_ROUTED",
            "mandatory_formula_family_status": "COVERED" if covered else "EXACT_GAP_ROUTED",
            "source_candidate_count": counts.get(family, 0),
            "materialized_or_gap_requirement_met_flag": True,
            "exact_gap_route_if_any": None if covered else "SOURCE_EVIDENCE_REVIEW_REQUIRED",
            "candidate_only_flag": True,
            "accepted_truth_flag": False,
            **common_route("FORMULA_FAMILY_COVERAGE_NON_PROOF"),
        }
        rows.append(row)
    return rows
