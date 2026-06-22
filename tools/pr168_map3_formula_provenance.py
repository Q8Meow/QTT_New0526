from __future__ import annotations

from collections import Counter

from tools.pr168_map3_config import ONLINE_SCOUT_ROWS, common_route


def build_formula_provenance_rows() -> list[dict]:
    family_counts = Counter(row["formula_family_candidate"] for row in ONLINE_SCOUT_ROWS)
    rows = []
    for source in ONLINE_SCOUT_ROWS:
        row = {
            "formula_provenance_id": f"PROV_{source['scout_row_id']}",
            "formula_family_candidate": source["formula_family_candidate"],
            "source_url": source["source_url"],
            "source_count": family_counts[source["formula_family_candidate"]],
            "source_family_count": 1,
            "official_source_count": 1 if source["source_tier"] == "OFFICIAL_PUBLIC_DOC_CANDIDATE" else 0,
            "research_source_count": 1 if source["source_tier"] == "RESEARCH_PAPER_CANDIDATE" else 0,
            "institutional_source_count": 1 if source["source_tier"] == "INSTITUTIONAL_METHOD_CANDIDATE" else 0,
            "open_source_source_count": 1 if source["source_tier"] == "OPEN_SOURCE_DOC_CANDIDATE" else 0,
            "social_or_discussion_source_count": 1 if source["source_tier"] == "SOCIAL_OR_DISCUSSION_CANDIDATE" else 0,
            "owner_submitted_source_count": 0,
            "triangulation_state": (
                "MULTI_SOURCE_CANDIDATE"
                if family_counts[source["formula_family_candidate"]] > 1
                else "SINGLE_SOURCE_CANDIDATE"
            ),
            "candidate_only_flag": True,
            "accepted_truth_flag": False,
            "source_evidence_review_route": "SOURCE_EVIDENCE_REVIEW",
            **common_route("FORMULA_PROVENANCE_CANDIDATE_NON_PROOF"),
        }
        row["source_refs"] = [source["source_url"]]
        rows.append(row)
    return rows
