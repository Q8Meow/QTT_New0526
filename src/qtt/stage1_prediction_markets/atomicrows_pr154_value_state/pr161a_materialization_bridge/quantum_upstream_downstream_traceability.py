"""Quantum upstream/downstream traceability construction."""

from __future__ import annotations

from . import constants as c


def build_quantum_traceability(profiles: list[dict[str, object]]) -> list[dict[str, object]]:
    upstream = [path.as_posix() for path in c.UPSTREAM_QUANTUM_ARTIFACT_PATHS]
    return [
        {
            "traceability_record_id": f"PR161A_QUANTUM_TRACE__{profile['quantum_candidate_id']}",
            "quantum_candidate_id": profile["quantum_candidate_id"],
            "upstream_pr_labels_consumed": ["PR82", "PR83", "PR84", "PR85", "PR86", "PR136", "PR137R", "PR138", "PR154", "PR159S"],
            "upstream_artifact_paths": upstream,
            "upstream_atomicrows_row_id": profile["atomicrows_row_ids"][0],
            "upstream_pr154_target_id": profile["pr154_target_ids"][0],
            "upstream_quantum_applicability_record_id": "QuantumApplicabilityClassificationRegistry.report.json",
            "upstream_owner_quantum_priority_record_id": "OwnerQuantumPriorityPolicyRegistry.report.json",
            "upstream_scoring_policy_record_id": "ParameterAlgorithmScoringPolicyRegistry.report.json",
            "upstream_optimizer_arbitration_record_id": "QuantumClassicalOptimizerArbitrationGate.report.json",
            "upstream_command_action_matrix_route": "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
            "upstream_market_specific_launch_readiness_route": "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
            "upstream_atomicrows_semantic_contract_link": "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
            "downstream_pr_targets": list(c.PR87_PR92_FLOW),
            "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "source_provenance_tag": "QTT_PR161A_OWNER_APPROVED_QUANTUM_CANDIDATE_DEFAULT",
        }
        for profile in profiles
    ]

