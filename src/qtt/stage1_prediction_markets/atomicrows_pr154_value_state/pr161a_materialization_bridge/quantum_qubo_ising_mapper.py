"""QUBO/Ising mapping candidate construction."""

from __future__ import annotations


def build_qubo_ising_mapping_candidates(profiles: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for profile in profiles:
        profile_type = str(profile["quantum_profile_type"])
        if profile_type.startswith(("QUBO_", "ISING_")):
            output.append(
                {
                    "mapping_candidate_id": f"PR161A_QUBO_ISING_MAPPING__{profile_type}",
                    "quantum_candidate_id": profile["quantum_candidate_id"],
                    "quantum_profile_type": profile_type,
                    "binary_domain": "BINARY_0_1",
                    "spin_domain": "SPIN_MINUS_ONE_PLUS_ONE",
                    "qubo_to_ising_decode_rule": "x=(z+1)/2",
                    "ising_to_qubo_encode_rule": "z=2x-1",
                    "constraint_penalty_candidate": "BOUND_GRID_1_TO_100",
                    "classical_baseline_formula_id": profile["classical_baseline_formula_id"],
                    "replay_paper_route_id": profile["replay_paper_route_id"],
                }
            )
    return output

