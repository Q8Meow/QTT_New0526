"""Central RP5E tunable parameter registry."""

from __future__ import annotations

from .models import generated_ref, with_common

BOOTSTRAP_PARAMETERS: tuple[dict[str, object], ...] = (
    {"parameter_name": "max_roles_per_stack", "value_or_range": "3..8", "default_value": 5, "unit": "role_count"},
    {"parameter_name": "max_formulas_per_stack", "value_or_range": "2..8", "default_value": 5, "unit": "formula_count"},
    {"parameter_name": "hot_max_previews_per_context", "value_or_range": "25..100", "default_value": 50, "unit": "preview_count"},
    {"parameter_name": "warm_max_previews_per_context", "value_or_range": "100..500", "default_value": 250, "unit": "preview_count"},
    {"parameter_name": "cold_max_previews_per_context", "value_or_range": "500..2000", "default_value": 1000, "unit": "preview_count"},
    {"parameter_name": "topk_hot", "value_or_range": "5..20", "default_value": 10, "unit": "preview_count"},
    {"parameter_name": "topk_warm", "value_or_range": "20..100", "default_value": 50, "unit": "preview_count"},
    {"parameter_name": "topk_cold", "value_or_range": "50..200", "default_value": 100, "unit": "preview_count"},
    {"parameter_name": "near_clone_jaccard_threshold", "value_or_range": "0.80..0.95", "default_value": "0.90", "unit": "ratio"},
    {"parameter_name": "role_coverage_min", "value_or_range": "0.60..1.00", "default_value": "0.80", "unit": "ratio"},
    {"parameter_name": "fdr_q_default", "value_or_range": "0.10", "default_value": "0.10", "unit": "q"},
    {"parameter_name": "fdr_q_sensitivity", "value_or_range": "[0.05,0.10,0.20]", "default_value": "[0.05,0.10,0.20]", "unit": "q"},
    {"parameter_name": "successive_halving_eta", "value_or_range": "3", "default_value": 3, "unit": "eta"},
    {"parameter_name": "exploit_vs1_rp5d_ready_weight", "value_or_range": "0.70", "default_value": "0.70", "unit": "ratio"},
    {"parameter_name": "diversity_challenger_weight", "value_or_range": "0.20", "default_value": "0.20", "unit": "ratio"},
    {"parameter_name": "cold_research_expansion_weight", "value_or_range": "0.10", "default_value": "0.10", "unit": "ratio"},
    {"parameter_name": "w_role", "value_or_range": "0.18", "default_value": "0.18", "unit": "score_weight"},
    {"parameter_name": "w_data", "value_or_range": "0.12", "default_value": "0.12", "unit": "score_weight"},
    {"parameter_name": "w_tca", "value_or_range": "0.11", "default_value": "0.11", "unit": "score_weight"},
    {"parameter_name": "w_latency", "value_or_range": "0.09", "default_value": "0.09", "unit": "score_weight"},
    {"parameter_name": "w_capacity", "value_or_range": "0.10", "default_value": "0.10", "unit": "score_weight"},
    {"parameter_name": "w_diversity", "value_or_range": "0.10", "default_value": "0.10", "unit": "score_weight"},
    {"parameter_name": "w_quantum", "value_or_range": "0.09", "default_value": "0.09", "unit": "score_weight"},
    {"parameter_name": "w_fallback", "value_or_range": "0.08", "default_value": "0.08", "unit": "score_weight"},
    {"parameter_name": "w_edge", "value_or_range": "0.13", "default_value": "0.13", "unit": "score_weight"},
    {"parameter_name": "w_duplicate", "value_or_range": "0.08", "default_value": "0.08", "unit": "score_weight"},
    {"parameter_name": "w_overfit", "value_or_range": "0.07", "default_value": "0.07", "unit": "score_weight"},
    {"parameter_name": "w_blocker", "value_or_range": "0.10", "default_value": "0.10", "unit": "score_weight"},
)


def build_parameter_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, item in enumerate(BOOTSTRAP_PARAMETERS, start=1):
        rows.append(
            with_common(
                {
                    **item,
                    "parameter_id": f"RP5E_PARAM_{index:04d}",
                    "default_scope": "STACK_PREVIEW_AND_PRESCREEN_ONLY",
                    "policy_provenance_ref": f"RP5E_POLICY_PROV_{index:04d}",
                    "profit_proof_flag": False,
                    "live_default_flag": False,
                    "replay_paper_verification_required": True,
                },
                row_id=f"RP5E_PARAM_{index:04d}",
                owner_agent="GovernanceAgent",
                consumer_agents=["StackGeneratorAgent", "RP5EValidator"],
                upstream_refs=["docs/master_plan/QTT_MasterPlan_Current.md"],
                downstream_refs=[generated_ref("policy_prov.jsonl"), generated_ref("prescreen.jsonl")],
            )
        )
    return rows


def parameter_defaults() -> dict[str, object]:
    return {str(row["parameter_name"]): row["default_value"] for row in BOOTSTRAP_PARAMETERS}
