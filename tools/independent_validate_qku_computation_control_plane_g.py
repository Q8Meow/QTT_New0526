#!/usr/bin/env python3
"""Independent structural reconstruction of the ST12-G owner projection contract."""

from __future__ import annotations

import ast
from dataclasses import fields
import inspect
import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (  # noqa: E402
    existing_owner_projection as projection,
)
from tools import changed_area_validation_router as router  # noqa: E402
from tools import ci_branch_context  # noqa: E402
from tools import validation_inventory as inventory  # noqa: E402
from tools import validation_scope_registry as scope  # noqa: E402


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENT_G_VALIDATED"
EXPECTED_BRANCH = "agent/st12g-existing-owner-projections-v2"
EXPECTED_PUBLIC_NAMES = frozenset(
    {
        "ST12GProjectionRequestV2",
        "ST12GProjectionResolutionStateV2",
        "ST12GReferenceCollectionStateV2",
        "ST12GReferenceCollectionV2",
        "ST12GVersionMappingStateV2",
        "ST12GVersionMappingV2",
        "ST12GBlockerSetStateV2",
        "ST12GBlockerStateV2",
        "ST12GProjectionCoreV2",
        "ST12GReadinessEvidenceProjectionV2",
        "ST12GPretradeEvidenceProjectionV2",
        "ST12GAgentEvidenceHandoffV2",
        "ST12GServiceEvidenceViewV2",
        "ST12GProjectionBundleV2",
        "ST12GProjectionAbsenceV2",
        "ST12GProjectionResolutionV2",
        "ST12GOwnerProjectionResolutionV2",
        "ST12GOwnerDashboardEvidenceViewV2",
        "ExistingOwnerProjectionCompilerV2",
        "ExistingOwnerProjectionCoordinatorV2",
    }
)
EXPECTED_CORE_FIELDS = (
    "core_id",
    "contract_version",
    "evaluation_context_id",
    "evaluated_at",
    "source_handoff_receipt_ref",
    "current_d_reference_receipt_ref",
    "current_d_reference_id",
    "handoff_id",
    "input_lock_id",
    "source_epoch_refs",
    "observed_at",
    "valid_until",
    "terminal_state",
    "evidence_bundle_ref",
    "evidence_id",
    "evidence_bundle_version",
    "component_or_template_ref",
    "independent_review_state",
    "actual_executed_component_versions",
    "actual_executed_stack_version_state",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "failure_and_negative_evidence_state",
    "source_and_provenance_refs",
    "bundle_blocker_state",
    "no_trade_blocker_reference_state",
    "champion_challenger_reference_state",
    "portfolio_utility_reference_state",
    "quantum_classical_comparison_receipt_ref",
    "runtime_authority",
    "no_effect_flags",
)
EXPECTED_TYPE_FIELDS = {
    "ST12GProjectionRequestV2": (
        "request_id",
        "context",
        "source_handoff_receipt_ref",
        "causation_id",
        "correlation_id",
    ),
    "ST12GReadinessEvidenceProjectionV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "evidence_readiness_state",
        "runtime_instance_state",
        "activation_authority",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GPretradeEvidenceProjectionV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "pretrade_evidence_state",
        "no_trade_route_state",
        "submit_authority_created",
        "order_authority_created",
        "profit_claim_created",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GAgentEvidenceHandoffV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "task_class",
        "allowed_operation",
        "self_promotion_allowed",
        "historical_rewrite_allowed",
        "owner_review_route",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GServiceEvidenceViewV2": (
        "projection_id",
        "projection_contract_version",
        "consumer_id",
        "core",
        "read_model_class",
        "stale_state",
        "action_eligibility_state",
        "fake_receipt_allowed",
        "runtime_execution_allowed",
        "runtime_effect_allowed",
        "write_authority",
    ),
    "ST12GOwnerDashboardEvidenceViewV2": (
        "projection_id",
        "contract_version",
        "consumer_id",
        "source_svc_resolution_state",
        "source_svc_projection_id_or_explicit_absence",
        "panel_id",
        "availability_badge",
        "stale_banner_state",
        "owner_safe_next_action",
        "direct_f_binding_allowed",
        "live_control_authority",
        "source_lineage_state",
        "no_effect_flags",
        "runtime_effect_allowed",
        "write_authority",
    ),
}
EXPECTED_DESCRIPTOR_FIELDS = frozenset(
    {
        "descriptor_id",
        "contract_version",
        "consumer_id",
        "contract_type",
        "source_contract_manifest_ref",
        "canonical_owner_ref",
        "runtime_instance_state",
        "manual_edit_allowed",
        "runtime_effect_allowed",
        "write_authority",
        "downstream_route_refs",
    }
)
CENTRAL_MANIFEST = (
    "docs/master_plan/generated/qku_control_plane/existing_owner_projection/"
    "st12g_projection_contract_manifest.json"
)
DESCRIPTORS = {
    "READINESS1": (
        "docs/master_plan/generated/pr169_readiness1/"
        "st12g_evidence_projection_contract.generated.jsonl",
        "ST12GReadinessEvidenceProjectionV2",
        ("READINESS1",),
    ),
    "PRETRADE1": (
        "docs/master_plan/generated/pr169_pretrade1/"
        "st12g_evidence_projection_contract.generated.jsonl",
        "ST12GPretradeEvidenceProjectionV2",
        ("PRETRADE1",),
    ),
    "AGENT_ORCH1": (
        "docs/master_plan/generated/pr169_agent_orch1/"
        "st12g_evidence_handoff_contract.generated.jsonl",
        "ST12GAgentEvidenceHandoffV2",
        ("AGENT_ORCH1",),
    ),
    "SVC1": (
        "docs/master_plan/generated/pr169_svc1/"
        "st12g_evidence_view_contract.generated.jsonl",
        "ST12GServiceEvidenceViewV2",
        ("SVC1", "DASH1_UI1"),
    ),
    "DASH1_UI1": (
        "docs/master_plan/generated/pr169_dash1/"
        "st12g_evidence_owner_view_contract.generated.jsonl",
        "ST12GOwnerDashboardEvidenceViewV2",
        ("DASH1_UI1",),
    ),
}
EXPECTED_HISTORICAL_IDS = frozenset(
    {
        "ST12-TEST::026",
        "ST12-TEST::027",
        "ST12-TEST::028",
        "ST12-TEST::103",
        "ST12-TEST::109",
        "ST12-TEST::117",
        "ST12-TEST::118",
        "ST12-TEST::141",
        "ST12-TEST::144",
        "ST12-TEST::145",
        "ST12-TEST::155",
        "ST12-TEST::160",
        "ST12-TEST::222",
        "ST12-TEST::226",
        "ST12-TEST::228",
    }
)


def _read_json(path: str) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        (REPO_ROOT / path).read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON constant: {value}")
        ),
    )


def _read_one_jsonl(path: str) -> dict[str, object]:
    lines = [
        line
        for line in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(lines) != 1:
        raise ValueError(f"{path} must contain exactly one row")
    value = json.loads(lines[0])
    if type(value) is not dict:
        raise ValueError(f"{path} row must be an object")
    return value


def _field_names(contract: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(contract))


def _function(tree: ast.Module, class_name: str, function_name: str) -> ast.FunctionDef:
    owner = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in owner.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )


def _test_contract_failures() -> list[str]:
    failures: list[str] = []
    if frozenset(projection.__all__) != EXPECTED_PUBLIC_NAMES:
        failures.append("public ST12-G type roster differs")
    if _field_names(projection.ST12GProjectionCoreV2) != EXPECTED_CORE_FIELDS:
        failures.append("shared core is not the exact ordered 33-field contract")
    for type_name, expected_fields in EXPECTED_TYPE_FIELDS.items():
        if _field_names(getattr(projection, type_name)) != expected_fields:
            failures.append(f"field roster differs: {type_name}")
    for type_name in EXPECTED_PUBLIC_NAMES:
        value = getattr(projection, type_name)
        if hasattr(value, "__dataclass_fields__"):
            params = value.__dataclass_params__
            if not params.frozen or not hasattr(value, "__slots__"):
                failures.append(f"contract is not frozen and slotted: {type_name}")
    if projection.ExistingOwnerProjectionCompilerV2.__slots__ != ():
        failures.append("compiler owns state")
    signature = tuple(
        inspect.signature(
            projection.ExistingOwnerProjectionCompilerV2.compile_current
        ).parameters
    )
    if signature != (
        "self",
        "context",
        "input_lock",
        "handoff",
        "bundle",
        "current_d_reference",
        "owner_views",
    ):
        failures.append("compiler input roster differs")

    source_path = (
        REPO_ROOT
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "existing_owner_projection.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    compiler = _function(tree, "ExistingOwnerProjectionCompilerV2", "compile_current")
    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "connect",
        "request",
        "urlopen",
    }
    if any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
            or isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_calls
        )
        for node in ast.walk(compiler)
    ):
        failures.append("compiler contains I/O or provider call")
    coordinator = _function(
        tree,
        "ExistingOwnerProjectionCoordinatorV2",
        "resolve",
    )
    call_counts = {
        method: sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == method
            for node in ast.walk(coordinator)
        )
        for method in (
            "resolve_g_handoff",
            "resolve_control_receipt",
            "resolve_bundle",
            "read_evidence_reference",
        )
    }
    if set(call_counts.values()) != {1}:
        failures.append(f"coordinator durable-read budget differs: {call_counts}")
    return failures


def _materialization_failures() -> list[str]:
    failures: list[str] = []
    manifest = _read_json(CENTRAL_MANIFEST)
    if type(manifest) is not dict:
        return ["central manifest is not an object"]
    if (
        manifest.get("contract_version") != "2.0"
        or manifest.get("shared_core_field_count") != 33
        or manifest.get("source_binding_row_count") != 71
        or manifest.get("direct_consumer_ids")
        != ["READINESS1", "PRETRADE1", "AGENT_ORCH1", "SVC1"]
        or manifest.get("derived_consumer_id") != "DASH1_UI1"
        or manifest.get("runtime_instance_state")
        != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
        or manifest.get("runtime_effect_allowed") is not False
        or manifest.get("write_authority") != "NONE"
    ):
        failures.append("central materialization manifest differs")
    if manifest.get("owner_descriptor_refs") != [
        details[0] for details in DESCRIPTORS.values()
    ]:
        failures.append("central owner descriptor roster differs")
    no_effects = manifest.get("no_effect_flags")
    if type(no_effects) is not dict or len(no_effects) != 8 or any(no_effects.values()):
        failures.append("central no-effect roster differs")

    for consumer_id, (path, contract_type, downstream) in DESCRIPTORS.items():
        row = _read_one_jsonl(path)
        if frozenset(row) != EXPECTED_DESCRIPTOR_FIELDS:
            failures.append(f"descriptor field roster differs: {consumer_id}")
            continue
        if (
            row["descriptor_id"] != f"ST12G-DESCRIPTOR::{consumer_id}"
            or row["contract_version"] != "2.0"
            or row["consumer_id"] != consumer_id
            or row["contract_type"] != contract_type
            or row["source_contract_manifest_ref"] != CENTRAL_MANIFEST
            or row["runtime_instance_state"]
            != "NOT_MATERIALIZED_BY_REPOSITORY_BUILD"
            or row["manual_edit_allowed"] is not False
            or row["runtime_effect_allowed"] is not False
            or row["write_authority"] != "NONE"
            or row["downstream_route_refs"] != list(downstream)
        ):
            failures.append(f"descriptor value contract differs: {consumer_id}")
        if any(
            forbidden in row
            for forbidden in ("runtime_evidence", "evidence_value", "owner_decision")
        ):
            failures.append(f"descriptor fabricates runtime evidence: {consumer_id}")
    return failures


def _test_partition_failures() -> list[str]:
    failures: list[str] = []
    test_paths = (
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_g/test_contract_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_g/test_consumer_integration_matrix.py",
    )
    trees = [
        ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"))
        for path in test_paths
    ]
    test_functions = {
        node.name
        for tree in trees
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    if test_functions != {"test_st12g_contract_case", "test_st12g_consumer_case"}:
        failures.append("created test function roster differs")
    strings = {
        node.value
        for tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    historical = {
        value for value in strings if re.fullmatch(r"ST12-TEST::\d{3}", value)
    }
    fail_closed = {
        value for value in strings if re.fullmatch(r"G-FAIL::\d{3}", value)
    }
    if historical != EXPECTED_HISTORICAL_IDS:
        failures.append("historical semantic identity roster differs")
    if fail_closed != {f"G-FAIL::{index:03d}" for index in range(1, 71)}:
        failures.append("70-case fail-closed roster differs")
    return failures


def _validation_wiring_failures() -> list[str]:
    failures: list[str] = []
    if scope.ST12G_BRANCH != EXPECTED_BRANCH:
        failures.append("authorized branch differs")
    if len(scope.ST12G_ALLOWED_EXACT_PATHS) != 65:
        failures.append("authorized path denominator differs")
    if len(scope.ST12G_FORBIDDEN_EXACT_PATHS) != 7:
        failures.append("forbidden path denominator differs")
    if any("*" in path for path in scope.ST12G_ALLOWED_EXACT_PATHS):
        failures.append("authorized path registry contains wildcard")
    if ci_branch_context.is_owner_authorized_validation_branch(
        f"{EXPECTED_BRANCH}-near"
    ):
        failures.append("near-name branch accepted")
    if not ci_branch_context.is_owner_authorized_validation_branch(EXPECTED_BRANCH):
        failures.append("exact authorized branch rejected")
    expected_commands = (
        "python tools/validate_qku_computation_control_plane.py --domain g",
        "python tools/independent_validate_qku_computation_control_plane_g.py",
        "python tools/validate_validation_inventory.py",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_contract_matrix.py -q",
        "python -m pytest tests/stage1_prediction_markets/qku_computation_control_plane/tranche_g/test_consumer_integration_matrix.py -q",
        "python tools/run_validation_gates.py --phase all --validation-mode full",
    )
    if inventory.ST12G_EXACT_VALIDATION_COMMANDS != expected_commands:
        failures.append("six-command validation roster differs")
    known = inventory.inventory_by_id()
    missing = inventory.ST12G_REQUIRED_VALIDATOR_IDS - known.keys()
    if missing:
        failures.append(f"registered ST12-G validators missing: {sorted(missing)}")
    classified = router._classify_changed_files(
        tuple(sorted(scope.ST12G_ALLOWED_EXACT_PATHS))
    )[0]
    for path in scope.ST12G_ALLOWED_EXACT_PATHS:
        routed = set(classified.get(path, ()))
        if not inventory.ST12G_REQUIRED_VALIDATOR_IDS <= routed:
            failures.append(f"incomplete ST12-G route: {path}")
            break
    return failures


def main() -> int:
    failures: list[str] = []
    for validator in (
        _test_contract_failures,
        _materialization_failures,
        _test_partition_failures,
        _validation_wiring_failures,
    ):
        try:
            failures.extend(validator())
        except Exception as exc:
            failures.append(f"{validator.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print("QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENT_G_VALIDATION_FAILED")
        for failure in failures:
            print(failure)
        return 1
    print(
        f"{SUCCESS_MARKER} public_types=20 core_fields=33 owners=5 "
        "field_bindings=71 historical_cases=15 fail_closed_cases=70 "
        "authorized_paths=65 validation_commands=6"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
