"""Candidate-only clean-room default lanes."""

from __future__ import annotations

from .models import generated_ref, with_common


DEFAULT_CANDIDATES = (
    {
        "parameter_name": "latency_budget_bucket_ms",
        "inferred_value_or_range": "100..1000",
        "unit": "millisecond_bucket",
        "inference_method": "PUBLIC_RESEARCH_DERIVED_AND_CLEAN_ROOM_BUCKETIZATION",
        "confidence_bucket": "MEDIUM_CANDIDATE_ONLY",
        "alternative_explanations": ["venue latency differs", "connector surface not accepted", "network path unknown"],
    },
    {
        "parameter_name": "thin_book_depth_bucket",
        "inferred_value_or_range": "low|medium|high",
        "unit": "ordinal_bucket",
        "inference_method": "CLEAN_ROOM_INFERRED_INSTITUTIONAL_STYLE_CANDIDATE",
        "confidence_bucket": "LOW_CANDIDATE_ONLY",
        "alternative_explanations": ["event-specific liquidity", "time-to-close effect", "venue-specific tick and min-size not accepted"],
    },
    {
        "parameter_name": "capacity_size_sensitivity_bucket",
        "inferred_value_or_range": "small|moderate|large_preview_only",
        "unit": "ordinal_bucket",
        "inference_method": "PUBLIC_INSTITUTIONAL_PRACTICE_CANDIDATE",
        "confidence_bucket": "LOW_CANDIDATE_ONLY",
        "alternative_explanations": ["portfolio exposure constraints", "crowding regime", "future RP5F size grid required"],
    },
)


def build_clean_room_default_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, item in enumerate(DEFAULT_CANDIDATES, start=1):
        rows.append(
            with_common(
                {
                    "candidate_default_id": f"RP5E_DEFAULT_CAND_{index:04d}",
                    **item,
                    "default_scope": "RP5E_STACK_PREVIEW_ONLY",
                    "provenance_tier": "CLEAN_ROOM_INFERRED_INSTITUTIONAL_STYLE_CANDIDATE",
                    "public_or_observable_inputs": ["public research receipts", "repo-local RP5D readiness buckets"],
                    "source_refs": [generated_ref("research_rec.jsonl"), generated_ref("policy_prov.jsonl")],
                    "owner_default_flag": False,
                    "clean_room_flag": True,
                    "nda_or_confidential_input_flag": False,
                    "improper_access_flag": False,
                    "proprietary_claim_flag": False,
                    "replay_paper_verification_required": True,
                    "paper_authority_flag": False,
                    "shadow_authority_flag": False,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                    "downstream_calibration_plan": "calib_queue.jsonl",
                    "downstream_consumers": ["RP5G", "RANK4", "QOPT1"],
                    "rollback_policy_ref": "RP5E_ROLLBACK::DROP_CANDIDATE_DEFAULT",
                    "calibration_handoff_ref": "calib_queue.jsonl",
                },
                row_id=f"RP5E_DEFAULT_CAND_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("research_rec.jsonl")],
                downstream_refs=[generated_ref("calib_queue.jsonl"), generated_ref("re_handoff.report.json")],
            )
        )
    return rows


def build_calibration_queue_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, item in enumerate(DEFAULT_CANDIDATES, start=1):
        rows.append(
            with_common(
                {
                    "calibration_queue_id": f"RP5E_CALIB_QUEUE_{index:04d}",
                    "parameter_name": item["parameter_name"],
                    "candidate_default_ref": f"RP5E_DEFAULT_CAND_{index:04d}",
                    "required_future_pr": "RP5G",
                    "calibration_status": "REPLAY_PAPER_VERIFICATION_REQUIRED",
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                },
                row_id=f"RP5E_CALIB_QUEUE_{index:04d}",
                owner_agent="ResearchScoutAgent",
                consumer_agents=["RP5G", "GovernanceAgent"],
                upstream_refs=[generated_ref("default_cand.jsonl")],
                downstream_refs=[generated_ref("re_handoff.report.json")],
            )
        )
    return rows
