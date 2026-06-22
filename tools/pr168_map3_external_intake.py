from __future__ import annotations

from tools.pr168_map3_config import ONLINE_SCOUT_ROWS, common_route


def build_external_source_rows() -> list[dict]:
    rows = []
    seen: set[str] = set()
    for source in ONLINE_SCOUT_ROWS:
        url = source["source_url"]
        if url in seen:
            continue
        seen.add(url)
        rows.append(
            {
                "external_source_row_id": f"EXTSRC_{len(rows) + 1:03d}",
                "source_url": url,
                "source_title": source["source_title"],
                "source_tier": source["source_tier"],
                "retrieved_at_utc": source["retrieved_at_utc"],
                "query_family_refs": [source["query_family"]],
                "candidate_only_flag": True,
                "accepted_truth_flag": False,
                "source_evidence_review_route": "SOURCE_EVIDENCE_REVIEW",
                "rejected_flag": source["rejected_flag"],
                "reject_reason_if_any": source["reject_reason_if_any"],
                **common_route("EXTERNAL_SOURCE_CANDIDATE_NON_PROOF"),
            }
        )
        rows[-1]["source_refs"] = [url]
    return rows


def build_external_intake_rows() -> list[dict]:
    rows = []
    for source in ONLINE_SCOUT_ROWS:
        row = {
            "external_candidate_id": f"EXT_{source['scout_row_id']}",
            "source_url": source["source_url"],
            "source_title": source["source_title"],
            "source_tier": source["source_tier"],
            "retrieved_at_utc": source["retrieved_at_utc"],
            "formula_name_candidate": source["scout_row_id"].lower(),
            "formula_family_candidate": source["formula_family_candidate"],
            "formula_expression_candidate_or_semantic_definition": source[
                "candidate_expression_or_semantic_definition"
            ],
            "required_inputs": source["required_inputs_candidate"],
            "optional_inputs": [],
            "applicable_venues": [source["query_family"].split("_")[0]],
            "applicable_market_types": ["binary_prediction_market", "event_contract"],
            "applicable_side": ["YES", "NO", "BOTH"],
            "unit_requirements": source["unit_requirements"],
            "data_requirement_contract_ref": f"DATAREQ_EXT_{source['scout_row_id']}",
            "possible_qku_family": source["formula_family_candidate"],
            "candidate_qku_id_or_new_id_route": "NEW_QTT_CANONICAL_QKU_ID_V1_CANDIDATE_ROUTE",
            "candidate_formula_id_or_new_id_route": "NEW_QTT_CANONICAL_FORMULA_ID_V1_CANDIDATE_ROUTE",
            "candidate_only_flag": True,
            "accepted_truth_flag": False,
            "proof_authority_class": "EXTERNAL_CANDIDATE_NON_PROOF",
            "source_evidence_review_route": source["source_evidence_review_route"],
            "replay_paper_route_if_computable": source["RP2_or_RANK2_route_if_computable"],
            "quantum_mapping_route_if_applicable": (
                "PR162E_Q_QUANTUM_MAPPING"
                if source["formula_family_candidate"] == "quantum_forward_optimization"
                else None
            ),
            "materialization_path": source["materialization_path"],
            "formula_intake_state": source["formula_intake_state"],
            "useful_formula_or_input_found_flag": source["useful_formula_or_input_found_flag"],
            "rejected_flag": source["rejected_flag"],
            "reject_reason_if_any": source["reject_reason_if_any"],
            **common_route("EXTERNAL_CANDIDATE_NON_PROOF"),
        }
        row["source_refs"] = [source["source_url"]]
        row["data_requirement_refs"] = [row["data_requirement_contract_ref"]]
        rows.append(row)
    return rows
