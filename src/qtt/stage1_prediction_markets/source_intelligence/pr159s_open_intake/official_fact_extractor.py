"""Official fact delta extraction for PR159S."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_official_fact_delta_records(classified_targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in classified_targets:
        if target["source_provenance_tag"] != c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value:
            continue
        records.append(
            {
                "official_delta_record_id": f"PR159S_OFFICIAL_PENDING__{len(records)+1:04d}",
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_field_path": target["target_field_id"],
                "source_provenance_tag": target["source_provenance_tag"],
                "authority_class": target["authority_class"],
                "source_class": target["source_class"],
                "official_confirmed_flag": False,
                "accepted_official_external_fact_created_flag": False,
                "official_source_packet_id": None,
                "official_source_locator": None,
                "exact_field_future_route": "official_source_exact_field_verification_required_before_live_or_connector_use",
                "source_artifact_path": target["source_artifact_path"],
                "profit_validation_tag": target["profit_validation_tag"],
                "no_fake_official_fact_confirmation": True,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records

