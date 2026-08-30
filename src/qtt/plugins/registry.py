"""Small in-memory registry for deterministic plugin adapters."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
import json
from types import MappingProxyType

from .authority import DEFAULT_AUTHORITY_ENVELOPE
from .contracts import (
    PLUGIN_FAMILIES,
    CompatibilityAndDependencyReceiptV1,
    PackageAdmissionStateV1,
    PackageCompatibilityStateV1,
    PackageOperationEligibilityStateV1,
    PackageOperationEligibilityV1,
    PackageReproducibilityReceiptV1,
    PackageRollbackTargetKindV1,
    PackageSupersessionStateV1,
    PackageValidationTerminalStateV1,
    PackageVersionV1,
    PluginAdapterBase,
    PluginPackageContractError,
    PluginPackageReasonCodeV1,
    RollbackAndSupersessionReceiptV1,
    SelectedComponentPackageEntryV1,
    SelectedComponentPackageManifestV1,
    _canonical_package_json,
)
from .dag import compile_selected_package_dependency_order_v1


_PACKAGE_ID = "S1-PLUGIN-PACKAGE-CURRENTIZATION-01"
_MANIFEST_SCHEMA_VERSION = "SELECTED_COMPONENT_PACKAGE_MANIFEST_V1"
_LAUNCH_GRAPH_PACKAGE_REF = "S1-LAUNCH-GRAPH-MATERIALIZATION-01"
_LAUNCH_GRAPH_SCHEMA_VERSION = "SELECTED_LAUNCH_GRAPH_V2"
_SELECTED_SCOPE_SCHEMA_VERSION = "STAGE1_SELECTED_SCOPE_V2"
_LAUNCH_GRAPH_SEMANTICS = "IMPLEMENTATION_CLOSURE_DAG_NOT_RUNTIME_GATE_DAG"
_CANONICAL_SERIALIZATION_POLICY = (
    "json.dumps(ensure_ascii=True,allow_nan=False,sort_keys=True,"
    "separators=(',',':'))"
)
_INITIAL_VERSION = PackageVersionV1(1, 0, 0)
_BUILDER_RUNTIME_VERSION = PackageVersionV1(3, 14, 6)
_SELECTED_PROFILE_IDS = (
    "GEMINI_TITAN_DIRECT",
    "POLYMARKET_US_RETAIL_DIRECT",
    "KALSHI_US_DCM_DIRECT",
)
_EXCLUDED_PROFILE_IDS = (
    "FORECASTEX_IBKR",
    "FORECASTEX_DIRECT_MEMBER",
)
_ROLE_IDS = tuple(f"ROLE-{value:02d}" for value in range(1, 29))
_COMPONENT_IDS = tuple(f"S1PKG::{role_id}" for role_id in _ROLE_IDS)
_BINDING_ONLY_ROLE_IDS = (
    "ROLE-01",
    "ROLE-03",
    "ROLE-05",
    "ROLE-06",
    "ROLE-10",
    "ROLE-15",
    "ROLE-18",
    "ROLE-19",
    "ROLE-24",
    "ROLE-26",
    "ROLE-28",
)
_EVIDENCE_ONLY_ROLE_IDS = (
    "ROLE-07",
    "ROLE-11",
    "ROLE-13",
    "ROLE-23",
    "ROLE-27",
)
_TRUE_MISSING_ROLE_IDS = (
    "ROLE-02",
    "ROLE-04",
    "ROLE-08",
    "ROLE-09",
    "ROLE-12",
    "ROLE-14",
    "ROLE-16",
    "ROLE-17",
    "ROLE-20",
    "ROLE-21",
    "ROLE-22",
    "ROLE-25",
)
_DIRECT_PREREQUISITE_ROLE_IDS = (
    (),
    ("ROLE-01",),
    ("ROLE-01", "ROLE-02"),
    ("ROLE-01", "ROLE-02", "ROLE-03"),
    ("ROLE-03", "ROLE-04"),
    ("ROLE-04",),
    ("ROLE-03", "ROLE-05", "ROLE-06"),
    ("ROLE-03", "ROLE-07"),
    ("ROLE-01", "ROLE-02", "ROLE-03"),
    ("ROLE-04", "ROLE-09"),
    ("ROLE-04", "ROLE-05", "ROLE-10", "ROLE-12"),
    ("ROLE-04", "ROLE-05"),
    ("ROLE-05", "ROLE-11"),
    ("ROLE-03", "ROLE-04", "ROLE-05"),
    (
        "ROLE-06",
        "ROLE-07",
        "ROLE-08",
        "ROLE-09",
        "ROLE-10",
        "ROLE-11",
        "ROLE-13",
        "ROLE-14",
    ),
    ("ROLE-08", "ROLE-15"),
    ("ROLE-01", "ROLE-03"),
    ("ROLE-01", "ROLE-03", "ROLE-17"),
    ("ROLE-16", "ROLE-17", "ROLE-18"),
    ("ROLE-16", "ROLE-17", "ROLE-18", "ROLE-19"),
    (
        "ROLE-14",
        "ROLE-16",
        "ROLE-17",
        "ROLE-18",
        "ROLE-19",
        "ROLE-20",
        "ROLE-26",
        "ROLE-28",
    ),
    ("ROLE-14", "ROLE-15", "ROLE-17", "ROLE-18", "ROLE-26"),
    (
        "ROLE-03",
        "ROLE-09",
        "ROLE-10",
        "ROLE-11",
        "ROLE-13",
        "ROLE-14",
        "ROLE-17",
        "ROLE-21",
        "ROLE-22",
    ),
    (
        "ROLE-03",
        "ROLE-08",
        "ROLE-16",
        "ROLE-17",
        "ROLE-18",
        "ROLE-21",
        "ROLE-22",
        "ROLE-23",
        "ROLE-26",
        "ROLE-28",
    ),
    (
        "ROLE-01",
        "ROLE-03",
        "ROLE-14",
        "ROLE-17",
        "ROLE-18",
        "ROLE-21",
        "ROLE-22",
        "ROLE-24",
        "ROLE-26",
        "ROLE-28",
    ),
    ("ROLE-01", "ROLE-03"),
    ("ROLE-16", "ROLE-20", "ROLE-26"),
    ("ROLE-01", "ROLE-03", "ROLE-26"),
)
_EXPECTED_DEPENDENCY_EDGES = tuple(
    sorted(
        (_component_id, f"S1PKG::{role_id}")
        for role_id, prerequisites in zip(
            _ROLE_IDS,
            _DIRECT_PREREQUISITE_ROLE_IDS,
            strict=True,
        )
        for _component_id in (
            f"S1PKG::{prerequisite}" for prerequisite in prerequisites
        )
    )
)
_EXPECTED_TOPOLOGICAL_ORDER = tuple(
    f"S1PKG::{role_id}"
    for role_id in (
        "ROLE-01",
        "ROLE-02",
        "ROLE-03",
        "ROLE-04",
        "ROLE-05",
        "ROLE-06",
        "ROLE-07",
        "ROLE-08",
        "ROLE-09",
        "ROLE-10",
        "ROLE-12",
        "ROLE-11",
        "ROLE-13",
        "ROLE-14",
        "ROLE-15",
        "ROLE-16",
        "ROLE-17",
        "ROLE-18",
        "ROLE-19",
        "ROLE-20",
        "ROLE-26",
        "ROLE-22",
        "ROLE-27",
        "ROLE-28",
        "ROLE-21",
        "ROLE-23",
        "ROLE-24",
        "ROLE-25",
    )
)
_OPERATION_CLASSES = (
    "NEW_OR_INCREASED_EXPOSURE",
    "CANCEL_QUERY_RECONCILE",
    "RISK_REDUCING_POSITION_ACTION",
    "REPLAY_PAPER_EVIDENCE",
    "QUANTUM_CHALLENGER_RESEARCH",
)
_OPERATION_REQUIRED_ROLE_IDS = (
    tuple(role_id for role_id in _ROLE_IDS if role_id != "ROLE-27"),
    ("ROLE-01", "ROLE-17", "ROLE-24", "ROLE-25", "ROLE-28"),
    (
        "ROLE-01",
        "ROLE-02",
        "ROLE-03",
        "ROLE-04",
        "ROLE-09",
        "ROLE-10",
        "ROLE-14",
        "ROLE-15",
        "ROLE-17",
        "ROLE-18",
        "ROLE-22",
        "ROLE-24",
        "ROLE-25",
        "ROLE-26",
        "ROLE-28",
    ),
    (
        "ROLE-01",
        "ROLE-02",
        "ROLE-03",
        "ROLE-04",
        "ROLE-05",
        "ROLE-06",
        "ROLE-07",
        "ROLE-08",
        "ROLE-09",
        "ROLE-10",
        "ROLE-11",
        "ROLE-12",
        "ROLE-13",
        "ROLE-14",
        "ROLE-15",
        "ROLE-16",
        "ROLE-17",
        "ROLE-18",
        "ROLE-23",
        "ROLE-26",
        "ROLE-28",
    ),
    (
        "ROLE-01",
        "ROLE-03",
        "ROLE-08",
        "ROLE-15",
        "ROLE-16",
        "ROLE-17",
        "ROLE-18",
        "ROLE-19",
        "ROLE-20",
        "ROLE-26",
        "ROLE-27",
    ),
)
_OPERATION_REQUIRED_COUNTS = tuple(
    len(role_ids) for role_ids in _OPERATION_REQUIRED_ROLE_IDS
)
_OPERATION_OPTIONAL_ROLE_IDS = (
    ("ROLE-27",),
    (),
    (),
    ("ROLE-27",),
    (),
)
_OPERATION_TERMINAL_ROUTES = (
    "NO_TRADE_AND_SUBMIT_DISABLED",
    "QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD",
    "SAFE_HOLD",
    "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "CLASSICAL_ONLY",
)
_EXPECTED_OPERATION_BLOCKERS = tuple(
    tuple(f"S1PKG::{role_id}" for role_id in roles)
    for roles in (
        (
            "ROLE-02",
            "ROLE-04",
            "ROLE-07",
            "ROLE-08",
            "ROLE-09",
            "ROLE-11",
            "ROLE-12",
            "ROLE-13",
            "ROLE-14",
            "ROLE-16",
            "ROLE-17",
            "ROLE-20",
            "ROLE-21",
            "ROLE-22",
            "ROLE-23",
            "ROLE-25",
        ),
        ("ROLE-17", "ROLE-25"),
        (
            "ROLE-02",
            "ROLE-04",
            "ROLE-09",
            "ROLE-14",
            "ROLE-17",
            "ROLE-22",
            "ROLE-25",
        ),
        (
            "ROLE-02",
            "ROLE-04",
            "ROLE-07",
            "ROLE-08",
            "ROLE-09",
            "ROLE-11",
            "ROLE-12",
            "ROLE-13",
            "ROLE-14",
            "ROLE-16",
            "ROLE-17",
            "ROLE-23",
        ),
        ("ROLE-08", "ROLE-16", "ROLE-17", "ROLE-20", "ROLE-27"),
    )
)
_NO_EFFECT_KEYS = frozenset(
    {
        "provider_connection_allowed",
        "private_state_read_allowed",
        "replay_or_paper_execution_allowed",
        "llm_inference_allowed",
        "qpu_execution_allowed",
        "mode_or_allow_activation_allowed",
        "order_release_allowed",
        "capital_mutation_allowed",
    }
)

_S1_SELECTED_ROLE_FAMILY_ROWS_JSON = r"""[
  {"role_id":"ROLE-01","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-02","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-03","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-04","primary_plugin_family_or_none":"ORDERBOOK_STATE_PLUGIN","supporting_plugin_families":["STALE_BOOK_DIAGNOSTIC_PLUGIN","STALE_BOOK_REPAIR_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-05","primary_plugin_family_or_none":"FEATURE_TRANSFORM_PLUGIN","supporting_plugin_families":["SIGNAL_SCORING_PLUGIN"],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-06","primary_plugin_family_or_none":"FORMULA_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-07","primary_plugin_family_or_none":"PROBABILITY_CALIBRATION_PLUGIN","supporting_plugin_families":["CALIBRATION_ERROR_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-08","primary_plugin_family_or_none":"PARAMETER_STACK_PLUGIN","supporting_plugin_families":["HOLDOUT_CONFIDENCE_PLUGIN","LOWER_CONFIDENCE_BOUND_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-09","primary_plugin_family_or_none":"EXECUTION_COST_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-10","primary_plugin_family_or_none":"SLIPPAGE_IMPACT_PLUGIN","supporting_plugin_families":["IMPL_SHORTFALL_PLUGIN"],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-11","primary_plugin_family_or_none":"FILL_MODEL_PLUGIN","supporting_plugin_families":["PARTIAL_FILL_PLUGIN","NO_FILL_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-12","primary_plugin_family_or_none":"QUEUE_RISK_PLUGIN","supporting_plugin_families":["QUEUE_SURVIVAL_PLUGIN"],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-13","primary_plugin_family_or_none":"ADVERSE_SELECTION_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-14","primary_plugin_family_or_none":"LATENCY_DECAY_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-15","primary_plugin_family_or_none":"EXPECTED_VALUE_PLUGIN","supporting_plugin_families":["EXECUTION_COST_PLUGIN"],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-16","primary_plugin_family_or_none":"LOWER_CONFIDENCE_BOUND_PLUGIN","supporting_plugin_families":["NO_TRADE_REASON_PLUGIN","DECISION_RULE_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-17","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-18","primary_plugin_family_or_none":"RISK_BUDGET_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-19","primary_plugin_family_or_none":"THRESHOLD_POLICY_PLUGIN","supporting_plugin_families":["DECISION_RULE_PLUGIN"],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-20","primary_plugin_family_or_none":"PORTFOLIO_UTILITY_PLUGIN","supporting_plugin_families":["MARGINAL_UTILITY_PLUGIN","DIVERSIFICATION_PLUGIN","CORRELATION_CLUSTER_PLUGIN","COMMON_DRIVER_EXPOSURE_PLUGIN","RISK_BUDGET_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-21","primary_plugin_family_or_none":"AGGRESSION_LADDER_PLUGIN","supporting_plugin_families":["CANCEL_REPLACE_PLUGIN","DECISION_RULE_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-22","primary_plugin_family_or_none":"DECISION_RULE_PLUGIN","supporting_plugin_families":["THRESHOLD_POLICY_PLUGIN"],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-23","primary_plugin_family_or_none":"TCA_PLUGIN","supporting_plugin_families":["EDGE_ATTRIBUTION_PLUGIN","IMPL_SHORTFALL_PLUGIN"],"rollback_target_kind":"NO_TRADE","fallback_role_id_or_none":null},
  {"role_id":"ROLE-24","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-25","primary_plugin_family_or_none":null,"supporting_plugin_families":[],"rollback_target_kind":"UNAVAILABLE_OWNER_REVIEW_REQUIRED","fallback_role_id_or_none":null},
  {"role_id":"ROLE-26","primary_plugin_family_or_none":"CLASSICAL_FALLBACK_PLUGIN","supporting_plugin_families":[],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null},
  {"role_id":"ROLE-27","primary_plugin_family_or_none":"QUANTUM_RECIPE_PLUGIN","supporting_plugin_families":["QUBO_ADAPTER_PLUGIN","BQM_ADAPTER_PLUGIN","ISING_ADAPTER_PLUGIN","CQM_ADAPTER_PLUGIN","DQM_ADAPTER_PLUGIN","QUAD_PROGRAM_ADAPTER_PLUGIN","HYBRID_ROUTE_PLUGIN","INTERPRET_BACK_VALIDATOR_PLUGIN","PROOF_VECTOR_VALIDATOR_PLUGIN","FEASIBILITY_VALIDATOR_PLUGIN","COEFFICIENT_SCALING_PLUGIN","UNIT_NORMALIZATION_PLUGIN","PRECISION_BINNING_PLUGIN","PENALTY_TUNING_PLUGIN","QUBIT_COST_ESTIMATOR_PLUGIN","EMBEDDING_READINESS_PLUGIN","QUANTUM_SHOT_BUDGET_STRUCTURAL_PLUGIN","ANNEAL_SCHEDULE_STRUCTURAL_PLUGIN"],"rollback_target_kind":"DETERMINISTIC_CLASSICAL_FALLBACK","fallback_role_id_or_none":"ROLE-26"},
  {"role_id":"ROLE-28","primary_plugin_family_or_none":"AGENT_WORK_ORDER_ROUTE","supporting_plugin_families":["GOVERNANCE_REVIEW_ROUTE","COMMANDER_DAG_ROUTE"],"rollback_target_kind":"DISABLE_TO_NO_EFFECT","fallback_role_id_or_none":null}
]"""

_FAMILY_ROW_KEYS = (
    "role_id",
    "primary_plugin_family_or_none",
    "supporting_plugin_families",
    "rollback_target_kind",
    "fallback_role_id_or_none",
)
_TOP_LEVEL_KEYS = frozenset({"package_ref", "graph", "validation"})
_GRAPH_KEYS = frozenset(
    {
        "binding_only_role_ids",
        "dependency_edges",
        "evidence_only_role_ids",
        "future_sole_write_role_id",
        "graph_semantics",
        "no_effects",
        "operation_profiles",
        "reason_codes",
        "roles",
        "schema_version",
        "scope",
        "terminal_state",
        "topological_order",
        "true_missing_role_ids",
    }
)
_SCOPE_KEYS = frozenset(
    {
        "active_live_profile_ids",
        "authority_class",
        "excluded_profile_ids",
        "no_effects",
        "profiles",
        "schema_version",
        "selected_profile_ids",
        "serialization",
        "source_decision_ref",
    }
)
_PROFILE_KEYS = frozenset(
    {
        "api_profile",
        "authority_ref",
        "clearing_or_access_route",
        "jurisdiction",
        "operating_legal_entity",
        "product_family",
        "profile_id",
        "research_state",
        "scope_state",
        "serialization_ordinal_or_none",
    }
)
_ROLE_KEYS = frozenset(
    {
        "default_failure_route",
        "direct_prerequisite_role_ids",
        "disposition",
        "frozen_output",
        "latency_class",
        "path_refs",
        "research_state",
        "responsibility",
        "role_id",
        "semantic_owner",
    }
)
_PATH_KEYS = frozenset({"disposition", "path", "reason", "semantic_owner"})
_EDGE_KEYS = frozenset(
    {"consumer_role_id", "edge_id", "failure_route", "producer_role_id", "required"}
)
_OPERATION_KEYS = frozenset(
    {
        "consumption_law",
        "no_effects",
        "operation_class",
        "optional_role_ids",
        "purpose",
        "required_role_ids",
        "research_state",
        "terminal_failure_route",
    }
)
_VALIDATION_KEYS = frozenset(
    {
        "checked_edge_count",
        "checked_operation_profile_count",
        "checked_path_count",
        "checked_profile_count",
        "checked_role_count",
        "reason_codes",
        "terminal_state",
    }
)


def _raise(reason_code: PluginPackageReasonCodeV1, message: str) -> None:
    raise PluginPackageContractError(reason_code, message)


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{name} must be a mapping",
        )
    return value


def _exact_keys(
    value: Mapping[str, object],
    expected: frozenset[str],
    name: str,
) -> None:
    if len(value) != len(expected) or frozenset(value) != expected:
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{name} fields differ from the exact contract",
        )


def _text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{name} must be nonempty canonical text",
        )
    return value


def _list(value: object, name: str) -> list[object]:
    if type(value) is not list:
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            f"{name} must be an exact JSON list",
        )
    return value


def _text_list(value: object, name: str) -> tuple[str, ...]:
    rows = _list(value, name)
    values = tuple(_text(row, name) for row in rows)
    if len(values) != len(set(values)):
        _raise(
            PluginPackageReasonCodeV1.IDENTITY_INVALID,
            f"{name} must be duplicate-free",
        )
    return values


def _exact_no_effects(value: object, name: str) -> None:
    row = _mapping(value, name)
    if frozenset(row) != _NO_EFFECT_KEYS or any(
        type(row[key]) is not bool or row[key] for key in _NO_EFFECT_KEYS
    ):
        _raise(
            PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN,
            f"{name} must preserve the exact all-false no-effect envelope",
        )


def _safe_relative_path(value: object) -> str:
    path = _text(value, "path")
    if (
        "\\" in path
        or ":" in path
        or path.startswith(("/", "./", "../"))
        or any(token in path for token in ("*", "?", "[", "]"))
        or any(segment in {"", ".", ".."} for segment in path.split("/"))
    ):
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "path must be a safe exact repository-relative path",
        )
    return path


def _component_id(role_id: str) -> str:
    return f"S1PKG::{role_id}"


def _validate_launch_projection(
    launch_graph_projection: Mapping[str, object],
) -> tuple[
    Mapping[str, object],
    tuple[Mapping[str, object], ...],
    tuple[Mapping[str, object], ...],
]:
    projection = _mapping(launch_graph_projection, "launch_graph_projection")
    _exact_keys(projection, _TOP_LEVEL_KEYS, "launch_graph_projection")
    if projection["package_ref"] != _LAUNCH_GRAPH_PACKAGE_REF:
        _raise(
            PluginPackageReasonCodeV1.IDENTITY_INVALID,
            "launch graph package reference differs",
        )

    graph = _mapping(projection["graph"], "graph")
    _exact_keys(graph, _GRAPH_KEYS, "graph")
    if (
        graph["schema_version"] != _LAUNCH_GRAPH_SCHEMA_VERSION
        or graph["graph_semantics"] != _LAUNCH_GRAPH_SEMANTICS
        or graph["future_sole_write_role_id"] != "ROLE-25"
        or graph["terminal_state"] != "VALIDATED_NO_EFFECT"
        or graph["reason_codes"] != []
    ):
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "launch graph identity or terminal state differs",
        )
    _exact_no_effects(graph["no_effects"], "graph.no_effects")

    scope = _mapping(graph["scope"], "graph.scope")
    _exact_keys(scope, _SCOPE_KEYS, "graph.scope")
    if (
        scope["schema_version"] != _SELECTED_SCOPE_SCHEMA_VERSION
        or tuple(_text_list(scope["selected_profile_ids"], "selected_profile_ids"))
        != _SELECTED_PROFILE_IDS
        or tuple(_text_list(scope["excluded_profile_ids"], "excluded_profile_ids"))
        != _EXCLUDED_PROFILE_IDS
        or tuple(_text_list(scope["serialization"], "scope.serialization"))
        != _SELECTED_PROFILE_IDS
        or scope["active_live_profile_ids"] != []
    ):
        _raise(
            PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
            "Stage-1 profile scope differs",
        )
    _text(scope["authority_class"], "scope.authority_class")
    _text(scope["source_decision_ref"], "scope.source_decision_ref")
    _exact_no_effects(scope["no_effects"], "scope.no_effects")
    profile_rows = _list(scope["profiles"], "scope.profiles")
    if len(profile_rows) != 5:
        _raise(
            PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
            "Stage-1 profile row count must be five",
        )
    expected_profile_ids = (*_SELECTED_PROFILE_IDS, *_EXCLUDED_PROFILE_IDS)
    for index, raw_profile in enumerate(profile_rows):
        profile = _mapping(raw_profile, "profile row")
        _exact_keys(profile, _PROFILE_KEYS, "profile row")
        if profile["profile_id"] != expected_profile_ids[index]:
            _raise(
                PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
                "profile row identity or order differs",
            )
        for name in _PROFILE_KEYS - {"serialization_ordinal_or_none"}:
            _text(profile[name], f"profile.{name}")
        if index < 3:
            if (
                profile["scope_state"] != "SELECTED_CORE"
                or profile["serialization_ordinal_or_none"] != index + 1
            ):
                _raise(
                    PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
                    "selected profile serialization differs",
                )
        elif (
            profile["scope_state"]
            != "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION"
            or profile["serialization_ordinal_or_none"] is not None
        ):
            _raise(
                PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID,
                "ForecastEx exclusion differs",
            )

    raw_roles = _list(graph["roles"], "graph.roles")
    if len(raw_roles) != 28:
        _raise(
            PluginPackageReasonCodeV1.IDENTITY_INVALID,
            "launch graph must contain 28 roles",
        )
    roles: list[Mapping[str, object]] = []
    derived_edges: list[tuple[str, str]] = []
    role_paths: list[str] = []
    dispositions: list[str] = []
    for role_index, (expected_role_id, raw_role) in enumerate(
        zip(_ROLE_IDS, raw_roles, strict=True)
    ):
        role = _mapping(raw_role, "role row")
        _exact_keys(role, _ROLE_KEYS, "role row")
        role_id = _text(role["role_id"], "role.role_id")
        if role_id != expected_role_id:
            _raise(
                PluginPackageReasonCodeV1.IDENTITY_INVALID,
                "launch role identity or order differs",
            )
        disposition = _text(role["disposition"], "role.disposition")
        if disposition not in {
            "BINDING_ONLY_GAP",
            "EVIDENCE_ONLY_GAP",
            "TRUE_MISSING_DEPENDENCY",
        }:
            _raise(
                PluginPackageReasonCodeV1.ADMISSION_INVALID,
                "launch role disposition differs",
            )
        dispositions.append(disposition)
        semantic_owner = _text(role["semantic_owner"], "role.semantic_owner")
        for name in (
            "responsibility",
            "frozen_output",
            "default_failure_route",
            "latency_class",
            "research_state",
        ):
            _text(role[name], f"role.{name}")
        prerequisites = _text_list(
            role["direct_prerequisite_role_ids"],
            "direct_prerequisite_role_ids",
        )
        if prerequisites != _DIRECT_PREREQUISITE_ROLE_IDS[role_index]:
            _raise(
                PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE,
                "direct prerequisites differ from the frozen role graph",
            )
        derived_edges.extend((producer, role_id) for producer in prerequisites)
        path_rows = _list(role["path_refs"], "role.path_refs")
        if not path_rows:
            _raise(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "each role requires at least one owner path",
            )
        for raw_path in path_rows:
            path_row = _mapping(raw_path, "path row")
            _exact_keys(path_row, _PATH_KEYS, "path row")
            path = _safe_relative_path(path_row["path"])
            if (
                path_row["semantic_owner"] != semantic_owner
                or path_row["disposition"]
                not in {
                    "EXISTING_CANONICAL_OWNER",
                    "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED",
                }
            ):
                _raise(
                    PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                    "owner path lineage differs",
                )
            _text(path_row["reason"], "path.reason")
            role_paths.append(path)
        roles.append(role)
    if Counter(dispositions) != Counter(
        {
            "BINDING_ONLY_GAP": 11,
            "EVIDENCE_ONLY_GAP": 5,
            "TRUE_MISSING_DEPENDENCY": 12,
        }
    ) or len(set(role_paths)) != 34:
        _raise(
            PluginPackageReasonCodeV1.ADMISSION_INVALID,
            "launch role disposition or owner-path denominators differ",
        )
    binding_role_ids = _text_list(
        graph["binding_only_role_ids"],
        "graph.binding_only_role_ids",
    )
    evidence_role_ids = _text_list(
        graph["evidence_only_role_ids"],
        "graph.evidence_only_role_ids",
    )
    missing_role_ids = _text_list(
        graph["true_missing_role_ids"],
        "graph.true_missing_role_ids",
    )
    if (
        binding_role_ids != _BINDING_ONLY_ROLE_IDS
        or evidence_role_ids != _EVIDENCE_ONLY_ROLE_IDS
        or missing_role_ids != _TRUE_MISSING_ROLE_IDS
        or binding_role_ids
        != tuple(
            role["role_id"]
            for role in roles
            if role["disposition"] == "BINDING_ONLY_GAP"
        )
        or evidence_role_ids
        != tuple(
            role["role_id"]
            for role in roles
            if role["disposition"] == "EVIDENCE_ONLY_GAP"
        )
        or missing_role_ids
        != tuple(
            role["role_id"]
            for role in roles
            if role["disposition"] == "TRUE_MISSING_DEPENDENCY"
        )
    ):
        _raise(
            PluginPackageReasonCodeV1.ADMISSION_INVALID,
            "launch disposition partitions differ",
        )

    raw_edges = _list(graph["dependency_edges"], "graph.dependency_edges")
    if len(raw_edges) != 102:
        _raise(
            PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE,
            "launch graph must contain 102 dependency edges",
        )
    observed_edges: list[tuple[str, str]] = []
    for expected_edge, raw_edge in zip(derived_edges, raw_edges, strict=True):
        edge = _mapping(raw_edge, "dependency edge")
        _exact_keys(edge, _EDGE_KEYS, "dependency edge")
        producer = _text(edge["producer_role_id"], "edge.producer_role_id")
        consumer = _text(edge["consumer_role_id"], "edge.consumer_role_id")
        pair = (producer, consumer)
        if (
            pair != expected_edge
            or edge["edge_id"] != f"S1-EDGE::{producer}->{consumer}"
            or edge["required"] is not True
            or edge["failure_route"]
            != next(
                role["default_failure_route"]
                for role in roles
                if role["role_id"] == consumer
            )
        ):
            _raise(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "launch dependency edge differs from role prerequisites",
            )
        observed_edges.append(pair)
    if len(observed_edges) != len(set(observed_edges)):
        _raise(
            PluginPackageReasonCodeV1.EDGE_DUPLICATE,
            "launch graph contains duplicate dependency edges",
        )
    component_edges = tuple(
        (_component_id(producer), _component_id(consumer))
        for producer, consumer in observed_edges
    )
    if tuple(sorted(component_edges)) != _EXPECTED_DEPENDENCY_EDGES:
        _raise(
            PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE,
            "launch dependency edge set differs from the frozen package graph",
        )
    compiled_order = compile_selected_package_dependency_order_v1(
        _COMPONENT_IDS,
        component_edges,
    )
    if (
        tuple(_component_id(role_id) for role_id in graph["topological_order"])
        != compiled_order
        or compiled_order != _EXPECTED_TOPOLOGICAL_ORDER
        or ("S1PKG::ROLE-12", "S1PKG::ROLE-11") not in component_edges
    ):
        _raise(
            PluginPackageReasonCodeV1.DEPENDENCY_CYCLE,
            "launch topological order or queue-to-fill edge differs",
        )

    raw_operations = _list(graph["operation_profiles"], "graph.operation_profiles")
    if len(raw_operations) != 5:
        _raise(
            PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
            "launch graph must contain five operation profiles",
        )
    operations: list[Mapping[str, object]] = []
    for index, raw_operation in enumerate(raw_operations):
        operation = _mapping(raw_operation, "operation profile")
        _exact_keys(operation, _OPERATION_KEYS, "operation profile")
        operation_class = _text(
            operation["operation_class"],
            "operation.operation_class",
        )
        required = _text_list(
            operation["required_role_ids"],
            "operation.required_role_ids",
        )
        optional = _text_list(
            operation["optional_role_ids"],
            "operation.optional_role_ids",
        )
        if (
            operation_class != _OPERATION_CLASSES[index]
            or required != _OPERATION_REQUIRED_ROLE_IDS[index]
            or optional != _OPERATION_OPTIONAL_ROLE_IDS[index]
            or operation["terminal_failure_route"]
            != _OPERATION_TERMINAL_ROUTES[index]
            or set(required).intersection(optional)
            or not set((*required, *optional)).issubset(_ROLE_IDS)
        ):
            _raise(
                PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID,
                "operation dependency profile differs",
            )
        for name in ("purpose", "consumption_law", "research_state"):
            _text(operation[name], f"operation.{name}")
        _exact_no_effects(operation["no_effects"], "operation.no_effects")
        operations.append(operation)

    validation = _mapping(projection["validation"], "validation")
    _exact_keys(validation, _VALIDATION_KEYS, "validation")
    if validation != {
        "checked_edge_count": 102,
        "checked_operation_profile_count": 5,
        "checked_path_count": 34,
        "checked_profile_count": 5,
        "checked_role_count": 28,
        "reason_codes": [],
        "terminal_state": "VALIDATED_NO_EFFECT",
    }:
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "launch graph validation receipt differs",
        )
    return graph, tuple(roles), tuple(operations)


def _selected_family_rows() -> tuple[Mapping[str, object], ...]:
    try:
        raw = json.loads(_S1_SELECTED_ROLE_FAMILY_ROWS_JSON)
    except json.JSONDecodeError as exc:
        raise PluginPackageContractError(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "selected role-family literal is invalid JSON",
        ) from exc
    if type(raw) is not list or len(raw) != 28:
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "selected role-family literal must contain 28 rows",
        )
    rows: list[Mapping[str, object]] = []
    family_refs: list[str] = []
    no_family_count = 0
    for expected_role_id, raw_row in zip(_ROLE_IDS, raw, strict=True):
        row = _mapping(raw_row, "selected role-family row")
        if tuple(row) != _FAMILY_ROW_KEYS or row["role_id"] != expected_role_id:
            _raise(
                PluginPackageReasonCodeV1.IDENTITY_INVALID,
                "selected role-family row schema, identity, or order differs",
            )
        primary = row["primary_plugin_family_or_none"]
        if primary is not None:
            primary = _text(primary, "primary_plugin_family_or_none")
            family_refs.append(primary)
        supporting = _text_list(
            row["supporting_plugin_families"],
            "supporting_plugin_families",
        )
        if primary in supporting:
            _raise(
                PluginPackageReasonCodeV1.FAMILY_UNKNOWN,
                "primary and supporting family references must be distinct",
            )
        family_refs.extend(supporting)
        if primary is None and not supporting:
            no_family_count += 1
        try:
            PackageRollbackTargetKindV1(row["rollback_target_kind"])
        except (TypeError, ValueError) as exc:
            raise PluginPackageContractError(
                PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                "selected role rollback target differs",
            ) from exc
        fallback = row["fallback_role_id_or_none"]
        if fallback is not None:
            fallback = _text(fallback, "fallback_role_id_or_none")
        if (expected_role_id, fallback) not in {
            (role_id, None) for role_id in _ROLE_IDS if role_id != "ROLE-27"
        } | {("ROLE-27", "ROLE-26")}:
            _raise(
                PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                "only ROLE-27 may use the ROLE-26 fallback",
            )
        rows.append(row)
    unknown = tuple(sorted(set(family_refs) - set(PLUGIN_FAMILIES)))
    if (
        unknown
        or len(family_refs) != 66
        or len(set(family_refs)) != 58
        or no_family_count != 6
        or len(PLUGIN_FAMILIES) != 95
    ):
        _raise(
            PluginPackageReasonCodeV1.FAMILY_UNKNOWN,
            "selected role-family denominators or canonical membership differ",
        )
    return tuple(rows)


def _admission_contract(
    disposition: object,
) -> tuple[
    PackageAdmissionStateV1,
    PackageCompatibilityStateV1,
    tuple[PluginPackageReasonCodeV1, ...],
]:
    if disposition == "BINDING_ONLY_GAP":
        return (
            PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT,
            PackageCompatibilityStateV1.PASS_CONTRACT_ONLY_NO_EFFECT,
            (),
        )
    if disposition == "EVIDENCE_ONLY_GAP":
        return (
            PackageAdmissionStateV1.HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION,
            PackageCompatibilityStateV1.BLOCKED_EVIDENCE_INSUFFICIENT,
            (PluginPackageReasonCodeV1.EVIDENCE_INSUFFICIENT,),
        )
    if disposition == "TRUE_MISSING_DEPENDENCY":
        return (
            PackageAdmissionStateV1.HELD_IMPLEMENTATION_MISSING_NO_ADMISSION,
            PackageCompatibilityStateV1.BLOCKED_MISSING_IMPLEMENTATION,
            (PluginPackageReasonCodeV1.IMPLEMENTATION_MISSING,),
        )
    _raise(
        PluginPackageReasonCodeV1.ADMISSION_INVALID,
        "role disposition has no admission contract",
    )


def _operation_rows_from_launch(
    entries: tuple[SelectedComponentPackageEntryV1, ...],
    operations: tuple[Mapping[str, object], ...],
) -> tuple[PackageOperationEligibilityV1, ...]:
    entry_by_role = {entry.launch_role_id: entry for entry in entries}
    rows: list[PackageOperationEligibilityV1] = []
    for operation in operations:
        required = tuple(
            _component_id(role_id) for role_id in operation["required_role_ids"]
        )
        optional = tuple(
            _component_id(role_id) for role_id in operation["optional_role_ids"]
        )
        blockers = tuple(
            _component_id(role_id)
            for role_id in operation["required_role_ids"]
            if entry_by_role[role_id].admission_state
            is not PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT
        )
        rows.append(
            PackageOperationEligibilityV1(
                operation_class=operation["operation_class"],
                required_component_ids=required,
                optional_component_ids=optional,
                blocking_component_ids=blockers,
                state=(
                    PackageOperationEligibilityStateV1.BLOCKED_CURRENT_PACKAGE_NO_EFFECT
                    if blockers
                    else PackageOperationEligibilityStateV1.ELIGIBLE_CONTRACT_ONLY_NO_EFFECT
                ),
                terminal_failure_route=operation["terminal_failure_route"],
            )
        )
    return tuple(rows)


def build_selected_component_package_manifest_v1(
    launch_graph_projection: Mapping[str, object],
) -> SelectedComponentPackageManifestV1:
    graph, roles, operations = _validate_launch_projection(launch_graph_projection)
    family_rows = _selected_family_rows()
    entries: list[SelectedComponentPackageEntryV1] = []
    for role, family_row in zip(roles, family_rows, strict=True):
        role_id = role["role_id"]
        admission, compatibility, compatibility_reasons = _admission_contract(
            role["disposition"]
        )
        existing_paths = tuple(
            path_row["path"]
            for path_row in role["path_refs"]
            if path_row["disposition"] == "EXISTING_CANONICAL_OWNER"
        )
        future_paths = tuple(
            path_row["path"]
            for path_row in role["path_refs"]
            if path_row["disposition"]
            == "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
        )
        required_operations = tuple(
            operation["operation_class"]
            for operation in operations
            if role_id in operation["required_role_ids"]
        )
        optional_operations = tuple(
            operation["operation_class"]
            for operation in operations
            if role_id in operation["optional_role_ids"]
        )
        fallback_role_id = family_row["fallback_role_id_or_none"]
        entries.append(
            SelectedComponentPackageEntryV1(
                package_component_id=_component_id(role_id),
                package_version=_INITIAL_VERSION,
                launch_role_id=role_id,
                role_disposition=role["disposition"],
                admission_state=admission,
                compatibility_state=compatibility,
                compatibility_reason_codes=compatibility_reasons,
                selected_profile_ids=_SELECTED_PROFILE_IDS,
                required_operation_classes=required_operations,
                optional_operation_classes=optional_operations,
                primary_plugin_family_or_none=family_row[
                    "primary_plugin_family_or_none"
                ],
                supporting_plugin_families=tuple(
                    family_row["supporting_plugin_families"]
                ),
                existing_owner_paths=existing_paths,
                future_owner_paths=future_paths,
                canonical_output_contract=role["frozen_output"],
                direct_dependency_component_ids=tuple(
                    sorted(
                        _component_id(dependency)
                        for dependency in role["direct_prerequisite_role_ids"]
                    )
                ),
                default_failure_route=role["default_failure_route"],
                latency_class=role["latency_class"],
                rollback_target_kind=PackageRollbackTargetKindV1(
                    family_row["rollback_target_kind"]
                ),
                fallback_component_id_or_none=(
                    _component_id(fallback_role_id)
                    if fallback_role_id is not None
                    else None
                ),
                authority_envelope_id=(
                    DEFAULT_AUTHORITY_ENVELOPE.authority_envelope_id
                ),
            )
        )
    entry_tuple = tuple(entries)
    dependency_edges = tuple(
        sorted(
            (
                _component_id(edge["producer_role_id"]),
                _component_id(edge["consumer_role_id"]),
            )
            for edge in graph["dependency_edges"]
        )
    )
    topological_order = compile_selected_package_dependency_order_v1(
        tuple(entry.package_component_id for entry in entry_tuple),
        dependency_edges,
    )
    manifest = SelectedComponentPackageManifestV1(
        schema_version=_MANIFEST_SCHEMA_VERSION,
        package_id=_PACKAGE_ID,
        package_version=_INITIAL_VERSION,
        launch_graph_package_ref=_LAUNCH_GRAPH_PACKAGE_REF,
        launch_graph_schema_version=_LAUNCH_GRAPH_SCHEMA_VERSION,
        selected_scope_schema_version=_SELECTED_SCOPE_SCHEMA_VERSION,
        selected_profile_ids=_SELECTED_PROFILE_IDS,
        excluded_profile_ids=_EXCLUDED_PROFILE_IDS,
        entries=entry_tuple,
        dependency_edges=dependency_edges,
        topological_order=topological_order,
        operation_eligibility_rows=_operation_rows_from_launch(
            entry_tuple,
            operations,
        ),
        builder_runtime_implementation="CPython",
        builder_runtime_version=_BUILDER_RUNTIME_VERSION,
        canonical_serialization_policy=_CANONICAL_SERIALIZATION_POLICY,
        authority_envelope=DEFAULT_AUTHORITY_ENVELOPE,
        active_live_profile_ids=(),
    )
    receipt = validate_selected_component_package_v1(manifest)
    if receipt.terminal_state is PackageValidationTerminalStateV1.REJECTED_INVALID:
        reason = receipt.reason_codes[0]
        raise PluginPackageContractError(
            reason,
            "internally constructed selected component package did not validate",
        )
    return manifest


def _sorted_reasons(
    reasons: set[PluginPackageReasonCodeV1],
) -> tuple[PluginPackageReasonCodeV1, ...]:
    return tuple(sorted(reasons, key=lambda reason: reason.value))


def _expected_disposition(role_id: str) -> str:
    if role_id in _BINDING_ONLY_ROLE_IDS:
        return "BINDING_ONLY_GAP"
    if role_id in _EVIDENCE_ONLY_ROLE_IDS:
        return "EVIDENCE_ONLY_GAP"
    return "TRUE_MISSING_DEPENDENCY"


def validate_selected_component_package_v1(
    manifest: SelectedComponentPackageManifestV1,
) -> CompatibilityAndDependencyReceiptV1:
    """Validate one exact typed selected-component package manifest."""

    if type(manifest) is not SelectedComponentPackageManifestV1:
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "manifest must be an exact SelectedComponentPackageManifestV1",
        )

    reasons: set[PluginPackageReasonCodeV1] = set()
    if (
        manifest.schema_version != _MANIFEST_SCHEMA_VERSION
        or manifest.package_id != _PACKAGE_ID
        or manifest.launch_graph_package_ref != _LAUNCH_GRAPH_PACKAGE_REF
        or manifest.launch_graph_schema_version != _LAUNCH_GRAPH_SCHEMA_VERSION
        or manifest.selected_scope_schema_version != _SELECTED_SCOPE_SCHEMA_VERSION
    ):
        reasons.add(PluginPackageReasonCodeV1.IDENTITY_INVALID)
    if (
        manifest.selected_profile_ids != _SELECTED_PROFILE_IDS
        or manifest.excluded_profile_ids != _EXCLUDED_PROFILE_IDS
    ):
        reasons.add(PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID)
    if manifest.active_live_profile_ids:
        reasons.add(PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN)
    if (
        manifest.builder_runtime_implementation != "CPython"
        or manifest.builder_runtime_version != _BUILDER_RUNTIME_VERSION
        or manifest.canonical_serialization_policy
        != _CANONICAL_SERIALIZATION_POLICY
    ):
        reasons.add(PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED)
    if manifest.authority_envelope != DEFAULT_AUTHORITY_ENVELOPE:
        reasons.add(PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN)

    entries = manifest.entries
    family_rows = _selected_family_rows()
    if len(entries) != 28:
        reasons.add(PluginPackageReasonCodeV1.IDENTITY_INVALID)
    for index, entry in enumerate(entries):
        if index >= len(_ROLE_IDS):
            reasons.add(PluginPackageReasonCodeV1.IDENTITY_INVALID)
            continue
        role_id = _ROLE_IDS[index]
        component_id = _COMPONENT_IDS[index]
        family_row = family_rows[index]
        disposition = _expected_disposition(role_id)
        admission, compatibility, compatibility_reasons = _admission_contract(
            disposition
        )
        expected_required_operations = tuple(
            operation_class
            for operation_class, required_role_ids in zip(
                _OPERATION_CLASSES,
                _OPERATION_REQUIRED_ROLE_IDS,
                strict=True,
            )
            if role_id in required_role_ids
        )
        expected_optional_operations = tuple(
            operation_class
            for operation_class, optional_role_ids in zip(
                _OPERATION_CLASSES,
                _OPERATION_OPTIONAL_ROLE_IDS,
                strict=True,
            )
            if role_id in optional_role_ids
        )
        if (
            entry.package_component_id != component_id
            or entry.launch_role_id != role_id
        ):
            reasons.add(PluginPackageReasonCodeV1.IDENTITY_INVALID)
        if entry.package_version != manifest.package_version:
            reasons.add(PluginPackageReasonCodeV1.VERSION_INVALID)
        if (
            entry.role_disposition != disposition
            or entry.admission_state is not admission
            or entry.compatibility_state is not compatibility
            or entry.compatibility_reason_codes != compatibility_reasons
        ):
            reasons.add(PluginPackageReasonCodeV1.ADMISSION_INVALID)
        if entry.selected_profile_ids != _SELECTED_PROFILE_IDS:
            reasons.add(PluginPackageReasonCodeV1.PROFILE_SCOPE_INVALID)
        if (
            entry.required_operation_classes != expected_required_operations
            or entry.optional_operation_classes != expected_optional_operations
        ):
            reasons.add(PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID)
        if (
            entry.primary_plugin_family_or_none
            != family_row["primary_plugin_family_or_none"]
            or entry.supporting_plugin_families
            != tuple(family_row["supporting_plugin_families"])
        ):
            reasons.add(PluginPackageReasonCodeV1.FAMILY_UNKNOWN)
        if (
            entry.rollback_target_kind.value != family_row["rollback_target_kind"]
            or entry.fallback_component_id_or_none
            != (
                _component_id(family_row["fallback_role_id_or_none"])
                if family_row["fallback_role_id_or_none"] is not None
                else None
            )
        ):
            reasons.add(PluginPackageReasonCodeV1.ROLLBACK_INVALID)
        if entry.direct_dependency_component_ids != tuple(
            _component_id(prerequisite)
            for prerequisite in _DIRECT_PREREQUISITE_ROLE_IDS[index]
        ):
            reasons.add(PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE)
        if entry.authority_envelope_id != (
            DEFAULT_AUTHORITY_ENVELOPE.authority_envelope_id
        ):
            reasons.add(PluginPackageReasonCodeV1.RUNTIME_EFFECT_FORBIDDEN)
        if not (*entry.existing_owner_paths, *entry.future_owner_paths):
            reasons.add(PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID)
        for path in (*entry.existing_owner_paths, *entry.future_owner_paths):
            try:
                _safe_relative_path(path)
            except PluginPackageContractError as exc:
                reasons.add(exc.reason_code)

    if len(
        {
            path
            for entry in entries
            for path in (*entry.existing_owner_paths, *entry.future_owner_paths)
        }
    ) != 34:
        reasons.add(PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID)
    if Counter(entry.admission_state for entry in entries) != Counter(
        {
            PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT: 11,
            PackageAdmissionStateV1.HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION: 5,
            PackageAdmissionStateV1.HELD_IMPLEMENTATION_MISSING_NO_ADMISSION: 12,
        }
    ):
        reasons.add(PluginPackageReasonCodeV1.ADMISSION_INVALID)

    family_refs = tuple(
        family
        for entry in entries
        for family in (
            *((entry.primary_plugin_family_or_none,)
              if entry.primary_plugin_family_or_none is not None
              else ()),
            *entry.supporting_plugin_families,
        )
    )
    if (
        len(family_refs) != 66
        or len(set(family_refs)) != 58
        or sum(
            entry.primary_plugin_family_or_none is None
            and not entry.supporting_plugin_families
            for entry in entries
        )
        != 6
        or not set(family_refs).issubset(PLUGIN_FAMILIES)
        or len(PLUGIN_FAMILIES) != 95
    ):
        reasons.add(PluginPackageReasonCodeV1.FAMILY_UNKNOWN)

    if len(manifest.dependency_edges) != 102:
        reasons.add(PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE)
    if manifest.dependency_edges != _EXPECTED_DEPENDENCY_EDGES:
        reasons.add(PluginPackageReasonCodeV1.EDGE_UNKNOWN_NODE)
    try:
        compiled_order = compile_selected_package_dependency_order_v1(
            tuple(entry.package_component_id for entry in entries),
            manifest.dependency_edges,
        )
    except PluginPackageContractError as exc:
        reasons.add(exc.reason_code)
        compiled_order = ()
    if (
        compiled_order != _EXPECTED_TOPOLOGICAL_ORDER
        or manifest.topological_order != _EXPECTED_TOPOLOGICAL_ORDER
        or ("S1PKG::ROLE-12", "S1PKG::ROLE-11")
        not in manifest.dependency_edges
    ):
        reasons.add(PluginPackageReasonCodeV1.DEPENDENCY_CYCLE)

    operation_rows = manifest.operation_eligibility_rows
    if len(operation_rows) != 5:
        reasons.add(PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID)
    for index, row in enumerate(operation_rows):
        if index >= len(_OPERATION_CLASSES):
            reasons.add(PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID)
            continue
        if (
            row.operation_class != _OPERATION_CLASSES[index]
            or row.required_component_ids
            != tuple(
                _component_id(role_id)
                for role_id in _OPERATION_REQUIRED_ROLE_IDS[index]
            )
            or row.optional_component_ids
            != tuple(
                _component_id(role_id)
                for role_id in _OPERATION_OPTIONAL_ROLE_IDS[index]
            )
            or row.blocking_component_ids != _EXPECTED_OPERATION_BLOCKERS[index]
            or row.state
            is not PackageOperationEligibilityStateV1.BLOCKED_CURRENT_PACKAGE_NO_EFFECT
            or row.terminal_failure_route != _OPERATION_TERMINAL_ROUTES[index]
        ):
            reasons.add(PluginPackageReasonCodeV1.OPERATION_PROFILE_INVALID)

    reason_codes = _sorted_reasons(reasons)
    if reason_codes:
        terminal_state = PackageValidationTerminalStateV1.REJECTED_INVALID
    elif any(
        entry.admission_state
        is not PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT
        for entry in entries
    ):
        terminal_state = (
            PackageValidationTerminalStateV1.VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES
        )
    else:
        terminal_state = (
            PackageValidationTerminalStateV1.VALIDATED_NO_EFFECT_ALL_REQUIRED_COMPONENTS_ADMITTED
        )
    return CompatibilityAndDependencyReceiptV1(
        package_id=manifest.package_id,
        package_version=manifest.package_version,
        checked_entry_count=len(entries),
        checked_edge_count=len(manifest.dependency_edges),
        checked_operation_count=len(operation_rows),
        topological_order=manifest.topological_order,
        operation_eligibility_rows=operation_rows,
        terminal_state=terminal_state,
        reason_codes=reason_codes,
        authority_envelope=manifest.authority_envelope,
    )


def _require_valid_manifest(
    manifest: SelectedComponentPackageManifestV1,
) -> CompatibilityAndDependencyReceiptV1:
    receipt = validate_selected_component_package_v1(manifest)
    if receipt.terminal_state is PackageValidationTerminalStateV1.REJECTED_INVALID:
        _raise(
            receipt.reason_codes[0],
            "selected component package manifest is invalid",
        )
    return receipt


def _disabled_operation_rows(
    manifest: SelectedComponentPackageManifestV1,
    disabled_component_ids: tuple[str, ...],
) -> tuple[PackageOperationEligibilityV1, ...]:
    disabled = set(disabled_component_ids)
    rows: list[PackageOperationEligibilityV1] = []
    for row in manifest.operation_eligibility_rows:
        blockers = tuple(
            component_id
            for component_id in row.required_component_ids
            if component_id in set(row.blocking_component_ids)
            or component_id in disabled
        )
        rows.append(
            PackageOperationEligibilityV1(
                operation_class=row.operation_class,
                required_component_ids=row.required_component_ids,
                optional_component_ids=row.optional_component_ids,
                blocking_component_ids=blockers,
                state=(
                    PackageOperationEligibilityStateV1.BLOCKED_CURRENT_PACKAGE_NO_EFFECT
                    if blockers
                    else PackageOperationEligibilityStateV1.ELIGIBLE_CONTRACT_ONLY_NO_EFFECT
                ),
                terminal_failure_route=row.terminal_failure_route,
            )
        )
    return tuple(rows)


def derive_rollback_and_supersession_receipt_v1(
    manifest: SelectedComponentPackageManifestV1,
    *,
    predecessor_manifest: SelectedComponentPackageManifestV1 | None = None,
    disabled_component_ids: tuple[str, ...] = (),
) -> RollbackAndSupersessionReceiptV1:
    """Derive immutable no-effect disable, rollback, and retention state."""

    manifest_receipt = _require_valid_manifest(manifest)
    if type(disabled_component_ids) is not tuple or any(
        type(component_id) is not str
        or not component_id
        or component_id != component_id.strip()
        or any(ord(character) < 0x20 for character in component_id)
        for component_id in disabled_component_ids
    ):
        _raise(
            PluginPackageReasonCodeV1.ROLLBACK_INVALID,
            "disabled_component_ids must be an exact canonical text tuple",
        )
    if len(disabled_component_ids) != len(set(disabled_component_ids)):
        _raise(
            PluginPackageReasonCodeV1.ROLLBACK_INVALID,
            "disabled_component_ids must be duplicate-free",
        )
    known_component_ids = {
        entry.package_component_id for entry in manifest.entries
    }
    if not set(disabled_component_ids).issubset(known_component_ids):
        _raise(
            PluginPackageReasonCodeV1.ROLLBACK_INVALID,
            "disabled_component_ids contain an unknown package component",
        )

    predecessor_version: PackageVersionV1 | None = None
    superseded_versions: tuple[PackageVersionV1, ...] = ()
    retained_versions: tuple[PackageVersionV1, ...] = ()
    supersession_state = PackageSupersessionStateV1.INITIAL_CURRENT_NO_PREDECESSOR
    reason_codes: tuple[PluginPackageReasonCodeV1, ...] = ()
    terminal_state = manifest_receipt.terminal_state
    if predecessor_manifest is not None:
        if type(predecessor_manifest) is not SelectedComponentPackageManifestV1:
            _raise(
                PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
                "predecessor_manifest must be an exact typed manifest or None",
            )
        predecessor_receipt = validate_selected_component_package_v1(
            predecessor_manifest
        )
        predecessor_version = predecessor_manifest.package_version
        predecessor_is_valid = (
            predecessor_receipt.terminal_state
            is not PackageValidationTerminalStateV1.REJECTED_INVALID
            and predecessor_manifest.package_id == manifest.package_id
            and predecessor_manifest.schema_version == manifest.schema_version
            and predecessor_manifest.package_version < manifest.package_version
            and predecessor_manifest.authority_envelope
            == manifest.authority_envelope
        )
        if predecessor_is_valid:
            superseded_versions = (predecessor_version,)
            retained_versions = (predecessor_version,)
            supersession_state = (
                PackageSupersessionStateV1.VALIDATED_MONOTONE_SUPERSESSION
            )
        else:
            supersession_state = (
                PackageSupersessionStateV1.REJECTED_NON_MONOTONE_OR_INCOMPATIBLE
            )
            terminal_state = PackageValidationTerminalStateV1.REJECTED_INVALID
            reason_codes = _sorted_reasons(
                {
                    *predecessor_receipt.reason_codes,
                    PluginPackageReasonCodeV1.ROLLBACK_INVALID,
                }
            )

    return RollbackAndSupersessionReceiptV1(
        package_id=manifest.package_id,
        package_version=manifest.package_version,
        predecessor_package_version_or_none=predecessor_version,
        superseded_package_versions=superseded_versions,
        retained_predecessor_versions=retained_versions,
        disabled_component_ids=disabled_component_ids,
        operation_eligibility_rows=_disabled_operation_rows(
            manifest,
            disabled_component_ids,
        ),
        supersession_state=supersession_state,
        terminal_state=terminal_state,
        reason_codes=reason_codes,
        authority_envelope=manifest.authority_envelope,
    )


def validate_package_supersession_v1(
    previous: SelectedComponentPackageManifestV1,
    candidate: SelectedComponentPackageManifestV1,
) -> RollbackAndSupersessionReceiptV1:
    """Validate strictly increasing append-only selected-package mechanics."""

    if (
        type(previous) is not SelectedComponentPackageManifestV1
        or type(candidate) is not SelectedComponentPackageManifestV1
    ):
        _raise(
            PluginPackageReasonCodeV1.CANONICAL_INPUT_INVALID,
            "previous and candidate must be exact typed manifests",
        )
    previous_receipt = validate_selected_component_package_v1(previous)
    candidate_receipt = validate_selected_component_package_v1(candidate)
    valid = (
        previous_receipt.terminal_state
        is not PackageValidationTerminalStateV1.REJECTED_INVALID
        and candidate_receipt.terminal_state
        is not PackageValidationTerminalStateV1.REJECTED_INVALID
        and previous.package_id == candidate.package_id
        and previous.schema_version == candidate.schema_version
        and candidate.package_version > previous.package_version
        and previous.authority_envelope == candidate.authority_envelope
    )
    if valid:
        return RollbackAndSupersessionReceiptV1(
            package_id=candidate.package_id,
            package_version=candidate.package_version,
            predecessor_package_version_or_none=previous.package_version,
            superseded_package_versions=(previous.package_version,),
            retained_predecessor_versions=(previous.package_version,),
            disabled_component_ids=(),
            operation_eligibility_rows=candidate.operation_eligibility_rows,
            supersession_state=(
                PackageSupersessionStateV1.VALIDATED_MONOTONE_SUPERSESSION
            ),
            terminal_state=candidate_receipt.terminal_state,
            reason_codes=(),
            authority_envelope=candidate.authority_envelope,
        )
    return RollbackAndSupersessionReceiptV1(
        package_id=candidate.package_id,
        package_version=candidate.package_version,
        predecessor_package_version_or_none=previous.package_version,
        superseded_package_versions=(),
        retained_predecessor_versions=(),
        disabled_component_ids=(),
        operation_eligibility_rows=candidate.operation_eligibility_rows,
        supersession_state=(
            PackageSupersessionStateV1.REJECTED_NON_MONOTONE_OR_INCOMPATIBLE
        ),
        terminal_state=PackageValidationTerminalStateV1.REJECTED_INVALID,
        reason_codes=_sorted_reasons(
            {
                *previous_receipt.reason_codes,
                *candidate_receipt.reason_codes,
                PluginPackageReasonCodeV1.SUPERSESSION_INVALID,
            }
        ),
        authority_envelope=candidate.authority_envelope,
    )


def _build_selected_component_package_core_v1(
    launch_graph_projection: Mapping[str, object],
) -> Mapping[str, object]:
    manifest = build_selected_component_package_manifest_v1(
        launch_graph_projection
    )
    compatibility = _require_valid_manifest(manifest)
    rollback = derive_rollback_and_supersession_receipt_v1(manifest)
    if rollback.terminal_state is PackageValidationTerminalStateV1.REJECTED_INVALID:
        _raise(
            rollback.reason_codes[0],
            "initial package rollback receipt is invalid",
        )
    return MappingProxyType(
        {
            "manifest": manifest,
            "compatibility_and_dependency": compatibility,
            "rollback_and_supersession": rollback,
        }
    )


def rebuild_selected_component_package_v1(
    launch_graph_projection: Mapping[str, object],
) -> PackageReproducibilityReceiptV1:
    """Perform two independent pure builds and compare canonical core bytes."""

    first_core = _build_selected_component_package_core_v1(
        launch_graph_projection
    )
    second_core = _build_selected_component_package_core_v1(
        launch_graph_projection
    )
    first_json = _canonical_package_json(first_core)
    second_json = _canonical_package_json(second_core)
    second_build_byte_equal = first_json.encode("utf-8") == second_json.encode(
        "utf-8"
    )
    manifest = first_core["manifest"]
    if type(manifest) is not SelectedComponentPackageManifestV1:
        _raise(
            PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED,
            "core build emitted an unsupported manifest shape",
        )
    return PackageReproducibilityReceiptV1(
        package_id=manifest.package_id,
        package_version=manifest.package_version,
        canonical_input_refs=(
            _LAUNCH_GRAPH_PACKAGE_REF,
            _LAUNCH_GRAPH_SCHEMA_VERSION,
            _SELECTED_SCOPE_SCHEMA_VERSION,
        ),
        builder_runtime_implementation=manifest.builder_runtime_implementation,
        builder_runtime_version=manifest.builder_runtime_version,
        canonical_serialization_policy=manifest.canonical_serialization_policy,
        canonical_core_projection_json=first_json,
        second_build_byte_equal=second_build_byte_equal,
        pure_build_effect_count=0,
        terminal_state=(
            PackageValidationTerminalStateV1.VALIDATED_NO_EFFECT_WITH_HELD_DEPENDENCIES
            if second_build_byte_equal
            else PackageValidationTerminalStateV1.REJECTED_INVALID
        ),
        reason_codes=(
            ()
            if second_build_byte_equal
            else (PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED,)
        ),
        authority_envelope=manifest.authority_envelope,
    )


def selected_component_package_projection_v1(
    launch_graph_projection: Mapping[str, object],
) -> Mapping[str, object]:
    """Return the immutable four-key selected-component package projection."""

    core = _build_selected_component_package_core_v1(launch_graph_projection)
    reproducibility = rebuild_selected_component_package_v1(
        launch_graph_projection
    )
    if (
        reproducibility.terminal_state
        is PackageValidationTerminalStateV1.REJECTED_INVALID
        or not reproducibility.second_build_byte_equal
        or reproducibility.pure_build_effect_count != 0
        or reproducibility.canonical_core_projection_json
        != _canonical_package_json(core)
    ):
        _raise(
            PluginPackageReasonCodeV1.REPRODUCIBILITY_FAILED,
            "selected package core failed independent byte reconstruction",
        )
    return MappingProxyType(
        {
            "manifest": core["manifest"],
            "compatibility_and_dependency": core[
                "compatibility_and_dependency"
            ],
            "rollback_and_supersession": core["rollback_and_supersession"],
            "reproducibility": reproducibility,
        }
    )


@dataclass
class PluginRegistry:
    adapters: dict[str, PluginAdapterBase] = field(default_factory=dict)

    def register(self, plugin_id: str, adapter: PluginAdapterBase) -> None:
        if not plugin_id:
            raise ValueError("plugin_id is required")
        self.adapters[plugin_id] = adapter

    def get(self, plugin_id: str) -> PluginAdapterBase:
        return self.adapters[plugin_id]

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.adapters))
