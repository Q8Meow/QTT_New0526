"""Policy/default provenance rows for RP5E."""

from __future__ import annotations

from .models import generated_ref, with_common
from .policy_parameters import BOOTSTRAP_PARAMETERS


def build_policy_provenance_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, item in enumerate(BOOTSTRAP_PARAMETERS, start=1):
        rows.append(
            with_common(
                {
                    "policy_provenance_id": f"RP5E_POLICY_PROV_{index:04d}",
                    "parameter_name": item["parameter_name"],
                    "parameter_family": "stack_generator_budget" if "max" in str(item["parameter_name"]) or "topk" in str(item["parameter_name"]) else "preview_prescreen_policy",
                    "value_or_range": item["value_or_range"],
                    "unit": item["unit"],
                    "default_scope": "RP5E_STACK_PREVIEW_ONLY",
                    "provenance_tier": "MASTER_PLAN_RECORDED_DEFAULT",
                    "source_refs": ["docs/master_plan/QTT_MasterPlan_Current.md"],
                    "owner_default_flag": False,
                    "clean_room_flag": False,
                    "replay_paper_verification_required": True,
                    "calibration_status": "FUTURE_REPLAY_PAPER_CALIBRATION_REQUIRED",
                    "paper_authority_flag": False,
                    "shadow_authority_flag": False,
                    "live_authority_flag": False,
                    "profit_proof_flag": False,
                    "proprietary_claim_flag": False,
                    "downstream_consumers": ["StackGeneratorAgent", "RP5G", "RANK4", "QOPT1"],
                    "rollback_policy_ref": "RP5E_ROLLBACK::REMOVE_DEFAULT_FROM_PARAMS_AND_REBUILD",
                    "calibration_handoff_ref": "calib_queue.jsonl",
                    "inference_method": "PROMPT_BOOTSTRAP_POLICY_TRANSCRIPTION",
                },
                row_id=f"RP5E_POLICY_PROV_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=[generated_ref("params.jsonl")],
                downstream_refs=[generated_ref("calib_queue.jsonl")],
            )
        )
    return rows
