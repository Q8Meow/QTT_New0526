from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.calibration_formulas import (
    brier_score_binary,
    log_loss_binary,
    probability_clipping,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.json_io import (
    read_json,
    records_from_payload,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.paths import (
    resolve_repo_relative,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.prediction_market_formulas import (
    expected_value_binary,
    no_trade_decision,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.quantum_formulations import (
    exact_qubo_smoke_solve,
    ising_energy,
    qubo_energy,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.risk_position_sizing_formulas import (
    capped_position_size,
    kelly_fraction_binary,
    max_drawdown,
    sharpe_ratio,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.technical_feature_formulas import (
    midpoint,
    spread,
)
from src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.validator import (
    validate_artifacts,
)
from tools import ci_branch_context, run_validation_gates


REPO_ROOT = Path(__file__).resolve().parents[3]


def _report(filename: str) -> dict[str, Any]:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


def _records(filename: str) -> list[dict[str, Any]]:
    payload = _report(filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest = _report(c.SHARD_MANIFEST_REPORT_FILENAME)
    manifest_record = {
        record["report_filename"]: record
        for record in records_from_payload(manifest)
    }[filename]
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_record["shard_files"]:
        rows.extend(records_from_payload(read_json(resolve_repo_relative(REPO_ROOT, shard_ref))))
    return rows


def test_pr162b_validator_accepts_generated_artifacts_and_consumes_upstream_inputs():
    result = validate_artifacts(REPO_ROOT)
    summary = _report("PR162B_FinalSummary.report.json")

    assert result.ok, result.failures
    assert summary["pr136_control_plane_artifacts_consumed_flag"] is True
    assert summary["pr137r_pr138_atomicrows_contracts_consumed_flag"] is True
    assert summary["pr161c_qku_inventory_graph_consumed_flag"] is True
    assert summary["pr161d_scoring_ranking_replay_paper_prep_consumed_flag"] is True
    assert summary["pr161e_pr161f_pr162_pr162a_artifacts_consumed_flag"] is True
    assert summary["total_qku_count"] == 9360
    assert summary["classified_qku_count"] == 9360
    assert summary["unclassified_qku_count"] == 0


def test_pr162b_market_execution_activation_and_dormancy_gates():
    execution = _records("PR162B_QKUExecutionClassificationAudit.report.json")
    market = _records("PR162B_QKUMarketClassificationRegistry.report.json")
    activation = _records("PR162B_QKUStage1PredictionMarketActivationGate.report.json")
    dormant = _records("PR162B_QKUDormancyRegistry.report.json")
    allowlists = _records("PR162B_QTTAgentStage1QKUActivationAllowlist.report.json")

    assert len(execution) == 9360
    assert len(market) == 9360
    assert len(activation) == 9360
    assert all(record["primary_execution_class"] in c.QKU_EXECUTION_CLASSES for record in execution)
    assert all(record["primary_market_scope"] in c.MARKET_SCOPES for record in market)
    assert all(record["primary_market_scope"] for record in execution)
    dormant_qkus = {record["qku_id"] for record in dormant}
    router = next(record for record in allowlists if record["agent_id"] == "QTT_EXECUTION_ROUTER_AGENT")
    assert not (dormant_qkus & set(router["execution_allowed_qku_refs"]))
    assert all(
        record["stage1_prediction_market_activation_status"].startswith("DORMANT_")
        for record in market
        if record["primary_market_scope"] in c.DORMANT_DEFAULT_MARKET_SCOPES
    )
    assert not any(
        record["primary_execution_class"] == "METADATA_ONLY_BLOCKED"
        and record["stage1_prediction_market_activation_status"]
        == "ACTIVE_STAGE1_PREDICTION_MARKET_TRADING_CANDIDATE"
        for record in execution
    )


def test_pr162b_formula_algorithm_solver_records_and_test_vectors():
    formulas = _records("PR162B_QKUFormulaRegistry.report.json")
    algorithms = _records("PR162B_QKUAlgorithmRegistry.report.json")
    objectives = _records("PR162B_QKUObjectiveFunctionRegistry.report.json")
    constraints = _records("PR162B_QKUConstraintRegistry.report.json")
    parameters = _records("PR162B_QKUParameterValueRegistry.report.json")
    tradable = _records("PR162B_QKUTradableValueCandidateRegistry.report.json")
    mappings = _records("PR162B_QKUSolverMappingRegistry.report.json")
    formula_tests = _records("PR162B_QKUFormulaTestVectorRegistry.report.json")
    algorithm_tests = _records("PR162B_QKUAlgorithmTestVectorRegistry.report.json")
    smoke = _records("PR162B_QuantumSolverSmokeExecutionReport.report.json")

    formula_names = {record["formula_name"] for record in formulas}
    assert "expected_value_binary" in formula_names
    assert "brier_score_binary" in formula_names
    assert "log_loss_binary" in formula_names
    assert "kelly_fraction" in formula_names
    assert "sharpe_ratio" in formula_names
    assert "max_drawdown" in formula_names
    assert "QUBO objective x^T Q x" in formula_names
    assert "Ising energy" in formula_names
    assert len(algorithms) >= 14
    assert objectives
    assert constraints
    assert len(parameters) >= 17
    assert len(tradable) >= 17
    assert all(record["test_vector_refs"] for record in formulas)
    assert all(record["test_vector_refs"] for record in algorithms)
    assert len(formula_tests) == len(formulas)
    assert len(algorithm_tests) == len(algorithms)
    assert any(record["compatible_solver_family"].startswith("CLASSICAL") for record in mappings)
    assert any("QUBO" in record["compatible_solver_family"] or "ISING" in record["compatible_solver_family"] for record in mappings)
    assert all(record["smoke_execution_status"] == "SMOKE_EXECUTED_NO_TRADING_EVIDENCE" for record in smoke)


def test_pr162b_formula_and_algorithm_functions_execute_expected_vectors():
    assert expected_value_binary(0.55, 1.0, 1.0) == 0.10000000000000009
    assert brier_score_binary(1, 0.8) == 0.03999999999999998
    assert round(log_loss_binary(1, 0.8), 12) == 0.223143551314
    assert probability_clipping(0.0, 0.01) == 0.01
    assert round(kelly_fraction_binary(0.55, 1.0), 12) == 0.1
    assert capped_position_size(0.3, 0.2) == 0.2
    assert max_drawdown([100, 120, 90, 130]) == 0.25
    assert sharpe_ratio(0.12, 0.02, 0.2) == 0.49999999999999994
    assert spread(0.6, 0.4) == 0.19999999999999996
    assert midpoint(0.6, 0.4) == 0.5
    assert no_trade_decision(0.01, 0.02) == "NO_TRADE"
    assert qubo_energy([1, 0], [[2, 3], [0, 4]]) == 2.0
    assert ising_energy([1, -1], [1.0, -0.5], {(0, 1): 0.25}) == 1.25
    assert exact_qubo_smoke_solve([[2.0, 3.0], [0.0, 4.0]])["status"] == "SMOKE_EXECUTED_NO_TRADING_EVIDENCE"


def test_pr162b_binding_pr162c_forbidden_authority_and_shard_guards():
    proofs = _records("PR162B_QKUFormulaBindingProofMatrix.report.json")
    handoff = _records("PR162B_PR162CDataRequirementHandoff.report.json")
    scan = _records("PR162B_ForbiddenAuthorityScan.report.json")[0]
    manifest = _report("PR162B_ReportShardManifest.report.json")
    summary = _report("PR162B_FinalSummary.report.json")

    assert any(record["binding_status"] == "STRICT_BINDING_CONFIRMED" for record in proofs)
    assert any(record["binding_method"] == "BROAD_BINDING_ATTEMPT_REJECTED" for record in proofs)
    assert handoff
    assert all(record["downstream_pr_route"] == "PR162C_STRICT_DATA_EXPANSION" for record in handoff)
    assert all(record["pr162r_ready_flag"] is False for record in handoff)
    assert "BLOCKED" in summary["pr162r_readiness_state"]
    assert "BLOCKED" in summary["pr163_readiness_state"]
    assert scan["scan_status"] == "PASS"
    assert scan["no_scattered_hardcoded_policy_scan_status"] == "PASS"
    assert manifest["all_shard_refs_posix_relative_flag"] is True
    assert not (REPO_ROOT / "docs/master_plan/QTT_MasterPlan_Current.md").is_file() or summary["master_plan_file_edited_flag"] is False
    assert summary["atomicrows_bundle_jsonl_changed_flag"] is False
    assert summary["forbidden_atomicrows_bundle_sidecar_artifact_created_or_referenced_flag"] is False
    assert summary["qtt_sha_freeze_checksum_global_digest_authority_created_flag"] is False


def test_pr162b_branch_context_and_validation_gate_wiring():
    branch = c.EXPECTED_BRANCH
    assert ci_branch_context.is_pr_or_later_branch(branch, minimum_pr=162) is True
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "src/qtt/stage1_prediction_markets/"
        "qku_formula_algorithm_solver_market_scope_materialization/validator.py",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/PR162B_FinalSummary.report.json",
    )
    assert ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/generated/pr162b_qku_formula_solver_market_scope_shards/"
        "PR162B_QKUExecutionClassificationAudit.report.shard_0001.json",
    )
    assert not ci_branch_context.is_explicit_downstream_repair_changed_path(
        branch,
        "docs/master_plan/QTT_MasterPlan_Current.md",
    )
    command_names = [Path(command[1]).name for command in run_validation_gates.build_validation_commands()]
    assert "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py" in command_names
    assert command_names.index("validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py") < command_names.index(
        "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
    )
