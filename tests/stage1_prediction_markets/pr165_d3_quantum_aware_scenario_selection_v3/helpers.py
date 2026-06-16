from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.authority import ZERO_AUTHORITY_KEYS
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.enums import FORBIDDEN_STATUS_VALUES
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.io import read_json, records_from_report_payload
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.models import REQUIRED_ROW_FIELDS

SPECIAL_TEST_REPORTS = {
    "build_outputs": ["PR165_D3_FinalSummary.report.json", "PR165_D3_ReportManifest.report.json"],
    "idempotence": ["PR165_D3_FinalSummary.report.json"],
    "validator": ["PR165_D3_FinalSummary.report.json"],
    "input_consumption": ["PR165_D3_InputAudit.report.json"],
    "shard_input_audit": ["PR165_D3_ShardInputAudit.report.json"],
    "row_count_reconciliation": ["PR165_D3_RowCountLedger.report.json"],
    "param_stack_select": ["PR165_D3_ParamStackSelect.report.json"],
    "exec_route_select": ["PR165_D3_ExecRouteSelect.report.json"],
    "exec_adjusted_score": ["PR165_D3_ExecAdjScore.report.json"],
    "diversity": ["PR165_D3_DiversityLedger.report.json"],
    "champion_challenger": ["PR165_D3_ChampionSlate.report.json", "PR165_D3_ChallengerSlate.report.json"],
    "suppression": ["PR165_D3_SuppressionLedger.report.json"],
    "portfolio_slate": ["PR165_D3_PortfolioSlate.report.json"],
    "downstream_handoffs": [name for name in c.REPORT_FILENAMES if name.endswith("Handoff.report.json")],
    "runtime_safety_handoff": ["PR165_D3_RuntimeSafetyHandoff.report.json"],
    "launch_review_filter": ["PR165_D3_LaunchReviewFilter.report.json"],
    "live_readiness_ref": ["PR165_D3_LiveReadinessRef.report.json"],
    "hot_path_snapshot": ["PR165_D3_HotPathSnapshot.report.json"],
    "owner_review_queue": ["PR165_D3_OwnerReviewQueue.report.json"],
    "agent_duty": ["PR165_D3_AgentDutyLedger.report.json"],
    "agent_task_queue": ["PR165_D3_AgentTaskQueue.report.json"],
    "agent_kpi": ["PR165_D3_AgentKPIAudit.report.json"],
    "route_crosswalk_cmd": ["PR165_D3_PlanCrosswalk.report.json", "PR165_D3_CmdActionMatrix.report.json", "PR165_D3_RouteTriageMatrix.report.json"],
    "connector_routing": ["PR165_D3_ConnectorRouting.report.json"],
    "connectivity": ["PR165_D3_FileConnAudit.report.json", "PR165_D3_ValueConnAudit.report.json", "PR165_D3_NoOrphanProof.report.json"],
    "authority_boundaries": ["PR165_D3_AuthorityAudit.report.json"],
    "no_profit_evidence": ["PR165_D3_NoProfitAudit.report.json"],
    "no_orphans": ["PR165_D3_OrphanAudit.report.json"],
    "status_enum_drift": ["PR165_D3_StatusDriftAudit.report.json"],
    "no_bad_status_tokens": ["PR165_D3_StatusDriftAudit.report.json", "PR165_D3_AuthorityAudit.report.json", "PR165_D3_SelectedCombos.report.json", "PR165_D3_OrderCandidateLedger.report.json"],
    "compact_names": ["PR165_D3_ReportManifest.report.json"],
    "summary_handoff": ["PR165_D3_SummaryHandoff.report.json"],
    "pr152_pr208_routing_contract": ["PR165_D3_FinalSummary.report.json"],
}

@lru_cache(maxsize=None)
def payload(report: str) -> dict:
    return read_json(REPO_ROOT / c.GENERATED_DIR / report)

@lru_cache(maxsize=None)
def records(report: str) -> tuple[dict, ...]:
    return tuple(records_from_report_payload(REPO_ROOT, payload(report)))

@lru_cache(maxsize=1)
def final_summary() -> dict:
    return records("PR165_D3_FinalSummary.report.json")[0]

@lru_cache(maxsize=1)
def manifest_records() -> tuple[dict, ...]:
    return records("PR165_D3_ReportManifest.report.json")

def report_from_test_file(file_path: str) -> list[str]:
    stem = Path(file_path).stem.removeprefix("test_pr165_d3_")
    if stem in SPECIAL_TEST_REPORTS:
        return SPECIAL_TEST_REPORTS[stem]
    report = _report_from_stem(stem)
    if report:
        return [report]
    raise AssertionError(f"No PR165-D3 report mapping for test stem {stem}")

def assert_reports_for_test(file_path: str) -> None:
    for report in report_from_test_file(file_path):
        assert_report_family(report)

def assert_report_family(report: str) -> None:
    p = payload(report)
    rows = records(report)
    assert p["roadmap_pr_id"] == c.PR_ID
    assert p["created_by_pr"] == c.PR_ID
    assert p["report_name"] == report
    assert p["schema_ref"] == c.REPORT_SCHEMA_REFS[report]
    assert p["record_count"] == len(rows)
    assert rows, f"{report} must not be empty"
    for row in rows[: min(3, len(rows))]:
        missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
        assert not missing, f"{report} missing required fields {missing}"
        assert row["created_by_pr"] == c.PR_ID
        assert row["roadmap_pr_id"] == c.PR_ID
        assert row["validator_ref"] == c.VALIDATOR_REF
        assert row["schema_ref"] == c.REPORT_SCHEMA_REFS[report]
        assert row["downstream_pr_refs"]
        assert row["connector_binding_allowed_in_this_pr"] is False
        assert row["live_order_authority_allowed_in_this_pr"] is False
        assert row["owner_live_approval_allowed_in_this_pr"] is False
        assert row["profit_evidence_allowed_in_this_pr"] is False
        assert row["quantum_backend_execution_allowed_in_this_pr"] is False
        for key in ZERO_AUTHORITY_KEYS:
            if key in row:
                assert row[key] == 0

def assert_no_forbidden_status_tokens() -> None:
    for report in SPECIAL_TEST_REPORTS["no_bad_status_tokens"]:
        for row in records(report):
            assert not _contains_forbidden(row), f"forbidden token emitted in {report}:{row.get('row_id')}"

def assert_manifest_is_synchronized() -> None:
    names = {row["manifest_report_name"] for row in manifest_records()}
    assert names == set(c.REPORT_FILENAMES)
    assert len(names) == 136
    for row in manifest_records():
        report = row["manifest_report_name"]
        assert row["referenced_schema_ref"] == c.REPORT_SCHEMA_REFS[report]
        assert row["record_count"] == payload(report)["record_count"]

def assert_compact_names_only() -> None:
    for report in c.REPORT_FILENAMES:
        assert report.startswith("PR165_D3_")
        assert "Full" not in report
        assert "Long" not in report
        assert not report.startswith("PR165_D_")
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("*PR165_D3*.sha*"))

def _report_from_stem(stem: str) -> str | None:
    normalized = stem.replace("qku", "QKU").replace("qubo", "QUBO").replace("cqm", "CQM")
    for report in c.REPORT_FILENAMES:
        candidate = report.removesuffix(".report.json").removeprefix("PR165_D3_")
        candidate_stem = _snake(candidate)
        if candidate_stem == stem:
            return report
    aliases = {
        "qku_combo_registry": "PR165_D3_QKUComboRegistry.report.json",
        "formula_algo_combo": "PR165_D3_FormulaAlgoCombo.report.json",
        "scenario_context": "PR165_D3_ScenarioContext.report.json",
        "condition_fingerprint": "PR165_D3_ConditionFingerprint.report.json",
        "regime_classifier": "PR165_D3_RegimeClassifier.report.json",
        "selection_policy": "PR165_D3_SelectionPolicy.report.json",
        "selection_universe": "PR165_D3_SelectionUniverse.report.json",
        "calibration": "PR165_D3_CalibrationLedger.report.json",
        "confidence": "PR165_D3_ConfidenceLedger.report.json",
    }
    return aliases.get(stem) or aliases.get(_snake(normalized))

def _snake(value: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()

def _contains_forbidden(value) -> bool:
    if isinstance(value, dict):
        return any(_contains_forbidden(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden(item) for item in value)
    return isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES
