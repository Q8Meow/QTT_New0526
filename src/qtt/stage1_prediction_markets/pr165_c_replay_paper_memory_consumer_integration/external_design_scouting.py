"""Web-scouted candidate/provisional design notes for PR165-C."""

from __future__ import annotations

from .central_vocab import AUTHORITY_BOUNDARY_REF, NO_ORPHAN_STATUS

SCOUT_SOURCES = (
    {
        "source_url": "https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html",
        "source_title": "OCC model risk management revised guidance",
        "design_note": "Use independent validation, monitoring, governance, and role clarity as workflow separation inputs.",
        "mapped_pr165_c_use": "governance_model_quality_challenge_review",
    },
    {
        "source_url": "https://mlflow.org/docs/latest/ml/model-registry/",
        "source_title": "MLflow Model Registry",
        "design_note": "Use lineage, versioning, aliases, metadata, and annotations as registry-pattern inputs.",
        "mapped_pr165_c_use": "computable_payload_registry_lineage",
    },
    {
        "source_url": "https://qiskit-community.github.io/qiskit-algorithms/tutorials/05_qaoa.html",
        "source_title": "Qiskit QAOA tutorial",
        "design_note": "Route QAOA candidates to comparator review; do not execute quantum backends in PR165-C.",
        "mapped_pr165_c_use": "quantum_consumer_route",
    },
    {
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html",
        "source_title": "D-Wave Ocean dimod model classes",
        "design_note": "Route BQM/CQM/DQM model-class fit as advisory formulation metadata.",
        "mapped_pr165_c_use": "quantum_model_class_candidate",
    },
    {
        "source_url": "https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/generated/dimod.cqm_to_bqm.html",
        "source_title": "D-Wave cqm_to_bqm conversion",
        "design_note": "Record penalty-conversion requirements as repair/review actions when CQM constraints need BQM conversion.",
        "mapped_pr165_c_use": "penalty_scale_candidate_action",
    },
    {
        "source_url": "https://docs.dwavequantum.com/en/latest/concepts/penalty.html",
        "source_title": "D-Wave penalty models",
        "design_note": "Represent constraint-penalty conversion as formulation repair metadata, not backend execution.",
        "mapped_pr165_c_use": "quantum_formulation_repair_route",
    },
)


def build_design_scout_rows() -> list[dict[str, object]]:
    rows = []
    for index, source in enumerate(SCOUT_SOURCES, start=1):
        rows.append(
            {
                "design_scout_candidate_id": f"PR165_C_DESIGN_SCOUT::{index:04d}",
                **source,
                "scout_status": "WEB_SCOUTED_CANDIDATE_PROVISIONAL_DESIGN_NOTE",
                "candidate_confidence_tier": "DESIGN_REFERENCE_ONLY",
                "provenance_label": "WEB_SCOUT_SOURCE_REFERENCED_BY_CODEX_ON_2026_06_09",
                "replay_paper_route": "DESIGN_PATTERN_ONLY_NO_RESULT_CLAIM",
                "downstream_pr_route": "PR165-D",
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows


def build_candidate_value_rows() -> list[dict[str, object]]:
    rows = []
    for index, source in enumerate(SCOUT_SOURCES, start=1):
        rows.append(
            {
                "web_scout_candidate_value_id": f"PR165_C_WEB_SCOUT_VALUE::{index:04d}",
                "source_url": source["source_url"],
                "candidate_value_or_formula": source["design_note"],
                "value_lane": "CANDIDATE_PROVISIONAL_DESIGN_VALUE",
                "provenance_label": "WEB_SCOUT_SOURCE_REFERENCED_BY_CODEX_ON_2026_06_09",
                "candidate_confidence_tier": "DESIGN_REFERENCE_ONLY",
                "replay_paper_route": "REPLAY_PAPER_CONSUMER_DESIGN_REVIEW_ONLY",
                "downstream_pr_route": "PR165-D",
                "owner_review_needed_flag": False,
                "no_orphan_status": NO_ORPHAN_STATUS,
                "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                "validation_status": "PASS",
            }
        )
    return rows
