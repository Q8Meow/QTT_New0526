#!/usr/bin/env python3
"""Independent exact operation-roster and no-runtime validation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import sys
from types import MappingProxyType


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "multiprocessing",
    "requests",
    "socket",
    "sqlite3",
    "subprocess",
    "threading",
}
FORBIDDEN_CALL_NAMES = {
    "connect",
    "create_connection",
    "listen",
    "Popen",
    "run",
    "serve_forever",
    "start",
}


@dataclass(frozen=True, slots=True)
class RuntimeTopologyExceptionV1:
    """One exact non-production standard-library runtime exception."""

    file_name: str
    allowed_import: str
    allowed_qualified_call: str
    adapter_class_name: str
    production_marker_name: str


RUNTIME_TOPOLOGY_EXCEPTIONS = MappingProxyType(
    {
        "sqlite_reference.py": RuntimeTopologyExceptionV1(
            file_name="sqlite_reference.py",
            allowed_import="sqlite3",
            allowed_qualified_call="sqlite3.connect",
            adapter_class_name="SQLiteReferenceAdapterV1",
            production_marker_name="is_production_adapter",
        )
    }
)
COMMON_REQUEST_FIELDS = (
    ("request_id", "str"),
    ("operation_name", "CertifiedOperationNameV1"),
    ("requested_at", "TimezoneAwareDateTimeV1"),
    ("principal_id", "str"),
    ("capability_bundle_id", "str"),
    ("context", "ComputationContextKeyV1"),
    ("idempotency_key", "EconomicIdempotencyKeyV1"),
    ("traceparent", "W3CTraceparentV1"),
    ("tracestate", "W3CTracestateV1"),
)
COMMON_RESPONSE_FIELDS = (
    ("response_id", "str"),
    ("operation_name", "CertifiedOperationNameV1"),
    ("request_id", "str"),
    ("completed_at", "TimezoneAwareDateTimeV1"),
    ("status", "OperationStatusV1"),
    ("context", "ComputationContextKeyV1"),
    ("warnings", "tuple[str,...]"),
    ("blocker_codes", "tuple[OperationBlockerCodeV1,...]"),
    ("receipt_refs", "tuple[str,...]"),
    ("traceparent", "W3CTraceparentV1"),
    ("tracestate", "W3CTracestateV1"),
)
EXPECTED_ROWS = (
    (
        "ST10-OP::01",
        "resolve_identity",
        "UnifiedCanonicalIdentityPlaneV1",
        "ResolveIdentityRequestV1",
        "ResolveIdentityResponseV1",
        (("identity_query", "TypedValueRecordV1"),),
        ("identity_resolution", "IdentityResolutionV1"),
        None,
    ),
    (
        "ST10-OP::02",
        "resolve_contextual_computability",
        "QKUComputationControlPlaneV1",
        "ResolveContextualComputabilityRequestV1",
        "ResolveContextualComputabilityResponseV1",
        (
            ("component_id", "str"),
            ("required_computability_classes", "tuple[ComputabilityClassV1,...]"),
        ),
        ("computability", "ContextualComputabilityResolutionV1"),
        "ContextualComputabilityResolverV1.resolve",
    ),
    (
        "ST10-OP::03",
        "resolve_applicable_stack",
        "QKUComputationControlPlaneV1",
        "ResolveApplicableStackRequestV1",
        "ResolveApplicableStackResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("required_launch_roles", "tuple[str,...]"),
        ),
        ("stack_resolution", "StackResolutionV1"),
        None,
    ),
    (
        "ST10-OP::04",
        "resolve_required_inputs",
        "QKUComputationControlPlaneV1",
        "ResolveRequiredInputsRequestV1",
        "ResolveRequiredInputsResponseV1",
        (
            ("component_ids", "tuple[str,...]"),
            ("include_optional", "bool"),
        ),
        ("input_resolution", "InputResolutionV1"),
        None,
    ),
    (
        "ST10-OP::05",
        "compute_component",
        "QKUComputationControlPlaneV1",
        "ComputeComponentRequestV1",
        "ComputeComponentResponseV1",
        (
            ("component_id", "str"),
            ("input_values", "TypedValueRecordV1"),
            ("expected_output_schema_ref", "str"),
        ),
        ("component_result", "ComponentResultV1"),
        None,
    ),
    (
        "ST10-OP::06",
        "compute_stack",
        "QKUComputationControlPlaneV1",
        "ComputeStackRequestV1",
        "ComputeStackResponseV1",
        (
            ("stack_id", "str"),
            ("component_ids", "tuple[str,...]"),
            ("input_values", "TypedValueRecordV1"),
        ),
        ("stack_result", "StackResultV1"),
        None,
    ),
    (
        "ST10-OP::07",
        "compare_with_no_trade",
        "QKUComputationControlPlaneV1",
        "CompareWithNoTradeRequestV1",
        "CompareWithNoTradeResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("no_trade_candidate_id", "str"),
            ("comparison_basis", "str"),
        ),
        ("comparison", "NoTradeComparisonV1"),
        None,
    ),
    (
        "ST10-OP::08",
        "evaluate_trade_plan",
        "QKUComputationControlPlaneV1",
        "EvaluateTradePlanRequestV1",
        "EvaluateTradePlanResponseV1",
        (
            ("trade_plan_candidate_id", "str"),
            ("stack_id", "str"),
            ("accounting_tca_view_ref", "str"),
            ("risk_cash_state_ref", "str"),
            ("no_trade_candidate_id", "str"),
        ),
        ("evaluation", "TradePlanEvaluationV1"),
        None,
    ),
    (
        "ST10-OP::09",
        "get_snapshot_view",
        "QKUComputationControlPlaneV1",
        "GetSnapshotViewRequestV1",
        "GetSnapshotViewResponseV1",
        (
            ("snapshot_id", "str"),
            ("view_class", "str"),
            ("include_value_lineage", "bool"),
        ),
        ("snapshot_view", "SnapshotViewV1"),
        None,
    ),
    (
        "ST10-OP::10",
        "explain_resolution",
        "QKUComputationControlPlaneV1",
        "ExplainResolutionRequestV1",
        "ExplainResolutionResponseV1",
        (
            ("resolution_receipt_id", "str"),
            ("explanation_scope", "str"),
            ("max_evidence_items", "int"),
        ),
        ("explanation", "ResolutionExplanationV1"),
        None,
    ),
    (
        "ST10-OP::11",
        "submit_candidate_proposal",
        "QKUComputationControlPlaneV1",
        "SubmitCandidateProposalRequestV1",
        "SubmitCandidateProposalResponseV1",
        (
            ("candidate_kind", "str"),
            ("proposed_specification", "TypedValueRecordV1"),
            ("source_candidate_refs", "tuple[str,...]"),
            ("requested_owner_review", "bool"),
        ),
        ("proposal", "CandidateProposalV1"),
        None,
    ),
    (
        "ST10-OP::12",
        "request_materialization_work_order",
        "QKUComputationControlPlaneV1",
        "RequestMaterializationWorkOrderRequestV1",
        "RequestMaterializationWorkOrderResponseV1",
        (
            ("missing_contract_ids", "tuple[str,...]"),
            ("reason_codes", "tuple[OperationBlockerCodeV1,...]"),
            ("priority", "str"),
            ("requested_owner", "str"),
        ),
        ("work_order", "MaterializationWorkOrderV1"),
        None,
    ),
    (
        "ST10-OP::13",
        "compile_replay_paper_cohort",
        "ReplayPaperCohortCompilerV1",
        "CompileReplayPaperCohortRequestV1",
        "CompileReplayPaperCohortResponseV1",
        (
            ("template_ids", "tuple[str,...]"),
            ("requested_lanes", "tuple[str,...]"),
            ("input_lock_id", "str"),
            ("campaign_execution_requested", "bool"),
        ),
        ("cohort_compilation", "ReplayPaperCohortCompilationV1"),
        None,
    ),
    (
        "ST10-OP::14",
        "register_replay_paper_result",
        "ComputationEvidenceServiceV1",
        "RegisterReplayPaperResultRequestV1",
        "RegisterReplayPaperResultResponseV1",
        (
            ("cohort_instance_id", "str"),
            ("lane", "str"),
            ("input_lock_id", "str"),
            ("result_packet", "TypedValueRecordV1"),
        ),
        ("registration", "ReplayPaperResultRegistrationV1"),
        None,
    ),
    (
        "ST10-OP::15",
        "build_evidence_bundle",
        "ComputationEvidenceServiceV1",
        "BuildEvidenceBundleRequestV1",
        "BuildEvidenceBundleResponseV1",
        (
            ("component_id", "str"),
            ("input_lock_id", "str"),
            ("evidence_record_refs", "tuple[str,...]"),
            ("required_lanes", "tuple[str,...]"),
        ),
        ("evidence_bundle", "EvidenceBundleResultV1"),
        None,
    ),
)
SUCCESS_MARKER = "QKU_OPERATIONS_INDEPENDENTLY_VALIDATED"


def _assignment(tree: ast.Module, name: str) -> ast.expr | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node.value
    return None


def _class_fields(tree: ast.Module, name: str) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return tuple(
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.target.id != "EXPECTED_OPERATION_NAME"
            )
    return ()


def _parse_operation_rows(tree: ast.Module) -> tuple[tuple[object, ...], ...]:
    value = _assignment(tree, "_OPERATION_ROWS")
    if not isinstance(value, ast.Tuple):
        return ()
    rows: list[tuple[object, ...]] = []
    for item in value.elts:
        if (
            not isinstance(item, ast.Call)
            or not isinstance(item.func, ast.Name)
            or item.func.id != "_operation_contract"
            or len(item.args) not in {7, 8}
            or not isinstance(item.args[3], ast.Name)
            or not isinstance(item.args[4], ast.Name)
        ):
            return ()
        try:
            rows.append(
                (
                    ast.literal_eval(item.args[0]),
                    ast.literal_eval(item.args[1]),
                    ast.literal_eval(item.args[2]),
                    item.args[3].id,
                    item.args[4].id,
                    ast.literal_eval(item.args[5]),
                    ast.literal_eval(item.args[6]),
                    ast.literal_eval(item.args[7]) if len(item.args) == 8 else None,
                )
            )
        except (ValueError, TypeError):
            return ()
    return tuple(rows)


def _qualified_callable_name(node: ast.expr) -> str:
    """Return the complete statically qualified name for a call target."""

    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _qualified_callable_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _has_exact_false_marker(
    tree: ast.Module,
    *,
    class_name: str,
    marker_name: str,
) -> bool:
    matching_classes = tuple(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    if len(matching_classes) != 1:
        return False
    marker_values: list[ast.expr] = []
    for statement in matching_classes[0].body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == marker_name
            for target in statement.targets
        ):
            marker_values.append(statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == marker_name
        ):
            marker_values.append(statement.value)
    return (
        len(marker_values) == 1
        and isinstance(marker_values[0], ast.Constant)
        and marker_values[0].value is False
    )


def _runtime_topology_failures(
    file_name: str,
    tree: ast.Module,
) -> tuple[str, ...]:
    policy = RUNTIME_TOPOLOGY_EXCEPTIONS.get(file_name)
    failures: list[str] = []
    permitted_import_count = 0
    permitted_call_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in FORBIDDEN_IMPORT_ROOTS:
                    continue
                is_exact_exception = (
                    policy is not None
                    and len(node.names) == 1
                    and alias.name == policy.allowed_import
                    and alias.asname is None
                )
                if is_exact_exception:
                    permitted_import_count += 1
                else:
                    failures.append(f"runtime import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                failures.append(f"runtime import {node.module}")
        elif isinstance(node, ast.Call):
            qualified_name = _qualified_callable_name(node.func)
            is_exact_exception = (
                policy is not None
                and qualified_name == policy.allowed_qualified_call
            )
            if is_exact_exception:
                permitted_call_count += 1
                continue
            terminal_name = qualified_name.rsplit(".", 1)[-1]
            if terminal_name in FORBIDDEN_CALL_NAMES:
                failures.append(f"runtime call {qualified_name or terminal_name}")
    if policy is not None:
        if permitted_import_count != 1:
            failures.append(
                f"reference exception requires exactly one import {policy.allowed_import}"
            )
        if permitted_call_count != 1:
            failures.append(
                "reference exception requires exactly one call "
                f"{policy.allowed_qualified_call}"
            )
        if not _has_exact_false_marker(
            tree,
            class_name=policy.adapter_class_name,
            marker_name=policy.production_marker_name,
        ):
            failures.append(
                f"{policy.adapter_class_name}.{policy.production_marker_name} "
                "must be literal False"
            )
    return tuple(failures)


def validate_runtime_topology_source(
    *,
    file_name: str,
    source: str,
) -> tuple[str, ...]:
    """Validate a source fragment against the exact centralized runtime policy."""

    tree = ast.parse(source, filename=file_name)
    return _runtime_topology_failures(file_name, tree)


def main() -> int:
    failures: list[str] = []
    parsed: dict[str, ast.Module] = {}
    for path in sorted(PACKAGE.glob("*.py"), key=lambda item: item.name):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed[path.name] = tree
        failures.extend(
            f"{path.name}: {failure}"
            for failure in _runtime_topology_failures(path.name, tree)
        )
    validation = parsed.get("validation.py")
    models = parsed.get("models.py")
    if validation is None or models is None:
        failures.append("operation registry source is absent")
    else:
        common_request = _assignment(validation, "_COMMON_OPERATION_REQUEST_FIELDS")
        common_response = _assignment(validation, "_COMMON_OPERATION_RESPONSE_FIELDS")
        if (
            common_request is None
            or ast.literal_eval(common_request) != COMMON_REQUEST_FIELDS
        ):
            failures.append("common request fields differ from the certified schema")
        if (
            common_response is None
            or ast.literal_eval(common_response) != COMMON_RESPONSE_FIELDS
        ):
            failures.append("common response fields differ from the certified schema")
        actual_rows = _parse_operation_rows(validation)
        if actual_rows != EXPECTED_ROWS:
            failures.append("operation roster differs from the exact certified roster")
        if _class_fields(models, "OperationRequestEnvelopeV1") != tuple(
            name for name, _type_name in COMMON_REQUEST_FIELDS
        ):
            failures.append("request envelope top-level fields are not exact")
        if _class_fields(models, "OperationResponseEnvelopeV1") != tuple(
            name for name, _type_name in COMMON_RESPONSE_FIELDS
        ):
            failures.append("response envelope top-level fields are not exact")
        for row in EXPECTED_ROWS:
            request_type = str(row[3])
            response_type = str(row[4])
            request_tail = tuple(name for name, _type_name in row[5])
            response_tail = (row[6][0],)
            if _class_fields(models, request_type) != request_tail:
                failures.append(f"{request_type}: request fields differ")
            if _class_fields(models, response_type) != response_tail:
                failures.append(f"{response_type}: response fields differ")
        model_text = (PACKAGE / "models.py").read_text(encoding="utf-8")
        validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
        for forbidden in ("payload_json", "result_json", "typing.Any"):
            if forbidden in model_text or forbidden in validation_text:
                failures.append(f"untyped operation surface remains: {forbidden}")
        for required in (
            "schema_version=\"1.4.0\"",
            "PURE_OR_APPEND_ONLY_NON_PROVIDER_EFFECT",
            "CONTRACT_DEFINITION_ONLY",
            "ContextualComputabilityResolverV1.resolve",
            "_validate_trace_context",
            "deterministic_json",
        ):
            if required not in model_text and required not in validation_text:
                failures.append(f"operation invariant is absent: {required}")
    forbidden_files = {
        "runtime.py",
        "supervision.py",
        "backup.py",
        "database.py",
    }
    if forbidden_files & {path.name for path in PACKAGE.glob("*.py")}:
        failures.append("a later-tranche runtime module exists")
    service = parsed.get("service.py")
    if service is None:
        failures.append("the centralized Tranche-B service extension is absent")
    else:
        service_class_nodes = tuple(
            node for node in service.body if isinstance(node, ast.ClassDef)
        )
        service_classes = {node.name for node in service_class_nodes}
        if service_classes != {"QKUComputationControlPlaneV1"}:
            failures.append("the central service class roster is not exact")
        else:
            service_methods = {
                node.name
                for node in service_class_nodes[0].body
                if isinstance(node, ast.FunctionDef)
            }
            expected_methods = {
                "__post_init__",
                *(str(row[1]) for row in EXPECTED_ROWS[:12]),
            }
            if service_methods != expected_methods:
                failures.append(
                    "the central service does not expose exactly operations 01..12"
                )
        if any(
            isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
            for node in ast.walk(service)
        ):
            failures.append("the central service catches an untyped broad exception")
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    for required in (
        "ST12B_CENTRAL_SERVICE_OPERATION_IDS = tuple(OPERATION_SCHEMA_REGISTRY)[:12]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[:8]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[8:10]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[10:12]",
        "tuple(OPERATION_SCHEMA_REGISTRY)[12:]",
    ):
        if required not in validation_text:
            failures.append(f"Tranche-B operation capability projection missing: {required}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} operation_contracts={len(EXPECTED_ROWS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
