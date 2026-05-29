"""Non-blocking online scout candidate enrichment records.

The builder records deterministic public-source locator candidates without
performing live network fetches, so CI remains independent from online access.
"""

from __future__ import annotations

from typing import Any

from . import constants as c


PUBLIC_SCOUT_LOCATORS = (
    ("ONLINE_SCOUT_QUBO_ISING_DOCS", "QUBO and Ising model optimizer documentation locator candidate", "QUANTUM", "QUBO_ISING"),
    ("ONLINE_SCOUT_QAOA_DOCS", "QAOA algorithm documentation locator candidate", "QUANTUM", "QAOA"),
    ("ONLINE_SCOUT_VQE_DOCS", "VQE algorithm documentation locator candidate", "QUANTUM", "VQE"),
    ("ONLINE_SCOUT_ANNEALING_DOCS", "simulated and quantum annealing documentation locator candidate", "QUANTUM", "ANNEALING"),
    ("ONLINE_SCOUT_OPTIMIZER_DEFAULTS", "classical optimizer default and tolerance documentation locator candidate", "GENERAL", "OPTIMIZER"),
    ("ONLINE_SCOUT_TRADING_RESEARCH", "prediction-market strategy and microstructure research locator candidate", "GENERAL", "STRATEGY"),
)


def build_online_scout_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    residual_names = [item["normalized_candidate_name"] for item in candidates if item.get("residual_gap_flag")]
    output: list[dict[str, Any]] = []
    for index, (locator_id, label, scope, family) in enumerate(PUBLIC_SCOUT_LOCATORS, start=1):
        output.append(
            {
                "online_scout_candidate_id": f"PR161B_ONLINE_SCOUT_{index:03d}",
                "source_locator_candidate_id": locator_id,
                "candidate_label": label,
                "candidate_family": family,
                "scope": scope,
                "source_intake_state": c.SourceIntakeState.SOURCE_ATTRIBUTION_INCOMPLETE_CANDIDATE.value,
                "online_network_fetch_attempted_flag": False,
                "ci_dependency_flag": False,
                "official_fact_created_flag": False,
                "profit_evidence_created_flag": False,
                "live_use_allowed_flag": False,
                "recommended_fill_lane": c.AssimilationFillLane.FILL_REQUIRES_PR161C_ONLINE_RESEARCH.value,
                "residual_candidate_names_for_possible_enrichment": residual_names[:50],
            }
        )
    return output


def quantum_online_scout_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record["scope"] == "QUANTUM"]
