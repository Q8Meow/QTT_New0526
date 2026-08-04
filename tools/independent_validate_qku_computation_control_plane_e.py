#!/usr/bin/env python3
"""Independent behavioral and source-lineage validator for ST12-E."""

from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PACKAGE = (
    REPO_ROOT
    / "src/qtt/stage1_prediction_markets/qku_computation_control_plane"
)
ARTIFACTS = (
    REPO_ROOT
    / "docs/master_plan/generated/qku_control_plane/agent_capability"
)
MASTER_PLAN = REPO_ROOT / "docs/master_plan/QTT_MasterPlan_Current.md"
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_E_INDEPENDENTLY_VALIDATED"
DOMAIN_PREFIXES = {
    "agent": "ST12-CLOSURE::ST11-AGENT::",
    "llm": "ST12-CLOSURE::ST11-LLM::",
    "security": "ST12-CLOSURE::ST11-SECURITY::",
}
EXPECTED_CLOSURE_IDS = (
    *(f"ST12-CLOSURE::ST11-AGENT::{index:03d}" for index in range(1, 18)),
    *(f"ST12-CLOSURE::ST11-LLM::{index:03d}" for index in range(1, 4)),
    *(f"ST12-CLOSURE::ST11-SECURITY::{index:03d}" for index in range(14, 17)),
)
EXPECTED_SEMANTIC_TEST_IDS = tuple(
    f"ST12-TEST::{value:03d}"
    for value in (
        21, 22, 23, 24, 25, 29, 30, 31, 32, 33, 34, 35, 36,
        37, 38, 39, 40, 101, 113, 114, 181, 187, 189, 222, 226, 230,
    )
)
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
REQUIRED_EFFECT_DENIAL_REASONS = {
    "DIRECT_PROVIDER_FORBIDDEN",
    "PRIVATE_STATE_FORBIDDEN",
    "SOURCE_TRUTH_FORBIDDEN",
    "REPLAY_PAPER_EFFECT_FORBIDDEN",
    "LLM_INFERENCE_FORBIDDEN",
    "QPU_EFFECT_FORBIDDEN",
    "MODE_ACTIVATION_FORBIDDEN",
    "ORDER_RELEASE_FORBIDDEN",
    "CAPITAL_EFFECT_FORBIDDEN",
    "EXECUTION_ROUTER_BYPASS_FORBIDDEN",
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
VALUE_BODY_FIELDS = {
    "raw",
    "day1_seed_or_resolution_rule",
    "reference_range_or_structural_constraint",
    "bounded_search_space_or_fit_constraint",
    "unit_or_basis",
    "precision_and_rounding_policy",
    "runtime_resolution_procedure",
    "fallback_behavior_when_value_unavailable",
    "value_source_class",
    "source_state_refs",
}
EXPECTED_APPENDIX_E_SPEC_FIELDS = {
    "bounded_search_space_or_fit_constraint",
    "capability_binding_owner",
    "capability_binding_rule",
    "certified_source_agent_id_class",
    "certified_source_agent_ids",
    "certified_source_owner",
    "current_agent_identity_resolution_rule",
    "day1_seed_or_resolution_rule",
    "default_authority_class",
    "fallback_behavior_when_value_unavailable",
    "family_evidence_binding_ref",
    "formula_or_qku_mutation_authorized_by_st12e",
    "implementation_resolution_kind",
    "launch_computability_state",
    "missing_stale_invalid_behavior",
    "no_trade_fallback_preserved",
    "parameter_audit_id",
    "parameter_id",
    "parameter_symbol",
    "precision_and_rounding_policy",
    "reference_range_or_structural_constraint",
    "resolution_class",
    "runtime_agent_selection_rule",
    "runtime_parameter_key",
    "runtime_resolution_procedure",
    "source_state_refs",
    "step12_implementation_route",
    "underlying_value_semantics_owner",
    "unit_or_basis",
    "value_mutation_authorized_by_st12e",
    "value_source_class",
}
MASTER_VALUE_FIELDS = {
    "day1_seed_or_resolution_rule": "day1_seed_value_or_resolution_rule",
    "reference_range_or_structural_constraint": (
        "reference_range_or_structural_constraint"
    ),
    "bounded_search_space_or_fit_constraint": (
        "bounded_search_space_or_fit_constraint"
    ),
    "unit_or_basis": "unit_or_basis",
    "resolution_class": "resolution_class",
    "value_source_class": "value_source_class",
}
EXPECTED_APPENDIX_E_MASTER_CURRENTIZATIONS = {
    ("ST10-PARAM::0399", "bounded_search_space_or_fit_constraint"): (
        "plugin may not go beyond read-only or triggered live-concurrent "
        "shadow-comparison-only if the schema version is missing or incompatible",
        "plugin may not go beyond read-only or applicable shadow-observe or "
        "live-twin comparison-only if the schema version is missing or incompatible",
    ),
    ("ST10-PARAM::0541", "bounded_search_space_or_fit_constraint"): (
        "no preset may enter triggered live-concurrent shadow comparison or live "
        "solely from label strength without the full hidden-parent objective card, "
        "comparator bundle, decision family, parameter pack, objective formula, "
        "and extractability state",
        "no preset may enter applicable shadow-observe or live-twin comparison or "
        "live solely from label strength without the full hidden-parent objective "
        "card, comparator bundle, decision family, parameter pack, objective "
        "formula, and extractability state",
    ),
    ("ST10-PARAM::3078", "bounded_search_space_or_fit_constraint"): (
        "remote-provider paths may not widen task scope outside the declared enum "
        "without a new controlling-edition row",
        "remote-provider paths may not widen task scope outside the declared enum "
        "without a new canonical-version row",
    ),
    ("ST10-PARAM::3354", "reference_range_or_structural_constraint"): (
        "{DIFFERENT_AGENT_ID_AND_DIFFERENT_REASONING_CHAIN_REQUIRED,"
        "DIFFERENT_AGENT_ID_ONLY,"
        "DIFFERENT_LANE_AND_AGENT_ID_REQUIRED_FOR_DIRECT_LIVE_EXCEPTION}",
        "{DIFFERENT_AGENT_ID_AND_DIFFERENT_REASONING_CHAIN_REQUIRED,"
        "DIFFERENT_AGENT_ID_ONLY,"
        "DIFFERENT_LANE_AND_AGENT_ID_REQUIRED_FOR_HIGH_RISK_LIVE_CANDIDATE_REVIEW}",
    ),
    ("ST10-PARAM::3354", "bounded_search_space_or_fit_constraint"): (
        "direct-live exception paths may not weaken below the declared stricter "
        "independence class",
        "high-risk live-candidate review paths may not weaken below the declared "
        "stricter independence class",
    ),
    ("ST10-PARAM::3355", "bounded_search_space_or_fit_constraint"): (
        "owner-declared exception lists remain research-only and may not silently "
        "govern direct-live exception review",
        "owner-declared exception lists remain research-only and may not silently "
        "govern high-risk live-candidate review review",
    ),
}
_UNIVERSE_LINE = re.compile(
    r"\{\s*((?:AGENT_(?:RT|NL|OFF)_\d{2})"
    r"(?:\s*,\s*AGENT_(?:RT|NL|OFF)_\d{2})*)\s*\}"
)
_PARAMETER_LINE = re.compile(r"`parameter_symbol`\s*:\s*`([^`]+)`")
_MASTER_VALUE_LINE = re.compile(
    r"^\s+- `([^`]+)`:\s*(?:`([^`]*)`|(.*?))\s*$"
)
_SOURCE_AGENT_TOKEN = re.compile(r"^AGENT_(RT|NL|OFF)_(\d{2})$")


def _jsonl(path: Path) -> tuple[dict[str, object], ...]:
    rows = tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} contains a non-object row")
    return rows


def _canonical_parameter_rows() -> tuple[
    tuple[str, str, tuple[str, ...]], ...
]:
    rows: list[tuple[str, str, tuple[str, ...]]] = []
    source_ids: tuple[str, ...] | None = None
    awaiting_universe = False
    for line in MASTER_PLAN.read_text(encoding="utf-8").splitlines():
        if "Explicit agent-selection-universe binding" in line:
            source_ids = None
            awaiting_universe = True
        if awaiting_universe and (match := _UNIVERSE_LINE.search(line)):
            source_ids = tuple(value.strip() for value in match.group(1).split(","))
            awaiting_universe = False
        if match := _PARAMETER_LINE.search(line):
            if source_ids is None:
                raise ValueError("canonical parameter lacks a source universe")
            rows.append(
                (
                    f"ST10-PARAM::{len(rows) + 1:04d}",
                    match.group(1),
                    source_ids,
                )
            )
    return tuple(rows)


def _canonical_parameter_semantics() -> dict[str, dict[str, str]]:
    """Parse independently available canonical value fields by ST10 identity."""

    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in MASTER_PLAN.read_text(encoding="utf-8").splitlines():
        if match := _PARAMETER_LINE.search(line):
            current = {
                "parameter_id": f"ST10-PARAM::{len(rows) + 1:04d}",
                "parameter_symbol": match.group(1),
            }
            rows.append(current)
            continue
        if current is None or not (match := _MASTER_VALUE_LINE.match(line)):
            continue
        name = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        current[name] = str(value).strip()
    return {row["parameter_id"]: row for row in rows}


def _assignment_literal(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if not isinstance(target, ast.Name) or target.id != name or value is None:
            continue
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "MappingProxyType"
            and len(value.args) == 1
        ):
            value = value.args[0]
        return ast.literal_eval(value)
    raise ValueError(f"literal declaration {name} is missing")


def _typed_call_rows(
    tree: ast.Module,
    assignment_name: str,
    call_name: str,
) -> tuple[dict[str, object], ...]:
    assignment_value: ast.expr | None = None
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == assignment_name
        ):
            assignment_value = node.value
            break
    if not isinstance(assignment_value, ast.Tuple):
        raise ValueError(f"typed declaration {assignment_name} is not a tuple")
    rows: list[dict[str, object]] = []
    for element in assignment_value.elts:
        if (
            not isinstance(element, ast.Call)
            or not isinstance(element.func, ast.Name)
            or element.func.id != call_name
            or element.args
        ):
            raise ValueError(f"{assignment_name} contains a non-{call_name} row")
        row: dict[str, object] = {}
        for keyword in element.keywords:
            if keyword.arg is None:
                raise ValueError(f"{assignment_name} uses keyword expansion")
            row[keyword.arg] = ast.literal_eval(keyword.value)
        rows.append(row)
    return tuple(rows)


def _class_methods(
    tree: ast.Module, class_name: str
) -> dict[str, ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name: child
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            }
    return {}


def _source_universe_registry(
    rows: tuple[tuple[str, str, tuple[str, ...]], ...]
) -> tuple[
    dict[str, dict[str, object]],
    dict[tuple[str, ...], str],
]:
    counts = Counter(source_ids for _, _, source_ids in rows)
    definitions: dict[str, dict[str, object]] = {}
    refs: dict[tuple[str, ...], str] = {}
    for source_ids in sorted(counts):
        ref = _stable_source_universe_ref(
            "UPSTREAM_SOURCE_UNIVERSE", source_ids
        )
        definitions[ref] = {
            "source_agent_ids": list(source_ids),
            "parameter_count": counts[source_ids],
        }
        refs[source_ids] = ref
    return definitions, refs


def _stable_source_universe_ref(
    namespace: str,
    source_ids: tuple[str, ...],
) -> str:
    tokens: list[str] = []
    for source_id in source_ids:
        match = _SOURCE_AGENT_TOKEN.fullmatch(source_id)
        if match is None:
            raise ValueError(f"invalid source identity: {source_id}")
        tokens.append(f"{match.group(1)}{match.group(2)}")
    return f"{namespace}::{'-'.join(tokens)}"


def _behavioral_probe() -> tuple[bool, str]:
    probe = r"""
from types import SimpleNamespace

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    AgentCapabilityDecisionStateV1,
    AgentCapabilityDecisionV1,
    POLICY_VERSION,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ContractValidationError,
    NoTradeReoptimizationRouteError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    CanonicalOwnerPacketRegistryV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)


class BodyTouched(Exception):
    pass


class ProbeRequest:
    request_id = "REQUEST::INDEPENDENT::E"
    operation_name = "resolve_identity"
    principal_id = "OWNER::TEST"
    capability_bundle_id = "CAPABILITY::READ_ONLY_TEST"
    idempotency_key = "IDEMPOTENCY::INDEPENDENT::E"
    context = SimpleNamespace(context_id="CTX::INDEPENDENT::E")

    def __init__(self):
        self.body_reads = 0

    @property
    def identity_query(self):
        self.body_reads += 1
        raise BodyTouched


class Admission:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0

    def admit_operation(self, request):
        self.calls += 1
        return self.decision


def decision(state, reasons, route):
    return AgentCapabilityDecisionV1(
        decision_id=f"DECISION::{state.value}",
        request_id=ProbeRequest.request_id,
        task_id="TASK::INDEPENDENT::E",
        principal_id=ProbeRequest.principal_id,
        current_agent_id="dashboard_agent",
        source_agent_refs=("AGENT_RT_11",),
        operation_id=ProbeRequest.operation_name,
        policy_version=POLICY_VERSION,
        decision_state=state,
        reason_codes=reasons,
        scope_refs=(
            "qku_scope_refs=QKU::IMMUTABLE",
            "formula_scope_refs=MATH-01",
            "reoptimization_variable_id=market",
        ),
        idempotency_key=ProbeRequest.idempotency_key,
        retry_disposition="NO_RETRY_AUTHORITY",
        peer_sod_disposition="SOD_ENFORCED",
        safety_state_disposition="NON_MATERIAL_LOCAL_NO_EFFECT",
        terminal_route=route,
        agent_orch_receipt_ref="AGENT_ORCH1::RECEIPT::REFERENCE_ONLY",
        st12c_causation_correlation_refs=(
            "OperationRequestEnvelopeV1.request_id=REQUEST::INDEPENDENT::E",
            "OperationRequestEnvelopeV1.idempotency_key=IDEMPOTENCY::INDEPENDENT::E",
        ),
        evidence_refs=("INDEPENDENT_BEHAVIORAL_PROBE",),
        alternative_route_refs=("OWNER_REVIEW_REQUIRED",),
        disagreement_state="NONE_DECLARED",
        confidence_state="INDEPENDENT_PROBE",
        limitation_codes=(
            "NO_PROVIDER_PRIVATE_STATE_ORDER_QPU_OR_RUNTIME_EFFECT",
            "QKU_AND_FORMULA_IMMUTABLE",
        ),
    )


registry = CanonicalOwnerPacketRegistryV1()
try:
    QKUComputationControlPlaneV1(registry)
except TypeError:
    omitted_closed = True
else:
    omitted_closed = False

try:
    QKUComputationControlPlaneV1(
        registry, agent_capability_resolver=None
    )
except ContractValidationError:
    explicit_none_closed = True
else:
    explicit_none_closed = False

class Malformed:
    def admit_operation(self, request):
        return object()

malformed_request = ProbeRequest()
try:
    QKUComputationControlPlaneV1(
        registry, agent_capability_resolver=Malformed()
    ).resolve_identity(malformed_request)
except AuthorityDeniedError:
    malformed_closed = malformed_request.body_reads == 0
else:
    malformed_closed = False

denied_request = ProbeRequest()
denied_admission = Admission(
    decision(
        AgentCapabilityDecisionStateV1.DENIED,
        (ReasonCode.DIRECT_PROVIDER_FORBIDDEN,),
        "DENY_TASK",
    )
)
try:
    QKUComputationControlPlaneV1(
        registry,
        agent_capability_resolver=denied_admission,
    ).resolve_identity(denied_request)
except AuthorityDeniedError as exc:
    denied_closed = (
        not isinstance(exc, NoTradeReoptimizationRouteError)
        and denied_request.body_reads == 0
        and denied_admission.calls == 1
    )
else:
    denied_closed = False

no_trade_packet = decision(
    AgentCapabilityDecisionStateV1.NO_TRADE_REOPTIMIZATION_ROUTED,
    (ReasonCode.NO_TRADE_REOPTIMIZATION_REQUIRED,),
    "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION",
)
no_trade_request = ProbeRequest()
no_trade_admission = Admission(no_trade_packet)
try:
    QKUComputationControlPlaneV1(
        registry,
        agent_capability_resolver=no_trade_admission,
    ).resolve_identity(no_trade_request)
except NoTradeReoptimizationRouteError as exc:
    no_trade_closed = (
        exc.decision is no_trade_packet
        and no_trade_request.body_reads == 0
        and exc.decision.terminal_route
        == "PRETRADE1_BOUNDED_TRADEPLAN_VARIABLE_REOPTIMIZATION"
        and "formula_scope_refs=MATH-01" in exc.decision.scope_refs
        and exc.decision.runtime_effect_authorized is False
        and no_trade_admission.calls == 1
    )
else:
    no_trade_closed = False

eligible_packet = decision(
    AgentCapabilityDecisionStateV1.ELIGIBLE_FOR_NO_EFFECT_QKU_REQUEST,
    (),
    "QKUComputationControlPlaneV1_NO_EFFECT_REQUEST",
)
eligible_request = ProbeRequest()
eligible_admission = Admission(eligible_packet)
try:
    QKUComputationControlPlaneV1(
        registry,
        agent_capability_resolver=eligible_admission,
    ).resolve_identity(eligible_request)
except BodyTouched:
    eligible_proceeds = (
        eligible_request.body_reads == 1 and eligible_admission.calls == 1
    )
else:
    eligible_proceeds = False

passed = (
    omitted_closed
    and explicit_none_closed
    and malformed_closed
    and denied_closed
    and no_trade_closed
    and eligible_proceeds
)
if not passed:
    raise SystemExit(
        "behavioral probe failed "
        f"omitted={omitted_closed} none={explicit_none_closed} "
        f"malformed={malformed_closed} "
        f"denied={denied_closed} no_trade={no_trade_closed} "
        f"eligible={eligible_proceeds}"
    )
print("BEHAVIORAL_PROBE_OK")
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", probe],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    detail = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, detail


def validate_domain(domain: str) -> list[str]:
    if domain not in DOMAIN_PREFIXES:
        return [f"unknown E validation domain: {domain}"]
    failures: list[str] = []
    try:
        manifest = json.loads(
            (ARTIFACTS / "manifest.json").read_text(encoding="utf-8")
        )
        policy = _jsonl(ARTIFACTS / "policy.jsonl")
        parameter_scope = _jsonl(ARTIFACTS / "parameter_scope.jsonl")
        master_rows = _canonical_parameter_rows()
        master_semantics = _canonical_parameter_semantics()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"canonical or generated E data cannot be loaded: {exc}"]

    policy_by_type = {
        row_type: tuple(
            row for row in policy if row.get("row_type") == row_type
        )
        for row_type in (
            "CONTROL",
            "IDENTITY_COMPATIBILITY",
            "PARAMETER_CAPABILITY_BINDING",
        )
    }
    controls = policy_by_type["CONTROL"]
    identities = policy_by_type["IDENTITY_COMPATIBILITY"]
    bindings = policy_by_type["PARAMETER_CAPABILITY_BINDING"]
    row_ids = tuple(str(row.get("row_id") or "") for row in policy)
    if (
        any(not row_id for row_id in row_ids)
        or len(row_ids) != len(set(row_ids))
        or sum(len(rows) for rows in policy_by_type.values()) != len(policy)
    ):
        failures.append("policy row types or identities are missing or duplicated")

    closure_ids = tuple(str(row.get("closure_id") or "") for row in controls)
    semantic_test_ids = tuple(manifest.get("semantic_test_ids") or ())
    if set(closure_ids) != set(EXPECTED_CLOSURE_IDS) or len(controls) != 23:
        failures.append("semantic closure IDs differ from the exact 23-row set")
    if (
        set(semantic_test_ids) != set(EXPECTED_SEMANTIC_TEST_IDS)
        or len(semantic_test_ids) != 26
    ):
        failures.append("semantic test IDs differ from the exact 26-row set")
    domain_controls = tuple(
        row
        for row in controls
        if str(row.get("closure_id") or "").startswith(DOMAIN_PREFIXES[domain])
    )
    if not domain_controls:
        failures.append(f"{domain} has no relevant compact predicate rows")
    if len({row.get("predicate_group") for row in controls}) <= 1:
        failures.append("closure labels still relabel one shared Boolean")

    counts = manifest.get("counts")
    derived_counts = {
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
        "semantic_test_rows": len(semantic_test_ids),
        "validation_commands": len(
            tuple(manifest.get("validation_commands") or ())
        ),
        "parameter_source_universe": len(master_rows),
    }
    if counts != derived_counts:
        failures.append(
            f"manifest counts differ from independent derivation: {derived_counts}"
        )

    parameter_tree = ast.parse(
        (PACKAGE / "parameter_policy.py").read_text(encoding="utf-8"),
        filename="parameter_policy.py",
    )
    agent_tree = ast.parse(
        (PACKAGE / "agent_policy.py").read_text(encoding="utf-8"),
        filename="agent_policy.py",
    )
    try:
        source_groups = _assignment_literal(
            parameter_tree, "ST12E_SOURCE_AGENT_GROUPS"
        )
        e_references = _assignment_literal(
            parameter_tree, "_ST12E_PARAMETER_CAPABILITY_REFERENCES"
        )
        appendix_e_specs = _typed_call_rows(
            parameter_tree,
            "ST12E_PARAMETER_POLICY_SPECS",
            "ST12EParameterValueSemanticsV1",
        )
        exact_mapping_spec = _assignment_literal(
            agent_tree, "_SOURCE_IDENTITY_SPEC"
        )
    except (ValueError, TypeError, SyntaxError) as exc:
        failures.append(f"readable E source declarations cannot be parsed: {exc}")
        source_groups = {}
        e_references = ()
        appendix_e_specs = ()
        exact_mapping_spec = ()

    appendix_e_spec_by_id = {
        str(row.get("parameter_id") or ""): row for row in appendix_e_specs
    }
    appendix_e_symbols = {
        str(row.get("parameter_symbol") or "") for row in appendix_e_specs
    }
    malformed_appendix_e_specs = tuple(
        str(row.get("parameter_id") or "MISSING")
        for row in appendix_e_specs
        if set(row) != EXPECTED_APPENDIX_E_SPEC_FIELDS
        or row.get("underlying_value_semantics_owner")
        != "QKUComputationControlPlaneV1.ComputationParameterPolicyV1"
        or row.get("capability_binding_owner") != "AgentCapabilityResolverV1"
        or row.get("value_mutation_authorized_by_st12e") is not False
        or row.get("formula_or_qku_mutation_authorized_by_st12e") is not False
        or row.get("no_trade_fallback_preserved") is not True
        or not row.get("precision_and_rounding_policy")
        or not row.get("runtime_resolution_procedure")
        or not row.get("source_state_refs")
    )
    if (
        len(appendix_e_specs) != 87
        or len(appendix_e_spec_by_id) != 87
        or len(appendix_e_symbols) != 87
        or malformed_appendix_e_specs
    ):
        failures.append(
            "readable Appendix-E policy specs are not exact typed 87-row closure "
            f"malformed={malformed_appendix_e_specs[:3]}"
        )

    master_semantic_mismatches: list[str] = []
    for parameter_id, spec in appendix_e_spec_by_id.items():
        canonical = master_semantics.get(parameter_id, {})
        if canonical.get("parameter_symbol") != spec.get("parameter_symbol"):
            master_semantic_mismatches.append(parameter_id)
            continue
        for spec_field, master_field in MASTER_VALUE_FIELDS.items():
            master_value = canonical.get(master_field)
            spec_value = spec.get(spec_field)
            authorized_currentization = (
                EXPECTED_APPENDIX_E_MASTER_CURRENTIZATIONS.get(
                    (parameter_id, spec_field)
                )
            )
            if master_value != spec_value and authorized_currentization != (
                master_value,
                spec_value,
            ):
                master_semantic_mismatches.append(
                    f"{parameter_id}:{spec_field}"
                )
                break
    if master_semantic_mismatches:
        failures.append(
            "Appendix-E specs differ from canonical master semantic fields: "
            f"{master_semantic_mismatches[:3]}"
        )

    polymarket_batch = appendix_e_spec_by_id.get("ST10-PARAM::2207", {})
    if (
        polymarket_batch.get("parameter_symbol") != "pm_batch_limit"
        or polymarket_batch.get("day1_seed_or_resolution_rule")
        != (
            "15_FOR_CURRENT_PUBLIC_POLYMARKET_BATCH_ORDERS_CAP_UNLESS_A_NEWER_"
            "OFFICIAL_CONNECTOR_RECEIPT_DECLARES_OTHERWISE"
        )
        or "FAIL_CLOSED" not in str(
            polymarket_batch.get("fallback_behavior_when_value_unavailable")
        )
    ):
        failures.append("Polymarket batch cap is not exact 15/receipt/fail-closed policy")

    source_ids = tuple(
        sorted(
            {
                source_id
                for _, _, row_source_ids in master_rows
                for source_id in row_source_ids
            }
        )
    )
    exact_mapping_ids = {
        str(row[0])
        for row in exact_mapping_spec
        if isinstance(row, tuple) and row
    }
    unmapped_ids = set(source_ids) - exact_mapping_ids
    invented_mapping_ids = exact_mapping_ids - set(source_ids)
    if (
        len(master_rows) != 3810
        or len(source_ids) != 25
        or len(exact_mapping_ids) != 12
        or len(unmapped_ids) != 13
        or invented_mapping_ids
    ):
        failures.append(
            "canonical source universe does not close at 3810/25/12/13 "
            f"invented={sorted(invented_mapping_ids)}"
        )

    identity_by_source = {
        str(row.get("source_agent_id") or ""): row for row in identities
    }
    if (
        set(identity_by_source) != set(source_ids)
        or len(identities) != 25
        or manifest.get("source_identity_row_count") != 25
        or manifest.get("exact_mapping_count") != 12
        or manifest.get("unmapped_mapping_count") != 13
        or set(manifest.get("unmapped_source_agent_ids") or ()) != unmapped_ids
    ):
        failures.append("generated compatibility map is not the exact 25/12/13 universe")
    for source_id, row in identity_by_source.items():
        is_unmapped = source_id in unmapped_ids
        current_fields = (
            "current_principal_refs",
            "current_role_refs",
            "current_duty_refs",
            "current_scope",
            "intersection_scope",
        )
        if is_unmapped:
            if (
                row.get("mapping_type") != "UNMAPPED"
                or row.get("terminal_mapping_state")
                != "UNMAPPED_CROSSWALK_REQUIRED_NO_AUTHORITY"
                or any(row.get(field) for field in current_fields)
                or row.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
            ):
                failures.append(f"{source_id}: unmapped state invents authority")
        else:
            source_scope = set(row.get("source_scope") or ())
            current_scope = set(row.get("current_scope") or ())
            intersection = set(row.get("intersection_scope") or ())
            if (
                row.get("mapping_type")
                not in {"EXACT_ONE_TO_ONE", "EXACT_SCOPED_MULTI_ROLE"}
                or not row.get("current_principal_refs")
                or not intersection
                or not intersection <= source_scope & current_scope
            ):
                failures.append(f"{source_id}: exact mapping broadens or lacks scope")

    expected_universe_defs, expected_universe_refs = (
        _source_universe_registry(master_rows)
    )
    generated_universe_defs = manifest.get("exact_upstream_source_universes")
    if (
        generated_universe_defs != expected_universe_defs
        or len(expected_universe_defs) != 67
        or manifest.get("exact_upstream_source_universe_count") != 67
        or manifest.get("exact_upstream_source_agent_id_count") != 25
    ):
        failures.append("exact 67-universe registry differs from canonical rows")
    if any(
        re.fullmatch(r"UPSTREAM_SOURCE_UNIVERSE::\d+", ref)
        for ref in expected_universe_defs
    ):
        failures.append("upstream source-universe references remain ordinal")
    sample_source_ids = master_rows[0][2]
    sample_ref = expected_universe_refs[sample_source_ids]
    augmented_defs, augmented_refs = _source_universe_registry(
        (*master_rows, ("ST10-PARAM::UNRELATED", "unrelated", ("AGENT_RT_02",)))
    )
    if augmented_refs.get(sample_source_ids) != sample_ref or sample_ref not in augmented_defs:
        failures.append("unrelated source-set addition renumbers an existing reference")

    scope_by_id = {
        str(row.get("parameter_id") or ""): row for row in parameter_scope
    }
    expected_parameter_ids = tuple(
        f"ST10-PARAM::{index:04d}" for index in range(1, len(master_rows) + 1)
    )
    if (
        tuple(scope_by_id) != expected_parameter_ids
        or len(scope_by_id) != len(parameter_scope)
    ):
        failures.append("parameter scope row identities are not exact and ordered")

    fully_mapped_count = 0
    crosswalk_required_count = 0
    source_set_rewrite_count = 0
    for parameter_id, symbol, row_source_ids in master_rows:
        generated = scope_by_id.get(parameter_id, {})
        expected_ref = expected_universe_refs[row_source_ids]
        actual_ref = str(generated.get("upstream_source_universe_ref") or "")
        projected_source_ids = tuple(
            (generated_universe_defs or {})
            .get(actual_ref, {})
            .get("source_agent_ids", ())
        )
        if (
            generated.get("parameter_symbol") != symbol
            or actual_ref != expected_ref
            or projected_source_ids != row_source_ids
        ):
            source_set_rewrite_count += 1
        mapped_subset = tuple(
            source_id for source_id in row_source_ids if source_id in exact_mapping_ids
        )
        unmapped_subset = tuple(
            source_id for source_id in row_source_ids if source_id in unmapped_ids
        )
        expected_mapped_refs = [
            f"ST12E_IDENTITY::{source_id}" for source_id in mapped_subset
        ] or ["ABSENT_NOT_APPLICABLE"]
        expected_unmapped_refs = [
            f"ST12E_IDENTITY::{source_id}" for source_id in unmapped_subset
        ] or ["ABSENT_NOT_APPLICABLE"]
        expected_state = (
            "UPSTREAM_IDENTITY_CROSSWALK_REQUIRED"
            if unmapped_subset
            else "UPSTREAM_IDENTITY_FULLY_MAPPED"
        )
        if (
            generated.get("mapped_compatibility_refs") != expected_mapped_refs
            or generated.get("unmapped_compatibility_refs")
            != expected_unmapped_refs
            or generated.get("upstream_identity_mapping_state")
            != expected_state
        ):
            failures.append(f"{parameter_id}: mapped/unmapped lineage subsets differ")
            break
        if unmapped_subset:
            crosswalk_required_count += 1
        else:
            fully_mapped_count += 1
    if (
        source_set_rewrite_count != 0
        or fully_mapped_count != 1721
        or crosswalk_required_count != 2089
        or manifest.get("fully_mapped_upstream_row_count") != 1721
        or manifest.get("crosswalk_required_upstream_row_count") != 2089
        or manifest.get("quota_reassignment_count") != 0
        or manifest.get("nearest_universe_assignment_count") != 0
        or manifest.get("source_set_rewrite_count") != 0
    ):
        failures.append(
            "upstream projection violates exact preservation or 1721/2089 split "
            f"rewrites={source_set_rewrite_count}"
        )

    canonical_symbols = {
        parameter_id: symbol for parameter_id, symbol, _ in master_rows
    }
    e_reference_by_id = {
        str(parameter_id): (str(symbol), str(group_id))
        for parameter_id, symbol, group_id in e_references
    }
    binding_by_id = {
        str(row.get("parameter_id") or ""): row for row in bindings
    }
    if (
        len(e_reference_by_id) != 87
        or set(binding_by_id) != set(e_reference_by_id)
        or set(appendix_e_spec_by_id) != set(e_reference_by_id)
        or len(bindings) != 87
    ):
        failures.append("E capability binding registry is not the exact 87 rows")

    typed_policy_resolution_count = 0
    typed_policy_conflict_count = 0
    typed_policy_unresolved_count = 0
    typed_policy_owner_refs: set[str] = set()
    try:
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
            get_parameter_policy,
        )

        for parameter_id, (symbol, _) in e_reference_by_id.items():
            try:
                typed_policy = get_parameter_policy(parameter_id)
            except Exception:
                typed_policy_unresolved_count += 1
                continue
            semantics = getattr(typed_policy, "appendix_e_value_semantics", None)
            expected_spec = appendix_e_spec_by_id.get(parameter_id, {})
            if (
                getattr(typed_policy, "parameter_id", None) != parameter_id
                or getattr(typed_policy, "parameter_symbol", None) != symbol
                or semantics is None
                or any(
                    getattr(semantics, field, object()) != expected_spec.get(field)
                    for field in EXPECTED_APPENDIX_E_SPEC_FIELDS
                )
            ):
                typed_policy_conflict_count += 1
                continue
            typed_policy_resolution_count += 1
            typed_policy_owner_refs.add(
                str(getattr(typed_policy, "canonical_owner", ""))
            )
    except Exception as exc:
        failures.append(f"canonical typed policy accessor cannot load: {exc}")
        typed_policy_unresolved_count = 87

    if (
        typed_policy_resolution_count != 87
        or typed_policy_unresolved_count != 0
        or typed_policy_conflict_count != 0
        or typed_policy_owner_refs
        != {"QKUComputationControlPlaneV1.ComputationParameterPolicyV1"}
        or manifest.get("appendix_e_policy_spec_count") != 87
        or manifest.get("parameter_identity_resolution_count") != 87
        or manifest.get("canonical_typed_policy_resolution_count") != 87
        or manifest.get("unresolved_typed_policy_count") != 0
        or manifest.get("conflicting_typed_policy_count") != 0
        or manifest.get("canonical_parameter_value_owner_count") != 1
    ):
        failures.append(
            "canonical accessor does not close actual Appendix-E typed policies "
            f"resolved={typed_policy_resolution_count} "
            f"unresolved={typed_policy_unresolved_count} "
            f"conflicting={typed_policy_conflict_count}"
        )
    e_source_sets = Counter(
        tuple(source_groups[group_id])
        for _, group_id in e_reference_by_id.values()
        if group_id in source_groups
    )
    expected_e_universe_defs = {
        _stable_source_universe_ref(
            "ST12E_CERTIFIED_SOURCE_UNIVERSE", source_set
        ): {
            "source_agent_ids": list(source_set),
            "parameter_count": e_source_sets[source_set],
            "authority_created": False,
        }
        for source_set in sorted(e_source_sets)
    }
    expected_e_refs = {
        tuple(spec["source_agent_ids"]): ref
        for ref, spec in expected_e_universe_defs.items()
    }
    if (
        manifest.get("st12e_certified_source_universes")
        != expected_e_universe_defs
        or len(expected_e_universe_defs) != 6
        or any(
            re.fullmatch(r"ST12E_CERTIFIED_SOURCE_UNIVERSE::\d+", ref)
            for ref in expected_e_universe_defs
        )
    ):
        failures.append("six-set E-certified distribution is not exact")

    exact_e_count = 0
    outside_e_count = 0
    e_upstream_gap_count = 0
    e_certified_unmapped_count = 0
    for parameter_id, generated in scope_by_id.items():
        if parameter_id in e_reference_by_id:
            exact_e_count += 1
            symbol, group_id = e_reference_by_id[parameter_id]
            certified_ids = tuple(source_groups.get(group_id, ()))
            if set(certified_ids) - exact_mapping_ids:
                e_certified_unmapped_count += 1
            binding = binding_by_id.get(parameter_id, {})
            expected_value_ref = (
                "QKUComputationControlPlaneV1."
                f"ComputationParameterPolicyV1::{parameter_id}"
            )
            if (
                canonical_symbols.get(parameter_id) != symbol
                or generated.get("st12e_binding_state")
                != "EXACT_ST12E_CAPABILITY_BINDING"
                or generated.get(
                    "st12e_certified_source_universe_ref_or_explicit_absence"
                )
                != expected_e_refs.get(certified_ids)
                or binding.get("certified_source_universe_ref")
                != expected_e_refs.get(certified_ids)
                or binding.get("parameter_symbol") != symbol
                or binding.get("value_policy_ref") != expected_value_ref
                or generated.get("value_policy_ref") != expected_value_ref
                or binding.get("capability_policy_ref")
                != f"ST12E_CAPABILITY_POLICY::{group_id}"
                or VALUE_BODY_FIELDS.intersection(binding)
            ):
                failures.append(f"{parameter_id}: E binding duplicates or loses value refs")
                break
            if (
                generated.get("upstream_identity_mapping_state")
                == "UPSTREAM_IDENTITY_CROSSWALK_REQUIRED"
            ):
                e_upstream_gap_count += 1
        else:
            outside_e_count += 1
            if (
                generated.get("st12e_binding_state")
                != "OUTSIDE_ST12E_CAPABILITY_BINDING_SCOPE"
                or generated.get(
                    "st12e_capability_binding_ref_or_explicit_absence"
                )
                != "ABSENT_NOT_APPLICABLE"
                or generated.get("terminal_route")
                != "ST12E_CAPABILITY_BINDING_NOT_APPLICABLE"
            ):
                failures.append(
                    f"{parameter_id}: outside-E state is mistaken for authority"
                )
                break
    if (
        exact_e_count != 87
        or outside_e_count != 3723
        or e_upstream_gap_count != 34
        or e_certified_unmapped_count != 0
        or manifest.get("exact_st12e_binding_count") != 87
        or manifest.get("outside_st12e_binding_scope_count") != 3723
        or manifest.get("exact_st12e_certified_mapping_count") != 87
        or manifest.get("st12e_binding_with_unmapped_certified_id_count") != 0
        or manifest.get("st12e_rows_with_upstream_crosswalk_gap") != 34
        or manifest.get("st12e_rows_with_fully_mapped_upstream_lineage") != 53
        or manifest.get("value_policy_ref_resolution_count") != 87
        or manifest.get("duplicated_value_body_count") != 0
        or manifest.get("capability_binding_value_body_count") != 0
        or manifest.get("generated_policy_value_body_count") != 0
    ):
        failures.append(
            "orthogonal E applicability does not close at 87/3723/34/53"
        )

    required_lineage = {
        "semantic_owner",
        "implementation_owner",
        "producer_ref",
        "upstream_artifact_refs",
        "upstream_row_or_value_refs",
        "current_principal_duty_policy_refs",
        "downstream_consumer_refs",
        "lifecycle_state",
        "activation_state",
        "terminal_route",
        "validator_ref",
    }
    for row in policy:
        if (
            not required_lineage <= set(row)
            or "timing_or_snapshot_state" not in row
            or row.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
        ):
            failures.append(f"{row.get('row_id')}: policy lineage is incomplete")
            break
    for row in parameter_scope:
        if (
            not required_lineage - {"timing_or_snapshot_state"} <= set(row)
            or "timing_state" not in row
            or row.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
        ):
            failures.append(
                f"{row.get('parameter_id')}: parameter lineage is incomplete"
            )
            break

    parameter_source = (PACKAGE / "parameter_policy.py").read_text(
        encoding="utf-8"
    )
    validation_source = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    for tree, label in (
        (parameter_tree, "parameter_policy.py"),
        (
            ast.parse(validation_source, filename="validation.py"),
            "validation.py",
        ),
    ):
        for node in ast.walk(tree):
            assignment_name = ""
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    assignment_name = target.id
            elif isinstance(node, ast.AnnAssign) and isinstance(
                node.target, ast.Name
            ):
                assignment_name = node.target.id
            if assignment_name.startswith("_ST12E") and (
                "B64" in assignment_name or "COMPRESSED" in assignment_name
            ):
                failures.append(f"{label}: opaque ST12-E payload exists")
    if (
        "_ST12E_SEMANTIC_ROWS_B64" in validation_source
        or "_ST12E_PARAMETER_CAPABILITY_ROWS_B64" in parameter_source
        or manifest.get("opaque_semantic_payload_count") != 0
    ):
        failures.append("opaque or value-bearing ST12-E payload remains")
    binding_class = next(
        (
            node
            for node in parameter_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ST12EParameterCapabilityBindingV1"
        ),
        None,
    )
    binding_fields = {
        node.target.id
        for node in (binding_class.body if binding_class is not None else ())
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
    }
    if binding_fields != {
        "parameter_id",
        "parameter_symbol",
        "certified_source_agent_ids",
        "value_policy_ref",
        "capability_policy_ref",
        "st12e_binding_state",
    }:
        failures.append("E binding class is not capability-reference-only")

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
    }
    if not REQUIRED_EFFECT_DENIAL_REASONS <= reason_names:
        failures.append("central reason enum lacks an effect-denial boundary")

    agent_source = (PACKAGE / "agent_policy.py").read_text(encoding="utf-8")
    service_source = (PACKAGE / "service.py").read_text(encoding="utf-8")
    service_tree = ast.parse(service_source, filename="service.py")
    for tree, label in (
        (agent_tree, "agent_policy.py"),
        (service_tree, "service.py"),
    ):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{label}: forbidden provider import {roots}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{label}: forbidden provider import {root}")
            elif (
                label == "agent_policy.py"
                and isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"glob", "rglob"}
            ):
                failures.append("agent policy performs a raw runtime library scan")

    service_methods = _class_methods(
        service_tree, "QKUComputationControlPlaneV1"
    )
    service_class = next(
        (
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "QKUComputationControlPlaneV1"
        ),
        None,
    )
    resolver_fields = tuple(
        node
        for node in (service_class.body if service_class is not None else ())
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "agent_capability_resolver"
    )
    production_admission_profile_tokens = (
        "InternalNoEffectAdmissionProfileV1",
        "INTERNAL_NO_EFFECT_ADMISSION_PROFILE",
        "OWNER::TEST",
        "CAPABILITY::READ_ONLY_TEST",
        "AGENT_ORCH1_RECEIPT_EXPLICITLY_NOT_APPLICABLE_INTERNAL_NO_EFFECT",
    )
    production_admission_default_exists = (
        len(resolver_fields) != 1 or resolver_fields[0].value is not None
    )
    if (
        production_admission_default_exists
        or any(
            token in agent_source or token in service_source
            for token in production_admission_profile_tokens
        )
        or manifest.get("implicit_admission_bypass_count") != 0
        or manifest.get("production_default_admission_profile_count") != 0
    ):
        failures.append("production service retains an implicit test admission path")
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
    admission_counts = {
        name: sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_admit_agent_request"
            for node in ast.walk(service_methods[name])
        )
        if name in service_methods
        else 0
        for name in implemented_names
    }
    admission_helper = next(
        (
            node
            for node in service_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_admit_agent_request"
        ),
        None,
    )
    optional_bypass = admission_helper is None or any(
        isinstance(node, ast.Compare)
        and any(
            isinstance(comparator, ast.Constant) and comparator.value is None
            for comparator in node.comparators
        )
        for node in ast.walk(admission_helper)
    )
    resolver_methods = _class_methods(agent_tree, "AgentCapabilityResolverV1")
    resolver_admit = resolver_methods.get("admit_operation")
    no_trade_collapsed = resolver_admit is None or any(
        isinstance(node, ast.Raise) for node in ast.walk(resolver_admit)
    )
    if (
        admission_counts != {name: 1 for name in implemented_names}
        or optional_bypass
        or no_trade_collapsed
        or "raise NoTradeReoptimizationRouteError(decision)"
        not in service_source
        or "self.decision = decision"
        not in (PACKAGE / "errors.py").read_text(encoding="utf-8")
    ):
        failures.append(
            "mandatory admission or typed NO_TRADE control flow is incomplete"
        )

    no_effect_flags = manifest.get("no_effect_authority_flags")
    if (
        not isinstance(no_effect_flags, dict)
        or set(no_effect_flags) != REQUIRED_NO_EFFECT_FLAG_NAMES
        or any(value is not False for value in no_effect_flags.values())
        or manifest.get("runtime_effect_authorized") is not False
        or manifest.get("no_effect_authority_closed") is not True
        or manifest.get("activation_state") != "NO_EFFECT_CONTRACT_ONLY"
        or tuple(manifest.get("no_trade_reoptimization_variable_ids") or ())
        != EXPECTED_NO_TRADE_VARIABLE_IDS
        or tuple(manifest.get("quantum_formulation_required_fields") or ())
        != EXPECTED_QUANTUM_FORMULATION_FIELDS
        or tuple(manifest.get("llm_advisory_task_fields") or ())
        != EXPECTED_LLM_ADVISORY_TASK_FIELDS
    ):
        failures.append("manifest no-effect, NO_TRADE, LLM, or quantum boundary drifts")

    behavior_passed, behavior_detail = _behavioral_probe()
    if not behavior_passed:
        failures.append(f"service behavioral admission probe failed: {behavior_detail}")

    if "_st12e_shared_state" in validation_source:
        failures.append("primary validation still relabels one shared Boolean")
    if "_st12e_predicate_matrix" not in validation_source:
        failures.append("primary compact predicate matrix is missing")
    physical_modules = tuple(
        sorted(
            (
                REPO_ROOT
                / "tests/stage1_prediction_markets/"
                "qku_computation_control_plane/tranche_e"
            ).glob("test_*_matrix.py")
        )
    )
    if len(physical_modules) != 3:
        failures.append("physical tranche-E matrix count is not exactly three")
    for name in FORBIDDEN_PARALLEL_PATHS:
        if (PACKAGE / name).exists():
            failures.append(f"parallel capability owner exists: {name}")
    if domain == "llm" and (
        "llm_inference_forbidden" not in agent_source.casefold()
        or "untrusted_content" not in agent_source.casefold()
    ):
        failures.append("LLM advisory and injection boundary is incomplete")
    if domain == "security" and not {
        "SAFETY_STATE_MISSING",
        "SAFETY_STATE_STALE",
        "SAFETY_STATE_CONFLICT",
    } <= reason_names:
        failures.append("safety-state fail-closed reasons are incomplete")
    return failures


def main(domain: str | None = None) -> int:
    selected = domain or "all"
    domains = tuple(DOMAIN_PREFIXES) if selected == "all" else (selected,)
    failures = [
        failure
        for current_domain in domains
        for failure in validate_domain(current_domain)
    ]
    if failures:
        print("\n".join(dict.fromkeys(failures)), file=sys.stderr)
        return 1
    print(f"{SUCCESS_MARKER} domain={selected}")
    return 0


if __name__ == "__main__":
    requested_domain = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(main(requested_domain))
