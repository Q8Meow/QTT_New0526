"""Open research source intake records for PR159S."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_open_research_source_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    sources_by_id = {str(source["source_id"]): source for source in c.RESEARCH_SOURCE_CATALOG}
    for target in classified_targets:
        source_id = target.get("assigned_research_source_id")
        if not source_id:
            continue
        source = sources_by_id[str(source_id)]
        records.append(
            {
                "intake_record_id": f"PR159S_OPEN_RESEARCH_INTAKE__{len(records)+1:04d}",
                "target_id_or_row_id": target["target_id_or_row_id"],
                "source_id": source_id,
                "source_url": source["source_locator"],
                "title": source["title"],
                "author_or_handle_if_available": source["author_or_handle"],
                "publication_time_if_available": source["publication_time_if_available"],
                "retrieval_time_utc": c.RETRIEVAL_TIMESTAMP_UTC,
                "source_class": source["source_class"],
                "source_quality_tier": source["source_quality_tier"],
                "source_risk_tier": target["source_risk_tier"],
                "authority_class": target["authority_class"],
                "source_provenance_tag": target["source_provenance_tag"],
                "profit_validation_tag": target["profit_validation_tag"],
                "target_mapping": {
                    "target_field_id": target["target_field_id"],
                    "target_population": target["target_population"],
                    "terminal_completion_state": target["terminal_completion_state"],
                },
                "claim_summary": "Open research source creates candidate intelligence only; it is not an official venue fact or profit result.",
                "candidate_extraction": target["field_value"],
                "author_identity_known_flag": target["author_identity_known_flag"],
                "reproducibility_level": target["reproducibility_level"],
                "evidence_strength": target["evidence_strength"],
                "hallucination_risk": target["hallucination_risk"],
                "manipulation_risk": target["manipulation_risk"],
                "duplicate_or_near_duplicate_status": target["duplicate_or_near_duplicate_status"],
                "replay_paper_required_flag": True,
                "live_use_forbidden_until_promoted_flag": True,
                "external_code_executed_flag": False,
                "external_repo_cloned_flag": False,
                "package_install_script_executed_flag": False,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records

