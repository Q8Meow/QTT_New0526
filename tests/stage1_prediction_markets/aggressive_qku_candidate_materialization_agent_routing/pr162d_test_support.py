from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.json_io import (
    read_json,
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.paths import (
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.quantum_execution.objective_value_calculator import (
    ising_objective_value,
    qubo_objective_value,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.quantum_execution.local_exact_ising_solver import (
    solve_ising_exact,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.quantum_execution.local_exact_qubo_solver import (
    solve_qubo_exact,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.quantum_execution.qiskit_adapter_optional import (
    qiskit_adapter,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.quantum_execution.dwave_ocean_adapter_optional import (
    dwave_ocean_adapter,
)
from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.validator import (
    validate_artifacts,
)
from tools import ci_branch_context, run_validation_gates


REPO_ROOT = Path(__file__).resolve().parents[3]


def report(filename: str) -> dict[str, Any]:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


def records(filename: str) -> list[dict[str, Any]]:
    payload = report(filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest_records = {
        record["report_filename"]: record
        for record in records_from_payload(report(c.SHARD_MANIFEST_REPORT_FILENAME))
    }
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_records[filename]["shard_files"]:
        rows.extend(records_from_payload(read_json(resolve_repo_relative(REPO_ROOT, shard_ref))))
    return rows


def summary() -> dict[str, Any]:
    return report("PR162D_FinalSummary.report.json")


def assert_validator_ok() -> None:
    result = validate_artifacts(REPO_ROOT)
    assert result.ok, result.failures


def assert_pr162c_records_consumed() -> None:
    assert_validator_ok()
    s = summary()
    assert s["pr162c_records_consumed"] == 6502
    assert s["candidate_materialization_target_count"] == 6502


def assert_no_blocker_carryover() -> None:
    s = summary()
    ledger = records("PR162D_PR162CBlockerReinterpretationLedger.report.json")
    assert s["generic_required_fields_blocker_remaining_count"] == 0
    assert all(record["acquisition_blocker_flag"] is False for record in ledger)
    assert all(record["generic_required_fields_blocker_remaining_flag"] is False for record in ledger)


def assert_candidate_progress_states() -> None:
    ledger = records("PR162D_PR162CBlockerReinterpretationLedger.report.json")
    statuses = {record["pr162d_progress_status"] for record in ledger}
    assert statuses <= set(c.CANDIDATE_PROGRESS_STATUSES)
    assert "CANDIDATE_FIELD_FILLED_PARTIAL" in statuses
    assert "CANDIDATE_REPLAY_PAPER_ROUTED" in statuses
    assert "CANDIDATE_AGENT_ROUTED_PARTIAL" in statuses


def assert_materialization_candidates() -> None:
    formulas = records("PR162D_QKUFormulaMaterializationExpansion.report.json")
    algorithms = records("PR162D_QKUAlgorithmMaterializationExpansion.report.json")
    parameters = records("PR162D_QKUParameterValueFieldFillExpansion.report.json")
    solvers = records("PR162D_QKUSolverInputAssemblyExpansion.report.json")
    assert formulas and algorithms and parameters and solvers
    assert all(record["expression"] for record in formulas + algorithms + parameters)
    assert all(record["executable_function_reference_or_planned_function_reference"] for record in formulas + algorithms + parameters)


def assert_no_metadata_only() -> None:
    audit = records("PR162D_NoMetadataOnlyMaterializationAudit.report.json")[0]
    assert audit["metadata_only_materialization_pass_count"] == 0


def assert_non_official_replay_paper() -> None:
    non_official = records("PR162D_NonOfficialCandidateIntakeRegistry.report.json")
    assert non_official
    assert all(record["candidate_or_provisional_flag"] for record in non_official)
    assert all(record["replay_paper_candidate_flag"] for record in non_official)


def assert_source_quality_priority() -> None:
    policy = records("PR162D_SourceQualityPolicy.report.json")[0]
    ladder = records("PR162D_SourcePriorityLadder.report.json")
    assert policy["source_quality_is_priority_not_gate_flag"] is True
    assert all(record["acquisition_gate_flag"] is False for record in ladder)


def assert_source_tier_fields() -> None:
    sources = records("PR162D_CandidateSourceIntakeRegistry.report.json")
    required = {
        "source_tier",
        "source_class",
        "source_quality_score",
        "authority_class",
        "confidence_class",
        "official_truth_flag",
        "candidate_or_provisional_flag",
        "replay_paper_candidate_flag",
        "source_locator",
        "source_capture_digest_or_locator_digest",
        "qku_refs",
        "formula_refs",
        "field_refs",
        "agent_route_refs",
    }
    assert sources
    assert all(required <= set(record) for record in sources)


def assert_no_acquisition_gate_regression() -> None:
    audit = records("PR162D_NoAcquisitionGateRegressionAudit.report.json")[0]
    assert audit["candidate_materialization_target_count"] == 6502
    assert audit["generic_required_fields_blocker_remaining_count"] == 0
    assert audit["non_official_source_quality_gate_count"] == 0
    assert audit["partial_field_missing_gate_count"] == 0


def assert_agent_routes_every_qku() -> None:
    ledger = records("PR162D_PR162CBlockerReinterpretationLedger.report.json")
    routes = records("PR162D_AgentConsumableQKURoutingMatrix.report.json")
    assert len(ledger) == len(routes) == 6502
    assert {record["qku_id"] for record in ledger} == {record["qku_id"] for record in routes}


def assert_no_orphans() -> None:
    audit = records("PR162D_NoOrphanQKUFormulaDatasetAgentAudit.report.json")[0]
    assert audit["orphan_count"] == 0


def assert_quantum_models_computable() -> None:
    models = records("PR162D_QuantumProblemModelRegistry.report.json")
    assert any(record["problem_model_type"] == "QUBO" for record in models)
    assert any(record["problem_model_type"] == "ISING" for record in models)
    assert all(record["objective_expression"] for record in models)
    assert all(record["strongest_classical_comparator"] for record in models)


def assert_qubo_smoke() -> None:
    result = solve_qubo_exact([[-1.0, -0.25], [-0.25, -0.5]])
    smoke = records("PR162D_QUBOIsingLocalExactSmokeExecution.report.json")
    assert result["best_assignment"] == [1, 1]
    assert any(record["problem_model_type"] == "QUBO" for record in smoke)


def assert_ising_smoke() -> None:
    result = solve_ising_exact([0.2, -0.4], [(0, 1, 0.15)])
    smoke = records("PR162D_QUBOIsingLocalExactSmokeExecution.report.json")
    assert result["best_assignment"] == [-1, 1]
    assert any(record["problem_model_type"] == "ISING" for record in smoke)


def assert_quantum_objective_values() -> None:
    models = records("PR162D_QuantumProblemModelRegistry.report.json")
    smoke = records("PR162D_QUBOIsingLocalExactSmokeExecution.report.json")
    by_id = {record["problem_model_id"]: record for record in models}
    for record in smoke:
        model = by_id[record["problem_model_ref"]]
        result = record["result"]
        if record["problem_model_type"] == "QUBO":
            value = qubo_objective_value(result["best_assignment"], model["objective_coefficients"]["Q"])
        else:
            coeffs = model["objective_coefficients"]
            value = ising_objective_value(result["best_assignment"], coeffs["h"], coeffs["J"])
        assert value == result["best_objective_value"]


def assert_quantum_constraints_penalties() -> None:
    smoke = records("PR162D_QUBOIsingLocalExactSmokeExecution.report.json")
    qubo = next(record for record in smoke if record["problem_model_type"] == "QUBO")
    feasibility = qubo["result"]["constraint_feasibility"]
    penalty = qubo["result"]["penalty_validation"]
    assert feasibility["feasible_flag"] is False
    assert penalty["penalty_valid_flag"] is True


def assert_optional_adapters_import() -> None:
    assert qiskit_adapter().dry_run_only is True
    assert dwave_ocean_adapter().dry_run_only is True


def assert_provider_dry_run() -> None:
    payloads = records("PR162D_QuantumProviderDryRunPayloadRegistry.report.json")
    assert payloads
    assert all(record["dry_run_flag"] for record in payloads)
    assert all(record["remote_submission_attempted_flag"] is False for record in payloads)


def assert_remote_not_required_for_ci() -> None:
    modes = records("PR162D_QuantumExecutionModeRegistry.report.json")
    deps = records("PR162D_QuantumBackendDependencyStatus.report.json")
    assert all(record["remote_execution_required_for_ci_flag"] is False for record in modes)
    assert all(record.get("remote_execution_required_flag", False) is False for record in deps if "remote_execution_required_flag" in record)


def assert_quantum_routes() -> None:
    routes = records("PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json")
    assert routes
    for record in routes:
        assert "QUANTUM_ADVISORY_AGENT" in record["agent_path_refs"]
        assert "QUANTUM_EXECUTION_HARNESS" in record["agent_path_refs"]
        assert "QUANTUM_CLASSICAL_HYBRID_COMPARATOR" in record["agent_path_refs"]
        assert "REPLAY_PAPER_CANDIDATE_ROUTER" in record["agent_path_refs"]


def assert_quantum_no_live_order() -> None:
    audit = records("PR162D_QuantumNoLiveOrderAuthorityAudit.report.json")[0]
    routes = records("PR162D_QuantumReplayPaperCandidateRouteMatrix.report.json")
    assert audit["quantum_direct_live_order_submission_count"] == 0
    assert all(record["direct_live_order_submission_flag"] is False for record in routes)


def assert_quantum_no_profit_advantage() -> None:
    audit = records("PR162D_QuantumNoProfitAdvantageClaimAudit.report.json")[0]
    smoke = records("PR162D_QUBOIsingLocalExactSmokeExecution.report.json")
    assert audit["quantum_profit_evidence_claim_count"] == 0
    assert audit["quantum_advantage_claim_count"] == 0
    assert all(record["profit_evidence_claim_flag"] is False for record in smoke)
    assert all(record["quantum_advantage_claim_flag"] is False for record in smoke)


def assert_quantum_launch_usability() -> None:
    routes = records("PR162D_QuantumAgentUsabilityAtLaunchMatrix.report.json")
    assert len(routes) == summary()["quantum_agent_launch_usability_route_count"]
    assert all(record["live_order_authority"] is False for record in routes)


def assert_strategy_intents_no_order_authority() -> None:
    intents = records("PR162D_StrategySignalDecisionCandidateIntentMatrix.report.json")
    assert intents
    assert all(record["order_authority_flag"] is False for record in intents)


def assert_execution_preview_non_authority() -> None:
    previews = records("PR162D_ExecutionRouterNonAuthorityPreviewMatrix.report.json")
    assert previews
    assert all(record["submit_cancel_reduce_close_order_allowed_flag"] is False for record in previews)
    assert all(record["live_order_authority"] is False for record in previews)


def assert_only_hard_boundaries_zero() -> None:
    s = summary()
    for field, expected in c.BOUNDARY_COUNT_FIELDS.items():
        assert s[field] == expected


def assert_no_private_state_or_secrets() -> None:
    sources = records("PR162D_CandidateSourceIntakeRegistry.report.json")
    deps = records("PR162D_QuantumBackendDependencyStatus.report.json")
    assert all(record["accepted_as_live_connector_truth_flag"] is False for record in sources)
    assert all(record.get("secret_value_captured_flag", False) is False for record in deps)


def assert_no_package_install_or_unknown_repo_execution() -> None:
    deps = records("PR162D_QuantumBackendDependencyStatus.report.json")
    assert all(record.get("package_install_attempted_flag", False) is False for record in deps)
    text = "\n".join(path.read_text(encoding="utf-8") for path in (REPO_ROOT / c.PACKAGE_DIR).rglob("*.py"))
    assert "pip install" not in text
    assert "git clone" not in text


def assert_online_cache_offline_safe() -> None:
    cache = records("PR162D_CachedOnlineSourceSnapshotManifest.report.json")
    assert cache
    assert all(record["ci_network_dependency_flag"] is False for record in cache)


def assert_no_qtt_digest_authority() -> None:
    s = summary()
    assert s["qtt_sha_freeze_checksum_authority_count"] == 0
    assert s["creates_qtt_digest_authority"] is False


def assert_no_atomicrows_hash_authority() -> None:
    s = summary()
    assert s["atomicrows_bundle_hash_sha_authority_count"] == 0
    assert s["forbidden_atomicrows_sidecar_artifact_created_or_referenced_flag"] is False


def assert_no_atomicrows_bundle_mutation() -> None:
    s = summary()
    assert s["atomicrows_bundle_mutation_count"] == 0
    assert s["atomicrows_bundle_jsonl_changed_flag"] is False


def assert_no_scattered_boundary_literals() -> None:
    audit = records("PR162D_LivePromotionOrderProfitEvidenceHardBoundaryReservation.report.json")[0]
    boundary = records("PR162D_SharedDictionary.report.json")[0]
    assert audit["scan_status"] == "PASS"
    assert set(c.DISALLOWED_ROUTE_STATUSES) == set(boundary["disallowed_route_statuses"])


def assert_pr136_consumed() -> None:
    crosswalk = records("PR162D_PR136CrosswalkConsumptionAudit.report.json")[0]
    market = records("PR162D_PR136MarketSpecificIndexConsumptionAudit.report.json")[0]
    command = records("PR162D_PR136CommandActionMatrixConsumptionAudit.report.json")[0]
    assert crosswalk["consumption_status"] == "CONSUMED_AVAILABLE_INPUTS_CONTINUED"
    assert market["consumed_flag"] is True
    assert command["consumed_flag"] is True


def assert_pr161f_consumed() -> None:
    audit = records("PR162D_PR161FAgentContractConsumptionAudit.report.json")[0]
    assert audit["consumed_flag"] is True
    assert audit["agent_contract_route_resolver_used_flag"] is True


def assert_pr162r_handoff_without_pr163() -> None:
    handoff = records("PR162D_PR162RReplayPaperAdapterCandidateHandoff.report.json")[0]
    pr163 = records("PR162D_PR163ResultPacketStillNotCreatedAudit.report.json")[0]
    assert handoff["result_packet_created_flag"] is False
    assert pr163["artifact_creation_status"] == "NOT_CREATED_BY_PR162D"


def assert_pr152_finalization_documented() -> None:
    s = summary()
    assert s["staged_files_before_final_validation_required_flag"] is True
    assert "currentize_pr152_after_generated_artifacts.py" in s["pr152_finalization_currentization_command"]


def assert_validation_gate_wiring() -> None:
    branch = c.EXPECTED_BRANCH
    assert ci_branch_context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing/validator.py",
    )
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py" in command_names
