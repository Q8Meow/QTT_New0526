#!/usr/bin/env python3
"""Independent static ST12-E validator; production values are never imported."""

from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
)
ARTIFACTS = (
    REPO_ROOT
    / "docs/master_plan/generated/qku_control_plane/agent_capability"
)
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_E_INDEPENDENTLY_VALIDATED"
DOMAIN_PREFIXES = {
    "agent": "ST12-CLOSURE::ST11-AGENT::",
    "llm": "ST12-CLOSURE::ST11-LLM::",
    "security": "ST12-CLOSURE::ST11-SECURITY::",
}
FORBIDDEN_PARALLEL_PATHS = (
    "capability_adapter.py",
    "agent_orch_adapter.py",
    "capability_enforcement.py",
    "principal_scope.py",
    "operation_authorization.py",
    "no_authority.py",
    "direct_provider_guard.py",
    "agent_parameter_capability.py",
)
FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "boto3",
    "ccxt",
    "cirq",
    "dwave",
    "ib_insync",
    "openai",
    "pennylane",
    "qiskit",
    "requests",
    "robin_stocks",
}
REQUIRED_REASON_NAMES = {
    "PRINCIPAL_UNKNOWN",
    "PRINCIPAL_AMBIGUOUS",
    "SOURCE_AGENT_ID_UNMAPPED",
    "SOURCE_AGENT_ID_SCOPE_BROADER_THAN_CURRENT_DUTY",
    "ROLE_MISMATCH",
    "DUTY_MISMATCH",
    "TASK_ENVELOPE_MISSING",
    "TASK_ENVELOPE_STALE",
    "TASK_SCOPE_MISMATCH",
    "OPERATION_NOT_ALLOWED",
    "QKU_SCOPE_MISMATCH",
    "FORMULA_SCOPE_MISMATCH",
    "DATA_SCOPE_MISMATCH",
    "TOOL_SCOPE_MISMATCH",
    "ACTION_SCOPE_MISMATCH",
    "CONTEXT_SCOPE_MISMATCH",
    "PARAMETER_SCOPE_MISMATCH",
    "BUDGET_EXCEEDED",
    "DEADLINE_EXCEEDED",
    "RETRY_NOT_ALLOWED",
    "IDEMPOTENCY_CONFLICT",
    "SEGREGATION_OF_DUTIES_VIOLATION",
    "SELF_PROMOTION_FORBIDDEN",
    "SELF_QUARANTINE_RELEASE_FORBIDDEN",
    "PEER_CHALLENGE_REQUIRED",
    "TRUST_STATE_INSUFFICIENT",
    "QUARANTINED",
    "MEMORY_PRIOR_REVALIDATION_REQUIRED",
    "LLM_ADVISORY_ONLY",
    "LLM_TOOL_NOT_ALLOWED",
    "UNTRUSTED_CONTENT_INSTRUCTION_REJECTED",
    "DIRECT_PROVIDER_FORBIDDEN",
    "PRIVATE_STATE_FORBIDDEN",
    "SOURCE_TRUTH_FORBIDDEN",
    "REPLAY_PAPER_EFFECT_FORBIDDEN",
    "LLM_INFERENCE_FORBIDDEN",
    "QPU_EFFECT_FORBIDDEN",
    "MODE_ACTIVATION_FORBIDDEN",
    "ORDER_RELEASE_FORBIDDEN",
    "CAPITAL_EFFECT_FORBIDDEN",
    "SAFETY_STATE_MISSING",
    "SAFETY_STATE_STALE",
    "SAFETY_STATE_CONFLICT",
    "EXECUTION_ROUTER_BYPASS_FORBIDDEN",
    "NO_TRADE_REOPTIMIZATION_REQUIRED",
    "OWNER_REVIEW_REQUIRED",
}
EXPECTED_NO_TRADE_VARIABLE_IDS = (
    "market",
    "venue",
    "stack",
    "side",
    "entry",
    "size",
    "hold_duration",
    "exit_rule",
    "maker_taker_split",
    "cancel_replace_interval",
    "liquidity_filter",
    "spread_filter",
    "latency_budget",
    "portfolio_exposure",
    "source_refresh",
    "retest_batch",
    "next_target",
)
EXPECTED_QUANTUM_FORMULATION_FIELDS = (
    "problem_id",
    "formulation_version",
    "objective_sense",
    "decision_variable_ids",
    "decision_variable_domains",
    "linear_coefficient_vector_ref",
    "quadratic_coefficient_matrix_ref",
    "constraint_matrix_or_expression_refs",
    "right_hand_side_refs",
    "coefficient_units_and_basis",
    "scaling_and_normalization_policy_ref",
    "penalty_or_native_constraint_policy_ref",
    "original_economic_model_ref",
    "inverse_mapping_ref",
    "original_model_feasibility_recheck_ref",
    "same_formulation_classical_comparator_ref",
    "provider_backend_state_ref_or_explicit_unavailable_state",
    "queue_cost_latency_budget_refs",
    "result_ttl",
    "classical_fallback",
    "no_trade_fallback",
)
EXPECTED_LLM_ADVISORY_TASK_FIELDS = (
    "structured_task_type",
    "redacted_context_refs",
    "untrusted_content_boundary",
    "allowlisted_tool_refs",
    "closed_output_schema_ref",
    "citation_provenance_requirements",
    "numerical_recheck_requirement",
    "source_truth_prohibition",
    "risk_mode_order_prohibition",
    "latency_token_cost_tool_budgets",
    "abstention_route",
)
REQUIRED_NO_EFFECT_FLAG_NAMES = {
    "provider_connection_allowed",
    "private_state_read_allowed",
    "replay_or_paper_execution_allowed",
    "mode_or_grant_activation_allowed",
    "order_release_allowed",
    "qpu_execution_allowed",
    "profit_or_quantum_advantage_claim_allowed",
    "master_plan_mutation_authorized",
    "merge_canary_live_or_launch_allowed",
    "llm_inference_allowed",
}


def _jsonl(path: Path) -> tuple[dict[str, object], ...]:
    rows = tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} contains a non-object row")
    return rows


def _class_methods(tree: ast.Module, class_name: str) -> dict[str, ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name: child
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            }
    return {}


def validate_domain(domain: str) -> list[str]:
    failures: list[str] = []
    if domain not in DOMAIN_PREFIXES:
        return [f"unknown E validation domain: {domain}"]
    try:
        manifest = json.loads(
            (ARTIFACTS / "manifest.json").read_text(encoding="utf-8")
        )
        policy = _jsonl(ARTIFACTS / "policy.jsonl")
        parameter_scope = _jsonl(ARTIFACTS / "parameter_scope.jsonl")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"generated E policy cannot be loaded: {exc}"]

    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        return ["manifest counts owner is missing"]
    typed_counts = {
        key: value
        for key, value in counts.items()
        if isinstance(key, str)
        and isinstance(value, int)
        and not isinstance(value, bool)
    }
    if typed_counts != counts or any(value <= 0 for value in typed_counts.values()):
        failures.append("manifest counts must be positive typed integers")

    controls = tuple(row for row in policy if row.get("row_type") == "CONTROL")
    bindings = tuple(
        row
        for row in policy
        if row.get("row_type") == "PARAMETER_CAPABILITY_BINDING"
    )
    identities = tuple(
        row
        for row in policy
        if row.get("row_type") == "IDENTITY_COMPATIBILITY"
    )
    derived = {
        "closure_controls": len(controls),
        "repository_dispositions": len(
            tuple(manifest.get("repository_disposition_ids") or ())
        ),
        "parameter_bindings": len(bindings),
        "math_specifications": len(
            tuple(manifest.get("reused_math_oracle_vector_refs") or ())
        ),
        "independent_oracle_specifications": len(
            tuple(manifest.get("reused_math_oracle_vector_refs") or ())
        ),
        "golden_vectors_and_invariants": len(
            tuple(manifest.get("reused_math_oracle_vector_refs") or ())
        ),
        "semantic_test_rows": len(
            tuple(manifest.get("semantic_test_ids") or ())
        ),
        "validation_commands": len(
            tuple(manifest.get("validation_commands") or ())
        ),
        "parameter_source_universe": len(parameter_scope),
    }
    if derived != counts:
        failures.append(
            f"manifest-owned semantic counts differ from materialized rows: {derived}"
        )
    if manifest.get("policy_row_count") != len(policy):
        failures.append("manifest policy-row count differs from policy.jsonl")
    if manifest.get("identity_mapping_count") != len(identities):
        failures.append("manifest identity count differs from policy.jsonl")
    if manifest.get("parameter_scope_row_count") != len(parameter_scope):
        failures.append("manifest scope count differs from parameter_scope.jsonl")
    if (
        manifest.get("runtime_effect_authorized") is not False
        or manifest.get("manual_edit_allowed") is not False
        or manifest.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
        or manifest.get("no_effect_profile_ref") != "TRANCHE_A_AUTHORITY"
        or manifest.get("no_effect_authority_closed") is not True
    ):
        failures.append("manifest does not preserve the all-false no-effect boundary")
    no_effect_flags = manifest.get("no_effect_authority_flags")
    if (
        not isinstance(no_effect_flags, dict)
        or set(no_effect_flags) != REQUIRED_NO_EFFECT_FLAG_NAMES
        or any(value is not False for value in no_effect_flags.values())
    ):
        failures.append("manifest no-effect view differs from TRANCHE_A_AUTHORITY")
    if tuple(manifest.get("no_trade_reoptimization_variable_ids") or ()) != (
        EXPECTED_NO_TRADE_VARIABLE_IDS
    ):
        failures.append("NO_TRADE variable scope is not the exact bounded E set")
    if tuple(manifest.get("quantum_formulation_required_fields") or ()) != (
        EXPECTED_QUANTUM_FORMULATION_FIELDS
    ):
        failures.append("quantum readiness is not coefficient-level complete")
    if tuple(manifest.get("llm_advisory_task_fields") or ()) != (
        EXPECTED_LLM_ADVISORY_TASK_FIELDS
    ):
        failures.append("LLM advisory schema is not the exact no-authority contract")

    row_ids = [str(row.get("row_id") or "") for row in policy]
    if any(not row_id for row_id in row_ids) or len(row_ids) != len(set(row_ids)):
        failures.append("policy row identities are missing or duplicated")
    domain_controls = tuple(
        row
        for row in controls
        if str(row.get("closure_id") or "").startswith(DOMAIN_PREFIXES[domain])
    )
    if not domain_controls:
        failures.append(f"{domain} has no manifest-owned closure controls")
    required_lineage = {
        "semantic_owner",
        "implementation_owner",
        "producer_ref",
        "upstream_artifact_refs",
        "upstream_row_or_value_refs",
        "current_principal_duty_policy_refs",
        "downstream_consumer_refs",
        "lifecycle_state",
        "timing_or_snapshot_state",
        "activation_state",
        "terminal_route",
        "validator_ref",
    }
    for row in policy:
        if not required_lineage <= set(row):
            failures.append(f"{row.get('row_id')}: no-orphan lineage is incomplete")
        if row.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY":
            failures.append(f"{row.get('row_id')}: activation state is not no-effect")
    for row in bindings:
        if (
            row.get("capability_binding_owner") != "AgentCapabilityResolverV1"
            or row.get("formula_or_qku_mutation_authorized_by_st12e") is not False
            or row.get("value_mutation_authorized_by_st12e") is not False
            or row.get("no_trade_fallback_preserved") is not True
        ):
            failures.append(f"{row.get('row_id')}: E binding changes stronger semantics")

    scope_ids = [str(row.get("parameter_id") or "") for row in parameter_scope]
    expected_scope_ids = [
        f"ST10-PARAM::{value:04d}" for value in range(1, len(parameter_scope) + 1)
    ]
    if scope_ids != expected_scope_ids or len(scope_ids) != len(set(scope_ids)):
        failures.append("parameter scope is not one exact ordered contiguous universe")
    universe_defs = manifest.get("source_universe_definitions")
    if not isinstance(universe_defs, dict):
        failures.append("source universe definitions are missing")
        universe_defs = {}
    distribution = Counter(
        str(row.get("source_universe_id") or "") for row in parameter_scope
    )
    expected_distribution = {
        str(universe_id): row.get("parameter_count")
        for universe_id, row in universe_defs.items()
        if isinstance(row, dict)
    }
    if dict(distribution) != expected_distribution:
        failures.append("parameter scope distribution differs from manifest owner")
    exact_binding_ids = {
        str(row.get("parameter_id") or "") for row in bindings
    }
    exact_scope = tuple(
        row
        for row in parameter_scope
        if row.get("mapping_state") == "EXACT_E_BINDING_CURRENT_SCOPE"
    )
    blocked_scope = tuple(
        row
        for row in parameter_scope
        if row.get("mapping_state")
        == "CERTIFIED_AGGREGATE_ONLY_PER_ROW_CURRENTIZATION_REQUIRED"
    )
    if (
        {str(row.get("parameter_id") or "") for row in exact_scope}
        != exact_binding_ids
        or len(exact_scope) != len(bindings)
        or len(blocked_scope) != len(parameter_scope) - len(bindings)
        or manifest.get("parameter_scope_eligible_count") != len(exact_scope)
        or manifest.get("parameter_scope_blocker_count") != len(blocked_scope)
        or manifest.get("parameter_scope_distribution_is_aggregate_only") is not True
    ):
        failures.append("parameter scope eligibility/blocker accounting is not exact")
    identity_sources = {
        str(row.get("source_agent_id") or "") for row in identities
    }
    for row in parameter_scope:
        if (
            not row.get("current_principal_refs_or_gap")
            or not set(row.get("source_agent_ids") or ()) <= identity_sources
            or row.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
            or not row.get("value_policy_ref")
            or not row.get("downstream_consumer_refs")
            or not row.get("validator_ref")
            or not row.get("terminal_route")
            or not row.get("semantic_owner")
            or not row.get("implementation_owner")
            or not row.get("producer_ref")
            or not row.get("upstream_artifact_refs")
            or not row.get("upstream_row_or_value_refs")
            or not row.get("current_principal_duty_policy_refs")
        ):
            failures.append(
                f"{row.get('parameter_id')}: compact scope or route closure is invalid"
            )
            break
        mapping_state = row.get("mapping_state")
        if mapping_state == "EXACT_E_BINDING_CURRENT_SCOPE":
            if row.get("terminal_route") != "NO_EFFECT_QKU_REQUEST_OR_TYPED_DENIAL":
                failures.append(
                    f"{row.get('parameter_id')}: exact E scope has an invalid terminal route"
                )
                break
        elif mapping_state == "CERTIFIED_AGGREGATE_ONLY_PER_ROW_CURRENTIZATION_REQUIRED":
            if (
                row.get("current_principal_refs_or_gap")
                != ["PACKAGE_CURRENT_MAIN_SOURCE_UNIVERSE_ASSIGNMENT_GAP"]
                or row.get("terminal_route")
                != "SOURCE_UNIVERSE_PER_ROW_CURRENTIZATION_REVIEW_REQUIRED"
            ):
                failures.append(
                    f"{row.get('parameter_id')}: aggregate-only scope is not fail closed"
                )
                break
        else:
            failures.append(
                f"{row.get('parameter_id')}: parameter scope has an unknown mapping state"
            )
            break

    errors_tree = ast.parse(
        (PACKAGE / "errors.py").read_text(encoding="utf-8"),
        filename="errors.py",
    )
    reason_names = {
        statement.targets[0].id
        for node in errors_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ReasonCode"
        for statement in node.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        for _ in (0,)
    }
    # AnnAssign is not used by this enum, but keep the extraction explicit.
    reason_names |= {
        statement.target.id
        for node in errors_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ReasonCode"
        for statement in node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    }
    if not REQUIRED_REASON_NAMES <= reason_names:
        failures.append(
            f"central reason enum is missing {sorted(REQUIRED_REASON_NAMES - reason_names)}"
        )

    agent_path = PACKAGE / "agent_policy.py"
    agent_tree = ast.parse(agent_path.read_text(encoding="utf-8"), filename=str(agent_path))
    for node in ast.walk(agent_tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".", 1)[0] for alias in node.names}
            if roots & FORBIDDEN_IMPORT_ROOTS:
                failures.append(f"agent policy imports forbidden runtime provider {roots}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                failures.append(f"agent policy imports forbidden runtime provider {root}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"glob", "rglob"}:
                failures.append("agent policy performs a raw runtime discovery scan")
    resolver_methods = _class_methods(agent_tree, "AgentCapabilityResolverV1")
    if not {"resolve", "admit_operation"} <= set(resolver_methods):
        failures.append("central resolver lacks one admission path")

    service_tree = ast.parse(
        (PACKAGE / "service.py").read_text(encoding="utf-8"),
        filename="service.py",
    )
    service_methods = _class_methods(service_tree, "QKUComputationControlPlaneV1")
    admission_helper = next(
        (
            node
            for node in service_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_admit_agent_request"
        ),
        None,
    )
    if admission_helper is None or not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "admit_operation"
        for node in ast.walk(admission_helper)
    ):
        failures.append("the one module-level E admission helper is absent")
    implemented_names = tuple(
        name
        for name in manifest.get("implemented_operation_ids", ())
        if isinstance(name, str)
    )
    if not implemented_names:
        implemented_names = (
            "resolve_identity",
            "resolve_contextual_computability",
            "resolve_applicable_stack",
            "resolve_required_inputs",
            "compute_component",
            "compute_stack",
            "compare_with_no_trade",
            "evaluate_trade_plan",
            "get_snapshot_view",
            "explain_resolution",
            "submit_candidate_proposal",
            "request_materialization_work_order",
        )
    for name in implemented_names:
        method = service_methods.get(name)
        if method is None or not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_admit_agent_request"
            and tuple(
                arg.id for arg in node.args if isinstance(arg, ast.Name)
            )
            == ("self", "request")
            for node in ast.walk(method)
        ):
            failures.append(f"service operation lacks E admission: {name}")
    held_names = {
        "compile_replay_paper_cohort",
        "register_replay_paper_result",
        "build_evidence_bundle",
    }
    if held_names & set(service_methods):
        failures.append("held replay/PAPER operations were implemented in E")

    for name in FORBIDDEN_PARALLEL_PATHS:
        if (PACKAGE / name).exists():
            failures.append(f"parallel capability owner exists: {name}")
    if domain == "llm":
        source = agent_path.read_text(encoding="utf-8").casefold()
        if "llm_inference_forbidden" not in source or "untrusted_content" not in source:
            failures.append("LLM advisory/injection boundary is incomplete")
    if domain == "security":
        if not {
            "SAFETY_STATE_MISSING",
            "SAFETY_STATE_STALE",
            "SAFETY_STATE_CONFLICT",
        } <= reason_names:
            failures.append("read-only safety-state denial reasons are incomplete")
    return failures


def main(domain: str | None = None) -> int:
    selected = domain or "all"
    domains = tuple(DOMAIN_PREFIXES) if selected == "all" else (selected,)
    failures = [
        failure
        for current in domains
        for failure in validate_domain(current)
    ]
    if failures:
        print("\n".join(dict.fromkeys(failures)), file=sys.stderr)
        return 1
    print(f"{SUCCESS_MARKER} domain={selected}")
    return 0


if __name__ == "__main__":
    requested = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(main(requested))
