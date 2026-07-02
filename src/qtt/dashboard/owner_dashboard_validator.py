"""Fail-closed validation for PR169-DASH1 owner dashboard artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .owner_action_registry import ACTION_DEFINITIONS
from .owner_dashboard_projection_builder import (
    CHART_CONTRACTS,
    FILTER_DIMENSIONS,
    INTERACTIVE_CHART_FAMILIES,
    RESEARCH_PIPELINE_STATES,
    RESEARCH_ROLES,
    RESEARCH_SOURCE_FAMILIES,
    TIME_RANGES,
)
from .owner_surface_models import (
    AUTHORITY_BOUNDARY_REF,
    FORBIDDEN_AGENT_FIELDS,
    FORBIDDEN_STRING_MARKERS,
    LIFECYCLE_STATES,
    PROJECTION_TRACE_FIELDS,
    REGISTRY_FILENAME,
    REGISTRY_REQUIRED_FIELDS,
    REQUIRED_JSONL_OUTPUTS,
    REQUIRED_JSON_OUTPUTS,
    REQUIRED_UI_OUTPUTS,
    V4_ROUTE_LABELS,
    VALIDATION_MARKER,
    read_json,
    read_jsonl,
    write_json,
)


def _failures_append_missing(failures: list[str], label: str, values: set[str], required: set[str]) -> None:
    missing = sorted(required - values)
    if missing:
        failures.append(f"{label}_missing:{','.join(missing)}")


def _walk_json(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(key)
            values.extend(_walk_json(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_json(child))
    return values


def validate_artifacts(base_dir: Path | str) -> tuple[str, ...]:
    base = Path(base_dir)
    failures: list[str] = []
    registry_path = base / REGISTRY_FILENAME
    if not registry_path.exists():
        return (f"missing_registry:{registry_path}",)

    for file_name in REQUIRED_JSONL_OUTPUTS:
        if not (base / file_name).exists():
            failures.append(f"missing_jsonl:{file_name}")
        if file_name.endswith("_hint.jsonl"):
            failures.append(f"weak_hint_artifact:{file_name}")
    for file_name in REQUIRED_JSON_OUTPUTS:
        if not (base / file_name).exists():
            failures.append(f"missing_json:{file_name}")
    for file_name in REQUIRED_UI_OUTPUTS:
        if not (base / file_name).exists():
            failures.append(f"missing_ui:{file_name}")

    registry_rows = read_jsonl(registry_path)
    if not registry_rows:
        failures.append("empty_registry")
        return tuple(failures)

    registry_ids = {str(row.get("feature_id")) for row in registry_rows}
    action_codes = set(ACTION_DEFINITIONS)
    panels = set()
    aliases = set()
    seen_feature_ids: set[str] = set()
    for row in registry_rows:
        missing_fields = [field for field in REGISTRY_REQUIRED_FIELDS if field not in row]
        if missing_fields:
            failures.append(f"registry_missing_fields:{row.get('feature_id')}:{','.join(missing_fields)}")
        feature_id = str(row.get("feature_id"))
        if feature_id in seen_feature_ids:
            failures.append(f"duplicate_feature_id:{feature_id}")
        seen_feature_ids.add(feature_id)
        panels.add(str(row.get("panel_id")))
        for alias in row.get("legacy_aliases", []):
            alias = str(alias)
            if alias in aliases:
                failures.append(f"duplicate_legacy_alias:{alias}")
            aliases.add(alias)
        if row.get("lifecycle_state") not in LIFECYCLE_STATES:
            failures.append(f"bad_lifecycle_state:{feature_id}:{row.get('lifecycle_state')}")
        if row.get("v4_route_label") not in V4_ROUTE_LABELS:
            failures.append(f"bad_v4_route_label:{feature_id}:{row.get('v4_route_label')}")
        if row.get("lifecycle_state") in {"CONTRACT_DEFINED_PROVIDER_PENDING", "ROUTED_PENDING_PROVIDER"}:
            for field in (
                "owning_stage_or_pr",
                "target_stage",
                "provider_stage",
                "provider_contract_ref",
                "activation_route",
            ):
                if not row.get(field):
                    failures.append(f"provider_pending_missing_{field}:{feature_id}")
        if not row.get("action_code_refs"):
            failures.append(f"registry_row_without_action:{feature_id}")
        for action_code in row.get("action_code_refs", []):
            if action_code not in action_codes:
                failures.append(f"unknown_action_code:{feature_id}:{action_code}")
        if not row.get("agent_role_refs_from_PR165_D2") or not row.get("agent_route_validation_ref"):
            failures.append(f"missing_agent_route_ref:{feature_id}")

    jsonl_rows_by_file = {file_name: read_jsonl(base / file_name) for file_name in REQUIRED_JSONL_OUTPUTS if (base / file_name).exists()}
    for file_name, rows in jsonl_rows_by_file.items():
        if not rows:
            failures.append(f"empty_projection:{file_name}")
        for index, row in enumerate(rows, start=1):
            for field in FORBIDDEN_AGENT_FIELDS:
                if field in row:
                    failures.append(f"forbidden_agent_field:{file_name}:{index}:{field}")
            if file_name != "owner_surface_projection_manifest.generated.jsonl":
                for field in PROJECTION_TRACE_FIELDS:
                    if field not in row:
                        failures.append(f"projection_missing_trace:{file_name}:{index}:{field}")
                ref = str(row.get("registry_row_ref", ""))
                if "::" not in ref or ref.rsplit("::", 1)[-1] not in registry_ids:
                    failures.append(f"projection_bad_registry_ref:{file_name}:{index}:{ref}")
                if row.get("manual_edit_allowed") is not False:
                    failures.append(f"projection_manual_edit_not_false:{file_name}:{index}")
            for raw_value in _walk_json(row):
                if isinstance(raw_value, str):
                    lowered = raw_value.lower()
                    for marker in FORBIDDEN_STRING_MARKERS:
                        if marker in lowered and raw_value not in {
                            "quantum_backend_execution",
                            "quantum_advantage_claim",
                            "paper_submit_authority_created",
                            "live_order_authority_created",
                        }:
                            failures.append(f"forbidden_authority_string:{file_name}:{index}:{marker}")

    chart_rows = jsonl_rows_by_file.get("owner_chart_surface_contract.generated.jsonl", [])
    _failures_append_missing(
        failures,
        "chart_contracts",
        {str(row.get("chart_id")) for row in chart_rows},
        set(CHART_CONTRACTS),
    )
    for row in chart_rows:
        for field in (
            "chart_id",
            "chart_family",
            "panel_id",
            "data_provider_stage",
            "source_dataset_refs",
            "x_axis_field",
            "y_axis_fields",
            "group_by_fields",
            "filter_fields",
            "time_window_policy",
            "staleness_policy",
            "empty_state_policy",
            "authority_boundary_ref",
            "owner_action_code_refs",
            "activation_route",
        ):
            if not row.get(field):
                failures.append(f"chart_missing_{field}:{row.get('chart_id')}")

    interactive_rows = jsonl_rows_by_file.get("owner_interactive_chart_registry.generated.jsonl", [])
    _failures_append_missing(
        failures,
        "interactive_chart_families",
        {str(row.get("chart_family")) for row in interactive_rows},
        set(INTERACTIVE_CHART_FAMILIES),
    )
    for row in interactive_rows:
        for field in (
            "data_contract_ref",
            "dataset_provider_stage",
            "dataset_snapshot_ref",
            "supported_time_ranges",
            "filter_dimensions",
            "tooltip_fields",
            "drilldown_route",
            "stale_data_policy",
            "authority_boundary_ref",
        ):
            if not row.get(field):
                failures.append(f"interactive_chart_missing_{field}:{row.get('chart_family')}")
        if set(row.get("supported_time_ranges", [])) != set(TIME_RANGES):
            failures.append(f"interactive_chart_bad_time_ranges:{row.get('chart_family')}")
        if not set(FILTER_DIMENSIONS).issubset(set(row.get("filter_dimensions", []))):
            failures.append(f"interactive_chart_bad_filters:{row.get('chart_family')}")

    action_rows = jsonl_rows_by_file.get("owner_action_registry.generated.jsonl", [])
    action_ids = {str(row.get("action_code")) for row in action_rows}
    _failures_append_missing(failures, "action_registry", action_ids, set(ACTION_DEFINITIONS))
    if len(action_ids) != len(action_rows):
        failures.append("duplicate_action_registry_code")
    ack_rows = [row for row in action_rows if row.get("action_code") == "ACK_OWNER_PACKET"]
    if not ack_rows or ack_rows[0].get("is_live_approval") is not False:
        failures.append("ack_is_live_approval_or_missing")

    decision_rows = jsonl_rows_by_file.get("owner_decision_queue.generated.jsonl", [])
    sort_keys = [
        (int(row["severity_rank"]), int(row["gate_priority"]), int(row["unresolved_order"]))
        for row in decision_rows
    ]
    if sort_keys != sorted(sort_keys):
        failures.append("decision_queue_ordering_bad")

    coverage_rows = jsonl_rows_by_file.get("owner_dashboard_feature_coverage.generated.jsonl", [])
    if len(coverage_rows) < 112:
        failures.append(f"feature_coverage_too_small:{len(coverage_rows)}")

    research_intake_rows = jsonl_rows_by_file.get("owner_research_candidate_intake_contract.generated.jsonl", [])
    _failures_append_missing(
        failures,
        "research_source_families",
        {str(row.get("source_family")) for row in research_intake_rows},
        set(RESEARCH_SOURCE_FAMILIES),
    )
    pipeline_rows = jsonl_rows_by_file.get("owner_research_candidate_pipeline_view.generated.jsonl", [])
    _failures_append_missing(
        failures,
        "research_pipeline_states",
        {str(row.get("pipeline_state")) for row in pipeline_rows},
        set(RESEARCH_PIPELINE_STATES),
    )
    if not set(RESEARCH_ROLES).intersection({str(row.get("agent_or_provider_role")) for row in pipeline_rows}):
        failures.append("research_roles_missing")
    for row in pipeline_rows:
        if row.get("positive_net_cash_evidence_required") and len(row.get("required_positive_evidence_refs", [])) < 10:
            failures.append(f"positive_net_cash_missing_required_refs:{row.get('pipeline_state')}")

    qku_rows = jsonl_rows_by_file.get("owner_qku_formula_candidate_route_view.generated.jsonl", [])
    for row in qku_rows:
        if not row.get("upstream_evidence_refs") and "READINESS1" not in str(row.get("activation_route", "")):
            failures.append("metadata_only_qku_route")

    quantum_rows = jsonl_rows_by_file.get("owner_quantum_structural_readiness_view.generated.jsonl", [])
    for row in quantum_rows:
        structural_refs = [
            row.get("qstruct_ref"),
            row.get("objective_function_ref"),
            row.get("constraint_ledger_ref"),
            row.get("variable_encoding_ref"),
            row.get("classical_fallback_ref"),
            row.get("interpret_back_map_ref"),
        ]
        if not any(structural_refs) and not row.get("QMAP1_activation_route"):
            failures.append("metadata_only_quantum_route")

    data_map_rows = jsonl_rows_by_file.get("owner_data_value_route_map.generated.jsonl", [])
    mapped_artifacts = {Path(str(row.get("artifact_path", ""))).name for row in data_map_rows}
    required_names = {Path(name).name for name in (REGISTRY_FILENAME, *REQUIRED_JSONL_OUTPUTS, *REQUIRED_JSON_OUTPUTS, *REQUIRED_UI_OUTPUTS)}
    _failures_append_missing(failures, "data_value_route_map_artifacts", mapped_artifacts, required_names)

    no_orphan = read_json(base / "owner_dashboard_no_orphan.report.json")
    authority = read_json(base / "owner_dashboard_authority_boundary.report.json")
    if no_orphan.get("status") != "PASS":
        failures.append("no_orphan_report_not_pass")
    if authority.get("status") != "PASS":
        failures.append("authority_report_not_pass")
    for key, value in authority.items():
        if key in {"status", "artifact_id", "owner_global_internal_authority_preserved_with_receipts"}:
            continue
        if isinstance(value, bool) and key.endswith(("authority", "reads", "writers", "readers", "created", "bypass", "override", "guarantee")) and value:
            failures.append(f"authority_boundary_true:{key}")

    ui_text = ""
    for ui_file in REQUIRED_UI_OUTPUTS:
        path = base / ui_file
        if path.suffix in {".html", ".css", ".js"} and path.exists():
            ui_text += path.read_text(encoding="utf-8").lower()
    ui_text_for_network_scan = ui_text.replace("http://www.w3.org/2000/svg", "")
    for network_marker in ("http://", "https://", "cdn."):
        if network_marker in ui_text_for_network_scan:
            failures.append(f"ui_external_network_marker:{network_marker}")
    if "<script src=\"owner_dashboard_review_surface.js\"" not in ui_text:
        failures.append("ui_local_script_ref_missing")

    return tuple(failures)


def validate_and_write_summary(base_dir: Path | str) -> tuple[str, ...]:
    base = Path(base_dir)
    failures = validate_artifacts(base)
    summary = read_json(base / "validation_summary.report.json") if (base / "validation_summary.report.json").exists() else {}
    summary.update(
        {
            "status": "PASS" if not failures else "FAIL",
            "validation_marker": VALIDATION_MARKER if not failures else "PR169_DASH1_OWNER_DASHBOARD_VALIDATION_FAILED",
            "failure_count": len(failures),
            "failures": list(failures)[:200],
        }
    )
    write_json(base / "validation_summary.report.json", summary)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", "--artifact-dir", dest="base_dir", default="docs/master_plan/generated/pr169_dash1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout-ms", default="3600000")
    args = parser.parse_args(argv)
    base = Path(args.repo_root) / args.base_dir
    failures = validate_and_write_summary(base)
    if failures:
        print("PR169_DASH1_OWNER_DASHBOARD_VALIDATION_FAILED")
        for failure in failures[:200]:
            print(failure)
        return 1
    print(VALIDATION_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
