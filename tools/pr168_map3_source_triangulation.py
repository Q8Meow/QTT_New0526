from __future__ import annotations

from collections import defaultdict

from tools.pr168_map3_config import ONLINE_SCOUT_ROWS, common_route


def build_source_triangulation_rows() -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in ONLINE_SCOUT_ROWS:
        grouped[row["formula_family_candidate"]].append(row)
    rows = []
    for family, sources in sorted(grouped.items()):
        tiers = sorted({source["source_tier"] for source in sources})
        state = (
            "OFFICIAL_PLUS_RESEARCH_CANDIDATE"
            if "OFFICIAL_PUBLIC_DOC_CANDIDATE" in tiers and "RESEARCH_PAPER_CANDIDATE" in tiers
            else "MULTI_SOURCE_CANDIDATE"
            if len(sources) > 1
            else "SINGLE_SOURCE_CANDIDATE"
        )
        row = {
            "source_triangulation_row_id": f"TRI_{family.upper()}",
            "formula_family_candidate": family,
            "source_count": len(sources),
            "source_family_count": len(tiers),
            "source_tiers": tiers,
            "source_urls": sorted({source["source_url"] for source in sources}),
            "triangulation_state": state,
            "candidate_only_flag": True,
            "accepted_truth_flag": False,
            "source_evidence_review_route": "SOURCE_EVIDENCE_REVIEW",
            **common_route("SOURCE_TRIANGULATION_CANDIDATE_NON_PROOF"),
        }
        row["source_refs"] = row["source_urls"]
        rows.append(row)
    return rows
