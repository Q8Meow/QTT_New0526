"""Single decision-centric computation control-plane facade.

The registry, expansion compiler, resolver, and executor in this module are
implementation-private.  They deliberately share one in-process authority and
one immutable snapshot rather than becoming separately callable services.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
from types import MappingProxyType
from typing import Any

from .models import (
    ComputationRecordV1,
    ComputationControlError,
    ComputationReceiptV1,
    ExpansionBatchV1,
    RegistryUpdateV1,
    ResolvedDecisionPlanV1,
    ResolvedNodeV1,
    _freeze,
    _thaw,
    json_compatible,
)


REGISTRY_SCHEMA_VERSION = "1.0"
REGISTRY_FILE = "registry.jsonl"
REGISTRY_MANIFEST = "registry.manifest.json"
SHARD_GLOB = "registry.part-*.jsonl"

# One measured storage policy, shared by the writer and validator-facing
# diagnostics.  Consumers never receive these thresholds or the chosen layout.
STORAGE_POLICY = MappingProxyType(
    {
        "single_file_max_rows": 2_500,
        "single_file_max_serialized_bytes": 16_000_000,
        "max_record_serialized_bytes": 1_000_000,
        "single_file_max_load_ms": 2_500,
        "single_file_max_index_build_ms": 2_500,
        "single_file_max_validation_ms": 10_000,
        "rp5c_rows_per_stable_partition": 10_000,
        "diff_size_budget_bytes": 8_000_000,
    }
)

ACTIVE_RECORD_STATES = frozenset({"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"})
TERMINAL_RECORD_STATES = frozenset(
    {"SUPERSEDED", "DORMANT_PRESERVED", "REJECTED_INVALID", "INAPPLICABLE_WITH_PROOF"}
)
ALLOWED_RECORD_STATES = ACTIVE_RECORD_STATES | TERMINAL_RECORD_STATES

DEFINITION_REQUIRED_FIELDS = frozenset(
    {
        "display_name",
        "description",
        "component_kind",
        "family_template_ref_or_null",
        "complete_mathematical_or_procedural_definition",
        "objective_sense_or_null",
        "assumptions",
        "hard_constraints",
        "soft_preferences",
        "domain_and_boundary_behavior",
        "state_and_time_semantics",
        "input_schema",
        "output_schema",
        "units_and_bases",
        "output_accounting_class",
        "missing_stale_nonfinite_behavior",
        "precision_and_rounding",
        "parameter_schema_and_default_provenance",
        "requirements",
        "latency_class",
        "risk_materiality",
        "failure_domain_tags",
        "classical_fallback",
        "quantum",
        "implementation_versions",
        "oracle_and_test_refs",
        "equivalence_proof_refs",
    }
)

BINDING_REQUIRED_FIELDS = frozenset(
    {
        "binding_id",
        "market",
        "venue",
        "context_selector",
        "qku_binding_selector_or_null",
        "supported_modes",
        "mode_state",
        "as_of_policy",
        "selected_implementation_version",
        "binding_version",
        "selected_parameter_policy",
        "input_source_bindings",
        "venue_semantic_version",
        "portfolio_state_requirement",
        "cash_state_requirement",
        "freshness_and_TTL",
        "point_in_time_policy",
        "requirement_context_policy",
        "selected_requirement_alternatives",
        "readiness",
        "derived_state",
        "exact_resolution_action_or_null",
        "evidence_summary",
        "agent_access_policy",
        "fallback_policy",
        "runtime_snapshot_ref_or_null",
        "activation_state",
        "rollback_target_or_null",
        "upstream_value_lineage",
        "downstream_consumer_classes",
        "producer_owner",
        "validator_refs",
        "terminal_disposition_or_null",
    }
)

REQUIREMENT_REQUIRED_FIELDS = frozenset(
    {
        "required_component_id_or_source_selector",
        "required_semantic_version_constraint",
        "requirement_role",
        "required_or_optional",
        "producer_output_name",
        "consumer_input_name",
        "unit_or_basis_conversion",
        "timing_and_freshness_constraint",
        "activation_condition",
        "fallback_component_id_or_null",
        "failure_behavior",
    }
)

READINESS_DIMENSIONS = (
    "specification",
    "implementation",
    "inputs",
    "requirements",
    "oracle",
    "context",
)

FORBIDDEN_PLACEHOLDER_TEXT = frozenset(
    {"TBD", "SCOPED_GAP", "future consumer", "metadata only", "solver compatible", "route later", "placeholder"}
)

FORBIDDEN_CALLABLE_FRAGMENTS = (
    "eval(",
    "exec(",
    "pickle",
    "__import__",
    "importlib",
    "caller_result",
)

MONEY_UNIT_TOKENS = frozenset(
    {
        "MONEY",
        "CURRENCY",
        "CASH",
        "PRICE",
        "FEE",
        "NOTIONAL",
        "QUANTITY",
        "USD",
        "CENTS",
    }
)

MODE_ORDER = MappingProxyType(
    {
        "STATIC_VALIDATION": 0,
        "TEST_VECTOR": 0,
        "FIXTURE_NONLIVE": 0,
        "REFERENCE_ONLY": 0,
        "REPLAY": 1,
        "PAPER": 2,
        "SHADOW": 3,
        "DRYRUN": 4,
        "NONLIVE_ONLY": 4,
        "CANARY": 5,
        "LIVE": 6,
    }
)

ALLOWED_COMPONENT_KINDS = frozenset(
    {
        "PURE_FORMULA",
        "DETERMINISTIC_TRANSFORM",
        "STATISTICAL_ESTIMATOR",
        "STATISTICAL_TEST",
        "RISK_MEASURE",
        "OBJECTIVE_FUNCTION",
        "HARD_CONSTRAINT",
        "SOFT_PREFERENCE",
        "OPTIMIZATION_PROGRAM",
        "ALLOCATION_OR_SIZING_POLICY",
        "NUMERICAL_ALGORITHM",
        "SOLVER_PROCEDURE",
        "QUANTUM_FORMULATION",
        "EXECUTION_POLICY",
        "EXIT_POLICY",
        "GOVERNANCE_GATE",
        "DIAGNOSTIC_OR_POSTPROCESSOR",
        "COMPUTATION_STACK",
        "QKU_SELECTION_POLICY",
        # Imported incomplete source identities remain dormant and cannot be
        # resolved or computed.  This terminal classification preserves their
        # exact source meaning without inventing a computation kind.
        "SPECIFICATION_REQUIRED",
    }
)

ALLOWED_DECISION_ROLES = frozenset(
    {
        "PROBABILITY_FAIR_VALUE_UNCERTAINTY",
        "EXECUTABLE_ENTRY_ECONOMICS",
        "EXECUTABLE_EXIT_OR_SETTLEMENT",
        "EXPECTED_NET_CASH",
        "CONSERVATIVE_EDGE_OR_NET_CASH_LCB",
        "NO_TRADE_OR_ALTERNATIVE_CAPITAL_USE",
        "POSITION_SIZING_CASH_AND_RESERVES",
        "PORTFOLIO_EVENT_VENUE_EXPOSURE",
        "LIQUIDITY_FILL_CAPACITY_AND_ADVERSE_SELECTION",
        "LATENCY_FRESHNESS_AND_EDGE_DECAY",
        "ENTRY_AND_EXECUTION_POLICY",
        "EXIT_AND_LOSS_DISPOSITION",
        "TCA_ACCOUNTING_AND_RECONCILIATION",
        "HARD_SOURCE_RISK_CASH_ALLOW_AND_ROUTER_GATES",
        "DETERMINISTIC_CLASSICAL_FALLBACK",
        "RESEARCH_EVIDENCE_AND_MODEL_VALIDATION",
        "QUANTUM_MAPPING_OR_COMPARATOR",
        "INTERNAL_SUPPORT",
    }
)

ALLOWED_SOURCE_CLASSIFICATIONS = frozenset(
    {
        "OFFICIAL_PROVIDER_OR_STANDARD",
        "PEER_REVIEWED_OR_PRIMARY_RESEARCH",
        "REPUTABLE_INSTITUTIONAL",
        "OPEN_SOURCE_IMPLEMENTATION",
        "NON_OFFICIAL_RESEARCH",
        "OWNER_SUBMITTED",
        "AGENT_DISCOVERED",
    }
)

ALLOWED_QUANTUM_MATURITY = frozenset(
    {"SPECIFIED", "MAPPED", "LOCAL_EXACT_PARITY", "CLASSICAL_COMPARATOR_READY"}
)

# The expansion compiler is a build-only boundary.  A batch cannot authenticate
# itself by supplying another matching string, and runtime facade callers never
# receive this capability.
BUILD_OWNED_EXPANSION_SUBMITTERS = frozenset({"CONTROL1_CENTRAL_BUILDER"})

# A reused canonical definition may not acquire or select a new implementation
# merely because the candidate supplied matching semantic metadata.  Entries in
# this catalog are reviewed code-owned verifier functions, not caller-provided
# proof labels.  CONTROL1 intentionally starts with no generic verifier: a new
# implementation stays on its own provisional/distinct path until a concrete
# verifier is added here by reviewed code.
_BUILD_OWNED_IMPLEMENTATION_VERIFIERS: Mapping[
    str,
    Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], Iterable[str]],
] = MappingProxyType({})

PROMOTION_STATE_ORDER = MappingProxyType(
    {
        "NOT_ELIGIBLE": 0,
        "SPECIFIED": 1,
        "VERIFIED": 2,
        "CONTEXT_READY": 3,
        "STACK_READY": 4,
        "EVIDENCED": 5,
        "AUTHORIZED": 6,
    }
)

PROMOTION_AUTHORIZATION_CEILING = MappingProxyType(
    {
        "NOT_ELIGIBLE": "NOT_ELIGIBLE",
        "SPECIFIED": "NOT_ELIGIBLE",
        "VERIFIED": "ELIGIBLE",
        "CONTEXT_READY": "ELIGIBLE",
        "STACK_READY": "ELIGIBLE",
        "EVIDENCED": "ALLOW_PENDING",
        "AUTHORIZED": "AUTHORIZED",
    }
)

AUTHORIZATION_ORDER = MappingProxyType(
    {"NOT_ELIGIBLE": 0, "ELIGIBLE": 1, "ALLOW_PENDING": 2, "AUTHORIZED": 3}
)

QUANTUM_REQUIRED_FIELDS = frozenset(
    {
        "applicability_state",
        "original_economic_problem_ref",
        "problem_family",
        "formulation_candidates",
        "selected_formulation_or_none",
        "variable_encoding",
        "objective_map",
        "constraint_map",
        "penalty_policy",
        "coefficient_scaling",
        "precision_and_quantization",
        "decomposition_or_embedding",
        "warm_start",
        "optimizer_and_version",
        "shots_reads_or_sampling_policy",
        "inverse_map",
        "original_model_feasibility_check",
        "same_formulation_classical_comparator",
        "local_exact_or_small_instance_parity",
        "fallback",
        "maturity_ceiling",
    }
)

FORBIDDEN_QUANTUM_CLAIMS = frozenset(
    {
        "TRUE_QPU_EXECUTED",
        "ECONOMIC_UTILITY_POSITIVE",
        "QUANTUM_ADVANTAGE",
        "LIVE_QUANTUM_AUTHORIZED",
    }
)


def _stable_json(value: Any) -> str:
    return json.dumps(json_compatible(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _record_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return (str(record["canonical_component_id"]), str(record["semantic_version"]))


def _binding_key(component_id: str, binding: Mapping[str, Any]) -> tuple[str, str]:
    return component_id, str(binding["binding_id"])


def _canonical_value(value: Any) -> Any:
    """Comparable, non-persisted semantic form; it is not a digest authority."""

    if isinstance(value, Mapping):
        return tuple((str(key), _canonical_value(item)) for key, item in sorted(value.items(), key=lambda pair: str(pair[0])))
    if isinstance(value, (list, tuple)):
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, Decimal):
        return ("DECIMAL", format(value, "f"))
    if isinstance(value, float):
        if not math.isfinite(value):
            return ("NONFINITE", repr(value))
        return ("FLOAT", format(value, ".17g"))
    return value


def _definition_semantic_core(definition: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    # Names are lookup/provenance hints, never identity proof.  Complete
    # semantics live in the typed procedure, domain, units, requirements, and
    # related fields.  Validation metadata is append-only rather than part of
    # semantic identity.
    excluded = {
        "display_name",
        "description",
        "implementation_versions",
        "oracle_and_test_refs",
        "equivalence_proof_refs",
    }
    order_insensitive = {
        "assumptions",
        "hard_constraints",
        "soft_preferences",
        "failure_domain_tags",
        "requirements",
        "input_schema",
        "output_schema",
    }
    normalized: list[tuple[str, Any]] = []
    for key, value in sorted(definition.items()):
        if key in excluded:
            continue
        canonical = _canonical_value(value)
        if key in order_insensitive and isinstance(canonical, tuple):
            canonical = tuple(sorted(canonical, key=repr))
        normalized.append((str(key), canonical))
    return tuple(normalized)


def _requirement_identity(requirement: Mapping[str, Any]) -> Any:
    return _canonical_value({key: requirement.get(key) for key in sorted(REQUIREMENT_REQUIRED_FIELDS)})


def _is_canonical_component_id(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_.:-]{4,199}", value)) and "SOURCE_SELECTOR" not in value


def _contains_forbidden_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped in FORBIDDEN_PLACEHOLDER_TEXT
    if isinstance(value, Mapping):
        return any(_contains_forbidden_placeholder(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_placeholder(item) for item in value)
    return False


def _validate_evidence_compact(evidence: Mapping[str, Any], *, path: str) -> None:
    bulk_key_fragments = (
        "history",
        "order_book",
        "fills",
        "ledger_rows",
        "bootstrap_samples",
        "qpu_samples",
        "time_series",
        "source_document",
        "trial_rows",
    )
    if len(_stable_json(evidence).encode("utf-8")) > 64_000:
        raise ValueError(f"EMBEDDED_BULK_EVIDENCE: {path} exceeds compact byte budget")

    visited_nodes = 0

    def visit(value: Any, *, value_path: str, depth: int) -> None:
        nonlocal visited_nodes
        visited_nodes += 1
        if visited_nodes > 512:
            raise ValueError(f"EMBEDDED_BULK_EVIDENCE: {path} exceeds compact value budget")
        if depth > 8:
            raise ValueError(f"EMBEDDED_BULK_EVIDENCE: {value_path} exceeds compact depth")
        if isinstance(value, Mapping):
            if len(value) > 64:
                raise ValueError(
                    f"EMBEDDED_BULK_EVIDENCE: {value_path} has {len(value)} entries"
                )
            for key, item in value.items():
                lowered = str(key).lower()
                item_path = f"{value_path}.{key}"
                if any(fragment in lowered for fragment in bulk_key_fragments) and isinstance(
                    item, (list, tuple, Mapping)
                ):
                    if len(item) > 0:
                        raise ValueError(f"EMBEDDED_BULK_EVIDENCE: {item_path}")
                visit(item, value_path=item_path, depth=depth + 1)
            return
        if isinstance(value, (list, tuple)):
            if len(value) > 64:
                raise ValueError(
                    f"EMBEDDED_BULK_EVIDENCE: {value_path} has {len(value)} entries"
                )
            for index, item in enumerate(value):
                visit(item, value_path=f"{value_path}[{index}]", depth=depth + 1)
            return
        if isinstance(value, str) and len(value.encode("utf-8")) > 4_096:
            raise ValueError(f"EMBEDDED_BULK_EVIDENCE: {value_path} has oversized text")

    visit(evidence, value_path=path, depth=0)


def _selector_value_is_wildcard(value: Any) -> bool:
    return value is None or str(value).upper() in {"ANY", "ALL", "*"}


def _selector_values_overlap(left: Any, right: Any) -> bool:
    return (
        _selector_value_is_wildcard(left)
        or _selector_value_is_wildcard(right)
        or _canonical_value(left) == _canonical_value(right)
    )


def _binding_selector_domains_overlap(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> bool:
    """Return whether two reusable binding selectors can match one request."""

    if not _selector_values_overlap(left.get("market"), right.get("market")):
        return False
    if not _selector_values_overlap(left.get("venue"), right.get("venue")):
        return False
    left_modes = {str(value) for value in left.get("supported_modes", ())}
    right_modes = {str(value) for value in right.get("supported_modes", ())}
    if not left_modes or not right_modes or not left_modes.intersection(right_modes):
        return False
    if not _selector_values_overlap(
        left.get("qku_binding_selector_or_null"),
        right.get("qku_binding_selector_or_null"),
    ):
        return False
    left_selector = left.get("context_selector", {})
    right_selector = right.get("context_selector", {})
    if not isinstance(left_selector, Mapping) or not isinstance(right_selector, Mapping):
        return _selector_values_overlap(left_selector, right_selector)
    for key in set(left_selector).intersection(right_selector):
        if not _selector_values_overlap(left_selector[key], right_selector[key]):
            return False
    return True


def _validate_quantum_block(
    quantum: Any, *, component_id: str, component_kind: str
) -> None:
    if not isinstance(quantum, Mapping):
        raise ValueError(f"INVALID_QUANTUM_BLOCK: {component_id}")
    missing = sorted(QUANTUM_REQUIRED_FIELDS - set(quantum))
    if missing:
        raise ValueError(f"MISSING_QUANTUM_FIELDS: {component_id}: {missing}")
    maturity = str(quantum.get("maturity_ceiling", ""))
    if maturity not in ALLOWED_QUANTUM_MATURITY:
        raise ValueError(f"FORBIDDEN_QUANTUM_MATURITY_OR_CLAIM: {component_id}: {maturity}")
    # CONTROL1 records may describe a mapping, comparator, and intended local
    # proof route, but the generic record boundary must not let authored labels
    # manufacture an executed parity result.  A later independent promotion
    # path can derive a higher maturity from executed proof receipts.
    if maturity != "SPECIFIED":
        raise ValueError(
            f"QUANTUM_MATURITY_REQUIRES_INDEPENDENT_PROMOTION_AUTHORITY: "
            f"{component_id}: {maturity}"
        )

    def scan(value: Any) -> None:
        if isinstance(value, str) and value.upper() in FORBIDDEN_QUANTUM_CLAIMS:
            raise ValueError(
                f"FORBIDDEN_QUANTUM_MATURITY_OR_CLAIM: {component_id}: {value}"
            )
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized_key = str(key).upper()
                if item is True and (
                    "QUANTUM_ADVANTAGE" in normalized_key
                    or "QPU_EXECUTION" in normalized_key
                    or "BACKEND_EXECUTION" in normalized_key
                ):
                    raise ValueError(
                        f"FORBIDDEN_QUANTUM_CLAIM_OR_QPU_EXECUTION: {component_id}: {key}"
                    )
                scan(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                scan(item)

    scan(quantum)
    applicability = str(quantum.get("applicability_state", ""))
    applicable = component_kind == "QUANTUM_FORMULATION" or not applicability.startswith(
        "NOT_APPLICABLE"
    )
    if applicable:
        required_nonempty = (
            "original_economic_problem_ref",
            "problem_family",
            "objective_map",
            "inverse_map",
            "same_formulation_classical_comparator",
            "fallback",
        )
        missing_meaning = [name for name in required_nonempty if not quantum.get(name)]
        missing_meaning.extend(
            name
            for name in ("variable_encoding", "constraint_map")
            if quantum.get(name) is None
        )
        if missing_meaning:
            raise ValueError(
                f"INCOMPLETE_APPLICABLE_QUANTUM_MAPPING: {component_id}: {missing_meaning}"
            )


def _validate_requirement_semantics(
    requirement: Mapping[str, Any], *, component_id: str
) -> None:
    required_or_optional = str(requirement.get("required_or_optional", ""))
    if required_or_optional not in {"REQUIRED", "OPTIONAL"}:
        raise ValueError(
            f"INVALID_REQUIREMENT_OPTIONALITY: {component_id}: {required_or_optional}"
        )
    activation = requirement.get("activation_condition")
    if isinstance(activation, str):
        if activation not in {"ALWAYS", "NEVER"}:
            raise ValueError(
                f"INVALID_REQUIREMENT_ACTIVATION: {component_id}: {activation}"
            )
    elif isinstance(activation, Mapping):
        if not str(activation.get("context_field", "")) or "equals" not in activation:
            raise ValueError(f"INVALID_REQUIREMENT_ACTIVATION: {component_id}")
    else:
        raise ValueError(f"INVALID_REQUIREMENT_ACTIVATION: {component_id}")
    failure_behavior = str(requirement.get("failure_behavior", ""))
    if failure_behavior not in {
        "FAIL_CLOSED",
        "USE_FALLBACK",
        "USE_FALLBACK_FAIL_CLOSED",
    }:
        raise ValueError(
            f"INVALID_REQUIREMENT_FAILURE_BEHAVIOR: {component_id}: {failure_behavior}"
        )
    fallback = requirement.get("fallback_component_id_or_null")
    if failure_behavior.startswith("USE_FALLBACK") and not fallback:
        raise ValueError(f"FALLBACK_COMPONENT_REQUIRED: {component_id}")
    timing = str(requirement.get("timing_and_freshness_constraint", ""))
    if not timing or not timing.startswith(("SAME_REQUEST", "AS_OF", "LAGGED", "PRIOR_STATE")):
        raise ValueError(f"INVALID_REQUIREMENT_TIMING: {component_id}: {timing}")
    if timing.startswith(("LAGGED", "PRIOR_STATE")):
        raise ValueError(
            f"TEMPORAL_FEEDBACK_MUST_BE_TYPED_PRIOR_STATE_INPUT: {component_id}: {timing}"
        )


def _validate_mode_state(
    state: Any, *, component_id: str, binding_id: str, mode: str
) -> None:
    if isinstance(state, Mapping):
        evidence = state.get("evidence")
        if evidence is not None and str(evidence) not in {
            "NONE",
            "FIXTURE",
            "REPLAY",
            "PAPER",
            "SHADOW",
            "DRYRUN",
            "CANARY",
            "LIVE",
        }:
            raise ValueError(
                f"INVALID_MODE_EVIDENCE_STATE: {component_id}: {binding_id}: {mode}"
            )
        authorization = state.get("authorization")
        if authorization is not None and str(authorization) not in {
            "NOT_ELIGIBLE",
            "NOT_AUTHORIZED",
            "ELIGIBLE",
            "ALLOW_PENDING",
            "AUTHORIZED",
        }:
            raise ValueError(
                f"INVALID_MODE_AUTHORIZATION_STATE: {component_id}: {binding_id}: {mode}"
            )
        eligibility = state.get("eligibility")
        if eligibility is not None and str(eligibility) not in {
            "NOT_ELIGIBLE",
            "ELIGIBLE",
            "ALLOW_PENDING",
            "AUTHORIZED",
        }:
            raise ValueError(
                f"INVALID_MODE_ELIGIBILITY_STATE: {component_id}: {binding_id}: {mode}"
            )
        if evidence is None and authorization is None and not state.get("state"):
            raise ValueError(f"EMPTY_MODE_STATE: {component_id}: {binding_id}: {mode}")
        return
    if str(state) not in {
        "FIXTURE_ONLY",
        "REFERENCE_ONLY",
        "NOT_ELIGIBLE",
        "ELIGIBLE",
        "ALLOW_PENDING",
        "AUTHORIZED",
        "NOT_AUTHORIZED",
        "DISABLED",
        "BLOCKED",
        "INELIGIBLE",
    }:
        raise ValueError(
            f"INVALID_MODE_STATE_VALUE: {component_id}: {binding_id}: {mode}={state}"
        )


def _validate_record_shape(
    record: Mapping[str, Any], *, _allow_source_selectors: bool = False
) -> None:
    """Fail closed on the canonical persistent record contract."""

    required_top = {
        "canonical_component_id",
        "semantic_version",
        "record_state",
        "origin_cohorts",
        "definition",
        "uses",
        "bindings",
        "provenance",
        "relations",
        "governance",
    }
    missing_top = sorted(required_top - set(record))
    if missing_top:
        raise ValueError(f"MISSING_RECORD_FIELDS: {missing_top}")
    component_id = str(record["canonical_component_id"])
    if not _is_canonical_component_id(component_id):
        raise ValueError(f"INVALID_CANONICAL_COMPONENT_ID: {component_id}")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", str(record["semantic_version"])):
        raise ValueError(f"INVALID_SEMANTIC_VERSION: {component_id}")
    if record["record_state"] not in ALLOWED_RECORD_STATES:
        raise ValueError(f"INVALID_RECORD_STATE: {component_id}")
    definition = record["definition"]
    if not isinstance(definition, Mapping):
        raise ValueError(f"INVALID_DEFINITION: {component_id}")
    missing_definition = sorted(DEFINITION_REQUIRED_FIELDS - set(definition))
    if missing_definition:
        raise ValueError(f"MISSING_DEFINITION_FIELDS: {component_id}: {missing_definition}")
    if _contains_forbidden_placeholder(record):
        raise ValueError(f"GENERIC_PLACEHOLDER_TERMINAL: {component_id}")
    component_kind = str(definition.get("component_kind", ""))
    if component_kind not in ALLOWED_COMPONENT_KINDS:
        raise ValueError(f"INVALID_COMPONENT_KIND: {component_id}: {component_kind}")
    _validate_quantum_block(
        definition.get("quantum"),
        component_id=component_id,
        component_kind=component_kind,
    )
    requirements = definition.get("requirements")
    if not isinstance(requirements, (list, tuple)):
        raise ValueError(f"INVALID_REQUIREMENTS: {component_id}")
    seen_requirements: set[Any] = set()
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            raise ValueError(f"INVALID_REQUIREMENT: {component_id}")
        missing_requirement = sorted(REQUIREMENT_REQUIRED_FIELDS - set(requirement))
        if missing_requirement:
            raise ValueError(f"MISSING_REQUIREMENT_FIELDS: {component_id}: {missing_requirement}")
        _validate_requirement_semantics(requirement, component_id=component_id)
        target = str(requirement["required_component_id_or_source_selector"])
        if not _is_canonical_component_id(target) and not (
            _allow_source_selectors and target.strip()
        ):
            raise ValueError(f"SOURCE_LOCAL_REQUIREMENT_TARGET: {component_id}: {target}")
        fallback = requirement.get("fallback_component_id_or_null")
        if fallback and not _is_canonical_component_id(str(fallback)) and not (
            _allow_source_selectors and str(fallback).strip()
        ):
            raise ValueError(
                f"SOURCE_LOCAL_FALLBACK_TARGET: {component_id}: {fallback}"
            )
        identity = _requirement_identity(requirement)
        if identity in seen_requirements:
            raise ValueError(f"DUPLICATE_REQUIREMENT_NOT_COLLAPSED: {component_id}")
        seen_requirements.add(identity)
    implementations = definition.get("implementation_versions")
    if not isinstance(implementations, (list, tuple)):
        raise ValueError(f"INVALID_IMPLEMENTATION_VERSIONS: {component_id}")
    for implementation in implementations:
        if not isinstance(implementation, Mapping):
            raise ValueError(f"INVALID_IMPLEMENTATION_VERSION: {component_id}")
        ref = str(implementation.get("callable_or_solver_ref", ""))
        if not ref:
            raise ValueError(f"MISSING_CALLABLE_REF: {component_id}")
        if any(fragment in ref.lower() for fragment in FORBIDDEN_CALLABLE_FRAGMENTS):
            raise ValueError(f"UNSAFE_DYNAMIC_DISPATCH_REF: {component_id}: {ref}")
        embedded_fixture_keys = {
            "fixture_inputs",
            "fixture_outputs",
            "fixture_vectors",
            "test_inputs",
            "test_outputs",
            "test_vectors",
            "golden_vector",
            "golden_vectors",
        } & set(implementation)
        if embedded_fixture_keys:
            raise ValueError(
                f"CANONICAL_FIXTURE_PAYLOAD: {component_id}: {sorted(embedded_fixture_keys)}"
            )
    parameter_block = definition.get("parameter_schema_and_default_provenance")
    parameter_schema = _parameter_schema_map(parameter_block)
    block_default_provenance = (
        parameter_block.get("default_provenance")
        if isinstance(parameter_block, Mapping)
        else None
    )
    for parameter_name, parameter_spec in parameter_schema.items():
        default_present = "default" in parameter_spec or "default_value" in parameter_spec
        if not default_present:
            continue
        default_value = parameter_spec.get(
            "default", parameter_spec.get("default_value")
        )
        if not parameter_spec.get("default_provenance") and not block_default_provenance:
            raise ValueError(
                f"MISSING_PARAMETER_DEFAULT_PROVENANCE: {component_id}: {parameter_name}"
            )
        _validate_schema_value(
            default_value,
            parameter_spec,
            path=f"{component_id}.definition.parameter.{parameter_name}.default",
        )
    uses = record["uses"]
    if not isinstance(uses, Mapping):
        raise ValueError(f"INVALID_USES: {component_id}")
    for field_name in ("decision_roles", "decision_outputs", "market_family_tags", "qku_role_bindings", "consumer_class_tags"):
        if field_name not in uses:
            raise ValueError(f"MISSING_USES_FIELD: {component_id}: {field_name}")
    invalid_roles = sorted(
        {str(value) for value in uses.get("decision_roles", ())}
        - ALLOWED_DECISION_ROLES
    )
    if invalid_roles:
        raise ValueError(f"INVALID_DECISION_ROLE: {component_id}: {invalid_roles}")
    qku_bindings = uses.get("qku_role_bindings")
    if not isinstance(qku_bindings, (list, tuple)):
        raise ValueError(f"INVALID_QKU_ROLE_BINDINGS: {component_id}")
    for qku_binding in qku_bindings:
        if not isinstance(qku_binding, Mapping):
            raise ValueError(f"INVALID_QKU_ROLE_BINDING: {component_id}")
    origins = {str(value) for value in record.get("origin_cohorts", ())}
    if "RP5C_BASELINE" in origins and qku_bindings:
        if record["record_state"] != "DORMANT_PRESERVED":
            raise ValueError(f"RP5C_QKU_ROLE_RUNTIME_ACTIVATION: {component_id}")
        for qku_binding in qku_bindings:
            if (
                qku_binding.get("stack_root_or_direct_component") is not None
                or qku_binding.get("selection_rule_if_container") is not None
                or qku_binding.get("runtime_root_eligibility")
                != "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            ):
                raise ValueError(f"RP5C_QKU_ROLE_RUNTIME_ROOT: {component_id}")
        ineligibility_relations = [
            relation
            for relation in record.get("relations", ())
            if isinstance(relation, Mapping)
            and _relation_type(relation) == "RP5C_RUNTIME_ROOT_INELIGIBILITY"
        ]
        if len(ineligibility_relations) != 1:
            raise ValueError(f"RP5C_QKU_ROLE_INELIGIBILITY_PROOF: {component_id}")
        ineligibility = ineligibility_relations[0]
        if (
            ineligibility.get("runtime_root_eligible") is not False
            or ineligibility.get("selector_or_root_invented") is not False
            or ineligibility.get("qku_roles_erased") is not False
            or ineligibility.get("preserved_qku_role_count") != len(qku_bindings)
        ):
            raise ValueError(f"RP5C_QKU_ROLE_INELIGIBILITY_PROOF: {component_id}")
    bindings = record["bindings"]
    if not isinstance(bindings, (list, tuple)):
        raise ValueError(f"INVALID_BINDINGS: {component_id}")
    seen_binding_ids: set[str] = set()
    validated_bindings: list[Mapping[str, Any]] = []
    for binding in bindings:
        if not isinstance(binding, Mapping):
            raise ValueError(f"INVALID_BINDING: {component_id}")
        missing_binding = sorted(BINDING_REQUIRED_FIELDS - set(binding))
        if missing_binding:
            raise ValueError(f"MISSING_BINDING_FIELDS: {component_id}: {missing_binding}")
        binding_id = str(binding["binding_id"])
        if not re.fullmatch(r"[A-Z][A-Z0-9_.:-]{3,199}", binding_id):
            raise ValueError(f"INVALID_BINDING_ID: {component_id}: {binding_id}")
        if binding_id in seen_binding_ids:
            raise ValueError(f"DUPLICATE_BINDING_ID: {component_id}: {binding_id}")
        seen_binding_ids.add(binding_id)
        selected_parameter_policy = binding.get("selected_parameter_policy")
        if not isinstance(selected_parameter_policy, Mapping):
            raise ValueError(
                f"INVALID_SELECTED_PARAMETER_POLICY: {component_id}: {binding_id}"
            )
        selected_defaults = selected_parameter_policy.get(
            "defaults", selected_parameter_policy.get("values", {})
        )
        if selected_defaults is None:
            selected_defaults = {}
        if not isinstance(selected_defaults, Mapping):
            raise ValueError(
                f"INVALID_PARAMETER_DEFAULTS: {component_id}: {binding_id}"
            )
        for parameter_name, default_value in selected_defaults.items():
            parameter_name = str(parameter_name)
            parameter_spec = parameter_schema.get(parameter_name)
            if parameter_spec is None:
                raise ValueError(
                    f"UNDECLARED_PARAMETER_DEFAULT: {component_id}: "
                    f"{binding_id}: {parameter_name}"
                )
            if not selected_parameter_policy.get(
                "default_provenance"
            ) and not parameter_spec.get("default_provenance") and not block_default_provenance:
                raise ValueError(
                    f"MISSING_PARAMETER_DEFAULT_PROVENANCE: {component_id}: "
                    f"{binding_id}: {parameter_name}"
                )
            _validate_schema_value(
                default_value,
                parameter_spec,
                path=f"{component_id}.{binding_id}.parameter.{parameter_name}",
            )
        supported_modes = {str(value) for value in binding.get("supported_modes", ())}
        invalid_modes = sorted(supported_modes - set(MODE_ORDER))
        if invalid_modes:
            raise ValueError(
                f"INVALID_SUPPORTED_MODE: {component_id}: {binding_id}: {invalid_modes}"
            )
        mode_state = binding.get("mode_state")
        if not isinstance(mode_state, Mapping):
            raise ValueError(f"INVALID_MODE_STATE: {component_id}: {binding_id}")
        missing_mode_states = sorted(supported_modes - {str(value) for value in mode_state})
        if missing_mode_states:
            raise ValueError(
                f"MODE_STATE_COVERAGE_MISSING: {component_id}: {binding_id}: {missing_mode_states}"
            )
        extra_mode_states = sorted({str(value) for value in mode_state} - supported_modes)
        if extra_mode_states:
            raise ValueError(
                f"MODE_STATE_WITHOUT_SUPPORTED_MODE: {component_id}: {binding_id}: {extra_mode_states}"
            )
        for mode in supported_modes:
            _validate_mode_state(
                mode_state[mode],
                component_id=component_id,
                binding_id=binding_id,
                mode=mode,
            )
        alternatives = binding.get("selected_requirement_alternatives")
        if not isinstance(alternatives, (list, tuple)):
            raise ValueError(
                f"INVALID_REQUIREMENT_ALTERNATIVES: {component_id}: {binding_id}"
            )
        for alternative in alternatives:
            if not isinstance(alternative, Mapping) or not alternative.get(
                "requirement_role"
            ) or not alternative.get("selected_component_id"):
                raise ValueError(
                    f"INVALID_REQUIREMENT_ALTERNATIVE: {component_id}: {binding_id}"
                )
            matching = [
                requirement
                for requirement in requirements
                if str(requirement.get("requirement_role"))
                == str(alternative["requirement_role"])
            ]
            selected = str(alternative["selected_component_id"])
            if len(matching) != 1 or selected not in {
                str(matching[0].get("required_component_id_or_source_selector"))
                if matching
                else "",
                str(matching[0].get("fallback_component_id_or_null"))
                if matching and matching[0].get("fallback_component_id_or_null")
                else "",
            }:
                raise ValueError(
                    f"UNDECLARED_REQUIREMENT_ALTERNATIVE: {component_id}: {binding_id}"
                )
        fallback_policy = binding.get("fallback_policy")
        if not isinstance(fallback_policy, Mapping):
            raise ValueError(f"INVALID_FALLBACK_POLICY: {component_id}: {binding_id}")
        fallback_behavior = str(
            fallback_policy.get("behavior", fallback_policy.get("state", "FAIL_CLOSED"))
        )
        if fallback_behavior not in {
            "FAIL_CLOSED",
            "NOT_REQUIRED",
            "USE_FALLBACK",
            "USE_FALLBACK_FAIL_CLOSED",
        }:
            raise ValueError(
                f"INVALID_FALLBACK_BEHAVIOR: {component_id}: {binding_id}: {fallback_behavior}"
            )
        fallback_component = fallback_policy.get(
            "fallback_component_id", fallback_policy.get("component_id")
        )
        if fallback_behavior.startswith("USE_FALLBACK") and not fallback_component:
            raise ValueError(
                f"FALLBACK_COMPONENT_REQUIRED: {component_id}: {binding_id}"
            )
        for prior in validated_bindings:
            if _binding_selector_domains_overlap(prior, binding):
                raise ValueError(
                    "OVERLAPPING_BINDING_SELECTORS: "
                    f"{component_id}: {prior['binding_id']} <> {binding_id}"
                )
        validated_bindings.append(binding)
        readiness = binding["readiness"]
        if not isinstance(readiness, Mapping):
            raise ValueError(f"INVALID_READINESS: {component_id}: {binding_id}")
        for dimension in READINESS_DIMENSIONS:
            if readiness.get(dimension) not in {"PASS", "REQUIRED", "INVALID"}:
                raise ValueError(f"INVALID_READINESS_DIMENSION: {component_id}: {binding_id}: {dimension}")
        if readiness.get("evidence") not in {"NONE", "FIXTURE", "REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}:
            raise ValueError(f"INVALID_EVIDENCE_STATE: {component_id}: {binding_id}")
        if readiness.get("authorization") not in {"NOT_ELIGIBLE", "ELIGIBLE", "ALLOW_PENDING", "AUTHORIZED"}:
            raise ValueError(f"INVALID_AUTHORIZATION_STATE: {component_id}: {binding_id}")
        evidence = binding.get("evidence_summary", {})
        if not isinstance(evidence, Mapping):
            raise ValueError(f"INVALID_EVIDENCE_SUMMARY: {component_id}: {binding_id}")
        _validate_evidence_compact(evidence, path=f"{component_id}.{binding_id}.evidence_summary")
    if "RP5C_BASELINE" in origins and qku_bindings:
        if any(
            binding.get("activation_state") != "DORMANT_PRESERVED"
            or binding.get("supported_modes")
            or binding.get("readiness", {}).get("authorization") != "NOT_ELIGIBLE"
            for binding in validated_bindings
        ):
            raise ValueError(f"RP5C_QKU_ROLE_RUNTIME_BINDING: {component_id}")
    if not bindings and record["record_state"] in ACTIVE_RECORD_STATES:
        disposition = record.get("terminal_disposition") or record.get("exact_resolution_action")
        if not disposition:
            raise ValueError(f"ACTIVE_RECORD_WITHOUT_BINDING_OR_ACTION: {component_id}")
    if not isinstance(record["provenance"], (list, tuple)) or not record["provenance"]:
        raise ValueError(f"MISSING_PROVENANCE: {component_id}")
    if not isinstance(record["relations"], (list, tuple)):
        raise ValueError(f"INVALID_RELATIONS: {component_id}")
    governance = record["governance"]
    for field_name in ("producer_owner", "validator_refs", "reviewer_or_challenger_owner", "change_authority"):
        if field_name not in governance:
            raise ValueError(f"MISSING_GOVERNANCE_FIELD: {component_id}: {field_name}")
    serialized_bytes = len(_stable_json(record).encode("utf-8"))
    if serialized_bytes > int(STORAGE_POLICY["max_record_serialized_bytes"]):
        raise ValueError(f"OVERSIZED_RECORD: {component_id}: {serialized_bytes}")
    # Materialize the one immutable record value type at the boundary.  The
    # mapping remains the JSONL serialization view; this wrapper is not a
    # second registry or authority.
    ComputationRecordV1.from_mapping(record)


def _stable_partition_name(component_id: str) -> tuple[str, str, str]:
    """Return stable filename token and inclusive logical range labels."""

    rp5c_match = re.fullmatch(r"QTT\.COMP\.RP5C\.(\d{8})", component_id)
    if rp5c_match:
        number = int(rp5c_match.group(1))
        width = int(STORAGE_POLICY["rp5c_rows_per_stable_partition"])
        lower = (number // width) * width
        upper = lower + width - 1
        token = f"rp5c-{lower:08d}-{upper:08d}"
        return token, f"QTT.COMP.RP5C.{lower:08d}", f"QTT.COMP.RP5C.{upper:08d}"
    numeric_match = re.fullmatch(r"(.+?)(\d{6,})", component_id)
    if numeric_match:
        prefix, raw_number = numeric_match.groups()
        number = int(raw_number)
        width = int(STORAGE_POLICY["rp5c_rows_per_stable_partition"])
        lower = (number // width) * width
        upper = lower + width - 1
        digits = len(raw_number)
        prefix_token = re.sub(
            r"[^a-z0-9-]+", "-", prefix.removeprefix("QTT.COMP.").lower()
        ).strip("-") or "other"
        token = f"other-{prefix_token}-{lower:0{digits}d}-{upper:0{digits}d}"
        return (
            token,
            f"{prefix}{lower:0{digits}d}",
            f"{prefix}{upper:0{digits}d}",
        )
    categories = (
        ("QTT.COMP.OWNER_REQUIREMENT.", "owner-requirements"),
        ("QTT.COMP.REQUIREMENT.", "requirements"),
        ("QTT.COMP.FORMULA.", "formula"),
        ("QTT.COMP.ALGORITHM.", "algorithm"),
        ("QTT.COMP.QUANTUM.", "quantum"),
        ("QTT.COMP.STACK.", "stack"),
        ("QTT.COMP.NATIVE.", "native"),
    )
    for prefix, token in categories:
        if component_id.startswith(prefix):
            return token, prefix, f"{prefix}\uffff"
    suffix = component_id.removeprefix("QTT.COMP.").split(".", 1)[0].lower()
    suffix = re.sub(r"[^a-z0-9-]+", "-", suffix).strip("-") or "other"
    return f"other-{suffix}", f"QTT.COMP.{suffix.upper()}.", f"QTT.COMP.{suffix.upper()}.\uffff"


@dataclass(frozen=True)
class _RegistryPartition:
    """One deterministic physical slice of the single logical registry."""

    token: str
    range_start: str
    range_end: str
    records: tuple[Mapping[str, Any], ...]

    @property
    def file_name(self) -> str:
        return f"registry.part-{self.token}.jsonl"

    def manifest_row(self) -> dict[str, Any]:
        return {
            "file": self.file_name,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "row_count": len(self.records),
        }


def _partition_serialized_bytes(records: Sequence[Mapping[str, Any]]) -> int:
    return sum(len(_stable_json(record).encode("utf-8")) + 1 for record in records)


def _partition_exceeds_policy(records: Sequence[Mapping[str, Any]]) -> bool:
    return (
        len(records) > int(STORAGE_POLICY["rp5c_rows_per_stable_partition"])
        or _partition_serialized_bytes(records) > int(STORAGE_POLICY["diff_size_budget_bytes"])
    )


def _fixed_range_common_prefix(range_start: str, range_end: str) -> str:
    limit = min(len(range_start), len(range_end))
    position = 0
    while position < limit and range_start[position] == range_end[position]:
        position += 1
    return range_start[:position]


def _partition_character_token(character: str) -> str:
    if not character:
        return "end"
    if "A" <= character <= "Z" or "0" <= character <= "9":
        return character.lower()
    return {
        ".": "dot",
        "_": "underscore",
        ":": "colon",
        "-": "dash",
    }.get(character, f"u{ord(character):04x}")


def _split_oversized_partition(
    *,
    token: str,
    range_start: str,
    range_end: str,
    records: Sequence[Mapping[str, Any]],
    split_prefix: str,
) -> list[_RegistryPartition]:
    """Split only an oversized prefix/range using canonical-ID characters.

    Every consumed character is retained in the child token even when the
    current population has only one child.  Consequently, introducing a new
    sibling prefix later does not rename or repartition the existing sibling.
    The token is a reversible character encoding, never a hash or digest.
    """

    sorted_records = tuple(sorted(records, key=_record_key))
    if not _partition_exceeds_policy(sorted_records):
        return [
            _RegistryPartition(
                token=token,
                range_start=range_start,
                range_end=range_end,
                records=sorted_records,
            )
        ]

    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in sorted_records:
        component_id = str(record["canonical_component_id"])
        if not component_id.startswith(split_prefix):
            raise ValueError(
                "REGISTRY_PARTITION_PREFIX_MISMATCH: "
                f"{token}: {split_prefix!r}: {component_id}"
            )
        remainder = component_id[len(split_prefix) :]
        groups[remainder[:1]].append(record)

    if set(groups) == {""}:
        raise ValueError(
            "UNSPLITTABLE_OVERSIZED_CANONICAL_ID_PARTITION: "
            f"{sorted_records[0]['canonical_component_id']}"
        )

    result: list[_RegistryPartition] = []
    for character in sorted(groups):
        child_records = groups[character]
        child_token = f"{token}-s-{_partition_character_token(character)}"
        if character:
            child_prefix = f"{split_prefix}{character}"
            child_start = child_prefix
            child_end = f"{child_prefix}\uffff"
        else:
            child_prefix = split_prefix
            child_start = split_prefix
            child_end = split_prefix
        result.extend(
            _split_oversized_partition(
                token=child_token,
                range_start=child_start,
                range_end=child_end,
                records=child_records,
                split_prefix=child_prefix,
            )
        )
    return result


def _registry_partitions(records: Sequence[Mapping[str, Any]]) -> tuple[_RegistryPartition, ...]:
    """Derive the only valid deterministic shard set from logical records."""

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    ranges: dict[str, tuple[str, str]] = {}
    for record in sorted(records, key=_record_key):
        token, lower, upper = _stable_partition_name(str(record["canonical_component_id"]))
        prior_range = ranges.setdefault(token, (lower, upper))
        if prior_range != (lower, upper):
            raise ValueError(
                "REGISTRY_BASE_PARTITION_TOKEN_COLLISION: "
                f"{token}: {prior_range!r} != {(lower, upper)!r}"
            )
        grouped[token].append(record)

    partitions: list[_RegistryPartition] = []
    for token in sorted(grouped):
        lower, upper = ranges[token]
        base_records = grouped[token]
        if _partition_exceeds_policy(base_records):
            split_prefix = _fixed_range_common_prefix(lower, upper)
            if not split_prefix:
                raise ValueError(f"REGISTRY_PARTITION_HAS_NO_STABLE_PREFIX: {token}")
            partitions.extend(
                _split_oversized_partition(
                    token=token,
                    range_start=lower,
                    range_end=upper,
                    records=base_records,
                    split_prefix=split_prefix,
                )
            )
        else:
            partitions.append(
                _RegistryPartition(
                    token=token,
                    range_start=lower,
                    range_end=upper,
                    records=tuple(sorted(base_records, key=_record_key)),
                )
            )
    return tuple(sorted(partitions, key=lambda partition: partition.file_name))


def _measure_storage_policy(
    records: Sequence[Mapping[str, Any]], *, validation_ms: float
) -> dict[str, Any]:
    """Measure every centralized input used by the physical-layout policy."""

    serialized_records = tuple(_stable_json(record) for record in records)
    record_sizes = tuple(len(value.encode("utf-8")) for value in serialized_records)
    serialized_lines = tuple(f"{value}\n" for value in serialized_records)
    line_sizes = tuple(size + 1 for size in record_sizes)

    load_started = time.perf_counter()
    for line in serialized_lines:
        json.loads(line)
    measured_load_ms = (time.perf_counter() - load_started) * 1_000

    index_started = time.perf_counter()
    _build_indexes(records)
    measured_index_ms = (time.perf_counter() - index_started) * 1_000

    return {
        "row_count": len(records),
        "serialized_bytes": sum(line_sizes),
        "maximum_record_serialized_bytes": max(record_sizes, default=0),
        "load_ms": measured_load_ms,
        "index_build_ms": measured_index_ms,
        "validation_ms": validation_ms,
        "diff_candidate_bytes": sum(line_sizes),
    }


def _storage_policy_reasons(measurements: Mapping[str, Any]) -> tuple[str, ...]:
    checks = (
        ("ROW_COUNT", "row_count", "single_file_max_rows"),
        ("SERIALIZED_BYTES", "serialized_bytes", "single_file_max_serialized_bytes"),
        ("MAXIMUM_RECORD_SIZE", "maximum_record_serialized_bytes", "max_record_serialized_bytes"),
        ("LOAD_TIME", "load_ms", "single_file_max_load_ms"),
        ("INDEX_BUILD_TIME", "index_build_ms", "single_file_max_index_build_ms"),
        ("VALIDATION_TIME", "validation_ms", "single_file_max_validation_ms"),
        ("DIFF_SIZE_BUDGET", "diff_candidate_bytes", "diff_size_budget_bytes"),
    )
    return tuple(
        reason
        for reason, measurement_key, policy_key in checks
        if float(measurements[measurement_key]) > float(STORAGE_POLICY[policy_key])
    )


def _choose_layout(
    records: Sequence[Mapping[str, Any]],
    force_layout: str = "auto",
    *,
    measurements: Mapping[str, Any] | None = None,
) -> str:
    if force_layout not in {"auto", "single", "sharded"}:
        raise ValueError(f"INVALID_LAYOUT_REQUEST: {force_layout}")
    if force_layout != "auto":
        return force_layout
    measured = measurements or _measure_storage_policy(records, validation_ms=0.0)
    return "sharded" if _storage_policy_reasons(measured) else "single"


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.in-process-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_registry_directory(staged: Path, target: Path) -> None:
    """Swap one validated physical layout as a directory transaction."""

    parent = target.parent.resolve()
    resolved_target = target.resolve()
    if resolved_target.parent != parent or resolved_target == parent:
        raise ValueError(f"UNSAFE_REGISTRY_PUBLICATION_TARGET: {target}")
    backup = parent / f".{target.name}.previous"
    if backup.exists():
        raise ValueError(f"STALE_REGISTRY_PUBLICATION_BACKUP: {backup}")
    if not target.exists():
        os.replace(staged, target)
        return
    os.replace(target, backup)
    try:
        os.replace(staged, target)
    except BaseException:
        os.replace(backup, target)
        raise
    if backup.resolve().parent != parent:
        raise ValueError(f"UNSAFE_REGISTRY_BACKUP_PATH: {backup}")
    shutil.rmtree(backup)


def _write_registry_layout(
    records: Iterable[Mapping[str, Any]],
    out_dir: str | Path,
    *,
    force_layout: str = "auto",
    _transactional: bool = True,
    _storage_measurements: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and atomically publish one active logical registry layout."""

    directory = Path(out_dir)
    sorted_records = sorted((dict(record) for record in records), key=_record_key)
    validation_started = time.perf_counter()
    keys: set[tuple[str, str]] = set()
    for record in sorted_records:
        _validate_record_shape(record)
        key = _record_key(record)
        if key in keys:
            raise ValueError(f"DUPLICATE_RECORD_KEY: {key[0]}@{key[1]}")
        keys.add(key)
    _validate_requirement_graph(sorted_records)
    validation_ms = (time.perf_counter() - validation_started) * 1_000
    storage_measurements = dict(
        _storage_measurements
        or _measure_storage_policy(sorted_records, validation_ms=validation_ms)
    )
    if _transactional:
        directory.parent.mkdir(parents=True, exist_ok=True)
        lock_path = directory.parent / f".{directory.name}.writer.lock"
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ValueError(f"CONCURRENT_REGISTRY_WRITER: {lock_path}") from exc
        os.close(lock_fd)
        staged = Path(
            tempfile.mkdtemp(
                prefix=f".{directory.name}.layout-stage-",
                dir=str(directory.parent),
            )
        )
        staged.rmdir()
        try:
            metadata = _write_registry_layout(
                sorted_records,
                staged,
                force_layout=force_layout,
                _transactional=False,
                _storage_measurements=storage_measurements,
            )
            loaded, _ = _load_logical_registry(staged)
            if [_stable_json(row) for row in sorted(loaded, key=_record_key)] != [
                _stable_json(row) for row in sorted_records
            ]:
                raise ValueError("STAGED_REGISTRY_SEMANTIC_MISMATCH")
            _publish_registry_directory(staged, directory)
            return metadata
        finally:
            if staged.exists():
                shutil.rmtree(staged)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass

    layout = _choose_layout(
        sorted_records,
        force_layout,
        measurements=storage_measurements,
    )
    directory.mkdir(parents=True, exist_ok=True)
    serialized_bytes = int(storage_measurements["serialized_bytes"])
    policy_reasons = list(_storage_policy_reasons(storage_measurements))
    reported_policy_reasons = (
        [f"FORCED_{force_layout.upper()}", *policy_reasons]
        if force_layout != "auto"
        else policy_reasons or ["WITHIN_CONTROL_STORAGE_POLICY"]
    )
    if layout == "single":
        payload = "".join(f"{_stable_json(record)}\n" for record in sorted_records)
        _write_text_atomic(directory / REGISTRY_FILE, payload)
        manifest = directory / REGISTRY_MANIFEST
        if manifest.exists():
            manifest.unlink()
        for shard in directory.glob(SHARD_GLOB):
            shard.unlink()
        return {
            "layout": "SINGLE_JSONL",
            "row_count": len(sorted_records),
            "serialized_bytes": serialized_bytes,
            "shard_count": 0,
            "files": [REGISTRY_FILE],
            "storage_policy": dict(STORAGE_POLICY),
            "storage_measurements": storage_measurements,
            "storage_policy_reasons": reported_policy_reasons,
        }

    partitions = _registry_partitions(sorted_records)
    staged_names: set[str] = set()
    partition_rows: list[dict[str, Any]] = []
    for partition in partitions:
        file_name = partition.file_name
        staged_names.add(file_name)
        payload = "".join(f"{_stable_json(record)}\n" for record in partition.records)
        _write_text_atomic(directory / file_name, payload)
        partition_rows.append(partition.manifest_row())
    manifest_payload = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "layout": "DETERMINISTIC_SHARDED_JSONL",
        "partition_policy": {
            "kind": "STABLE_CANONICAL_ID_PREFIX_AND_RANGE",
            "rp5c_rows_per_partition": STORAGE_POLICY["rp5c_rows_per_stable_partition"],
        },
        "row_count": len(sorted_records),
        "partitions": partition_rows,
    }
    _write_text_atomic(directory / REGISTRY_MANIFEST, f"{_stable_json(manifest_payload)}\n")
    registry_file = directory / REGISTRY_FILE
    if registry_file.exists():
        registry_file.unlink()
    for existing in directory.glob(SHARD_GLOB):
        if existing.name not in staged_names:
            existing.unlink()
    return {
        "layout": "DETERMINISTIC_SHARDED_JSONL",
        "row_count": len(sorted_records),
        "serialized_bytes": serialized_bytes,
        "shard_count": len(partition_rows),
        "files": [REGISTRY_MANIFEST, *[row["file"] for row in partition_rows]],
        "storage_policy": dict(STORAGE_POLICY),
        "storage_measurements": storage_measurements,
        "storage_policy_reasons": reported_policy_reasons,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"INVALID_REGISTRY_ROW: {path}:{line_number}")
            rows.append(value)
    return rows


def _load_logical_registry(registry_root: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read one active physical layout exactly once."""

    root = Path(registry_root)
    if root.is_file():
        if root.name == REGISTRY_FILE:
            if (root.parent / REGISTRY_MANIFEST).exists() or any(
                root.parent.glob(SHARD_GLOB)
            ):
                raise ValueError("TWO_ACTIVE_REGISTRY_LAYOUTS")
            rows = _read_jsonl(root)
            return rows, {"layout": "SINGLE_JSONL", "files_read": 1, "shard_count": 0}
        if root.name == REGISTRY_MANIFEST:
            root = root.parent
        else:
            raise ValueError(f"UNSUPPORTED_REGISTRY_PATH: {root}")
    registry_file = root / REGISTRY_FILE
    manifest_file = root / REGISTRY_MANIFEST
    if registry_file.exists() and manifest_file.exists():
        raise ValueError("TWO_ACTIVE_REGISTRY_LAYOUTS")
    if registry_file.exists():
        if any(root.glob(SHARD_GLOB)):
            raise ValueError("TWO_ACTIVE_REGISTRY_LAYOUTS")
        rows = _read_jsonl(registry_file)
        return rows, {"layout": "SINGLE_JSONL", "files_read": 1, "shard_count": 0}
    if not manifest_file.exists():
        raise FileNotFoundError(f"NO_ACTIVE_REGISTRY_LAYOUT: {root}")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping):
        raise ValueError("INVALID_REGISTRY_MANIFEST")
    expected_manifest_fields = {
        "registry_schema_version",
        "layout",
        "partition_policy",
        "row_count",
        "partitions",
    }
    if set(manifest) != expected_manifest_fields:
        raise ValueError("INVALID_REGISTRY_MANIFEST_FIELDS")
    if manifest.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise ValueError(
            f"INCOMPATIBLE_REGISTRY_SCHEMA: {manifest.get('registry_schema_version')} != {REGISTRY_SCHEMA_VERSION}"
        )
    if manifest.get("layout") != "DETERMINISTIC_SHARDED_JSONL":
        raise ValueError("INVALID_REGISTRY_MANIFEST_LAYOUT")
    expected_partition_policy = {
        "kind": "STABLE_CANONICAL_ID_PREFIX_AND_RANGE",
        "rp5c_rows_per_partition": STORAGE_POLICY["rp5c_rows_per_stable_partition"],
    }
    if manifest.get("partition_policy") != expected_partition_policy:
        raise ValueError("INVALID_REGISTRY_MANIFEST_PARTITION_POLICY")
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("EMPTY_REGISTRY_MANIFEST")
    expected_partition_fields = {"file", "range_start", "range_end", "row_count"}
    for partition in partitions:
        if not isinstance(partition, Mapping) or set(partition) != expected_partition_fields:
            raise ValueError("INVALID_REGISTRY_MANIFEST_PARTITION_FIELDS")
        row_count = partition.get("row_count")
        if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 1:
            raise ValueError("INVALID_REGISTRY_MANIFEST_PARTITION_COUNT")
    expected_files = [str(item["file"]) for item in partitions]
    if len(expected_files) != len(set(expected_files)):
        raise ValueError("DUPLICATE_REGISTRY_MANIFEST_SHARD")
    if expected_files != sorted(expected_files):
        raise ValueError("NONDETERMINISTIC_REGISTRY_MANIFEST_PARTITION_ORDER")
    actual_files = sorted(path.name for path in root.glob(SHARD_GLOB))
    if expected_files != actual_files:
        raise ValueError("REGISTRY_MANIFEST_SHARD_SET_MISMATCH")
    rows: list[dict[str, Any]] = []
    rows_by_file: dict[str, list[dict[str, Any]]] = {}
    record_keys: set[tuple[str, str]] = set()
    for partition in partitions:
        file_name = str(partition["file"])
        if Path(file_name).name != file_name or not re.fullmatch(r"registry\.part-[a-z0-9-]+\.jsonl", file_name):
            raise ValueError(f"UNSAFE_REGISTRY_SHARD_PATH: {file_name}")
        shard_rows = _read_jsonl(root / file_name)
        if len(shard_rows) != int(partition["row_count"]):
            raise ValueError(f"REGISTRY_SHARD_COUNT_MISMATCH: {file_name}")
        if shard_rows != sorted(shard_rows, key=_record_key):
            raise ValueError(f"NONDETERMINISTIC_REGISTRY_SHARD_ROW_ORDER: {file_name}")
        for record in shard_rows:
            key = _record_key(record)
            if key in record_keys:
                raise ValueError(f"DUPLICATE_RECORD_KEY: {key[0]}@{key[1]}")
            record_keys.add(key)
        rows.extend(shard_rows)
        rows_by_file[file_name] = shard_rows
    manifest_row_count = manifest.get("row_count")
    if isinstance(manifest_row_count, bool) or not isinstance(manifest_row_count, int):
        raise ValueError("INVALID_REGISTRY_MANIFEST_TOTAL_COUNT")
    if len(rows) != manifest_row_count:
        raise ValueError("REGISTRY_MANIFEST_TOTAL_COUNT_MISMATCH")

    # Reconstruct the complete deterministic partition set from logical truth.
    # This single comparison checks every non-RP5C range label, overflow range,
    # filename, row count, and manifest position rather than trusting metadata.
    expected_partitions = _registry_partitions(rows)
    reconstructed_manifest_rows = [partition.manifest_row() for partition in expected_partitions]
    if partitions != reconstructed_manifest_rows:
        raise ValueError("REGISTRY_MANIFEST_PARTITION_DERIVATION_MISMATCH")
    for expected_partition in expected_partitions:
        actual_rows = rows_by_file.get(expected_partition.file_name, [])
        if actual_rows != list(expected_partition.records):
            raise ValueError(
                f"REGISTRY_SHARD_PARTITION_MISMATCH: {expected_partition.file_name}"
            )
    return rows, {
        "layout": "DETERMINISTIC_SHARDED_JSONL",
        "files_read": 1 + len(partitions),
        "shard_count": len(partitions),
    }


def _validate_requirement_graph(records: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    record_map = {_record_key(record): record for record in records}
    current: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key, record in record_map.items():
        if record.get("record_state") in ACTIVE_RECORD_STATES:
            current[key[0]].append(key)
    graph: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for key, record in record_map.items():
        for requirement in record["definition"].get("requirements", []):
            target_id = str(requirement["required_component_id_or_source_selector"])
            constraint = str(requirement["required_semantic_version_constraint"])
            candidates = current.get(target_id, [])
            if constraint not in {"*", "ANY"}:
                normalized = constraint.removeprefix("==")
                candidates = [candidate for candidate in candidates if candidate[1] == normalized]
            fallback_id = requirement.get("fallback_component_id_or_null")
            fallback_candidates = (
                current.get(str(fallback_id), []) if fallback_id else []
            )
            if fallback_id and len(fallback_candidates) != 1:
                raise ValueError(
                    f"UNRESOLVED_OR_AMBIGUOUS_FALLBACK: {key[0]} -> {fallback_id}"
                )
            if not candidates:
                if fallback_candidates:
                    graph[key].add(fallback_candidates[0])
                    _validate_requirement_ports(
                        record,
                        record_map[fallback_candidates[0]],
                        requirement,
                    )
                    continue
                if requirement.get("required_or_optional") == "REQUIRED":
                    raise ValueError(f"UNRESOLVED_REQUIRED_REQUIREMENT: {key[0]} -> {target_id}@{constraint}")
                continue
            if len(candidates) != 1:
                raise ValueError(f"AMBIGUOUS_REQUIREMENT_VERSION: {key[0]} -> {target_id}@{constraint}")
            graph[key].add(candidates[0])
            _validate_requirement_ports(record, record_map[candidates[0]], requirement)
            if fallback_candidates:
                graph[key].add(fallback_candidates[0])
                _validate_requirement_ports(
                    record,
                    record_map[fallback_candidates[0]],
                    requirement,
                )
        for binding in record.get("bindings", ()):
            policy = binding.get("fallback_policy", {})
            behavior = str(policy.get("behavior", policy.get("state", "FAIL_CLOSED")))
            if not behavior.startswith("USE_FALLBACK"):
                continue
            fallback_id = str(
                policy.get("fallback_component_id", policy.get("component_id", ""))
            )
            fallback_candidates = current.get(fallback_id, ())
            if len(fallback_candidates) != 1:
                raise ValueError(
                    f"UNRESOLVED_OR_AMBIGUOUS_BINDING_FALLBACK: {key[0]} -> {fallback_id}"
                )
            fallback_key = fallback_candidates[0]
            source_outputs = _schema_map(record["definition"].get("output_schema", ()))
            fallback_outputs = _schema_map(
                record_map[fallback_key]["definition"].get("output_schema", ())
            )
            if set(source_outputs) != set(fallback_outputs) or any(
                _schema_unit(source_outputs[name]) != _schema_unit(fallback_outputs[name])
                for name in source_outputs
            ):
                raise ValueError(
                    f"BINDING_FALLBACK_OUTPUT_CONTRACT_MISMATCH: {key[0]} -> {fallback_id}"
                )
            graph[key].add(fallback_key)
    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()
    order: list[tuple[str, str]] = []

    def visit(node: tuple[str, str]) -> None:
        if node in visiting:
            raise ValueError(f"REQUIREMENT_CYCLE: {node[0]}@{node[1]}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in sorted(graph.get(node, ())):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)
        order.append(node)

    for node in sorted(record_map):
        visit(node)
    return tuple(f"{component_id}@{version}" for component_id, version in order)


def _decimal(value: Any, *, name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ComputationControlError("BINARY_FLOAT_MONEY_BOUNDARY", f"{name} must use Decimal, int, or decimal text")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ComputationControlError("INVALID_DECIMAL", name) from exc
    if not result.is_finite():
        raise ComputationControlError("NONFINITE_INPUT", name)
    return result


def _native_decimal_implied_probability(inputs: dict[str, Any]) -> dict[str, Any]:
    price = _decimal(inputs["price"], name="price")
    payout = _decimal(inputs["payout"], name="payout")
    if payout <= 0:
        raise ComputationControlError("INVALID_DOMAIN", "payout must be positive")
    value = price / payout
    if value < 0 or value > 1:
        raise ComputationControlError("INVALID_DOMAIN", "implied probability must be in [0, 1]")
    return {"implied_probability": value}


def _native_decimal_probability_edge(inputs: dict[str, Any]) -> dict[str, Any]:
    model = _decimal(inputs["p_model"], name="p_model")
    implied = _decimal(inputs["implied_probability"], name="implied_probability")
    if not (Decimal("0") <= model <= Decimal("1")):
        raise ComputationControlError("INVALID_DOMAIN", "p_model must be in [0, 1]")
    return {"probability_edge": model - implied}


def _native_decimal_mid_price(inputs: dict[str, Any]) -> dict[str, Any]:
    bid = _decimal(inputs["best_bid"], name="best_bid")
    ask = _decimal(inputs["best_ask"], name="best_ask")
    if bid < 0 or ask < bid:
        raise ComputationControlError("INVALID_DOMAIN", "require 0 <= best_bid <= best_ask")
    return {"mid_price": (bid + ask) / Decimal("2")}


def _native_decimal_spread(inputs: dict[str, Any]) -> dict[str, Any]:
    bid = _decimal(inputs["best_bid"], name="best_bid")
    ask = _decimal(inputs["best_ask"], name="best_ask")
    if bid < 0 or ask < bid:
        raise ComputationControlError("INVALID_DOMAIN", "require 0 <= best_bid <= best_ask")
    return {"spread": ask - bid}


def _native_decimal_relative_spread(inputs: dict[str, Any]) -> dict[str, Any]:
    spread = _decimal(inputs["spread"], name="spread")
    mid = _decimal(inputs["mid_price"], name="mid_price")
    if spread < 0 or mid <= 0:
        raise ComputationControlError("INVALID_DOMAIN", "require nonnegative spread and positive mid price")
    return {"relative_spread": spread / mid}


def _native_stack_identity(inputs: dict[str, Any]) -> dict[str, Any]:
    output_name = str(inputs.get("stack_output_name", "result"))
    if output_name not in inputs:
        raise ComputationControlError("MISSING_STACK_OUTPUT", output_name)
    return {output_name: inputs[output_name]}


NATIVE_IMPLEMENTATIONS: Mapping[str, Callable[[dict[str, Any]], dict[str, Any]]] = MappingProxyType(
    {
        "qtt.computation_control.native:decimal_implied_probability": _native_decimal_implied_probability,
        "qtt.computation_control.native:decimal_probability_edge": _native_decimal_probability_edge,
        "qtt.computation_control.native:decimal_mid_price": _native_decimal_mid_price,
        "qtt.computation_control.native:decimal_spread": _native_decimal_spread,
        "qtt.computation_control.native:decimal_relative_spread": _native_decimal_relative_spread,
        "qtt.computation_control.native:stack_identity": _native_stack_identity,
    }
)


def _default_implementation_allowlist() -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
    allowlist = dict(NATIVE_IMPLEMENTATIONS)
    try:
        from qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library import algorithm_specs
        from qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import formula_specs
        from qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library import quantum_specs
    except ImportError:
        try:
            # Repository tools execute from the checkout root and therefore use
            # the fixed ``src.qtt`` package path.  This is still a statically
            # enumerated allowlist; no caller-selected module is imported.
            from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library import (  # noqa: E501
                algorithm_specs,
            )
            from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (  # noqa: E501
                formula_specs,
            )
            from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.quantum_seed_library import (  # noqa: E501
                quantum_specs,
            )
        except ImportError:
            # A small synthetic registry can still use injected/native callables.
            return allowlist

    specs = [*formula_specs(), *algorithm_specs(), *quantum_specs()]
    for spec in specs:
        ref = str(spec.callable_ref)
        callable_value = (
            getattr(spec, "compute", None)
            or getattr(spec, "implementation", None)
            or getattr(spec, "build_shape", None)
        )
        if callable(callable_value):
            allowlist[ref] = callable_value
            if ref.startswith("src."):
                allowlist[ref.removeprefix("src.")] = callable_value
            else:
                allowlist[f"src.{ref}"] = callable_value
    return allowlist


@dataclass(frozen=True)
class _RegistryIndexes:
    records_by_key: Mapping[tuple[str, str], Mapping[str, Any]]
    record_keys_by_id: Mapping[str, tuple[tuple[str, str], ...]]
    direct_aliases: Mapping[str, tuple[str, str]]
    qku_roots: Mapping[str, tuple[tuple[str, str], ...]]
    qku_context_roots: Mapping[tuple[str, str, str], tuple[tuple[str, str], ...]]
    decision_role_candidates: Mapping[str, tuple[tuple[str, str], ...]]
    family_candidates: Mapping[str, tuple[tuple[str, str], ...]]
    bindings_by_record: Mapping[tuple[str, str], tuple[Mapping[str, Any], ...]]
    context_binding_candidates: Mapping[tuple[str, str, str], tuple[tuple[tuple[str, str], str], ...]]
    requirements_by_record: Mapping[tuple[str, str], tuple[Mapping[str, Any], ...]]
    reverse_requirements: Mapping[str, tuple[str, ...]]
    implementation_records: Mapping[str, tuple[tuple[str, str], ...]]
    agent_policy_records: Mapping[str, tuple[tuple[str, str], ...]]


@dataclass(frozen=True)
class _RegistrySnapshot:
    generation: int
    records: tuple[Mapping[str, Any], ...]
    indexes: _RegistryIndexes
    layout: str
    shard_count: int
    registry_file_reads: int
    built_at_monotonic: float


def _freeze_tuple_mapping(mapping: Mapping[Any, Iterable[Any]]) -> Mapping[Any, tuple[Any, ...]]:
    return MappingProxyType(
        {
            key: tuple(sorted(set(values), key=repr))
            for key, values in sorted(mapping.items(), key=lambda pair: repr(pair[0]))
        }
    )


def _relation_type(relation: Mapping[str, Any]) -> str:
    return str(relation.get("relation_type", relation.get("type", relation.get("relation", ""))))


def _build_indexes(records: Iterable[Mapping[str, Any]]) -> _RegistryIndexes:
    """Build disposable indexes from logical registry truth."""

    records_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    keys_by_id: dict[str, list[tuple[str, str]]] = defaultdict(list)
    aliases: dict[str, tuple[str, str]] = {}
    qku_roots: dict[str, list[tuple[str, str]]] = defaultdict(list)
    qku_context_roots: dict[tuple[str, str, str], list[tuple[str, str]]] = defaultdict(list)
    roles: dict[str, list[tuple[str, str]]] = defaultdict(list)
    families: dict[str, list[tuple[str, str]]] = defaultdict(list)
    bindings: dict[tuple[str, str], tuple[Mapping[str, Any], ...]] = {}
    context_bindings: dict[tuple[str, str, str], list[tuple[tuple[str, str], str]]] = defaultdict(list)
    requirements: dict[tuple[str, str], tuple[Mapping[str, Any], ...]] = {}
    reverse_requirements: dict[str, set[str]] = defaultdict(set)
    implementations: dict[str, list[tuple[str, str]]] = defaultdict(list)
    agent_policies: dict[str, list[tuple[str, str]]] = defaultdict(list)
    alias_sources: dict[str, tuple[str, str]] = {}

    for raw_record in sorted(records, key=_record_key):
        _validate_record_shape(raw_record)
        record = _freeze(raw_record)
        key = _record_key(record)
        if key in records_by_key:
            raise ValueError(f"DUPLICATE_RECORD_KEY: {key[0]}@{key[1]}")
        records_by_key[key] = record
        keys_by_id[key[0]].append(key)
        uses = record["uses"]
        for role in uses.get("decision_roles", ()):
            roles[str(role)].append(key)
        family_ref = record["definition"].get("family_template_ref_or_null")
        if family_ref:
            families[str(family_ref)].append(key)
        for family_tag in uses.get("market_family_tags", ()):
            families[f"MARKET::{family_tag}"].append(key)
        for relation in record.get("relations", ()):
            if not isinstance(relation, Mapping) or _relation_type(relation) != "ALIAS_OF":
                continue
            alias = relation.get("alias") or relation.get("source_identity_or_alias") or relation.get("source_local_identity_or_name")
            target = str(relation.get("canonical_target_ref", key[0])).split("@", 1)[0]
            target_version = str(relation.get("canonical_target_version", key[1]))
            if not alias:
                raise ValueError(f"ALIAS_WITHOUT_DIRECT_NAME: {key[0]}")
            alias_text = str(alias)
            target_key = (target, target_version)
            prior = aliases.get(alias_text)
            if prior is not None and prior != target_key:
                raise ValueError(f"AMBIGUOUS_DIRECT_ALIAS: {alias_text}")
            aliases[alias_text] = target_key
            alias_sources[alias_text] = key
        runtime_qku_bindings = (
            uses.get("qku_role_bindings", ())
            if record.get("record_state") in ACTIVE_RECORD_STATES
            else ()
        )
        for qku_binding in runtime_qku_bindings:
            if not isinstance(qku_binding, Mapping):
                continue
            qku_id = str(qku_binding.get("qku_id", ""))
            if not qku_id:
                continue
            root_id = str(qku_binding.get("stack_root_or_direct_component") or key[0])
            root_keys = keys_by_id.get(root_id)
            # Forward references are resolved after all records have been read.
            root_key = (root_id, str(qku_binding.get("semantic_version", key[1])))
            qku_roots[qku_id].append(root_key)
            qku_context_roots[
                (
                    qku_id,
                    str(qku_binding.get("role_or_decision_stage", "ANY")),
                    str(qku_binding.get("market_family", "ANY")),
                )
            ].append(root_key)
        record_bindings = tuple(record.get("bindings", ()))
        bindings[key] = record_bindings
        for binding in record_bindings:
            market = str(binding.get("market", "ANY"))
            venue = str(binding.get("venue", "ANY"))
            for mode in binding.get("supported_modes", ()):
                context_bindings[(market, venue, str(mode))].append((key, str(binding["binding_id"])))
            policy = binding.get("agent_access_policy", {})
            if isinstance(policy, Mapping):
                for agent_id in policy:
                    agent_policies[str(agent_id)].append(key)
        record_requirements = tuple(record["definition"].get("requirements", ()))
        requirements[key] = record_requirements
        for requirement in record_requirements:
            reverse_requirements[
                str(requirement["required_component_id_or_source_selector"])
            ].add(key[0])
            fallback_target = requirement.get("fallback_component_id_or_null")
            if fallback_target:
                reverse_requirements[str(fallback_target)].add(key[0])
        for binding in record_bindings:
            fallback_policy = binding.get("fallback_policy", {})
            fallback_behavior = str(
                fallback_policy.get(
                    "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                )
            )
            fallback_target = fallback_policy.get(
                "fallback_component_id", fallback_policy.get("component_id")
            )
            if fallback_behavior.startswith("USE_FALLBACK") and fallback_target:
                reverse_requirements[str(fallback_target)].add(key[0])
        for implementation in record["definition"].get("implementation_versions", ()):
            implementations[str(implementation["callable_or_solver_ref"])].append(key)

    # Resolve QKU forward references and reject missing/ambiguous active roots.
    def resolved_qku_root(qku_id: str, root_key: tuple[str, str]) -> tuple[str, str]:
        if root_key in records_by_key:
            return root_key
        candidates = keys_by_id.get(root_key[0], ())
        if len(candidates) != 1:
            raise ValueError(
                f"UNRESOLVED_QKU_ROOT: {qku_id}: {root_key[0]}@{root_key[1]}"
            )
        return candidates[0]

    for qku_id, root_keys in tuple(qku_roots.items()):
        qku_roots[qku_id] = [resolved_qku_root(qku_id, key) for key in root_keys]
    for qku_context, root_keys in tuple(qku_context_roots.items()):
        qku_context_roots[qku_context] = [
            resolved_qku_root(qku_context[0], key) for key in root_keys
        ]

    for alias, target_key in aliases.items():
        target = records_by_key.get(target_key)
        if target is None:
            raise ValueError(
                f"UNRESOLVED_DIRECT_ALIAS_TARGET: {alias} -> {target_key[0]}@{target_key[1]}"
            )
        if target.get("record_state") != "CANONICAL_ACCEPTED":
            raise ValueError(
                f"ALIAS_TARGET_NOT_CANONICAL_ACCEPTED: {alias} -> {target_key[0]}@{target_key[1]}"
            )
        if alias_sources[alias] != target_key:
            raise ValueError(
                f"ALIAS_RELATION_NOT_ATTACHED_TO_CANONICAL_TARGET: {alias}"
            )
        if alias in keys_by_id:
            raise ValueError(f"ALIAS_COLLIDES_WITH_CANONICAL_ID: {alias}")

    for qku_context, root_keys in qku_context_roots.items():
        unique_roots = tuple(sorted(set(root_keys)))
        if len(unique_roots) != 1:
            raise ValueError(
                "AMBIGUOUS_ACTIVE_QKU_CONTEXT: "
                f"{qku_context[0]}::{qku_context[1]}::{qku_context[2]} -> {unique_roots}"
            )
        root = records_by_key.get(unique_roots[0])
        if root is None or root.get("record_state") not in ACTIVE_RECORD_STATES:
            raise ValueError(
                f"QKU_ROOT_NOT_ACTIVE: {qku_context[0]} -> {unique_roots[0]}"
            )

    return _RegistryIndexes(
        records_by_key=MappingProxyType(records_by_key),
        record_keys_by_id=_freeze_tuple_mapping(keys_by_id),
        direct_aliases=MappingProxyType(dict(sorted(aliases.items()))),
        qku_roots=_freeze_tuple_mapping(qku_roots),
        qku_context_roots=_freeze_tuple_mapping(qku_context_roots),
        decision_role_candidates=_freeze_tuple_mapping(roles),
        family_candidates=_freeze_tuple_mapping(families),
        bindings_by_record=MappingProxyType(dict(sorted(bindings.items(), key=lambda pair: pair[0]))),
        context_binding_candidates=_freeze_tuple_mapping(context_bindings),
        requirements_by_record=MappingProxyType(dict(sorted(requirements.items(), key=lambda pair: pair[0]))),
        reverse_requirements=MappingProxyType(
            {key: tuple(sorted(value)) for key, value in sorted(reverse_requirements.items())}
        ),
        implementation_records=_freeze_tuple_mapping(implementations),
        agent_policy_records=_freeze_tuple_mapping(agent_policies),
    )


def _build_snapshot(
    records: Iterable[Mapping[str, Any]],
    *,
    generation: int,
    layout: str = "IN_MEMORY",
    shard_count: int = 0,
    registry_file_reads: int = 0,
) -> _RegistrySnapshot:
    sorted_records = tuple(_freeze(record) for record in sorted(records, key=_record_key))
    _validate_requirement_graph(sorted_records)
    indexes = _build_indexes(sorted_records)
    return _RegistrySnapshot(
        generation=generation,
        records=sorted_records,
        indexes=indexes,
        layout=layout,
        shard_count=shard_count,
        registry_file_reads=registry_file_reads,
        built_at_monotonic=time.monotonic(),
    )


def _index_signature(indexes: _RegistryIndexes) -> Any:
    return _canonical_value(
        {
            "record_keys": sorted(f"{key[0]}@{key[1]}" for key in indexes.records_by_key),
            "by_id": indexes.record_keys_by_id,
            "aliases": indexes.direct_aliases,
            "qku": indexes.qku_roots,
            "qku_context": indexes.qku_context_roots,
            "roles": indexes.decision_role_candidates,
            "families": indexes.family_candidates,
            "bindings": {
                f"{key[0]}@{key[1]}": [binding["binding_id"] for binding in value]
                for key, value in indexes.bindings_by_record.items()
            },
            "context_bindings": indexes.context_binding_candidates,
            "requirements": {
                f"{key[0]}@{key[1]}": list(value) for key, value in indexes.requirements_by_record.items()
            },
            "reverse": indexes.reverse_requirements,
            "implementations": indexes.implementation_records,
            "agents": indexes.agent_policy_records,
        }
    )


def _refresh_indexes_incrementally(
    base: _RegistryIndexes,
    candidate_records: Sequence[Mapping[str, Any]],
    affected_component_ids: set[str],
) -> _RegistryIndexes:
    """Replace only affected record contributions in disposable indexes."""

    records_by_key = dict(base.records_by_key)
    keys_by_id = {key: list(value) for key, value in base.record_keys_by_id.items()}
    aliases = dict(base.direct_aliases)
    qku_roots = {key: list(value) for key, value in base.qku_roots.items()}
    qku_context_roots = {
        key: list(value) for key, value in base.qku_context_roots.items()
    }
    roles = {
        key: list(value) for key, value in base.decision_role_candidates.items()
    }
    families = {key: list(value) for key, value in base.family_candidates.items()}
    bindings = dict(base.bindings_by_record)
    context_bindings = {
        key: list(value) for key, value in base.context_binding_candidates.items()
    }
    requirements = dict(base.requirements_by_record)
    reverse_requirements = {
        key: set(value) for key, value in base.reverse_requirements.items()
    }
    implementations = {
        key: list(value) for key, value in base.implementation_records.items()
    }
    agent_policies = {
        key: list(value) for key, value in base.agent_policy_records.items()
    }

    def discard(mapping: dict[Any, list[Any]], key: Any, value: Any) -> None:
        values = mapping.get(key)
        if values is None:
            return
        mapping[key] = [item for item in values if item != value]
        if not mapping[key]:
            mapping.pop(key, None)

    def resolved_root(
        record: Mapping[str, Any], qku_binding: Mapping[str, Any]
    ) -> tuple[str, str]:
        root_id = str(
            qku_binding.get("stack_root_or_direct_component")
            or record["canonical_component_id"]
        )
        requested = (
            root_id,
            str(qku_binding.get("semantic_version", record["semantic_version"])),
        )
        if requested in records_by_key:
            return requested
        alternatives = keys_by_id.get(root_id, ())
        if len(alternatives) != 1:
            raise ValueError(
                f"UNRESOLVED_QKU_ROOT: {qku_binding.get('qku_id')}: {requested}"
            )
        return alternatives[0]

    old_records = [
        base.records_by_key[key]
        for component_id in affected_component_ids
        for key in base.record_keys_by_id.get(component_id, ())
    ]

    # Remove old contributions while their root/version indexes are intact.
    for record in old_records:
        key = _record_key(record)
        uses = record["uses"]
        for role in uses.get("decision_roles", ()):
            discard(roles, str(role), key)
        family_ref = record["definition"].get("family_template_ref_or_null")
        if family_ref:
            discard(families, str(family_ref), key)
        for family_tag in uses.get("market_family_tags", ()):
            discard(families, f"MARKET::{family_tag}", key)
        for relation in record.get("relations", ()):
            if isinstance(relation, Mapping) and _relation_type(relation) == "ALIAS_OF":
                alias = (
                    relation.get("alias")
                    or relation.get("source_identity_or_alias")
                    or relation.get("source_local_identity_or_name")
                )
                if alias:
                    aliases.pop(str(alias), None)
        if record.get("record_state") in ACTIVE_RECORD_STATES:
            for qku_binding in uses.get("qku_role_bindings", ()):
                if not isinstance(qku_binding, Mapping) or not qku_binding.get("qku_id"):
                    continue
                qku_id = str(qku_binding["qku_id"])
                root_key = resolved_root(record, qku_binding)
                discard(qku_roots, qku_id, root_key)
                context_key = (
                    qku_id,
                    str(qku_binding.get("role_or_decision_stage", "ANY")),
                    str(qku_binding.get("market_family", "ANY")),
                )
                discard(qku_context_roots, context_key, root_key)
        for binding in record.get("bindings", ()):
            for mode in binding.get("supported_modes", ()):
                context_key = (
                    str(binding.get("market", "ANY")),
                    str(binding.get("venue", "ANY")),
                    str(mode),
                )
                discard(context_bindings, context_key, (key, str(binding["binding_id"])))
            policy = binding.get("agent_access_policy", {})
            if isinstance(policy, Mapping):
                for agent_id in policy:
                    discard(agent_policies, str(agent_id), key)
        for requirement in record["definition"].get("requirements", ()):
            targets = [str(requirement["required_component_id_or_source_selector"])]
            if requirement.get("fallback_component_id_or_null"):
                targets.append(str(requirement["fallback_component_id_or_null"]))
            for target in targets:
                dependents = reverse_requirements.get(target)
                if dependents is not None:
                    dependents.discard(key[0])
                    if not dependents:
                        reverse_requirements.pop(target, None)
        for binding in record.get("bindings", ()):
            fallback_policy = binding.get("fallback_policy", {})
            fallback_behavior = str(
                fallback_policy.get(
                    "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                )
            )
            fallback_target = fallback_policy.get(
                "fallback_component_id", fallback_policy.get("component_id")
            )
            if fallback_behavior.startswith("USE_FALLBACK") and fallback_target:
                dependents = reverse_requirements.get(str(fallback_target))
                if dependents is not None:
                    dependents.discard(key[0])
                    if not dependents:
                        reverse_requirements.pop(str(fallback_target), None)
        for implementation in record["definition"].get("implementation_versions", ()):
            discard(
                implementations,
                str(implementation["callable_or_solver_ref"]),
                key,
            )
        records_by_key.pop(key, None)
        discard(keys_by_id, key[0], key)
        bindings.pop(key, None)
        requirements.pop(key, None)

    new_records = [
        _freeze(record)
        for record in candidate_records
        if str(record["canonical_component_id"]) in affected_component_ids
    ]
    # Install keys first so affected QKU roots may reference one another.
    for record in new_records:
        key = _record_key(record)
        if key in records_by_key:
            raise ValueError(f"DUPLICATE_RECORD_KEY: {key[0]}@{key[1]}")
        records_by_key[key] = record
        keys_by_id.setdefault(key[0], []).append(key)

    for record in new_records:
        key = _record_key(record)
        uses = record["uses"]
        for role in uses.get("decision_roles", ()):
            roles.setdefault(str(role), []).append(key)
        family_ref = record["definition"].get("family_template_ref_or_null")
        if family_ref:
            families.setdefault(str(family_ref), []).append(key)
        for family_tag in uses.get("market_family_tags", ()):
            families.setdefault(f"MARKET::{family_tag}", []).append(key)
        for relation in record.get("relations", ()):
            if not isinstance(relation, Mapping) or _relation_type(relation) != "ALIAS_OF":
                continue
            alias = (
                relation.get("alias")
                or relation.get("source_identity_or_alias")
                or relation.get("source_local_identity_or_name")
            )
            target = str(relation.get("canonical_target_ref", key[0])).split("@", 1)[0]
            target_key = (
                target,
                str(relation.get("canonical_target_version", key[1])),
            )
            if not alias:
                raise ValueError(f"ALIAS_WITHOUT_DIRECT_NAME: {key[0]}")
            prior = aliases.get(str(alias))
            if prior is not None and prior != target_key:
                raise ValueError(f"AMBIGUOUS_DIRECT_ALIAS: {alias}")
            aliases[str(alias)] = target_key
        if record.get("record_state") in ACTIVE_RECORD_STATES:
            for qku_binding in uses.get("qku_role_bindings", ()):
                if not isinstance(qku_binding, Mapping) or not qku_binding.get("qku_id"):
                    continue
                qku_id = str(qku_binding["qku_id"])
                root_key = resolved_root(record, qku_binding)
                qku_roots.setdefault(qku_id, []).append(root_key)
                qku_context_roots.setdefault(
                    (
                        qku_id,
                        str(qku_binding.get("role_or_decision_stage", "ANY")),
                        str(qku_binding.get("market_family", "ANY")),
                    ),
                    [],
                ).append(root_key)
        record_bindings = tuple(record.get("bindings", ()))
        bindings[key] = record_bindings
        for binding in record_bindings:
            for mode in binding.get("supported_modes", ()):
                context_bindings.setdefault(
                    (
                        str(binding.get("market", "ANY")),
                        str(binding.get("venue", "ANY")),
                        str(mode),
                    ),
                    [],
                ).append((key, str(binding["binding_id"])))
            policy = binding.get("agent_access_policy", {})
            if isinstance(policy, Mapping):
                for agent_id in policy:
                    agent_policies.setdefault(str(agent_id), []).append(key)
        record_requirements = tuple(record["definition"].get("requirements", ()))
        requirements[key] = record_requirements
        for requirement in record_requirements:
            reverse_requirements.setdefault(
                str(requirement["required_component_id_or_source_selector"]), set()
            ).add(key[0])
            fallback_target = requirement.get("fallback_component_id_or_null")
            if fallback_target:
                reverse_requirements.setdefault(str(fallback_target), set()).add(
                    key[0]
                )
        for binding in record_bindings:
            fallback_policy = binding.get("fallback_policy", {})
            fallback_behavior = str(
                fallback_policy.get(
                    "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                )
            )
            fallback_target = fallback_policy.get(
                "fallback_component_id", fallback_policy.get("component_id")
            )
            if fallback_behavior.startswith("USE_FALLBACK") and fallback_target:
                reverse_requirements.setdefault(str(fallback_target), set()).add(
                    key[0]
                )
        for implementation in record["definition"].get("implementation_versions", ()):
            implementations.setdefault(
                str(implementation["callable_or_solver_ref"]), []
            ).append(key)

    return _RegistryIndexes(
        records_by_key=MappingProxyType(dict(sorted(records_by_key.items()))),
        record_keys_by_id=_freeze_tuple_mapping(keys_by_id),
        direct_aliases=MappingProxyType(dict(sorted(aliases.items()))),
        qku_roots=_freeze_tuple_mapping(qku_roots),
        qku_context_roots=_freeze_tuple_mapping(qku_context_roots),
        decision_role_candidates=_freeze_tuple_mapping(roles),
        family_candidates=_freeze_tuple_mapping(families),
        bindings_by_record=MappingProxyType(dict(sorted(bindings.items()))),
        context_binding_candidates=_freeze_tuple_mapping(context_bindings),
        requirements_by_record=MappingProxyType(dict(sorted(requirements.items()))),
        reverse_requirements=MappingProxyType(
            {
                key: tuple(sorted(value))
                for key, value in sorted(reverse_requirements.items())
            }
        ),
        implementation_records=_freeze_tuple_mapping(implementations),
        agent_policy_records=_freeze_tuple_mapping(agent_policies),
    )


def _record_map_by_component(records: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        result[str(record["canonical_component_id"])].append(record)
    for values in result.values():
        values.sort(key=lambda record: str(record["semantic_version"]))
    return result


def _binding_map(records: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in records:
        component_id = str(record["canonical_component_id"])
        for binding in record.get("bindings", ()):
            key = _binding_key(component_id, binding)
            if key in result:
                raise ValueError(f"DUPLICATE_LOGICAL_BINDING_ID: {key[0]}::{key[1]}")
            result[key] = binding
    return result


def _binding_is_selectable(binding: Mapping[str, Any]) -> bool:
    return not binding.get("terminal_disposition_or_null") and str(
        binding.get("activation_state", "")
    ) not in {"RETIRED", "REMOVED", "SUPERSEDED"}


def _derive_registry_update(
    base_records: Iterable[Mapping[str, Any]],
    candidate_records: Iterable[Mapping[str, Any]],
    *,
    batch_id: str = "IN_PROCESS_UPDATE",
) -> RegistryUpdateV1:
    """Derive an exact transient delta from two logical registry states."""

    base_list = list(base_records)
    candidate_list = list(candidate_records)
    base_by_id = _record_map_by_component(base_list)
    candidate_by_id = _record_map_by_component(candidate_list)
    base_ids = set(base_by_id)
    candidate_ids = set(candidate_by_id)
    added = candidate_ids - base_ids
    retired = base_ids - candidate_ids
    changed: set[str] = set()
    for component_id in base_ids & candidate_ids:
        if _canonical_value(base_by_id[component_id]) != _canonical_value(candidate_by_id[component_id]):
            changed.add(component_id)
        base_active = any(record.get("record_state") in ACTIVE_RECORD_STATES for record in base_by_id[component_id])
        candidate_active = any(record.get("record_state") in ACTIVE_RECORD_STATES for record in candidate_by_id[component_id])
        if base_active and not candidate_active:
            retired.add(component_id)

    base_bindings = _binding_map(base_list)
    candidate_bindings = _binding_map(candidate_list)
    base_selectable = {
        key for key, binding in base_bindings.items() if _binding_is_selectable(binding)
    }
    candidate_selectable = {
        key
        for key, binding in candidate_bindings.items()
        if _binding_is_selectable(binding)
    }
    added_binding_keys = candidate_selectable - base_selectable
    removed_binding_keys = base_selectable - candidate_selectable
    changed_binding_keys = {
        key
        for key in set(base_bindings) & set(candidate_bindings)
        if _canonical_value(base_bindings[key]) != _canonical_value(candidate_bindings[key])
    }
    directly_affected = added | changed | retired | {component_id for component_id, _ in added_binding_keys | removed_binding_keys | changed_binding_keys}

    reverse: dict[str, set[str]] = defaultdict(set)
    for record in candidate_list:
        dependent = str(record["canonical_component_id"])
        for requirement in record["definition"].get("requirements", ()):
            reverse[str(requirement["required_component_id_or_source_selector"])].add(dependent)
            fallback_target = requirement.get("fallback_component_id_or_null")
            if fallback_target:
                reverse[str(fallback_target)].add(dependent)
        for binding in record.get("bindings", ()):
            fallback_policy = binding.get("fallback_policy", {})
            fallback_behavior = str(
                fallback_policy.get(
                    "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                )
            )
            fallback_target = fallback_policy.get(
                "fallback_component_id", fallback_policy.get("component_id")
            )
            if fallback_behavior.startswith("USE_FALLBACK") and fallback_target:
                reverse[str(fallback_target)].add(dependent)
    affected_dependents: set[str] = set()
    queue = deque(sorted(directly_affected))
    while queue:
        current = queue.popleft()
        for dependent in sorted(reverse.get(current, ())):
            if dependent not in affected_dependents and dependent not in directly_affected:
                affected_dependents.add(dependent)
                queue.append(dependent)

    candidate_lookup = {str(record["canonical_component_id"]): record for record in candidate_list}
    base_lookup = {str(record["canonical_component_id"]): record for record in base_list}
    consumer_classes: set[str] = set()
    for component_id in directly_affected | affected_dependents:
        for record in (base_lookup.get(component_id), candidate_lookup.get(component_id)):
            if record is None:
                continue
            consumer_classes.update(
                str(item) for item in record["uses"].get("consumer_class_tags", ())
            )
            for binding in record.get("bindings", ()):
                consumer_classes.update(
                    str(item)
                    for item in binding.get("downstream_consumer_classes", ())
                )

    def binding_labels(keys: Iterable[tuple[str, str]]) -> tuple[str, ...]:
        return tuple(sorted(f"{component_id}::{binding_id}" for component_id, binding_id in keys))

    return RegistryUpdateV1(
        batch_id=batch_id,
        registry_schema_version=REGISTRY_SCHEMA_VERSION,
        added_component_ids=tuple(sorted(added)),
        changed_component_ids=tuple(sorted(changed)),
        retired_component_ids=tuple(sorted(retired)),
        added_binding_ids=binding_labels(added_binding_keys),
        changed_binding_ids=binding_labels(changed_binding_keys),
        removed_binding_ids=binding_labels(removed_binding_keys),
        affected_dependent_ids=tuple(sorted(affected_dependents)),
        affected_consumer_classes=tuple(sorted(consumer_classes)),
    )


def _apply_registry_update(
    snapshot: _RegistrySnapshot,
    delta: RegistryUpdateV1 | Mapping[str, Any],
    candidate_records: Iterable[Mapping[str, Any]],
    *,
    verify_full_rebuild: bool = False,
) -> tuple[_RegistrySnapshot, dict[str, Any]]:
    """Build a replacement snapshot and prove incremental/full index parity.

    The immutable snapshot itself is built off to the side.  Index contribution
    accounting is restricted to changed IDs/dependents; a full rebuild remains
    the recovery oracle and is compared before publication.
    """

    if not isinstance(delta, RegistryUpdateV1):
        delta = RegistryUpdateV1.from_mapping(delta)
    if delta.registry_schema_version != REGISTRY_SCHEMA_VERSION:
        raise ValueError("INCOMPATIBLE_REGISTRY_DELTA_SCHEMA")
    candidate_list = [dict(record) for record in candidate_records]
    expected = _derive_registry_update(snapshot.records, candidate_list, batch_id=delta.batch_id)
    if expected.as_dict() != delta.as_dict():
        raise ValueError("REGISTRY_DELTA_NOT_EXACT")
    affected_ids = set(delta.affected_component_ids)
    old_by_id = _record_map_by_component(snapshot.records)
    new_by_id = _record_map_by_component(candidate_list)
    unchanged_ids = (set(old_by_id) & set(new_by_id)) - affected_ids
    for component_id in unchanged_ids:
        if _canonical_value(old_by_id[component_id]) != _canonical_value(new_by_id[component_id]):
            raise ValueError(f"UNDECLARED_REGISTRY_CHANGE: {component_id}")

    old_by_key = {_record_key(record): record for record in snapshot.records}
    new_by_key = {_record_key(record): record for record in candidate_list}
    deleted_accepted = sorted(
        key
        for key, prior in old_by_key.items()
        if prior.get("record_state") == "CANONICAL_ACCEPTED" and key not in new_by_key
    )
    if deleted_accepted:
        raise ValueError(
            "ACCEPTED_RECORD_DELETION_FORBIDDEN: "
            + ", ".join(f"{key[0]}@{key[1]}" for key in deleted_accepted)
        )
    for key in sorted(set(old_by_key).intersection(new_by_key)):
        prior = old_by_key[key]
        candidate = new_by_key[key]
        prior_state = str(prior.get("record_state", ""))
        candidate_state = str(candidate.get("record_state", ""))
        if prior_state == "CANONICAL_ACCEPTED" and candidate_state not in {
            "CANONICAL_ACCEPTED",
            "SUPERSEDED",
            "DORMANT_PRESERVED",
        }:
            raise ValueError(
                f"ACCEPTED_RECORD_STATE_DEMOTION_FORBIDDEN: "
                f"{key[0]}@{key[1]}: {prior_state} -> {candidate_state}"
            )
        if prior_state in TERMINAL_RECORD_STATES and candidate_state != prior_state:
            raise ValueError(
                f"TERMINAL_RECORD_REACTIVATION_FORBIDDEN: "
                f"{key[0]}@{key[1]}: {prior_state} -> {candidate_state}"
            )
        if prior_state == "CANONICAL_ACCEPTED" and candidate_state in {
            "SUPERSEDED",
            "DORMANT_PRESERVED",
        }:
            has_terminal_lineage = any(
                _relation_type(relation) in {"SUCCESSOR_OF", "SUPERSEDES"}
                for relation in candidate.get("relations", ())
                if isinstance(relation, Mapping)
            ) or all(
                binding.get("terminal_disposition_or_null")
                for binding in candidate.get("bindings", ())
            )
            if not has_terminal_lineage:
                raise ValueError(
                    f"ACCEPTED_RECORD_TERMINAL_LINEAGE_REQUIRED: {key[0]}@{key[1]}"
                )
        _validate_binding_authority_transition(prior, candidate)
        if prior.get("record_state") not in {
            "CANONICAL_ACCEPTED",
            "SUPERSEDED",
            "DORMANT_PRESERVED",
        }:
            continue
        if _definition_semantic_core(prior["definition"]) != _definition_semantic_core(
            new_by_key[key]["definition"]
        ):
            raise ValueError(
                f"MATERIAL_DEFINITION_CHANGE_REQUIRES_SUCCESSOR: {key[0]}@{key[1]}"
            )
        if prior.get("record_state") == "CANONICAL_ACCEPTED":
            prior_binding_ids = {
                str(binding["binding_id"]) for binding in prior.get("bindings", ())
            }
            candidate_binding_ids = {
                str(binding["binding_id"])
                for binding in new_by_key[key].get("bindings", ())
            }
            deleted_bindings = sorted(prior_binding_ids - candidate_binding_ids)
            if deleted_bindings:
                raise ValueError(
                    "ACCEPTED_BINDING_DELETION_FORBIDDEN: "
                    f"{key[0]}@{key[1]}: {deleted_bindings}; terminalize in place"
                )

    for record in candidate_list:
        if str(record["canonical_component_id"]) in affected_ids:
            _validate_record_shape(record)
    sorted_records = tuple(
        _freeze(record) for record in sorted(candidate_list, key=_record_key)
    )
    _validate_requirement_graph(sorted_records)
    incremental_indexes = _refresh_indexes_incrementally(
        snapshot.indexes,
        candidate_list,
        affected_ids,
    )
    replacement = _RegistrySnapshot(
        generation=snapshot.generation + 1,
        records=sorted_records,
        indexes=incremental_indexes,
        layout=snapshot.layout,
        shard_count=snapshot.shard_count,
        registry_file_reads=snapshot.registry_file_reads,
        built_at_monotonic=time.monotonic(),
    )
    full_rebuild_parity: bool | None = None
    if verify_full_rebuild:
        full_reference = _build_indexes(candidate_list)
        full_rebuild_parity = (
            _index_signature(replacement.indexes) == _index_signature(full_reference)
        )
        if not full_rebuild_parity:
            raise ValueError("INCREMENTAL_INDEX_FULL_REBUILD_MISMATCH")
    stats = {
        "changed_index_component_ids": sorted(affected_ids),
        "unchanged_index_component_count": len(unchanged_ids),
        "full_rebuild_parity": full_rebuild_parity,
        "new_generation": replacement.generation,
    }
    return replacement, stats


def _semantic_bucket(record: Mapping[str, Any]) -> Any:
    definition = record["definition"]
    input_schema = sorted(
        definition.get("input_schema", ()), key=lambda value: repr(_canonical_value(value))
    )
    output_schema = sorted(
        definition.get("output_schema", ()), key=lambda value: repr(_canonical_value(value))
    )
    requirement_shape = sorted(
        [
        {
            "role": requirement.get("requirement_role"),
            "producer_output": requirement.get("producer_output_name"),
            "consumer_input": requirement.get("consumer_input_name"),
            "required": requirement.get("required_or_optional"),
        }
        for requirement in definition.get("requirements", ())
        ],
        key=lambda value: repr(_canonical_value(value)),
    )
    return _canonical_value(
        {
            "component_kind": definition.get("component_kind"),
            "input_signature": input_schema,
            "output_signature": output_schema,
            "objective_sense": definition.get("objective_sense_or_null"),
            "domain": definition.get("domain_and_boundary_behavior"),
            "state_time": definition.get("state_and_time_semantics"),
            "requirements_shape": requirement_shape,
        }
    )


def _merge_unique_rows(existing: Iterable[Any], additions: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[Any] = set()
    for value in [*existing, *additions]:
        identity = _canonical_value(value)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(_thaw(value))
    return sorted(result, key=_stable_json)


def _merge_bindings_by_id(existing: Iterable[Any], additions: Iterable[Any]) -> list[Any]:
    """Apply contextual binding updates without cloning one binding identity."""

    by_id: dict[str, Any] = {}
    for value in existing:
        binding = _thaw(value)
        binding_id = str(binding.get("binding_id", ""))
        if not binding_id:
            raise ValueError("BINDING_ID_REQUIRED")
        prior = by_id.get(binding_id)
        if prior is not None and _canonical_value(prior) != _canonical_value(binding):
            raise ValueError(f"AMBIGUOUS_EXISTING_BINDING_ID: {binding_id}")
        by_id[binding_id] = binding

    candidate_seen: dict[str, Any] = {}
    for value in additions:
        binding = _thaw(value)
        binding_id = str(binding.get("binding_id", ""))
        if not binding_id:
            raise ValueError("BINDING_ID_REQUIRED")
        prior_candidate = candidate_seen.get(binding_id)
        if (
            prior_candidate is not None
            and _canonical_value(prior_candidate) != _canonical_value(binding)
        ):
            raise ValueError(f"AMBIGUOUS_CANDIDATE_BINDING_ID: {binding_id}")
        candidate_seen[binding_id] = binding
        by_id[binding_id] = binding
    return [by_id[binding_id] for binding_id in sorted(by_id)]


def _validate_proof_refs(proof_refs: Iterable[str], *, candidate_id: str) -> tuple[str, ...]:
    refs = tuple(sorted({str(value).strip() for value in proof_refs if str(value).strip()}))
    independent_tokens = (
        "tests/",
        "tools/validate_",
        "DIRECT_DIFFERENTIAL_TEST::",
        "CONTROL1_DIRECT_PROOF::",
        "SYMBOLIC_EQUIVALENCE::",
        "DIMENSIONAL_EQUIVALENCE::",
        "EXACT_ARITHMETIC::",
        "PROPERTY_TEST::",
        "METAMORPHIC_TEST::",
        "BRUTE_FORCE::",
        "QUANTUM_PARITY::",
    )
    if not refs or not any(
        any(token in reference for token in independent_tokens)
        for reference in refs
    ):
        raise ValueError(f"INDEPENDENT_EQUIVALENCE_PROOF_REQUIRED: {candidate_id}")
    return refs


def _execute_build_owned_equivalence_proof(
    candidate: Mapping[str, Any],
    target: Mapping[str, Any],
    *,
    relation: str,
) -> tuple[str, ...]:
    """Execute the fixed compiler-owned complete-semantics proof.

    Proof outcomes and submitter identity never cross the same caller boundary
    as the candidate.  Contextual family members must preserve the generic
    definition exactly; their differences live in bindings, uses, or
    provenance and therefore reuse the target record.
    """

    candidate_id = str(candidate["canonical_component_id"])
    target_id = str(target["canonical_component_id"])
    if _definition_semantic_core(candidate["definition"]) != _definition_semantic_core(
        target["definition"]
    ):
        raise ValueError(
            f"BUILD_OWNED_EQUIVALENCE_PROOF_FAILED: {candidate_id} -> {target_id}"
        )
    if relation not in {"ALIAS_OF", "FAMILY_BINDING_OF"}:
        raise ValueError(f"INVALID_BUILD_OWNED_PROOF_RELATION: {relation}")
    # This is an exact typed-identity match, not an independent implementation
    # oracle.  Implementation correctness is checked separately below and the
    # reference deliberately does not claim that an oracle was executed.
    return (
        "CONTROL1_COMPILER_MATCH::COMPLETE_TYPED_SEMANTIC_IDENTITY_V1",
        f"CONTROL1_COMPILER_MATCH::{relation}::{target_id}",
    )


def _verify_reused_implementation_changes(
    candidate: dict[str, Any], target: Mapping[str, Any]
) -> tuple[str, ...]:
    """Execute fixed catalog verifiers for implementation additions on reuse.

    Candidate-supplied proof strings are intentionally ignored.  Exact existing
    implementation metadata may be reused without another invocation because
    it adds no implementation behavior.  Any new or changed version/ref must
    have a reviewed verifier callable in the fixed catalog.
    """

    target_rows = {
        str(row.get("implementation_version", "")): row
        for row in target["definition"].get("implementation_versions", ())
        if isinstance(row, Mapping)
    }
    verified_refs: list[str] = []
    for implementation in candidate["definition"].get(
        "implementation_versions", ()
    ):
        if not isinstance(implementation, Mapping):
            continue
        version = str(implementation.get("implementation_version", ""))
        existing = target_rows.get(version)
        if existing is not None and _canonical_value(existing) == _canonical_value(
            implementation
        ):
            continue
        callable_ref = str(implementation.get("callable_or_solver_ref", ""))
        verifier = _BUILD_OWNED_IMPLEMENTATION_VERIFIERS.get(callable_ref)
        if verifier is None:
            raise ValueError(
                "NEW_REUSED_IMPLEMENTATION_REQUIRES_BUILD_OWNED_VERIFIER: "
                f"{target['canonical_component_id']}::{version}::{callable_ref}"
            )
        executed = tuple(
            str(value).strip()
            for value in verifier(candidate, target, implementation)
            if str(value).strip()
        )
        if not executed:
            raise ValueError(
                "BUILD_OWNED_IMPLEMENTATION_VERIFIER_RETURNED_NO_PROOF: "
                f"{target['canonical_component_id']}::{version}::{callable_ref}"
            )
        verified_refs.extend(executed)

    selected_versions = {
        str(binding.get("selected_implementation_version"))
        for binding in candidate.get("bindings", ())
        if isinstance(binding, Mapping)
        and binding.get("selected_implementation_version") not in {None, ""}
    }
    known_versions = set(target_rows) | {
        str(row.get("implementation_version", ""))
        for row in candidate["definition"].get("implementation_versions", ())
        if isinstance(row, Mapping)
        and str(row.get("callable_or_solver_ref", ""))
        in _BUILD_OWNED_IMPLEMENTATION_VERIFIERS
    }
    unverified_selection = sorted(selected_versions - known_versions)
    if unverified_selection:
        raise ValueError(
            "REUSED_BINDING_SELECTS_UNVERIFIED_IMPLEMENTATION: "
            f"{target['canonical_component_id']}: {unverified_selection}"
        )
    if verified_refs:
        candidate["definition"]["equivalence_proof_refs"] = _merge_unique_rows(
            candidate["definition"].get("equivalence_proof_refs", ()),
            verified_refs,
        )
    return tuple(sorted(set(verified_refs)))


def _verify_reused_qku_role_changes(
    candidate: Mapping[str, Any], target: Mapping[str, Any]
) -> None:
    """Reject new QKU authority on semantic reuse without a code-owned proof.

    Existing QKU purposes survive aliases even when the candidate-local root is
    rewritten to the canonical component.  A genuinely new QKU/decision-stage
    key is an authority-bearing use change and may not be admitted from caller
    metadata alone.  The sole narrow exception preserves a newly discovered
    RP5C baseline role on an already dormant, semantically incomplete RP5C row.
    That lane proves the role has no runtime root, selector, readiness, or mode
    authority and therefore cannot turn source provenance into capability.
    """

    candidate_id = str(candidate["canonical_component_id"])
    target_id = str(target["canonical_component_id"])

    def normalized(role: Mapping[str, Any], *, source_id: str) -> Any:
        value = _thaw(role)
        if str(value.get("stack_root_or_direct_component", "")) == source_id:
            value["stack_root_or_direct_component"] = target_id
        return _canonical_value(value)

    existing_roles = {
        normalized(role, source_id=target_id)
        for role in target.get("uses", {}).get("qku_role_bindings", ())
        if isinstance(role, Mapping)
    }
    additions = [
        role
        for role in candidate.get("uses", {}).get("qku_role_bindings", ())
        if isinstance(role, Mapping)
        and normalized(role, source_id=candidate_id) not in existing_roles
    ]
    if additions:
        rp5c_nonruntime_preservation = bool(
            candidate_id == target_id
            and candidate_id.startswith("QTT.COMP.RP5C.")
            and "RP5C_BASELINE" in candidate.get("origin_cohorts", ())
            and "RP5C_BASELINE" in target.get("origin_cohorts", ())
            and candidate.get("record_state") == "DORMANT_PRESERVED"
            and target.get("record_state") == "DORMANT_PRESERVED"
            and str(
                candidate.get("definition", {}).get(
                    "complete_mathematical_or_procedural_definition", ""
                )
            ).startswith(f"MISSING_SEMANTIC_SPECIFICATION: {candidate_id}")
            and all(
                role.get("stack_root_or_direct_component") is None
                and role.get("selection_rule_if_container") is None
                and role.get("runtime_root_eligibility")
                == "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
                and role.get("exact_resolution_action")
                == f"MISSING_SEMANTIC_SPECIFICATION: {candidate_id}"
                and any(
                    str(reference).startswith("docs/master_plan/generated/rp5c/")
                    for reference in role.get("source_refs", ())
                )
                for role in additions
            )
        )
        if rp5c_nonruntime_preservation:
            return
        keys = sorted(
            {
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                )
                for role in additions
            }
        )
        raise ValueError(
            "NEW_REUSED_QKU_ROLE_REQUIRES_BUILD_OWNED_VERIFIER: "
            f"{target_id}: {keys}"
        )


def _validate_binding_authority_transition(
    existing: Mapping[str, Any] | None,
    candidate: Mapping[str, Any],
) -> None:
    existing_bindings = {
        str(value["binding_id"]): value for value in (existing or {}).get("bindings", ())
    }
    for candidate_binding in candidate.get("bindings", ()):
        binding_id = str(candidate_binding["binding_id"])
        prior = existing_bindings.get(binding_id)
        candidate_readiness = candidate_binding.get("readiness", {})
        candidate_authorization = str(candidate_readiness.get("authorization", "NOT_ELIGIBLE"))
        candidate_activation = str(candidate_binding.get("activation_state", "INACTIVE"))
        if prior is None:
            if candidate_authorization == "AUTHORIZED" or candidate_activation in {
                "ACTIVE",
                "AUTHORIZED",
            }:
                raise ValueError(f"BINDING_AUTHORITY_GRANT_FORBIDDEN: {binding_id}")
            continue
        prior_readiness = prior.get("readiness", {})
        if candidate_authorization != str(
            prior_readiness.get("authorization", "NOT_ELIGIBLE")
        ) or candidate_activation != str(prior.get("activation_state", "INACTIVE")):
            raise ValueError(f"BINDING_AUTHORITY_CHANGE_FORBIDDEN: {binding_id}")
        for protected_field in (
            "supported_modes",
            "mode_state",
            "rollback_target_or_null",
            "agent_access_policy",
        ):
            if _canonical_value(candidate_binding.get(protected_field)) != _canonical_value(
                prior.get(protected_field)
            ):
                raise ValueError(
                    f"BINDING_AUTHORITY_CHANGE_FORBIDDEN: {binding_id}.{protected_field}"
                )


def _validate_expansion_envelope(batch: ExpansionBatchV1) -> None:
    if not batch.batch_id.strip() or not batch.batch_origin.strip():
        raise ValueError("INVALID_EXPANSION_BATCH_ID_OR_ORIGIN")
    if batch.submitted_by not in BUILD_OWNED_EXPANSION_SUBMITTERS:
        raise ValueError(
            f"UNTRUSTED_EXPANSION_SUBMITTER: {batch.submitted_by or '<missing>'}"
        )
    try:
        submitted = datetime.fromisoformat(batch.submission_time.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_EXPANSION_SUBMISSION_TIME") from exc
    if submitted.tzinfo is None:
        raise ValueError("NAIVE_EXPANSION_SUBMISSION_TIME")
    if not batch.source_refs:
        raise ValueError("EXPANSION_SOURCE_REFS_REQUIRED")
    if batch.source_classification not in ALLOWED_SOURCE_CLASSIFICATIONS:
        raise ValueError(
            f"INVALID_EXPANSION_SOURCE_CLASSIFICATION: {batch.source_classification}"
        )
    if batch.requested_promotion_ceiling not in {
        "NOT_ELIGIBLE",
        "SPECIFIED",
        "VERIFIED",
        "CONTEXT_READY",
        "STACK_READY",
        "EVIDENCED",
        "AUTHORIZED",
    }:
        raise ValueError(
            f"INVALID_EXPANSION_PROMOTION_CEILING: {batch.requested_promotion_ceiling}"
        )
    invalid_evidence = set(batch.requested_evidence_modes) - {
        "NONE",
        "FIXTURE",
        "REPLAY",
        "PAPER",
        "SHADOW",
        "DRYRUN",
        "CANARY",
        "LIVE",
    }
    if invalid_evidence:
        raise ValueError(f"INVALID_EXPANSION_EVIDENCE_MODES: {sorted(invalid_evidence)}")
    for context in batch.intended_market_venue_modes:
        if not isinstance(context, Mapping):
            raise ValueError("INVALID_EXPANSION_INTENDED_CONTEXT")
        mode = context.get("mode")
        if mode is not None and str(mode) not in MODE_ORDER:
            raise ValueError(f"INVALID_EXPANSION_INTENDED_MODE: {mode}")


def _apply_expansion_envelope_to_candidate(
    candidate: dict[str, Any],
    *,
    batch: ExpansionBatchV1,
    existing: Mapping[str, Any] | None,
) -> None:
    origins = {str(value) for value in candidate.get("origin_cohorts", ())}
    origins.add(batch.batch_origin)
    candidate["origin_cohorts"] = sorted(origins)
    provenance = candidate.get("provenance", ())
    if not any(
        str(value.get("source_artifact_ref", ""))
        in {*batch.source_refs, batch.batch_origin}
        for value in provenance
        if isinstance(value, Mapping)
    ):
        raise ValueError(
            f"EXPANSION_PROVENANCE_NOT_COVERED_BY_ENVELOPE: {candidate['canonical_component_id']}"
        )
    existing_bindings = {
        str(value["binding_id"]): value for value in (existing or {}).get("bindings", ())
    }
    intended = tuple(batch.intended_market_venue_modes)
    requested_evidence = set(batch.requested_evidence_modes)
    for binding in candidate.get("bindings", ()):
        prior = existing_bindings.get(str(binding["binding_id"]))
        if prior is not None and _canonical_value(prior) == _canonical_value(binding):
            continue
        if intended:
            covered = False
            for context in intended:
                market_ok = _selector_values_overlap(
                    context.get("market", "ANY"), binding.get("market", "ANY")
                )
                venue_ok = _selector_values_overlap(
                    context.get("venue", "ANY"), binding.get("venue", "ANY")
                )
                mode = context.get("mode")
                mode_ok = mode is None or str(mode) in {
                    str(value) for value in binding.get("supported_modes", ())
                }
                if market_ok and venue_ok and mode_ok:
                    covered = True
                    break
            if not covered:
                raise ValueError(
                    f"EXPANSION_BINDING_OUTSIDE_INTENDED_CONTEXT: {binding['binding_id']}"
                )
        evidence = str(binding.get("readiness", {}).get("evidence", "NONE"))
        if evidence != "NONE" and evidence not in requested_evidence:
            raise ValueError(
                f"EXPANSION_EVIDENCE_EXCEEDS_REQUEST: {binding['binding_id']}: {evidence}"
            )
        authorization = str(
            binding.get("readiness", {}).get("authorization", "NOT_ELIGIBLE")
        )
        state_ceiling = (
            "SPECIFIED"
            if batch.requested_promotion_ceiling == "NOT_ELIGIBLE"
            else batch.requested_promotion_ceiling
        )
        derived_state = _derived_state(
            candidate,
            binding,
            plan_ready=binding.get("readiness", {}).get("requirements") == "PASS",
        )
        prior_derived_state = (
            _derived_state(
                existing,
                prior,
                plan_ready=prior.get("readiness", {}).get("requirements") == "PASS",
            )
            if prior is not None and existing is not None
            else None
        )
        state_is_new_promotion = prior_derived_state not in PROMOTION_STATE_ORDER or (
            derived_state in PROMOTION_STATE_ORDER
            and PROMOTION_STATE_ORDER[derived_state]
            > PROMOTION_STATE_ORDER[prior_derived_state]
        )
        if derived_state in PROMOTION_STATE_ORDER and (
            PROMOTION_STATE_ORDER[derived_state] > PROMOTION_STATE_ORDER[state_ceiling]
        ) and state_is_new_promotion:
            raise ValueError(
                f"EXPANSION_STATE_EXCEEDS_CEILING: {binding['binding_id']}: "
                f"{derived_state} > {state_ceiling}"
            )
        authorization_ceiling = PROMOTION_AUTHORIZATION_CEILING[
            batch.requested_promotion_ceiling
        ]
        prior_authorization = str(
            (prior or {}).get("readiness", {}).get("authorization", "NOT_ELIGIBLE")
        )
        if (
            AUTHORIZATION_ORDER.get(authorization, 99)
            > AUTHORIZATION_ORDER[authorization_ceiling]
            and AUTHORIZATION_ORDER.get(authorization, 99)
            > AUTHORIZATION_ORDER.get(prior_authorization, -1)
        ):
            raise ValueError(
                f"EXPANSION_AUTHORIZATION_EXCEEDS_CEILING: {binding['binding_id']}: "
                f"{authorization} > {authorization_ceiling}"
            )
        for mode_name, mode_state in binding.get("mode_state", {}).items():
            if not isinstance(mode_state, Mapping):
                continue
            mode_authorization = str(
                mode_state.get(
                    "authorization",
                    mode_state.get("eligibility", "NOT_ELIGIBLE"),
                )
            )
            prior_mode_state = (prior or {}).get("mode_state", {}).get(mode_name, {})
            prior_mode_authorization = (
                str(
                    prior_mode_state.get(
                        "authorization",
                        prior_mode_state.get("eligibility", "NOT_ELIGIBLE"),
                    )
                )
                if isinstance(prior_mode_state, Mapping)
                else "NOT_ELIGIBLE"
            )
            if (
                AUTHORIZATION_ORDER.get(mode_authorization, 99)
                > AUTHORIZATION_ORDER[authorization_ceiling]
                and AUTHORIZATION_ORDER.get(mode_authorization, 99)
                > AUTHORIZATION_ORDER.get(prior_mode_authorization, -1)
            ):
                raise ValueError(
                    f"EXPANSION_MODE_AUTHORITY_EXCEEDS_CEILING: "
                    f"{binding['binding_id']}.{mode_name}: {mode_authorization}"
                )
        if (
            str(binding.get("activation_state", "")).upper()
            in {"ACTIVE", "AUTHORIZED"}
            and batch.requested_promotion_ceiling != "AUTHORIZED"
            and str((prior or {}).get("activation_state", "")).upper()
            not in {"ACTIVE", "AUTHORIZED"}
        ):
            raise ValueError(
                f"EXPANSION_ACTIVATION_EXCEEDS_CEILING: {binding['binding_id']}"
            )
    if batch.source_classification in {
        "OPEN_SOURCE_IMPLEMENTATION",
        "NON_OFFICIAL_RESEARCH",
        "AGENT_DISCOVERED",
    } and candidate.get("record_state") == "CANONICAL_ACCEPTED":
        candidate["record_state"] = "PROVISIONAL"
        for binding in candidate.get("bindings", ()):
            binding["exact_resolution_action_or_null"] = (
                binding.get("exact_resolution_action_or_null")
                or f"MISSING_INDEPENDENT_ACCEPTANCE: {candidate['canonical_component_id']}"
            )


def _rewrite_reused_candidate_targets(
    candidate: dict[str, Any],
    *,
    source_component_id: str,
    canonical_component_id: str,
    canonical_version: str,
) -> None:
    for qku_binding in candidate.get("uses", {}).get("qku_role_bindings", ()):
        if str(qku_binding.get("stack_root_or_direct_component", "")) == source_component_id:
            qku_binding["stack_root_or_direct_component"] = canonical_component_id
            if "semantic_version" in qku_binding:
                qku_binding["semantic_version"] = canonical_version
    for provenance in candidate.get("provenance", ()):
        if str(provenance.get("canonical_target_ref", "")) == source_component_id:
            provenance["canonical_target_ref"] = canonical_component_id


def _merge_provenance_reuse(canonical: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    merged = _thaw(canonical)
    merged["origin_cohorts"] = sorted(set(merged.get("origin_cohorts", ())) | set(candidate.get("origin_cohorts", ())))
    merged["provenance"] = _merge_unique_rows(merged.get("provenance", ()), candidate.get("provenance", ()))
    merged["relations"] = _merge_unique_rows(merged.get("relations", ()), candidate.get("relations", ()))
    for field_name in ("decision_roles", "decision_outputs", "market_family_tags", "qku_role_bindings", "consumer_class_tags"):
        merged["uses"][field_name] = _merge_unique_rows(
            merged["uses"].get(field_name, ()), candidate["uses"].get(field_name, ())
        )
    merged["bindings"] = _merge_bindings_by_id(
        merged.get("bindings", ()), candidate.get("bindings", ())
    )
    for field_name in ("implementation_versions", "oracle_and_test_refs", "equivalence_proof_refs"):
        merged["definition"][field_name] = _merge_unique_rows(
            merged["definition"].get(field_name, ()), candidate["definition"].get(field_name, ())
        )
    return merged


def _canonicalize_requirements(
    records: list[dict[str, Any]],
    *,
    selector_map: Mapping[str, str] | None = None,
    ambiguous_selectors: Iterable[str] = (),
) -> list[dict[str, Any]]:
    selector_map = selector_map or {}
    ambiguous = {str(value) for value in ambiguous_selectors}
    known_ids = {str(record["canonical_component_id"]) for record in records}
    result: list[dict[str, Any]] = []
    for record in records:
        updated = _thaw(record)
        canonical_requirements: list[dict[str, Any]] = []
        seen: set[Any] = set()
        for raw_requirement in updated["definition"].get("requirements", ()):
            requirement = dict(raw_requirement)
            raw_target = str(requirement["required_component_id_or_source_selector"])
            if raw_target in ambiguous:
                raise ValueError(
                    f"AMBIGUOUS_SOURCE_SELECTOR: {updated['canonical_component_id']} -> {raw_target}"
                )
            target = selector_map.get(raw_target, raw_target)
            requirement["required_component_id_or_source_selector"] = target
            fallback = requirement.get("fallback_component_id_or_null")
            if fallback:
                if str(fallback) in ambiguous:
                    raise ValueError(
                        f"AMBIGUOUS_SOURCE_SELECTOR: {updated['canonical_component_id']} -> {fallback}"
                    )
                requirement["fallback_component_id_or_null"] = selector_map.get(str(fallback), str(fallback))
            if target not in known_ids and requirement.get("required_or_optional") == "REQUIRED":
                raise ValueError(f"UNRESOLVED_REQUIRED_REQUIREMENT: {updated['canonical_component_id']} -> {target}")
            identity = _requirement_identity(requirement)
            if identity in seen:
                continue
            seen.add(identity)
            canonical_requirements.append(requirement)
        updated["definition"]["requirements"] = sorted(canonical_requirements, key=_stable_json)
        result.append(updated)
    _validate_requirement_graph(result)
    return result


def _allocate_human_component_id(candidate_name: Any) -> str:
    """Allocate a stable readable ID without source order, time, or hashing."""

    raw = str(candidate_name or "").strip().upper()
    if not raw:
        raise ValueError("EXPANSION_CANDIDATE_IDENTITY_REQUIRED")
    if raw.startswith("QTT.COMP."):
        candidate_id = re.sub(r"[^A-Z0-9_.:-]+", "_", raw)
    else:
        suffix = re.sub(r"[^A-Z0-9]+", "_", raw).strip("_")
        if not suffix:
            raise ValueError("EXPANSION_CANDIDATE_IDENTITY_REQUIRED")
        candidate_id = f"QTT.COMP.EXPANSION.{suffix}"
    if not _is_canonical_component_id(candidate_id):
        raise ValueError(f"INVALID_ALLOCATED_COMPONENT_ID: {candidate_id}")
    return candidate_id


def _not_applicable_quantum_block() -> dict[str, Any]:
    return {
        "applicability_state": "NOT_APPLICABLE",
        "original_economic_problem_ref": None,
        "problem_family": None,
        "formulation_candidates": [],
        "selected_formulation_or_none": None,
        "variable_encoding": None,
        "objective_map": None,
        "constraint_map": None,
        "penalty_policy": None,
        "coefficient_scaling": None,
        "precision_and_quantization": None,
        "decomposition_or_embedding": None,
        "warm_start": None,
        "optimizer_and_version": None,
        "shots_reads_or_sampling_policy": None,
        "seed_resampling_policy": None,
        "inverse_map": None,
        "original_model_feasibility_check": None,
        "same_formulation_classical_comparator": None,
        "local_exact_or_small_instance_parity": None,
        "fallback": "FAIL_CLOSED",
        "maturity_ceiling": "SPECIFIED",
    }


def _materialize_expansion_record(
    item: Mapping[str, Any], batch: ExpansionBatchV1
) -> dict[str, Any]:
    """Compile a raw typed batch item into the sole persistent record shape."""

    embedded = item.get("record")
    if isinstance(embedded, Mapping):
        return _thaw(embedded)
    if "canonical_component_id" in item and "definition" in item:
        return _thaw(item)

    candidate_name = item.get("candidate_identity", item.get("candidate_name"))
    component_id = _allocate_human_component_id(candidate_name)
    component_kind = str(item.get("component_kind", ""))
    procedure = item.get(
        "complete_mathematical_or_procedural_definition",
        item.get("mathematical_or_procedural_specification"),
    )
    input_schema = item.get("input_schema")
    output_schema = item.get("output_schema")
    units = item.get("units_and_bases")
    domain = item.get("domain_and_boundary_behavior")
    state_time = item.get("state_and_time_semantics")
    decision_roles = item.get("decision_roles")
    missing = [
        name
        for name, value in (
            ("component_kind", component_kind),
            ("complete_mathematical_or_procedural_definition", procedure),
            ("input_schema", input_schema),
            ("output_schema", output_schema),
            ("units_and_bases", units),
            ("domain_and_boundary_behavior", domain),
            ("state_and_time_semantics", state_time),
            ("decision_roles", decision_roles),
        )
        if value is None or value == "" or value == []
    ]
    if missing:
        raise ValueError(
            f"INCOMPLETE_RAW_EXPANSION_ITEM: {component_id}: {sorted(missing)}"
        )
    source_provenance = item.get("source_provenance")
    if source_provenance is None:
        source_provenance = [
            {
                "source_artifact_ref": source_ref,
                "source_row_ref": str(candidate_name),
                "source_local_identity_or_name": str(candidate_name),
                "source_fields_consumed": sorted(str(key) for key in item),
                "source_relation": "EXPANSION_BATCH_CANDIDATE",
                "canonical_target_ref": component_id,
                "proof_refs": [],
            }
            for source_ref in batch.source_refs
        ]
    bindings = _thaw(item.get("bindings", ()))
    record: dict[str, Any] = {
        "canonical_component_id": component_id,
        "semantic_version": str(item.get("semantic_version", "1.0")),
        "record_state": "PROVISIONAL",
        "origin_cohorts": [batch.batch_origin],
        "definition": {
            "display_name": str(item.get("display_name", candidate_name)),
            "description": str(
                item.get("description", f"Expansion candidate {candidate_name}")
            ),
            "component_kind": component_kind,
            "family_template_ref_or_null": item.get("family_template_ref_or_null"),
            "complete_mathematical_or_procedural_definition": _thaw(procedure),
            "objective_sense_or_null": item.get("objective_sense_or_null"),
            "assumptions": _thaw(item.get("assumptions", ())),
            "hard_constraints": _thaw(item.get("hard_constraints", ())),
            "soft_preferences": _thaw(item.get("soft_preferences", ())),
            "domain_and_boundary_behavior": _thaw(domain),
            "state_and_time_semantics": _thaw(state_time),
            "input_schema": _thaw(input_schema),
            "output_schema": _thaw(output_schema),
            "units_and_bases": _thaw(units),
            "output_accounting_class": str(
                item.get("output_accounting_class", "NON_ACCOUNTING_CANDIDATE")
            ),
            "missing_stale_nonfinite_behavior": str(
                item.get("missing_stale_nonfinite_behavior", "FAIL_CLOSED")
            ),
            "precision_and_rounding": _thaw(
                item.get("precision_and_rounding", "EXPLICIT_BEFORE_PROMOTION")
            ),
            "parameter_schema_and_default_provenance": _thaw(
                item.get(
                    "parameter_schema_and_default_provenance",
                    {"parameters": [], "default_provenance": None},
                )
            ),
            "requirements": _thaw(item.get("requirement_candidates", item.get("requirements", ()))),
            "latency_class": str(item.get("latency_class", "OFFLINE_RESEARCH")),
            "risk_materiality": _thaw(
                item.get(
                    "risk_materiality",
                    {
                        "economic_materiality": "REQUIRES_REVIEW",
                        "independent_validation_strength_required": "INDEPENDENT_ORACLE",
                    },
                )
            ),
            "failure_domain_tags": _thaw(
                item.get(
                    "failure_domain_tags",
                    ("MISSING_INPUT", "STALE_INPUT", "NONFINITE_INPUT", "DOMAIN_ERROR"),
                )
            ),
            "classical_fallback": _thaw(
                item.get("classical_fallback", {"state": "FAIL_CLOSED"})
            ),
            "quantum": _thaw(item.get("quantum", _not_applicable_quantum_block())),
            "implementation_versions": _thaw(
                item.get("implementation_versions", item.get("implementation_refs", ()))
            ),
            "oracle_and_test_refs": _thaw(item.get("oracle_and_test_refs", ())),
            "equivalence_proof_refs": [],
        },
        "uses": {
            "decision_roles": _thaw(decision_roles),
            "decision_outputs": _thaw(item.get("decision_outputs", ())),
            "market_family_tags": _thaw(item.get("market_family_tags", ())),
            "qku_role_bindings": _thaw(
                item.get("qku_role_bindings", item.get("qku_and_decision_role_links", ()))
            ),
            "consumer_class_tags": _thaw(
                item.get("consumer_class_tags", ("CONTROL1_INDEPENDENT_VALIDATOR",))
            ),
        },
        "bindings": bindings,
        "provenance": _thaw(source_provenance),
        "relations": _thaw(item.get("relations", ())),
        "governance": {
            "producer_owner": "CONTROL1_CENTRAL_BUILDER",
            "validator_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            "reviewer_or_challenger_owner": "OWNER_DESIGNATED_INDEPENDENT_AUDITOR",
            "change_authority": "CONTROL1_CENTRAL_BUILDER_REVIEWED_GIT_PR_ONLY",
        },
    }
    if not bindings:
        record["exact_resolution_action"] = f"MISSING_CONTEXTUAL_BINDING: {component_id}"
    return record


def _selector_seed_from_base(
    base: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, str], set[str]]:
    selector_map: dict[str, str] = {}
    ambiguous: set[str] = set()

    def register(selector: Any, target: str) -> None:
        value = str(selector or "").strip()
        if not value or value in ambiguous:
            return
        prior = selector_map.get(value)
        if prior is not None and prior != target:
            selector_map.pop(value, None)
            ambiguous.add(value)
            return
        selector_map[value] = target

    for record in base:
        if record.get("record_state") != "CANONICAL_ACCEPTED":
            continue
        target = str(record["canonical_component_id"])
        register(target, target)
        for provenance in record.get("provenance", ()):
            if not isinstance(provenance, Mapping):
                continue
            register(provenance.get("source_local_identity_or_name"), target)
            register(provenance.get("source_row_ref"), target)
        for relation in record.get("relations", ()):
            if isinstance(relation, Mapping) and _relation_type(relation) == "ALIAS_OF":
                register(relation.get("source_identity_or_alias"), target)
    return selector_map, ambiguous


def _compile_expansion_batch(
    base_records: Iterable[Mapping[str, Any]],
    batch: ExpansionBatchV1 | Mapping[str, Any],
) -> tuple[list[dict[str, Any]], RegistryUpdateV1, dict[str, Any]]:
    """Private proof-gated expansion compiler used only by the central builder."""

    if not isinstance(batch, ExpansionBatchV1):
        batch = ExpansionBatchV1.from_mapping(batch)
    _validate_expansion_envelope(batch)
    base = [_thaw(record) for record in base_records]
    for record in base:
        _validate_record_shape(record)
    by_key = {_record_key(record): record for record in base}
    buckets: dict[Any, list[tuple[str, str]]] = defaultdict(list)
    for key, record in by_key.items():
        if record.get("record_state") == "CANONICAL_ACCEPTED":
            buckets[_semantic_bucket(record)].append(key)
    pending_occurrences: dict[Any, tuple[str, str]] = {}

    materialized: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for frozen_item in batch.items:
        item = _thaw(frozen_item)
        if not isinstance(item, Mapping):
            raise ValueError("INVALID_EXPANSION_ITEM")
        candidate = _materialize_expansion_record(item, batch)
        _validate_record_shape(candidate, _allow_source_selectors=True)
        materialized.append((dict(item), candidate))

    selector_map, ambiguous_selectors = _selector_seed_from_base(base)

    def register_batch_selector(selector: Any, target: str) -> None:
        value = str(selector or "").strip()
        if not value:
            return
        if value in ambiguous_selectors:
            raise ValueError(f"AMBIGUOUS_SOURCE_SELECTOR: {value}")
        prior = selector_map.get(value)
        if prior is not None and prior != target:
            raise ValueError(
                f"AMBIGUOUS_SOURCE_SELECTOR: {value}: {prior} <> {target}"
            )
        selector_map[value] = target

    for item, candidate in materialized:
        key = _record_key(candidate)
        register_batch_selector(key[0], key[0])
        for source_selector in item.get("source_selector_aliases", ()):
            register_batch_selector(source_selector, key[0])
        register_batch_selector(
            item.get("candidate_identity", item.get("candidate_name")), key[0]
        )

    def redirect_selectors(source: str, target: str) -> None:
        for selector, selected in tuple(selector_map.items()):
            if selected == source:
                selector_map[selector] = target

    outcomes: list[dict[str, Any]] = []
    for item, candidate in sorted(
        materialized,
        key=lambda value: (_record_key(value[1]), _stable_json(value[0])),
    ):
        key = _record_key(candidate)
        decision = str(item.get("equivalence_decision", "INCONCLUSIVE"))
        if decision not in {"YES", "NO", "INCONCLUSIVE"}:
            raise ValueError(f"INVALID_EQUIVALENCE_DECISION: {decision}")
        relation = str(item.get("nonidentical_relation", "DISTINCT"))
        if relation not in {
            "FAMILY_COMPATIBLE",
            "SUCCESSOR",
            "DISTINCT",
            "INVALID",
            "INAPPLICABLE",
        }:
            raise ValueError(f"INVALID_NONIDENTICAL_RELATION: {relation}")

        plausible = tuple(buckets.get(_semantic_bucket(candidate), ()))
        identical = [
            plausible_key
            for plausible_key in plausible
            if _definition_semantic_core(by_key[plausible_key]["definition"])
            == _definition_semantic_core(candidate["definition"])
        ]

        family_target_key: tuple[str, str] | None = None
        if relation == "FAMILY_COMPATIBLE":
            family_targets = {
                str(value.get("canonical_target_ref", "")).split("@", 1)[0]
                for value in candidate.get("relations", ())
                if isinstance(value, Mapping)
                and _relation_type(value) == "FAMILY_BINDING_OF"
            }
            if len(family_targets) != 1 or not next(iter(family_targets)):
                raise ValueError(f"FAMILY_CANONICAL_TARGET_REQUIRED: {key[0]}")
            target_id = next(iter(family_targets))
            family_keys = sorted(
                value
                for value, record in by_key.items()
                if value[0] == target_id
                and record.get("record_state") == "CANONICAL_ACCEPTED"
            )
            if len(family_keys) != 1:
                raise ValueError(f"FAMILY_CANONICAL_TARGET_AMBIGUOUS: {key[0]}")
            family_target_key = family_keys[0]

        envelope_existing = by_key.get(key)
        if envelope_existing is None and family_target_key is not None:
            envelope_existing = by_key[family_target_key]
        if envelope_existing is None and len(identical) == 1:
            envelope_existing = by_key[identical[0]]
        _apply_expansion_envelope_to_candidate(
            candidate,
            batch=batch,
            existing=envelope_existing,
        )
        _validate_record_shape(candidate, _allow_source_selectors=True)

        if key in by_key:
            existing = by_key[key]
            if _definition_semantic_core(existing["definition"]) != _definition_semantic_core(candidate["definition"]):
                raise ValueError(f"MATERIAL_DEFINITION_CHANGE_REQUIRES_SUCCESSOR: {key[0]}@{key[1]}")
            _verify_reused_implementation_changes(candidate, existing)
            _verify_reused_qku_role_changes(candidate, existing)
            _validate_binding_authority_transition(existing, candidate)
            merged = _merge_provenance_reuse(existing, candidate)
            by_key[key] = merged
            outcomes.append({"candidate": key[0], "decision": "EXISTING_ID_UPDATE", "canonical_target": key[0]})
            continue

        if family_target_key is not None:
            canonical_key = family_target_key
            proof_refs = _execute_build_owned_equivalence_proof(
                candidate,
                by_key[canonical_key],
                relation="FAMILY_BINDING_OF",
            )
            implementation_proof_refs = _verify_reused_implementation_changes(
                candidate, by_key[canonical_key]
            )
            _verify_reused_qku_role_changes(candidate, by_key[canonical_key])
            proof_refs = tuple(
                sorted(set(proof_refs) | set(implementation_proof_refs))
            )
            candidate["definition"]["equivalence_proof_refs"] = _merge_unique_rows(
                candidate["definition"].get("equivalence_proof_refs", ()),
                proof_refs,
            )
            _validate_binding_authority_transition(by_key[canonical_key], candidate)
            _rewrite_reused_candidate_targets(
                candidate,
                source_component_id=key[0],
                canonical_component_id=canonical_key[0],
                canonical_version=canonical_key[1],
            )
            candidate["relations"] = _merge_unique_rows(
                candidate.get("relations", ()),
                (
                    {
                        "relation_type": "FAMILY_BINDING_OF",
                        "source_identity_or_alias": item.get(
                            "candidate_identity", item.get("candidate_name", key[0])
                        ),
                        "canonical_target_ref": canonical_key[0],
                        "canonical_target_version": canonical_key[1],
                        "proof_refs": list(proof_refs),
                    },
                ),
            )
            by_key[canonical_key] = _merge_provenance_reuse(
                by_key[canonical_key], candidate
            )
            redirect_selectors(key[0], canonical_key[0])
            outcomes.append(
                {
                    "candidate": key[0],
                    "decision": "FAMILY_COMPATIBLE_REUSED",
                    "canonical_target": canonical_key[0],
                }
            )
            continue

        if identical:
            if len(identical) != 1:
                raise ValueError(f"AMBIGUOUS_EQUIVALENT_CANONICAL: {key[0]}")
            canonical_key = identical[0]
            if decision == "NO":
                raise ValueError(
                    f"SEMANTIC_DECISION_CONTRADICTS_COMPLETE_EQUALITY: {key[0]}"
                )
            proof_refs = _execute_build_owned_equivalence_proof(
                candidate,
                by_key[canonical_key],
                relation="ALIAS_OF",
            )
            implementation_proof_refs = _verify_reused_implementation_changes(
                candidate, by_key[canonical_key]
            )
            _verify_reused_qku_role_changes(candidate, by_key[canonical_key])
            proof_refs = tuple(
                sorted(set(proof_refs) | set(implementation_proof_refs))
            )
            candidate["definition"]["equivalence_proof_refs"] = _merge_unique_rows(
                candidate["definition"].get("equivalence_proof_refs", ()),
                proof_refs,
            )
            _validate_binding_authority_transition(by_key[canonical_key], candidate)
            _rewrite_reused_candidate_targets(
                candidate,
                source_component_id=key[0],
                canonical_component_id=canonical_key[0],
                canonical_version=canonical_key[1],
            )
            candidate["relations"] = _merge_unique_rows(
                candidate.get("relations", ()),
                (
                    {
                        "relation_type": "ALIAS_OF",
                        "source_identity_or_alias": item.get("candidate_alias", key[0]),
                        "canonical_target_ref": canonical_key[0],
                        "canonical_target_version": canonical_key[1],
                        "proof_refs": list(proof_refs),
                    },
                ),
            )
            by_key[canonical_key] = _merge_provenance_reuse(by_key[canonical_key], candidate)
            redirect_selectors(key[0], canonical_key[0])
            outcomes.append({"candidate": key[0], "decision": "REUSED", "canonical_target": canonical_key[0]})
            continue

        pending_identity = (
            _semantic_bucket(candidate),
            _definition_semantic_core(candidate["definition"]),
        )
        pending_key = pending_occurrences.get(pending_identity)
        if pending_key is not None:
            pending = by_key[pending_key]
            _verify_reused_implementation_changes(candidate, pending)
            _verify_reused_qku_role_changes(candidate, pending)
            _validate_binding_authority_transition(pending, candidate)
            _rewrite_reused_candidate_targets(
                candidate,
                source_component_id=key[0],
                canonical_component_id=pending_key[0],
                canonical_version=pending_key[1],
            )
            by_key[pending_key] = _merge_provenance_reuse(pending, candidate)
            redirect_selectors(key[0], pending_key[0])
            outcomes.append(
                {
                    "candidate": key[0],
                    "decision": "PROVISIONAL_OCCURRENCE_MERGED",
                    "canonical_target": pending_key[0],
                }
            )
            continue
        if decision == "YES":
            raise ValueError(f"UNPROVEN_EQUIVALENCE: {key[0]}")
        if decision == "INCONCLUSIVE":
            candidate["record_state"] = "PROVISIONAL"
            for binding in candidate.get("bindings", ()):
                binding["exact_resolution_action_or_null"] = binding.get("exact_resolution_action_or_null") or (
                    f"MISSING_EQUIVALENCE_PROOF: {key[0]}"
                )
                binding["readiness"]["specification"] = "REQUIRED"
        if relation == "SUCCESSOR" and not any(
            _relation_type(value) == "SUCCESSOR_OF" for value in candidate.get("relations", ()) if isinstance(value, Mapping)
        ):
            raise ValueError(f"SUCCESSOR_LINEAGE_REQUIRED: {key[0]}")
        if relation == "INVALID" and candidate.get("record_state") != "REJECTED_INVALID":
            raise ValueError(f"INVALID_RELATION_REQUIRES_REJECTED_STATE: {key[0]}")
        if relation == "INAPPLICABLE" and candidate.get("record_state") != "INAPPLICABLE_WITH_PROOF":
            raise ValueError(f"INAPPLICABLE_RELATION_REQUIRES_TERMINAL_STATE: {key[0]}")
        _validate_binding_authority_transition(None, candidate)
        by_key[key] = candidate
        if candidate.get("record_state") == "CANONICAL_ACCEPTED":
            buckets[_semantic_bucket(candidate)].append(key)
        elif candidate.get("record_state") in {"PROVISIONAL", "UNDER_REVIEW"}:
            pending_occurrences[pending_identity] = key
        outcomes.append({"candidate": key[0], "decision": relation, "canonical_target": key[0]})

    candidate_records = _canonicalize_requirements(
        list(by_key.values()),
        selector_map=selector_map,
        ambiguous_selectors=ambiguous_selectors,
    )
    for record in candidate_records:
        _validate_record_shape(record)
    delta = _derive_registry_update(base, candidate_records, batch_id=batch.batch_id)
    report = {
        "batch_id": batch.batch_id,
        "items_read": len(batch.items),
        "bounded_candidate_bucket_count": len(buckets),
        "all_pairs_proof_attempted": False,
        "outcomes": sorted(outcomes, key=lambda value: str(value["candidate"])),
    }
    return sorted(candidate_records, key=_record_key), delta, report


def _schema_map(schema: Any) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    if isinstance(schema, Mapping):
        for name, spec in schema.items():
            if isinstance(spec, Mapping):
                result[str(name)] = spec
            else:
                result[str(name)] = MappingProxyType({"type": str(spec), "unit": "UNSPECIFIED"})
        return result
    if isinstance(schema, (list, tuple)):
        for entry in schema:
            if isinstance(entry, str):
                result[entry] = MappingProxyType({"name": entry, "type": "ANY", "unit": "UNSPECIFIED"})
            elif isinstance(entry, Mapping):
                name = entry.get("name") or entry.get("field") or entry.get("input_name") or entry.get("output_name")
                if name:
                    result[str(name)] = entry
    return result


def _parameter_schema_map(schema: Any) -> dict[str, Mapping[str, Any]]:
    """Normalize both compact and nested parameter-schema representations."""

    if isinstance(schema, Mapping) and "parameters" in schema:
        parameters = schema.get("parameters")
        if not isinstance(parameters, (Mapping, list, tuple)):
            raise ValueError("INVALID_PARAMETER_SCHEMA_PARAMETERS")
        return _schema_map(parameters)
    return _schema_map(schema)


def _schema_unit(spec: Mapping[str, Any] | None) -> str:
    if not spec:
        return "UNSPECIFIED"
    return str(
        spec.get(
            "unit",
            spec.get(
                "units",
                spec.get("unit_or_basis", spec.get("basis", "UNSPECIFIED")),
            ),
        )
    )


def _input_source_expectation(binding: Mapping[str, Any], input_name: str) -> Any:
    configured = binding.get("input_source_bindings", {})
    if isinstance(configured, Mapping):
        return configured.get(input_name)
    if isinstance(configured, (list, tuple)):
        for entry in configured:
            if not isinstance(entry, Mapping):
                continue
            declared_name = entry.get("input_name", entry.get("name"))
            if declared_name is not None and str(declared_name) == input_name:
                return entry.get("source", entry.get("source_ref", entry))
    return None


def _validate_input_lineage_binding(
    lineage: Any,
    *,
    binding: Mapping[str, Any],
    input_name: str,
    mode: str,
) -> None:
    if mode in {"STATIC_VALIDATION", "TEST_VECTOR", "FIXTURE_NONLIVE"}:
        return
    expectation = _input_source_expectation(binding, input_name)
    if expectation is None:
        raise ComputationControlError(
            "MISSING_INPUT_SOURCE_BINDING",
            f"{binding['binding_id']}: {input_name}",
        )
    lineage_candidates: list[Any]
    if isinstance(lineage, Mapping):
        lineage_candidates = [
            lineage.get("source"),
            lineage.get("source_class"),
            lineage.get("binding_ref"),
            lineage.get("input_source_binding"),
        ]
    else:
        lineage_candidates = [lineage]
    if _canonical_value(expectation) not in {
        _canonical_value(value) for value in lineage_candidates if value is not None
    }:
        raise ComputationControlError(
            "INPUT_LINEAGE_BINDING_MISMATCH",
            f"{binding['binding_id']}.{input_name}",
        )


def _validate_schema_value(
    value: Any,
    spec: Mapping[str, Any] | None,
    *,
    path: str,
    output_accounting_class: str | None = None,
) -> None:
    _reject_nonfinite(value, path=path)
    if not spec:
        return
    declared = str(spec.get("type", "ANY")).upper().replace(" ", "_")
    valid = True
    if declared not in {"", "ANY", "UNSPECIFIED"}:
        if "NUMERIC_OR_SEQUENCE" in declared:
            valid = (
                not isinstance(value, bool)
                and isinstance(value, (int, float, Decimal, list, tuple))
            )
        elif "NUMERIC_OR_STRUCTURE" in declared:
            valid = (
                not isinstance(value, bool)
                and isinstance(value, (int, float, Decimal, list, tuple, Mapping))
            )
        elif any(token in declared for token in ("ARRAY", "LIST", "SEQUENCE")):
            valid = isinstance(value, (list, tuple))
        elif any(token in declared for token in ("OBJECT", "MAPPING", "DICT", "RECORD", "STRUCTURE")):
            valid = isinstance(value, Mapping)
        elif "BOOL" in declared:
            valid = isinstance(value, bool)
        elif any(token in declared for token in ("STRING", "TEXT", "IDENTIFIER")):
            valid = isinstance(value, str)
        elif "INTEGER" in declared or declared == "INT":
            try:
                numeric = Decimal(str(value))
                valid = not isinstance(value, bool) and numeric.is_finite() and numeric == numeric.to_integral_value()
            except (InvalidOperation, ValueError, TypeError):
                valid = False
        elif any(token in declared for token in ("NUMBER", "NUMERIC", "DECIMAL", "FLOAT", "PROBABILITY")):
            try:
                numeric = Decimal(str(value))
                valid = not isinstance(value, bool) and numeric.is_finite()
            except (InvalidOperation, ValueError, TypeError):
                valid = False
    if not valid:
        raise ComputationControlError(
            "TYPE_MISMATCH", f"{path}: expected {declared}, got {type(value).__name__}"
        )
    def numeric_constraint(name: str) -> Decimal | None:
        if name not in spec:
            return None
        try:
            result = Decimal(str(spec[name]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ComputationControlError("INVALID_SCHEMA_BOUND", f"{path}.{name}") from exc
        if not result.is_finite():
            raise ComputationControlError("INVALID_SCHEMA_BOUND", f"{path}.{name}")
        return result

    minimum = numeric_constraint("minimum")
    maximum = numeric_constraint("maximum")
    exclusive_minimum = numeric_constraint("exclusiveMinimum")
    exclusive_maximum = numeric_constraint("exclusiveMaximum")
    if any(
        bound is not None
        for bound in (minimum, maximum, exclusive_minimum, exclusive_maximum)
    ):
        try:
            numeric_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ComputationControlError("SCHEMA_BOUND_TYPE_MISMATCH", path) from exc
        if minimum is not None and numeric_value < minimum:
            raise ComputationControlError(
                "BELOW_MINIMUM", f"{path}: {numeric_value} < {minimum}"
            )
        if maximum is not None and numeric_value > maximum:
            raise ComputationControlError(
                "ABOVE_MAXIMUM", f"{path}: {numeric_value} > {maximum}"
            )
        if exclusive_minimum is not None and numeric_value <= exclusive_minimum:
            raise ComputationControlError(
                "BELOW_EXCLUSIVE_MINIMUM",
                f"{path}: {numeric_value} <= {exclusive_minimum}",
            )
        if exclusive_maximum is not None and numeric_value >= exclusive_maximum:
            raise ComputationControlError(
                "ABOVE_EXCLUSIVE_MAXIMUM",
                f"{path}: {numeric_value} >= {exclusive_maximum}",
            )
    allowed_values = spec.get("enum", spec.get("allowed_values"))
    if allowed_values is not None:
        if not isinstance(allowed_values, (list, tuple)) or not allowed_values:
            raise ComputationControlError("INVALID_SCHEMA_ENUM", path)
        if _canonical_value(value) not in {
            _canonical_value(item) for item in allowed_values
        }:
            raise ComputationControlError(
                "ENUM_ALLOWED_VALUE_VIOLATION", f"{path}: {value!r}"
            )
    shape = spec.get("shape")
    if shape is not None and isinstance(shape, (list, tuple)) and shape:
        if not isinstance(value, (list, tuple)) or (
            isinstance(shape[0], int) and len(value) != shape[0]
        ):
            raise ComputationControlError("SHAPE_MISMATCH", path)
    if isinstance(value, (list, tuple, Mapping, str)):
        minimum_size = spec.get("minItems", spec.get("minLength"))
        maximum_size = spec.get("maxItems", spec.get("maxLength"))
        if minimum_size is not None and len(value) < int(minimum_size):
            raise ComputationControlError("BELOW_MINIMUM_SIZE", path)
        if maximum_size is not None and len(value) > int(maximum_size):
            raise ComputationControlError("ABOVE_MAXIMUM_SIZE", path)
    unit = _schema_unit(spec)
    money_tokens = {
        token for token in re.split(r"[^A-Z0-9]+", unit.upper()) if token
    }
    accounting = str(output_accounting_class or "").upper()
    money_boundary = bool(
        money_tokens & MONEY_UNIT_TOKENS
        or any(token in accounting for token in MONEY_UNIT_TOKENS)
    )
    if money_boundary:
        def contains_binary_float(candidate: Any) -> bool:
            if isinstance(candidate, float):
                return True
            if isinstance(candidate, Mapping):
                return any(contains_binary_float(item) for item in candidate.values())
            if isinstance(candidate, (list, tuple)):
                return any(contains_binary_float(item) for item in candidate)
            return False

        if contains_binary_float(value):
            raise ComputationControlError("BINARY_FLOAT_MONEY_BOUNDARY", path)


def _units_compatible(producer: str, consumer: str, conversion: Any) -> bool:
    neutral = {"", "NONE", "IDENTITY", None}
    if producer == consumer:
        return True
    if producer in {"UNSPECIFIED", "ANY"} or consumer in {"UNSPECIFIED", "ANY"}:
        return conversion not in {"REQUIRED_UNSPECIFIED", "MISSING"}
    if conversion in neutral:
        return False
    if conversion in {"PERCENT_TO_DECIMAL", "DECIMAL_TO_PERCENT"}:
        return {producer, consumer} <= {"PERCENT", "DECIMAL_PROBABILITY", "PROBABILITY"}
    if isinstance(conversion, Mapping) and "factor" in conversion:
        return True
    return False


def _validate_requirement_ports(
    consumer: Mapping[str, Any],
    producer: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> None:
    producer_outputs = _schema_map(producer["definition"].get("output_schema", ()))
    consumer_inputs = _schema_map(consumer["definition"].get("input_schema", ()))
    producer_name = str(requirement["producer_output_name"])
    consumer_name = str(requirement["consumer_input_name"])
    if producer_name not in producer_outputs:
        raise ValueError(
            f"REQUIREMENT_PRODUCER_PORT_MISSING: {consumer['canonical_component_id']} <- "
            f"{producer['canonical_component_id']}.{producer_name}"
        )
    if consumer_name not in consumer_inputs:
        raise ValueError(f"REQUIREMENT_CONSUMER_PORT_MISSING: {consumer['canonical_component_id']}.{consumer_name}")
    producer_unit = _schema_unit(producer_outputs[producer_name])
    consumer_unit = _schema_unit(consumer_inputs[consumer_name])
    if not _units_compatible(producer_unit, consumer_unit, requirement.get("unit_or_basis_conversion")):
        raise ValueError(
            f"REQUIREMENT_UNIT_MISMATCH: {producer['canonical_component_id']}.{producer_name}({producer_unit}) -> "
            f"{consumer['canonical_component_id']}.{consumer_name}({consumer_unit})"
        )


def _semantic_version_for_constraint(
    indexes: _RegistryIndexes,
    component_id: str,
    constraint: str,
) -> tuple[str, str]:
    candidates = [
        key
        for key in indexes.record_keys_by_id.get(component_id, ())
        if indexes.records_by_key[key].get("record_state") in ACTIVE_RECORD_STATES
    ]
    if constraint not in {"*", "ANY"}:
        exact = constraint.removeprefix("==")
        candidates = [key for key in candidates if key[1] == exact]
    if not candidates:
        raise ComputationControlError("MISSING_REQUIREMENT", f"{component_id}@{constraint}", component_id=component_id)
    if len(candidates) != 1:
        raise ComputationControlError(
            "AMBIGUOUS_SEMANTIC_VERSION",
            f"explicit version required for {component_id}: {[key[1] for key in candidates]}",
            component_id=component_id,
        )
    return candidates[0]


def _binding_compatibility_score(binding: Mapping[str, Any], context: Mapping[str, Any]) -> int | None:
    if not _binding_is_selectable(binding):
        return None
    score = 0
    for field_name in ("market", "venue"):
        requested = context.get(field_name)
        available = binding.get(field_name, "ANY")
        if requested is None:
            continue
        if available in {"ANY", "ALL", "*", None}:
            continue
        if str(requested) != str(available):
            return None
        score += 4
    mode = str(context.get("mode", "STATIC_VALIDATION"))
    supported_modes = {str(value) for value in binding.get("supported_modes", ())}
    if mode not in supported_modes:
        return None
    score += 2
    selector = binding.get("context_selector", {})
    if isinstance(selector, Mapping):
        for key, expected in selector.items():
            if expected in {"ANY", "*", None}:
                continue
            if key not in context:
                return None
            if key in context and _canonical_value(context[key]) != _canonical_value(expected):
                return None
            if key in context:
                score += 1
    requested_binding = context.get("binding_id")
    if requested_binding is not None:
        if str(binding.get("binding_id")) != str(requested_binding):
            return None
        score += 100
    return score


def _select_binding(
    record: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    indexes: _RegistryIndexes | None = None,
    record_key: tuple[str, str] | None = None,
) -> Mapping[str, Any]:
    candidates: list[tuple[int, str, Mapping[str, Any]]] = []
    scoring_context = dict(context)
    scoring_context.setdefault(
        "component_id", str(record.get("canonical_component_id", ""))
    )
    scoring_context.setdefault(
        "canonical_component_id", str(record.get("canonical_component_id", ""))
    )
    bindings: Iterable[Mapping[str, Any]] = record.get("bindings", ())
    if indexes is not None and record_key is not None:
        requested_market = context.get("market")
        requested_venue = context.get("venue")
        requested_mode = str(context.get("mode", "STATIC_VALIDATION"))
        if requested_market is not None and requested_venue is not None:
            matching_ids: set[str] = set()
            for market in (str(requested_market), "ANY", "ALL", "*"):
                for venue in (str(requested_venue), "ANY", "ALL", "*"):
                    for candidate_key, binding_id in indexes.context_binding_candidates.get(
                        (market, venue, requested_mode), ()
                    ):
                        if candidate_key == record_key:
                            matching_ids.add(str(binding_id))
            bindings = tuple(
                binding
                for binding in indexes.bindings_by_record.get(record_key, ())
                if str(binding.get("binding_id")) in matching_ids
            )
        else:
            bindings = indexes.bindings_by_record.get(record_key, ())
    for binding in bindings:
        score = _binding_compatibility_score(binding, scoring_context)
        if score is not None:
            candidates.append((score, str(binding["binding_id"]), binding))
    if not candidates:
        raise ComputationControlError(
            "MISSING_CONTEXT_BINDING",
            f"no binding for {record['canonical_component_id']} and context {_stable_json(context)}",
            component_id=str(record["canonical_component_id"]),
        )
    candidates.sort(key=lambda value: (-value[0], value[1]))
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise ComputationControlError(
            "AMBIGUOUS_CONTEXT_BINDING",
            f"{record['canonical_component_id']}: {candidates[0][1]}, {candidates[1][1]}",
            component_id=str(record["canonical_component_id"]),
        )
    return candidates[0][2]


def _selected_implementation(
    record: Mapping[str, Any], binding: Mapping[str, Any]
) -> tuple[str, str, Mapping[str, Any]]:
    selected = str(binding.get("selected_implementation_version", ""))
    implementations = record["definition"].get("implementation_versions", ())
    for implementation in implementations:
        version = str(implementation.get("implementation_version", ""))
        if version == selected:
            return version, str(implementation["callable_or_solver_ref"]), implementation
    if not implementations:
        return "UNAVAILABLE", "", MappingProxyType({})
    raise ComputationControlError(
        "MISSING_IMPLEMENTATION",
        f"{record['canonical_component_id']} selected {selected}",
        component_id=str(record["canonical_component_id"]),
    )


def _binding_blockers(binding: Mapping[str, Any], *, mode: str) -> tuple[str, ...]:
    readiness = binding.get("readiness", {})
    blockers: list[str] = []
    for dimension in READINESS_DIMENSIONS:
        state = readiness.get(dimension)
        if state == "INVALID":
            blockers.append(f"INVALID_{dimension.upper()}: {binding['binding_id']}")
        elif state == "REQUIRED":
            blockers.append(f"MISSING_{dimension.upper()}: {binding['binding_id']}")
    if mode not in {"STATIC_VALIDATION", "TEST_VECTOR", "FIXTURE_NONLIVE"}:
        state_value = binding.get("mode_state", {}).get(mode)
        if _mode_state_is_ineligible(state_value):
            blockers.append(f"MODE_STATE_NOT_ELIGIBLE: {mode}")
        if _mode_state_authorization(state_value) != "AUTHORIZED":
            blockers.append(f"MODE_STATE_NOT_AUTHORIZED: {mode}")
        if readiness.get("authorization") != "AUTHORIZED":
            blockers.append(f"MODE_NOT_AUTHORIZED: {mode}")
        if str(binding.get("activation_state")) not in {"ACTIVE", "AUTHORIZED"}:
            blockers.append(f"BINDING_NOT_ACTIVE: {binding['binding_id']}")
    action = binding.get("exact_resolution_action_or_null")
    if blockers and action:
        blockers.append(str(action))
    return tuple(dict.fromkeys(blockers))


def _mode_state_is_ineligible(state_value: Any) -> bool:
    if isinstance(state_value, Mapping):
        state = " ".join(str(value).upper() for value in state_value.values())
    else:
        state = str(state_value).upper()
    return any(
        token in state
        for token in (
            "NOT_AUTHORIZED",
            "DISABLED",
            "BLOCKED",
            "INELIGIBLE",
            "NOT_ELIGIBLE",
            "FIXTURE_ONLY",
            "REFERENCE_ONLY",
        )
    )


def _mode_state_authorization(state_value: Any) -> str:
    if isinstance(state_value, Mapping):
        return str(
            state_value.get(
                "authorization",
                state_value.get("eligibility", state_value.get("state", "")),
            )
        ).upper()
    return str(state_value or "").upper()


def _derived_state(record: Mapping[str, Any], binding: Mapping[str, Any], *, plan_ready: bool) -> str:
    if record.get("record_state") in {"REJECTED_INVALID", "INAPPLICABLE_WITH_PROOF"}:
        return "INVALID"
    if record.get("record_state") in {"SUPERSEDED", "DORMANT_PRESERVED"} or binding.get("terminal_disposition_or_null"):
        return "RETIRED"
    if record.get("record_state") in {"PROVISIONAL", "UNDER_REVIEW"}:
        return "SPECIFIED"
    readiness = binding.get("readiness", {})
    if readiness.get("specification") != "PASS":
        return "SPECIFIED"
    if readiness.get("implementation") != "PASS" or readiness.get("oracle") != "PASS":
        return "SPECIFIED"
    state = "VERIFIED"
    if all(readiness.get(name) == "PASS" for name in ("inputs", "requirements", "context")):
        state = "CONTEXT_READY"
    if state == "CONTEXT_READY" and plan_ready:
        state = "STACK_READY"
    if state == "STACK_READY" and readiness.get("evidence") not in {"NONE", "FIXTURE"}:
        state = "EVIDENCED"
    if state == "EVIDENCED" and readiness.get("authorization") == "AUTHORIZED" and binding.get("activation_state") == "ACTIVE":
        state = "AUTHORIZED"
    return state


def _pinned_node_context(
    selection_context: Mapping[str, Any],
    *,
    component_id: str,
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    context = _thaw(selection_context)
    context["component_id"] = component_id
    context["canonical_component_id"] = component_id
    context["binding_id"] = str(binding["binding_id"])
    context["binding_as_of_policy"] = _thaw(binding.get("as_of_policy"))
    context["binding_point_in_time_policy"] = _thaw(
        binding.get("point_in_time_policy")
    )
    context["binding_freshness_and_TTL"] = _thaw(
        binding.get("freshness_and_TTL", {})
    )
    freshness = binding.get("freshness_and_TTL", {})
    if isinstance(freshness, Mapping):
        ttl = freshness.get("ttl_seconds", freshness.get("TTL_seconds"))
        if ttl is not None:
            context["freshness_ttl_seconds"] = ttl
    context["request_scope"] = "SAME_REQUEST"
    return context


def _derive_requirement_context(
    consumer_context: Mapping[str, Any],
    *,
    consumer_binding: Mapping[str, Any],
    requirement: Mapping[str, Any],
    target_component_id: str,
) -> dict[str, Any]:
    policy = consumer_binding.get("requirement_context_policy")
    if isinstance(policy, str):
        if policy in {"", "UNRESOLVED", "NOT_RESOLVED"}:
            raise ComputationControlError(
                "UNRESOLVED_REQUIREMENT_CONTEXT_POLICY",
                f"{consumer_binding['binding_id']}: {requirement.get('requirement_role')}",
            )
        if policy not in {
            "INHERIT_ROOT_CONTEXT",
            "SAME_REQUEST",
            "SAME_REQUEST_INPUT_LOCK",
            "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
            "SAME_FIXTURE_INPUT_LOCK",
        }:
            raise ComputationControlError(
                "UNSUPPORTED_REQUIREMENT_CONTEXT_POLICY", str(policy)
            )
        context = _thaw(consumer_context)
    elif isinstance(policy, Mapping):
        inherit = bool(policy.get("inherit_root_context", True))
        context = _thaw(consumer_context) if inherit else {}
        include_fields = policy.get("include_fields")
        if include_fields is not None:
            if not isinstance(include_fields, (list, tuple)):
                raise ComputationControlError(
                    "INVALID_REQUIREMENT_CONTEXT_POLICY", "include_fields"
                )
            context = {
                str(name): _thaw(consumer_context[str(name)])
                for name in include_fields
                if str(name) in consumer_context
            }
        overrides = policy.get("overrides", {})
        if not isinstance(overrides, Mapping):
            raise ComputationControlError(
                "INVALID_REQUIREMENT_CONTEXT_POLICY", "overrides"
            )
        context.update(_thaw(overrides))
    else:
        raise ComputationControlError(
            "INVALID_REQUIREMENT_CONTEXT_POLICY",
            str(consumer_binding.get("binding_id", "")),
        )

    timing = str(requirement.get("timing_and_freshness_constraint", ""))
    supported_timing = {
        "SAME_REQUEST",
        "SAME_REQUEST_INPUT_LOCK",
        "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
    }
    if timing not in supported_timing:
        raise ComputationControlError(
            "UNSUPPORTED_REQUIREMENT_TIMING_POLICY", timing
        )
    consumer_mode = str(
        consumer_context.get("mode", "STATIC_VALIDATION")
    )
    producer_mode = str(context.get("mode", consumer_mode))
    consumer_rank = MODE_ORDER.get(consumer_mode)
    producer_rank = MODE_ORDER.get(producer_mode)
    if (
        consumer_rank is None
        or producer_rank is None
        or producer_rank > consumer_rank
    ):
        raise ComputationControlError(
            "REQUIREMENT_CONTEXT_MODE_ESCALATION",
            f"{consumer_mode} -> {producer_mode}",
        )
    context.pop("binding_id", None)
    context.pop("binding_as_of_policy", None)
    context.pop("binding_point_in_time_policy", None)
    context.pop("binding_freshness_and_TTL", None)
    context["component_id"] = target_component_id
    context["canonical_component_id"] = target_component_id
    context["request_scope"] = "SAME_REQUEST"
    context["requirement_timing_policy"] = timing
    context["input_lock_policy"] = (
        "IMMUTABLE"
        if timing == "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
        else "REQUEST_SCOPED"
    )
    if policy == "SAME_FIXTURE_INPUT_LOCK" and str(
        context.get("mode", "STATIC_VALIDATION")
    ) not in {"STATIC_VALIDATION", "TEST_VECTOR", "FIXTURE_NONLIVE"}:
        raise ComputationControlError(
            "FIXTURE_REQUIREMENT_CONTEXT_OUTSIDE_FIXTURE_MODE",
            str(context.get("mode")),
        )
    return context


def _external_input_contract(
    plan: ResolvedDecisionPlanV1,
) -> dict[str, Mapping[str, Any]]:
    contract: dict[str, Mapping[str, Any]] = {}
    for node in plan.topological_nodes:
        schema = _schema_map(node.definition.get("input_schema", ()))
        dependency_names = {
            str(requirement["consumer_input_name"])
            for requirement in node.requirement_inputs
        }
        parameter_policy = _thaw(node.parameter_policy)
        defaults = (
            parameter_policy.get("defaults", parameter_policy.get("values", {}))
            if isinstance(parameter_policy, Mapping)
            else {}
        )
        default_names = (
            {str(name) for name in defaults} if isinstance(defaults, Mapping) else set()
        )
        for name in sorted(set(schema) - dependency_names - default_names):
            prior = contract.get(name)
            if prior is not None and _canonical_value(prior) != _canonical_value(
                schema[name]
            ):
                raise ComputationControlError(
                    "INCOMPATIBLE_SHARED_EXTERNAL_INPUT_CONTRACT", name
                )
            contract[name] = schema[name]
    return contract


def _project_fallback_inputs(
    plan: ResolvedDecisionPlanV1,
    available_input_locks: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for name, spec in _external_input_contract(plan).items():
        lock = available_input_locks.get(name)
        if not isinstance(lock, Mapping) or "value" not in lock:
            raise ComputationControlError(
                "MISSING_FALLBACK_INPUT_MAPPING",
                f"{plan.root_component_id}: {name}",
            )
        supplied_unit = str(lock.get("unit", _schema_unit(spec)))
        if not _units_compatible(supplied_unit, _schema_unit(spec), "IDENTITY"):
            raise ComputationControlError(
                "FALLBACK_INPUT_UNIT_MISMATCH",
                f"{plan.root_component_id}.{name}: {supplied_unit} -> {_schema_unit(spec)}",
            )
        projected[name] = {
            "value": _thaw(lock["value"]),
            "unit": supplied_unit,
            "lineage": _thaw(lock.get("lineage", {})),
        }
        if lock.get("as_of") is not None:
            projected[name]["as_of"] = lock["as_of"]
    return projected


@dataclass
class _PlanNodeWork:
    token: str
    key: tuple[str, str]
    record: Mapping[str, Any]
    binding: Mapping[str, Any]
    implementation_version: str
    callable_ref: str
    implementation: Mapping[str, Any]
    context: Mapping[str, Any]
    requirements: list[dict[str, Any]]


class _DecisionComputationRegistryV1:
    """Private holder for exactly one immutable logical-registry snapshot."""

    def __init__(self, snapshot: _RegistrySnapshot) -> None:
        self._snapshot = snapshot
        self._lock = threading.RLock()

    def pin(self) -> _RegistrySnapshot:
        with self._lock:
            return self._snapshot

    def swap(self, expected_generation: int, replacement: _RegistrySnapshot) -> None:
        with self._lock:
            if self._snapshot.generation != expected_generation:
                raise ComputationControlError(
                    "CONCURRENT_REGISTRY_WRITER",
                    f"expected generation {expected_generation}, found {self._snapshot.generation}",
                )
            self._snapshot = replacement


class QKUComputationControlPlaneV1:
    """The single public runtime object for decision computation."""

    def __init__(
        self,
        registry_root: str | Path | None = None,
        *,
        records: Iterable[Mapping[str, Any]] | None = None,
        implementation_allowlist: Mapping[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
        trusted_memoizable_refs: Iterable[str] | None = None,
    ) -> None:
        if registry_root is not None and records is not None:
            raise ValueError("choose registry_root or records, not both")
        if implementation_allowlist is not None and records is None:
            raise ValueError(
                "implementation injection is limited to explicit in-memory validation registries"
            )
        if trusted_memoizable_refs is not None and records is None:
            raise ValueError(
                "memoization capability injection is limited to explicit in-memory validation registries"
            )
        load_started = time.perf_counter()
        if records is not None:
            loaded_records = [dict(record) for record in records]
            layout_info = {"layout": "IN_MEMORY", "files_read": 0, "shard_count": 0}
        else:
            root = Path(registry_root) if registry_root is not None else (
                Path(__file__).resolve().parents[3]
                / "docs"
                / "master_plan"
                / "generated"
                / "pr169_qku_comp_control1"
            )
            loaded_records, layout_info = _load_logical_registry(root)
        snapshot = _build_snapshot(
            loaded_records,
            generation=1,
            layout=str(layout_info["layout"]),
            shard_count=int(layout_info["shard_count"]),
            registry_file_reads=int(layout_info["files_read"]),
        )
        self._registry = _DecisionComputationRegistryV1(snapshot)
        trusted = _default_implementation_allowlist()
        trusted_memoizable = set(trusted)
        if implementation_allowlist:
            for ref, implementation in implementation_allowlist.items():
                if not callable(implementation):
                    raise TypeError(f"implementation is not callable: {ref}")
                trusted[str(ref)] = implementation
        requested_memoizable = {
            str(value) for value in (trusted_memoizable_refs or ())
        }
        unknown_memoizable = requested_memoizable - set(trusted)
        if unknown_memoizable:
            raise ValueError(
                f"UNKNOWN_TRUSTED_MEMOIZABLE_REF: {sorted(unknown_memoizable)}"
            )
        trusted_memoizable.update(requested_memoizable)
        self._implementation_allowlist = MappingProxyType(trusted)
        self._trusted_memoizable_refs = frozenset(trusted_memoizable)
        self._counter_lock = threading.Lock()
        self._request_sequence = 0
        self._receipt_sequence = 0
        self._diagnostic_state: dict[str, Any] = {
            "initial_registry_file_reads": snapshot.registry_file_reads,
            "runtime_registry_file_reads_after_initialization": 0,
            "per_request_full_registry_iterations": 0,
            "unrelated_component_executions": 0,
            "requests": 0,
            "records_examined_last_request": 0,
            "nodes_executed_last_request": 0,
            "shared_invocations_reused_last_request": 0,
            "implementation_call_counts": defaultdict(int),
            "layout": snapshot.layout,
            "shard_count": snapshot.shard_count,
            "registry_rows": len(snapshot.records),
            "load_and_index_ms": (time.perf_counter() - load_started) * 1_000,
            "last_incremental_refresh": None,
        }

    def _next_request_id(self, generation: int) -> str:
        with self._counter_lock:
            self._request_sequence += 1
            self._diagnostic_state["requests"] += 1
            return f"plan-{generation}-{self._request_sequence}"

    def _next_receipt_id(self, generation: int, *, node: bool = False) -> str:
        with self._counter_lock:
            self._receipt_sequence += 1
            prefix = "node-receipt" if node else "receipt"
            return f"{prefix}-{generation}-{self._receipt_sequence}"

    def _diagnostics(self) -> dict[str, Any]:
        result = dict(self._diagnostic_state)
        result["implementation_call_counts"] = dict(result["implementation_call_counts"])
        result["current_generation"] = self._registry.pin().generation
        return result

    def _fallback_plan_is_memoizable(
        self, plan: ResolvedDecisionPlanV1
    ) -> bool:
        for node in plan.topological_nodes:
            implementation = next(
                (
                    value
                    for value in node.definition.get("implementation_versions", ())
                    if str(value.get("implementation_version"))
                    == node.implementation_version
                ),
                {},
            )
            if not (
                bool(
                    implementation.get(
                        "memoizable",
                        implementation.get("memoizable_flag", False),
                    )
                )
                and node.callable_or_solver_ref in self._trusted_memoizable_refs
            ):
                return False
        return True

    @staticmethod
    def _fallback_invocation_key(
        plan: ResolvedDecisionPlanV1,
        projected_inputs: Mapping[str, Any],
        *,
        agent_id: str | None,
        consumer: str,
        mode: str,
    ) -> Any:
        return _canonical_value(
            {
                "generation": plan.generation,
                "root": (
                    plan.root_component_id,
                    plan.root_semantic_version,
                    plan.root_binding_id,
                ),
                "nodes": [
                    {
                        "component": node.canonical_component_id,
                        "semantic_version": node.semantic_version,
                        "binding": node.binding_id,
                        "implementation": node.implementation_version,
                        "parameter_policy": node.parameter_policy,
                        "context": node.context,
                    }
                    for node in plan.topological_nodes
                ],
                "inputs": projected_inputs,
                "agent": agent_id,
                "consumer": consumer,
                "mode": mode,
            }
        )

    def _record_key_from_selector(
        self,
        snapshot: _RegistrySnapshot,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> tuple[str, str]:
        indexes = snapshot.indexes
        semantic_version: str | None = None
        candidate_keys: tuple[tuple[str, str], ...] = ()
        if isinstance(selector, Mapping):
            if selector.get("semantic_version"):
                semantic_version = str(selector["semantic_version"])
            if selector.get("canonical_component_id") or selector.get("stack_root"):
                component_id = str(selector.get("canonical_component_id") or selector.get("stack_root"))
                candidate_keys = indexes.record_keys_by_id.get(component_id, ())
            elif selector.get("alias"):
                alias_key = indexes.direct_aliases.get(str(selector["alias"]))
                candidate_keys = (alias_key,) if alias_key else ()
            elif selector.get("qku_id"):
                qku_id = str(selector["qku_id"])
                role = str(selector.get("role_or_decision_stage", context.get("role_or_decision_stage", "ANY")))
                market = str(selector.get("market_family", context.get("market_family", "ANY")))
                candidate_keys = indexes.qku_context_roots.get((qku_id, role, market), ())
                if not candidate_keys:
                    candidate_keys = indexes.qku_roots.get(qku_id, ())
            elif selector.get("decision_role"):
                candidate_keys = indexes.decision_role_candidates.get(str(selector["decision_role"]), ())
            elif selector.get("family"):
                candidate_keys = indexes.family_candidates.get(str(selector["family"]), ())
        else:
            text = str(selector)
            if "@" in text:
                component_id, semantic_version = text.rsplit("@", 1)
                candidate_keys = indexes.record_keys_by_id.get(component_id, ())
            elif text in indexes.record_keys_by_id:
                candidate_keys = indexes.record_keys_by_id[text]
            elif text in indexes.direct_aliases:
                candidate_keys = (indexes.direct_aliases[text],)
            elif text in indexes.qku_roots:
                candidate_keys = indexes.qku_roots[text]
            elif text in indexes.decision_role_candidates:
                candidate_keys = indexes.decision_role_candidates[text]
            elif text in indexes.family_candidates:
                candidate_keys = indexes.family_candidates[text]
        unique = []
        seen: set[tuple[str, str]] = set()
        for key in candidate_keys:
            if key not in indexes.records_by_key:
                alternatives = indexes.record_keys_by_id.get(key[0], ())
                if len(alternatives) == 1:
                    key = alternatives[0]
                else:
                    continue
            if key in seen:
                continue
            record = indexes.records_by_key[key]
            if record.get("record_state") not in ACTIVE_RECORD_STATES:
                continue
            if semantic_version is not None and key[1] != semantic_version:
                continue
            unique.append(key)
            seen.add(key)
        requested_root = context.get("root_component_id")
        if requested_root:
            unique = [key for key in unique if key[0] == str(requested_root)]
        if not unique:
            raise ComputationControlError("SELECTOR_NOT_RESOLVED", _stable_json(selector))
        if len(unique) != 1:
            raise ComputationControlError(
                "AMBIGUOUS_SELECTOR",
                f"selector resolves to {[f'{key[0]}@{key[1]}' for key in unique]}; provide an exact root/version/context",
            )
        return unique[0]

    def _enforce_agent(
        self,
        binding: Mapping[str, Any],
        *,
        agent_id: str | None,
        operation: str,
        mode: str,
    ) -> None:
        mode_state = binding.get("mode_state", {})
        if not isinstance(mode_state, Mapping) or mode not in mode_state:
            raise ComputationControlError(
                "MODE_STATE_MISSING", f"{binding['binding_id']}: {mode}"
            )
        # Eligibility and authorization are reported as plan blockers.  This
        # keeps status/resolve truthful while compute still fails closed.
        if agent_id is None:
            return
        policy = binding.get("agent_access_policy", {})
        entry = policy.get(agent_id) if isinstance(policy, Mapping) else None
        if not isinstance(entry, Mapping):
            raise ComputationControlError("AGENT_ACCESS_DENIED", f"{agent_id} has no policy for {binding['binding_id']}")
        operations = entry.get("control_plane_operations", entry.get("allowed_operations", ()))
        if operation not in {str(value) for value in operations}:
            raise ComputationControlError("AGENT_OPERATION_DENIED", f"{agent_id}: {operation}")
        ceiling = str(entry.get("mode_ceiling", "STATIC_VALIDATION"))
        requested_rank = MODE_ORDER.get(mode)
        ceiling_rank = MODE_ORDER.get(ceiling)
        if requested_rank is None or ceiling_rank is None or requested_rank > ceiling_rank:
            raise ComputationControlError("AGENT_MODE_ESCALATION", f"{agent_id}: {mode} exceeds {ceiling}")

    def _resolve_on_snapshot(
        self,
        snapshot: _RegistrySnapshot,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        agent_id: str | None,
        operation: str,
        _fallback_validation_stack: tuple[str, ...] = (),
    ) -> ResolvedDecisionPlanV1:
        root_key = self._record_key_from_selector(snapshot, selector, context)
        if root_key[0] in _fallback_validation_stack:
            raise ComputationControlError(
                "FALLBACK_CYCLE",
                " -> ".join((*_fallback_validation_stack, root_key[0])),
            )
        fallback_validation_stack = (*_fallback_validation_stack, root_key[0])
        mode = str(context.get("mode", "STATIC_VALIDATION"))
        work_nodes: list[_PlanNodeWork] = []
        blockers: list[str] = []
        token_counter = 0
        shared_node_tokens: dict[Any, str] = {}

        def expand(
            key: tuple[str, str],
            stack: tuple[tuple[str, str], ...],
            selection_context: Mapping[str, Any],
        ) -> str:
            nonlocal token_counter
            if key in stack:
                raise ComputationControlError("REQUIREMENT_CYCLE", " -> ".join(value[0] for value in (*stack, key)))
            record = snapshot.indexes.records_by_key.get(key)
            if record is None:
                raise ComputationControlError("MISSING_REQUIREMENT", f"{key[0]}@{key[1]}")
            binding = _select_binding(
                record,
                selection_context,
                indexes=snapshot.indexes,
                record_key=key,
            )
            node_context = _pinned_node_context(
                selection_context,
                component_id=key[0],
                binding=binding,
            )
            node_mode = str(node_context.get("mode", mode))
            self._enforce_agent(
                binding,
                agent_id=agent_id,
                operation=operation,
                mode=node_mode,
            )
            implementation_version, callable_ref, implementation = _selected_implementation(record, binding)
            memoizable = bool(
                implementation.get(
                    "memoizable", implementation.get("memoizable_flag", False)
                )
            ) and callable_ref in self._trusted_memoizable_refs
            shared_key = (
                key,
                str(binding["binding_id"]),
                implementation_version,
                _canonical_value(binding.get("selected_parameter_policy", {})),
                _canonical_value(node_context),
                _canonical_value(
                    implementation.get(
                        "determinism_seed_policy",
                        implementation.get("determinism_or_seed_policy"),
                    )
                ),
            )
            if memoizable and shared_key in shared_node_tokens:
                return shared_node_tokens[shared_key]
            if record.get("record_state") != "CANONICAL_ACCEPTED":
                blockers.append(
                    f"RECORD_NOT_CANONICAL_ACCEPTED: {key[0]}@{key[1]}"
                )
            if callable_ref and callable_ref not in self._implementation_allowlist:
                blockers.append(f"UNALLOWLISTED_IMPLEMENTATION: {callable_ref}")
            requirement_links: list[dict[str, Any]] = []
            for requirement in snapshot.indexes.requirements_by_record.get(key, ()):
                activation = requirement.get("activation_condition")
                if activation == "NEVER":
                    continue
                if isinstance(activation, Mapping):
                    field_name = str(activation.get("context_field", ""))
                    if field_name and _canonical_value(node_context.get(field_name)) != _canonical_value(activation.get("equals")):
                        continue
                target_id = str(requirement["required_component_id_or_source_selector"])
                for alternative in binding.get("selected_requirement_alternatives", ()):
                    if str(alternative.get("requirement_role")) == str(
                        requirement.get("requirement_role")
                    ):
                        target_id = str(alternative["selected_component_id"])
                        break
                selected_declared_fallback = bool(
                    requirement.get("fallback_component_id_or_null")
                    and target_id
                    == str(requirement.get("fallback_component_id_or_null"))
                )
                producer_context = _derive_requirement_context(
                    node_context,
                    consumer_binding=binding,
                    requirement=requirement,
                    target_component_id=target_id,
                )
                try:
                    target_key = _semantic_version_for_constraint(
                        snapshot.indexes,
                        target_id,
                        str(requirement["required_semantic_version_constraint"]),
                    )
                except ComputationControlError:
                    fallback = requirement.get("fallback_component_id_or_null")
                    if fallback:
                        target_key = _semantic_version_for_constraint(snapshot.indexes, str(fallback), "ANY")
                        fallback_selected = True
                    elif requirement.get("required_or_optional") == "OPTIONAL":
                        continue
                    else:
                        raise
                else:
                    fallback_selected = selected_declared_fallback
                producer = snapshot.indexes.records_by_key[target_key]
                _validate_requirement_ports(record, producer, requirement)
                declared_fallback = requirement.get("fallback_component_id_or_null")
                if declared_fallback and not fallback_selected:
                    fallback_key = _semantic_version_for_constraint(
                        snapshot.indexes, str(declared_fallback), "ANY"
                    )
                    fallback_record = snapshot.indexes.records_by_key[fallback_key]
                    _validate_requirement_ports(record, fallback_record, requirement)
                    fallback_context = {
                        **producer_context,
                        "component_id": fallback_key[0],
                        "canonical_component_id": fallback_key[0],
                    }
                    fallback_plan = self._resolve_on_snapshot(
                        snapshot,
                        {
                            "canonical_component_id": fallback_key[0],
                            "semantic_version": fallback_key[1],
                        },
                        fallback_context,
                        agent_id=agent_id,
                        operation=operation,
                        _fallback_validation_stack=fallback_validation_stack,
                    )
                    fallback_root = fallback_plan.topological_nodes[-1]
                    fallback_binding = fallback_root.binding
                    fallback_version = fallback_root.implementation_version
                    fallback_ref = fallback_root.callable_or_solver_ref
                    blockers.extend(
                        f"FALLBACK_NOT_READY: {fallback_key[0]}@{fallback_version}: {value}"
                        for value in fallback_plan.blockers
                    )
                producer_context["component_id"] = target_key[0]
                producer_context["canonical_component_id"] = target_key[0]
                producer_token = expand(target_key, (*stack, key), producer_context)
                requirement_links.append(
                    {
                        **_thaw(requirement),
                        "producer_node_token": producer_token,
                        "producer_component_id": target_key[0],
                        "producer_semantic_version": target_key[1],
                        "producer_context": _thaw(producer_context),
                        "fallback_selected": fallback_selected,
                        "fallback_pin": (
                            {
                                "canonical_component_id": fallback_key[0],
                                "semantic_version": fallback_key[1],
                                "binding_id": str(fallback_binding["binding_id"]),
                                "implementation_version": fallback_version,
                                "callable_or_solver_ref": fallback_ref,
                                "context": _thaw(
                                    _pinned_node_context(
                                        {
                                            **producer_context,
                                            "component_id": fallback_key[0],
                                            "canonical_component_id": fallback_key[0],
                                        },
                                        component_id=fallback_key[0],
                                        binding=fallback_binding,
                                    )
                                ),
                            }
                            if declared_fallback and not fallback_selected
                            else None
                        ),
                    }
                )
            token_counter += 1
            token = f"work-{token_counter:06d}"
            work_nodes.append(
                _PlanNodeWork(
                    token=token,
                    key=key,
                    record=record,
                    binding=binding,
                    implementation_version=implementation_version,
                    callable_ref=callable_ref,
                    implementation=implementation,
                    context=node_context,
                    requirements=requirement_links,
                )
            )
            if memoizable:
                shared_node_tokens[shared_key] = token
            blockers.extend(_binding_blockers(binding, mode=node_mode))
            if not callable_ref:
                blockers.append(f"MISSING_IMPLEMENTATION: {key[0]}@{key[1]}")
            return token

        root_token = expand(root_key, (), context)
        token_to_node_id = {work.token: f"node-{index:06d}" for index, work in enumerate(work_nodes, start=1)}
        resolved_nodes: list[ResolvedNodeV1] = []
        for work in work_nodes:
            requirement_inputs = []
            for requirement in work.requirements:
                copied = dict(requirement)
                copied["producer_node_id"] = token_to_node_id[copied.pop("producer_node_token")]
                requirement_inputs.append(copied)
            resolved_nodes.append(
                ResolvedNodeV1(
                    node_id=token_to_node_id[work.token],
                    canonical_component_id=work.key[0],
                    semantic_version=work.key[1],
                    binding_id=str(work.binding["binding_id"]),
                    implementation_version=work.implementation_version,
                    callable_or_solver_ref=work.callable_ref,
                    parameter_policy=work.binding.get("selected_parameter_policy", {}),
                    context=work.context,
                    requirement_inputs=tuple(requirement_inputs),
                    definition=work.record["definition"],
                    binding=work.binding,
                )
            )
        root_work = next(work for work in work_nodes if work.token == root_token)
        if _fallback_validation_stack:
            plan_id = (
                f"fallback-plan-{snapshot.generation}-"
                f"{len(_fallback_validation_stack)}-{root_key[0]}"
            )
        else:
            plan_id = self._next_request_id(snapshot.generation)
            self._diagnostic_state["records_examined_last_request"] = len(
                resolved_nodes
            )
        fallback_descriptors: list[dict[str, Any]] = [
            {
                "consumer_component_id": node.canonical_component_id,
                "fallback_component_id": requirement.get(
                    "fallback_component_id_or_null"
                ),
                "pin": _thaw(requirement.get("fallback_pin")),
            }
            for node in resolved_nodes
            for requirement in node.requirement_inputs
            if requirement.get("fallback_component_id_or_null")
        ]
        for node in resolved_nodes:
            fallback_policy = node.binding.get("fallback_policy", {})
            fallback_behavior = str(
                fallback_policy.get(
                    "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                )
            )
            if not fallback_behavior.startswith("USE_FALLBACK"):
                continue
            fallback_id = str(
                fallback_policy.get(
                    "fallback_component_id", fallback_policy.get("component_id", "")
                )
            )
            fallback_key = _semantic_version_for_constraint(
                snapshot.indexes, fallback_id, "ANY"
            )
            fallback_context = _thaw(node.context)
            for context_field in (
                "binding_id",
                "binding_as_of_policy",
                "binding_point_in_time_policy",
                "binding_freshness_and_TTL",
            ):
                fallback_context.pop(context_field, None)
            fallback_context["component_id"] = fallback_key[0]
            fallback_context["canonical_component_id"] = fallback_key[0]
            fallback_plan = self._resolve_on_snapshot(
                snapshot,
                {
                    "canonical_component_id": fallback_key[0],
                    "semantic_version": fallback_key[1],
                },
                fallback_context,
                agent_id=agent_id,
                operation=operation,
                _fallback_validation_stack=fallback_validation_stack,
            )
            fallback_root = fallback_plan.topological_nodes[-1]
            fallback_binding = fallback_root.binding
            fallback_version = fallback_root.implementation_version
            fallback_ref = fallback_root.callable_or_solver_ref
            blockers.extend(
                f"FALLBACK_NOT_READY: {fallback_key[0]}@{fallback_version}: {value}"
                for value in fallback_plan.blockers
            )
            fallback_descriptors.append(
                {
                    "consumer_component_id": node.canonical_component_id,
                    "fallback_component_id": fallback_key[0],
                    "pin": {
                        "canonical_component_id": fallback_key[0],
                        "semantic_version": fallback_key[1],
                        "binding_id": str(fallback_binding["binding_id"]),
                        "implementation_version": fallback_version,
                        "callable_or_solver_ref": fallback_ref,
                        "context": _thaw(fallback_root.context),
                    },
                }
            )
        return ResolvedDecisionPlanV1(
            plan_id=plan_id,
            generation=snapshot.generation,
            root_component_id=root_key[0],
            root_semantic_version=root_key[1],
            root_binding_id=str(root_work.binding["binding_id"]),
            decision_roles=tuple(str(value) for value in snapshot.indexes.records_by_key[root_key]["uses"].get("decision_roles", ())),
            context=context,
            topological_nodes=tuple(resolved_nodes),
            blockers=tuple(dict.fromkeys(blockers)),
            fallback_paths=tuple(fallback_descriptors),
        )

    def resolve(
        self,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> ResolvedDecisionPlanV1:
        snapshot = self._registry.pin()
        return self._resolve_on_snapshot(
            snapshot,
            selector,
            dict(context or {}),
            agent_id=agent_id,
            operation="resolve",
        )

    @staticmethod
    def _typed_input(
        name: str,
        raw: Any,
        *,
        expected_spec: Mapping[str, Any] | None,
        context: Mapping[str, Any],
    ) -> tuple[Any, str, Any]:
        unit = None
        lineage = None
        as_of = None
        value = raw
        declared_type = str((expected_spec or {}).get("type", "ANY")).upper()
        expects_mapping_value = any(
            token in declared_type
            for token in ("OBJECT", "MAPPING", "DICT", "RECORD", "STRUCTURE")
        )
        explicitly_typed = isinstance(raw, Mapping) and raw.get(
            "__qtt_typed_input_v1__"
        ) is True
        legacy_typed = (
            isinstance(raw, Mapping)
            and "value" in raw
            and not expects_mapping_value
        )
        if explicitly_typed or legacy_typed:
            if "value" not in raw:
                raise ComputationControlError("TYPED_INPUT_VALUE_REQUIRED", name)
            value = raw["value"]
            unit = raw.get("unit")
            lineage = raw.get("lineage")
            as_of = raw.get("as_of")
        if unit is None:
            unit = context.get("input_units", {}).get(name) if isinstance(context.get("input_units"), Mapping) else None
        if lineage is None:
            lineage = context.get("input_lineage", {}).get(name) if isinstance(context.get("input_lineage"), Mapping) else None
        if lineage is None:
            if str(context.get("mode", "STATIC_VALIDATION")) not in {
                "STATIC_VALIDATION",
                "TEST_VECTOR",
                "FIXTURE_NONLIVE",
            }:
                raise ComputationControlError("MISSING_INPUT_LINEAGE", name)
            lineage = "STATIC_VALIDATION_CALLER_PROVIDED"
        expected_unit = _schema_unit(expected_spec)
        if expected_unit not in {"UNSPECIFIED", "ANY"}:
            if unit is None:
                raise ComputationControlError("MISSING_UNIT", f"{name} requires {expected_unit}")
            if str(unit) != expected_unit:
                raise ComputationControlError("UNIT_MISMATCH", f"{name}: {unit} != {expected_unit}")
        unit = str(unit or expected_unit)
        tokens = {token for token in re.split(r"[^A-Z0-9]+", expected_unit.upper()) if token}
        if tokens & MONEY_UNIT_TOKENS and isinstance(value, float):
            raise ComputationControlError("BINARY_FLOAT_MONEY_BOUNDARY", name)
        if context.get("require_input_as_of") and not as_of:
            raise ComputationControlError("MISSING_INPUT_AS_OF", name)
        if as_of:
            request_time = context.get("request_time")
            if request_time is None:
                raise ComputationControlError("MISSING_REQUEST_TIME", name)
            try:
                observed = datetime.fromisoformat(str(as_of).replace("Z", "+00:00"))
                requested = datetime.fromisoformat(str(request_time).replace("Z", "+00:00"))
            except ValueError as exc:
                raise ComputationControlError("INVALID_AS_OF", name) from exc
            if observed.tzinfo is None or requested.tzinfo is None:
                raise ComputationControlError("NAIVE_AS_OF_FORBIDDEN", name)
            age_seconds = (requested - observed).total_seconds()
            if age_seconds < 0:
                raise ComputationControlError("FUTURE_INPUT_AS_OF", name)
            ttl = context.get("freshness_ttl_seconds")
            if ttl is not None and age_seconds > float(ttl):
                raise ComputationControlError("STALE_INPUT", name)
        _validate_schema_value(value, expected_spec, path=name)
        return value, unit, lineage

    def compute(
        self,
        selector: str | Mapping[str, Any],
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
        consumer: str = "UNSPECIFIED",
        mode: str | None = None,
    ) -> ComputationReceiptV1:
        snapshot = self._registry.pin()
        return self._compute_on_snapshot(
            snapshot,
            selector,
            inputs,
            context,
            agent_id=agent_id,
            consumer=consumer,
            mode=mode,
        )

    def _compute_on_snapshot(
        self,
        snapshot: _RegistrySnapshot,
        selector: str | Mapping[str, Any],
        inputs: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
        consumer: str = "UNSPECIFIED",
        mode: str | None = None,
        _fallback_chain: tuple[str, ...] = (),
        _resolved_plan: ResolvedDecisionPlanV1 | None = None,
        _fallback_memo: dict[Any, ComputationReceiptV1] | None = None,
    ) -> ComputationReceiptV1:
        for forbidden in ("expected_result", "expected_outputs", "caller_result"):
            if forbidden in inputs:
                raise ComputationControlError("CALLER_RESULT_PASSTHROUGH", forbidden)
        request_context = dict(context or {})
        selected_mode = str(mode or request_context.get("mode", "STATIC_VALIDATION"))
        request_context["mode"] = selected_mode
        plan = _resolved_plan or self._resolve_on_snapshot(
            snapshot,
            selector,
            request_context,
            agent_id=agent_id,
            operation="compute",
        )
        if plan.generation != snapshot.generation:
            raise ComputationControlError(
                "MIXED_REGISTRY_GENERATION",
                f"plan={plan.generation}, snapshot={snapshot.generation}",
            )
        if plan.blockers:
            raise ComputationControlError("PLAN_NOT_READY", "; ".join(plan.blockers), component_id=plan.root_component_id)
        if plan.root_component_id in _fallback_chain:
            raise ComputationControlError(
                "FALLBACK_CYCLE",
                " -> ".join((*_fallback_chain, plan.root_component_id)),
            )
        next_fallback_chain = (*_fallback_chain, plan.root_component_id)
        fallback_memo = _fallback_memo if _fallback_memo is not None else {}
        fixture_modes = {
            "STATIC_VALIDATION",
            "TEST_VECTOR",
            "FIXTURE_NONLIVE",
        }
        nonfixture_nodes = tuple(
            node
            for node in plan.topological_nodes
            if str(node.context.get("mode", selected_mode)) not in fixture_modes
        )
        if nonfixture_nodes and agent_id is None:
            if not consumer or consumer == "UNSPECIFIED":
                raise ComputationControlError(
                    "AGENT_OR_CONSUMER_REQUIRED",
                    f"{plan.root_component_id}: {selected_mode}",
                )
            for node in nonfixture_nodes:
                record = snapshot.indexes.records_by_key[
                    (node.canonical_component_id, node.semantic_version)
                ]
                record_consumers = {
                    str(value)
                    for value in record["uses"].get("consumer_class_tags", ())
                }
                binding_consumers = {
                    str(value)
                    for value in node.binding.get("downstream_consumer_classes", ())
                }
                if consumer not in record_consumers or consumer not in binding_consumers:
                    raise ComputationControlError(
                        "UNTRUSTED_CONSUMER",
                        f"{consumer}: {node.canonical_component_id}",
                    )

        external_input_names = set(_external_input_contract(plan))
        pinned_parameter_names: set[str] = set()
        for node in plan.topological_nodes:
            parameter_policy = _thaw(node.parameter_policy)
            defaults = (
                parameter_policy.get("defaults", parameter_policy.get("values", {}))
                if isinstance(parameter_policy, Mapping)
                else {}
            )
            default_names = (
                {str(name) for name in defaults} if isinstance(defaults, Mapping) else set()
            )
            pinned_parameter_names.update(default_names)
        unexpected_inputs = sorted(set(inputs) - external_input_names)
        if unexpected_inputs:
            if set(unexpected_inputs).intersection(pinned_parameter_names):
                raise ComputationControlError(
                    "PINNED_PARAMETER_OVERRIDE", str(unexpected_inputs)
                )
            raise ComputationControlError("UNDECLARED_INPUT", str(unexpected_inputs))
        started_clock = time.perf_counter()
        started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        global_values = dict(inputs)
        node_outputs: dict[str, Mapping[str, Any]] = {}
        node_receipt_ids: dict[str, str] = {}
        node_lineage: dict[str, Any] = {}
        node_input_locks: dict[str, dict[str, Mapping[str, Any]]] = {}
        memo: dict[Any, tuple[Mapping[str, Any], str]] = {}
        executed = 0
        node_errors: dict[str, ComputationControlError] = {}
        runtime_fallback_receipts: dict[Any, ComputationReceiptV1] = {}
        runtime_fallback_receipt_entries: list[dict[str, Any]] = []
        runtime_fallback_used = False
        runtime_requirement_fallbacks: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        inbound_references: dict[str, int] = defaultdict(int)
        for resolved_node in plan.topological_nodes:
            for requirement in resolved_node.requirement_inputs:
                inbound_references[str(requirement["producer_node_id"])] += 1
                if (
                    str(requirement.get("failure_behavior", "")).startswith(
                        "USE_FALLBACK"
                    )
                    and requirement.get("fallback_component_id_or_null")
                    and not requirement.get("fallback_selected")
                ):
                    runtime_requirement_fallbacks[
                        str(requirement["producer_node_id"])
                    ].append(requirement)
        reused = sum(
            count - 1 for count in inbound_references.values() if count > 1
        )
        warnings: list[str] = []

        for node in plan.topological_nodes:
            schema = _schema_map(node.definition.get("input_schema", ()))
            node_inputs: dict[str, Any] = {}
            input_units: dict[str, str] = {}
            input_lineage: dict[str, Any] = {}
            typed_context = _thaw(node.context)
            node_mode = str(typed_context.get("mode", selected_mode))
            freshness_policy = node.binding.get("freshness_and_TTL", {})
            if isinstance(freshness_policy, Mapping):
                binding_ttl = freshness_policy.get(
                    "ttl_seconds", freshness_policy.get("TTL_seconds")
                )
                if binding_ttl is not None:
                    typed_context["freshness_ttl_seconds"] = binding_ttl
            if node_mode not in fixture_modes:
                point_policy = " ".join(
                    (
                        str(node.binding.get("as_of_policy", "")),
                        str(node.binding.get("point_in_time_policy", "")),
                    )
                ).upper()
                typed_context["require_input_as_of"] = not any(
                    token in point_policy
                    for token in ("NOT_REQUIRED", "TIME_INVARIANT", "IMMUTABLE")
                )
            parameter_policy = _thaw(node.parameter_policy)
            defaults = parameter_policy.get("defaults", parameter_policy.get("values", {})) if isinstance(parameter_policy, Mapping) else {}
            parameter_schema = _parameter_schema_map(
                node.definition.get("parameter_schema_and_default_provenance", ())
            )
            if isinstance(defaults, Mapping):
                for name, value in defaults.items():
                    parameter_name = str(name)
                    parameter_spec = parameter_schema.get(
                        parameter_name, schema.get(parameter_name)
                    )
                    if parameter_spec is not None:
                        _validate_schema_value(
                            value,
                            parameter_spec,
                            path=f"{node.canonical_component_id}.parameter.{parameter_name}",
                        )
                    node_inputs[parameter_name] = value
                    input_units[parameter_name] = _schema_unit(parameter_spec)
                    input_lineage[parameter_name] = {
                        "source": "PINNED_PARAMETER_POLICY",
                        "policy": parameter_policy.get("policy_id", parameter_policy.get("version", "PINNED")),
                    }
            dependency_input_names: set[str] = set()
            upstream_identity: list[Any] = []
            for requirement in node.requirement_inputs:
                producer_node_id = str(requirement["producer_node_id"])
                producer_output = str(requirement["producer_output_name"])
                consumer_input = str(requirement["consumer_input_name"])
                selected_receipt_ref = node_receipt_ids.get(producer_node_id)
                if producer_node_id in node_errors:
                    if not str(requirement.get("failure_behavior", "")).startswith(
                        "USE_FALLBACK"
                    ):
                        raise node_errors[producer_node_id]
                    fallback_component_id = str(
                        requirement.get("fallback_component_id_or_null", "")
                    )
                    if not fallback_component_id:
                        raise node_errors[producer_node_id]
                    fallback_context = _thaw(
                        requirement.get("producer_context", node.context)
                    )
                    fallback_context["component_id"] = fallback_component_id
                    fallback_context["canonical_component_id"] = fallback_component_id
                    fallback_mode = str(
                        fallback_context.get("mode", selected_mode)
                    )
                    fallback_plan = self._resolve_on_snapshot(
                        snapshot,
                        fallback_component_id,
                        fallback_context,
                        agent_id=agent_id,
                        operation="compute",
                    )
                    expected_pin = requirement.get("fallback_pin")
                    if isinstance(expected_pin, Mapping):
                        fallback_root = fallback_plan.topological_nodes[-1]
                        actual_pin = {
                            "canonical_component_id": fallback_root.canonical_component_id,
                            "semantic_version": fallback_root.semantic_version,
                            "binding_id": fallback_root.binding_id,
                            "implementation_version": fallback_root.implementation_version,
                            "callable_or_solver_ref": fallback_root.callable_or_solver_ref,
                        }
                        for pin_name, pin_value in actual_pin.items():
                            if _canonical_value(expected_pin.get(pin_name)) != _canonical_value(
                                pin_value
                            ):
                                raise ComputationControlError(
                                    "FALLBACK_PLAN_PIN_MISMATCH",
                                    f"{fallback_component_id}.{pin_name}",
                                )
                    projected_inputs = _project_fallback_inputs(
                        fallback_plan,
                        node_input_locks.get(producer_node_id, {}),
                    )
                    fallback_cache_key = self._fallback_invocation_key(
                        fallback_plan,
                        projected_inputs,
                        agent_id=agent_id,
                        consumer=consumer,
                        mode=fallback_mode,
                    )
                    fallback_receipt = (
                        fallback_memo.get(fallback_cache_key)
                        if self._fallback_plan_is_memoizable(fallback_plan)
                        else None
                    )
                    reused_fallback = fallback_receipt is not None
                    if fallback_receipt is None:
                        fallback_receipt = self._compute_on_snapshot(
                            snapshot,
                            fallback_component_id,
                            projected_inputs,
                            fallback_context,
                            agent_id=agent_id,
                            consumer=consumer,
                            mode=fallback_mode,
                            _fallback_chain=next_fallback_chain,
                            _resolved_plan=fallback_plan,
                            _fallback_memo=fallback_memo,
                        )
                        if self._fallback_plan_is_memoizable(fallback_plan):
                            fallback_memo[fallback_cache_key] = fallback_receipt
                    runtime_fallback_receipts[
                        fallback_receipt.receipt_id
                    ] = fallback_receipt
                    runtime_fallback_receipt_entries.append(
                        {
                            "component_id": fallback_component_id,
                            "receipt_ref": fallback_receipt.receipt_id,
                            "receipt_generation": fallback_receipt.generation,
                            "runtime_fallback_for_node_id": producer_node_id,
                            "context": _thaw(fallback_plan.context),
                        }
                    )
                    if reused_fallback:
                        reused += 1
                    else:
                        executed += fallback_receipt.nodes_executed
                        reused += fallback_receipt.shared_invocations_reused
                    if producer_output not in fallback_receipt.outputs:
                        raise ComputationControlError(
                            "MISSING_FALLBACK_OUTPUT",
                            f"{fallback_component_id}.{producer_output}",
                        )
                    value = fallback_receipt.outputs[producer_output]
                    selected_receipt_ref = fallback_receipt.receipt_id
                    runtime_fallback_used = True
                    warnings.append(
                        f"RUNTIME_REQUIREMENT_FALLBACK: {producer_node_id} -> {fallback_component_id}"
                    )
                else:
                    if (
                        producer_node_id not in node_outputs
                        or producer_output not in node_outputs[producer_node_id]
                    ):
                        raise ComputationControlError(
                            "MISSING_REQUIREMENT_OUTPUT",
                            f"{producer_node_id}.{producer_output}",
                        )
                    value = node_outputs[producer_node_id][producer_output]
                value = _apply_unit_conversion(value, requirement.get("unit_or_basis_conversion"))
                if consumer_input in inputs:
                    raise ComputationControlError("DEPENDENCY_INPUT_OVERRIDE", consumer_input)
                node_inputs[consumer_input] = value
                _validate_schema_value(
                    value,
                    schema.get(consumer_input),
                    path=f"{node.canonical_component_id}.requirement.{consumer_input}",
                    output_accounting_class=str(
                        node.definition.get("output_accounting_class", "")
                    ),
                )
                dependency_input_names.add(consumer_input)
                input_units[consumer_input] = _schema_unit(schema.get(consumer_input))
                input_lineage[consumer_input] = {
                    "requirement_receipt_ref": selected_receipt_ref,
                    "producer_output": producer_output,
                }
                upstream_identity.append(
                    (selected_receipt_ref, producer_output, _canonical_value(value))
                )
            for name, spec in schema.items():
                if name in dependency_input_names or name in node_inputs:
                    continue
                if name not in global_values:
                    if bool(spec.get("required", True)):
                        raise ComputationControlError("MISSING_INPUT", name, component_id=node.canonical_component_id)
                    continue
                value, unit, lineage = self._typed_input(
                    name,
                    global_values[name],
                    expected_spec=spec,
                    context=typed_context,
                )
                _validate_input_lineage_binding(
                    lineage,
                    binding=node.binding,
                    input_name=name,
                    mode=node_mode,
                )
                node_inputs[name] = value
                input_units[name] = unit
                input_lineage[name] = lineage
            node_input_locks[node.node_id] = {
                name: {
                    "value": _thaw(value),
                    "unit": input_units.get(name, _schema_unit(schema.get(name))),
                    "lineage": _thaw(input_lineage.get(name, {})),
                    **(
                        {"as_of": global_values[name].get("as_of")}
                        if name in global_values
                        and isinstance(global_values[name], Mapping)
                        and global_values[name].get("as_of") is not None
                        else {}
                    ),
                }
                for name, value in node_inputs.items()
            }
            ref = node.callable_or_solver_ref
            implementation = self._implementation_allowlist.get(ref)
            if implementation is None:
                raise ComputationControlError("UNALLOWLISTED_IMPLEMENTATION", ref, component_id=node.canonical_component_id)
            implementation_entry = next(
                (
                    value
                    for value in node.definition.get("implementation_versions", ())
                    if str(value.get("implementation_version")) == node.implementation_version
                ),
                {},
            )
            memoizable = bool(
                implementation_entry.get(
                    "memoizable", implementation_entry.get("memoizable_flag", False)
                )
            ) and ref in self._trusted_memoizable_refs
            seed_policy = implementation_entry.get("determinism_seed_policy", implementation_entry.get("determinism_or_seed_policy"))
            memo_key = (
                node.canonical_component_id,
                node.semantic_version,
                node.binding_id,
                node.implementation_version,
                _canonical_value(node.parameter_policy),
                _canonical_value(node.context),
                _canonical_value(node_inputs),
                tuple(upstream_identity),
                _canonical_value(seed_policy),
            )
            if memoizable and memo_key in memo:
                outputs, node_receipt_id = memo[memo_key]
                reused += 1
            else:
                used_binding_fallback = False
                try:
                    raw_outputs = implementation(dict(node_inputs))
                except Exception as exc:
                    failure = (
                        exc
                        if isinstance(exc, ComputationControlError)
                        else ComputationControlError(
                        "IMPLEMENTATION_ERROR",
                        f"{node.canonical_component_id}: {type(exc).__name__}: {exc}",
                        component_id=node.canonical_component_id,
                        )
                    )
                    executed += 1
                    self._diagnostic_state["implementation_call_counts"][ref] += 1
                    fallback_policy = node.binding.get("fallback_policy", {})
                    fallback_behavior = str(
                        fallback_policy.get(
                            "behavior", fallback_policy.get("state", "FAIL_CLOSED")
                        )
                    )
                    if fallback_behavior.startswith("USE_FALLBACK"):
                        fallback_component_id = str(
                            fallback_policy.get(
                                "fallback_component_id",
                                fallback_policy.get("component_id", ""),
                            )
                        )
                        fallback_context = _thaw(node.context)
                        for context_field in (
                            "binding_id",
                            "binding_as_of_policy",
                            "binding_point_in_time_policy",
                            "binding_freshness_and_TTL",
                        ):
                            fallback_context.pop(context_field, None)
                        fallback_context["component_id"] = fallback_component_id
                        fallback_context["canonical_component_id"] = fallback_component_id
                        fallback_plan = self._resolve_on_snapshot(
                            snapshot,
                            fallback_component_id,
                            fallback_context,
                            agent_id=agent_id,
                            operation="compute",
                        )
                        expected_descriptor = next(
                            (
                                value
                                for value in plan.fallback_paths
                                if value.get("consumer_component_id")
                                == node.canonical_component_id
                                and value.get("fallback_component_id")
                                == fallback_component_id
                                and isinstance(value.get("pin"), Mapping)
                            ),
                            None,
                        )
                        if expected_descriptor is not None:
                            expected_pin = expected_descriptor["pin"]
                            fallback_root = fallback_plan.topological_nodes[-1]
                            for pin_name, pin_value in {
                                "canonical_component_id": fallback_root.canonical_component_id,
                                "semantic_version": fallback_root.semantic_version,
                                "binding_id": fallback_root.binding_id,
                                "implementation_version": fallback_root.implementation_version,
                                "callable_or_solver_ref": fallback_root.callable_or_solver_ref,
                            }.items():
                                if _canonical_value(expected_pin.get(pin_name)) != _canonical_value(
                                    pin_value
                                ):
                                    raise ComputationControlError(
                                        "FALLBACK_PLAN_PIN_MISMATCH",
                                        f"{fallback_component_id}.{pin_name}",
                                    )
                        projected_inputs = _project_fallback_inputs(
                            fallback_plan,
                            node_input_locks.get(node.node_id, {}),
                        )
                        fallback_cache_key = self._fallback_invocation_key(
                            fallback_plan,
                            projected_inputs,
                            agent_id=agent_id,
                            consumer=consumer,
                            mode=node_mode,
                        )
                        fallback_receipt = (
                            fallback_memo.get(fallback_cache_key)
                            if self._fallback_plan_is_memoizable(fallback_plan)
                            else None
                        )
                        reused_fallback = fallback_receipt is not None
                        if fallback_receipt is None:
                            fallback_receipt = self._compute_on_snapshot(
                                snapshot,
                                fallback_component_id,
                                projected_inputs,
                                fallback_context,
                                agent_id=agent_id,
                                consumer=consumer,
                                mode=node_mode,
                                _fallback_chain=next_fallback_chain,
                                _resolved_plan=fallback_plan,
                                _fallback_memo=fallback_memo,
                            )
                            if self._fallback_plan_is_memoizable(fallback_plan):
                                fallback_memo[fallback_cache_key] = fallback_receipt
                        runtime_fallback_receipts[
                            fallback_receipt.receipt_id
                        ] = fallback_receipt
                        runtime_fallback_receipt_entries.append(
                            {
                                "component_id": fallback_component_id,
                                "receipt_ref": fallback_receipt.receipt_id,
                                "receipt_generation": fallback_receipt.generation,
                                "runtime_fallback_for_node_id": node.node_id,
                                "context": _thaw(fallback_plan.context),
                            }
                        )
                        raw_outputs = fallback_receipt.outputs
                        node_receipt_id = fallback_receipt.receipt_id
                        used_binding_fallback = True
                        if reused_fallback:
                            reused += 1
                        else:
                            executed += fallback_receipt.nodes_executed
                            reused += fallback_receipt.shared_invocations_reused
                        runtime_fallback_used = True
                        warnings.append(
                            f"RUNTIME_BINDING_FALLBACK: {node.canonical_component_id} -> {fallback_component_id}"
                        )
                    elif node.node_id in runtime_requirement_fallbacks:
                        node_errors[node.node_id] = failure
                        warnings.append(
                            f"PRIMARY_REQUIREMENT_FAILED: {node.canonical_component_id}"
                        )
                        continue
                    else:
                        raise failure from exc
                if not isinstance(raw_outputs, Mapping):
                    raise ComputationControlError("INVALID_IMPLEMENTATION_OUTPUT", node.canonical_component_id)
                outputs = dict(raw_outputs)
                declared_outputs = _schema_map(node.definition.get("output_schema", ()))
                missing_outputs = sorted(set(declared_outputs) - set(outputs))
                if missing_outputs:
                    raise ComputationControlError("MISSING_OUTPUT", f"{node.canonical_component_id}: {missing_outputs}")
                extra_outputs = sorted(set(outputs) - set(declared_outputs))
                if extra_outputs:
                    raise ComputationControlError(
                        "UNDECLARED_OUTPUT",
                        f"{node.canonical_component_id}: {extra_outputs}",
                    )
                for output_name, output_spec in declared_outputs.items():
                    _validate_schema_value(
                        outputs[output_name],
                        output_spec,
                        path=f"{node.canonical_component_id}.outputs.{output_name}",
                        output_accounting_class=str(
                            node.definition.get("output_accounting_class", "")
                        ),
                    )
                if not used_binding_fallback:
                    node_receipt_id = self._next_receipt_id(plan.generation, node=True)
                if not used_binding_fallback:
                    executed += 1
                    self._diagnostic_state["implementation_call_counts"][ref] += 1
                if memoizable and not used_binding_fallback:
                    memo[memo_key] = (outputs, node_receipt_id)
            if node.binding.get("readiness", {}).get("oracle") != "PASS":
                warnings.append(f"UNVERIFIED_STATIC_INVOCATION: {node.canonical_component_id}")
            node_outputs[node.node_id] = outputs
            node_receipt_ids[node.node_id] = node_receipt_id
            node_lineage[node.node_id] = input_lineage

        root_node = plan.topological_nodes[-1]
        root_outputs = node_outputs[root_node.node_id]
        ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        latency_ms = (time.perf_counter() - started_clock) * 1_000
        output_schema = _schema_map(root_node.definition.get("output_schema", ()))
        output_units = {name: _schema_unit(spec) for name, spec in output_schema.items()}
        requirement_receipts = tuple(
            {
                "node_id": node.node_id,
                "component_id": node.canonical_component_id,
                "receipt_ref": node_receipt_ids[node.node_id],
                "receipt_generation": plan.generation,
                "context": _thaw(node.context),
                "shared_ref": inbound_references.get(node.node_id, 0) > 1,
            }
            for node in plan.topological_nodes
            if node.node_id in node_receipt_ids
        ) + tuple(runtime_fallback_receipt_entries)
        if any(
            receipt.generation != plan.generation
            for receipt in runtime_fallback_receipts.values()
        ):
            raise ComputationControlError(
                "MIXED_REGISTRY_GENERATION", "runtime fallback generation mismatch"
            )
        self._diagnostic_state["nodes_executed_last_request"] = executed
        self._diagnostic_state["shared_invocations_reused_last_request"] = reused
        self._diagnostic_state["unrelated_component_executions"] = 0
        return ComputationReceiptV1(
            receipt_id=self._next_receipt_id(plan.generation),
            plan_id=plan.plan_id,
            generation=plan.generation,
            component_id=plan.root_component_id,
            decision_roles=plan.decision_roles,
            context_lock=request_context,
            input_values=inputs,
            input_lineage=node_lineage,
            requirement_receipts=requirement_receipts,
            selected_versions={
                "root_node_id": root_node.node_id,
                "nodes": {
                    node.node_id: {
                    "canonical_component_id": node.canonical_component_id,
                    "semantic_version": node.semantic_version,
                    "binding_id": node.binding_id,
                    "binding_version": node.binding.get("binding_version"),
                    "implementation_version": node.implementation_version,
                    "parameter_policy": _thaw(node.parameter_policy),
                    "context": _thaw(node.context),
                    "evidence_state": node.binding.get("readiness", {}).get("evidence"),
                    "activation_state": node.binding.get("activation_state"),
                    "exact_resolution_action": node.binding.get(
                        "exact_resolution_action_or_null"
                    ),
                    "fallback_policy": _thaw(node.binding.get("fallback_policy", {})),
                    "supported_modes": list(node.binding.get("supported_modes", ())),
                    "mode_state": _thaw(node.binding.get("mode_state", {})),
                    "agent_access_policy": _thaw(
                        node.binding.get("agent_access_policy", {})
                    ),
                }
                for node in plan.topological_nodes
                },
                "fallback_receipts": {
                    receipt.receipt_id: _thaw(receipt.selected_versions)
                    for receipt in runtime_fallback_receipts.values()
                },
            },
            started_at=started_at,
            ended_at=ended_at,
            latency_ms=latency_ms,
            outputs=root_outputs,
            output_units=output_units,
            output_accounting_class=str(root_node.definition.get("output_accounting_class", "UNSPECIFIED")),
            fallback_used=runtime_fallback_used or any(
                bool(requirement.get("fallback_selected"))
                for node in plan.topological_nodes
                for requirement in node.requirement_inputs
            ),
            warnings=tuple(dict.fromkeys(warnings)),
            errors=(),
            consumer=consumer,
            mode=selected_mode,
            nodes_executed=executed,
            shared_invocations_reused=reused,
            no_order_authority=True,
        )

    def status(
        self,
        selector: str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        request_context = dict(context or {})
        snapshot = self._registry.pin()
        plan = self._resolve_on_snapshot(
            snapshot,
            selector,
            request_context,
            agent_id=agent_id,
            operation="status",
        )
        key = (plan.root_component_id, plan.root_semantic_version)
        record = snapshot.indexes.records_by_key[key]
        binding = next(value for value in record["bindings"] if value["binding_id"] == plan.root_binding_id)
        return {
            "canonical_component_id": plan.root_component_id,
            "semantic_version": plan.root_semantic_version,
            "record_state": record["record_state"],
            "binding_id": plan.root_binding_id,
            "binding_readiness": _thaw(binding["readiness"]),
            "derived_state": _derived_state(record, binding, plan_ready=plan.ready),
            "selected_implementation_version": binding["selected_implementation_version"],
            "binding_version": binding["binding_version"],
            "selected_parameter_policy": _thaw(binding["selected_parameter_policy"]),
            "context_applicable": True,
            "evidence_ceiling": binding["readiness"]["evidence"],
            "mode_state": _thaw(binding["mode_state"]),
            "authorization": binding["readiness"]["authorization"],
            "activation_state": binding["activation_state"],
            "exact_resolution_action": binding["exact_resolution_action_or_null"],
            "agent_access": _thaw(binding["agent_access_policy"]),
            "fallback": _thaw(binding["fallback_policy"]),
            "requirements_closed": plan.ready,
            "blockers": list(plan.blockers),
            "generation": plan.generation,
            "no_order_authority": True,
        }

    def explain(
        self,
        receipt_or_selector: ComputationReceiptV1 | str | Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(receipt_or_selector, ComputationReceiptV1):
            receipt = receipt_or_selector
            selected_nodes = receipt.selected_versions.get("nodes", {})
            root_node_id = str(receipt.selected_versions.get("root_node_id", ""))
            selected = _thaw(
                selected_nodes.get(root_node_id, {})
                if isinstance(selected_nodes, Mapping)
                else {}
            )
            if not selected or str(selected.get("canonical_component_id")) != str(
                receipt.component_id
            ):
                raise ComputationControlError(
                    "RECEIPT_ROOT_SELECTION_MISSING", receipt.receipt_id
                )
            if agent_id is not None:
                self._enforce_agent(
                    selected,
                    agent_id=agent_id,
                    operation="explain",
                    mode=receipt.mode,
                )
            semantic_version = str(selected.get("semantic_version", ""))
            snapshot = self._registry.pin()
            record = snapshot.indexes.records_by_key.get(
                (receipt.component_id, semantic_version)
            )
            immutable_definition = record.get("definition", {}) if record else {}
            return {
                "receipt_ref": receipt.receipt_id,
                "receipt_generation": receipt.generation,
                "identity": {
                    "canonical_component_id": receipt.component_id,
                    "semantic_version": semantic_version,
                    "record_state_at_explanation": (
                        record.get("record_state") if record else "RETAINED_RECEIPT_ONLY"
                    ),
                    "origin_cohorts": list(record.get("origin_cohorts", ())) if record else [],
                },
                "decision_use": {
                    "decision_roles": list(receipt.decision_roles),
                    "consumer": receipt.consumer,
                    "mode": receipt.mode,
                },
                "provenance": {
                    "input_lineage": _thaw(receipt.input_lineage),
                    "requirement_receipts": _thaw(receipt.requirement_receipts),
                },
                "mathematics_or_procedure": immutable_definition.get(
                    "complete_mathematical_or_procedural_definition"
                ),
                "assumptions": _thaw(immutable_definition.get("assumptions", ())),
                "domain_and_boundary_behavior": _thaw(
                    immutable_definition.get("domain_and_boundary_behavior", {})
                ),
                "inputs": _thaw(immutable_definition.get("input_schema", ())),
                "outputs": _thaw(immutable_definition.get("output_schema", ())),
                "units_and_bases": _thaw(
                    immutable_definition.get("units_and_bases", {})
                ),
                "selected_binding": selected,
                "requirements_summary": _thaw(receipt.requirement_receipts),
                "evidence_summary": {
                    "state": selected.get("evidence_state"),
                    "receipt_pinned": True,
                },
                "limitations": list(receipt.warnings),
                "fallback": selected.get("fallback_policy", {}),
                "fallback_used": receipt.fallback_used,
                "exact_next_action": selected.get("exact_resolution_action"),
                "blockers": list(receipt.errors),
                "outputs_unchanged": _thaw(receipt.outputs),
                "no_new_numerical_output": True,
                "no_order_authority": True,
            }
        else:
            selector = receipt_or_selector
            receipt_ref = None
            request_context = dict(context or {})
        if context:
            request_context.update(context)
        snapshot = self._registry.pin()
        plan = self._resolve_on_snapshot(
            snapshot,
            selector,
            request_context,
            agent_id=agent_id,
            operation="explain",
        )
        record = snapshot.indexes.records_by_key[(plan.root_component_id, plan.root_semantic_version)]
        binding = next(value for value in record["bindings"] if value["binding_id"] == plan.root_binding_id)
        return {
            "receipt_ref": receipt_ref,
            "identity": {
                "canonical_component_id": plan.root_component_id,
                "semantic_version": plan.root_semantic_version,
                "record_state": record["record_state"],
                "origin_cohorts": list(record["origin_cohorts"]),
            },
            "decision_use": _thaw(record["uses"]),
            "provenance": _thaw(record["provenance"]),
            "mathematics_or_procedure": record["definition"]["complete_mathematical_or_procedural_definition"],
            "assumptions": _thaw(record["definition"]["assumptions"]),
            "domain_and_boundary_behavior": _thaw(record["definition"]["domain_and_boundary_behavior"]),
            "inputs": _thaw(record["definition"]["input_schema"]),
            "outputs": _thaw(record["definition"]["output_schema"]),
            "units_and_bases": _thaw(record["definition"]["units_and_bases"]),
            "selected_binding": {
                "binding_id": binding["binding_id"],
                "binding_version": binding["binding_version"],
                "implementation_version": binding["selected_implementation_version"],
                "parameter_policy": _thaw(binding["selected_parameter_policy"]),
            },
            "requirements_summary": [
                {
                    "node_id": node.node_id,
                    "component_id": node.canonical_component_id,
                    "semantic_version": node.semantic_version,
                    "binding_id": node.binding_id,
                    "requirements": _thaw(node.requirement_inputs),
                }
                for node in plan.topological_nodes
            ],
            "evidence_summary": _thaw(binding["evidence_summary"]),
            "limitations": _thaw(binding["evidence_summary"].get("limitations", ())),
            "fallback": _thaw(binding["fallback_policy"]),
            "exact_next_action": binding["exact_resolution_action_or_null"],
            "blockers": list(plan.blockers),
            "no_new_numerical_output": True,
            "no_order_authority": True,
        }

    def _replace_snapshot(
        self,
        candidate_records: Iterable[Mapping[str, Any]],
        delta: RegistryUpdateV1 | Mapping[str, Any],
    ) -> dict[str, Any]:
        base = self._registry.pin()
        replacement, stats = _apply_registry_update(base, delta, candidate_records)
        self._registry.swap(base.generation, replacement)
        self._diagnostic_state["last_incremental_refresh"] = stats
        self._diagnostic_state["registry_rows"] = len(replacement.records)
        return stats

def _reject_nonfinite(value: Any, *, path: str) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ComputationControlError("NONFINITE_VALUE", path)
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ComputationControlError("NONFINITE_VALUE", path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_nonfinite(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_nonfinite(item, path=f"{path}[{index}]")


def _apply_unit_conversion(value: Any, conversion: Any) -> Any:
    if conversion in {None, "", "NONE", "IDENTITY"}:
        return value
    if conversion == "PERCENT_TO_DECIMAL":
        if isinstance(value, Decimal):
            return value / Decimal("100")
        return float(value) / 100.0
    if conversion == "DECIMAL_TO_PERCENT":
        if isinstance(value, Decimal):
            return value * Decimal("100")
        return float(value) * 100.0
    if isinstance(conversion, Mapping) and "factor" in conversion:
        factor = conversion["factor"]
        if isinstance(value, Decimal):
            return value * _decimal(factor, name="unit_conversion.factor")
        return float(value) * float(factor)
    raise ComputationControlError("UNSUPPORTED_UNIT_CONVERSION", _stable_json(conversion))
