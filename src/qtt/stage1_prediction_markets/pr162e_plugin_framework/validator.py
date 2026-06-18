"""Focused validators for PR162E generated artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.pr162e_plugin_framework import constants as C
from src.qtt.stage1_prediction_markets.pr162e_plugin_framework.io import read_json


REQUIRED_PLUGIN_FIELDS = (
    "plugin_id",
    "plugin_family",
    "plugin_version",
    "plugin_status",
    "plugin_materialization_status",
    "qku_refs",
    "formula_refs",
    "algorithm_refs",
    "parameter_stack_refs",
    "quantum_recipe_refs",
    "upstream_report_refs",
    "upstream_row_refs",
    "upstream_producer_pr",
    "owning_agent",
    "supporting_agents",
    "duty_source_ref",
    "input_schema_ref",
    "output_schema_ref",
    "request_type_ref",
    "response_type_ref",
    "diagnostic_type_ref",
    "repair_plan_ref",
    "retest_plan_ref",
    "authority_envelope_ref",
    "required_fields",
    "optional_fields",
    "candidate_fill_values",
    "runtime_lane",
    "runtime_budget_ms",
    "timeout_behavior",
    "fail_closed_behavior",
    "missing_input_behavior",
    "stale_input_behavior",
    "schema_mismatch_behavior",
    "runtime_error_behavior",
    "expected_output_fields",
    "score_components",
    "negative_root_cause_refs",
    "repair_action_refs",
    "downstream_report_refs",
    "downstream_pr",
    "downstream_consumer_agent",
    "dashboard_visibility",
    "commander_visibility",
    "governance_visibility",
    "repair_or_retest_route",
    "no_orphan_proof_ref",
)


def _report_path(repo_root: Path, filename: str) -> Path:
    return repo_root / C.GENERATED_DIR / filename


def _load_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = _report_path(repo_root, filename)
    if not path.exists():
        raise AssertionError(f"missing report: {filename}")
    payload = read_json(path)
    if payload.get("report_filename") != filename:
        raise AssertionError(f"bad report_filename for {filename}")
    if payload.get("record_count") != len(payload.get("records") or []):
        raise AssertionError(f"record_count mismatch for {filename}")
    if payload.get("authority_envelope_ref") != C.AUTHORITY_ENVELOPE_REF:
        raise AssertionError(f"missing authority envelope ref: {filename}")
    for field in C.FORBIDDEN_COUNT_FIELDS:
        if payload.get(field, 0) != 0:
            raise AssertionError(f"forbidden authority count {field} in {filename}")
    return payload


def _plugin_rows(repo_root: Path) -> list[dict[str, Any]]:
    payload = _load_report(repo_root, "PR162E_PluginRegistry.report.json")
    rows = payload.get("records") or []
    if not rows:
        raise AssertionError("plugin registry is empty")
    return rows


def _validate_report_inventory(repo_root: Path) -> None:
    for filename in C.REPORT_FILENAMES:
        _load_report(repo_root, filename)
    for schema_name in C.SCHEMA_FILENAMES:
        path = repo_root / C.SCHEMA_DIR / schema_name
        if not path.exists():
            raise AssertionError(f"missing schema: {schema_name}")


def _validate_read_receipt(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_ReadReceipt.report.json").get("records") or []
    repo_rows = [row for row in rows if str(row.get("row_id", "")).startswith("PR162E_READ_RECEIPT_REPO")]
    online_rows = [row for row in rows if str(row.get("row_id", "")).startswith("PR162E_READ_RECEIPT_ONLINE")]
    if len(repo_rows) != len(C.READING_LIST_REPORTS):
        raise AssertionError("read receipt repo artifact coverage mismatch")
    if len(online_rows) != len(C.EXTERNAL_SOURCE_ROWS):
        raise AssertionError("read receipt online source coverage mismatch")
    required = {
        "PR167_PluginNeeds.report.json",
        "PR167_AgentWorkOrders.report.json",
        "PR162E_Q_To_PR162E.report.json",
        "PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "PR165_D2_AgentDutySourceCrosswalk.report.json",
    }
    found = {Path(str(row.get("artifact_path", ""))).name for row in repo_rows if row.get("exists_flag")}
    missing = sorted(required - found)
    if missing:
        raise AssertionError(f"required upstream read receipts missing: {missing}")
    if any(row.get("source_truth_accepted") is not False for row in online_rows):
        raise AssertionError("online source truth accepted")


def _validate_counts(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_CountReconcile.report.json").get("records") or []
    if not rows:
        raise AssertionError("count reconcile rows missing")
    for row in rows:
        if row.get("actual_count") is None:
            raise AssertionError(f"count row missing actual_count: {row.get('row_id')}")
        if row.get("reconcile_status") not in {"MATCH", "DIFF_USE_ACTUAL_REPO_TRUTH"}:
            raise AssertionError(f"bad reconcile status: {row.get('row_id')}")


def _validate_plugin_contracts(repo_root: Path) -> None:
    rows = _plugin_rows(repo_root)
    if len(rows) != 559:
        raise AssertionError(f"expected 559 plugin rows from actual PR167 truth, got {len(rows)}")
    families = {row.get("plugin_family") for row in rows}
    missing_families = sorted(set(C.PLUGIN_FAMILIES) - families)
    if missing_families:
        raise AssertionError(f"missing plugin families: {missing_families[:5]}")
    for row in rows:
        missing = [field for field in REQUIRED_PLUGIN_FIELDS if field not in row]
        if missing:
            raise AssertionError(f"{row.get('row_id')} missing fields: {missing}")
        if row["plugin_materialization_status"] not in C.MATERIALIZATION_STATUSES:
            raise AssertionError(f"bad materialization status: {row.get('row_id')}")
        if row["runtime_lane"] not in C.ALLOWED_RUNTIME_LANES:
            raise AssertionError(f"bad runtime lane: {row.get('row_id')}")
        if row["runtime_lane"] in C.FORBIDDEN_RUNTIME_LANES:
            raise AssertionError(f"forbidden runtime lane: {row.get('row_id')}")
        if row["authority_envelope_ref"] != C.AUTHORITY_ENVELOPE_REF:
            raise AssertionError(f"bad authority ref: {row.get('row_id')}")
        if not row["upstream_report_refs"] or not row["upstream_row_refs"]:
            raise AssertionError(f"missing upstream refs: {row.get('row_id')}")
        if not row["downstream_report_refs"] and not row.get("terminal_reason"):
            raise AssertionError(f"missing downstream refs: {row.get('row_id')}")
        if row["plugin_materialization_status"] != "TERMINAL_NO_TRADE_NONLIVE" and not row["test_vector_refs"]:
            raise AssertionError(f"missing test vector: {row.get('row_id')}")
        if row["plugin_materialization_status"] in {"COMPUTABLE_REPAIR_READY", "POST_REPAIR_RETEST_READY"}:
            if not row["repair_action_refs"] or not row["repair_or_retest_route"]:
                raise AssertionError(f"repair row missing repair route: {row.get('row_id')}")
        if row["plugin_materialization_status"] == "POST_REPAIR_RETEST_READY" and "Retest" not in row["repair_or_retest_route"]:
            raise AssertionError(f"post-repair row missing retest route: {row.get('row_id')}")
        for flag in (
            "live_order_authority_flag",
            "live_order_execution_flag",
            "live_promotion_claim_flag",
            "source_truth_acceptance_flag",
            "connector_semantic_binding_flag",
            "private_state_fetch_flag",
            "runtime_cash_receipt_flag",
            "profit_evidence_flag",
            "quantum_backend_execution_flag",
            "quantum_advantage_claim_flag",
            "llm_hot_path_flag",
            "llm_order_release_flag",
            "llm_source_acceptance_flag",
            "llm_result_rewrite_flag",
            "qtt_sha_freeze_checksum_global_digest_authority_flag",
            "atomicrows_bundle_sha_hash_checksum_authority_flag",
        ):
            if row.get(flag) is not False:
                raise AssertionError(f"forbidden flag set: {flag} {row.get('row_id')}")


def validate_negative_repair_factory(repo_root: Path) -> None:
    negative_inventory = _load_report(repo_root, "PR162E_NegativeReplayPaperCandidateInventory.report.json").get("records") or []
    repair_plan = _load_report(repo_root, "PR162E_NegativeCandidateRepairPlan.report.json").get("records") or []
    retest_queue = _load_report(repo_root, "PR162E_PostRepairRetestQueue.report.json").get("records") or []
    terminal = _load_report(repo_root, "PR162E_TerminalNoTradeNonLive.report.json").get("records") or []
    taxonomy = _load_report(repo_root, "PR162E_NegativeRootCauseTaxonomy.report.json").get("records") or []
    count_rows = _load_report(repo_root, "PR162E_CountReconcile.report.json").get("records") or []
    if not negative_inventory:
        raise AssertionError("negative inventory empty")
    if len(taxonomy) != len(C.ROOT_CAUSE_CODES):
        raise AssertionError("root cause taxonomy incomplete")
    if len(repair_plan) != len(negative_inventory):
        raise AssertionError("negative repair plan does not cover inventory")
    if len(retest_queue) != len(negative_inventory):
        raise AssertionError("post repair retest queue does not cover inventory")
    no_trade_expected = next(
        (
            int(row["actual_count"])
            for row in count_rows
            if row.get("count_semantics") == "PR167 no-trade non-live rows"
        ),
        len(terminal),
    )
    if len(terminal) != no_trade_expected:
        raise AssertionError("terminal no-trade visibility does not cover actual no-trade subset")
    for row in repair_plan:
        if not row.get("repair_actions_applied"):
            raise AssertionError(f"missing repair action: {row.get('row_id')}")
        if not row.get("retest_route"):
            raise AssertionError(f"missing retest route: {row.get('row_id')}")
        if row.get("plugin_materialization_status") not in {
            "COMPUTABLE_REPAIR_READY",
            "POST_REPAIR_RETEST_READY",
        }:
            raise AssertionError(f"bad repair status: {row.get('row_id')}")
    for row in terminal:
        if not row.get("terminal_reason") or not row.get("terminal_reason_code"):
            raise AssertionError(f"terminal row missing reason: {row.get('row_id')}")


def validate_no_orphan_lineage(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_NoOrphanProof.report.json").get("records") or []
    lineage = _load_report(repo_root, "PR162E_UniversalArtifactLineageMap.report.json").get("records") or []
    file_map = _load_report(repo_root, "PR162E_FileConsumerMap.report.json").get("records") or []
    value_map = _load_report(repo_root, "PR162E_ValueLineageMap.report.json").get("records") or []
    crosswalk = _load_report(repo_root, "PR162E_ReportConsumerCrosswalk.report.json").get("records") or []
    if not rows or not lineage or not file_map or not value_map or not crosswalk:
        raise AssertionError("lineage/no-orphan reports must be non-empty")
    if any(row.get("no_orphan_status") != "PASS" for row in rows):
        raise AssertionError("no-orphan proof contains non-pass row")
    report_paths = {f"{C.GENERATED_DIR.as_posix()}/{filename}" for filename in C.REPORT_FILENAMES}
    file_paths = {row.get("artifact_path") for row in file_map}
    missing = sorted(report_paths - file_paths)
    if missing:
        raise AssertionError(f"file consumer map missing reports: {missing[:5]}")
    crosswalk_reports = {row.get("report_filename") for row in crosswalk}
    missing_crosswalk = sorted(set(C.REPORT_FILENAMES) - crosswalk_reports)
    if missing_crosswalk:
        raise AssertionError(f"report consumer crosswalk missing reports: {missing_crosswalk[:5]}")
    for row in lineage:
        if not row.get("authority_envelope_ref"):
            raise AssertionError(f"lineage missing authority: {row.get('row_id')}")
        if row.get("terminal_flag") and not row.get("terminal_reason_if_terminal"):
            raise AssertionError(f"terminal lineage missing reason: {row.get('row_id')}")


def _validate_external_candidates(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_ExternalCandidateIntake.report.json").get("records") or []
    if len(rows) != len(C.EXTERNAL_SOURCE_ROWS):
        raise AssertionError("external candidate intake source count mismatch")
    for row in rows:
        if row.get("source_truth_accepted") is not False:
            raise AssertionError(f"source truth accepted: {row.get('row_id')}")
        if not row.get("source_url") or not row.get("plugin_family_mapping"):
            raise AssertionError(f"external source row incomplete: {row.get('row_id')}")


def _validate_dag(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_PluginDependencyDAG.report.json").get("records") or []
    if len(rows) != len(_plugin_rows(repo_root)):
        raise AssertionError("DAG row count mismatch")
    seen: set[str] = set()
    previous_order = 0
    for row in rows:
        node = row.get("node_id")
        if not node:
            raise AssertionError("DAG row missing node_id")
        if node in seen:
            raise AssertionError(f"duplicate DAG node: {node}")
        seen.add(str(node))
        order = int(row.get("topological_order_index") or 0)
        if order <= previous_order:
            raise AssertionError("DAG topological order is not deterministic")
        previous_order = order
        if row.get("cycle_detection_status") != "NO_CYCLE":
            raise AssertionError(f"DAG cycle found: {row.get('row_id')}")
        if row.get("orphan_status") != "NOT_ORPHAN":
            raise AssertionError(f"DAG orphan found: {row.get('row_id')}")


def _validate_authority_audit(repo_root: Path) -> None:
    rows = _load_report(repo_root, "PR162E_AuthorityBoundaryAudit.report.json").get("records") or []
    if len(rows) != 1:
        raise AssertionError("authority audit must have one row")
    row = rows[0]
    if row.get("forbidden_authority_total") != 0:
        raise AssertionError("forbidden authority total not zero")
    for field in C.FORBIDDEN_COUNT_FIELDS:
        if row.get(field, 0) != 0:
            raise AssertionError(f"authority audit nonzero: {field}")


def validate(repo_root: Path) -> dict[str, Any]:
    repo_root = Path(repo_root)
    _validate_report_inventory(repo_root)
    _validate_read_receipt(repo_root)
    _validate_counts(repo_root)
    _validate_plugin_contracts(repo_root)
    validate_negative_repair_factory(repo_root)
    validate_no_orphan_lineage(repo_root)
    _validate_external_candidates(repo_root)
    _validate_dag(repo_root)
    _validate_authority_audit(repo_root)
    return {
        "status": "PASS",
        "report_count": len(C.REPORT_FILENAMES),
        "schema_count": len(C.SCHEMA_FILENAMES),
        "plugin_count": len(_plugin_rows(repo_root)),
    }
