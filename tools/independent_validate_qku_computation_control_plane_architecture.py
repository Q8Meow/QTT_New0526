#!/usr/bin/env python3
"""Independent architecture and its exact 29-row mathematical reconstruction.

This validator intentionally does not import the production package or primary
validator.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from itertools import combinations, product
import json
import math
from math import log, sqrt
from pathlib import Path
from random import Random
from statistics import NormalDist
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
PRODUCTION_NAMES = (
    "__init__.py",
    "models.py",
    "errors.py",
    "context.py",
    "specification.py",
    "implementation_registry.py",
    "identity_adapter.py",
    "plugin_adapter.py",
    "quantum_adapter.py",
    "source_policy.py",
    "parameter_policy.py",
    "bindings.py",
    "dependency_graph.py",
    "oracle_contracts.py",
    "authority.py",
    "agent_policy.py",
    "protocols.py",
    "serialization.py",
    "validation.py",
    "source_rights.py",
    "contextual_computability.py",
    "fallback.py",
    "freshness.py",
    "input_resolver.py",
    "point_in_time.py",
    "service.py",
    "stack_resolver.py",
    "unit_conversion.py",
    "accounting.py",
    "economic_math.py",
    "idempotency.py",
    "lifecycle.py",
    "latency_policy.py",
    "migrations.py",
    "outbox.py",
    "persistence.py",
    "receipts.py",
    "rollback.py",
    "sqlite_reference.py",
    "transaction.py",
    "mode_snapshot_policy.py",
    "cohort_compiler.py",
    "input_lock.py",
    "evidence.py",
    "model_risk.py",
    "quantum_benchmark.py",
    "llm_gateway.py",
    "existing_owner_projection.py",
    "stage1_launch_graph.py",
)
EXPECTED_MATH_IDS = tuple(f"MATH-{value:02d}" for value in range(1, 16))
ARCHITECTURE_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(1, 26)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
CURRENT_ST12B_ARCHITECTURE_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(16, 26)),
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
_LEGACY_GOLDEN_REGRESSION_TIER = "LEGACY_GOLDEN_REGRESSION"
_CURRENT_FULL_CONTRACT_TIER = "CURRENT_FULL_CONTRACT"
_LEGACY_NOT_CLAIMED = "NOT_CLAIMED_FOR_LEGACY_REGRESSION_TIER"
_CURRENT_LEGACY_NOT_APPLICABLE = (
    "NOT_APPLICABLE_FOR_CURRENT_FULL_CONTRACT_TIER"
)
_EVIDENCE_TIER_BY_MATH_ID = MappingProxyType(
    {
        "MATH-01": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-02": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-03": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-04": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-05": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-06": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-07": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-08": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-09": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-10": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-11": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-12": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-13": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-14": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-15": _LEGACY_GOLDEN_REGRESSION_TIER,
        "MATH-16": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-17": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-18": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-19": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-20": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-21": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-22": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-23": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-24": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-25": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-46": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-47": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-48": _CURRENT_FULL_CONTRACT_TIER,
        "MATH-49": _CURRENT_FULL_CONTRACT_TIER,
    }
)
EXPECTED_ALL_MATH_IDS = (
    *EXPECTED_MATH_IDS,
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
EXPECTED_ST12B_MATH_IDS = (
    *(f"MATH-{value:02d}" for value in range(1, 26)),
    "MATH-36",
    "MATH-46",
    "MATH-47",
    "MATH-48",
    "MATH-49",
)
SHARED_VALIDATION_TEST_PATHS = (
    "tests/fail_closed/test_run_validation_gates.py",
    "tests/tools/test_changed_area_validation_router.py",
    "tests/tools/test_validation_inventory.py",
    "tests/tools/test_validation_scope_registry.py",
    "tests/tools/test_ci_branch_context.py",
)
FORMULA_EXECUTION_FIELDS = (
    "canonical_component_id",
    "canonical_qku_ids",
    "canonical_formula_id_or_null",
    "canonical_algorithm_id_or_null",
    "semantic_version",
    "contract_version",
    "component_kind",
    "identity_authority_state",
    "specification_ref",
    "implementation_ref",
    "binding_profile_ref",
    "parameter_policy_refs",
    "dependency_graph_ref",
    "oracle_pack_ref",
    "evidence_bundle_ref",
    "mode_eligibility_ref",
    "registered_fallback_ref",
    "latency_class",
    "consumer_refs",
    "typed_input_contract",
    "typed_output_contract",
    "context_key",
    "authority_envelope",
)
EVIDENCE_BUNDLE_FIELDS = (
    "evidence_id",
    "schema_version",
    "contract_version",
    "evidence_bundle_version",
    "component_or_template_ref",
    "input_lock_id",
    "actual_executed_component_versions",
    "actual_executed_stack_versions",
    "replay_result_ref",
    "paper_result_ref",
    "divergence_assessment_ref",
    "lane_execution_receipt_refs",
    "calibration_and_probability_quality",
    "transaction_cost_decomposition",
    "fill_and_queue_quality",
    "latency_and_staleness",
    "capacity_and_crowding",
    "portfolio_marginal_contribution",
    "false_discovery_and_overfit_controls",
    "regime_and_scenario_outcomes",
    "uncertainty_and_model_risk_reserves",
    "agent_and_model_disagreement",
    "no_trade_comparison",
    "independent_review_state",
    "failure_and_negative_evidence_states",
    "source_and_provenance_refs",
    "d_evidence_reference_projection",
    "g_handoff_projection",
    "terminal_state",
    "blocker_codes",
)
SUCCESS_MARKER = "QKU_ARCHITECTURE_INDEPENDENTLY_VALIDATED"
EVIDENCE_MARKER = "ST12_ARCHITECTURE_MATH_EVIDENCE_V1"
CURRENT_FULL_CONTRACT_EVIDENCE_MARKER = (
    "ST12_ARCHITECTURE_CURRENT_FULL_CONTRACT_EVIDENCE_V1"
)
STAGE1_LAUNCH_GRAPH_MARKER = "STAGE1_LAUNCH_GRAPH_V2_INDEPENDENTLY_VALIDATED"
_EXPECTED_STAGE1_SELECTED_PROFILE_IDS = (
    "GEMINI_TITAN_DIRECT",
    "POLYMARKET_US_RETAIL_DIRECT",
    "KALSHI_US_DCM_DIRECT",
)
_EXPECTED_STAGE1_EXCLUDED_PROFILE_IDS = (
    "FORECASTEX_IBKR",
    "FORECASTEX_DIRECT_MEMBER",
)
_EXPECTED_STAGE1_TOPOLOGICAL_ORDER = (
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
_EXPECTED_STAGE1_OPERATION_CLASSES = (
    "NEW_OR_INCREASED_EXPOSURE",
    "CANCEL_QUERY_RECONCILE",
    "RISK_REDUCING_POSITION_ACTION",
    "REPLAY_PAPER_EVIDENCE",
    "QUANTUM_CHALLENGER_RESEARCH",
)
_EXPECTED_STAGE1_VENUE_PROFILE_ROWS_JSON = r"""[
  {
    "profile_id": "GEMINI_TITAN_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 1,
    "operating_legal_entity": "Gemini Titan, LLC",
    "clearing_or_access_route": "Gemini Olympus, LLC",
    "product_family": "GEMINI_PREDICTION_MARKETS_EVENT_CONTRACTS",
    "api_profile": "DIRECT_ACCOUNT_SCOPED_REST_WEBSOCKET",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "POLYMARKET_US_RETAIL_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 2,
    "operating_legal_entity": "QCX LLC d/b/a Polymarket US",
    "clearing_or_access_route": "QC Clearing LLC d/b/a Polymarket Clearing",
    "product_family": "POLYMARKET_US_RETAIL_EVENT_CONTRACTS",
    "api_profile": "RETAIL_APP_USER_REST_MARKET_PRIVATE_WEBSOCKET",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "KALSHI_US_DCM_DIRECT",
    "scope_state": "SELECTED_CORE",
    "serialization_ordinal_or_none": 3,
    "operating_legal_entity": "KalshiEX LLC",
    "clearing_or_access_route": "Kalshi Klear LLC",
    "product_family": "KALSHI_EVENT_CONTRACTS",
    "api_profile": "DIRECT_REST_WEBSOCKET_FIX_IF_ENTITLED",
    "jurisdiction": "UNITED_STATES_CFTC_DCM_DCO",
    "authority_ref": "S1-SCOPE-DECISION-01::LaunchScopeDecisionV1",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "profile_id": "FORECASTEX_IBKR",
    "scope_state": "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION",
    "serialization_ordinal_or_none": null,
    "operating_legal_entity": "ForecastEx LLC",
    "clearing_or_access_route": "Interactive Brokers access route",
    "product_family": "FORECASTEX_EVENT_CONTRACTS",
    "api_profile": "INTERMEDIATED_IBKR",
    "jurisdiction": "UNITED_STATES_CFTC_DCM",
    "authority_ref": "CURRENT_OWNER_EXCLUSION",
    "research_state": "NOT_APPLICABLE_WITH_PROOF"
  },
  {
    "profile_id": "FORECASTEX_DIRECT_MEMBER",
    "scope_state": "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION",
    "serialization_ordinal_or_none": null,
    "operating_legal_entity": "ForecastEx LLC",
    "clearing_or_access_route": "Direct member route",
    "product_family": "FORECASTEX_EVENT_CONTRACTS",
    "api_profile": "DIRECT_MEMBER",
    "jurisdiction": "UNITED_STATES_CFTC_DCM",
    "authority_ref": "CURRENT_OWNER_EXCLUSION",
    "research_state": "NOT_APPLICABLE_WITH_PROOF"
  }
]"""
_EXPECTED_STAGE1_LAUNCH_ROLE_ROWS_JSON = r"""[
  {
    "role_id": "ROLE-01",
    "responsibility": "Canonical venue/product/account/API-profile identity",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Identity/specification owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/stage1_launch_graph.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/identity_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/specification.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Stage1SelectedScopeV2 plus exact compound profile identities and authority lineage",
    "direct_prerequisite_role_ids": [],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-02",
    "responsibility": "Market/event/contract discovery",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Source/PIT owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/market_data.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Current contract inventory with lifecycle and resolution binding",
    "direct_prerequisite_role_ids": [
      "ROLE-01"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-03",
    "responsibility": "Point-in-time source acceptance",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Source/rights/PIT owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_rights.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Observed/effective/available/received/processed clocks and rights",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-04",
    "responsibility": "Local order-book reconstruction",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Selected venue public-state owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/market_data.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Snapshot + contiguous deltas + gap/reconnect receipt",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-05",
    "responsibility": "Trade-flow and microstructure features",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU computation owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Point-in-time feature vector with own-action lineage",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-04"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-06",
    "responsibility": "Market-implied probability/fair value",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU computation owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Executable-side probability/fair value under exact scale",
    "direct_prerequisite_role_ids": [
      "ROLE-04"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-07",
    "responsibility": "Source/model probability and calibration",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Evidence/model-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Versioned probability distribution and calibration artifact",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-05",
      "ROLE-06"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-08",
    "responsibility": "Uncertainty decomposition",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Evidence/model-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Typed source/model/parameter/regime/execution/latency/settlement vector",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-07"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-09",
    "responsibility": "Fee/rebate/reward computation",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Binding plus economic-math owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/bindings.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/profiles.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Exact effective-time/eligibility/rounding/embedding result",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-02",
      "ROLE-03"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-10",
    "responsibility": "Executable depth/slippage/impact",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU economic-math owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Exact book walk plus residual impact and embedding ledger",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-09"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-11",
    "responsibility": "Fill and partial-fill distribution",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Evidence/model owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Contextual fill probability and quantity distribution",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-05",
      "ROLE-10",
      "ROLE-12"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-12",
    "responsibility": "Queue position and survival",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-science owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Native queue state or independently validated proxy",
    "direct_prerequisite_role_ids": [
      "ROLE-04",
      "ROLE-05"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-13",
    "responsibility": "Adverse selection and markout",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "TCA/evidence owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Conditional signed markout distribution by horizon/context",
    "direct_prerequisite_role_ids": [
      "ROLE-05",
      "ROLE-11"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-14",
    "responsibility": "Latency-decay curve and economic-TTL inputs",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Latency/economic owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/latency_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Versioned net-cash decay function, current opportunity age, joint latency safety margin, and deterministic TTL resolver",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-04",
      "ROLE-05"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-15",
    "responsibility": "Expected executable net cash",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Economic/accounting owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Complete projected executable cash once, with embedding flags",
    "direct_prerequisite_role_ids": [
      "ROLE-06",
      "ROLE-07",
      "ROLE-08",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-13",
      "ROLE-14"
    ],
    "default_failure_route": "UNAVAILABLE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-16",
    "responsibility": "Joint robust net-cash LCB and final economic TTL",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Evidence/model-risk/QKU owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/model_risk.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Dependent lower bound versus NO_TRADE/best alternative plus final positive-TTL decision",
    "direct_prerequisite_role_ids": [
      "ROLE-08",
      "ROLE-15"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "PRECOMPUTED_ARTIFACT_PLUS_BOUNDED_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-17",
    "responsibility": "Cash/reservation/order-custody truth",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Accounting/capital-risk/private-state owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/transaction.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/persistence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/private_state.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/reconciliation.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "OrderCustodyStateV2 and conservative reservations",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-18",
    "responsibility": "Hard risk and exposure",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Capital-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Exact selected scope and cash/event/venue/concentration/drawdown gates",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-17"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-19",
    "responsibility": "Position sizing",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "QKU/capital-risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Micro-only cash size under robust edge/capacity/loss caps",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-17",
      "ROLE-18"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-20",
    "responsibility": "Portfolio and capital-time allocation",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Portfolio/QKU/quantum owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/implementation_registry.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Deterministic classical constrained allocation plus optional challenger",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-21",
    "responsibility": "Entry/execution action policy",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-policy owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/lifecycle.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "MAKE/TAKE/SPLIT/WAIT/CANCEL/NO_TRADE state machine",
    "direct_prerequisite_role_ids": [
      "ROLE-14",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-19",
      "ROLE-20",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "BOUNDED_HOTPATH_COMPUTE",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-22",
    "responsibility": "Exit/hold/reduce/hedge/reverse policy",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "Execution-policy/lifecycle/risk owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/lifecycle.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/capital_risk/stage1_risk_policy.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Bounded current-state lifecycle policy",
    "direct_prerequisite_role_ids": [
      "ROLE-14",
      "ROLE-15",
      "ROLE-17",
      "ROLE-18",
      "ROLE-26"
    ],
    "default_failure_route": "SAFE_HOLD",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-23",
    "responsibility": "TCA and realized attribution",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "TCA/evidence/accounting owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/economic_math.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/evidence.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/accounting.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Attempt-level source/model/execution/cost attribution",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-09",
      "ROLE-10",
      "ROLE-11",
      "ROLE-13",
      "ROLE-14",
      "ROLE-17",
      "ROLE-21",
      "ROLE-22"
    ],
    "default_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "latency_class": "OFFLINE_EVIDENCE_ONLY",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-24",
    "responsibility": "Mode/ALLOW/snapshot eligibility",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Mode/snapshot owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/mode_snapshot_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/authority.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Pinned graph/source/evidence/security/risk/owner envelope",
    "direct_prerequisite_role_ids": [
      "ROLE-03",
      "ROLE-08",
      "ROLE-16",
      "ROLE-17",
      "ROLE-18",
      "ROLE-21",
      "ROLE-22",
      "ROLE-23",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-25",
    "responsibility": "Sole venue-write release",
    "disposition": "TRUE_MISSING_DEPENDENCY",
    "semantic_owner": "ExecutionRouterV1 owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/selected_venues/execution_router.py",
        "disposition": "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
      }
    ],
    "frozen_output": "Idempotent stale-checked fenced custody-aware dispatch",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-14",
      "ROLE-17",
      "ROLE-18",
      "ROLE-21",
      "ROLE-22",
      "ROLE-24",
      "ROLE-26",
      "ROLE-28"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "SOLE_WRITE_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-26",
    "responsibility": "Deterministic classical fallback",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Dependency/fallback owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/dependency_graph.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/fallback.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Same-input admissible fallback for every selected path",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03"
    ],
    "default_failure_route": "NO_TRADE",
    "latency_class": "IMMUTABLE_PRECOMPUTED_SNAPSHOT_LOOKUP",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-27",
    "responsibility": "Quantum challenger artifact",
    "disposition": "EVIDENCE_ONLY_GAP",
    "semantic_owner": "Quantum mapper/benchmark owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/quantum_benchmark.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/plugin_adapter.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Same-formulation challenger with feasibility/economic interpret-back",
    "direct_prerequisite_role_ids": [
      "ROLE-16",
      "ROLE-20",
      "ROLE-26"
    ],
    "default_failure_route": "CLASSICAL_ONLY",
    "latency_class": "ASYNC_CHALLENGER_ONLY",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "role_id": "ROLE-28",
    "responsibility": "Agent capability and duty enforcement",
    "disposition": "BINDING_ONLY_GAP",
    "semantic_owner": "Agent/LLM policy owner",
    "path_refs": [
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/agent_policy.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      },
      {
        "path": "src/qtt/stage1_prediction_markets/qku_computation_control_plane/llm_gateway.py",
        "disposition": "EXISTING_CANONICAL_OWNER"
      }
    ],
    "frozen_output": "Typed tasks, duties, budgets, abstention, quarantine",
    "direct_prerequisite_role_ids": [
      "ROLE-01",
      "ROLE-03",
      "ROLE-26"
    ],
    "default_failure_route": "SUBMIT_DISABLED",
    "latency_class": "HARD_CONTROL_HOTPATH",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  }
]"""
_EXPECTED_STAGE1_OPERATION_PROFILE_ROWS_JSON = r"""[
  {
    "operation_class": "NEW_OR_INCREASED_EXPOSURE",
    "required_role_ids": [
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
      "ROLE-19",
      "ROLE-20",
      "ROLE-21",
      "ROLE-22",
      "ROLE-23",
      "ROLE-24",
      "ROLE-25",
      "ROLE-26",
      "ROLE-28"
    ],
    "optional_role_ids": [
      "ROLE-27"
    ],
    "terminal_failure_route": "NO_TRADE_AND_SUBMIT_DISABLED",
    "purpose": "Full release-critical lifecycle closure for any new or increased exposure.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "CANCEL_QUERY_RECONCILE",
    "required_role_ids": [
      "ROLE-01",
      "ROLE-17",
      "ROLE-24",
      "ROLE-25",
      "ROLE-28"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD",
    "purpose": "Narrow emergency/control path independent of public-source, market-discovery, alpha, hard-risk computation, portfolio, and quantum availability.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "RISK_REDUCING_POSITION_ACTION",
    "required_role_ids": [
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
      "ROLE-28"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "SAFE_HOLD",
    "purpose": "Bounded hold, cancel-only, reduce-only, close-only, offset, or exact reverse using current authoritative state.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "REPLAY_PAPER_EVIDENCE",
    "required_role_ids": [
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
      "ROLE-28"
    ],
    "optional_role_ids": [
      "ROLE-27"
    ],
    "terminal_failure_route": "EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
    "purpose": "Immutable-input replay and distinct PAPER evidence without order authority.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  },
  {
    "operation_class": "QUANTUM_CHALLENGER_RESEARCH",
    "required_role_ids": [
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
      "ROLE-27"
    ],
    "optional_role_ids": [],
    "terminal_failure_route": "CLASSICAL_ONLY",
    "purpose": "Same-formulation true-quantum challenger evidence with deterministic classical fallback.",
    "consumption_law": "EXECUTE_ONLY_HOTPATH_CLASS_ROLES_AND_READ_VERSION_PINNED_CURRENT_OUTPUTS_FOR_PRECOMPUTED_OFFLINE_OR_ASYNC_ROLES",
    "research_state": "COMPLETE_NO_CODEX_MATERIAL_DECISION_RESEARCH_REQUIRED"
  }
]"""

DECIMAL_CONTEXT = Context(prec=34, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class _ArchitectureMathEvidenceV1:
    math_id: str
    evidence_tier: str
    oracle_id: str
    golden_vector_id: str
    comparison_policy: str
    independent_algorithm_id: str
    actual_observed_evidence: object
    golden_comparison_passed: bool
    formula_or_procedure_mutation_observed: bool
    domain_guard_rejection_observed: bool
    precision_or_tolerance_mutation_observed: bool | str
    semantic_binding_mutation_observed: bool | str
    production_import_count: int
    production_callable_count: int
    terminal_state: str
    legacy_golden_observation: object
    legacy_formula_regression_mutation_observation: object
    legacy_domain_rejection_observation: object
    boundary_vector_id: object
    negative_vector_id: object
    property_id: object
    current_output_schema: object
    declared_comparison_policy: object
    compiled_comparison_mode: str
    compiled_absolute_tolerance_or_not_applicable: str
    comparator_registry_version: object
    comparator_authority_classification: object
    numeric_text_leaf_paths: object
    numeric_text_representation: object
    comparison_execution_trace: object
    comparison_policy_execution_observed: bool
    golden_observation: object
    boundary_observation: object
    negative_exception_observation: object
    property_mutation_observation: object
    actual_execution_mutation_observation: object
    semantic_binding_mutation_observation: object


def _stationary_means(
    seed: int,
    series: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0, 5.0),
) -> tuple[float, ...]:
    if len(series) < 2:
        raise ValueError("series too short")
    rng = Random(seed)
    results: list[float] = []
    for _ in range(64):
        current = rng.randrange(len(series))
        sample = [series[current]]
        for _position in range(1, len(series)):
            if rng.random() < 0.5:
                current = rng.randrange(len(series))
            else:
                current = (current + 1) % len(series)
            sample.append(series[current])
        results.append(sum(sample) / len(sample))
    return tuple(results)


def _string_literal(tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    raise ValueError(f"missing string literal: {name}")


def _json_rows(tree: ast.Module, name: str) -> list[dict[str, object]]:
    value = json.loads(_string_literal(tree, name))
    if not isinstance(value, list) or any(
        not isinstance(row, dict) for row in value
    ):
        raise ValueError(f"{name} must be a JSON array of objects")
    return value


def _stage1_launch_graph_failures() -> list[str]:
    """Independently reconstruct the frozen launch graph from source literals."""

    failures: list[str] = []
    source_path = PACKAGE / "stage1_launch_graph.py"
    try:
        source_text = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(source_path))
        profile_rows = _json_rows(tree, "_STAGE1_VENUE_PROFILE_ROWS_JSON")
        role_rows = _json_rows(tree, "_STAGE1_LAUNCH_ROLE_ROWS_JSON")
        operation_rows = _json_rows(
            tree,
            "_STAGE1_OPERATION_PROFILE_ROWS_JSON",
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        return [f"Stage-1 launch graph literals could not be reconstructed: {exc}"]

    expected_profile_rows = json.loads(
        _EXPECTED_STAGE1_VENUE_PROFILE_ROWS_JSON
    )
    expected_role_rows = json.loads(_EXPECTED_STAGE1_LAUNCH_ROLE_ROWS_JSON)
    expected_operation_rows = json.loads(
        _EXPECTED_STAGE1_OPERATION_PROFILE_ROWS_JSON
    )
    if profile_rows != expected_profile_rows:
        failures.append("Stage-1 venue-profile rows differ from independent rows")
    if role_rows != expected_role_rows:
        failures.append("Stage-1 launch-role rows differ from independent rows")
    if operation_rows != expected_operation_rows:
        failures.append("Stage-1 operation rows differ from independent rows")

    expected_profile_fields = (
        "profile_id",
        "scope_state",
        "serialization_ordinal_or_none",
        "operating_legal_entity",
        "clearing_or_access_route",
        "product_family",
        "api_profile",
        "jurisdiction",
        "authority_ref",
        "research_state",
    )
    expected_role_fields = (
        "role_id",
        "responsibility",
        "disposition",
        "semantic_owner",
        "path_refs",
        "frozen_output",
        "direct_prerequisite_role_ids",
        "default_failure_route",
        "latency_class",
        "research_state",
    )
    expected_path_fields = ("path", "disposition")
    expected_operation_fields = (
        "operation_class",
        "required_role_ids",
        "optional_role_ids",
        "terminal_failure_route",
        "purpose",
        "consumption_law",
        "research_state",
    )
    if len(profile_rows) != 5 or any(
        tuple(row) != expected_profile_fields for row in profile_rows
    ):
        failures.append("Stage-1 profile count or schema differs")
    if len(role_rows) != 28 or any(
        tuple(row) != expected_role_fields for row in role_rows
    ):
        failures.append("Stage-1 role count or schema differs")
    if len(operation_rows) != 5 or any(
        tuple(row) != expected_operation_fields for row in operation_rows
    ):
        failures.append("Stage-1 operation count or schema differs")

    selected_rows = tuple(
        row for row in profile_rows if row.get("scope_state") == "SELECTED_CORE"
    )
    excluded_rows = tuple(
        row
        for row in profile_rows
        if row.get("scope_state") == "OWNER_EXCLUDED_STAGE1_NO_IMPLEMENTATION"
    )
    try:
        selected_serialization = tuple(
            str(row["profile_id"])
            for row in sorted(
                selected_rows,
                key=lambda row: int(row["serialization_ordinal_or_none"]),
            )
        )
    except (KeyError, TypeError, ValueError):
        selected_serialization = ()
    excluded_profile_ids = tuple(
        str(row.get("profile_id")) for row in excluded_rows
    )
    all_profile_ids = tuple(str(row.get("profile_id")) for row in profile_rows)
    if (
        len(selected_rows) != 3
        or selected_serialization != _EXPECTED_STAGE1_SELECTED_PROFILE_IDS
        or any(
            row.get("serialization_ordinal_or_none") != ordinal
            for ordinal, row in enumerate(
                sorted(
                    selected_rows,
                    key=lambda row: (
                        row.get("serialization_ordinal_or_none")
                        if isinstance(
                            row.get("serialization_ordinal_or_none"), int
                        )
                        else 99
                    ),
                ),
                start=1,
            )
        )
    ):
        failures.append("Stage-1 selected profile serialization differs")
    if (
        len(excluded_rows) != 2
        or excluded_profile_ids != _EXPECTED_STAGE1_EXCLUDED_PROFILE_IDS
        or any(
            row.get("serialization_ordinal_or_none") is not None
            for row in excluded_rows
        )
    ):
        failures.append("Stage-1 owner-excluded profile set differs")
    if "POLYMARKET" in all_profile_ids:
        failures.append("generic POLYMARKET profile identity is forbidden")
    if any(
        str(row.get("profile_id", "")).startswith("FORECASTEX")
        for row in selected_rows
    ):
        failures.append("ForecastEx is active in the selected profile set")

    expected_role_ids = tuple(f"ROLE-{value:02d}" for value in range(1, 29))
    role_ids = tuple(str(row.get("role_id")) for row in role_rows)
    role_id_counts = Counter(role_ids)
    if role_ids != expected_role_ids or any(
        count != 1 for count in role_id_counts.values()
    ):
        failures.append("Stage-1 role identity closure differs")
    disposition_counts = Counter(str(row.get("disposition")) for row in role_rows)
    if disposition_counts != Counter(
        {
            "BINDING_ONLY_GAP": 11,
            "EVIDENCE_ONLY_GAP": 5,
            "TRUE_MISSING_DEPENDENCY": 12,
        }
    ):
        failures.append("Stage-1 11/5/12 role disposition closure differs")

    path_references: list[tuple[str, str, str]] = []
    for role in role_rows:
        role_id = str(role.get("role_id"))
        refs = role.get("path_refs")
        if not isinstance(refs, list):
            failures.append(f"{role_id}: path_refs is not a JSON list")
            continue
        for ref in refs:
            if not isinstance(ref, dict) or tuple(ref) != expected_path_fields:
                failures.append(f"{role_id}: path-reference schema differs")
                continue
            path_references.append(
                (role_id, str(ref.get("path")), str(ref.get("disposition")))
            )

    def safe_relative_path(value: str) -> bool:
        if (
            not value
            or value != value.strip()
            or "\\" in value
            or ":" in value
            or value.startswith(("/", "./", "../"))
            or any(token in value for token in ("*", "?", "[", "]"))
            or any(ord(character) < 0x20 for character in value)
        ):
            return False
        segments = value.split("/")
        return bool(segments) and all(segment not in {"", ".", ".."} for segment in segments)

    if len(path_references) != 68:
        failures.append("Stage-1 role path-reference denominator differs")
    if len({path for _role, path, _disposition in path_references}) != 34:
        failures.append("Stage-1 distinct role-path denominator differs")
    if any(not safe_relative_path(path) for _role, path, _disp in path_references):
        failures.append("Stage-1 role path is not a safe exact relative path")
    final_dispositions = Counter(
        disposition for _role, _path, disposition in path_references
    )
    if final_dispositions != Counter(
        {
            "EXISTING_CANONICAL_OWNER": 57,
            "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED": 11,
        }
    ):
        failures.append("Stage-1 57/11 path-disposition closure differs")
    for _role, path, disposition in path_references:
        resolved = REPO_ROOT / path
        if disposition == "EXISTING_CANONICAL_OWNER" and not resolved.is_file():
            failures.append(f"Stage-1 existing owner path is missing: {path}")
        if (
            disposition == "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
            and resolved.exists()
        ):
            failures.append(f"Stage-1 future owner path already exists: {path}")

    role_set = set(role_ids)
    role_by_id = {str(row.get("role_id")): row for row in role_rows}
    edges: list[tuple[str, str]] = []
    for role in role_rows:
        consumer = str(role.get("role_id"))
        prerequisites = role.get("direct_prerequisite_role_ids")
        if not isinstance(prerequisites, list):
            failures.append(f"{consumer}: prerequisites are not a JSON list")
            continue
        if len(prerequisites) != len(set(map(str, prerequisites))):
            failures.append(f"{consumer}: duplicate direct prerequisite")
        edges.extend((str(producer), consumer) for producer in prerequisites)
    unknown_role_ids = {
        role_id
        for edge in edges
        for role_id in edge
        if role_id not in role_set
    }
    if unknown_role_ids:
        failures.append(
            f"Stage-1 dependency edges contain unknown roles: {sorted(unknown_role_ids)!r}"
        )
    if len(edges) != 102 or len(set(edges)) != 102:
        failures.append("Stage-1 102-edge closure differs")
    if any(producer == consumer for producer, consumer in edges):
        failures.append("Stage-1 dependency graph contains a self-edge")
    if "ROLE-12" not in role_by_id.get("ROLE-11", {}).get(
        "direct_prerequisite_role_ids", []
    ):
        failures.append("ROLE-12 must be a direct prerequisite of ROLE-11")
    if "ROLE-16" in role_by_id.get("ROLE-18", {}).get(
        "direct_prerequisite_role_ids", []
    ):
        failures.append("ROLE-18 must remain independent of ROLE-16")
    if "ROLE-21" in role_by_id.get("ROLE-22", {}).get(
        "direct_prerequisite_role_ids", []
    ):
        failures.append("ROLE-22 must remain independent of ROLE-21")

    indegree = {role_id: 0 for role_id in role_ids}
    adjacency = {role_id: [] for role_id in role_ids}
    for producer, consumer in edges:
        if producer in adjacency and consumer in indegree:
            adjacency[producer].append(consumer)
            indegree[consumer] += 1
    ready = sorted(role_id for role_id, degree in indegree.items() if degree == 0)
    topological_order: list[str] = []
    while ready:
        producer = ready.pop(0)
        topological_order.append(producer)
        for consumer in sorted(adjacency[producer]):
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                ready.append(consumer)
                ready.sort()
    if len(topological_order) != len(role_ids):
        failures.append("Stage-1 dependency graph contains a cycle")
    if tuple(topological_order) != _EXPECTED_STAGE1_TOPOLOGICAL_ORDER:
        failures.append("Stage-1 lexicographic Kahn order differs")

    operation_classes = tuple(
        str(row.get("operation_class")) for row in operation_rows
    )
    if operation_classes != _EXPECTED_STAGE1_OPERATION_CLASSES:
        failures.append("Stage-1 operation profile identities differ")
    operation_role_ids: set[str] = set()
    for row in operation_rows:
        operation_class = str(row.get("operation_class"))
        required = row.get("required_role_ids")
        optional = row.get("optional_role_ids")
        if not isinstance(required, list) or not isinstance(optional, list):
            failures.append(f"{operation_class}: role closure is not a JSON list")
            continue
        required_ids = tuple(map(str, required))
        optional_ids = tuple(map(str, optional))
        operation_role_ids.update(required_ids)
        operation_role_ids.update(optional_ids)
        if (
            len(required_ids) != len(set(required_ids))
            or len(optional_ids) != len(set(optional_ids))
            or set(required_ids).intersection(optional_ids)
            or not set(required_ids + optional_ids).issubset(role_set)
        ):
            failures.append(f"{operation_class}: operation role closure differs")
    orphan_role_ids = role_set - operation_role_ids
    if orphan_role_ids:
        failures.append(f"Stage-1 orphan roles exist: {sorted(orphan_role_ids)!r}")
    operation_by_class = {
        str(row.get("operation_class")): row for row in operation_rows
    }
    emergency = operation_by_class.get("CANCEL_QUERY_RECONCILE", {})
    if (
        tuple(emergency.get("required_role_ids", ()))
        != ("ROLE-01", "ROLE-17", "ROLE-24", "ROLE-25", "ROLE-28")
        or tuple(emergency.get("optional_role_ids", ()))
        or emergency.get("terminal_failure_route")
        != "QUERY_RECONCILE_REQUIRED_OR_SAFE_HOLD"
    ):
        failures.append("CANCEL_QUERY_RECONCILE emergency closure differs")
    risk_reducing = operation_by_class.get("RISK_REDUCING_POSITION_ACTION", {})
    if {"ROLE-16", "ROLE-21"}.intersection(
        map(str, risk_reducing.get("required_role_ids", ()))
    ):
        failures.append("risk-reducing operation depends on economic/new-entry passage")

    writer_roles = tuple(
        str(row.get("role_id"))
        for row in role_rows
        if row.get("latency_class") == "SOLE_WRITE_HOTPATH"
    )
    execution_router_refs = tuple(
        (role_id, path, disposition)
        for role_id, path, disposition in path_references
        if path.endswith("/execution_router.py")
    )
    if (
        writer_roles != ("ROLE-25",)
        or len(execution_router_refs) != 1
        or execution_router_refs[0][0] != "ROLE-25"
        or execution_router_refs[0][2]
        != "FUTURE_AUTHORIZED_OWNER_NOT_YET_IMPLEMENTED"
    ):
        failures.append("ROLE-25 sole future execution-writer closure differs")

    import_rows: list[
        tuple[str, int, str, tuple[tuple[str, str | None], ...]]
    ] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_rows.append(
                (
                    "import",
                    0,
                    "",
                    tuple((alias.name, alias.asname) for alias in node.names),
                )
            )
        elif isinstance(node, ast.ImportFrom):
            import_rows.append(
                (
                    "from",
                    node.level,
                    node.module or "",
                    tuple((alias.name, alias.asname) for alias in node.names),
                )
            )
    expected_import_rows = [
        ("from", 0, "__future__", (("annotations", None),)),
        ("from", 0, "collections.abc", (("Mapping", None),)),
        ("from", 0, "dataclasses", (("dataclass", None),)),
        ("from", 0, "enum", (("StrEnum", None),)),
        ("import", 0, "", (("heapq", None),)),
        ("import", 0, "", (("json", None),)),
        ("import", 0, "", (("re", None),)),
        (
            "from",
            1,
            "errors",
            (("ContractValidationError", None), ("ReasonCode", None)),
        ),
        (
            "from",
            1,
            "models",
            (("NO_EFFECTS_V1", None), ("NoEffectFlagsV1", None)),
        ),
        (
            "from",
            1,
            "serialization",
            (
                ("deterministic_json", None),
                ("safe_json_loads", None),
                ("validate_relative_path", None),
            ),
        ),
    ]
    if import_rows != expected_import_rows:
        failures.append("Stage-1 launch graph import surface differs")

    forbidden_call_names = {
        "__import__",
        "compile",
        "eval",
        "exec",
        "input",
        "open",
    }
    forbidden_call_attributes = {
        "Popen",
        "connect",
        "fromtimestamp",
        "getenv",
        "mkdir",
        "now",
        "popen",
        "request",
        "run",
        "sleep",
        "system",
        "time",
        "today",
        "unlink",
        "urlopen",
        "utcnow",
        "write",
        "write_bytes",
        "write_text",
    }
    if any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id in forbidden_call_names
            or isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_call_attributes
        )
        for node in ast.walk(tree)
    ):
        failures.append("Stage-1 launch graph contains a forbidden effect call")

    def assigned_call(name: str) -> ast.Call | None:
        values = tuple(
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
        )
        return values[0] if len(values) == 1 else None

    def exact_no_effect_keyword(call: ast.Call | None) -> bool:
        if call is None:
            return False
        keyword = next(
            (row.value for row in call.keywords if row.arg == "no_effects"),
            None,
        )
        return isinstance(keyword, ast.Name) and keyword.id == "NO_EFFECTS_V1"

    scope_call = assigned_call("STAGE1_SELECTED_SCOPE_V2")
    active_live_value = (
        next(
            (
                row.value
                for row in scope_call.keywords
                if row.arg == "active_live_profile_ids"
            ),
            None,
        )
        if scope_call is not None
        else None
    )
    operation_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Stage1OperationDependencyProfileV1"
    )
    graph_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "SelectedLaunchGraphV2"
    )
    if (
        scope_call is None
        or not isinstance(active_live_value, ast.Tuple)
        or active_live_value.elts
        or not exact_no_effect_keyword(scope_call)
        or len(operation_calls) != 1
        or not all(exact_no_effect_keyword(call) for call in operation_calls)
        or len(graph_calls) != 1
        or not all(exact_no_effect_keyword(call) for call in graph_calls)
    ):
        failures.append("Stage-1 active-live/no-effect AST closure differs")

    return failures


def _tracked_architecture_material() -> dict[str, dict[str, object]]:
    """Read immutable oracle/vector data without importing production code."""

    comparator_failures = _comparator_registry_failures(
        _ARCHITECTURE_COMPARATOR_REGISTRY
    )
    if comparator_failures:
        raise ValueError("; ".join(comparator_failures))

    tree = ast.parse(
        (PACKAGE / "oracle_contracts.py").read_text(encoding="utf-8"),
        filename=str(PACKAGE / "oracle_contracts.py"),
    )
    legacy_oracle_rows = _json_rows(tree, "_ORACLE_ROWS_JSON")
    legacy_vector_rows = _json_rows(tree, "_GOLDEN_VECTOR_ROWS_JSON")
    st12b_oracle_rows = _json_rows(tree, "_ST12B_ORACLE_CONTRACTS_JSON")
    st12b_vector_rows = _json_rows(tree, "_ST12B_VECTOR_PACK_JSON")
    st12b_property_rows = _json_rows(tree, "_ST12B_PROPERTY_PACK_JSON")

    def unique_by(
        rows: Sequence[Mapping[str, object]],
        key_name: str,
        family: str,
    ) -> dict[str, Mapping[str, object]]:
        counts = Counter(str(row.get(key_name)) for row in rows)
        duplicates = tuple(sorted(key for key, count in counts.items() if count != 1))
        if duplicates:
            raise ValueError(f"{family} identities are not unique: {duplicates!r}")
        return {str(row[key_name]): row for row in rows}

    legacy_oracles = unique_by(legacy_oracle_rows, "math_spec_ref", "legacy oracle")
    legacy_vectors = unique_by(legacy_vector_rows, "math_spec_ref", "legacy vector")
    st12b_oracles = unique_by(st12b_oracle_rows, "math_spec_id", "ST12-B oracle")
    st12b_vectors: dict[str, dict[str, dict[str, object]]] = {}
    vector_keys: set[tuple[str, str]] = set()
    for row in st12b_vector_rows:
        key = (str(row["math_spec_id"]), str(row["case_type"]))
        if key in vector_keys:
            raise ValueError(f"ST12-B vector class is ambiguous: {key!r}")
        vector_keys.add(key)
        st12b_vectors.setdefault(key[0], {})[key[1]] = row
    st12b_properties = unique_by(
        st12b_property_rows,
        "math_spec_id",
        "ST12-B property",
    )

    material: dict[str, dict[str, object]] = {}
    for math_id in ARCHITECTURE_MATH_IDS:
        if math_id in EXPECTED_MATH_IDS:
            oracle = legacy_oracles.get(math_id)
            golden = legacy_vectors.get(math_id)
            if oracle is None or golden is None:
                raise ValueError(f"missing legacy architecture material: {math_id}")
            material[math_id] = {
                "evidence_tier": _EVIDENCE_TIER_BY_MATH_ID[math_id],
                "oracle": oracle,
                "golden": golden,
                "boundary": None,
                "negative": None,
                "property": None,
                "oracle_id": str(oracle["oracle_id"]),
                "golden_vector_id": str(golden["vector_id"]),
                "comparison_policy": str(golden["comparison_policy"]),
            }
            continue

        if math_id not in CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
            raise ValueError(f"unrouted architecture material: {math_id}")
        oracle = st12b_oracles.get(math_id)
        vectors = st12b_vectors.get(math_id, {})
        property_row = st12b_properties.get(math_id)
        if (
            oracle is None
            or set(vectors) != {"GOLDEN", "BOUNDARY", "NEGATIVE"}
            or property_row is None
        ):
            raise ValueError(f"missing ST12-B architecture material: {math_id}")
        assert isinstance(oracle, Mapping)
        assert isinstance(property_row, Mapping)
        declared_keys = oracle.get("input_keys")
        if (
            not isinstance(declared_keys, list)
            or not declared_keys
            or len(declared_keys) != len(set(declared_keys))
            or any(not isinstance(key, str) or not key for key in declared_keys)
            or oracle.get("output_schema_ref") != f"{math_id}::OUTPUT"
            or oracle.get("output_schema_version") != "ST12B_OUTPUT_V3_4"
        ):
            raise ValueError(f"invalid current ST12-B oracle contract: {math_id}")
        for case_type in ("GOLDEN", "BOUNDARY", "NEGATIVE"):
            vector = vectors[case_type]
            if (
                vector.get("math_spec_id") != math_id
                or vector.get("case_type") != case_type
                or vector.get("input_keys") != declared_keys
                or not isinstance(vector.get("inputs"), Mapping)
                or len(vector["inputs"]) != len(declared_keys)
                or set(vector["inputs"]) != set(declared_keys)
            ):
                raise ValueError(
                    f"invalid current ST12-B {case_type} binding: {math_id}"
                )
        if (
            property_row.get("math_spec_id") != math_id
            or not isinstance(property_row.get("base_inputs"), Mapping)
            or len(property_row["base_inputs"]) != len(declared_keys)
            or set(property_row["base_inputs"]) != set(declared_keys)
            or not isinstance(property_row.get("mutation"), Mapping)
            or not isinstance(property_row.get("property_id"), str)
            or not property_row.get("property_id")
        ):
            raise ValueError(f"invalid current ST12-B property binding: {math_id}")
        material[math_id] = {
            "evidence_tier": _EVIDENCE_TIER_BY_MATH_ID[math_id],
            "oracle": oracle,
            "golden": vectors["GOLDEN"],
            "boundary": vectors["BOUNDARY"],
            "negative": vectors["NEGATIVE"],
            "property": property_row,
            "oracle_id": str(oracle["oracle_id"]),
            "golden_vector_id": str(vectors["GOLDEN"]["vector_id"]),
            "boundary_vector_id": str(vectors["BOUNDARY"]["vector_id"]),
            "negative_vector_id": str(vectors["NEGATIVE"]["vector_id"]),
            "property_id": str(property_row["property_id"]),
            "output_schema_ref": str(oracle["output_schema_ref"]),
            "output_schema_version": str(oracle["output_schema_version"]),
            "comparison_policy": (
                "CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE"
            ),
        }

    if tuple(material) != ARCHITECTURE_MATH_IDS:
        raise ValueError("architecture material denominator/order is not exact")
    if tuple(_EVIDENCE_TIER_BY_MATH_ID) != ARCHITECTURE_MATH_IDS:
        raise ValueError("architecture evidence-tier membership/order is not exact")
    if tuple(
        math_id
        for math_id, tier in _EVIDENCE_TIER_BY_MATH_ID.items()
        if tier == _LEGACY_GOLDEN_REGRESSION_TIER
    ) != EXPECTED_MATH_IDS:
        raise ValueError("legacy evidence-tier membership is not exact")
    if tuple(
        math_id
        for math_id, tier in _EVIDENCE_TIER_BY_MATH_ID.items()
        if tier == _CURRENT_FULL_CONTRACT_TIER
    ) != CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
        raise ValueError("current evidence-tier membership is not exact")
    if len({row["oracle_id"] for row in material.values()}) != 29 or len(
        {row["golden_vector_id"] for row in material.values()}
    ) != 29:
        raise ValueError("architecture oracle/vector identities are not unique")
    current_rows = tuple(material[math_id] for math_id in CURRENT_ST12B_ARCHITECTURE_MATH_IDS)
    for identity_field in (
        "oracle_id",
        "golden_vector_id",
        "boundary_vector_id",
        "negative_vector_id",
        "property_id",
    ):
        values = tuple(row[identity_field] for row in current_rows)
        if len(values) != 14 or len(set(values)) != 14:
            raise ValueError(
                f"current ST12-B architecture {identity_field} identities are not exact"
            )
    comparator_failures = _comparator_registry_failures(
        _ARCHITECTURE_COMPARATOR_REGISTRY,
        material,
    )
    if comparator_failures:
        raise ValueError("; ".join(comparator_failures))
    return material


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_int(value: object, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _sequence(value: object, name: str, minimum: int = 1) -> list[object]:
    if (
        isinstance(value, str | bytes)
        or not isinstance(value, Sequence)
        or len(value) < minimum
    ):
        raise ValueError(f"{name} must contain at least {minimum} item(s)")
    return list(value)


def _matrix(value: object, name: str) -> list[list[float]]:
    rows = _sequence(value, name)
    if any(
        isinstance(row, str | bytes)
        or not isinstance(row, Sequence)
        or not row
        for row in rows
    ):
        raise ValueError(f"{name} must be a nonempty rectangular matrix")
    width = len(rows[0])  # type: ignore[arg-type]
    if any(len(row) != width for row in rows):  # type: ignore[arg-type]
        raise ValueError(f"{name} must be rectangular")
    return [
        [
            _finite(item, f"{name}[{row_index}][{column_index}]")
            for column_index, item in enumerate(row)  # type: ignore[union-attr]
        ]
        for row_index, row in enumerate(rows)
    ]


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires data")
    return math.fsum(values) / len(values)


def _sample_variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise ValueError("sample variance requires at least two values")
    center = _mean(values)
    return math.fsum((value - center) ** 2 for value in values) / (len(values) - 1)


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    return value


@dataclass(frozen=True)
class _CompiledComparisonPolicyV1:
    declared_policy: str
    compiled_comparison_mode: str
    operational_policy: str
    absolute_tolerance: Decimal | None
    exact_mapping_order: bool
    exact_decimal_representation: bool
    structural_rules: tuple[str, ...]
    numeric_text_leaf_paths: tuple[tuple[str, ...], ...]
    numeric_text_representation: str


@dataclass
class _ComparisonExecutionTraceV1:
    structural_mapping_checks: int = 0
    structural_sequence_checks: int = 0
    exact_decimal_text_leaf_checks: int = 0
    precision_34_exact_leaf_checks: int = 0
    numeric_float_tolerance_leaf_checks: int = 0
    numeric_text_tolerance_leaf_checks: int = 0
    exact_order_or_index_checks: int = 0
    boolean_leaf_checks: int = 0
    exact_scalar_checks: int = 0
    declared_mode_branch_reached: bool = False


@dataclass(frozen=True)
class _ArchitectureComparisonResultV1:
    math_id: str
    comparison_passed: bool
    tracked_comparison_policy: str
    compiled_comparison_mode: str
    compiled_absolute_tolerance_or_not_applicable: str
    structural_rules: tuple[str, ...]
    numeric_text_leaf_paths: tuple[tuple[str, ...], ...]
    numeric_text_representation: str
    comparator_registry_version: str
    execution_trace: _ComparisonExecutionTraceV1
    comparison_policy_execution_observed: bool


_COMPARATOR_REGISTRY_VERSION = "ST12_ARCHITECTURE_COMPARATOR_REGISTRY_V3"
_COMPARATOR_AUTHORITY_CLASSIFICATION = (
    "INDEPENDENT_VALIDATOR_FROZEN_COMPARATOR_AUTHORITY"
)
_CURRENT_DECLARED_COMPARISON_POLICY = (
    "CANONICAL_STRUCTURE_WITH_DECLARED_NUMERIC_TOLERANCE"
)
_COMPARATOR_TOLERANCE_NOT_APPLICABLE = "NOT_APPLICABLE"
_COMPARATOR_NUMERIC_TEXT_REPRESENTATION_NOT_APPLICABLE = "NOT_APPLICABLE"
_CANONICAL_FIXED_DECIMAL_TEXT = "CANONICAL_FIXED_DECIMAL_TEXT"
_BASE_STRUCTURAL_RULES = (
    "EXACT_NESTED_FIELD_SET",
    "EXACT_NESTED_VALUE_TYPE",
    "EXACT_SEQUENCE_ORDER",
)


@dataclass(frozen=True)
class _ComparisonPolicyModeCompatibilityV1:
    tracked_comparison_policy: str
    compiled_comparison_mode: str
    allowed_tolerances: tuple[str, ...]


_COMPARISON_POLICY_MODE_COMPATIBILITY = MappingProxyType(
    {
        "EXACT_DECIMAL": _ComparisonPolicyModeCompatibilityV1(
            "EXACT_DECIMAL",
            "EXACT_DECIMAL",
            (_COMPARATOR_TOLERANCE_NOT_APPLICABLE,),
        ),
        "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT": (
            _ComparisonPolicyModeCompatibilityV1(
                "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
                "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
                (_COMPARATOR_TOLERANCE_NOT_APPLICABLE,),
            )
        ),
        "ABS_TOL_1E-15": _ComparisonPolicyModeCompatibilityV1(
            "ABS_TOL_1E-15",
            "ABSOLUTE_TOLERANCE",
            ("1E-15",),
        ),
        "ABS_TOL_1E-12": _ComparisonPolicyModeCompatibilityV1(
            "ABS_TOL_1E-12",
            "ABSOLUTE_TOLERANCE",
            ("1E-12",),
        ),
        "EXACT_ORDER_AND_INDEX_SET": _ComparisonPolicyModeCompatibilityV1(
            "EXACT_ORDER_AND_INDEX_SET",
            "EXACT_ORDER_AND_INDEX_SET",
            (_COMPARATOR_TOLERANCE_NOT_APPLICABLE,),
        ),
        "BOOLEAN_INVARIANTS": _ComparisonPolicyModeCompatibilityV1(
            "BOOLEAN_INVARIANTS",
            "BOOLEAN_INVARIANTS",
            (_COMPARATOR_TOLERANCE_NOT_APPLICABLE,),
        ),
        _CURRENT_DECLARED_COMPARISON_POLICY: _ComparisonPolicyModeCompatibilityV1(
            _CURRENT_DECLARED_COMPARISON_POLICY,
            "STRUCTURAL_NESTED_NUMERIC",
            ("1E-15", "1E-12"),
        ),
    }
)


@dataclass(frozen=True)
class _ArchitectureComparatorRegistryRowV3:
    math_id: str
    tracked_comparison_policy: str
    compiled_comparison_mode: str
    absolute_tolerance_or_not_applicable: str
    structural_rules: tuple[str, ...]
    numeric_text_leaf_paths: tuple[tuple[str, ...], ...]
    numeric_text_representation: str
    registry_version: str
    authority_classification: str


def _architecture_comparator_row(
    math_id: str,
    tracked_policy: str,
    mode: str,
    tolerance: str = _COMPARATOR_TOLERANCE_NOT_APPLICABLE,
    *additional_structural_rules: str,
    numeric_text_leaf_paths: tuple[tuple[str, ...], ...] = (),
    numeric_text_representation: str = (
        _COMPARATOR_NUMERIC_TEXT_REPRESENTATION_NOT_APPLICABLE
    ),
) -> _ArchitectureComparatorRegistryRowV3:
    return _ArchitectureComparatorRegistryRowV3(
        math_id=math_id,
        tracked_comparison_policy=tracked_policy,
        compiled_comparison_mode=mode,
        absolute_tolerance_or_not_applicable=tolerance,
        structural_rules=(*_BASE_STRUCTURAL_RULES, *additional_structural_rules),
        numeric_text_leaf_paths=numeric_text_leaf_paths,
        numeric_text_representation=numeric_text_representation,
        registry_version=_COMPARATOR_REGISTRY_VERSION,
        authority_classification=_COMPARATOR_AUTHORITY_CLASSIFICATION,
    )


_ARCHITECTURE_COMPARATOR_REGISTRY = MappingProxyType(
    {
        "MATH-01": _architecture_comparator_row("MATH-01", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-02": _architecture_comparator_row(
            "MATH-02",
            "ABS_TOL_1E-15",
            "ABSOLUTE_TOLERANCE",
            "1E-15",
            numeric_text_leaf_paths=(("edge_probability",),),
            numeric_text_representation=_CANONICAL_FIXED_DECIMAL_TEXT,
        ),
        "MATH-03": _architecture_comparator_row("MATH-03", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-04": _architecture_comparator_row("MATH-04", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-05": _architecture_comparator_row("MATH-05", "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT", "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION", "DECIMAL_CONTEXT_PRECISION_34"),
        "MATH-06": _architecture_comparator_row("MATH-06", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-07": _architecture_comparator_row("MATH-07", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-08": _architecture_comparator_row("MATH-08", "EXACT_DECIMAL", "EXACT_DECIMAL", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_DECIMAL_REPRESENTATION"),
        "MATH-09": _architecture_comparator_row("MATH-09", "ABS_TOL_1E-15", "ABSOLUTE_TOLERANCE", "1E-15"),
        "MATH-10": _architecture_comparator_row("MATH-10", "ABS_TOL_1E-15", "ABSOLUTE_TOLERANCE", "1E-15"),
        "MATH-11": _architecture_comparator_row("MATH-11", "ABS_TOL_1E-12", "ABSOLUTE_TOLERANCE", "1E-12"),
        "MATH-12": _architecture_comparator_row("MATH-12", "EXACT_ORDER_AND_INDEX_SET", "EXACT_ORDER_AND_INDEX_SET", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_MAPPING_ORDER", "EXACT_INDEX_SET"),
        "MATH-13": _architecture_comparator_row("MATH-13", "EXACT_ORDER_AND_INDEX_SET", "EXACT_ORDER_AND_INDEX_SET", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_MAPPING_ORDER", "EXACT_INDEX_SET"),
        "MATH-14": _architecture_comparator_row("MATH-14", "BOOLEAN_INVARIANTS", "BOOLEAN_INVARIANTS", _COMPARATOR_TOLERANCE_NOT_APPLICABLE, "EXACT_BOOLEAN_TYPE_AND_VALUE"),
        "MATH-15": _architecture_comparator_row("MATH-15", "ABS_TOL_1E-15", "ABSOLUTE_TOLERANCE", "1E-15"),
        "MATH-16": _architecture_comparator_row("MATH-16", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-17": _architecture_comparator_row("MATH-17", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-18": _architecture_comparator_row("MATH-18", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-19": _architecture_comparator_row("MATH-19", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-15", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-20": _architecture_comparator_row("MATH-20", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-21": _architecture_comparator_row("MATH-21", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-22": _architecture_comparator_row("MATH-22", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-23": _architecture_comparator_row("MATH-23", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-24": _architecture_comparator_row("MATH-24", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-25": _architecture_comparator_row("MATH-25", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-46": _architecture_comparator_row("MATH-46", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-15", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-47": _architecture_comparator_row("MATH-47", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-15", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-48": _architecture_comparator_row("MATH-48", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-12", "TOLERANT_NUMERIC_LEAVES_ONLY"),
        "MATH-49": _architecture_comparator_row("MATH-49", _CURRENT_DECLARED_COMPARISON_POLICY, "STRUCTURAL_NESTED_NUMERIC", "1E-15", "TOLERANT_NUMERIC_LEAVES_ONLY"),
    }
)


def _policy_mode_compatibility_failures(
    entry: _ArchitectureComparatorRegistryRowV3,
) -> tuple[str, ...]:
    compatibility = _COMPARISON_POLICY_MODE_COMPATIBILITY.get(
        entry.tracked_comparison_policy
    )
    if compatibility is None:
        return (f"{entry.math_id}: unknown tracked comparison policy",)
    failures: list[str] = []
    if entry.compiled_comparison_mode != compatibility.compiled_comparison_mode:
        failures.append(f"{entry.math_id}: policy/mode compatibility mismatch")
    if (
        entry.absolute_tolerance_or_not_applicable
        not in compatibility.allowed_tolerances
    ):
        failures.append(f"{entry.math_id}: policy/tolerance compatibility mismatch")
    return tuple(failures)


def _comparator_registry_failures(
    registry: Mapping[str, _ArchitectureComparatorRegistryRowV3],
    tracked_material: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[str, ...]:
    failures: list[str] = []
    if tuple(registry) != ARCHITECTURE_MATH_IDS:
        failures.append("comparator registry identity/order differs")
    for math_id in ARCHITECTURE_MATH_IDS:
        entry = registry.get(math_id)
        expected = _ARCHITECTURE_COMPARATOR_REGISTRY.get(math_id)
        if entry is None:
            failures.append(f"{math_id}: comparator row missing")
            continue
        if expected is None or entry != expected:
            failures.append(f"{math_id}: comparator registry row drift")
        if entry.math_id != math_id:
            failures.append(f"{math_id}: comparator row identity drift")
        if entry.registry_version != _COMPARATOR_REGISTRY_VERSION:
            failures.append(f"{math_id}: comparator registry version drift")
        if entry.authority_classification != _COMPARATOR_AUTHORITY_CLASSIFICATION:
            failures.append(f"{math_id}: comparator authority drift")
        failures.extend(_policy_mode_compatibility_failures(entry))
        if math_id == "MATH-02":
            if entry.numeric_text_leaf_paths != (("edge_probability",),):
                failures.append("MATH-02: numeric-text path registration differs")
            if entry.numeric_text_representation != _CANONICAL_FIXED_DECIMAL_TEXT:
                failures.append("MATH-02: numeric-text representation differs")
        elif entry.numeric_text_leaf_paths:
            failures.append(f"{math_id}: unauthorized numeric-text tolerance path")
        elif entry.numeric_text_representation != (
            _COMPARATOR_NUMERIC_TEXT_REPRESENTATION_NOT_APPLICABLE
        ):
            failures.append(f"{math_id}: unauthorized numeric-text representation")
        if tracked_material is not None:
            tracked = tracked_material.get(math_id)
            if tracked is None or entry.tracked_comparison_policy != str(
                tracked.get("comparison_policy")
            ):
                failures.append(f"{math_id}: tracked comparison policy mismatch")
    return tuple(failures)


def _compile_comparison_policy(
    declared_policy: str,
    *,
    math_id: str,
) -> _CompiledComparisonPolicyV1:
    authority = _ARCHITECTURE_COMPARATOR_REGISTRY.get(math_id)
    if authority is None:
        raise ValueError(f"unknown architecture comparator row: {math_id}")
    if authority.tracked_comparison_policy != declared_policy:
        raise ValueError(f"tracked comparison policy mismatch: {math_id}")
    compatibility = _COMPARISON_POLICY_MODE_COMPATIBILITY.get(declared_policy)
    if compatibility is None:
        raise ValueError(f"unknown tracked comparison policy: {math_id}")
    if authority.compiled_comparison_mode != compatibility.compiled_comparison_mode:
        raise ValueError(f"policy/mode compatibility mismatch: {math_id}")
    if (
        authority.absolute_tolerance_or_not_applicable
        not in compatibility.allowed_tolerances
    ):
        raise ValueError(f"policy/tolerance compatibility mismatch: {math_id}")
    tolerance_text = authority.absolute_tolerance_or_not_applicable
    if tolerance_text == _COMPARATOR_TOLERANCE_NOT_APPLICABLE:
        tolerance = None
    elif tolerance_text == "1E-15":
        tolerance = Decimal("1E-15")
    elif tolerance_text == "1E-12":
        tolerance = Decimal("1E-12")
    else:
        raise ValueError(f"unknown comparison tolerance: {math_id}")
    allowed_modes = {
        "EXACT_DECIMAL",
        "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT",
        "ABSOLUTE_TOLERANCE",
        "EXACT_ORDER_AND_INDEX_SET",
        "BOOLEAN_INVARIANTS",
        "STRUCTURAL_NESTED_NUMERIC",
    }
    if authority.compiled_comparison_mode not in allowed_modes:
        raise ValueError(f"unknown comparison policy: {math_id}")
    operational_policy = declared_policy
    if tolerance is not None and not declared_policy.endswith(tolerance_text):
        operational_policy = f"{declared_policy}::{tolerance_text}"
    return _CompiledComparisonPolicyV1(
        declared_policy=declared_policy,
        compiled_comparison_mode=authority.compiled_comparison_mode,
        operational_policy=operational_policy,
        absolute_tolerance=tolerance,
        exact_mapping_order="EXACT_MAPPING_ORDER" in authority.structural_rules,
        exact_decimal_representation=(
            "EXACT_DECIMAL_REPRESENTATION" in authority.structural_rules
        ),
        structural_rules=authority.structural_rules,
        numeric_text_leaf_paths=authority.numeric_text_leaf_paths,
        numeric_text_representation=authority.numeric_text_representation,
    )


def _canonical_numeric_text_decimal(value: object) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = Decimal(value)
        if not parsed.is_finite() or _canonical_decimal_text(parsed) != value:
            return None
    except DecimalException:
        return None
    return parsed


def _trace_count(
    trace: _ComparisonExecutionTraceV1 | Mapping[str, object],
    field_name: str,
) -> int:
    value = (
        trace.get(field_name)
        if isinstance(trace, Mapping)
        else getattr(trace, field_name, None)
    )
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _trace_declared_mode_reached(
    compiled_mode: str,
    trace: _ComparisonExecutionTraceV1 | Mapping[str, object],
) -> bool:
    numeric_tolerance_checks = _trace_count(
        trace, "numeric_float_tolerance_leaf_checks"
    ) + _trace_count(trace, "numeric_text_tolerance_leaf_checks")
    if compiled_mode == "EXACT_DECIMAL":
        return _trace_count(trace, "exact_decimal_text_leaf_checks") > 0
    if compiled_mode == "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT":
        return _trace_count(trace, "precision_34_exact_leaf_checks") > 0
    if compiled_mode == "ABSOLUTE_TOLERANCE":
        return numeric_tolerance_checks > 0
    if compiled_mode == "EXACT_ORDER_AND_INDEX_SET":
        return _trace_count(trace, "exact_order_or_index_checks") > 0
    if compiled_mode == "BOOLEAN_INVARIANTS":
        return _trace_count(trace, "boolean_leaf_checks") > 0
    if compiled_mode == "STRUCTURAL_NESTED_NUMERIC":
        structural_checks = _trace_count(
            trace, "structural_mapping_checks"
        ) + _trace_count(trace, "structural_sequence_checks")
        return structural_checks > 0 and numeric_tolerance_checks > 0
    return False


def _compiled_payload_matches(
    observed: object,
    expected: object,
    policy: _CompiledComparisonPolicyV1,
    *,
    path: tuple[object, ...],
    trace: _ComparisonExecutionTraceV1,
) -> bool:
    if isinstance(expected, Mapping):
        trace.structural_mapping_checks += 1
        if not isinstance(observed, Mapping) or type(observed) is not type(expected):
            return False
        if policy.exact_mapping_order:
            trace.exact_order_or_index_checks += 1
            if tuple(observed) != tuple(expected):
                return False
        elif set(observed) != set(expected):
            return False
        return all(
            _compiled_payload_matches(
                observed[key],
                expected[key],
                policy,
                path=(*path, key),
                trace=trace,
            )
            for key in expected
        )
    if isinstance(expected, list | tuple):
        trace.structural_sequence_checks += 1
        if policy.compiled_comparison_mode == "EXACT_ORDER_AND_INDEX_SET":
            trace.exact_order_or_index_checks += 1
        return (
            isinstance(observed, list | tuple)
            and type(observed) is type(expected)
            and len(observed) == len(expected)
            and all(
                _compiled_payload_matches(
                    left,
                    right,
                    policy,
                    path=(*path, index),
                    trace=trace,
                )
                for index, (left, right) in enumerate(
                    zip(observed, expected, strict=True)
                )
            )
        )
    if path in policy.numeric_text_leaf_paths:
        trace.numeric_text_tolerance_leaf_checks += 1
        if policy.numeric_text_representation != _CANONICAL_FIXED_DECIMAL_TEXT:
            return False
        observed_decimal = _canonical_numeric_text_decimal(observed)
        expected_decimal = _canonical_numeric_text_decimal(expected)
        return (
            observed_decimal is not None
            and expected_decimal is not None
            and policy.absolute_tolerance is not None
            and abs(observed_decimal - expected_decimal)
            <= policy.absolute_tolerance
        )
    if policy.compiled_comparison_mode == "EXACT_DECIMAL" and isinstance(
        expected, str | Decimal
    ):
        trace.exact_decimal_text_leaf_checks += 1
        if isinstance(expected, str):
            observed_decimal = _canonical_numeric_text_decimal(observed)
            expected_decimal = _canonical_numeric_text_decimal(expected)
            return (
                observed_decimal is not None
                and expected_decimal is not None
                and observed_decimal == expected_decimal
                and observed == expected
            )
        return (
            isinstance(observed, Decimal)
            and observed == expected
            and (
                not policy.exact_decimal_representation
                or observed.as_tuple() == expected.as_tuple()
            )
        )
    if (
        policy.compiled_comparison_mode
        == "DECIMAL_CONTEXT_PRECISION_34_EXACT_RESULT"
        and isinstance(expected, str | Decimal)
    ):
        trace.precision_34_exact_leaf_checks += 1
        if isinstance(expected, str):
            observed_decimal = _canonical_numeric_text_decimal(observed)
            expected_decimal = _canonical_numeric_text_decimal(expected)
            return (
                observed_decimal is not None
                and expected_decimal is not None
                and observed_decimal == expected_decimal
                and observed == expected
            )
        return (
            isinstance(observed, Decimal)
            and observed == expected
            and observed.as_tuple() == expected.as_tuple()
        )
    if isinstance(expected, bool):
        trace.boolean_leaf_checks += 1
        return isinstance(observed, bool) and observed is expected
    if isinstance(expected, Decimal):
        trace.exact_decimal_text_leaf_checks += 1
        return (
            isinstance(observed, Decimal)
            and observed == expected
            and (
                not policy.exact_decimal_representation
                or observed.as_tuple() == expected.as_tuple()
            )
        )
    if (
        isinstance(expected, int | float)
        and not isinstance(expected, bool)
        and isinstance(observed, int | float)
        and not isinstance(observed, bool)
    ):
        if type(observed) is not type(expected):
            return False
        if not math.isfinite(float(expected)) or not math.isfinite(float(observed)):
            return False
        if policy.absolute_tolerance is None:
            trace.exact_scalar_checks += 1
            return type(observed) is type(expected) and observed == expected
        trace.numeric_float_tolerance_leaf_checks += 1
        return math.isclose(
            float(observed),
            float(expected),
            rel_tol=0.0,
            abs_tol=float(policy.absolute_tolerance),
        )
    trace.exact_scalar_checks += 1
    return type(observed) is type(expected) and observed == expected


def _compare_architecture_payload(
    math_id: str,
    observed: object,
    expected: object,
    *,
    tracked_comparison_policy: str,
) -> _ArchitectureComparisonResultV1:
    policy = _compile_comparison_policy(
        tracked_comparison_policy,
        math_id=math_id,
    )
    authority = _ARCHITECTURE_COMPARATOR_REGISTRY[math_id]
    trace = _ComparisonExecutionTraceV1()
    comparison_passed = _compiled_payload_matches(
        observed,
        expected,
        policy,
        path=(),
        trace=trace,
    )
    comparison_policy_execution_observed = _trace_declared_mode_reached(
        policy.compiled_comparison_mode,
        trace,
    )
    trace.declared_mode_branch_reached = comparison_policy_execution_observed
    return _ArchitectureComparisonResultV1(
        math_id=math_id,
        comparison_passed=comparison_passed,
        tracked_comparison_policy=tracked_comparison_policy,
        compiled_comparison_mode=policy.compiled_comparison_mode,
        compiled_absolute_tolerance_or_not_applicable=(
            authority.absolute_tolerance_or_not_applicable
        ),
        structural_rules=policy.structural_rules,
        numeric_text_leaf_paths=policy.numeric_text_leaf_paths,
        numeric_text_representation=policy.numeric_text_representation,
        comparator_registry_version=authority.registry_version,
        execution_trace=trace,
        comparison_policy_execution_observed=(
            comparison_policy_execution_observed
        ),
    )


def _mutated_copy(value: object, path: Sequence[object], replacement_value: object) -> object:
    clone = json.loads(json.dumps(_json_ready(value), allow_nan=False))
    cursor = clone
    for component in path[:-1]:
        cursor = cursor[component]  # type: ignore[index]
    cursor[path[-1]] = replacement_value  # type: ignore[index]
    return clone


def _value_at_path(value: object, path: Sequence[object]) -> object:
    cursor = value
    for component in path:
        cursor = cursor[component]  # type: ignore[index]
    return cursor


def _legacy_tolerance_window_false_acceptance_count(
    material: Mapping[str, Mapping[str, object]],
) -> int:
    false_acceptances = 0
    for math_id, field_name in (
        ("MATH-09", "log_loss"),
        ("MATH-10", "ece"),
        ("MATH-15", "p_value"),
    ):
        expected: dict[str, object] = {field_name: 0.0}
        observed = {field_name: 5e-13}
        if math_id == "MATH-15":
            expected["reject"] = True
            observed["reject"] = True
        false_acceptances += int(
            _compare_architecture_payload(
                math_id,
                observed,
                expected,
                tracked_comparison_policy=str(
                    material[math_id]["comparison_policy"]
                ),
            ).comparison_passed
        )
    return false_acceptances


def _math_02_numeric_text_comparator_matrix(
    material: Mapping[str, Mapping[str, object]],
) -> Mapping[str, bool]:
    tracked_policy = str(material["MATH-02"]["comparison_policy"])

    def compare(observed: object, expected: object) -> _ArchitectureComparisonResultV1:
        return _compare_architecture_payload(
            "MATH-02",
            {"edge_probability": observed},
            {"edge_probability": expected},
            tracked_comparison_policy=tracked_policy,
        )

    within = compare("0.0600000000000005", "0.06")
    outside = compare("0.060000000000002", "0.06")
    trailing_zero = compare("0.060", "0.06")
    exponent = compare("6E-2", "0.06")
    float_coercion = compare(0.06, "0.06")
    invalid_text = compare("not-a-number", "0.06")
    no_tolerance_leaf = _compare_architecture_payload(
        "MATH-02",
        {"unrelated": "same"},
        {"unrelated": "same"},
        tracked_comparison_policy=tracked_policy,
    )
    missing_registration = dict(_ARCHITECTURE_COMPARATOR_REGISTRY)
    missing_registration["MATH-02"] = replace(
        missing_registration["MATH-02"],
        numeric_text_leaf_paths=(),
        numeric_text_representation=(
            _COMPARATOR_NUMERIC_TEXT_REPRESENTATION_NOT_APPLICABLE
        ),
    )
    wrong_tolerance = dict(_ARCHITECTURE_COMPARATOR_REGISTRY)
    wrong_tolerance["MATH-02"] = replace(
        wrong_tolerance["MATH-02"],
        absolute_tolerance_or_not_applicable="1E-12",
    )
    incompatible_mode = replace(
        _ARCHITECTURE_COMPARATOR_REGISTRY["MATH-02"],
        compiled_comparison_mode="EXACT_DECIMAL",
    )
    return MappingProxyType(
        {
            "within_tolerance_canonical_numeric_text_accepted": (
                within.comparison_passed
                and within.comparison_policy_execution_observed
                and within.execution_trace.numeric_text_tolerance_leaf_checks == 1
            ),
            "outside_tolerance_canonical_numeric_text_rejected": (
                not outside.comparison_passed
            ),
            "noncanonical_trailing_zero_text_rejected": (
                not trailing_zero.comparison_passed
            ),
            "exponent_text_rejected": not exponent.comparison_passed,
            "float_coercion_rejected": not float_coercion.comparison_passed,
            "invalid_numeric_text_rejected": not invalid_text.comparison_passed,
            "missing_numeric_text_registration_rejected": bool(
                _comparator_registry_failures(missing_registration)
            ),
            "absolute_tolerance_leaf_not_reached_is_unobserved": (
                no_tolerance_leaf.comparison_passed
                and not no_tolerance_leaf.comparison_policy_execution_observed
                and no_tolerance_leaf.execution_trace.numeric_text_tolerance_leaf_checks
                == 0
            ),
            "incorrect_tolerance_rejected": bool(
                _comparator_registry_failures(wrong_tolerance)
            ),
            "policy_mode_incompatibility_rejected": bool(
                _policy_mode_compatibility_failures(incompatible_mode)
            ),
        }
    )


def _comparison_policy_self_rejections() -> int:
    material = _tracked_architecture_material()
    math_02_matrix = _math_02_numeric_text_comparator_matrix(material)
    failed_math_02_checks = tuple(
        name for name, passed in math_02_matrix.items() if not passed
    )
    if failed_math_02_checks:
        raise ValueError(
            "MATH-02 numeric-text comparator defects escaped: "
            + ", ".join(failed_math_02_checks)
        )
    missing_row = dict(_ARCHITECTURE_COMPARATOR_REGISTRY)
    missing_row.pop("MATH-01")
    if not _comparator_registry_failures(missing_row):
        raise ValueError("missing comparator row was accepted")
    unknown_policy = dict(_ARCHITECTURE_COMPARATOR_REGISTRY)
    unknown_policy["MATH-01"] = replace(
        unknown_policy["MATH-01"],
        compiled_comparison_mode="UNKNOWN_POLICY",
    )
    if not _comparator_registry_failures(unknown_policy):
        raise ValueError("unknown comparator policy was accepted")
    changed_tolerance = dict(_ARCHITECTURE_COMPARATOR_REGISTRY)
    changed_tolerance["MATH-09"] = replace(
        changed_tolerance["MATH-09"],
        absolute_tolerance_or_not_applicable="1E-12",
    )
    if not _comparator_registry_failures(changed_tolerance):
        raise ValueError("1E-15 comparator row accepted a 1E-12 replacement")
    if _legacy_tolerance_window_false_acceptance_count(material):
        raise ValueError("legacy 1E-15 rows accepted 1E-12-window drift")
    if _compare_architecture_payload(
        "MATH-01",
        {"p_market": "0.420"},
        {"p_market": "0.42"},
        tracked_comparison_policy=str(material["MATH-01"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("exact Decimal drift was accepted")
    if _compare_architecture_payload(
        "MATH-05",
        {"relative_spread": "0.04651162790697674418604651162790699"},
        {"relative_spread": "0.04651162790697674418604651162790698"},
        tracked_comparison_policy=str(material["MATH-05"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("precision-34 representation drift was accepted")
    if _compare_architecture_payload(
        "MATH-12",
        {"rejected_original_indices": [0, 1], "largest_rank": 2},
        {"largest_rank": 2, "rejected_original_indices": [0, 1]},
        tracked_comparison_policy=str(material["MATH-12"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("exact ordered comparison accepted reordered output")
    if _compare_architecture_payload(
        "MATH-12",
        {"largest_rank": 2, "rejected_original_indices": [0, 2]},
        {"largest_rank": 2, "rejected_original_indices": [0, 1]},
        tracked_comparison_policy=str(material["MATH-12"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("exact comparison accepted index-set drift")
    if _compare_architecture_payload(
        "MATH-14",
        {"interval_contains_sample_mean": False, "same_seed_reproducible": True},
        {"interval_contains_sample_mean": True, "same_seed_reproducible": True},
        tracked_comparison_policy=str(material["MATH-14"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("Boolean invariant drift was accepted")
    if _compare_architecture_payload(
        "MATH-16",
        {"required": 1.0},
        {"required": 1.0, "also_required": 2.0},
        tracked_comparison_policy=str(material["MATH-16"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("structural comparison accepted an omitted field")
    try:
        _compile_comparison_policy("UNKNOWN_COMPARISON_POLICY", math_id="MATH-01")
    except ValueError as exc:
        if "tracked comparison policy mismatch" not in str(exc):
            raise
    else:
        raise ValueError("tracked-policy/registry-policy mismatch was accepted")
    try:
        _compile_comparison_policy("UNKNOWN_COMPARISON_POLICY", math_id="MATH-99")
    except ValueError as exc:
        if "unknown architecture comparator row" not in str(exc):
            raise
    else:
        raise ValueError("unknown comparator row was accepted")
    if _compare_architecture_payload(
        "MATH-01",
        {"p_market": 0.42},
        {"p_market": "0.42"},
        tracked_comparison_policy=str(material["MATH-01"]["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("exact Decimal comparison accepted float coercion")
    return 15 + len(math_02_matrix)


def _apply_declared_mutation(inputs: object, mutation: Mapping[str, object]) -> object:
    path = mutation.get("path")
    if not isinstance(path, list) or not path:
        raise ValueError("property mutation path must be nonempty")
    return _mutated_copy(inputs, path, mutation.get("replacement"))


def _v34_frozen_literal_checks(failures: list[str]) -> None:
    try:
        trees = {
            name: ast.parse(
                (PACKAGE / name).read_text(encoding="utf-8"),
                filename=str(PACKAGE / name),
            )
            for name in (
                "specification.py",
                "bindings.py",
                "parameter_policy.py",
                "oracle_contracts.py",
                "quantum_adapter.py",
                "validation.py",
            )
        }
        requirements = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_REQUIREMENTS_JSON"
        )
        input_contracts = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_INPUT_CONTRACTS_JSON"
        )
        output_contracts = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_OUTPUT_CONTRACTS_JSON"
        )
        formula_dispositions = _json_rows(
            trees["specification.py"], "_ST12B_FORMULA_DISPOSITIONS_JSON"
        )
        formula_input_owners = _json_rows(
            trees["bindings.py"], "_ST12B_FORMULA_INPUT_AUTHORITY_JSON"
        )
        primary_sources = _json_rows(
            trees["bindings.py"], "_ST12B_PRIMARY_SOURCE_REGISTRY_JSON"
        )
        source_conflicts = _json_rows(
            trees["bindings.py"], "_ST12B_SOURCE_CONFLICT_RESOLUTION_JSON"
        )
        source_currentizations = _json_rows(
            trees["bindings.py"], "_ST12B_SOURCE_CURRENTIZATION_JSON"
        )
        numeric_authorities = _json_rows(
            trees["bindings.py"], "_ST12B_NUMERIC_VALUE_AUTHORITY_JSON"
        )
        online_currentizations = _json_rows(
            trees["bindings.py"], "_ST12B_ONLINE_CURRENTIZATION_JSON"
        )
        parameter_crosswalk = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_CROSSWALK_JSON"
        )
        parameter_applications = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_APPLICATION_JSON"
        )
        parameter_ultimate = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_ULTIMATE_JSON"
        )
        parameter_runtime = _json_rows(
            trees["parameter_policy.py"],
            "_ST12B_RUNTIME_PARAMETER_OWNER_JSON",
        )
        parameter_dispositions = _json_rows(
            trees["parameter_policy.py"], "_ST12B_PARAMETER_DISPOSITION_JSON"
        )
        optimizer_currentizations = _json_rows(
            trees["parameter_policy.py"],
            "_ST12B_OPTIMIZER_DEFAULT_CURRENTIZATION_JSON",
        )
        oracles = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_ORACLE_CONTRACTS_JSON"
        )
        vectors = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_VECTOR_PACK_JSON"
        )
        properties = _json_rows(
            trees["oracle_contracts.py"], "_ST12B_PROPERTY_PACK_JSON"
        )
        quantum = _json_rows(
            trees["quantum_adapter.py"],
            "_ST12B_QUANTUM_STRUCTURAL_READINESS_JSON",
        )
        agent_dag = _json_rows(
            trees["validation.py"], "_ST12B_AGENT_CONSUMER_DAG_JSON"
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"v3.4 frozen literals could not be reconstructed: {exc}")
        return

    formula_ids = tuple(str(row.get("math_spec_id")) for row in requirements)
    if formula_ids != EXPECTED_ST12B_MATH_IDS:
        failures.append("v3.4 formula requirement identities are not exact")
    if any(
        tuple(str(row.get("math_spec_id")) for row in rows)
        != EXPECTED_ST12B_MATH_IDS
        for rows in (
            input_contracts,
            output_contracts,
            formula_dispositions,
            oracles,
        )
    ):
        failures.append("v3.4 formula/input/output/oracle identities are not aligned")
    if (
        len(output_contracts) != 30
        or sum(len(row.get("members", ())) for row in output_contracts) != 130
        or any(row.get("schema_version") != "ST12B_OUTPUT_V3_4" for row in output_contracts)
    ):
        failures.append("v3.4 named output closure is not 30 schemas/130 members")
    if Counter(str(row.get("disposition")) for row in formula_dispositions) != {
        "REUSE_EXISTING_EXACT_VERSION": 10,
        "REGISTER_SEMANTIC_SUCCESSOR": 9,
        "NEW_TRANCHE_B_IMPLEMENTATION": 11,
    }:
        failures.append("v3.4 formula repository dispositions are not 10/9/11")
    if (
        len(formula_input_owners) != 142
        or len({row.get("binding_id") for row in formula_input_owners}) != 142
    ):
        failures.append("v3.4 formula-input owner denominator is not 142")
    if (
        len(primary_sources) != 55
        or Counter(
            str(row.get("normalized_source_class")) for row in primary_sources
        )
        != {
            "EXTERNAL_PRIMARY_OR_OFFICIAL_SOURCE": 24,
            "OWNER_FORMAL_DERIVATION": 30,
            "OWNER_ARCHITECTURE_OR_POLICY": 1,
        }
        or len(source_conflicts) != 1
        or len(source_currentizations) != 7
        or len(online_currentizations) != 5
    ):
        failures.append("v3.4 source/currentization population is not exact")
    if (
        len(numeric_authorities) != 621
        or Counter(str(row.get("subject_kind")) for row in numeric_authorities)
        != {"PARAMETER": 479, "FORMULA_INPUT": 142}
    ):
        failures.append("v3.4 numeric-value authority population is not 479+142")

    parameter_sets = tuple(
        {str(row.get("parameter_id")) for row in rows}
        for rows in (
            parameter_crosswalk,
            parameter_applications,
            parameter_ultimate,
            parameter_dispositions,
            optimizer_currentizations,
        )
    )
    if (
        any(len(rows) != 479 for rows in parameter_sets)
        or any(rows != parameter_sets[0] for rows in parameter_sets[1:])
        or len(parameter_runtime) != 190
        or not {
            str(row.get("parameter_id")) for row in parameter_runtime
        } <= parameter_sets[0]
        or any(
            row.get("generic_compiler_is_sole_terminal_consumer") is not False
            for row in parameter_ultimate
        )
    ):
        failures.append("v3.4 parameter owner/application closure is not exact")
    if (
        len(vectors) != 90
        or Counter(str(row.get("math_spec_id")) for row in vectors)
        != {math_id: 3 for math_id in EXPECTED_ST12B_MATH_IDS}
        or len(properties) != 30
        or tuple(str(row.get("math_spec_id")) for row in properties)
        != EXPECTED_ST12B_MATH_IDS
    ):
        failures.append("v3.4 oracle/vector/property closure is not 30/90/30")
    if (
        tuple(str(row.get("math_spec_id")) for row in quantum)
        != ("MATH-46", "MATH-47", "MATH-48", "MATH-49")
        or any(row.get("qpu_or_simulator_authority") is not False for row in quantum)
    ):
        failures.append("v3.4 quantum structural readiness is not exact/no-QPU")
    if (
        len(agent_dag) != 1351
        or len({row.get("edge_id") for row in agent_dag}) != 1351
        or any(row.get("orphan_state") is not False for row in agent_dag)
        or Counter(str(row.get("edge_kind")) for row in agent_dag)
        != {
            "FORMULA_SPECIFICATION_TO_CENTRAL_EXECUTION_CONTRACT": 30,
            "NUMERIC_VALUE_OWNER_TO_FORMULA_INPUT": 142,
            "DATA_FLOW_EDGE": 1,
            "CALLABLE_OR_SUBROUTINE_DEPENDENCY": 4,
            "SHARED_POLICY_OR_METHOD_DEPENDENCY": 1,
            "PARAMETER_POLICY_TO_CENTRAL_COMPILER": 479,
            "PARAMETER_POLICY_TO_ULTIMATE_BEHAVIOR_OR_HELD_OWNER": 479,
            "RUNTIME_VALUE_OWNER_TO_PARAMETER_POLICY": 190,
            "PARAMETER_TO_DIRECT_FORMULA_POLICY": 25,
        }
    ):
        failures.append("v3.4 agent/consumer DAG is not the exact 1,351 routes")


def _bh(p_values: tuple[float, ...], q: float, correction: float) -> tuple[int, ...]:
    if (
        not p_values
        or any(not math.isfinite(value) or not 0 <= value <= 1 for value in p_values)
        or not 0 < q <= 1
        or not math.isfinite(correction)
        or correction < 1
    ):
        raise ValueError("invalid multiple-testing inputs")
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    largest = 0
    for rank, (_index, value) in enumerate(ordered, 1):
        if value <= rank * q / (len(ordered) * correction):
            largest = rank
    return tuple(sorted(index for index, _value in ordered[:largest]))


def _adjusted_p(
    p_values: tuple[float, ...],
    correction: float,
) -> tuple[float, ...]:
    _bh(p_values, 1.0, correction)
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    adjusted_by_rank = [1.0] * len(ordered)
    running = 1.0
    for rank in range(len(ordered), 0, -1):
        running = min(
            running,
            ordered[rank - 1][1] * len(ordered) * correction / rank,
            1.0,
        )
        adjusted_by_rank[rank - 1] = running
    result = [0.0] * len(ordered)
    for (original_index, _value), adjusted in zip(
        ordered,
        adjusted_by_rank,
        strict=True,
    ):
        result[original_index] = adjusted
    return tuple(result)


def _expect_value_error(callable_) -> bool:
    try:
        callable_()
    except (ValueError, ArithmeticError, OverflowError):
        return True
    return False


def _probability_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(
        value,
        Decimal | str | int | float,
    ):
        raise ValueError("invalid probability type")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite probability")
        converted = Decimal(repr(value))
    else:
        converted = Decimal(value)
    if not Decimal(0) <= converted <= Decimal(1):
        raise ValueError("probability outside [0,1]")
    return converted


def _binary_net(
    quantity: object,
    probability: object,
    win_cash: object,
    lose_cash: object,
    *friction: object,
) -> Decimal:
    quantity_value = Decimal(quantity)
    if quantity_value < 0:
        raise ValueError("negative quantity")
    p = _probability_decimal(probability)
    friction_values = tuple(Decimal(value) for value in friction)
    if any(value < 0 for value in friction_values):
        raise ValueError("negative friction")
    return (
        quantity_value
        * (p * Decimal(win_cash) + (Decimal(1) - p) * Decimal(lose_cash))
        - sum(friction_values, Decimal(0))
    )


def _normalize_probabilities(values: tuple[object, ...]) -> tuple[Decimal, ...]:
    if not values:
        raise ValueError("empty probabilities")
    floats = tuple(float(value) for value in values)
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in floats):
        raise ValueError("invalid probability")
    tolerance = 8 * math.ulp(1.0) * len(values)
    if abs(math.fsum(floats) - 1.0) > tolerance:
        raise ValueError("probability closure")
    canonical = tuple(_probability_decimal(value) for value in values)
    total = sum(canonical, Decimal(0))
    if total <= 0 or abs(total - Decimal(1)) > Decimal(repr(tolerance)):
        raise ValueError("decimal probability closure")
    return tuple(value / total for value in canonical)


def _multi_net(
    probabilities: tuple[object, ...],
    payoffs: tuple[object, ...],
    quantity: object,
    *friction: object,
) -> Decimal:
    if len(probabilities) != len(payoffs):
        raise ValueError("vector mismatch")
    normalized = _normalize_probabilities(probabilities)
    products = sorted(
        probability * Decimal(payoff)
        for probability, payoff in zip(normalized, payoffs, strict=True)
    )
    return (
        Decimal(quantity) * sum(products, Decimal(0))
        - sum((Decimal(value) for value in friction), Decimal(0))
    )


def _brier(p: object, y: object) -> float:
    if isinstance(p, tuple):
        if not isinstance(y, tuple) or len(p) != len(y):
            raise ValueError("vector mismatch")
        probabilities = tuple(float(value) for value in p)
        if (
            abs(math.fsum(probabilities) - 1.0)
            > 8 * math.ulp(1.0) * len(probabilities)
            or any(value not in (0, 1) for value in y)
            or sum(y) != 1
        ):
            raise ValueError("invalid multiclass brier inputs")
        return math.fsum(
            (probability - outcome) ** 2
            for probability, outcome in zip(probabilities, y, strict=True)
        )
    probability = float(_probability_decimal(p))
    if isinstance(y, bool) or y not in (0, 1):
        raise ValueError("unresolved outcome")
    return (probability - y) ** 2


def _log_loss(p: object, y: int, epsilon: float = math.ulp(1.0)) -> float:
    probability = float(_probability_decimal(p))
    if isinstance(y, bool) or y not in (0, 1):
        raise ValueError("unresolved outcome")
    if not 0 < epsilon < 0.5:
        raise ValueError("invalid clipping")
    clipped = min(max(probability, epsilon), 1.0 - epsilon)
    result = -(y * log(clipped) + (1 - y) * log(1 - clipped))
    if not math.isfinite(result):
        raise ValueError("nonfinite loss")
    return result


def _wilson(successes: int, trials: int, confidence: float) -> tuple[float, float]:
    if (
        isinstance(successes, bool)
        or isinstance(trials, bool)
        or trials <= 0
        or not 0 <= successes <= trials
        or not 0 < confidence < 1
    ):
        raise ValueError("invalid Wilson inputs")
    z = NormalDist().inv_cdf(1.0 - (1.0 - confidence) / 2.0)
    phat = successes / trials
    denominator = 1.0 + z * z / trials
    center = (phat + z * z / (2.0 * trials)) / denominator
    half = (
        z
        / denominator
        * sqrt(
            phat * (1.0 - phat) / trials
            + z * z / (4.0 * trials * trials)
        )
    )
    return max(0.0, center - half), min(1.0, center + half)


def _ece_from_raw(
    probabilities: tuple[float, ...],
    outcomes: tuple[int, ...],
    edges: tuple[float, ...],
) -> float:
    if (
        not probabilities
        or len(probabilities) != len(outcomes)
        or len(edges) < 2
        or edges[0] != 0.0
        or edges[-1] != 1.0
        or any(left >= right for left, right in zip(edges, edges[1:]))
        or any(not 0 <= value <= 1 for value in probabilities)
        or any(value not in (0, 1) for value in outcomes)
    ):
        raise ValueError("invalid calibration rows")
    weighted_error = 0.0
    for left, right in zip(edges, edges[1:]):
        indices = tuple(
            index
            for index, probability in enumerate(probabilities)
            if left <= probability < right
            or (right == 1.0 and probability == 1.0)
        )
        if not indices:
            continue
        confidence = sum(probabilities[index] for index in indices) / len(indices)
        frequency = sum(outcomes[index] for index in indices) / len(indices)
        weighted_error += (
            len(indices) / len(probabilities) * abs(confidence - frequency)
        )
    return weighted_error


def _white_reality_p_value(
    time_rows: tuple[tuple[float, ...], ...],
    *,
    benchmark_minus_candidate: bool,
    seed: int,
    replicates: int,
) -> float:
    if (
        not time_rows
        or not time_rows[0]
        or not any(value != 0.0 for row in time_rows for value in row)
    ):
        raise ValueError("uninformative loss differentials")
    candidates = tuple(zip(*time_rows, strict=True))
    if not benchmark_minus_candidate:
        candidates = tuple(
            tuple(-value for value in candidate) for candidate in candidates
        )
    length = len(time_rows)
    means = tuple(sum(candidate) / length for candidate in candidates)
    observed = max(sqrt(length) * mean for mean in means)
    rng = Random(seed)
    exceedances = 0
    for _ in range(replicates):
        current = rng.randrange(length)
        indices = [current]
        for _position in range(1, length):
            if rng.random() < 0.5:
                current = rng.randrange(length)
            else:
                current = (current + 1) % length
            indices.append(current)
        statistic = max(
            sqrt(length)
            * (
                sum(candidate[index] for index in indices) / length
                - candidate_mean
            )
            for candidate, candidate_mean in zip(candidates, means, strict=True)
        )
        if statistic >= observed:
            exceedances += 1
    return exceedances / replicates


def _stationary_sample_indices(
    length: int,
    expected_block_length: float,
    rng: Random,
) -> tuple[int, ...]:
    restart_probability = 1.0 / expected_block_length
    current = rng.randrange(length)
    indices = [current]
    for _ in range(1, length):
        if rng.random() < restart_probability:
            current = rng.randrange(length)
        else:
            current = (current + 1) % length
        indices.append(current)
    return tuple(indices)


def _spa_long_run_variance(values: Sequence[float], block: float) -> float:
    count = len(values)
    center = _mean(values)
    demeaned = tuple(value - center for value in values)
    restart_probability = 1.0 / block
    variance = math.fsum(value * value for value in demeaned) / count
    for lag in range(1, count):
        weight = (1.0 - lag / count) * (
            (1.0 - restart_probability) ** lag
        ) + (lag / count) * (
            (1.0 - restart_probability) ** (count - lag)
        )
        covariance = math.fsum(
            demeaned[index] * demeaned[index + lag]
            for index in range(count - lag)
        ) / count
        variance += 2.0 * weight * covariance
    return max(0.0, variance)


def _independent_math_16(inputs: Mapping[str, object]) -> dict[str, object]:
    matrix = _matrix(inputs.get("loss_differentials"), "loss_differentials")
    convention = inputs.get("sign_convention")
    if convention == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER":
        pass
    elif convention == (
        "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER"
    ):
        matrix = [[-value for value in row] for row in matrix]
    else:
        raise ValueError("unsupported loss-differential sign convention")
    observation_count = len(matrix)
    if observation_count < 3:
        raise ValueError("Hansen SPA requires at least three observations")
    if inputs.get("recenter_variant") != "HANSEN_CONSISTENT_LOG_LOG_THRESHOLD":
        raise ValueError("unsupported Hansen SPA recentering rule")
    seed = inputs.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Hansen SPA seed must be an integer")
    replicates = _positive_int(inputs.get("replicates"), "replicates")
    block = _finite(inputs.get("expected_block_length"), "expected_block_length")
    if not 1.0 <= block <= observation_count:
        raise ValueError("expected block length must be in [1,n]")
    alpha = _finite(inputs.get("alpha"), "alpha")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0,1)")

    candidates = tuple(zip(*matrix, strict=True))
    means = tuple(_mean(candidate) for candidate in candidates)
    variances = tuple(
        _spa_long_run_variance(candidate, block) for candidate in candidates
    )
    valid: list[bool] = []
    standardized: list[float] = []
    for index, (center, variance) in enumerate(
        zip(means, variances, strict=True)
    ):
        if variance <= 0.0:
            if center > 0.0:
                raise ValueError(
                    f"candidate {index} has positive mean and zero long-run variance"
                )
            valid.append(False)
            standardized.append(float("-inf"))
            continue
        threshold = -math.sqrt(
            variance
            / observation_count
            * 2.0
            * math.log(math.log(observation_count))
        )
        valid.append(center >= threshold)
        standardized.append(
            math.sqrt(observation_count) * center / math.sqrt(variance)
        )
    statistic = max(
        0.0,
        max((value for value in standardized if math.isfinite(value)), default=0.0),
    )
    recentered = tuple(
        center if admitted else 0.0
        for center, admitted in zip(means, valid, strict=True)
    )
    rng = Random(seed)
    simulated: list[float] = []
    exceedances = 0
    for _ in range(replicates):
        indices = _stationary_sample_indices(observation_count, block, rng)
        draw = max(
            0.0,
            max(
                (
                    math.sqrt(observation_count)
                    * (
                        math.fsum(candidate[index] for index in indices)
                        / observation_count
                        - center
                    )
                    / math.sqrt(variance)
                    for candidate, center, variance in zip(
                        candidates,
                        recentered,
                        variances,
                        strict=True,
                    )
                    if variance > 0.0
                ),
                default=0.0,
            ),
        )
        simulated.append(draw)
        if draw >= statistic:
            exceedances += 1
    p_value = (1 + exceedances) / (replicates + 1)
    return {
        "statistic": statistic,
        "p_value": p_value,
        "reject": p_value <= alpha,
        "candidate_means": list(means),
        "long_run_variances": list(variances),
        "consistent_valid_columns": valid,
        "simulated_statistics": simulated,
        "recenter_variant": inputs["recenter_variant"],
    }


def _probabilistic_sharpe(
    observed_sharpe: object,
    reference_sharpe: object,
    observations: object,
    skewness: object,
    kurtosis: object,
) -> dict[str, float]:
    observed = _finite(observed_sharpe, "observed_sharpe")
    reference = _finite(reference_sharpe, "reference_sharpe")
    count = _positive_int(
        observations,
        "independent_equivalent_observations",
        minimum=2,
    )
    skew = _finite(skewness, "skewness")
    non_excess_kurtosis = _finite(kurtosis, "kurtosis")
    if non_excess_kurtosis < 1.0:
        raise ValueError("non-excess kurtosis must be at least one")
    denominator_squared = (
        1.0
        - skew * observed
        + ((non_excess_kurtosis - 1.0) / 4.0) * observed * observed
    )
    if denominator_squared <= 0.0:
        raise ValueError("probabilistic Sharpe denominator must be positive")
    z_score = (
        (observed - reference)
        * math.sqrt(count - 1)
        / math.sqrt(denominator_squared)
    )
    return {
        "probabilistic_sharpe_ratio": NormalDist().cdf(z_score),
        "z_score": z_score,
    }


def _independent_math_17(inputs: Mapping[str, object]) -> dict[str, float]:
    return _probabilistic_sharpe(
        inputs.get("estimated_sharpe"),
        inputs.get("reference_sharpe"),
        inputs.get("independent_equivalent_observations"),
        inputs.get("sample_skewness"),
        inputs.get("sample_non_excess_kurtosis"),
    )


def _expected_maximum_sharpe(
    trial_mean: float,
    trial_variance: float,
    effective_count: float,
) -> float:
    if not effective_count > 1.0:
        raise ValueError(
            "effective independent trial count must be greater than one"
        )
    euler_mascheroni = 0.5772156649015329
    return trial_mean + math.sqrt(trial_variance) * (
        (1.0 - euler_mascheroni)
        * NormalDist().inv_cdf(1.0 - 1.0 / effective_count)
        + euler_mascheroni
        * NormalDist().inv_cdf(1.0 - 1.0 / (effective_count * math.e))
    )


def _independent_math_18(inputs: Mapping[str, object]) -> dict[str, float]:
    sharpes = tuple(
        _finite(value, f"complete_material_trial_sharpes[{index}]")
        for index, value in enumerate(
            _sequence(
                inputs.get("complete_material_trial_sharpes"),
                "complete_material_trial_sharpes",
                minimum=2,
            )
        )
    )
    effective_count = _finite(
        inputs.get("effective_independent_trial_count"),
        "effective_independent_trial_count",
    )
    if not 1.0 < effective_count <= len(sharpes):
        raise ValueError(
            "effective independent trial count must be in "
            "(1, material trial count]"
        )
    trial_mean = _mean(sharpes)
    trial_variance = _sample_variance(sharpes)
    expected_maximum = _expected_maximum_sharpe(
        trial_mean,
        trial_variance,
        effective_count,
    )
    psr = _probabilistic_sharpe(
        inputs.get("candidate_estimated_sharpe"),
        expected_maximum,
        inputs.get("candidate_independent_equivalent_observations"),
        inputs.get("candidate_sample_skewness"),
        inputs.get("candidate_sample_non_excess_kurtosis"),
    )
    return {
        "deflated_sharpe_ratio": psr["probabilistic_sharpe_ratio"],
        "expected_maximum_sharpe_threshold": expected_maximum,
        "trial_mean_sharpe": trial_mean,
        "trial_sharpe_variance": trial_variance,
    }


def _stable_midranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        midrank = ((cursor + 1) + end) / 2.0
        for index in order[cursor:end]:
            ranks[index] = midrank
        cursor = end
    return ranks


def _independent_math_19(inputs: Mapping[str, object]) -> dict[str, object]:
    matrix = _matrix(inputs.get("performance_matrix"), "performance_matrix")
    strategy_ids = _sequence(inputs.get("strategy_ids"), "strategy_ids")
    if (
        len(strategy_ids) != len(matrix[0])
        or len(strategy_ids) != len(set(strategy_ids))
        or any(not isinstance(value, str) or not value for value in strategy_ids)
    ):
        raise ValueError("strategy IDs must uniquely identify every column")
    group_count = _positive_int(inputs.get("S"), "S", minimum=2)
    if group_count % 2 or len(matrix) % group_count:
        raise ValueError("S must be even and exactly partition the observations")
    width = len(matrix) // group_count
    groups = tuple(
        tuple(range(group * width, (group + 1) * width))
        for group in range(group_count)
    )
    split_rows: list[dict[str, object]] = []
    logits: list[float] = []
    for train_groups_tuple in combinations(range(group_count), group_count // 2):
        train_groups = set(train_groups_tuple)
        train_indices = tuple(
            index for group in train_groups for index in groups[group]
        )
        test_indices = tuple(
            index
            for group in range(group_count)
            if group not in train_groups
            for index in groups[group]
        )
        train_means = tuple(
            math.fsum(matrix[index][column] for index in train_indices)
            / len(train_indices)
            for column in range(len(strategy_ids))
        )
        best = max(train_means)
        winner = min(
            (
                column
                for column, value in enumerate(train_means)
                if value == best
            ),
            key=lambda column: str(strategy_ids[column]),
        )
        test_means = tuple(
            math.fsum(matrix[index][column] for index in test_indices)
            / len(test_indices)
            for column in range(len(strategy_ids))
        )
        ranks = _stable_midranks(test_means)
        relative_rank = ranks[winner] / (len(strategy_ids) + 1.0)
        logit_value = math.log(relative_rank / (1.0 - relative_rank))
        logits.append(logit_value)
        split_rows.append(
            {
                "train_groups": list(train_groups_tuple),
                "is_winner_strategy_id": strategy_ids[winner],
                "oos_midrank_worst_1_best_n": ranks[winner],
                "relative_rank": relative_rank,
                "logit": logit_value,
            }
        )
    return {
        "probability_of_backtest_overfitting": (
            sum(value <= 0.0 for value in logits) / len(logits)
        ),
        "S": group_count,
        "split_count": len(split_rows),
        "logits": logits,
        "splits": split_rows,
    }


def _parsed_intervals(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(_sequence(value, "sample_intervals")):
        if not isinstance(raw, Mapping):
            raise ValueError("sample interval must be a mapping")
        identifier = raw.get("sample_id")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
        ):
            raise ValueError("sample IDs must be unique nonempty strings")
        identifiers.add(identifier)
        start = _finite(raw.get("start"), f"interval[{index}].start")
        end = _finite(raw.get("end"), f"interval[{index}].end")
        if not start < end:
            raise ValueError(
                "intervals use half-open [start,end) semantics and require start<end"
            )
        rows.append({"sample_id": identifier, "start": start, "end": end})
    return sorted(
        rows,
        key=lambda row: (
            float(row["start"]),
            float(row["end"]),
            str(row["sample_id"]),
        ),
    )


def _balanced_blocks(length: int, count: int) -> list[list[int]]:
    if not 2 <= count <= length:
        raise ValueError("fold/group count must be in [2,n]")
    base, remainder = divmod(length, count)
    blocks: list[list[int]] = []
    cursor = 0
    for index in range(count):
        width = base + (1 if index < remainder else 0)
        blocks.append(list(range(cursor, cursor + width)))
        cursor += width
    return blocks


def _intervals_overlap(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return float(left["start"]) < float(right["end"]) and float(
        right["start"]
    ) < float(left["end"])


def _merged_intervals(rows: Sequence[Mapping[str, object]]) -> list[tuple[float, float]]:
    ordered = sorted((float(row["start"]), float(row["end"])) for row in rows)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _purged_split(
    intervals: Sequence[Mapping[str, object]],
    test_indices: Sequence[int],
    embargo_duration: float,
) -> dict[str, object]:
    if any(index < 0 or index >= len(intervals) for index in test_indices):
        raise ValueError("test index is outside the interval population")
    test_set = set(test_indices)
    test = [intervals[index] for index in test_indices]
    merged = _merged_intervals(test)
    train: list[str] = []
    purged: list[str] = []
    embargoed: list[str] = []
    for index, row in enumerate(intervals):
        if index in test_set:
            continue
        identifier = str(row["sample_id"])
        if any(_intervals_overlap(row, test_row) for test_row in test):
            purged.append(identifier)
        elif any(
            end <= float(row["start"]) < end + embargo_duration
            for _, end in merged
        ):
            embargoed.append(identifier)
        else:
            train.append(identifier)
    return {
        "test_sample_ids": [str(row["sample_id"]) for row in test],
        "train_sample_ids": train,
        "purged_sample_ids": purged,
        "embargoed_sample_ids": embargoed,
        "merged_test_intervals": [list(value) for value in merged],
    }


def _independent_math_20(inputs: Mapping[str, object]) -> dict[str, object]:
    intervals = _parsed_intervals(inputs.get("sample_intervals"))
    fold_count = _positive_int(inputs.get("folds"), "folds", minimum=2)
    embargo = _finite(inputs.get("embargo_duration"), "embargo_duration")
    if embargo < 0.0:
        raise ValueError("embargo duration must be nonnegative")
    results: list[dict[str, object]] = []
    for fold_id, indices in enumerate(_balanced_blocks(len(intervals), fold_count)):
        row = _purged_split(intervals, indices, embargo)
        row["fold_id"] = fold_id
        results.append(row)
    return {
        "ordered_sample_ids": [str(row["sample_id"]) for row in intervals],
        "interval_semantics": "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE",
        "embargo_basis": "TIME_DURATION_AFTER_MERGED_TEST_INTERVAL",
        "folds": results,
    }


def _set_partitions(
    items: tuple[int, ...],
    block_size: int,
) -> list[tuple[tuple[int, ...], ...]]:
    if not items:
        return [tuple()]
    first = items[0]
    results: list[tuple[tuple[int, ...], ...]] = []
    for rest in combinations(items[1:], block_size - 1):
        block = tuple(sorted((first, *rest)))
        remaining = tuple(item for item in items if item not in block)
        for suffix in _set_partitions(remaining, block_size):
            results.append(tuple(sorted((block, *suffix))))
    return sorted(set(results))


def _resolvable_paths(
    group_count: int,
    test_group_count: int,
) -> list[list[tuple[int, ...]]]:
    if group_count % test_group_count:
        raise ValueError(
            "frozen CPCV path assembly requires k_test_groups to divide N_groups"
        )
    splits = list(combinations(range(group_count), test_group_count))
    partitions = _set_partitions(tuple(range(group_count)), test_group_count)
    target_count = math.comb(group_count - 1, test_group_count - 1)
    candidates = {
        split: tuple(partition for partition in partitions if split in partition)
        for split in splits
    }

    def solve(
        uncovered: frozenset[tuple[int, ...]],
        chosen: tuple[tuple[tuple[int, ...], ...], ...],
    ) -> tuple[tuple[tuple[int, ...], ...], ...] | None:
        if not uncovered:
            return chosen if len(chosen) == target_count else None
        if len(chosen) >= target_count:
            return None
        pivot = min(
            uncovered,
            key=lambda split: (
                sum(set(partition) <= uncovered for partition in candidates[split]),
                split,
            ),
        )
        for partition in candidates[pivot]:
            members = frozenset(partition)
            if members <= uncovered:
                answer = solve(uncovered - members, (*chosen, partition))
                if answer is not None:
                    return answer
        return None

    answer = solve(frozenset(splits), tuple())
    if answer is None:
        raise ValueError("deterministic CPCV path design does not exist")
    return [[tuple(block) for block in partition] for partition in answer]


def _independent_math_21(inputs: Mapping[str, object]) -> dict[str, object]:
    intervals = _parsed_intervals(inputs.get("sample_intervals"))
    group_count = _positive_int(inputs.get("N_groups"), "N_groups", minimum=2)
    test_group_count = _positive_int(inputs.get("k_test_groups"), "k_test_groups")
    if (
        not 1 <= test_group_count < group_count
        or group_count > len(intervals)
        or group_count > 8
    ):
        raise ValueError("CPCV requires 1<=k<N<=sample_count and N<=8")
    embargo = _finite(inputs.get("embargo_duration"), "embargo_duration")
    if embargo < 0.0:
        raise ValueError("embargo duration must be nonnegative")
    aggregation_rule = inputs.get("aggregation_rule")
    if aggregation_rule != "ALL_PATHS_NO_CHERRY_PICKING":
        raise ValueError(
            "aggregation_rule must equal ALL_PATHS_NO_CHERRY_PICKING"
        )
    groups = _balanced_blocks(len(intervals), group_count)
    split_rows: list[dict[str, object]] = []
    lookup: dict[tuple[int, ...], int] = {}
    for split_id, group_tuple in enumerate(
        combinations(range(group_count), test_group_count)
    ):
        test_indices = [index for group in group_tuple for index in groups[group]]
        row = _purged_split(intervals, test_indices, embargo)
        row.update({"split_id": split_id, "test_groups": list(group_tuple)})
        split_rows.append(row)
        lookup[group_tuple] = split_id
    partitions = _resolvable_paths(group_count, test_group_count)
    paths = [
        {
            "path_id": path_id,
            "split_ids": [lookup[tuple(block)] for block in partition],
            "test_group_partition": [list(block) for block in partition],
        }
        for path_id, partition in enumerate(partitions)
    ]
    expected_path_count = math.comb(group_count - 1, test_group_count - 1)
    if (
        len(paths) != expected_path_count
        or sorted(split_id for path in paths for split_id in path["split_ids"])
        != list(range(len(split_rows)))
    ):
        raise ValueError("CPCV path coverage invariant failed")
    return {
        "N_groups": group_count,
        "k_test_groups": test_group_count,
        "split_count": len(split_rows),
        "expected_path_count": expected_path_count,
        "path_count": len(paths),
        "aggregation_rule": aggregation_rule,
        "splits": split_rows,
        "paths": paths,
    }


def _logged_rows(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row_index, raw in enumerate(_sequence(value, "logged_rows")):
        if not isinstance(raw, Mapping):
            raise ValueError("logged row must be a mapping")
        behavior = tuple(
            _finite(item, f"behavior[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("behavior_action_probabilities"),
                    "behavior probabilities",
                )
            )
        )
        target = tuple(
            _finite(item, f"target[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("target_action_probabilities"),
                    "target probabilities",
                )
            )
        )
        predictions = tuple(
            _finite(item, f"reward_model[{index}]")
            for index, item in enumerate(
                _sequence(
                    raw.get("cross_fitted_reward_model_predictions"),
                    "reward-model predictions",
                )
            )
        )
        if not len(behavior) == len(target) == len(predictions):
            raise ValueError("behavior, target, and model vectors must align")
        if (
            any(value < 0.0 or value > 1.0 for value in (*behavior, *target))
            or abs(math.fsum(behavior) - 1.0) > 1e-12
            or abs(math.fsum(target) - 1.0) > 1e-12
            or any(
                pi > 0.0 and mu <= 0.0
                for mu, pi in zip(behavior, target, strict=True)
            )
        ):
            raise ValueError(
                "target support must be contained in behavior support and both "
                "policies must be probability simplexes"
            )
        action = raw.get("logged_action_index")
        fold_id = raw.get("fold_id")
        if (
            isinstance(action, bool)
            or not isinstance(action, int)
            or not 0 <= action < len(behavior)
            or isinstance(fold_id, bool)
            or not isinstance(fold_id, int)
            or fold_id < 0
            or raw.get("cross_fitted_prediction") is not True
        ):
            if raw.get("cross_fitted_prediction") is not True:
                raise ValueError("reward-model prediction must be cross-fitted")
            raise ValueError("logged action and fold state is invalid")
        rows.append(
            {
                "row_id": str(raw.get("row_id")),
                "behavior": behavior,
                "target": target,
                "model": predictions,
                "action": action,
                "reward": _finite(raw.get("reward"), f"reward[{row_index}]"),
                "fold_id": fold_id,
            }
        )
    return rows


def _logged_terms(row: Mapping[str, object]) -> tuple[float, float, float, float]:
    action = int(row["action"])
    behavior = row["behavior"]
    target = row["target"]
    model = row["model"]
    if not isinstance(behavior, tuple) or not isinstance(target, tuple) or not isinstance(model, tuple):
        raise ValueError("parsed logged vectors are unavailable")
    mu = float(behavior[action])
    pi = float(target[action])
    if pi > 0.0 and mu <= 0.0:
        raise ValueError("logged row violates positivity")
    weight = 0.0 if pi == 0.0 else pi / mu
    direct = math.fsum(
        float(probability) * float(prediction)
        for probability, prediction in zip(target, model, strict=True)
    )
    reward = float(row["reward"])
    residual = reward - float(model[action])
    return direct, weight, residual, reward


def _effective_sample_size(weights: Sequence[float]) -> float:
    total = math.fsum(weights)
    squares = math.fsum(value * value for value in weights)
    if total <= 0.0 or squares <= 0.0:
        raise ValueError("weights require positive total and squared total")
    return total * total / squares


def _independent_math_22(inputs: Mapping[str, object]) -> dict[str, object]:
    values: list[float] = []
    weights: list[float] = []
    for row in _logged_rows(inputs.get("logged_rows")):
        direct, weight, residual, _ = _logged_terms(row)
        values.append(direct + weight * residual)
        weights.append(weight)
    return {
        "doubly_robust_estimate": _mean(values),
        "row_values": values,
        "importance_weights": weights,
        "effective_sample_size": (
            _effective_sample_size(weights) if any(weight > 0.0 for weight in weights) else 0.0
        ),
        "clipping_applied": False,
    }


def _independent_math_23(inputs: Mapping[str, object]) -> dict[str, object]:
    values: list[float] = []
    weights: list[float] = []
    for row in _logged_rows(inputs.get("logged_rows")):
        _, weight, _, reward = _logged_terms(row)
        values.append(weight * reward)
        weights.append(weight)
    return {
        "inverse_propensity_score_estimate": _mean(values),
        "row_values": values,
        "importance_weights": weights,
        "effective_sample_size": (
            _effective_sample_size(weights) if any(weight > 0.0 for weight in weights) else 0.0
        ),
        "clipping_applied": False,
    }


def _independent_math_24(inputs: Mapping[str, object]) -> dict[str, float]:
    weights = tuple(
        _finite(item, f"weight[{index}]")
        for index, item in enumerate(_sequence(inputs.get("weights"), "weights"))
    )
    rewards = tuple(
        _finite(item, f"reward[{index}]")
        for index, item in enumerate(_sequence(inputs.get("rewards"), "rewards"))
    )
    if len(weights) != len(rewards):
        raise ValueError("weights and rewards must align")
    if any(weight < 0.0 for weight in weights):
        raise ValueError("weights must be nonnegative with positive total")
    total = math.fsum(weights)
    if total <= 0.0:
        raise ValueError("weights must be nonnegative with positive total")
    return {
        "self_normalized_ips_estimate": math.fsum(
            weight * reward for weight, reward in zip(weights, rewards, strict=True)
        )
        / total,
        "weight_sum": total,
        "effective_sample_size": _effective_sample_size(weights),
    }


def _tau(value: object) -> float:
    if value == "INF":
        return math.inf
    result = _finite(value, "tau")
    if result < 0.0:
        raise ValueError("tau must be nonnegative")
    return result


def _switch_value(row: Mapping[str, object], tau: float) -> float:
    direct, weight, residual, _ = _logged_terms(row)
    return direct + (weight * residual if weight <= tau else 0.0)


def _switch_bias_bound(
    rows: Sequence[Mapping[str, object]],
    tau: float,
    reward_range: float,
) -> float:
    masses: list[float] = []
    for row in rows:
        behavior = row["behavior"]
        target = row["target"]
        if not isinstance(behavior, tuple) or not isinstance(target, tuple):
            raise ValueError("parsed logged policy is unavailable")
        masses.append(
            math.fsum(
                float(pi)
                for mu, pi in zip(behavior, target, strict=True)
                if float(pi) > 0.0 and float(pi) / float(mu) > tau
            )
        )
    return reward_range * _mean(masses)


def _independent_math_25(inputs: Mapping[str, object]) -> dict[str, object]:
    rows = _logged_rows(inputs.get("logged_rows"))
    lower = _finite(inputs.get("reward_lower_bound"), "reward_lower_bound")
    upper = _finite(inputs.get("reward_upper_bound"), "reward_upper_bound")
    if not lower < upper or any(
        not lower <= float(row["reward"]) <= upper for row in rows
    ):
        raise ValueError("reward bounds must be ordered and cover rewards")
    fold_count = _positive_int(inputs.get("outer_fold_count"), "outer_fold_count", minimum=2)
    if {int(row["fold_id"]) for row in rows} != set(range(fold_count)):
        raise ValueError("fold IDs must cover 0..outer_fold_count-1")
    taus = [_tau(value) for value in _sequence(inputs.get("tau_grid"), "tau_grid")]
    if taus != sorted(set(taus)):
        raise ValueError("tau_grid must be unique and ascending")
    fold_results: list[dict[str, object]] = []
    held_out_values: list[float] = []
    for fold in range(fold_count):
        train = [row for row in rows if int(row["fold_id"]) != fold]
        held = [row for row in rows if int(row["fold_id"]) == fold]
        if len(train) < 2 or not held:
            raise ValueError("each fold requires training and held-out support")
        criteria: list[dict[str, object]] = []
        for tau in taus:
            values = [_switch_value(row, tau) for row in train]
            variance_of_mean = _sample_variance(values) / len(values)
            bias = _switch_bias_bound(train, tau, upper - lower)
            criteria.append(
                {
                    "tau": "INF" if math.isinf(tau) else tau,
                    "variance_of_mean": variance_of_mean,
                    "bias_upper_bound": bias,
                    "estimated_mse_upper_bound": variance_of_mean + bias * bias,
                }
            )
        selected_index = min(
            range(len(criteria)),
            key=lambda index: (
                float(criteria[index]["estimated_mse_upper_bound"]),
                taus[index],
            ),
        )
        selected_tau = taus[selected_index]
        values = [_switch_value(row, selected_tau) for row in held]
        held_out_values.extend(values)
        fold_results.append(
            {
                "outer_fold": fold,
                "selected_tau": "INF" if math.isinf(selected_tau) else selected_tau,
                "criteria": criteria,
                "held_out_row_values": values,
            }
        )
    return {
        "switch_ope_estimate": _mean(held_out_values),
        "held_out_row_values": held_out_values,
        "outer_fold_results": fold_results,
        "selection_rule": "MIN_ESTIMATED_MSE_UPPER_BOUND_THEN_SMALLEST_TAU",
        "clipping_applied": False,
    }


def _upper_qubo(
    diagonal_value: object,
    upper_terms_value: object,
    constant_value: object,
) -> tuple[tuple[float, ...], dict[tuple[int, int], float], float]:
    diagonal = tuple(
        _finite(value, f"diagonal[{index}]")
        for index, value in enumerate(_sequence(diagonal_value, "diagonal"))
    )
    upper: dict[tuple[int, int], float] = {}
    for index, raw in enumerate(_sequence(upper_terms_value, "upper_terms", minimum=0)):
        if not isinstance(raw, Mapping):
            raise ValueError("upper-triangular term must be a mapping")
        left = raw.get("i")
        right = raw.get("j")
        if isinstance(left, int) and isinstance(right, int) and (left, right) in upper:
            raise ValueError("duplicate upper-triangular interaction")
        if (
            isinstance(left, bool)
            or not isinstance(left, int)
            or isinstance(right, bool)
            or not isinstance(right, int)
            or not 0 <= left < right < len(diagonal)
        ):
            raise ValueError("QUBO interactions require unique indices with 0<=i<j<n")
        upper[(left, right)] = _finite(raw.get("value"), f"upper_terms[{index}].value")
    return diagonal, upper, _finite(constant_value, "constant")


def _canonical_qubo_from_current_inputs(
    inputs: Mapping[str, object],
) -> tuple[tuple[float, ...], dict[tuple[int, int], float], float, dict[str, object]]:
    representation = inputs.get("representation")
    diagonal = tuple(
        _finite(value, f"diagonal[{index}]")
        for index, value in enumerate(_sequence(inputs.get("diagonal"), "diagonal"))
    )
    if len(diagonal) > 12:
        raise ValueError("bounded exact QUBO enumeration supports at most 12 variables")
    constant = _finite(inputs.get("constant"), "constant")
    raw_upper = _sequence(inputs.get("upper_terms"), "upper_terms", minimum=0)
    raw_matrix = _sequence(
        inputs.get("full_symmetric_matrix"),
        "full_symmetric_matrix",
        minimum=0,
    )
    if representation == "CANONICAL_UPPER_TRIANGULAR":
        if raw_matrix:
            raise ValueError(
                "canonical upper-triangular representation conflicts with full matrix"
            )
        parsed_diagonal, upper, parsed_constant = _upper_qubo(
            diagonal,
            raw_upper,
            constant,
        )
    elif representation == "FULL_SYMMETRIC_ADAPTER_SUM_OFF_DIAGONAL_PAIRS":
        if raw_upper:
            raise ValueError(
                "full-symmetric representation conflicts with upper-triangular terms"
            )
        if len(raw_matrix) != len(diagonal):
            raise ValueError("full symmetric matrix must be square with declared dimension")
        matrix: list[list[float]] = []
        for row_index, raw_row in enumerate(raw_matrix):
            if (
                isinstance(raw_row, str | bytes)
                or not isinstance(raw_row, Sequence)
                or len(raw_row) != len(diagonal)
            ):
                raise ValueError(
                    "full symmetric matrix must be square with declared dimension"
                )
            matrix.append(
                [
                    _finite(value, f"full_symmetric_matrix[{row_index}][{column}]")
                    for column, value in enumerate(raw_row)
                ]
            )
        if any(matrix[index][index] != diagonal[index] for index in range(len(diagonal))):
            raise ValueError("full symmetric matrix diagonal conflicts with explicit diagonal")
        parsed_diagonal = diagonal
        upper = {
            (left, right): matrix[left][right] + matrix[right][left]
            for left in range(len(diagonal))
            for right in range(left + 1, len(diagonal))
        }
        parsed_constant = constant
    else:
        raise ValueError("unknown QUBO representation")
    canonical = {
        "constant": parsed_constant,
        "diagonal": list(parsed_diagonal),
        "representation": "CANONICAL_UPPER_TRIANGULAR",
        "schema_version": "CANONICAL_QUBO_MODEL_V1",
        "upper_terms": [
            {"i": left, "j": right, "value": coefficient}
            for (left, right), coefficient in sorted(upper.items())
        ],
        "variable_count": len(parsed_diagonal),
    }
    return parsed_diagonal, upper, parsed_constant, canonical


def _binary_assignment(value: object, variable_count: int) -> tuple[int, ...]:
    raw = _sequence(value, "binary_assignment")
    if (
        len(raw) != variable_count
        or any(isinstance(item, bool) or not isinstance(item, int) or item not in (0, 1) for item in raw)
    ):
        raise ValueError(
            "binary_assignment must contain one binary integer per variable"
        )
    return tuple(raw)


def _qubo_energy(
    diagonal: Sequence[float],
    upper: Mapping[tuple[int, int], float],
    offset: float,
    assignment_value: object,
) -> float:
    assignment = _binary_assignment(assignment_value, len(diagonal))
    return (
        offset
        + math.fsum(diagonal[index] * int(value) for index, value in enumerate(assignment))
        + math.fsum(
            coefficient * int(assignment[left]) * int(assignment[right])
            for (left, right), coefficient in upper.items()
        )
    )


def _independent_math_46(inputs: Mapping[str, object]) -> dict[str, object]:
    diagonal, upper, constant, canonical = _canonical_qubo_from_current_inputs(inputs)
    selected = _binary_assignment(inputs.get("binary_assignment"), len(diagonal))
    ledger = [
        {
            "binary_assignment": list(assignment),
            "energy": _qubo_energy(diagonal, upper, constant, assignment),
        }
        for assignment in product((0, 1), repeat=len(diagonal))
    ]
    if len(ledger) != 2 ** len(diagonal):
        raise ValueError("bounded QUBO enumeration is incomplete")
    return {
        "binary_assignment": list(selected),
        "canonical_qubo": canonical,
        "energy": _qubo_energy(diagonal, upper, constant, selected),
        "exhaustive_assignments": ledger,
    }


def _ising_from_qubo(
    diagonal: Sequence[float],
    upper: Mapping[tuple[int, int], float],
    offset: float,
) -> tuple[float, tuple[float, ...], dict[tuple[int, int], float]]:
    constant = offset + math.fsum(diagonal) / 2.0 + math.fsum(upper.values()) / 4.0
    linear = [-(value / 2.0) for value in diagonal]
    interactions: dict[tuple[int, int], float] = {}
    for (left, right), coefficient in upper.items():
        linear[left] -= coefficient / 4.0
        linear[right] -= coefficient / 4.0
        interactions[(left, right)] = coefficient / 4.0
    return constant, tuple(linear), interactions


def _ising_energy(
    constant: float,
    linear: Sequence[float],
    interactions: Mapping[tuple[int, int], float],
    spins: Sequence[int],
) -> float:
    if len(spins) != len(linear) or any(value not in (-1, 1) for value in spins):
        raise ValueError("spin assignment must contain one -1/+1 value per variable")
    return (
        constant
        + math.fsum(linear[index] * value for index, value in enumerate(spins))
        + math.fsum(
            coefficient * spins[left] * spins[right]
            for (left, right), coefficient in interactions.items()
        )
    )


def _independent_math_47(inputs: Mapping[str, object]) -> dict[str, object]:
    diagonal, upper, qubo_constant, _canonical = _canonical_qubo_from_current_inputs(inputs)
    selected = _binary_assignment(inputs.get("binary_assignment"), len(diagonal))
    offset, linear, interactions = _ising_from_qubo(diagonal, upper, qubo_constant)
    parity_rows: list[dict[str, object]] = []
    for assignment in product((0, 1), repeat=len(diagonal)):
        spins = tuple(1 - 2 * value for value in assignment)
        qubo_energy = _qubo_energy(diagonal, upper, qubo_constant, assignment)
        ising_energy = _ising_energy(offset, linear, interactions, spins)
        if not math.isclose(qubo_energy, ising_energy, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("QUBO/Ising assignment-energy parity failed")
        parity_rows.append(
            {
                "binary_assignment": list(assignment),
                "ising_energy": ising_energy,
                "qubo_energy": qubo_energy,
                "spin_assignment": list(spins),
            }
        )
    selected_spins = tuple(1 - 2 * value for value in selected)
    return {
        "binary_assignment": list(selected),
        "binary_to_spin_convention": (
            "x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1"
        ),
        "couplers_J": [
            {"i": left, "j": right, "value": coefficient}
            for (left, right), coefficient in sorted(interactions.items())
        ],
        "exhaustive_parity_rows": parity_rows,
        "ising_energy": _ising_energy(offset, linear, interactions, selected_spins),
        "linear_fields_h": list(linear),
        "offset": offset,
        "qubo_energy": _qubo_energy(diagonal, upper, qubo_constant, selected),
        "spin_assignment": list(selected_spins),
    }


def _cqm_expression(
    constant: float,
    linear: Mapping[str, float],
    quadratic: Sequence[tuple[str, str, float]],
    assignment: Mapping[str, float],
) -> float:
    return constant + math.fsum(
        coefficient * assignment[name] for name, coefficient in linear.items()
    ) + math.fsum(
        coefficient * assignment[left] * assignment[right]
        for left, right, coefficient in quadratic
    )


def _parse_cqm_model(
    value: object,
) -> tuple[
    tuple[str, ...],
    tuple[tuple[float, ...], ...],
    tuple[str, ...],
    str,
    float,
    dict[str, float],
    list[tuple[str, str, float]],
    list[dict[str, object]],
    float,
    float,
]:
    if not isinstance(value, Mapping) or set(value) != {
        "constraints",
        "conversion_penalty_candidate",
        "feasibility_tolerance",
        "objective_constant",
        "objective_linear",
        "objective_quadratic",
        "objective_sense",
        "schema_version",
        "variables",
    }:
        raise ValueError("CQM model must match QTT_CQM_GRAMMAR_V1 exactly")
    if value.get("schema_version") != "QTT_CQM_GRAMMAR_V1":
        raise ValueError("unsupported CQM schema version")
    raw_variables = _sequence(value.get("variables"), "CQM variables")
    names: list[str] = []
    domains: list[tuple[float, ...]] = []
    units: list[str] = []
    for index, raw in enumerate(raw_variables):
        if not isinstance(raw, Mapping) or set(raw) != {
            "enumeration_values", "id", "lower", "type", "unit", "upper"
        }:
            raise ValueError("CQM variable must match the typed grammar")
        name = raw.get("id")
        variable_type = raw.get("type")
        unit = raw.get("unit")
        if (
            not isinstance(name, str)
            or not name
            or name in names
            or variable_type not in {"BINARY", "INTEGER"}
            or not isinstance(unit, str)
            or not unit
        ):
            raise ValueError("CQM variable identity/domain/unit is invalid")
        lower = _finite(raw.get("lower"), f"variables[{index}].lower")
        upper = _finite(raw.get("upper"), f"variables[{index}].upper")
        raw_values = _sequence(
            raw.get("enumeration_values"),
            f"variables[{index}].enumeration_values",
        )
        values = tuple(
            _finite(item, f"variables[{index}].enumeration_values")
            for item in raw_values
        )
        if (
            lower > upper
            or len(values) != len(set(values))
            or tuple(sorted(values)) != values
            or any(not lower <= item <= upper for item in values)
            or variable_type == "BINARY" and values != (0.0, 1.0)
            or variable_type == "INTEGER" and any(not item.is_integer() for item in values)
        ):
            raise ValueError("CQM enumeration values violate the declared domain")
        names.append(name)
        domains.append(values)
        units.append(unit)
    if math.prod(len(domain) for domain in domains) > 4096:
        raise ValueError("CQM exact enumeration resource ceiling exceeded")
    known = set(names)

    def linear_terms(raw: object, label: str) -> dict[str, float]:
        if not isinstance(raw, Mapping) or any(key not in known for key in raw):
            raise ValueError(f"{label} contains an unknown variable")
        return {str(key): _finite(item, f"{label}.{key}") for key, item in raw.items()}

    def quadratic_terms(raw: object, label: str) -> list[tuple[str, str, float]]:
        rows: list[tuple[str, str, float]] = []
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(_sequence(raw, label, minimum=0)):
            if not isinstance(item, Mapping) or set(item) != {"coefficient", "u", "v"}:
                raise ValueError(f"{label} term is malformed")
            left, right = item.get("u"), item.get("v")
            if not isinstance(left, str) or not isinstance(right, str) or left not in known or right not in known:
                raise ValueError(f"{label} contains an unknown variable")
            key = (left, right) if names.index(left) <= names.index(right) else (right, left)
            if key in seen:
                raise ValueError(f"{label} contains duplicate quadratic terms")
            seen.add(key)
            rows.append((left, right, _finite(item.get("coefficient"), f"{label}[{index}]")))
        return rows

    sense = value.get("objective_sense")
    if sense not in {"MINIMIZE", "MAXIMIZE"}:
        raise ValueError("CQM objective sense must be MINIMIZE or MAXIMIZE")
    objective_constant = _finite(value.get("objective_constant"), "objective_constant")
    objective_linear = linear_terms(value.get("objective_linear"), "objective_linear")
    objective_quadratic = quadratic_terms(value.get("objective_quadratic"), "objective_quadratic")
    constraints: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(_sequence(value.get("constraints"), "constraints", minimum=0)):
        if not isinstance(raw, Mapping) or set(raw) != {
            "constant", "hard", "id", "linear", "quadratic", "rhs", "sense", "soft_penalty_weight"
        }:
            raise ValueError("CQM constraint must match the typed grammar")
        identifier = raw.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise ValueError("CQM constraint IDs must be unique")
        identifiers.add(identifier)
        constraint_sense = raw.get("sense")
        if constraint_sense not in {"LE", "GE", "EQ"}:
            raise ValueError("CQM constraint sense must be LE, GE, or EQ")
        hard = raw.get("hard")
        if not isinstance(hard, bool):
            raise ValueError("CQM constraint hard flag must be Boolean")
        penalty = _finite(raw.get("soft_penalty_weight"), "soft_penalty_weight")
        if penalty < 0.0 or hard and penalty != 0.0 or not hard and penalty <= 0.0:
            raise ValueError("CQM soft penalty weight conflicts with hard/soft state")
        constraints.append(
            {
                "id": identifier,
                "hard": hard,
                "constant": _finite(raw.get("constant"), f"constraints[{index}].constant"),
                "linear": linear_terms(raw.get("linear"), f"constraints[{index}].linear"),
                "quadratic": quadratic_terms(raw.get("quadratic"), f"constraints[{index}].quadratic"),
                "sense": constraint_sense,
                "rhs": _finite(raw.get("rhs"), f"constraints[{index}].rhs"),
                "penalty": penalty,
            }
        )
    tolerance = _finite(value.get("feasibility_tolerance"), "feasibility_tolerance")
    penalty_candidate = _finite(value.get("conversion_penalty_candidate"), "conversion_penalty_candidate")
    if tolerance < 0.0 or penalty_candidate <= 0.0:
        raise ValueError("CQM tolerance and conversion penalty must be positive")
    return (
        tuple(names), tuple(domains), tuple(units), str(sense), objective_constant,
        objective_linear, objective_quadratic, constraints, tolerance, penalty_candidate,
    )


def _constraint_violation(lhs: float, sense: str, rhs: float) -> float:
    if sense == "LE":
        return max(0.0, lhs - rhs)
    if sense == "GE":
        return max(0.0, rhs - lhs)
    return abs(lhs - rhs)


def _independent_math_48(inputs: Mapping[str, object]) -> dict[str, object]:
    (
        names, domains, _units, sense, objective_constant, objective_linear,
        objective_quadratic, constraints, tolerance, conversion_penalty,
    ) = _parse_cqm_model(inputs.get("model"))
    raw_assignment = inputs.get("assignment")
    if not isinstance(raw_assignment, Mapping) or tuple(raw_assignment) != names:
        raise ValueError("assignment must provide every variable exactly once")

    def parsed_assignment(values: Sequence[float] | Mapping[str, object]) -> dict[str, float]:
        if isinstance(values, Mapping):
            result = {name: _finite(values[name], f"assignment.{name}") for name in names}
        else:
            result = {name: float(item) for name, item in zip(names, values, strict=True)}
        if any(result[name] not in domains[index] for index, name in enumerate(names)):
            raise ValueError("assignment value violates the declared variable domain")
        return result

    selected = parsed_assignment(raw_assignment)

    def evaluate(assignment: Mapping[str, float]) -> dict[str, object]:
        raw_objective = _cqm_expression(
            objective_constant, objective_linear, objective_quadratic, assignment
        )
        constraint_rows: list[dict[str, object]] = []
        hard_feasible = True
        soft_penalty = 0.0
        hard_penalty = 0.0
        for row in constraints:
            lhs = _cqm_expression(
                float(row["constant"]),
                row["linear"],  # type: ignore[arg-type]
                row["quadratic"],  # type: ignore[arg-type]
                assignment,
            )
            violation = _constraint_violation(lhs, str(row["sense"]), float(row["rhs"]))
            hard = bool(row["hard"])
            hard_feasible = hard_feasible and (not hard or violation <= tolerance)
            if hard:
                hard_penalty += conversion_penalty * violation * violation
            else:
                soft_penalty += float(row["penalty"]) * violation * violation
            constraint_rows.append(
                {
                    "hard": hard,
                    "id": row["id"],
                    "lhs": lhs,
                    "rhs": float(row["rhs"]),
                    "sense": row["sense"],
                    "soft_penalty_weight": float(row["penalty"]),
                    "violation": violation,
                }
            )
        penalized = raw_objective + soft_penalty if sense == "MINIMIZE" else raw_objective - soft_penalty
        converted = penalized + hard_penalty if sense == "MINIMIZE" else penalized - hard_penalty
        return {
            "assignment": dict(assignment),
            "raw": raw_objective,
            "constraints": constraint_rows,
            "feasible": hard_feasible,
            "soft_penalty": soft_penalty,
            "penalized": penalized,
            "converted": converted,
        }

    ledger = [evaluate(parsed_assignment(values)) for values in product(*domains)]
    feasible = [row for row in ledger if row["feasible"] is True]
    if not feasible:
        raise ValueError("CQM exact fixture has no native feasible assignment")

    def objective_key(row: Mapping[str, object], field: str) -> tuple[object, ...]:
        value = float(row[field])
        assignment = row["assignment"]
        assert isinstance(assignment, Mapping)
        ordered = tuple(float(assignment[name]) for name in names)
        return ((value if sense == "MINIMIZE" else -value), ordered)

    native = min(feasible, key=lambda row: objective_key(row, "penalized"))
    converted = min(ledger, key=lambda row: objective_key(row, "converted"))
    if converted["assignment"] != native["assignment"] or converted["feasible"] is not True:
        raise ValueError("conversion penalty is inadequate for the exact CQM fixture")
    selected_result = evaluate(selected)
    native_assignment = native["assignment"]
    converted_assignment = converted["assignment"]
    assert isinstance(native_assignment, Mapping) and isinstance(converted_assignment, Mapping)
    return {
        "assignment": dict(selected),
        "constraint_evaluations": selected_result["constraints"],
        "conversion_penalty_adequacy": {
            "converted_best_assignment": dict(converted_assignment),
            "matches_native_feasible_optimum": True,
            "penalty": conversion_penalty,
            "state": "ADEQUATE_FOR_EXACT_ENUMERATED_FIXTURE",
        },
        "interpret_back_state": "EXACT_ORIGINAL_VARIABLE_LABELS_AND_UNITS_PRESERVED",
        "objective_sense": sense,
        "original_model_feasible": selected_result["feasible"],
        "penalized_objective": selected_result["penalized"],
        "raw_objective": selected_result["raw"],
        "schema_version": "QTT_CQM_GRAMMAR_V1",
        "small_exact_solution": {
            "assignment": dict(native_assignment),
            "enumerated_assignment_count": len(ledger),
            "feasible_assignment_count": len(feasible),
            "penalized_objective": native["penalized"],
            "raw_objective": native["raw"],
            "state": "EXACT_FEASIBLE_OPTIMUM",
        },
        "soft_penalty": selected_result["soft_penalty"],
    }


def _independent_math_49(inputs: Mapping[str, object]) -> dict[str, object]:
    model = inputs.get("model")
    if not isinstance(model, Mapping) or set(model) != {
        "constant", "linear_biases", "pairwise_biases", "schema_version", "variables"
    }:
        raise ValueError("DQM model must match QTT_DQM_GRAMMAR_V1 exactly")
    if model.get("schema_version") != "QTT_DQM_GRAMMAR_V1":
        raise ValueError("unsupported DQM schema version")
    raw_variables = _sequence(model.get("variables"), "DQM variables")
    variable_names: list[str] = []
    case_sets: list[tuple[str, ...]] = []
    for raw in raw_variables:
        if not isinstance(raw, Mapping) or set(raw) != {"cases", "id"}:
            raise ValueError("DQM variable row is malformed")
        name = raw.get("id")
        cases = raw.get("cases")
        if (
            not isinstance(name, str)
            or not name
            or name in variable_names
            or
            isinstance(cases, str | bytes)
            or not isinstance(cases, Sequence)
            or not cases
            or len(set(cases)) != len(cases)
            or any(not isinstance(case, str) or not case for case in cases)
        ):
            raise ValueError("each DQM variable needs unique nonempty cases")
        variable_names.append(name)
        case_sets.append(tuple(cases))
    if math.prod(len(cases) for cases in case_sets) > 4096:
        raise ValueError("DQM exact enumeration resource ceiling exceeded")
    known_cases = {
        (name, case)
        for name, cases in zip(variable_names, case_sets, strict=True)
        for case in cases
    }
    linear: dict[tuple[str, str], float] = {}
    for index, raw in enumerate(_sequence(model.get("linear_biases"), "linear_biases")):
        if not isinstance(raw, Mapping) or set(raw) != {"bias", "case", "variable"}:
            raise ValueError("DQM linear bias row is malformed")
        key = (raw.get("variable"), raw.get("case"))
        if key not in known_cases or key in linear:
            raise ValueError("DQM linear biases must cover each variable/case exactly once")
        linear[key] = _finite(raw.get("bias"), f"linear_biases[{index}].bias")
    if set(linear) != known_cases:
        raise ValueError("DQM linear biases must cover each variable/case exactly once")
    pairwise: dict[tuple[str, str, str, str], float] = {}
    for index, raw in enumerate(_sequence(model.get("pairwise_biases"), "pairwise_biases", minimum=0)):
        if not isinstance(raw, Mapping) or set(raw) != {"bias", "case_u", "case_v", "u", "v"}:
            raise ValueError("DQM pairwise bias row is malformed")
        left, right = raw.get("u"), raw.get("v")
        left_case, right_case = raw.get("case_u"), raw.get("case_v")
        if (
            not isinstance(left, str) or not isinstance(right, str) or left == right
            or (left, left_case) not in known_cases or (right, right_case) not in known_cases
        ):
            raise ValueError("DQM pairwise bias references an unknown variable or case")
        if variable_names.index(left) > variable_names.index(right):
            left, right, left_case, right_case = right, left, right_case, left_case
        key = (left, str(left_case), right, str(right_case))
        if key in pairwise:
            raise ValueError("DQM pairwise bias is duplicate or conflicting")
        pairwise[key] = _finite(raw.get("bias"), f"pairwise_biases[{index}].bias")
    constant = _finite(model.get("constant"), "DQM constant")

    def energy(assignment: Mapping[str, str]) -> float:
        return constant + math.fsum(
            linear[(name, assignment[name])] for name in variable_names
        ) + math.fsum(
            coefficient
            for (left, left_case, right, right_case), coefficient in pairwise.items()
            if assignment[left] == left_case and assignment[right] == right_case
        )

    raw_assignment = inputs.get("assignment")
    if not isinstance(raw_assignment, Mapping) or tuple(raw_assignment) != tuple(variable_names):
        raise ValueError("assignment must select one known case per variable")
    selected = {name: raw_assignment[name] for name in variable_names}
    if any((name, selected[name]) not in known_cases for name in variable_names):
        raise ValueError("assignment must select one known case per variable")
    ledger: list[dict[str, object]] = []
    for assignment in product(*case_sets):
        mapped = {
            name: case for name, case in zip(variable_names, assignment, strict=True)
        }
        ledger.append({"assignment": mapped, "energy": energy(mapped)})
    optimum = _ordered_dqm_optimum(ledger, variable_names)
    if optimum != _ordered_dqm_optimum(tuple(reversed(ledger)), variable_names):
        raise ValueError("DQM deterministic tie-break drift observed")
    return {
        "assignment": selected,
        "energy": energy(selected),
        "exhaustive_assignments": ledger,
        "interpret_back_state": "EXACT_ORDERED_VARIABLE_AND_CASE_LABELS_PRESERVED",
        "one_hot_expansion_applied": False,
        "schema_version": "QTT_DQM_GRAMMAR_V1",
    }


def _ordered_dqm_optimum(
    ledger: Sequence[Mapping[str, object]],
    variable_names: Sequence[str],
) -> dict[str, object]:
    if not ledger:
        raise ValueError("DQM optimum requires a nonempty assignment ledger")
    selected = min(
        ledger,
        key=lambda row: (
            float(row["energy"]),
            tuple(
                str(row["assignment"][name])  # type: ignore[index]
                for name in variable_names
            ),
        ),
    )
    return _json_ready(selected)  # type: ignore[return-value]


_NEW_ARCHITECTURE_ALGORITHMS = {
    "MATH-16": _independent_math_16,
    "MATH-17": _independent_math_17,
    "MATH-18": _independent_math_18,
    "MATH-19": _independent_math_19,
    "MATH-20": _independent_math_20,
    "MATH-21": _independent_math_21,
    "MATH-22": _independent_math_22,
    "MATH-23": _independent_math_23,
    "MATH-24": _independent_math_24,
    "MATH-25": _independent_math_25,
    "MATH-46": _independent_math_46,
    "MATH-47": _independent_math_47,
    "MATH-48": _independent_math_48,
    "MATH-49": _independent_math_49,
}


def _declared_input_keys(material: Mapping[str, object]) -> tuple[str, ...]:
    oracle = material["oracle"]
    golden = material["golden"]
    if not isinstance(oracle, Mapping) or not isinstance(golden, Mapping):
        raise ValueError("tracked oracle/vector material must be mappings")
    raw = oracle.get("input_keys")
    if raw is None:
        inputs = golden.get("inputs")
        if not isinstance(inputs, Mapping):
            raise ValueError("legacy golden inputs must be a mapping")
        return tuple(str(key) for key in inputs)
    if not isinstance(raw, list) or any(not isinstance(key, str) for key in raw):
        raise ValueError("tracked oracle input keys must be exact strings")
    return tuple(raw)


def _legacy_stationary_bootstrap_means(
    inputs: Mapping[str, object],
) -> tuple[float, ...]:
    series = tuple(
        _finite(value, "stationary bootstrap series value")
        for value in _sequence(inputs.get("series"), "series", minimum=2)
    )
    seed = _positive_int(inputs.get("seed"), "seed", minimum=0)
    replicates = _positive_int(inputs.get("replicates"), "replicates")
    expected_block_length = _finite(
        inputs.get("expected_block_length"),
        "expected_block_length",
    )
    if expected_block_length < 1.0:
        raise ValueError("expected block length must be >= 1")
    restart_probability = 1.0 / expected_block_length
    rng = Random(seed)
    results: list[float] = []
    for _ in range(replicates):
        current = rng.randrange(len(series))
        sample = [series[current]]
        for _position in range(1, len(series)):
            if rng.random() < restart_probability:
                current = rng.randrange(len(series))
            else:
                current = (current + 1) % len(series)
            sample.append(series[current])
        results.append(math.fsum(sample) / len(sample))
    return tuple(results)


def _canonical_decimal_text(value: Decimal) -> str:
    return format(value.normalize(DECIMAL_CONTEXT), "f")


def _execute_legacy_architecture_row(
    math_id: str,
    inputs: object,
    material: Mapping[str, object],
) -> dict[str, object]:
    """Execute the tracked MATH-01..15 vector with independent local arithmetic."""

    if not isinstance(inputs, Mapping):
        raise ValueError("legacy architecture row inputs must be a mapping")
    declared = _declared_input_keys(material)
    if len(inputs) != len(declared) or set(inputs) != set(declared):
        raise ValueError("legacy architecture input binding differs from tracked vector")

    with localcontext(DECIMAL_CONTEXT):
        if math_id == "MATH-01":
            price = Decimal(str(inputs["contract_price"]))
            payout = Decimal(str(inputs["payout_per_winning_contract"]))
            if payout <= 0 or price < 0 or price > payout:
                raise ValueError("invalid binary contract")
            return {"p_market": _canonical_decimal_text(price / payout)}
        if math_id == "MATH-02":
            model = _probability_decimal(inputs["calibrated_model_probability"])
            market = _probability_decimal(inputs["market_implied_probability"])
            return {"edge_probability": _canonical_decimal_text(model - market)}
        if math_id in {"MATH-03", "MATH-04", "MATH-05"}:
            bid = Decimal(str(inputs["best_bid"]))
            ask = Decimal(str(inputs["best_ask"]))
            if bid < 0 or ask < bid:
                raise ValueError("crossed book")
            midpoint = (bid + ask) / Decimal(2)
            spread = ask - bid
            if math_id == "MATH-03":
                return {"mid": _canonical_decimal_text(midpoint)}
            if math_id == "MATH-04":
                return {"spread": _canonical_decimal_text(spread)}
            if midpoint <= 0:
                raise ValueError("zero midpoint")
            return {"relative_spread": _canonical_decimal_text(spread / midpoint)}
        if math_id == "MATH-06":
            result = _binary_net(
                inputs["quantity"],
                inputs["p"],
                inputs["win_cash"],
                inputs["lose_cash"],
                inputs["fees"],
                inputs["acquisition_cost"],
                inputs["expected_slippage"],
                inputs["expected_impact"],
            )
            return {"expected_net_cash": _canonical_decimal_text(result)}
        if math_id == "MATH-07":
            probabilities = tuple(
                _sequence(inputs["probabilities"], "probabilities")
            )
            payoffs = tuple(_sequence(inputs["payoffs"], "payoffs"))
            result = _multi_net(
                probabilities,
                payoffs,
                inputs["quantity"],
                inputs["acquisition_cost"],
                inputs["fees"],
                inputs["expected_slippage"],
                inputs["expected_impact"],
            )
            return {"expected_net_cash": _canonical_decimal_text(result)}
        if math_id == "MATH-08":
            probability = _probability_decimal(inputs["p"])
            outcome = inputs["y"]
            if isinstance(outcome, bool) or outcome not in (0, 1):
                raise ValueError("unresolved outcome")
            return {
                "brier_score": _canonical_decimal_text(
                    (probability - Decimal(outcome)) ** 2
                )
            }

    if math_id == "MATH-09":
        return {
            "log_loss": _log_loss(
                inputs["p"],
                inputs["y"],  # type: ignore[arg-type]
                _finite(inputs["clip_epsilon"], "clip_epsilon"),
            )
        }
    if math_id == "MATH-10":
        raw_bins = _sequence(inputs["bins"], "bins")
        parsed: list[tuple[int, float, float]] = []
        for raw in raw_bins:
            if not isinstance(raw, Mapping) or set(raw) != {
                "count",
                "empirical_frequency",
                "mean_confidence",
            }:
                raise ValueError("invalid calibration bin")
            count = _positive_int(raw["count"], "bin count")
            frequency = float(_probability_decimal(raw["empirical_frequency"]))
            confidence = float(_probability_decimal(raw["mean_confidence"]))
            parsed.append((count, frequency, confidence))
        total = sum(count for count, _frequency, _confidence in parsed)
        return {
            "ece": math.fsum(
                count / total * abs(confidence - frequency)
                for count, frequency, confidence in parsed
            )
        }
    if math_id == "MATH-11":
        successes = _positive_int(inputs["successes"], "successes", minimum=0)
        trials = _positive_int(inputs["trials"], "trials")
        confidence = _finite(inputs["confidence"], "confidence")
        lower, upper = _wilson(successes, trials, confidence)
        return {"lower": lower, "upper": upper}
    if math_id in {"MATH-12", "MATH-13"}:
        p_values = tuple(
            _finite(value, "p value")
            for value in _sequence(inputs["p_values"], "p_values")
        )
        q = _finite(inputs["q"], "q")
        correction = (
            1.0
            if math_id == "MATH-12"
            else math.fsum(1.0 / rank for rank in range(1, len(p_values) + 1))
        )
        rejected = _bh(p_values, q, correction)
        return {
            "largest_rank": len(rejected),
            "rejected_original_indices": list(rejected),
        }
    if math_id == "MATH-14":
        first = _legacy_stationary_bootstrap_means(inputs)
        second = _legacy_stationary_bootstrap_means(inputs)
        series = tuple(
            _finite(value, "series value")
            for value in _sequence(inputs["series"], "series", minimum=2)
        )
        ordered = sorted(first)
        sample_mean = math.fsum(series) / len(series)
        return {
            "interval_contains_sample_mean": ordered[1] <= sample_mean <= ordered[-2],
            "same_seed_reproducible": first == second,
        }
    if math_id == "MATH-15":
        raw_rows = _sequence(
            inputs["loss_differentials"],
            "loss_differentials",
            minimum=2,
        )
        rows = tuple(
            tuple(
                _finite(value, "loss differential")
                for value in _sequence(raw, "loss differential row")
            )
            for raw in raw_rows
        )
        if len({len(row) for row in rows}) != 1:
            raise ValueError("loss differential dimensions differ")
        seed = _positive_int(inputs["seed"], "seed", minimum=0)
        replicates = _positive_int(inputs["replicates"], "replicates")
        p_value = _white_reality_p_value(
            rows,
            benchmark_minus_candidate=True,
            seed=seed,
            replicates=replicates,
        )
        return {"p_value": p_value, "reject": p_value < 0.05}
    raise ValueError(f"no legacy architecture algorithm: {math_id}")


def _legacy_formula_regression_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    observed: object,
) -> dict[str, object]:
    golden = material["golden"]
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        raise _EvidenceContractMismatch(f"{math_id} legacy golden inputs are absent")
    inputs = golden["inputs"]
    if math_id == "MATH-14":
        path: tuple[object, ...] = ("seed",)
        replacement: object = int(inputs["seed"]) + 1
    elif math_id == "MATH-15":
        rows = _sequence(inputs["loss_differentials"], "loss differentials")
        path = ("loss_differentials",)
        replacement = [
            [-_finite(value, "loss differential") for value in _sequence(row, "row")]
            for row in rows
        ]
    else:
        mutations: dict[str, tuple[tuple[object, ...], object]] = {
            "MATH-01": (("contract_price",), "0.43"),
            "MATH-02": (("calibrated_model_probability",), "0.59"),
            "MATH-03": (("best_ask",), "0.45"),
            "MATH-04": (("best_ask",), "0.45"),
            "MATH-05": (("best_ask",), "0.45"),
            "MATH-06": (("p",), "0.70"),
            "MATH-07": (("payoffs", 0), "1.1"),
            "MATH-08": (("p",), "0.60"),
            "MATH-09": (("p",), 0.6),
            "MATH-10": (("bins", 0, "mean_confidence"), 0.7),
            "MATH-11": (("successes",), 7),
            "MATH-12": (("p_values", 0), 0.1),
            "MATH-13": (("p_values", 0), 0.1),
        }
        path, replacement = mutations[math_id]
    mutated = _mutated_copy(inputs, path, replacement)
    if math_id == "MATH-14":
        baseline_observed = _legacy_stationary_bootstrap_means(inputs)
        mutated_observed = _legacy_stationary_bootstrap_means(mutated)
    else:
        baseline_observed = observed
        mutated_observed = _execute_legacy_architecture_row(math_id, mutated, material)
    comparison = _compare_architecture_payload(
        math_id,
        baseline_observed,
        mutated_observed,
        tracked_comparison_policy=str(material["comparison_policy"]),
    )
    changed = not comparison.comparison_passed
    if not changed:
        raise _EvidenceContractMismatch(
            f"{math_id} legacy formula-regression mutation produced no change"
        )
    return {
        "baseline_observed": _json_ready(baseline_observed),
        "baseline_value": _json_ready(_value_at_path(inputs, path)),
        "comparison_policy": comparison.tracked_comparison_policy,
        "comparison_policy_execution": _json_ready(asdict(comparison)),
        "exact_consequence": {
            "comparison_matches_baseline": False,
            "state": "OBSERVED_LEGACY_FORMULA_REGRESSION_CHANGE",
        },
        "input_path": list(path),
        "mutated_observed": _json_ready(mutated_observed),
        "mutation_family": f"LEGACY_FORMULA_REGRESSION_INPUT_MUTATION::{math_id}",
        "mutation_observed": True,
        "replacement_value": _json_ready(replacement),
    }


def _legacy_domain_rejection_evidence(
    math_id: str,
    material: Mapping[str, object],
) -> dict[str, object]:
    golden = material["golden"]
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        raise _EvidenceContractMismatch(f"{math_id} legacy golden inputs are absent")
    inputs = golden["inputs"]
    mutations: dict[str, tuple[tuple[object, ...], object]] = {
        "MATH-01": (("payout_per_winning_contract",), "0"),
        "MATH-02": (("calibrated_model_probability",), "1.1"),
        "MATH-03": (("best_bid",), "0.50"),
        "MATH-04": (("best_bid",), "0.50"),
        "MATH-05": (("best_ask",), "0.00"),
        "MATH-06": (("p",), "1.1"),
        "MATH-07": (("probabilities", 0), "0.1"),
        "MATH-08": (("y",), 2),
        "MATH-09": (("clip_epsilon",), 0.6),
        "MATH-10": (("bins",), []),
        "MATH-11": (("successes",), 11),
        "MATH-12": (("q",), 0.0),
        "MATH-13": (("q",), 0.0),
        "MATH-14": (("series",), [1.0]),
        "MATH-15": (("loss_differentials",), [[0.0], [0.0], [0.0], [0.0]]),
    }
    path, replacement = mutations[math_id]
    invalid = _mutated_copy(inputs, path, replacement)
    try:
        _execute_legacy_architecture_row(math_id, invalid, material)
    except (ValueError, ArithmeticError, OverflowError) as exc:
        return {
            "baseline_value": _json_ready(_value_at_path(inputs, path)),
            "comparison_policy": "LEGACY_TYPED_DOMAIN_REJECTION",
            "exact_consequence": {
                "exception_message": str(exc),
                "exception_type": type(exc).__name__,
                "state": "OBSERVED_LEGACY_DOMAIN_REJECTION",
            },
            "input_path": list(path),
            "mutation_family": f"LEGACY_DOMAIN_GUARD_MUTATION::{math_id}",
            "mutation_observed": True,
            "replacement_value": _json_ready(replacement),
        }
    raise _EvidenceContractMismatch(
        f"{math_id} legacy domain mutation was accepted"
    )


def _execute_new_architecture_row(
    math_id: str,
    inputs: object,
    material: Mapping[str, object],
) -> dict[str, object] | dict[str, float]:
    if not isinstance(inputs, Mapping):
        raise ValueError("architecture row inputs must be a mapping")
    declared = _declared_input_keys(material)
    if len(inputs) != len(declared) or set(inputs) != set(declared):
        raise ValueError("architecture row input binding differs from tracked vector")
    algorithm = _NEW_ARCHITECTURE_ALGORITHMS.get(math_id)
    if algorithm is None:
        raise ValueError(f"missing architecture algorithm: {math_id}")
    return algorithm(inputs)


def _expect_rejection(operation) -> bool:
    try:
        operation()
    except (ValueError, ArithmeticError, OverflowError):
        return True
    return False


def _exact_value_error_message(operation: Callable[[], object]) -> str:
    try:
        operation()
    except ValueError as exc:
        return str(exc)
    raise _EvidenceContractMismatch("invalid operation was accepted")


class _EvidenceContractMismatch(ValueError):
    pass


def _execute_observed_mutation(
    math_id: str,
    material: Mapping[str, object],
    baseline_inputs: Mapping[str, object],
    mutated_inputs: object,
    policy: _CompiledComparisonPolicyV1,
    *,
    input_path: Sequence[object],
    baseline_value: object,
    replacement_value: object,
    mutation_family: str,
) -> dict[str, object]:
    baseline = _execute_new_architecture_row(math_id, baseline_inputs, material)
    try:
        mutated = _execute_new_architecture_row(math_id, mutated_inputs, material)
    except ValueError as exc:
        return {
            "baseline_observed": _json_ready(baseline),
            "baseline_value": _json_ready(baseline_value),
            "comparison_policy": policy.operational_policy,
            "exact_consequence": {
                "exception_message": str(exc),
                "exception_type": type(exc).__name__,
                "state": "TYPED_REJECTION",
            },
            "input_path": list(input_path),
            "mutation_family": mutation_family,
            "mutation_outcome": "TYPED_REJECTION",
            "mutation_exception_type": type(exc).__name__,
            "mutation_exception_message": str(exc),
            "mutation_observed": True,
            "replacement_value": _json_ready(replacement_value),
        }
    comparison = _compare_architecture_payload(
        math_id,
        baseline,
        mutated,
        tracked_comparison_policy=str(material["comparison_policy"]),
    )
    changed = not comparison.comparison_passed
    if not changed:
        raise _EvidenceContractMismatch(
            f"{math_id} {mutation_family} produced no observed result change"
        )
    return {
        "baseline_observed": _json_ready(baseline),
        "baseline_value": _json_ready(baseline_value),
        "comparison_policy": policy.operational_policy,
        "comparison_policy_execution": _json_ready(asdict(comparison)),
        "exact_consequence": {
            "comparison_matches_baseline": False,
            "state": "OBSERVED_OUTPUT_CHANGE",
        },
        "input_path": list(input_path),
        "mutated_observed": _json_ready(mutated),
        "mutation_family": mutation_family,
        "mutation_outcome": "OBSERVED_OUTPUT_CHANGE",
        "mutation_observed": True,
        "replacement_value": _json_ready(replacement_value),
    }


def _observe_exact_negative_operation(
    operation: Callable[[], object],
    *,
    math_id: str,
    vector_id: object,
    expected_name: object,
    expected_message: object,
) -> dict[str, object]:
    if expected_name != "ValueError" or not isinstance(expected_message, str) or not expected_message:
        raise _EvidenceContractMismatch(
            f"{math_id} NEGATIVE exception contract is not exact"
        )
    try:
        operation()
    except ValueError as exc:
        if expected_message not in str(exc):
            raise _EvidenceContractMismatch(
                f"{math_id} NEGATIVE reason mismatch: expected {expected_message!r}; "
                f"observed {str(exc)!r}"
            ) from exc
        return {
            "attempted_execution": True,
            "exception_type": type(exc).__name__,
            "failure_family": f"{math_id}::TRACKED_NEGATIVE_CONTRACT",
            "message": str(exc),
            "message_substring_matched": True,
            "vector_id": vector_id,
        }
    raise _EvidenceContractMismatch(f"{math_id} NEGATIVE vector was accepted")


def _exact_negative_evidence(
    math_id: str,
    material: Mapping[str, object],
) -> dict[str, object]:
    negative = material.get("negative")
    if not isinstance(negative, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} NEGATIVE vector is absent")
    return _observe_exact_negative_operation(
        lambda: _execute_new_architecture_row(
            math_id,
            negative.get("inputs"),
            material,
        ),
        math_id=math_id,
        vector_id=negative.get("vector_id"),
        expected_name=negative.get("expected_exception"),
        expected_message=negative.get("expected_message_contains"),
    )


def _property_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    property_row = material.get("property")
    if not isinstance(property_row, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} property row is absent")
    baseline = property_row.get("base_inputs")
    mutation = property_row.get("mutation")
    if not isinstance(baseline, Mapping) or not isinstance(mutation, Mapping):
        raise _EvidenceContractMismatch(f"{math_id} property row is malformed")
    mutated = _apply_declared_mutation(baseline, mutation)
    path = mutation.get("path")
    assert isinstance(path, list)
    replacement = mutation.get("replacement")
    evidence = _execute_observed_mutation(
        math_id,
        material,
        baseline,
        mutated,
        policy,
        input_path=path,
        baseline_value=_value_at_path(baseline, path),
        replacement_value=replacement,
        mutation_family="TRACKED_PROPERTY_FORMULA_OR_PROCEDURE_MUTATION",
    )
    evidence.update(
        {
            "property_id": property_row.get("property_id"),
            "required_outcome": property_row.get("required_outcome"),
            "test_id": property_row.get("test_id"),
        }
    )
    return evidence


_ACTUAL_EXECUTION_MUTATIONS: dict[
    str,
    tuple[tuple[object, ...], object, str],
] = {
    "MATH-16": (("expected_block_length",), 2.25, "EXPECTED_BLOCK_LENGTH_EXECUTION_SENSITIVITY"),
    "MATH-17": (("estimated_sharpe",), 0.500001, "ESTIMATED_SHARPE_INPUT_SENSITIVITY"),
    "MATH-18": (("candidate_estimated_sharpe",), 0.500001, "CANDIDATE_SHARPE_OUTPUT_SENSITIVITY"),
    "MATH-19": (("performance_matrix", 0, 0), 2.0, "PERFORMANCE_INPUT_RANKING_SENSITIVITY"),
    "MATH-20": (("embargo_duration",), 2.0, "EMBARGO_DURATION_SENSITIVITY_UNDER_HALF_OPEN_INTERVALS"),
    "MATH-21": (("embargo_duration",), 1.5, "EMBARGO_MUTATION_WITH_EXACT_SPLIT_AND_PATH_OUTPUT_COMPARISON"),
    "MATH-22": (("logged_rows", 0, "reward"), 0.999999, "LOGGED_REWARD_DOUBLY_ROBUST_OUTPUT_SENSITIVITY"),
    "MATH-23": (("logged_rows", 0, "reward"), 0.5, "REWARD_AND_IMPORTANCE_WEIGHT_OUTPUT_SENSITIVITY"),
    "MATH-24": (("weights", 0), 1.600001, "IMPORTANCE_WEIGHT_NORMALIZATION_OUTPUT_SENSITIVITY"),
    "MATH-25": (("tau_grid", 1), 1.000001, "TAU_INEQUALITY_SELECTION_SENSITIVITY"),
    "MATH-46": (("diagonal", 0), 1.000001, "QUBO_DIAGONAL_COEFFICIENT_ENERGY_SENSITIVITY"),
    "MATH-47": (("diagonal", 0), 1.000001, "QUBO_COEFFICIENT_PARITY_PRESERVATION_SENSITIVITY"),
    "MATH-48": (("model", "conversion_penalty_candidate"), 1.0, "CONVERSION_PENALTY_ADEQUACY_MUTATION"),
    "MATH-49": (("model", "pairwise_biases", 0, "bias"), -1.999999, "PAIRWISE_BIAS_AND_ASSIGNMENT_ENERGY_SENSITIVITY"),
}


def _actual_execution_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    golden = material.get("golden")
    boundary = material.get("boundary")
    if (
        not isinstance(golden, Mapping)
        or not isinstance(golden.get("inputs"), Mapping)
        or not isinstance(boundary, Mapping)
    ):
        raise _EvidenceContractMismatch(f"{math_id} precision/boundary material is absent")
    path, replacement, label = _ACTUAL_EXECUTION_MUTATIONS[math_id]
    mutated = _mutated_copy(golden["inputs"], path, replacement)
    evidence = _execute_observed_mutation(
        math_id,
        material,
        golden["inputs"],
        mutated,
        policy,
        input_path=path,
        baseline_value=_value_at_path(golden["inputs"], path),
        replacement_value=replacement,
        mutation_family=label,
    )
    boundary_observed = _execute_new_architecture_row(
        math_id,
        boundary.get("inputs"),
        material,
    )
    boundary_comparison = _compare_architecture_payload(
        math_id,
        boundary_observed,
        boundary.get("expected"),
        tracked_comparison_policy=str(material["comparison_policy"]),
    )
    if not boundary_comparison.comparison_passed:
        raise _EvidenceContractMismatch(f"{math_id} BOUNDARY vector comparison failed")
    evidence.update(
        {
            "boundary_observed": _json_ready(boundary_observed),
            "boundary_comparison": _json_ready(asdict(boundary_comparison)),
            "boundary_vector_id": boundary.get("vector_id"),
            "expected_output_mutated": False,
        }
    )
    return evidence


_BINDING_MUTATIONS: dict[str, tuple[tuple[object, ...], object, str]] = {
    "MATH-16": (("sign_convention",), "CANDIDATE_LOSS_MINUS_BENCHMARK_LOSS_NEGATED_TO_POSITIVE_IS_BETTER", "SIGN_CONVENTION_BINDING_MUTATION"),
    "MATH-17": (("independent_equivalent_observations",), 101, "INDEPENDENT_EQUIVALENT_OBSERVATION_COUNT_BINDING_MUTATION"),
    "MATH-18": (("effective_independent_trial_count",), 4.0, "EFFECTIVE_INDEPENDENT_TRIAL_COUNT_BINDING_MUTATION"),
    "MATH-19": (("strategy_ids",), ["S-B", "S-A", "S-C"], "STRATEGY_ID_ORDER_BINDING_MUTATION"),
    "MATH-20": (("sample_intervals", 0, "start"), -0.25, "FIRST_INTERVAL_START_TIME_BINDING_MUTATION"),
    "MATH-21": (("aggregation_rule",), "CHERRY_PICK_ONE_PATH", "AGGREGATION_RULE_BINDING_MUTATION"),
    "MATH-22": (("logged_rows", 0, "behavior_action_probabilities"), [0.0, 1.0], "BEHAVIOR_POLICY_SUPPORT_BINDING_MUTATION"),
    "MATH-23": (("logged_rows", 0, "logged_action_index"), 1, "LOGGED_ACTION_INDEX_BINDING_MUTATION"),
    "MATH-24": (("rewards",), [1.0], "REWARD_WEIGHT_CARDINALITY_BINDING_MUTATION"),
    "MATH-25": (("tau_grid",), [2.0, 1.0], "TAU_GRID_ORDER_BINDING_MUTATION"),
    "MATH-46": (("representation",), "UNKNOWN_QUBO_REPRESENTATION", "QUBO_REPRESENTATION_BINDING_MUTATION"),
    "MATH-47": (("representation",), "UNKNOWN_BINARY_TO_SPIN_MAPPING", "BINARY_TO_SPIN_MAPPING_CONVENTION_MUTATION"),
    "MATH-48": (("model", "objective_sense"), "MAXIMIZE", "OBJECTIVE_SENSE_BINDING_MUTATION"),
    "MATH-49": (("model", "schema_version"), "QTT_DQM_GRAMMAR_V0", "DQM_SCHEMA_VERSION_BINDING_MUTATION"),
}


def _semantic_binding_mutation_evidence(
    math_id: str,
    material: Mapping[str, object],
    policy: _CompiledComparisonPolicyV1,
) -> dict[str, object]:
    golden = material.get("golden")
    if not isinstance(golden, Mapping) or not isinstance(golden.get("inputs"), Mapping):
        raise _EvidenceContractMismatch(f"{math_id} binding material is absent")
    if math_id == "MATH-47":
        baseline = _execute_new_architecture_row(
            math_id,
            golden["inputs"],
            material,
        )
        diagonal, upper, constant, _canonical = _canonical_qubo_from_current_inputs(
            golden["inputs"]
        )
        offset, linear, interactions = _ising_from_qubo(diagonal, upper, constant)
        drift_rows: list[dict[str, object]] = []
        for assignment in product((0, 1), repeat=len(diagonal)):
            wrong_spins = tuple(2 * value - 1 for value in assignment)
            qubo = _qubo_energy(diagonal, upper, constant, assignment)
            wrong_ising = _ising_energy(offset, linear, interactions, wrong_spins)
            if not math.isclose(qubo, wrong_ising, rel_tol=0.0, abs_tol=1e-15):
                drift_rows.append(
                    {
                        "binary_assignment": list(assignment),
                        "drifted_spin_assignment": list(wrong_spins),
                        "ising_energy": wrong_ising,
                        "qubo_energy": qubo,
                    }
                )
        if not drift_rows:
            raise _EvidenceContractMismatch(
                "MATH-47 mapping-convention drift did not break parity"
            )
        return {
            "baseline_observed": _json_ready(baseline),
            "baseline_value": (
                "x_i=(1-s_i)/2; s=+1 maps to x=0 and s=-1 maps to x=1"
            ),
            "comparison_policy": policy.operational_policy,
            "exact_consequence": {
                "parity_failure_rows": len(drift_rows),
                "state": "OBSERVED_PARITY_REJECTION",
            },
            "input_path": ["independent_procedure", "binary_to_spin_convention"],
            "input_binding_mutation_observed": True,
            "mutated_observed": drift_rows,
            "mutation_family": "BINARY_TO_SPIN_MAPPING_CONVENTION_MUTATION",
            "mutation_observed": True,
            "mutation_outcome": "OBSERVED_PARITY_REJECTION",
            "replacement_value": (
                "s_i=2*x_i-1; s=-1 maps to x=0 and s=+1 maps to x=1"
            ),
            "semantic_binding_dimension": "BINARY_TO_SPIN_MAPPING_CONVENTION",
        }
    path, replacement, label = _BINDING_MUTATIONS[math_id]
    mutated = _mutated_copy(golden["inputs"], path, replacement)
    evidence = _execute_observed_mutation(
        math_id,
        material,
        golden["inputs"],
        mutated,
        policy,
        input_path=path,
        baseline_value=_value_at_path(golden["inputs"], path),
        replacement_value=replacement,
        mutation_family=label,
    )
    evidence.update(
        {
            "input_binding_mutation_observed": True,
            "semantic_binding_dimension": label,
        }
    )
    return evidence


def _build_architecture_evidence(
    reconstructed_01_15: Mapping[str, bool],
    *,
    production_import_count: int,
    production_callable_count: int,
) -> tuple[_ArchitectureMathEvidenceV1, ...]:
    material = _tracked_architecture_material()
    rows: list[_ArchitectureMathEvidenceV1] = []
    for math_id in ARCHITECTURE_MATH_IDS:
        tracked = material[math_id]
        if math_id in EXPECTED_MATH_IDS:
            golden = tracked["golden"]
            if not isinstance(golden, Mapping):
                raise ValueError(f"legacy golden row is not a mapping: {math_id}")
            observed = _execute_legacy_architecture_row(
                math_id,
                golden.get("inputs"),
                tracked,
            )
            regression_passed = reconstructed_01_15.get(math_id) is True
            golden_comparison = _compare_architecture_payload(
                math_id,
                observed,
                golden.get("expected"),
                tracked_comparison_policy=str(tracked["comparison_policy"]),
            )
            comparison_passed = regression_passed and golden_comparison.comparison_passed
            formula_regression = _legacy_formula_regression_mutation_evidence(
                math_id,
                tracked,
                observed,
            )
            domain_regression = _legacy_domain_rejection_evidence(
                math_id,
                tracked,
            )
            rows.append(
                _ArchitectureMathEvidenceV1(
                    math_id=math_id,
                    evidence_tier=_EVIDENCE_TIER_BY_MATH_ID[math_id],
                    oracle_id=str(tracked["oracle_id"]),
                    golden_vector_id=str(tracked["golden_vector_id"]),
                    comparison_policy=str(tracked["comparison_policy"]),
                    independent_algorithm_id=(
                        f"ARCHITECTURE_LEGACY_INDEPENDENT_RECONSTRUCTION::{math_id}"
                    ),
                    actual_observed_evidence={
                        "evidence_tier": _LEGACY_GOLDEN_REGRESSION_TIER,
                        "legacy_domain_rejection": _json_ready(domain_regression),
                        "legacy_formula_regression_mutation": _json_ready(
                            formula_regression
                        ),
                        "legacy_golden_comparison": _json_ready(
                            asdict(golden_comparison)
                        ),
                        "legacy_golden_observation": _json_ready(observed),
                        "legacy_regression_group_passed": regression_passed,
                    },
                    golden_comparison_passed=comparison_passed,
                    formula_or_procedure_mutation_observed=True,
                    domain_guard_rejection_observed=True,
                    precision_or_tolerance_mutation_observed=_LEGACY_NOT_CLAIMED,
                    semantic_binding_mutation_observed=_LEGACY_NOT_CLAIMED,
                    production_import_count=production_import_count,
                    production_callable_count=production_callable_count,
                    terminal_state=(
                        "LEGACY_GOLDEN_REGRESSION_PASSED"
                        if comparison_passed
                        else "LEGACY_GOLDEN_REGRESSION_HELD"
                    ),
                    legacy_golden_observation=_json_ready(observed),
                    legacy_formula_regression_mutation_observation=_json_ready(
                        formula_regression
                    ),
                    legacy_domain_rejection_observation=_json_ready(
                        domain_regression
                    ),
                    boundary_vector_id=_LEGACY_NOT_CLAIMED,
                    negative_vector_id=_LEGACY_NOT_CLAIMED,
                    property_id=_LEGACY_NOT_CLAIMED,
                    current_output_schema=_LEGACY_NOT_CLAIMED,
                    declared_comparison_policy=str(tracked["comparison_policy"]),
                    compiled_comparison_mode=(
                        golden_comparison.compiled_comparison_mode
                    ),
                    compiled_absolute_tolerance_or_not_applicable=(
                        golden_comparison.compiled_absolute_tolerance_or_not_applicable
                    ),
                    comparator_registry_version=(
                        golden_comparison.comparator_registry_version
                    ),
                    comparator_authority_classification=(
                        _COMPARATOR_AUTHORITY_CLASSIFICATION
                    ),
                    numeric_text_leaf_paths=_json_ready(
                        golden_comparison.numeric_text_leaf_paths
                    ),
                    numeric_text_representation=(
                        golden_comparison.numeric_text_representation
                    ),
                    comparison_execution_trace=_json_ready(
                        asdict(golden_comparison.execution_trace)
                    ),
                    comparison_policy_execution_observed=(
                        golden_comparison.comparison_policy_execution_observed
                    ),
                    golden_observation=_LEGACY_NOT_CLAIMED,
                    boundary_observation=_LEGACY_NOT_CLAIMED,
                    negative_exception_observation=_LEGACY_NOT_CLAIMED,
                    property_mutation_observation=_LEGACY_NOT_CLAIMED,
                    actual_execution_mutation_observation=_LEGACY_NOT_CLAIMED,
                    semantic_binding_mutation_observation=_LEGACY_NOT_CLAIMED,
                )
            )
            continue

        golden = tracked["golden"]
        if not isinstance(golden, Mapping):
            raise ValueError(f"golden row is not a mapping: {math_id}")
        policy = _compile_comparison_policy(
            str(tracked["comparison_policy"]),
            math_id=math_id,
        )
        observed = _execute_new_architecture_row(math_id, golden.get("inputs"), tracked)
        expected = golden.get("expected")
        golden_comparison = _compare_architecture_payload(
            math_id,
            observed,
            expected,
            tracked_comparison_policy=str(tracked["comparison_policy"]),
        )
        comparison_passed = golden_comparison.comparison_passed
        boundary = tracked.get("boundary")
        if not isinstance(boundary, Mapping):
            raise ValueError(f"boundary row is not a mapping: {math_id}")
        boundary_observed = _execute_new_architecture_row(
            math_id,
            boundary.get("inputs"),
            tracked,
        )
        boundary_comparison = _compare_architecture_payload(
            math_id,
            boundary_observed,
            boundary.get("expected"),
            tracked_comparison_policy=str(tracked["comparison_policy"]),
        )
        if not boundary_comparison.comparison_passed:
            raise ValueError(f"{math_id} BOUNDARY vector comparison failed")
        negative_evidence = _exact_negative_evidence(math_id, tracked)
        property_evidence = _property_mutation_evidence(math_id, tracked, policy)
        execution_mutation_evidence = _actual_execution_mutation_evidence(
            math_id,
            tracked,
            policy,
        )
        binding_evidence = _semantic_binding_mutation_evidence(
            math_id,
            tracked,
            policy,
        )
        rows.append(
            _ArchitectureMathEvidenceV1(
                math_id=math_id,
                evidence_tier=_EVIDENCE_TIER_BY_MATH_ID[math_id],
                oracle_id=str(tracked["oracle_id"]),
                golden_vector_id=str(tracked["golden_vector_id"]),
                comparison_policy=str(tracked["comparison_policy"]),
                independent_algorithm_id=(
                    f"ARCHITECTURE_STANDARD_LIBRARY_RECONSTRUCTION::{math_id}::V2"
                ),
                actual_observed_evidence={
                    "actual_execution_mutation_observation": _json_ready(
                        execution_mutation_evidence
                    ),
                    "boundary_observation": _json_ready(boundary_observed),
                    "boundary_comparison": _json_ready(asdict(boundary_comparison)),
                    "evidence_tier": _CURRENT_FULL_CONTRACT_TIER,
                    "golden_comparison": _json_ready(asdict(golden_comparison)),
                    "golden_observation": _json_ready(observed),
                    "negative_exception_observation": _json_ready(
                        negative_evidence
                    ),
                    "property_mutation_observation": _json_ready(property_evidence),
                    "semantic_binding_mutation_observation": _json_ready(
                        binding_evidence
                    ),
                },
                golden_comparison_passed=comparison_passed,
                formula_or_procedure_mutation_observed=True,
                domain_guard_rejection_observed=True,
                precision_or_tolerance_mutation_observed=True,
                semantic_binding_mutation_observed=True,
                production_import_count=production_import_count,
                production_callable_count=production_callable_count,
                terminal_state=(
                    "CURRENT_FULL_CONTRACT_PASSED"
                    if comparison_passed
                    else "CURRENT_FULL_CONTRACT_HELD"
                ),
                legacy_golden_observation=_CURRENT_LEGACY_NOT_APPLICABLE,
                legacy_formula_regression_mutation_observation=(
                    _CURRENT_LEGACY_NOT_APPLICABLE
                ),
                legacy_domain_rejection_observation=(
                    _CURRENT_LEGACY_NOT_APPLICABLE
                ),
                boundary_vector_id=str(tracked["boundary_vector_id"]),
                negative_vector_id=str(tracked["negative_vector_id"]),
                property_id=str(tracked["property_id"]),
                current_output_schema={
                    "schema_ref": str(tracked["output_schema_ref"]),
                    "schema_version": str(tracked["output_schema_version"]),
                },
                declared_comparison_policy=str(tracked["comparison_policy"]),
                compiled_comparison_mode=golden_comparison.compiled_comparison_mode,
                compiled_absolute_tolerance_or_not_applicable=(
                    golden_comparison.compiled_absolute_tolerance_or_not_applicable
                ),
                comparator_registry_version=_COMPARATOR_REGISTRY_VERSION,
                comparator_authority_classification=(
                    _COMPARATOR_AUTHORITY_CLASSIFICATION
                ),
                numeric_text_leaf_paths=_json_ready(
                    golden_comparison.numeric_text_leaf_paths
                ),
                numeric_text_representation=(
                    golden_comparison.numeric_text_representation
                ),
                comparison_execution_trace=_json_ready(
                    asdict(golden_comparison.execution_trace)
                ),
                comparison_policy_execution_observed=(
                    golden_comparison.comparison_policy_execution_observed
                ),
                golden_observation=_json_ready(observed),
                boundary_observation=_json_ready(boundary_observed),
                negative_exception_observation=_json_ready(negative_evidence),
                property_mutation_observation=_json_ready(property_evidence),
                actual_execution_mutation_observation=_json_ready(
                    execution_mutation_evidence
                ),
                semantic_binding_mutation_observation=_json_ready(binding_evidence),
            )
        )
    return tuple(rows)


def _mutation_observation_complete(value: object) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("mutation_observed") is True
        and isinstance(value.get("mutation_family"), str)
        and bool(value.get("mutation_family"))
        and isinstance(value.get("input_path"), list)
        and bool(value.get("input_path"))
        and "baseline_value" in value
        and "replacement_value" in value
        and isinstance(value.get("exact_consequence"), Mapping)
        and isinstance(value.get("comparison_policy"), str)
        and bool(value.get("comparison_policy"))
    )


def _comparison_execution_complete(
    value: object,
    row: _ArchitectureMathEvidenceV1,
) -> bool:
    authority = _ARCHITECTURE_COMPARATOR_REGISTRY.get(row.math_id)
    if authority is None or not isinstance(value, Mapping):
        return False
    raw_paths = value.get("numeric_text_leaf_paths")
    if not isinstance(raw_paths, list | tuple):
        return False
    normalized_paths: list[tuple[str, ...]] = []
    for raw_path in raw_paths:
        if not isinstance(raw_path, list | tuple) or any(
            not isinstance(component, str) for component in raw_path
        ):
            return False
        normalized_paths.append(tuple(raw_path))
    execution_trace = value.get("execution_trace")
    mode_reached = (
        isinstance(execution_trace, Mapping)
        and execution_trace.get("declared_mode_branch_reached") is True
        and _trace_declared_mode_reached(
            authority.compiled_comparison_mode,
            execution_trace,
        )
    )
    return (
        value.get("math_id") == row.math_id
        and value.get("comparison_passed") is True
        and value.get("tracked_comparison_policy")
        == authority.tracked_comparison_policy
        and value.get("compiled_comparison_mode")
        == authority.compiled_comparison_mode
        and value.get("compiled_absolute_tolerance_or_not_applicable")
        == authority.absolute_tolerance_or_not_applicable
        and tuple(value.get("structural_rules", ())) == authority.structural_rules
        and tuple(normalized_paths) == authority.numeric_text_leaf_paths
        and value.get("numeric_text_representation")
        == authority.numeric_text_representation
        and value.get("comparator_registry_version")
        == _COMPARATOR_REGISTRY_VERSION
        and execution_trace == row.comparison_execution_trace
        and row.numeric_text_leaf_paths == _json_ready(
            authority.numeric_text_leaf_paths
        )
        and row.numeric_text_representation
        == authority.numeric_text_representation
        and mode_reached
        and value.get("comparison_policy_execution_observed") is True
        and row.comparison_policy_execution_observed is True
    )


def _row_golden_comparison_observation(
    row: _ArchitectureMathEvidenceV1,
) -> object:
    if not isinstance(row.actual_observed_evidence, Mapping):
        return None
    key = (
        "legacy_golden_comparison"
        if row.evidence_tier == _LEGACY_GOLDEN_REGRESSION_TIER
        else "golden_comparison"
    )
    return row.actual_observed_evidence.get(key)


def _generic_default_comparator_call_count() -> int:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    return sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_payload_matches"
        for node in ast.walk(tree)
    )


def _legacy_within_tolerance_false_rejection_count(
    material: Mapping[str, Mapping[str, object]],
) -> int:
    result = _compare_architecture_payload(
        "MATH-02",
        {"edge_probability": "0.0600000000000005"},
        {"edge_probability": "0.06"},
        tracked_comparison_policy=str(material["MATH-02"]["comparison_policy"]),
    )
    return int(
        not result.comparison_passed
        or not result.comparison_policy_execution_observed
        or result.execution_trace.numeric_text_tolerance_leaf_checks < 1
    )


def _evidence_denominators(
    rows: Sequence[_ArchitectureMathEvidenceV1],
) -> dict[str, int]:
    legacy_rows = tuple(
        row for row in rows if row.evidence_tier == _LEGACY_GOLDEN_REGRESSION_TIER
    )
    current_rows = tuple(
        row for row in rows if row.evidence_tier == _CURRENT_FULL_CONTRACT_TIER
    )
    material = _tracked_architecture_material()
    return {
        "architecture_identity_order_rows": len(rows),
        "architecture_comparator_rows": sum(
            row.math_id in _ARCHITECTURE_COMPARATOR_REGISTRY for row in rows
        ),
        "legacy_golden_regression_rows": len(legacy_rows),
        "current_full_contract_rows": len(current_rows),
        "legacy_declared_policy_executions": sum(
            row.comparison_policy_execution_observed is True
            and _comparison_execution_complete(
                _row_golden_comparison_observation(row),
                row,
            )
            for row in legacy_rows
        ),
        "current_declared_policy_executions": sum(
            row.comparison_policy_execution_observed is True
            and _comparison_execution_complete(
                _row_golden_comparison_observation(row),
                row,
            )
            for row in current_rows
        ),
        "mode_specific_policy_executions": sum(
            _comparison_execution_complete(
                _row_golden_comparison_observation(row),
                row,
            )
            for row in rows
        ),
        "math_02_numeric_text_tolerance_executions": sum(
            _trace_count(
                row.comparison_execution_trace,
                "numeric_text_tolerance_leaf_checks",
            )
            for row in rows
            if row.math_id == "MATH-02"
            and _comparison_execution_complete(
                _row_golden_comparison_observation(row),
                row,
            )
        ),
        "generic_default_comparator_calls": _generic_default_comparator_call_count(),
        "tracked_policy_registry_mismatches": len(
            _comparator_registry_failures(
                _ARCHITECTURE_COMPARATOR_REGISTRY,
                material,
            )
        ),
        "legacy_tolerance_window_false_acceptances": (
            _legacy_tolerance_window_false_acceptance_count(material)
        ),
        "legacy_within_tolerance_false_rejections": (
            _legacy_within_tolerance_false_rejection_count(material)
        ),
        "policy_execution_flags_without_matching_trace": sum(
            row.comparison_policy_execution_observed is True
            and not (
                isinstance(row.comparison_execution_trace, Mapping)
                and row.comparison_execution_trace.get(
                    "declared_mode_branch_reached"
                )
                is True
                and _trace_declared_mode_reached(
                    row.compiled_comparison_mode,
                    row.comparison_execution_trace,
                )
            )
            for row in rows
        ),
        "current_golden_executions": sum(
            row.golden_observation != _LEGACY_NOT_CLAIMED
            and row.golden_comparison_passed
            for row in current_rows
        ),
        "current_boundary_executions": sum(
            row.boundary_observation != _LEGACY_NOT_CLAIMED
            for row in current_rows
        ),
        "current_exact_negative_executions": sum(
            isinstance(row.negative_exception_observation, Mapping)
            and row.negative_exception_observation.get("attempted_execution") is True
            and row.negative_exception_observation.get("message_substring_matched") is True
            for row in current_rows
        ),
        "current_property_mutations": sum(
            _mutation_observation_complete(row.property_mutation_observation)
            for row in current_rows
        ),
        "current_actual_execution_mutations": sum(
            _mutation_observation_complete(row.actual_execution_mutation_observation)
            for row in current_rows
        ),
        "current_semantic_binding_mutations": sum(
            _mutation_observation_complete(row.semantic_binding_mutation_observation)
            for row in current_rows
        ),
        "legacy_rows_counted_as_current_full_contract": sum(
            row.math_id in EXPECTED_MATH_IDS
            and row.evidence_tier == _CURRENT_FULL_CONTRACT_TIER
            for row in rows
        ),
        "legacy_formula_mutations_reused_as_precision_evidence": sum(
            row.math_id in EXPECTED_MATH_IDS
            and (
                row.precision_or_tolerance_mutation_observed is True
                or (
                    row.actual_execution_mutation_observation != _LEGACY_NOT_CLAIMED
                    and row.actual_execution_mutation_observation
                    == row.legacy_formula_regression_mutation_observation
                )
            )
            for row in rows
        ),
        "legacy_formula_mutations_reused_as_semantic_binding_evidence": sum(
            row.math_id in EXPECTED_MATH_IDS
            and (
                row.semantic_binding_mutation_observed is True
                or (
                    row.semantic_binding_mutation_observation != _LEGACY_NOT_CLAIMED
                    and row.semantic_binding_mutation_observation
                    == row.legacy_formula_regression_mutation_observation
                )
            )
            for row in rows
        ),
    }


def _denominator_claim_failures(
    rows: Sequence[_ArchitectureMathEvidenceV1],
    claimed: Mapping[str, object],
) -> tuple[str, ...]:
    actual = _evidence_denominators(rows)
    failures: list[str] = []
    if set(claimed) != set(actual):
        failures.append("aggregate denominator field set differs")
    for name, expected in actual.items():
        if claimed.get(name) != expected:
            failures.append(
                f"aggregate denominator claim {name}={claimed.get(name)!r}; "
                f"observed {expected}"
            )
    return tuple(failures)


def _evidence_contract_failures(
    rows: Sequence[_ArchitectureMathEvidenceV1],
) -> tuple[str, ...]:
    failures: list[str] = []
    material = _tracked_architecture_material()
    if tuple(row.math_id for row in rows) != ARCHITECTURE_MATH_IDS:
        failures.append("architecture evidence identities/order differ")
    if len(rows) != 29 or len({row.math_id for row in rows}) != 29:
        failures.append("architecture evidence denominator/uniqueness differ")
    for row in rows:
        tracked = material.get(row.math_id)
        if tracked is None:
            failures.append(f"{row.math_id}: wrong owner routing")
            continue
        comparator = _ARCHITECTURE_COMPARATOR_REGISTRY.get(row.math_id)
        if comparator is None:
            failures.append(f"{row.math_id}: comparator row missing")
            continue
        if row.comparison_policy != comparator.tracked_comparison_policy:
            failures.append(f"{row.math_id}: tracked comparison policy drift")
        if row.declared_comparison_policy != comparator.tracked_comparison_policy:
            failures.append(f"{row.math_id}: declared comparison policy drift")
        if row.compiled_comparison_mode != comparator.compiled_comparison_mode:
            failures.append(f"{row.math_id}: compiled comparison mode drift")
        if row.compiled_absolute_tolerance_or_not_applicable != (
            comparator.absolute_tolerance_or_not_applicable
        ):
            failures.append(f"{row.math_id}: compiled comparison tolerance drift")
        if row.comparator_registry_version != _COMPARATOR_REGISTRY_VERSION:
            failures.append(f"{row.math_id}: comparator registry version drift")
        if row.comparator_authority_classification != (
            _COMPARATOR_AUTHORITY_CLASSIFICATION
        ):
            failures.append(f"{row.math_id}: comparator authority drift")
        if row.numeric_text_leaf_paths != _json_ready(
            comparator.numeric_text_leaf_paths
        ):
            failures.append(f"{row.math_id}: numeric-text path authority drift")
        if row.numeric_text_representation != comparator.numeric_text_representation:
            failures.append(f"{row.math_id}: numeric-text representation drift")
        trace_supports_mode = (
            isinstance(row.comparison_execution_trace, Mapping)
            and row.comparison_execution_trace.get("declared_mode_branch_reached")
            is True
            and _trace_declared_mode_reached(
                comparator.compiled_comparison_mode,
                row.comparison_execution_trace,
            )
        )
        if row.comparison_policy_execution_observed is not trace_supports_mode:
            failures.append(f"{row.math_id}: unsupported policy execution flag")
        if not trace_supports_mode:
            failures.append(f"{row.math_id}: comparison policy was not executed")
        if not _comparison_execution_complete(
            _row_golden_comparison_observation(row),
            row,
        ):
            failures.append(f"{row.math_id}: golden comparator execution missing")
        golden_material = tracked.get("golden")
        aggregate_observed = (
            row.legacy_golden_observation
            if row.evidence_tier == _LEGACY_GOLDEN_REGRESSION_TIER
            else row.golden_observation
        )
        if not isinstance(golden_material, Mapping):
            failures.append(f"{row.math_id}: aggregate golden material missing")
        else:
            aggregate_comparison = _compare_architecture_payload(
                row.math_id,
                aggregate_observed,
                golden_material.get("expected"),
                tracked_comparison_policy=str(tracked["comparison_policy"]),
            )
            if not aggregate_comparison.comparison_passed:
                failures.append(
                    f"{row.math_id}: aggregate comparator validation failed"
                )
            if not aggregate_comparison.comparison_policy_execution_observed:
                failures.append(
                    f"{row.math_id}: aggregate comparator mode was not executed"
                )
        expected_tier = _EVIDENCE_TIER_BY_MATH_ID.get(row.math_id)
        if row.evidence_tier != expected_tier or row.evidence_tier != tracked.get(
            "evidence_tier"
        ):
            failures.append(f"{row.math_id}: wrong evidence tier")
        if row.oracle_id != tracked["oracle_id"]:
            failures.append(f"{row.math_id}: wrong oracle ID")
        if row.golden_vector_id != tracked["golden_vector_id"]:
            failures.append(f"{row.math_id}: wrong golden vector ID")
        if row.actual_observed_evidence in (None, {}, SUCCESS_MARKER):
            failures.append(f"{row.math_id}: missing or marker-only observed evidence")
        if row.actual_observed_evidence == {"declared_steps_only": True}:
            failures.append(f"{row.math_id}: declared steps are not execution")
        if row.actual_observed_evidence == {"stored_expected_object_parity": True}:
            failures.append(f"{row.math_id}: stored expected parity is not execution")
        if "H_AGGREGATE" in row.independent_algorithm_id:
            failures.append(f"{row.math_id}: wrong owner routing")
        if not row.golden_comparison_passed:
            failures.append(f"{row.math_id}: golden comparison failed")
        if not row.formula_or_procedure_mutation_observed:
            failures.append(f"{row.math_id}: formula/procedure mutation missing")
        if not row.domain_guard_rejection_observed:
            failures.append(f"{row.math_id}: domain mutation missing")
        if row.production_import_count != 0:
            failures.append(f"{row.math_id}: production import observed")
        if row.production_callable_count != 0:
            failures.append(f"{row.math_id}: production callable observed")

        if expected_tier == _LEGACY_GOLDEN_REGRESSION_TIER:
            if row.comparison_policy != tracked["comparison_policy"]:
                failures.append(f"{row.math_id}: wrong legacy comparison policy")
            if row.terminal_state != "LEGACY_GOLDEN_REGRESSION_PASSED":
                failures.append(f"{row.math_id}: legacy row is held")
            if row.precision_or_tolerance_mutation_observed != _LEGACY_NOT_CLAIMED:
                failures.append(f"{row.math_id}: false legacy precision claim")
            if row.semantic_binding_mutation_observed != _LEGACY_NOT_CLAIMED:
                failures.append(f"{row.math_id}: false legacy semantic-binding claim")
            if row.legacy_golden_observation in (None, _CURRENT_LEGACY_NOT_APPLICABLE):
                failures.append(f"{row.math_id}: legacy golden observation missing")
            if not _mutation_observation_complete(
                row.legacy_formula_regression_mutation_observation
            ):
                failures.append(f"{row.math_id}: legacy formula regression missing")
            if not _mutation_observation_complete(
                row.legacy_domain_rejection_observation
            ):
                failures.append(f"{row.math_id}: legacy domain rejection missing")
            for field_name, value in (
                ("boundary vector", row.boundary_vector_id),
                ("negative vector", row.negative_vector_id),
                ("property", row.property_id),
                ("current output schema", row.current_output_schema),
                ("golden observation", row.golden_observation),
                ("boundary observation", row.boundary_observation),
                ("negative observation", row.negative_exception_observation),
                ("property mutation", row.property_mutation_observation),
                ("actual execution mutation", row.actual_execution_mutation_observation),
                ("semantic binding mutation", row.semantic_binding_mutation_observation),
            ):
                if value != _LEGACY_NOT_CLAIMED:
                    failures.append(f"{row.math_id}: legacy {field_name} was claimed")
            continue

        if expected_tier != _CURRENT_FULL_CONTRACT_TIER:
            failures.append(f"{row.math_id}: unknown registered evidence tier")
            continue
        expected_policy = _compile_comparison_policy(
            str(tracked["comparison_policy"]),
            math_id=row.math_id,
        )
        if row.terminal_state != "CURRENT_FULL_CONTRACT_PASSED":
            failures.append(f"{row.math_id}: current row is held")
        if row.precision_or_tolerance_mutation_observed is not True:
            failures.append(f"{row.math_id}: actual execution mutation missing")
        if row.semantic_binding_mutation_observed is not True:
            failures.append(f"{row.math_id}: semantic binding mutation missing")
        if any(
            value != _CURRENT_LEGACY_NOT_APPLICABLE
            for value in (
                row.legacy_golden_observation,
                row.legacy_formula_regression_mutation_observation,
                row.legacy_domain_rejection_observation,
            )
        ):
            failures.append(f"{row.math_id}: current row claimed legacy evidence")
        if row.boundary_vector_id != tracked.get("boundary_vector_id"):
            failures.append(f"{row.math_id}: wrong boundary vector ID")
        if row.negative_vector_id != tracked.get("negative_vector_id"):
            failures.append(f"{row.math_id}: wrong negative vector ID")
        if row.property_id != tracked.get("property_id"):
            failures.append(f"{row.math_id}: wrong property ID")
        if row.current_output_schema != {
            "schema_ref": tracked.get("output_schema_ref"),
            "schema_version": "ST12B_OUTPUT_V3_4",
        }:
            failures.append(f"{row.math_id}: wrong current output schema")
        if row.golden_observation == _LEGACY_NOT_CLAIMED:
            failures.append(f"{row.math_id}: current GOLDEN execution missing")
        if row.boundary_observation == _LEGACY_NOT_CLAIMED:
            failures.append(f"{row.math_id}: current BOUNDARY execution missing")
        negative = row.negative_exception_observation
        if (
            not isinstance(negative, Mapping)
            or negative.get("attempted_execution") is not True
            or negative.get("exception_type") != "ValueError"
            or negative.get("message_substring_matched") is not True
        ):
            failures.append(f"{row.math_id}: exact NEGATIVE evidence missing")
        for label, value in (
            ("property", row.property_mutation_observation),
            ("actual execution", row.actual_execution_mutation_observation),
            ("semantic binding", row.semantic_binding_mutation_observation),
        ):
            if not _mutation_observation_complete(value):
                failures.append(f"{row.math_id}: {label} mutation evidence missing")
            elif value.get("comparison_policy") != expected_policy.operational_policy:
                failures.append(f"{row.math_id}: {label} comparison policy drift")
        expected_execution_label = _ACTUAL_EXECUTION_MUTATIONS[row.math_id][2]
        if (
            isinstance(row.actual_execution_mutation_observation, Mapping)
            and row.actual_execution_mutation_observation.get("mutation_family")
            != expected_execution_label
        ):
            failures.append(f"{row.math_id}: overbroad execution mutation description")
        expected_binding_label = (
            "BINARY_TO_SPIN_MAPPING_CONVENTION_MUTATION"
            if row.math_id == "MATH-47"
            else _BINDING_MUTATIONS[row.math_id][2]
        )
        if (
            isinstance(row.semantic_binding_mutation_observation, Mapping)
            and row.semantic_binding_mutation_observation.get("mutation_family")
            != expected_binding_label
        ):
            failures.append(f"{row.math_id}: overbroad binding mutation description")
        if ("tracked_legacy_" + "golden_is_locked_fixture") in json.dumps(
            _json_ready(asdict(row)),
            sort_keys=True,
        ):
            failures.append(f"{row.math_id}: stale legacy fixture evidence emitted")

    expected_denominators = {
        "architecture_identity_order_rows": 29,
        "architecture_comparator_rows": 29,
        "legacy_golden_regression_rows": 15,
        "current_full_contract_rows": 14,
        "legacy_declared_policy_executions": 15,
        "current_declared_policy_executions": 14,
        "mode_specific_policy_executions": 29,
        "math_02_numeric_text_tolerance_executions": 1,
        "generic_default_comparator_calls": 0,
        "tracked_policy_registry_mismatches": 0,
        "legacy_tolerance_window_false_acceptances": 0,
        "legacy_within_tolerance_false_rejections": 0,
        "policy_execution_flags_without_matching_trace": 0,
        "current_golden_executions": 14,
        "current_boundary_executions": 14,
        "current_exact_negative_executions": 14,
        "current_property_mutations": 14,
        "current_actual_execution_mutations": 14,
        "current_semantic_binding_mutations": 14,
        "legacy_rows_counted_as_current_full_contract": 0,
        "legacy_formula_mutations_reused_as_precision_evidence": 0,
        "legacy_formula_mutations_reused_as_semantic_binding_evidence": 0,
    }
    actual_denominators = _evidence_denominators(rows)
    for name, expected in expected_denominators.items():
        if actual_denominators.get(name) != expected:
            failures.append(
                f"aggregate denominator {name}={actual_denominators.get(name)!r}; "
                f"expected {expected}"
            )
    return tuple(failures)


def _exercise_evidence_contract_mutations(
    rows: tuple[_ArchitectureMathEvidenceV1, ...],
) -> int:
    first = rows[0]
    current_index = len(EXPECTED_MATH_IDS)
    current = rows[current_index]

    def replace_at(
        math_id: str,
        value: _ArchitectureMathEvidenceV1,
    ) -> tuple[_ArchitectureMathEvidenceV1, ...]:
        index = next(
            position for position, row in enumerate(rows) if row.math_id == math_id
        )
        return (*rows[:index], value, *rows[index + 1 :])

    def changed_mapping(value: object, **changes: object) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise ValueError("mutation target is not a mapping")
        result = dict(value)
        result.update(changes)
        return result

    math_48_row = next(row for row in rows if row.math_id == "MATH-48")
    math_49_row = next(row for row in rows if row.math_id == "MATH-49")
    math_02_row = next(row for row in rows if row.math_id == "MATH-02")
    unsupported_execution_claim = math_02_row.comparison_policy_execution_observed
    if unsupported_execution_claim is not True:
        raise ValueError("MATH-02 valid evidence did not execute its policy")
    unsupported_trace = {
        "structural_mapping_checks": 1,
        "structural_sequence_checks": 0,
        "exact_decimal_text_leaf_checks": 0,
        "precision_34_exact_leaf_checks": 0,
        "numeric_float_tolerance_leaf_checks": 0,
        "numeric_text_tolerance_leaf_checks": 0,
        "exact_order_or_index_checks": 0,
        "boolean_leaf_checks": 0,
        "exact_scalar_checks": 1,
        "declared_mode_branch_reached": True,
    }
    math_02_golden_comparison = changed_mapping(
        math_02_row.actual_observed_evidence["legacy_golden_comparison"],
        execution_trace=unsupported_trace,
        comparison_policy_execution_observed=unsupported_execution_claim,
    )
    math_02_actual_observed = changed_mapping(
        math_02_row.actual_observed_evidence,
        legacy_golden_comparison=math_02_golden_comparison,
    )

    mutations: tuple[Sequence[_ArchitectureMathEvidenceV1], ...] = (
        rows[1:],
        (*rows, first),
        (replace(first, oracle_id="WRONG::ORACLE"), *rows[1:]),
        (replace(first, golden_vector_id="WRONG::VECTOR"), *rows[1:]),
        (replace(first, comparison_policy="WRONG_POLICY"), *rows[1:]),
        (replace(first, compiled_comparison_mode="WRONG_MODE"), *rows[1:]),
        (
            replace(
                first,
                compiled_absolute_tolerance_or_not_applicable="1E-12",
            ),
            *rows[1:],
        ),
        (
            replace(first, comparison_policy_execution_observed=False),
            *rows[1:],
        ),
        replace_at(
            "MATH-02",
            replace(
                math_02_row,
                actual_observed_evidence=math_02_actual_observed,
                comparison_execution_trace=unsupported_trace,
                comparison_policy_execution_observed=unsupported_execution_claim,
            ),
        ),
        replace_at(
            "MATH-02",
            replace(math_02_row, numeric_text_leaf_paths=[]),
        ),
        (
            replace(
                first,
                actual_observed_evidence=changed_mapping(
                    first.actual_observed_evidence,
                    legacy_golden_comparison=None,
                ),
            ),
            *rows[1:],
        ),
        (replace(first, actual_observed_evidence=None), *rows[1:]),
        (replace(first, actual_observed_evidence=SUCCESS_MARKER), *rows[1:]),
        (replace(first, actual_observed_evidence={"declared_steps_only": True}), *rows[1:]),
        (replace(first, actual_observed_evidence={"stored_expected_object_parity": True}), *rows[1:]),
        (replace(first, formula_or_procedure_mutation_observed=False), *rows[1:]),
        (replace(first, domain_guard_rejection_observed=False), *rows[1:]),
        (replace(first, evidence_tier=_CURRENT_FULL_CONTRACT_TIER), *rows[1:]),
        (replace(first, precision_or_tolerance_mutation_observed=True), *rows[1:]),
        (replace(first, semantic_binding_mutation_observed=True), *rows[1:]),
        (
            replace(
                first,
                actual_execution_mutation_observation=(
                    first.legacy_formula_regression_mutation_observation
                ),
            ),
            *rows[1:],
        ),
        (
            replace(
                first,
                semantic_binding_mutation_observation=(
                    first.legacy_formula_regression_mutation_observation
                ),
            ),
            *rows[1:],
        ),
        (replace(first, boundary_observation=True), *rows[1:]),
        (replace(first, production_import_count=1), *rows[1:]),
        (replace(first, production_callable_count=1), *rows[1:]),
        (replace(first, independent_algorithm_id="H_AGGREGATE_VALIDATOR"), *rows[1:]),
        replace_at(
            current.math_id,
            replace(current, evidence_tier=_LEGACY_GOLDEN_REGRESSION_TIER),
        ),
        replace_at(current.math_id, replace(current, boundary_vector_id="WRONG::BOUNDARY")),
        replace_at(current.math_id, replace(current, negative_vector_id="WRONG::NEGATIVE")),
        replace_at(current.math_id, replace(current, property_id="WRONG::PROPERTY")),
        replace_at(current.math_id, replace(current, comparison_policy="WRONG_POLICY")),
        replace_at(current.math_id, replace(current, comparator_registry_version="DRIFTED")),
        replace_at(current.math_id, replace(current, golden_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(current.math_id, replace(current, boundary_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(current.math_id, replace(current, negative_exception_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(current.math_id, replace(current, property_mutation_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(current.math_id, replace(current, actual_execution_mutation_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(current.math_id, replace(current, semantic_binding_mutation_observation=_LEGACY_NOT_CLAIMED)),
        replace_at(
            "MATH-48",
            replace(
                math_48_row,
                semantic_binding_mutation_observation=changed_mapping(
                    math_48_row.semantic_binding_mutation_observation,
                    mutation_family="CQM_SCHEMA_UNIT_DOMAIN_OBJECTIVE_SENSE",
                ),
            ),
        ),
        replace_at(
            "MATH-49",
            replace(
                math_49_row,
                semantic_binding_mutation_observation=changed_mapping(
                    math_49_row.semantic_binding_mutation_observation,
                    mutation_family="DQM_SCHEMA_VARIABLE_CASE_PAIRWISE_BINDING",
                ),
            ),
        ),
    )
    if any(not _evidence_contract_failures(candidate) for candidate in mutations):
        raise ValueError("architecture grouped evidence mutation escaped rejection")

    truthful_denominators = _evidence_denominators(rows)
    false_precision_claim = dict(truthful_denominators)
    false_precision_claim["current_actual_execution_mutations"] = 29
    if not _denominator_claim_failures(rows, false_precision_claim):
        raise ValueError("aggregate 29/29 execution-mutation claim was accepted")
    false_binding_claim = dict(truthful_denominators)
    false_binding_claim["current_semantic_binding_mutations"] = 29
    if not _denominator_claim_failures(rows, false_binding_claim):
        raise ValueError("aggregate 29/29 semantic-binding claim was accepted")
    denominator_mutation_count = 2

    material = _tracked_architecture_material()
    for math_id in ("MATH-46", "MATH-47", "MATH-48", "MATH-49"):
        row = next(item for item in rows if item.math_id == math_id)
        stale_index = rows.index(row)
        stale = (
            *rows[:stale_index],
            replace(
                row,
                oracle_id=f"ORACLE::{math_id}::LEGACY",
                boundary_vector_id=None,
                negative_vector_id=None,
                property_id=None,
            ),
            *rows[stale_index + 1 :],
        )
        if not _evidence_contract_failures(stale):
            raise ValueError(f"legacy material selection escaped for {math_id}")

    try:
        _observe_exact_negative_operation(
            lambda: (_ for _ in ()).throw(ValueError("wrong ValueError")),
            math_id="MATH-18",
            vector_id="VECTOR::MATH-18::NEGATIVE",
            expected_name="ValueError",
            expected_message="effective independent trial count",
        )
    except _EvidenceContractMismatch:
        pass
    else:
        raise ValueError("generic ValueError satisfied an exact negative contract")

    operational_checks = 0
    for math_id in CURRENT_ST12B_ARCHITECTURE_MATH_IDS:
        _exact_negative_evidence(math_id, material[math_id])
        operational_checks += 1

    math_18 = material["MATH-18"]
    golden_18 = math_18["golden"]
    assert isinstance(golden_18, Mapping) and isinstance(golden_18.get("inputs"), Mapping)
    invalid_18 = dict(golden_18["inputs"])
    invalid_18["effective_independent_trial_count"] = 1.0
    if "(1, material trial count]" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-18", invalid_18, math_18)
    ):
        raise ValueError("MATH-18 effective trial count 1.0 was not rejected exactly")
    operational_checks += 1

    math_21 = material["MATH-21"]
    golden_21 = math_21["golden"]
    assert isinstance(golden_21, Mapping) and isinstance(golden_21.get("inputs"), Mapping)
    invalid_21 = dict(golden_21["inputs"])
    invalid_21["aggregation_rule"] = "NONEMPTY_BUT_WRONG"
    if "ALL_PATHS_NO_CHERRY_PICKING" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-21", invalid_21, math_21)
    ):
        raise ValueError("MATH-21 accepted a wrong nonempty aggregation token")
    operational_checks += 1

    math_46 = material["MATH-46"]
    golden_46 = math_46["golden"]
    assert isinstance(golden_46, Mapping)
    full_symmetric_46 = {
        "representation": "FULL_SYMMETRIC_ADAPTER_SUM_OFF_DIAGONAL_PAIRS",
        "diagonal": [1.0, -2.0],
        "upper_terms": [],
        "full_symmetric_matrix": [[1.0, 1.0], [2.0, -2.0]],
        "constant": 0.5,
        "binary_assignment": [1, 0],
    }
    converted_46 = _execute_new_architecture_row(
        "MATH-46",
        full_symmetric_46,
        math_46,
    )
    if not _compare_architecture_payload(
        "MATH-46",
        converted_46,
        golden_46.get("expected"),
        tracked_comparison_policy=str(math_46["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("MATH-46 full-symmetric adapter changed canonical QUBO meaning")
    conflicting_46 = dict(full_symmetric_46)
    conflicting_46["upper_terms"] = [{"i": 0, "j": 1, "value": 3.0}]
    if "conflicts" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-46", conflicting_46, math_46)
    ):
        raise ValueError("MATH-46 conflicting representations were accepted")
    operational_checks += 2

    math_47 = material["MATH-47"]
    golden_47 = math_47["golden"]
    assert isinstance(golden_47, Mapping)
    output_47 = _execute_new_architecture_row("MATH-47", golden_47.get("inputs"), math_47)
    drifted_47 = _mutated_copy(output_47, ("offset",), float(output_47["offset"]) + 1.0)
    if _compare_architecture_payload(
        "MATH-47",
        drifted_47,
        golden_47.get("expected"),
        tracked_comparison_policy=str(math_47["comparison_policy"]),
    ).comparison_passed:
        raise ValueError("MATH-47 sign/offset parity drift escaped comparison")
    operational_checks += 1

    math_48 = material["MATH-48"]
    golden_48 = math_48["golden"]
    assert isinstance(golden_48, Mapping) and isinstance(golden_48.get("inputs"), Mapping)
    inadequate_48 = _mutated_copy(
        golden_48["inputs"],
        ("model", "conversion_penalty_candidate"),
        1.0,
    )
    if "conversion penalty is inadequate" not in _exact_value_error_message(
        lambda: _execute_new_architecture_row("MATH-48", inadequate_48, math_48)
    ):
        raise ValueError("MATH-48 inadequate conversion penalty was accepted")
    if _execute_new_architecture_row("MATH-48", golden_48["inputs"], math_48).get(
        "schema_version"
    ) != "QTT_CQM_GRAMMAR_V1":
        raise ValueError("MATH-48 current CQM grammar was not executed")
    operational_checks += 2

    math_49 = material["MATH-49"]
    golden_49 = math_49["golden"]
    assert isinstance(golden_49, Mapping) and isinstance(golden_49.get("inputs"), Mapping)
    with_pairwise = _execute_new_architecture_row("MATH-49", golden_49["inputs"], math_49)
    without_pairwise_inputs = _mutated_copy(
        golden_49["inputs"],
        ("model", "pairwise_biases"),
        [],
    )
    without_pairwise = _execute_new_architecture_row(
        "MATH-49",
        without_pairwise_inputs,
        math_49,
    )
    if with_pairwise["energy"] == without_pairwise["energy"]:
        raise ValueError("MATH-49 pairwise interaction was ignored")
    operational_checks += 1

    source_text = Path(__file__).read_text(encoding="utf-8")
    renamed_key_token = "WRONG_" + "UNIT_OR_SOURCE"
    stale_fixture_token = "tracked_legacy_" + "golden_is_locked_fixture"
    if renamed_key_token in source_text or stale_fixture_token in source_text:
        raise ValueError("false renamed-key or legacy evidence design remains")
    operational_checks += 1
    return (
        len(mutations)
        + 4
        + denominator_mutation_count
        + operational_checks
        + _comparison_policy_self_rejections()
        + _exercise_independence_guard_mutations()
    )


def _independent_source_boundary_counts_for_tree(
    tree: ast.Module,
) -> tuple[int, int]:
    production_import_count = 0
    production_callable_count = 0
    forbidden_aliases: set[str] = set()

    def production_module(name: str) -> bool:
        return (
            name == "qtt"
            or name.startswith("qtt.")
            or name == "src.qtt"
            or name.startswith("src.qtt.")
        )

    def forbidden_symbol(name: str) -> bool:
        lowered = name.lower()
        return (
            name == "IMPLEMENTATION_REGISTRY"
            or name.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            or name.startswith("compute_math_")
            or "production" in lowered and "registry" in lowered
            or lowered in {
                "validate_domain",
                "validate_qku_computation_control_plane",
                "import_module",
            }
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if production_module(alias.name) or alias.name == "importlib" or alias.name.startswith("importlib."):
                    production_import_count += 1
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if (
                node.level > 0
                or production_module(module)
                or module == "src"
                and any(alias.name == "qtt" for alias in node.names)
                or module == "importlib"
                or module.startswith("importlib.")
            ):
                production_import_count += 1
        elif isinstance(node, ast.Assign):
            value_name = ""
            if isinstance(node.value, ast.Name):
                value_name = node.value.id
            elif isinstance(node.value, ast.Attribute):
                value_name = node.value.attr
            if forbidden_symbol(value_name):
                forbidden_aliases.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                production_callable_count += int(
                    node.func.id in {"eval", "exec", "__import__"}
                    or forbidden_symbol(node.func.id)
                    or node.func.id in forbidden_aliases
                )
            elif isinstance(node.func, ast.Attribute):
                production_callable_count += int(
                    forbidden_symbol(node.func.attr)
                    or (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "importlib"
                    )
                )
        elif isinstance(node, ast.Name):
            production_callable_count += int(
                node.id == "IMPLEMENTATION_REGISTRY"
                or node.id.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            )
        elif isinstance(node, ast.Attribute):
            production_callable_count += int(
                node.attr == "IMPLEMENTATION_REGISTRY"
                or node.attr.startswith("TRANCHE_A_ORACLE_BY_MATH_ID")
            )
    return production_import_count, production_callable_count


def _independent_source_boundary_counts() -> tuple[int, int]:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    return _independent_source_boundary_counts_for_tree(tree)


def _exercise_independence_guard_mutations() -> int:
    prohibited_sources = (
        "import qtt",
        "import src.qtt.validation",
        "from src import qtt",
        "from qtt.foo import compute_math_46\ncompute_math_46()",
        "from src.qtt.foo import validate_domain\nvalidate_domain()",
        "from .production import oracle",
        "import importlib\nimportlib.import_module('src.qtt.validation')",
        "eval('1 + 1')",
        "exec('answer = 2')",
        "__import__('qtt')",
        "runner = compute_math_46\nrunner()",
        "registry = IMPLEMENTATION_REGISTRY",
    )
    for source in prohibited_sources:
        counts = _independent_source_boundary_counts_for_tree(ast.parse(source))
        if counts == (0, 0):
            raise ValueError(
                f"independence guard accepted prohibited source: {source!r}"
            )
    return len(prohibited_sources)


def independently_reconstruct() -> dict[str, bool]:
    with localcontext(DECIMAL_CONTEXT):
        def implied(price: object, payout: object) -> Decimal:
            price_value = Decimal(price)
            payout_value = Decimal(payout)
            if payout_value <= 0 or not 0 <= price_value <= payout_value:
                raise ValueError("invalid binary contract")
            return price_value / payout_value

        def edge(model: object, market: object) -> float:
            model_value = float(_probability_decimal(model))
            market_value = float(_probability_decimal(market))
            return model_value - market_value

        def book(bid: object, ask: object) -> tuple[Decimal, Decimal, Decimal]:
            bid_value = Decimal(bid)
            ask_value = Decimal(ask)
            if bid_value < 0 or ask_value < bid_value:
                raise ValueError("crossed book")
            midpoint = (bid_value + ask_value) / Decimal(2)
            spread = ask_value - bid_value
            if midpoint <= 0:
                raise ValueError("zero midpoint")
            return midpoint, spread, spread / midpoint

        midpoint = (Decimal("0.42") + Decimal("0.44")) / Decimal(2)
        spread = Decimal("0.44") - Decimal("0.42")
        math_01 = (
            implied("0.42", "1.00") == Decimal("0.42")
            and implied("0.84", "2.00") == implied("0.42", "1.00")
            and implied("0", "1") == 0
            and implied("1", "1") == 1
            and _expect_value_error(lambda: implied("1", "0"))
        )
        math_02 = (
            abs(edge(0.58, 0.52) - 0.06) <= 1e-15
            and edge(0.58, 0.52) == -edge(0.52, 0.58)
            and _expect_value_error(lambda: edge(1.01, 0.5))
        )
        translated = book("10.42", "10.44")
        base_book = book("0.42", "0.44")
        scaled_book = book("0.84", "0.88")
        math_03 = (
            midpoint == Decimal("0.43")
            and (Decimal("0.44") + Decimal("0.42")) / Decimal(2) == midpoint
            and Decimal("0.42") <= midpoint <= Decimal("0.44")
            and _expect_value_error(lambda: book("0.5", "0.4"))
        )
        math_04 = (
            spread == Decimal("0.02")
            and spread >= 0
            and translated[1] == spread
            and _expect_value_error(lambda: book("0.5", "0.4"))
        )
        math_05 = (
            base_book[2]
            == Decimal("0.04651162790697674418604651162790698")
            and scaled_book[2] == base_book[2]
            and _expect_value_error(lambda: book("0", "0"))
        )
        math_06_golden = _binary_net(
            "1",
            0.60,
            "0.55",
            "-0.45",
            "0.01",
            "0",
            "0",
            "0",
        )
        math_06 = (
            math_06_golden == Decimal("0.14")
            and math_06_golden
            == _binary_net(
                "1",
                "0.60",
                "0.55",
                "-0.45",
                "0.01",
                "0",
                "0",
                "0",
            )
            and _binary_net("1", 0.0, "2", "-1", "0", "0", "0", "0")
            == Decimal("-1")
            and _binary_net("1", 1.0, "2", "-1", "0", "0", "0", "0")
            == Decimal("2")
            and _binary_net("2", 0.6, "2", "-1", "0", "0", "0", "0")
            == 2 * _binary_net("1", 0.6, "2", "-1", "0", "0", "0", "0")
            and _expect_value_error(
                lambda: _binary_net("1", float("nan"), "1", "0", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _binary_net("1", 1.1, "1", "0", "0", "0", "0", "0")
            )
        )
        math_07_golden = _multi_net(
            (0.2, 0.3, 0.5),
            ("1.0", "-0.2", "0.1"),
            "1",
            "0.02",
            "0",
            "0",
            "0",
        )
        math_07_permuted = _multi_net(
            (0.5, 0.2, 0.3),
            ("0.1", "1.0", "-0.2"),
            "1",
            "0.02",
            "0",
            "0",
            "0",
        )
        math_07 = (
            math_07_golden == Decimal("0.17")
            and math_07_golden
            == _multi_net(
                ("0.2", "0.3", "0.5"),
                ("1.0", "-0.2", "0.1"),
                "1",
                "0.02",
                "0",
                "0",
                "0",
            )
            and math_07_permuted == math_07_golden
            and _multi_net((1.0, 0.0), ("2", "-9"), "1", "0", "0", "0", "0")
            == Decimal("2")
            and _expect_value_error(
                lambda: _multi_net((0.4, 0.4), ("1", "2"), "1", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _multi_net((float("inf"), 0.0), ("1", "2"), "1", "0", "0", "0", "0")
            )
            and _expect_value_error(
                lambda: _multi_net((0.5, 0.5), ("1",), "1", "0", "0", "0", "0")
            )
        )
        math_08 = (
            abs(_brier("0.70", 1) - 0.09) <= 1e-15
            and _brier(1.0, 1) == 0.0
            and _brier(0.0, 0) == 0.0
            and _brier((0.7, 0.3), (1, 0))
            == _brier(0.7, 1) + _brier(0.3, 0)
            and _expect_value_error(lambda: _brier((0.6, 0.3), (1, 0)))
        )
        math_09 = (
            abs(_log_loss(0.7, 1, 1e-15) - 0.35667494393873245)
            <= 1e-15
            and math.isfinite(_log_loss(0.0, 1))
            and math.isfinite(_log_loss(1.0, 0))
            and _log_loss(0.9, 1) < _log_loss(0.6, 1)
            and _log_loss(0.1, 0) < _log_loss(0.4, 0)
            and _expect_value_error(lambda: _log_loss(float("nan"), 1))
        )
        ece_golden = _ece_from_raw(
            (0.3, 0.3, 0.8, 0.8),
            (1, 0, 1, 0),
            (0.0, 0.5, 1.0),
        )
        ece_boundary = _ece_from_raw(
            (0.0, 1.0),
            (0, 1),
            (0.0, 0.5, 1.0),
        )
        values: dict[str, bool] = {
            "MATH-01": math_01,
            "MATH-02": math_02,
            "MATH-03": math_03,
            "MATH-04": math_04,
            "MATH-05": math_05,
            "MATH-06": math_06,
            "MATH-07": math_07,
            "MATH-08": math_08,
            "MATH-09": math_09,
            "MATH-10": (
                abs(ece_golden - 0.25) <= 1e-15
                and ece_boundary == 0.0
                and _expect_value_error(
                    lambda: _ece_from_raw(
                        (0.2, 0.8),
                        (1,),
                        (0.0, 0.5, 1.0),
                    )
                )
            ),
        }
    lower, upper = _wilson(8, 10, 0.95)
    low_boundary = _wilson(0, 10, 0.95)
    high_boundary = _wilson(10, 10, 0.95)
    values["MATH-11"] = (
        abs(lower - 0.49016247153664183) <= 1e-12
        and abs(upper - 0.9433178485456247) <= 1e-12
        and 0 <= low_boundary[0] <= low_boundary[1] <= 1
        and 0 <= high_boundary[0] <= high_boundary[1] <= 1
        and low_boundary[1] <= high_boundary[1]
        and _expect_value_error(lambda: _wilson(11, 10, 0.95))
    )
    p_values = (0.001, 0.01, 0.04, 0.2)
    bh_adjusted = _adjusted_p(p_values, 1.0)
    tied = _adjusted_p((0.01, 0.01, 0.2), 1.0)
    values["MATH-12"] = (
        _bh(p_values, 0.05, 1.0) == (0, 1)
        and tuple(sorted(bh_adjusted)) == bh_adjusted
        and tied[0] == tied[1]
        and _bh((0.01, 0.01, 0.2), 0.05, 1.0) == (0, 1)
        and _expect_value_error(lambda: _bh((0.1,), -0.1, 1.0))
    )
    harmonic = sum(1 / index for index in range(1, len(p_values) + 1))
    by_rejections = _bh(p_values, 0.05, harmonic)
    by_adjusted = _adjusted_p(p_values, harmonic)
    values["MATH-13"] = (
        by_rejections == (0, 1)
        and set(by_rejections) <= set(_bh(p_values, 0.05, 1.0))
        and all(
            by_value >= bh_value
            for by_value, bh_value in zip(
                by_adjusted,
                bh_adjusted,
                strict=True,
            )
        )
        and _expect_value_error(lambda: _bh((), 0.05, harmonic))
    )
    first = _stationary_means(1401)
    second = _stationary_means(1401)
    ordered = sorted(first)
    values["MATH-14"] = (
        first == second
        and ordered[1] <= 3.0 <= ordered[-2]
        and ordered[1] <= ordered[-2]
        and _stationary_means(1402) != first
        and _expect_value_error(lambda: _stationary_means(1401, (1.0,)))
    )
    oriented_rows = ((1.0,),) * 4
    values["MATH-15"] = (
        _white_reality_p_value(
            oriented_rows,
            benchmark_minus_candidate=True,
            seed=1501,
            replicates=64,
        )
        == 0.0
        and _white_reality_p_value(
            oriented_rows,
            benchmark_minus_candidate=False,
            seed=1501,
            replicates=64,
        )
        == 1.0
        and _expect_value_error(
            lambda: _white_reality_p_value(
                ((0.0, 0.0),) * 4,
                benchmark_minus_candidate=True,
                seed=1501,
                replicates=64,
            )
        )
    )
    return values


def main(*, emit_stage1_launch_graph_marker: bool = True) -> int:
    failures: list[str] = []
    expected_names = frozenset(PRODUCTION_NAMES)
    actual_names = frozenset(path.name for path in PACKAGE.glob("*.py"))
    if len(expected_names) != len(PRODUCTION_NAMES):
        failures.append(
            "independent production module roster contains duplicate names"
        )
    missing_names = tuple(sorted(expected_names - actual_names))
    unexpected_names = tuple(sorted(actual_names - expected_names))
    if missing_names or unexpected_names:
        failures.append(
            "production core differs from the exact independently declared "
            f"centralized module roster: missing={missing_names!r} "
            f"unexpected={unexpected_names!r}"
        )
    data_names = frozenset(path.name for path in (PACKAGE / "data").glob("*") if path.is_file())
    if len(data_names) != 13 or "st12f_parameter_resources_manifest.json" not in data_names or "__init__.py" in data_names:
        failures.append("certified ST12-F data directory differs from 13 exact non-package resources")
    for name in PRODUCTION_NAMES:
        path = PACKAGE / name
        if not path.is_file():
            failures.append(f"missing production file: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{name}: {exc}")
    try:
        failures.extend(_stage1_launch_graph_failures())
    except Exception as exc:
        failures.append(f"Stage-1 independent reconstruction failed closed: {exc}")
    for file_name, class_name, expected_count in (
        ("input_lock.py", "ImmutableReplayPaperInputLockV1", 33),
        ("evidence.py", "ReplayResultContractV1", 26),
        ("evidence.py", "PaperResultContractV1", 26),
        ("evidence.py", "DivergenceAssessmentV1", 18),
        ("evidence.py", "ComputationEvidenceBundleV1", 30),
    ):
        tree = ast.parse((PACKAGE / file_name).read_text(encoding="utf-8"))
        classes = tuple(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        field_names = tuple(
            node.target.id
            for node in (classes[0].body if len(classes) == 1 else ())
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
        )
        field_count = len(field_names)
        if field_count != expected_count:
            failures.append(f"{class_name}: canonical field count={field_count}, expected={expected_count}")
        if (
            class_name == "ComputationEvidenceBundleV1"
            and field_names != EVIDENCE_BUNDLE_FIELDS
        ):
            failures.append(
                "ComputationEvidenceBundleV1 exact 30-field roster differs"
            )
    specification_tree = ast.parse(
        (PACKAGE / "specification.py").read_text(encoding="utf-8")
    )
    formula_class = next(
        (
            node
            for node in specification_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "FormulaExecutionContractV1"
        ),
        None,
    )
    formula_fields = tuple(
        statement.target.id
        for statement in (formula_class.body if formula_class else ())
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    )
    if formula_fields != FORMULA_EXECUTION_FIELDS:
        failures.append("FormulaExecutionContractV1 mandatory fields differ")
    alias_is_same_class = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "CompiledComputationEnvelopeV1"
            for target in node.targets
        )
        and isinstance(node.value, ast.Name)
        and node.value.id == "FormulaExecutionContractV1"
        for node in specification_tree.body
    )
    if not alias_is_same_class:
        failures.append("historical contract name is not a same-class alias")
    math_io_assignment = next(
        (
            node.value
            for node in specification_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_MATH_IO_ROWS"
                for target in node.targets
            )
        ),
        None,
    )
    math_io_ids = (
        tuple(
            ast.literal_eval(item.args[0])
            for item in math_io_assignment.elts
            if isinstance(item, ast.Call) and item.args
        )
        if isinstance(math_io_assignment, ast.Tuple)
        else ()
    )
    if math_io_ids != EXPECTED_ALL_MATH_IDS:
        failures.append("typed math I/O contract identities differ")
    if (
        not isinstance(math_io_assignment, ast.Tuple)
        or not math_io_assignment.elts
        or not isinstance(math_io_assignment.elts[0], ast.Call)
        or tuple(
            field[0]
            for field in ast.literal_eval(math_io_assignment.elts[0].args[2])
        )
        != ("contract_price", "payout_per_winning_contract")
    ):
        failures.append("MATH-01 payout input is absent from the typed contract")
    specification_text = (PACKAGE / "specification.py").read_text(encoding="utf-8")
    if (
        "identity_binding: CanonicalIdentityBindingV1" not in specification_text
        or "qku_id:" in specification_text[
            specification_text.find("class ComputationContractCompilerV1") :
        ]
    ):
        failures.append("compiler accepts a free-form QKU identity")
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    if (
        any(path not in validation_text for path in SHARED_VALIDATION_TEST_PATHS)
        or "ST12A-TEST::INDEPENDENT::" in validation_text
    ):
        failures.append(
            "derived test coverage does not reference the exact shared test paths"
        )
    try:
        parameter_tree = ast.parse(
            (PACKAGE / "parameter_policy.py").read_text(encoding="utf-8")
        )
        parameter_rows = json.loads(
            _string_literal(parameter_tree, "_PARAMETER_ROWS_JSON")
        )
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"parameter literal could not be reconstructed: {exc}")
        parameter_rows = []
    required_parameter_fields = {
        "canonical_owner",
        "codex_online_research_allowed",
        "effective_bounded_search_space_or_fit_constraint",
        "effective_day1_seed_value_or_resolution_rule",
        "effective_default_authority_class",
        "effective_fallback_behavior_when_value_unavailable",
        "effective_owner_dashboard_editability_class",
        "effective_reference_range_or_structural_constraint",
        "effective_resolution_class",
        "effective_source_state_refs",
        "effective_unit_or_basis",
        "missing_stale_invalid_behavior",
        "parameter_audit_id",
        "parameter_id",
        "precision_and_rounding_policy",
        "runtime_resolution_procedure",
        "source_line_end",
        "source_line_start",
        "step12_primary_tranche_id",
    }
    if (
        len(parameter_rows) != 135
        or len(
            {
                row.get("parameter_id")
                for row in parameter_rows
                if isinstance(row, dict)
            }
        )
        != 135
        or len(
            {
                row.get("parameter_audit_id")
                for row in parameter_rows
                if isinstance(row, dict)
            }
        )
        != 135
        or any(
            not isinstance(row, dict)
            or not required_parameter_fields <= set(row)
            or any(
                row[field] in ("", None)
                for field in required_parameter_fields
            )
            or row["canonical_owner"] != "QKUComputationControlPlaneV1"
            or row["codex_online_research_allowed"] is not False
            or row["step12_primary_tranche_id"] != "ST12-TRANCHE-A"
            or not isinstance(row["effective_source_state_refs"], list)
            or not isinstance(row["precision_and_rounding_policy"], dict)
            or not row["precision_and_rounding_policy"]
            or not isinstance(row["runtime_resolution_procedure"], list)
            or not row["runtime_resolution_procedure"]
            or isinstance(row["source_line_start"], bool)
            or not isinstance(row["source_line_start"], int)
            or isinstance(row["source_line_end"], bool)
            or not isinstance(row["source_line_end"], int)
            or row["source_line_start"] <= 0
            or row["source_line_end"] < row["source_line_start"]
            for row in parameter_rows
        )
    ):
        failures.append("independent 135-row parameter reconstruction failed")
    _v34_frozen_literal_checks(failures)
    reconstructed = independently_reconstruct()
    if tuple(reconstructed) != EXPECTED_MATH_IDS:
        failures.append("independent MATH-01..15 denominator mismatch")
    failures.extend(
        f"{math_id}: independent golden reconstruction failed"
        for math_id, passed in reconstructed.items()
        if not passed
    )
    evidence_rows: tuple[_ArchitectureMathEvidenceV1, ...] = tuple()
    grouped_mutation_count = 0
    production_import_count, production_callable_count = (
        _independent_source_boundary_counts()
    )
    try:
        evidence_rows = _build_architecture_evidence(
            reconstructed,
            production_import_count=production_import_count,
            production_callable_count=production_callable_count,
        )
        failures.extend(_evidence_contract_failures(evidence_rows))
        grouped_mutation_count = _exercise_evidence_contract_mutations(evidence_rows)
        failures.extend(
            _denominator_claim_failures(
                evidence_rows,
                _evidence_denominators(evidence_rows),
            )
        )
    except (OSError, SyntaxError, ValueError, KeyError, TypeError) as exc:
        failures.append(f"architecture row evidence reconstruction failed: {exc}")
    if production_import_count or production_callable_count:
        failures.append(
            "architecture validator crossed the production import/call boundary"
        )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    evidence_denominators = _evidence_denominators(evidence_rows)
    current_evidence_rows = tuple(
        row
        for row in evidence_rows
        if row.evidence_tier == _CURRENT_FULL_CONTRACT_TIER
    )
    evidence_payload = {
        "architecture_math_count": len(evidence_rows),
        "denominators": evidence_denominators,
        "evidence_tier_domain": [
            _LEGACY_GOLDEN_REGRESSION_TIER,
            _CURRENT_FULL_CONTRACT_TIER,
        ],
        "rows": [_json_ready(asdict(row)) for row in evidence_rows],
        "schema_version": EVIDENCE_MARKER,
    }
    print(
        f"{EVIDENCE_MARKER} "
        + json.dumps(
            evidence_payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    current_evidence_payload = {
        "current_full_contract_count": len(current_evidence_rows),
        "denominators": evidence_denominators,
        "rows": [_json_ready(asdict(row)) for row in current_evidence_rows],
        "schema_version": CURRENT_FULL_CONTRACT_EVIDENCE_MARKER,
    }
    print(
        f"{CURRENT_FULL_CONTRACT_EVIDENCE_MARKER} "
        + json.dumps(
            current_evidence_payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    if emit_stage1_launch_graph_marker:
        print(STAGE1_LAUNCH_GRAPH_MARKER)
    print(
        f"{SUCCESS_MARKER} "
        f"architecture_identity_order_rows={evidence_denominators['architecture_identity_order_rows']} "
        f"architecture_comparator_rows={evidence_denominators['architecture_comparator_rows']} "
        f"legacy_golden_regression_rows={evidence_denominators['legacy_golden_regression_rows']} "
        f"current_full_contract_rows={evidence_denominators['current_full_contract_rows']} "
        f"legacy_declared_policy_executions={evidence_denominators['legacy_declared_policy_executions']} "
        f"current_declared_policy_executions={evidence_denominators['current_declared_policy_executions']} "
        f"mode_specific_policy_executions={evidence_denominators['mode_specific_policy_executions']} "
        f"math_02_numeric_text_tolerance_executions={evidence_denominators['math_02_numeric_text_tolerance_executions']} "
        f"generic_default_comparator_calls={evidence_denominators['generic_default_comparator_calls']} "
        f"tracked_policy_registry_mismatches={evidence_denominators['tracked_policy_registry_mismatches']} "
        f"legacy_tolerance_window_false_acceptances={evidence_denominators['legacy_tolerance_window_false_acceptances']} "
        f"legacy_within_tolerance_false_rejections={evidence_denominators['legacy_within_tolerance_false_rejections']} "
        f"policy_execution_flags_without_matching_trace={evidence_denominators['policy_execution_flags_without_matching_trace']} "
        f"current_golden_executions={evidence_denominators['current_golden_executions']} "
        f"current_boundary_executions={evidence_denominators['current_boundary_executions']} "
        f"current_exact_negative_executions={evidence_denominators['current_exact_negative_executions']} "
        f"current_property_mutations={evidence_denominators['current_property_mutations']} "
        f"current_actual_execution_mutations={evidence_denominators['current_actual_execution_mutations']} "
        f"current_semantic_binding_mutations={evidence_denominators['current_semantic_binding_mutations']} "
        f"legacy_rows_counted_as_current_full_contract={evidence_denominators['legacy_rows_counted_as_current_full_contract']} "
        f"legacy_formula_mutations_reused_as_precision_evidence={evidence_denominators['legacy_formula_mutations_reused_as_precision_evidence']} "
        f"legacy_formula_mutations_reused_as_semantic_binding_evidence={evidence_denominators['legacy_formula_mutations_reused_as_semantic_binding_evidence']} "
        f"grouped_contract_mutations={grouped_mutation_count} "
        f"production_imports={production_import_count} "
        f"production_calls={production_callable_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
