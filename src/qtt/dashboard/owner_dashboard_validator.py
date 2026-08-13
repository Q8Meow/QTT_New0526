"""Fail-closed validation for PR169-DASH1 owner dashboard artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)

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
    ST12G_CONTRACT_MANIFEST_REF,
    ST12G_DASHBOARD_SURFACE_ID,
    ST12G_DESCRIPTOR_FILENAME,
    ST12G_MATERIALIZATION_FIELDS,
    ST12G_REGISTRY_FEATURE_ID,
    ST12G_SOURCE_OWNER,
    ST12G_SVC_DESCRIPTOR_REF,
    V4_ROUTE_LABELS,
    VALIDATION_MARKER,
    read_json,
    read_jsonl,
    registry_row_ref,
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


def validate_st12g_descriptor_candidate(
    candidate: object,
    *,
    existing: object | None = None,
) -> dict[str, object]:
    """Validate one real generated DASH1 ST12-G descriptor candidate."""

    if type(candidate) is not dict:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "ST12-G dashboard descriptor must be an exact object",
        )
    if any(
        key in candidate
        for key in ("runtime_evidence", "evidence_value", "owner_decision")
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
            "repository descriptor cannot materialize runtime evidence",
        )
    if set(candidate) != set(ST12G_MATERIALIZATION_FIELDS):
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "ST12-G dashboard descriptor field roster differs",
        )
    if existing is not None:
        if type(existing) is not dict or set(existing) != set(
            ST12G_MATERIALIZATION_FIELDS
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "existing ST12-G dashboard descriptor is not canonical",
            )
        if existing["descriptor_id"] == candidate["descriptor_id"]:
            if deterministic_json(existing) != deterministic_json(candidate):
                raise ContractValidationError(
                    ReasonCode.IDEMPOTENCY_CONFLICT,
                    "same dashboard descriptor slot carries changed payload",
                )
            return existing
    expected = {
        "descriptor_id": "ST12G-DESCRIPTOR::DASH1_UI1",
        "contract_version": "2.0",
        "consumer_id": "DASH1_UI1",
        "contract_type": "ST12GOwnerDashboardEvidenceViewV2",
        "source_contract_manifest_ref": ST12G_CONTRACT_MANIFEST_REF,
        "canonical_owner_ref": "PR169_DASH1_OWNER_DASHBOARD_SURFACE_REGISTRY",
        "runtime_instance_state": "NOT_MATERIALIZED_BY_REPOSITORY_BUILD",
        "manual_edit_allowed": False,
        "runtime_effect_allowed": False,
        "write_authority": "NONE",
        "downstream_route_refs": ["DASH1_UI1"],
    }
    if (
        candidate["runtime_instance_state"]
        != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
    ):
        raise ContractValidationError(
            ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
            "generated descriptor cannot be presented as empirical evidence",
        )
    if candidate != expected:
        raise ContractValidationError(
            ReasonCode.SCHEMA_MISMATCH,
            "ST12-G dashboard descriptor payload differs",
        )
    return candidate


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

    st12g_path = base / ST12G_DESCRIPTOR_FILENAME
    st12g_rows = read_jsonl(st12g_path) if st12g_path.exists() else []
    if len(st12g_rows) != 1:
        failures.append(f"st12g_descriptor_count:{len(st12g_rows)}")
    else:
        descriptor = st12g_rows[0]
        try:
            validate_st12g_descriptor_candidate(descriptor)
        except ContractValidationError as exc:
            failures.append(
                "st12g_descriptor_"
                f"{exc.reason_code.name.casefold()}"
            )

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
    required_names = {
        Path(name).name
        for name in (
            REGISTRY_FILENAME,
            *REQUIRED_JSONL_OUTPUTS,
            ST12G_DESCRIPTOR_FILENAME,
            *REQUIRED_JSON_OUTPUTS,
            *REQUIRED_UI_OUTPUTS,
        )
    }
    _failures_append_missing(failures, "data_value_route_map_artifacts", mapped_artifacts, required_names)
    st12g_route_rows = [
        row
        for row in data_map_rows
        if Path(str(row.get("artifact_path", ""))).name
        == ST12G_DESCRIPTOR_FILENAME
    ]
    if len(st12g_route_rows) != 1:
        failures.append("st12g_data_route_count_mismatch")
    else:
        route = st12g_route_rows[0]
        route_refs = tuple(
            str(value) for value in route.get("owner_surface_registry_refs", [])
        )
        if any("READ_LATER_QUEUE" in value for value in route_refs):
            failures.append("st12g_route_assigned_to_read_later_queue")
        if route.get("destination_surface") != ST12G_DASHBOARD_SURFACE_ID:
            failures.append("st12g_route_destination_not_qku_control_plane")
        if (
            route.get("source_owner") != ST12G_SOURCE_OWNER
            or route.get("canonical_source_ref") != REGISTRY_FILENAME
            or route.get("upstream_artifact_refs") != [ST12G_SVC_DESCRIPTOR_REF]
        ):
            failures.append("st12g_route_missing_svc1_source_binding")
        if route_refs != (registry_row_ref(ST12G_REGISTRY_FEATURE_ID),):
            failures.append("st12g_route_registry_anchor_drift")
        if route.get("direct_f_binding_allowed") is not False:
            failures.append("st12g_route_direct_f_source_detected")
        if (
            route.get("write_authority") != "NONE"
            or route.get("runtime_effect_allowed") is not False
            or route.get("order_authority") is not False
            or route.get("mode_authority") is not False
            or route.get("capital_authority") is not False
        ):
            failures.append("st12g_route_effect_or_authority_detected")

    no_orphan = read_json(base / "owner_dashboard_no_orphan.report.json")
    authority = read_json(base / "owner_dashboard_authority_boundary.report.json")
    if no_orphan.get("status") != "PASS":
        failures.append("no_orphan_report_not_pass")
    if (
        no_orphan.get("st12g_svc1_only_projection_connected") is not True
        or no_orphan.get("st12g_zero_direct_f_bindings") is not True
    ):
        failures.append("st12g_svc1_only_lineage_not_proven")
    if authority.get("status") != "PASS":
        failures.append("authority_report_not_pass")
    for key, value in authority.items():
        if key in {"status", "artifact_id", "owner_global_internal_authority_preserved_with_receipts"}:
            continue
        if isinstance(value, bool) and key.endswith(("authority", "reads", "writers", "readers", "created", "bypass", "override", "guarantee")) and value:
            failures.append(f"authority_boundary_true:{key}")

    projection_manifest_rows = jsonl_rows_by_file.get(
        "owner_surface_projection_manifest.generated.jsonl", []
    )
    st12g_manifest_rows = [
        row
        for row in projection_manifest_rows
        if row.get("projection_file") == ST12G_DESCRIPTOR_FILENAME
    ]
    if len(st12g_manifest_rows) != 1:
        failures.append("st12g_projection_manifest_registration_mismatch")
    elif (
        st12g_manifest_rows[0].get("projection_authoritative_source")
        != ST12G_SVC_DESCRIPTOR_REF
        or st12g_manifest_rows[0].get("direct_f_binding_allowed") is not False
    ):
        failures.append("st12g_projection_manifest_direct_f_or_lineage_drift")
    elif (
        st12g_manifest_rows[0].get("source_owner") != ST12G_SOURCE_OWNER
        or st12g_manifest_rows[0].get("destination_surface")
        != ST12G_DASHBOARD_SURFACE_ID
        or st12g_manifest_rows[0].get("registry_row_ref")
        != registry_row_ref(ST12G_REGISTRY_FEATURE_ID)
        or st12g_manifest_rows[0].get("write_authority") != "NONE"
        or st12g_manifest_rows[0].get("runtime_effect_allowed") is not False
        or st12g_manifest_rows[0].get("order_authority") is not False
        or st12g_manifest_rows[0].get("mode_authority") is not False
        or st12g_manifest_rows[0].get("capital_authority") is not False
    ):
        failures.append("st12g_projection_manifest_route_or_authority_drift")

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
