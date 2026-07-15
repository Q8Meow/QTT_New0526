#!/usr/bin/env python3
"""Build the single PR169 CONTROL1 decision-computation registry.

This is a build-time writer only.  It imports immutable RP5C identity and
lineage facts, registers the explicit PR162D-R2A callable inventory, and
preserves the owner-supplied 213 requirements without inheriting the reverted
implementation's execution or equivalence claims.  It never reads private
state, executes connectors or QPUs, releases orders, or promotes a mode.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
from decimal import Decimal
import importlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc
from typing import Any, Callable, Iterable, Mapping, Sequence


REGISTRY_SCHEMA_VERSION = "1.0"
BUILDER_NAME = "tools/build_pr169_qku_comp_control1.py"
VALIDATOR_NAME = "tools/validate_pr169_qku_comp_control1.py"
GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_qku_comp_control1")

RP5C_PREFIX = Path("docs/master_plan/generated/rp5c")
RP5C_DEDUPE = RP5C_PREFIX / "identity_deduplication_ledger.jsonl"
RP5C_LINEAGE = RP5C_PREFIX / "qku_formula_identity_lineage.jsonl"
RP5C_CANONICAL_LIBRARY = RP5C_PREFIX / "immutable_qku_formula_library.jsonl"
RP5C_LIBRARIES = (
    RP5C_PREFIX / "immutable_qku_library.jsonl",
    RP5C_PREFIX / "immutable_formula_library.jsonl",
    RP5C_PREFIX / "immutable_qku_formula_library.jsonl",
)
RP5C_GROUP_CUSTODY_KEY_VERSION = "RP5C_SOURCE_GROUP_CUSTODY_KEY_V1"
RP5C_GROUP_KEY_FIELDS = (
    "identity_type",
    "qku_id",
    "formula_id",
    "formula_variant_id",
    "formula_expression_ref",
    "plugin_ref",
)
PR165_D2_ROSTER = Path(
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
)
PR162D_TEST_VECTOR_REGISTRY = Path(
    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json"
)

_CLOSED_FIXTURE_FORMULA_IDS = frozenset(
    {
        "IMPLIED_PROBABILITY",
        "PROBABILITY_EDGE",
        "MID_PRICE",
        "SPREAD",
        "RELATIVE_SPREAD",
    }
)

EXPECTED_RP5C_IDENTITIES = 10_189
EXPECTED_RP5C_OCCURRENCES = 183_802
EXPECTED_GFP_DISCOVERY_UNRESOLVED_ROWS = 20_115
EXPECTED_GFP_DISCOVERY_TEXTUAL_CONTAINMENT_HINT_ROWS = 5
EXPECTED_GFP_DISCOVERY_UNRESOLVED_BY_COHORT = {
    "MASTER_PLAN_DISCOVERY": 15_917,
    "POST_RP5C_DISCOVERY": 4_198,
}
EXPECTED_CANDIDATE_PACKET_SOURCE_ALTERNATIVES = 6_502
EXPECTED_CANDIDATE_PACKET_KNOWN_CONFLICTS = 63
EXPECTED_SOURCE_SELECTION_TUPLES = 9
EXPECTED_SOURCE_SELECTION_QKUS = 697
EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS = 12
EXPECTED_AGENT_REACHABLE_REFERENCE_OCCURRENCES = 110
EXPECTED_AGENT_REACHABLE_SELECTOR_KEYS = 110
PR162B_TEST_VECTOR_PATHS = (
    "docs/master_plan/generated/PR162B_QKUFormulaTestVectorRegistry.report.json",
    "docs/master_plan/generated/PR162B_QKUAlgorithmTestVectorRegistry.report.json",
)
PR162B_IMPLEMENTATION_MODULE_ALLOWLIST = (
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.prediction_market_formulas",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.calibration_formulas",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.risk_position_sizing_formulas",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.portfolio_objectives",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.technical_feature_formulas",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.quantum_formulations",
    "src.qtt.stage1_prediction_markets.qku_formula_algorithm_solver_market_scope_materialization.algorithm_registry",
)
GFP_IMPLEMENTATION_MODULE_ALLOWLIST = (
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.prediction_market_math",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.execution_costs",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.pnl",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.decision",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.tca",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.fill_queue_latency",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.overfit_controls",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.portfolio_utility",
    "src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.quantum_objectives",
)
RP5D_FORMULA_TO_PNL_CONTEXT_REF = (
    "RP5D_FORMULA_TO_PNL::BINARY_CONTRACT_CASH_PATH"
)
EXPECTED_FORMULA_IMPLEMENTATIONS = 61
EXPECTED_ALGORITHM_IMPLEMENTATIONS = 30
EXPECTED_QUANTUM_FORMULATIONS = 25
EXPECTED_QUANTUM_CALLABLE_FAMILIES = 9
EXPECTED_OWNER_REQUIREMENTS = 213
EXPECTED_CANONICAL_UNIQUE_QKUS = 9_425
EXPECTED_QKU_ROLE_KEYS = 9_645
EXPECTED_QKU_ROLE_OCCURRENCES = 10_023

QKU_VERIFICATION_RECEIPT_SCHEMA = "QKUVerificationReceiptV1"
QKU_VERIFICATION_STATES = frozenset(
    {
        "VERIFIED_BY_PRIMARY_EXTERNAL_SOURCE",
        "VERIFIED_BY_OFFICIAL_CURRENT_DOCUMENTATION",
        "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION",
        "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE",
        "VERIFIED_AS_QTT_INTERNAL_POLICY",
        "VERIFIED_AS_REPOSITORY_HISTORICAL_EVIDENCE",
        "NO_EXTERNAL_VERIFICATION_APPLICABLE",
        "UNRESOLVED_MATERIAL_BLOCKER",
        "REJECTED_INVALID_OR_CONTRADICTORY",
    }
)
QKU_INHERITANCE_SEMANTIC_FIELDS = (
    "component_kind",
    "complete_mathematical_or_procedural_definition",
    "objective_sense_or_null",
    "hard_constraints",
    "soft_preferences",
    "input_schema",
    "output_schema",
    "units_and_bases",
    "output_accounting_class",
    "assumptions",
    "domain_and_boundary_behavior",
    "state_and_time_semantics",
    "missing_stale_nonfinite_behavior",
    "precision_and_rounding",
    "parameter_schema_and_default_provenance",
    "requirements",
    "failure_domain_tags",
    "classical_fallback",
    "quantum",
)
_CLOSED_DECIMAL_PRIMARY_COMPONENTS = frozenset()
_CLOSED_DECIMAL_DERIVATION_COMPONENTS = frozenset(
    {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
        "QTT.COMP.FORMULA.PROBABILITY_EDGE",
        "QTT.COMP.FORMULA.MID_PRICE",
        "QTT.COMP.FORMULA.SPREAD",
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
    }
)
_CLOSED_DECIMAL_COMPONENTS = (
    _CLOSED_DECIMAL_PRIMARY_COMPONENTS
    | _CLOSED_DECIMAL_DERIVATION_COMPONENTS
)
_CLOSED_DECIMAL_PRICE_COMPONENTS = frozenset(
    {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
        "QTT.COMP.FORMULA.MID_PRICE",
        "QTT.COMP.FORMULA.SPREAD",
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
    }
)
_QKU_UNRESOLVED_PACK = "QKU.CLAIM.UNRESOLVED.V1"
_QKU_PRICE_PACK = "QKU.CLAIM.PRICE_QUOTE.V1"
_QKU_DECIMAL_PACK = "QKU.CLAIM.DECIMAL.V1"
_QKU_INSTITUTIONAL_PACK = "QKU.CLAIM.INSTITUTIONAL.V1"
_QKU_QUANTUM_PACK = "QKU.CLAIM.QUANTUM.V1"
_QKU_PROVIDER_PACK = "QKU.CLAIM.VENUE_PROVIDER.V1"
_CANDIDATE_FORMULA_PREFIX = "QTT.COMP.CANDIDATE.FORMULA."
_QKU_PRICE_COMPONENT_IDS = frozenset(
    _CANDIDATE_FORMULA_PREFIX + suffix
    for suffix in (
        "FAIR_PRICE_FROM_PROBABILITY",
        "IMPLIED_PROBABILITY_FROM_BINARY_PRICE",
        "POLY_SPREAD_001",
        "SPREAD",
    )
)
_QKU_INSTITUTIONAL_COMPONENT_IDS = frozenset(
    _CANDIDATE_FORMULA_PREFIX + suffix
    for suffix in (
        "BOLLINGER_BANDS", "BRIER_SCORE_BINARY", "CALIBRATION_ERROR_CANDIDATE",
        "CALIB_BRIER_001", "CALIB_ECE_001", "CAPPED_KELLY", "COVARIANCE",
        "EMA", "FDR_BH_001", "FDR_DSR_001",
        "FRACTIONAL_KELLY", "KELLY_FRACTION", "LOG_LOSS_BINARY", "MACD",
        "PORTFOLIO_QP_OBJECTIVE", "PORT_KELLY_001", "PORT_KELLY_002",
        "RSI", "TCA_001", "TCA_002",
    )
)
_QKU_QUANTUM_COMPONENT_IDS = frozenset(
    _CANDIDATE_FORMULA_PREFIX + suffix
    for suffix in (
        "ANNEALING_BQM_CQM_CANDIDATE", "BQM_ENERGY",
        "CQM_OBJECTIVE_AND_CONSTRAINTS", "EXPANDED_QUBO_TERMS",
        "ISING_ENERGY", "QAOA_HAMILTONIAN_MAPPING_CANDIDATE",
        "QUBO_OBJECTIVE_X_T_Q_X", "VQE_OBJECTIVE_CANDIDATE",
    )
)
_QKU_PROVIDER_COMPONENT_IDS = frozenset(
    _CANDIDATE_FORMULA_PREFIX + suffix
    for suffix in (
        "KALSHI_CANDLES_001", "KALSHI_CANDLES_002", "KALSHI_FEE_001",
        "KALSHI_ORDERBOOK_001", "KALSHI_ORDERBOOK_002",
        "KALSHI_ORDERBOOK_003", "KALSHI_TICK_001", "KALSHI_TRADES_001",
        "KALSHI_WS_001", "KALSHI_WS_002", "POLY_BOOK_001", "POLY_BOOK_002",
        "POLY_HISTORY_001", "POLY_LAST_001", "POLY_MID_001", "POLY_SPREAD_001",
        "POLY_TICK_001", "POLY_WS_001",
    )
)

# This is a build-time closure surface, not another registry.  Each entry names
# the exact current owner artifact whose rows are read and classified.  Sharded
# JSON reports are loaded only through their declared shard list; preview rows
# and manifest counts never substitute for value-level consumption.
SOURCE_UNIVERSE_ARTIFACTS: tuple[dict[str, Any], ...] = (
    {"cohort": "MAP3", "path": "docs/master_plan/generated/map3/formula_materialization_rows.jsonl", "role": "SEMANTIC_ROOT", "expected": 47, "key": "formula_id"},
    {"cohort": "MAP3", "path": "docs/master_plan/generated/map3/formula_ontology_rows.jsonl", "role": "QKU_ROLE", "expected": 47, "key": "formula_id"},
    {"cohort": "RP5D", "path": "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl", "role": "CONTEXT", "expected": 10_189, "key": "identity_ref"},
    {"cohort": "RP5D", "path": "docs/master_plan/generated/pr168_rp5d/rp5d_rp5c_vs1_crosswalk.jsonl", "role": "PROVENANCE_MAPPING", "expected": 10_189, "key": "identity_ref"},
    {"cohort": "FIXTURE_5", "path": "docs/master_plan/generated/pr168_rp5d_r1/calc_smoke.jsonl", "role": "CONTEXT", "expected": 5, "key": "calc_smoke_id"},
    {"cohort": "ADAPTER_READY_52", "path": "docs/master_plan/generated/pr168_rp5e/triage52.jsonl", "role": "CONTEXT", "expected": 52, "key": "triage52_id"},
    {"cohort": "PR162B", "path": "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json", "role": "SEMANTIC_ROOT", "expected": 61, "key": "formula_id"},
    {"cohort": "PR162B", "path": "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json", "role": "SEMANTIC_ROOT", "expected": 14, "key": "algorithm_id"},
    {"cohort": "PR162B", "path": "docs/master_plan/generated/PR162B_QKUFormulaTestVectorRegistry.report.json", "role": "SOURCE_TEST_VECTOR", "expected": 61, "key": "test_vector_id"},
    {"cohort": "PR162B", "path": "docs/master_plan/generated/PR162B_QKUAlgorithmTestVectorRegistry.report.json", "role": "SOURCE_TEST_VECTOR", "expected": 14, "key": "test_vector_id"},
    {"cohort": "PR162D", "path": "docs/master_plan/generated/PR162D_R2A_FormulationRecordRegistry.report.json", "role": "SEMANTIC_ROOT", "expected": 132, "key": "formulation_id"},
    {"cohort": "CANDIDATE_PACKET_6502", "path": "docs/master_plan/generated/PR162D_R2A_CandidatePacketV1Registry.report.json", "role": "CONTEXT", "expected": 6_502, "key": "candidate_packet_id"},
    {"cohort": "PR162E", "path": "docs/master_plan/generated/PR162E_PluginRegistry.report.json", "role": "CONTEXT", "expected": 559, "key": "plugin_id"},
    {"cohort": "QUANTUM_559", "path": "docs/master_plan/generated/PR162E_Q_ObjectiveMap.report.json", "role": "CONTEXT", "expected": 559, "key": "mapping_row_ref"},
    {"cohort": "GFP", "path": "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json", "role": "SEMANTIC_ROOT", "expected": 35, "key": "formula_id"},
    {"cohort": "GFP", "path": "docs/master_plan/generated/PR168_GFP_FormulaSourceArbitration.report.json", "role": "SOURCE_DISPOSITION", "expected": 44, "key": "formula_candidate_id"},
    {"cohort": "POSITIVE_EVIDENCE_150", "path": "docs/master_plan/generated/PR166_SM3_PosEvidence.report.json", "role": "EVIDENCE", "expected": 150, "key": "row_id"},
    {"cohort": "VALUE_GAPS_2852", "path": "docs/master_plan/generated/PR164_PR162D_R3RepairTriggerMatrix.report.json", "role": "CONTEXT", "expected": 2_852, "key": "downstream_route_record_ref"},
    {"cohort": "MASTER_PLAN_DISCOVERY", "path": "docs/master_plan/generated/PR168_GFP_MasterPlanFormulaCatalog.report.json", "role": "DISCOVERY", "expected": 15_917, "key": "formula_catalog_id"},
    {"cohort": "POST_RP5C_DISCOVERY", "path": "docs/master_plan/generated/PR168_GFP_PriorPRFormulaCatalog.report.json", "role": "DISCOVERY", "expected": 4_198, "key": "formula_catalog_id"},
    {"cohort": "MASTER_PLAN_CANDIDATES", "path": "docs/master_plan/generated/PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 80, "key": "candidate_id"},
    {"cohort": "MASTER_PLAN_CANDIDATES", "path": "docs/master_plan/generated/PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 42, "key": "candidate_id"},
    {"cohort": "POST_RP5C_CANDIDATES", "path": "docs/master_plan/generated/PR165_ExternalFormulaAndParameterCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 20, "key": "external_formula_parameter_ref"},
)

# Manifest-reachable current-owner projections are read row by row and
# dispositioned, but never copied into the runtime registry.  They close the
# semantic/reference surface that surrounds the compact roots above: contracts,
# units, requirements, implementations, fixture contexts, plugin/quantum maps,
# and QKU owner projections.  A projection label is not equivalence proof,
# readiness proof, or authority to promote the source row.
_MAP3_OWNER_PROJECTIONS = (
    ("formula_contract_rows.jsonl", 47, "formula_contract_row_id"),
    ("data_requirement_rows.jsonl", 47, "data_requirement_contract_ref"),
    ("unit_normalization_rows.jsonl", 47, "unit_normalization_contract_ref"),
    ("formula_dependency_rows.jsonl", 47, "formula_dependency_row_id"),
    ("formula_invariant_rows.jsonl", 47, "invariants_row_id"),
    ("property_test_rows.jsonl", 47, "property_tests_row_id"),
    ("formula_family_rows.jsonl", 14, "formula_family_matrix_row_id"),
    ("dedupe_quality_rows.jsonl", 47, "dedupe_row_id"),
    ("binding_registry_rows.jsonl", 47, "binding_registry_row_id"),
    ("formula_dryrun_rows.jsonl", 47, "formula_dryrun_row_id"),
    ("formula_factory_rows.jsonl", 47, "formula_factory_row_id"),
    ("external_intake_rows.jsonl", 47, "external_candidate_id"),
    ("source_tier_rows.jsonl", 47, "external_source_row_id"),
    ("source_triangulation_rows.jsonl", 14, "source_triangulation_row_id"),
    ("formula_provenance_rows.jsonl", 47, "formula_provenance_id"),
    ("quantum_mapping_rows.jsonl", 4, "qmap_row_id"),
    ("quantum_objective_rows.jsonl", 4, "qobjective_row_id"),
    ("quantum_fallback_rows.jsonl", 4, "qfallback_row_id"),
    ("quantum_lift_rows.jsonl", 4, "qformula_lift_row_id"),
    ("quantum_repair_rows.jsonl", 4, "qrepair_row_id"),
)


def _discover_map3_owner_projections() -> tuple[tuple[str, int, str], ...]:
    """Enumerate every manifest-backed MAP3 row surface from repository truth."""

    root = Path(__file__).resolve().parents[1] / "docs/master_plan/generated/map3"
    excluded_roots = {
        "formula_materialization_rows.jsonl",
        "formula_ontology_rows.jsonl",
    }
    discovered: list[tuple[str, int, str]] = []
    for manifest_path in sorted(root.glob("*.manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        name = manifest_path.name.removesuffix(".manifest.json")
        if name in excluded_roots:
            continue
        declared = next(
            (
                int(manifest[field])
                for field in (
                    "total_record_count",
                    "record_count",
                    "total_row_count",
                    "row_count",
                )
                if isinstance(manifest.get(field), int)
                and not isinstance(manifest.get(field), bool)
            ),
            -1,
        )
        if declared < 0:
            raise RuntimeError(
                f"MAP3 manifest lacks a declared row count: {manifest_path}"
            )
        discovered.append((name, declared, ""))
    if len(discovered) != 61 or sum(row[1] for row in discovered) != 3_207:
        raise RuntimeError(
            "MAP3 manifest discovery drift: "
            f"surfaces={len(discovered)}, rows={sum(row[1] for row in discovered)}"
        )
    return tuple(discovered)


# The two canonical root surfaces remain in SOURCE_UNIVERSE_ARTIFACTS; every
# other manifest-backed MAP3 row surface is an owner projection.
_MAP3_OWNER_PROJECTIONS = _discover_map3_owner_projections()

_RP5D_OWNER_PROJECTIONS = (
    ("rp5d_adapter_family_registry.jsonl", 21, "rp5d_adapter_family_row_id"),
    ("rp5d_agent_exec_queries.jsonl", 24, "executable_universe_query_receipt_ref"),
    ("rp5d_agent_exec_resolver.jsonl", 24, "resolver_ref"),
    ("rp5d_agent_route_queue.jsonl", 58, "adapter_queue_ref"),
    ("rp5d_blocker_policy_registry.jsonl", 26, "rp5d_blocker_policy_row_id"),
    ("rp5d_comp_state_registry.jsonl", 24, "state_ref"),
    ("rp5d_exec_state_registry.jsonl", 6, "state_ref"),
    ("rp5d_external_candidates.jsonl", 1, "external_acquisition_candidate_ref"),
    ("rp5d_external_research.jsonl", 1, "external_research_candidate_ref"),
    ("rp5d_no_mutation_proof.jsonl", 10_189, "no_mutation_proof_ref"),
    ("rp5d_no_orphan_qku_formula.jsonl", 10_189, "no_orphan_qku_formula_ref"),
    ("rp5d_policy_params.jsonl", 52, "rp5d_policy_parameter_row_id"),
    ("rp5d_source_coverage.jsonl", 1, "source_coverage_ref"),
    ("rp5d_stage_agent_exec_view.jsonl", 24, "stage_agent_exec_view_ref"),
    ("rp5d_computable_universe.jsonl", 2_001, "computable_universe_ref"),
    ("rp5d_contract_bundles.jsonl", 10_189, "contract_bundle_ref"),
    ("rp5d_exec_tiers.jsonl", 2_001, "tier_ref"),
    ("rp5d_qobj_constraint_ledger.jsonl", 2_001, "quantum_materialization_ref"),
    ("rp5d_quantum_compat.jsonl", 2_001, "quantum_compatibility_ref"),
    ("rp5d_stage1_coverage.jsonl", 2_001, "stage1_coverage_ref"),
    ("rp5d_universal_coverage.jsonl", 10_189, "coverage_ref"),
    ("rp5d_alpha_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_capacity_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_champion_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_hot_path_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_marginal_utility_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_no_trade_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_optimizer_readiness.jsonl", 2_001, "optimizer_readiness_ref"),
    ("rp5d_overfit_fdr_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_portfolio_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_rank_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_regime_memory_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_tca_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_trade_var_readiness.jsonl", 2_001, "readiness_ref"),
    ("rp5d_alpha_queue.jsonl", 1_838, "adapter_queue_ref"),
    ("rp5d_capacity_queue.jsonl", 1_989, "adapter_queue_ref"),
    ("rp5d_champion_queue.jsonl", 1_990, "adapter_queue_ref"),
    ("rp5d_classical_fb_queue.jsonl", 1_952, "adapter_queue_ref"),
    ("rp5d_fill_liquidity_queue.jsonl", 1_936, "adapter_queue_ref"),
    ("rp5d_formula_pnl_queue.jsonl", 1_949, "adapter_queue_ref"),
    ("rp5d_hot_path_queue.jsonl", 1_959, "adapter_queue_ref"),
    ("rp5d_input_queue.jsonl", 1_924, "adapter_queue_ref"),
    ("rp5d_latency_queue.jsonl", 1_959, "adapter_queue_ref"),
    ("rp5d_market_data_queue.jsonl", 1_852, "adapter_queue_ref"),
    ("rp5d_no_trade_queue.jsonl", 1_990, "adapter_queue_ref"),
    ("rp5d_overfit_fdr_queue.jsonl", 1_990, "adapter_queue_ref"),
    ("rp5d_portfolio_queue.jsonl", 1_658, "adapter_queue_ref"),
    ("rp5d_quantum_map_queue.jsonl", 1_065, "adapter_queue_ref"),
    ("rp5d_rank_queue.jsonl", 1_990, "adapter_queue_ref"),
    ("rp5d_regime_memory_queue.jsonl", 1_976, "adapter_queue_ref"),
    ("rp5d_scenario_queue.jsonl", 1_976, "adapter_queue_ref"),
    ("rp5d_tca_queue.jsonl", 1_948, "adapter_queue_ref"),
    ("rp5d_unit_queue.jsonl", 1_878, "adapter_queue_ref"),
)

_RP5D_R1_OWNER_PROJECTIONS = (
    ("fixture_bind.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("input_bind.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("unit_adapt.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("pnl_map.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("fee_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("spread_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("slip_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("fill_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("lat_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("capacity_ready.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("cash_settle.jsonl", 20, "row_id", "CONTEXTUAL_BINDING"),
    ("contract_matrix.jsonl", 20, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("contract_patch.jsonl", 324, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("tca_comp.jsonl", 20, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("params.jsonl", 33, "row_id", "INTERNAL_POLICY"),
    ("policy_prov.jsonl", 33, "row_id", "INTERNAL_POLICY"),
    ("exec_now_proof.jsonl", 5, "row_id", "REPOSITORY_HISTORICAL_EVIDENCE"),
    ("proof_tier.jsonl", 20, "row_id", "REPOSITORY_HISTORICAL_EVIDENCE"),
    ("research_rec.jsonl", 7, "row_id", "REPOSITORY_HISTORICAL_EVIDENCE"),
    ("q_struct_carry.jsonl", 5, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_solver_carry.jsonl", 5, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_interp_carry.jsonl", 5, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("edge_profit_map.jsonl", 52, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("rp5e_unlock_in.jsonl", 52, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("unlock_select.jsonl", 20, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("promote.jsonl", 5, "row_id", "REPOSITORY_HISTORICAL_EVIDENCE"),
    ("nonpromote.jsonl", 47, "row_id", "REPOSITORY_HISTORICAL_EVIDENCE"),
)

_RP5E_OWNER_PROJECTIONS = (
    ("roles.jsonl", 12, "row_id", "INTERNAL_POLICY"),
    ("templates.jsonl", 3, "row_id", "INTERNAL_POLICY"),
    ("params.jsonl", 28, "row_id", "INTERNAL_POLICY"),
    ("policy_prov.jsonl", 28, "row_id", "INTERNAL_POLICY"),
    ("ctx_pools.jsonl", 3, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("ctx_univ.jsonl", 3, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("qku_guard.jsonl", 52, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("tmp_previews.jsonl", 52, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("topk.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_obj.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_coeffs.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_interp.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_solver.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("q_tags.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("unlock_pri.jsonl", 52, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("features.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("edge_feats.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("exec_prev.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("classic.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("tca_ready.jsonl", 50, "row_id", "CONTEXT_RESOLVED_PREVIEW"),
    ("default_cand.jsonl", 3, "row_id", "INTERNAL_POLICY"),
    ("calib_queue.jsonl", 3, "row_id", "INTERNAL_POLICY"),
    ("eph_contracts.jsonl", 1, "row_id", "CONTEXTUAL_BINDING"),
    ("no_hardcode.jsonl", 1, "row_id", "INTERNAL_POLICY"),
)

_PR162B_OWNER_PROJECTIONS = (
    ("PR162B_QKUConstraintRegistry.report.json", 6, "constraint_id"),
    ("PR162B_QKUObjectiveFunctionRegistry.report.json", 8, "objective_id"),
    ("PR162B_QKUParameterRangeScaleRegistry.report.json", 19, "parameter_range_scale_id"),
    ("PR162B_QKUParameterValueRegistry.report.json", 19, "parameter_id"),
    ("PR162B_QKUTradableValueCandidateRegistry.report.json", 19, "tradable_value_id"),
    ("PR162B_QKUFormulaImplementationBindingRegistry.report.json", 61, "binding_id"),
    ("PR162B_QKUExecutableComputeContractRegistry.report.json", 75, "compute_contract_id"),
    ("PR162B_QuantumQUBOIsingFormulaMaterialization.report.json", 156, "materialization_id"),
    ("PR162B_QuantumSolverSmokeExecutionReport.report.json", 3, "smoke_id"),
    ("PR162B_QKUExecutionClassificationAudit.report.json", 9_360, "record_id"),
    ("PR162B_QKUMarketClassificationRegistry.report.json", 9_360, "record_id"),
    ("PR162B_QKUStage1PredictionMarketActivationGate.report.json", 9_360, "activation_gate_id"),
    ("PR162B_QKUDormancyRegistry.report.json", 2_227, "dormancy_id"),
    ("PR162B_QKUTradeRoleRegistry.report.json", 9_360, "trade_role_record_id"),
    ("PR162B_QKUMarketInputFieldRequirementMatrix.report.json", 9_360, "input_field_requirement_id"),
    ("PR162B_QKUFormulaCoverageAudit.report.json", 9_360, "formula_coverage_id"),
    ("PR162B_QKUSolverMappingRegistry.report.json", 4_631, "solver_mapping_id"),
    ("PR162B_QKUFormulaBindingProofMatrix.report.json", 4_695, "binding_proof_id"),
    ("PR162B_LiveModeFormulaGateStatus.report.json", 9_360, "live_gate_id"),
    ("PR162B_MetadataOnlyBlockerAudit.report.json", 2_227, "metadata_blocker_id"),
    ("PR162B_PR162CDataRequirementHandoff.report.json", 6_502, "handoff_id"),
    ("PR162B_AgentFormulaConsumerRoutingMatrix.report.json", 169, "route_id"),
    ("PR162B_FormulaSourceRetrievalTargetMatrix.report.json", 9, "retrieval_target_id"),
    ("PR162B_QKUMarketClassificationCoverageAudit.report.json", 7, "coverage_audit_id"),
    ("PR162B_QTTAgentStage1QKUActivationAllowlist.report.json", 16, "record_id"),
)

_PR162D_OWNER_PROJECTIONS = (
    ("PR162D_R2A_FormulaExpressionRegistry.report.json", 61, "formula_id"),
    ("PR162D_R2A_AlgorithmProcedureRegistry.report.json", 30, "algorithm_id"),
    ("PR162D_R2A_QuantumObjectiveRegistry.report.json", 25, "quantum_formulation_id"),
    ("PR162D_R2A_ClassicalComparatorRegistry.report.json", 25, "classical_comparator_id"),
    ("PR162D_R2A_TestVectorRegistry.report.json", 157, "test_vector_id"),
    ("PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json", 129, "hierarchy_id"),
    ("PR162D_R2A_PR162RGenericCandidateInputExtension.report.json", 6_502, "pr162r_input_id"),
    ("PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json", 132, "plugin_seed_id"),
    ("PR162D_R2A_FormulaLatencyClassRegistry.report.json", 132, "latency_record_id"),
    ("PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json", 132, "hotpath_record_id"),
    ("PR162D_R2A_LatencySensitiveCandidateQueue.report.json", 73, "latency_queue_id"),
    ("PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json", 6_502, "orchestration_id"),
    ("PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json", 6_502, "traceability_id"),
    ("PR162D_R2A_CandidateIntakeLaneMatrix.report.json", 6_502, "candidate_packet_id"),
    ("PR162D_R2A_FormulaPluginSeedRegistry.report.json", 77, "plugin_seed_id"),
    ("PR162D_R2A_AlgorithmPluginSeedRegistry.report.json", 30, "plugin_seed_id"),
    ("PR162D_R2A_QuantumPluginSeedRegistry.report.json", 25, "plugin_seed_id"),
    ("PR162D_R2A_FormulaVersionAndRollbackSeedLedger.report.json", 132, "version_seed_id"),
    ("PR162D_R2A_FormulaEquivalenceDedupeMatrix.report.json", 58, "dedupe_record_id"),
    ("PR162D_R2A_MaterializationExpansionPriorityQueue.report.json", 1_000, "priority_record_id"),
    ("PR162D_R2A_FormulationCoverageAudit.report.json", 1, "record_id"),
    ("PR162D_R2A_HumanReviewTopFormulations.report.json", 1, "record_id"),
    ("PR162D_R2A_OnlineSourceSearchQueue.report.json", 9, "source_locator_id"),
)

_PR162E_OWNER_PROJECTIONS = (
    ("PR162E_PluginFamilyRegistry.report.json", 95, "row_id"),
    ("PR162E_FormulaPluginInterface.report.json", 6, "row_id"),
    ("PR162E_AlgorithmPluginInterface.report.json", 6, "row_id"),
    ("PR162E_QuantumRecipePluginInterface.report.json", 6, "row_id"),
    ("PR162E_PluginVersionLedger.report.json", 559, "row_id"),
    ("PR162E_PluginRollbackLedger.report.json", 559, "row_id"),
    ("PR162E_PluginEquivalenceDedupe.report.json", 559, "row_id"),
    ("PR162E_PluginCompatibilityMatrix.report.json", 559, "row_id"),
    ("PR162E_PluginDependencyDAG.report.json", 559, "row_id"),
    ("PR162E_PluginRuntimeBudget.report.json", 559, "row_id"),
    ("PR162E_PluginFailClosed.report.json", 559, "row_id"),
    ("PR162E_PluginTestVectors.report.json", 559, "row_id"),
    ("PR162E_PluginValidator.report.json", 559, "row_id"),
    ("PR162E_PluginChampChallenger.report.json", 559, "row_id"),
    ("PR162E_PluginRepairQueue.report.json", 389, "row_id"),
    ("PR162E_RepairedCandidateToPluginMap.report.json", 389, "row_id"),
    ("PR162E_ExternalCandidateIntake.report.json", 12, "row_id"),
    ("PR162E_ExternalCandidateDedup.report.json", 12, "row_id"),
    ("PR162E_ExternalCandidateToPluginMap.report.json", 12, "row_id"),
    ("PR162E_ExternalCandidateRepairFill.report.json", 12, "row_id"),
    ("PR162E_AgentDutyBinding.report.json", 559, "row_id"),
    ("PR162E_QKUFormulaAlgorithmLineage.report.json", 559, "row_id"),
    ("PR162E_ValueLineageMap.report.json", 559, "row_id"),
    ("PR162E_ExternalCandidateLineage.report.json", 12, "row_id"),
)

_PR162E_Q_OWNER_PROJECTIONS = tuple(
    (name, 559, "mapping_row_ref")
    for name in (
        "PR162E_Q_MapEligibility.report.json",
        "PR162E_Q_FormulaObjectiveCanonical.report.json",
        "PR162E_Q_UnitNorm.report.json",
        "PR162E_Q_ModelFamilySelection.report.json",
        "PR162E_Q_VariableEncoding.report.json",
        "PR162E_Q_SolutionInterpretBack.report.json",
        "PR162E_Q_ConstraintMap.report.json",
        "PR162E_Q_PenaltyMap.report.json",
        "PR162E_Q_CoeffScaling.report.json",
        "PR162E_Q_QUBORecipe.report.json",
        "PR162E_Q_BQMRecipe.report.json",
        "PR162E_Q_IsingRecipe.report.json",
        "PR162E_Q_CQMRecipe.report.json",
        "PR162E_Q_DQMRecipe.report.json",
        "PR162E_Q_QuadProgramRecipe.report.json",
        "PR162E_Q_HybridRecipe.report.json",
        "PR162E_Q_TestVectors.report.json",
        "PR162E_Q_MapProof.report.json",
        "PR162E_Q_FeasibilityChecks.report.json",
        "PR162E_Q_ComplexityEstimate.report.json",
        "PR162E_Q_SparsityEmbedding.report.json",
        "PR162E_Q_MapQuality.report.json",
        "PR162E_Q_MapSensitivityStress.report.json",
    )
)

_PR162E_Q_OWNER_PROJECTIONS = (
    *_PR162E_Q_OWNER_PROJECTIONS,
    ("PR162E_Q_SourceMapParams.report.json", 12, "row_id"),
    ("PR162E_Q_MapBudget.report.json", 1, "row_id"),
    *(
        (name, 559, "mapping_row_ref")
        for name in (
            "PR162E_Q_EdgeAttribution.report.json",
            "PR162E_Q_MapFairnessNorm.report.json",
            "PR162E_Q_ExecutionAdjustedMapRank.report.json",
            "PR162E_Q_TCAMapImpact.report.json",
            "PR162E_Q_OverfitFDRMapRisk.report.json",
            "PR162E_Q_PortfolioUtilityMap.report.json",
            "PR162E_Q_ChampChallengerMap.report.json",
            "PR162E_Q_RegimeMapMemory.report.json",
            "PR162E_Q_StillNegativeMapRepair.report.json",
            "PR162E_Q_ReplayPaperRetestMap.report.json",
            "PR162E_Q_OpenTradeSimMap.report.json",
            "PR162E_Q_OwnerDashboardMapReview.report.json",
            "PR162E_Q_ConnectorRouteReady.report.json",
            "PR162E_Q_MarketPortability.report.json",
        )
    ),
)

_GFP_OWNER_PROJECTIONS = (
    ("PR168_GFP_FormulaFamilySearchMatrix.report.json", 35, "selected_formula_id"),
    ("PR168_GFP_FormulaDiscoveryCoverageAudit.report.json", 35, "formula_family"),
    ("PR168_GFP_RequiredFormulaSetMap.report.json", 5, "required_formula_set_id"),
    ("PR168_GFP_MasterPlanFormulaCoverageAudit.report.json", 35, "selected_formula_id"),
    ("PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json", 20_115, "formula_catalog_id"),
    ("PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json", 11_437, "formula_catalog_id"),
    ("PR168_GFP_FormulaAssignmentMatrix.report.json", 20_387, "source_row_pointer"),
    ("PR168_GFP_QKUComputationCoverage.report.json", 9_360, "canonical_row_key"),
    ("PR168_GFP_CandidatePacketV1ComputationCoverage.report.json", 6_502, "canonical_row_key"),
    ("PR168_GFP_AtomicRowsComputationCoverage.report.json", 4_183, "canonical_row_key"),
    ("PR168_GFP_CanonicalRowKeyMap.report.json", 20_387, "source_row_pointer"),
)

SOURCE_OWNER_PROJECTION_ARTIFACTS: tuple[dict[str, Any], ...] = (
    *(
        {"cohort": "MAP3", "path": f"docs/master_plan/generated/map3/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_SEMANTIC_PROJECTION"}
        for name, count, key in _MAP3_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "RP5D", "path": f"docs/master_plan/generated/pr168_rp5d/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_CONTEXTUAL_READINESS_PROJECTION"}
        for name, count, key in _RP5D_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "RP5D_R1", "path": f"docs/master_plan/generated/pr168_rp5d_r1/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": disposition}
        for name, count, key, disposition in _RP5D_R1_OWNER_PROJECTIONS
    ),
    {
        "cohort": "RP5D_R1_OWNER_CONTEXT",
        "path": "docs/master_plan/generated/pr168_rp5d_r1/source_req.jsonl",
        "role": "OWNER_CONTEXT",
        "expected": 15,
        "key": "row_id",
        "projection_disposition": "SOURCE_READINESS_BLOCKER_RETAINED_WITH_OWNER",
    },
    *(
        {"cohort": "RP5E", "path": f"docs/master_plan/generated/pr168_rp5e/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": disposition}
        for name, count, key, disposition in _RP5E_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "PR162B", "path": f"docs/master_plan/generated/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_QKU_SEMANTIC_PROJECTION"}
        for name, count, key in _PR162B_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "PR162D", "path": f"docs/master_plan/generated/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_IMPLEMENTATION_OR_CONTEXT_PROJECTION"}
        for name, count, key in _PR162D_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "PR162E", "path": f"docs/master_plan/generated/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_PLUGIN_PROJECTION"}
        for name, count, key in _PR162E_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "QUANTUM_559", "path": f"docs/master_plan/generated/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_QUANTUM_MAPPING_PROJECTION"}
        for name, count, key in _PR162E_Q_OWNER_PROJECTIONS
    ),
    *(
        {"cohort": "GFP", "path": f"docs/master_plan/generated/{name}", "role": "OWNER_PROJECTION", "expected": count, "key": key, "projection_disposition": "SOURCE_OWNER_DISCOVERY_CROSSWALK_PROJECTION"}
        for name, count, key in _GFP_OWNER_PROJECTIONS
    ),
)

SOURCE_CLOSURE_ARTIFACTS = SOURCE_UNIVERSE_ARTIFACTS + SOURCE_OWNER_PROJECTION_ARTIFACTS

_SEMANTIC_CORE_FIELDS = (
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
)

# This inventory is owner-supplied requirement evidence.  Only card identity,
# family, and requested name were inspected from the negative-regression PR;
# none of its callable, alias, PASS, route, or implementation claims survive.
_OWNER_REQUIREMENT_TEXT = (
    "A01=TOTAL_REALIZED_NET_CASH A02=BRANCH_NET_CASH A03=EXPECTED_NET_CASH_SCENARIO A04=ROBUST_NET_CASH_INTERVAL A05=NET_CASH_LCB_UCB A06=NET_CASH_VELOCITY A07=CAPITAL_TIME_EFFICIENCY A08=REQUIRED_EXIT_PROFIT A09=DEPTH_WALK_SELL_PROCEEDS A10=DEPTH_WALK_BUY_COST A11=EXECUTABLE_EXIT_NET_CASH A12=FILL_ADJUSTED_EXECUTABLE_NET_CASH A13=PARTIAL_HARVEST_NET_CASH A14=PNL_STATE_CLASSIFICATION A15=EXIT_NOW_VALUE A16=CONTINUE_HOLDING_VALUE A17=HOLD_TO_SETTLEMENT_VALUE A18=HEDGE_OFFSET_VALUE A19=REVERSE_VALUE A20=FORWARD_ACTION_VALUE A21=CONTINUATION_HYSTERESIS A22=REENTRY_EDGE_HURDLE A23=CAPITAL_OPPORTUNITY_COST A24=RISK_RESERVE_HURDLE A25=NO_TRADE_MARGIN A26=CAMPAIGN_CASH_AGGREGATES A27=CAMPAIGN_CAPACITY_FRONTIER A28=CAMPAIGN_REMAINING_CAPACITY A29=EVIDENCE_STOP_STATISTICS A30=VENUE_FEE_GENERIC A31=FEE_CURVE_PRODUCT A32=MAKER_REBATE_SHARE A33=NET_QUOTE_UTILITY "
    "B01=IMPLEMENTATION_SHORTFALL B02=TCA_DECOMPOSITION_RECONCILIATION B03=EFFECTIVE_ARRIVAL_PRICE B04=REALIZED_SPREAD B05=SIGNED_MARKOUT B06=SPREAD_COST B07=DEPTH_IMPACT B08=LATENCY_DECAY_COST B09=FILL_SURVIVAL_HAZARD B10=QUEUE_AHEAD_DEPLETION B11=ORDERBOOK_IMBALANCE B12=MICROPRICE B13=ORDER_FLOW_IMBALANCE B14=HAWKES_INTENSITY_CANDIDATE B15=MAKER_TAKER_ROUTE_UTILITY B16=CANCEL_REPLACE_VALUE B17=AVELLANEDA_STOIKOV_RESERVATION_PRICE B18=AVELLANEDA_STOIKOV_HALF_SPREAD B19=INVENTORY_SKEW B20=RATE_LIMIT_BUDGET B21=ORDER_GROUP_ROLLING_USAGE "
    "C01=BRIER_SCORE C02=LOG_LOSS C03=EXPECTED_CALIBRATION_ERROR C04=CALIBRATION_SLOPE_INTERCEPT C05=WEIGHTED_EFFECTIVE_SAMPLE_SIZE C06=AUTOCORRELATION_EFFECTIVE_SAMPLE_SIZE C07=CLUSTER_EVENT_EFFECTIVE_SAMPLE_SIZE C08=DEPENDENCE_AWARE_BOOTSTRAP_LCB C09=ANYTIME_EVIDENCE_PROCESS C10=BENJAMINI_HOCHBERG_FDR C11=BENJAMINI_YEKUTIEL_FDR C12=PROBABILISTIC_SHARPE_RATIO C13=DEFLATED_SHARPE_RATIO C14=PBO_CSCV C15=WHITE_REALITY_CHECK C16=HANSEN_SPA C17=STEPM_MULTIPLE_COMPARISON C18=MODEL_CONFIDENCE_SET C19=PAIRED_CHALLENGER_DELTA C20=RANK_STABILITY C21=PROBABILITY_OF_POSITIVE_NET_CASH C22=MINIMUM_TRACK_RECORD_LENGTH C23=CONFORMAL_INTERVAL_CANDIDATE C24=TRIAL_FAMILY_EFFECTIVE_COUNT C25=DIFFERENTIAL_SHARPE "
    "D01=FINANCIAL_LOSS_CVAR D02=ROBUST_CVAR D03=MEAN_VARIANCE_UTILITY D04=MARGINAL_RISK_CONTRIBUTION D05=EXPOSURE_HERFINDAHL D06=DIVERSIFICATION_ENTROPY D07=CORRELATION_INTERACTION_PENALTY D08=FRACTIONAL_KELLY_ROBUST D09=MAX_DRAWDOWN D10=CAPITAL_UTILIZATION D11=PORTFOLIO_MARGINAL_UTILITY D12=CAPITAL_TIME_ROTATION D13=EVENT_EXPOSURE_NETTING D14=TIME_BUCKET_CAPITAL D15=ENTROPIC_RISK_CANDIDATE D16=DISTRIBUTIONALLY_ROBUST_UTILITY D17=LEXICOGRAPHIC_ECONOMIC_OBJECTIVE D18=EPSILON_CONSTRAINED_PARETO D19=CONDITION_SCOPED_SHRINKAGE D20=CHAMPION_CHALLENGER_REGRET D21=VALUE_OF_INFORMATION D22=EXPERIMENT_DESIGN_UTILITY D23=IPS_OFF_POLICY_VALUE D24=SNIPS_OFF_POLICY_VALUE D25=DOUBLY_ROBUST_POLICY_VALUE D26=NO_TRADE_RECOVERY_DISTANCE D27=REGIME_ROBUSTNESS D28=AGENT_DISAGREEMENT_VECTOR D29=PARETO_DOMINANCE D30=ADAPTIVE_SEARCH_BUDGET "
    "E01=COMPLETE_SET_BUY_MARGIN E02=COMPLETE_SET_SELL_MARGIN E03=OUTCOME_SUM_CONSISTENCY E04=COMPLEMENT_CONSISTENCY E05=LOGICAL_IMPLICATION E06=INTERSECTION_BOUND E07=DATE_MONOTONICITY E08=SUBSET_SUPERSET E09=CROSS_VENUE_PARITY_MARGIN E10=SIMULTANEOUS_FILL_PROBABILITY E11=BASKET_EXECUTABLE_UTILITY E12=LOGICAL_ARBITRAGE_HYPERGRAPH_OBJECTIVE "
    "F01=DISCRETE_TRADE_ALTERNATIVE_SELECTION F02=QUANTUM_ROBUST_ECONOMIC_OBJECTIVE F03=QUBO_CANONICAL F04=BQM_CANONICAL F05=QUBO_TO_ISING F06=COEFFICIENT_SCALING F07=PENALTY_SUFFICIENCY F08=ONE_HOT_CONSTRAINT F09=FIXED_CARDINALITY_CONSTRAINT F10=BOUNDED_BINARY_ENCODING F11=UNARY_ENCODING F12=MIXED_RADIX_ENCODING F13=GRAY_CODE_ENCODING F14=DOMAIN_WALL_ENCODING F15=QAOA_EXPECTATION F16=WARM_START_QAOA_ANGLE F17=VARIATIONAL_CVAR_AGGREGATOR F18=SAMPLE_SELECTION_MARGINAL F19=SAMPLE_PAIRWISE_COSELECTION F20=SOLUTION_ENTROPY F21=HAMMING_DIVERSITY F22=NEAR_OPTIMAL_CLUSTER_COUNT F23=SELECTION_OVERLAP F24=OBJECTIVE_GAP F25=ECONOMIC_UTILITY_GAP F26=CONSTRAINT_DISAGREEMENT F27=PORTFOLIO_EXPOSURE_DISAGREEMENT F28=TRADE_PLAN_DISAGREEMENT F29=COEFFICIENT_STRESS_SENSITIVITY F30=QUANTUM_SOLUTION_FRAGILITY F31=QUANTUM_REGIME_ROBUSTNESS F32=QUANTUM_ECONOMIC_UTILITY F33=QPU_IMPROVEMENT_PER_COST F34=QPU_IMPROVEMENT_PER_SECOND F35=QUANTUM_VALUE_OF_INFORMATION F36=QAE_NORMALIZED_EXPECTATION F37=QAE_TAIL_PROBABILITY F38=QAE_CVAR_CANDIDATE F39=FEASIBLE_SAMPLE_RATE F40=CHAIN_BREAK_FRACTION F41=TIME_TO_FIRST_FEASIBLE F42=TIME_TO_BEST F43=EMBEDDING_GAUGE_STABILITY F44=REVERSE_ANNEAL_IMPROVEMENT F45=POSTPROCESSING_IMPROVEMENT F46=QUANTUM_RESOURCE_ESTIMATE "
    "G01=SHRINKAGE_COVARIANCE G02=COMPONENT_CVAR G03=RISK_BUDGET_PARITY_OBJECTIVE G04=SQUARE_ROOT_MARKET_IMPACT_CANDIDATE G05=EXECUTION_SCHEDULE_MEAN_VARIANCE G06=CUSUM_DRIFT_STATISTIC G07=BAYESIAN_MODEL_AVERAGING_WEIGHT G08=ENTROPY_REGULARIZED_ALLOCATION G09=OPTIMIZATION_TARGET_SUCCESS_RATE G10=QUANTUM_TIME_TO_SOLUTION G11=MITIGATION_VARIANCE_OVERHEAD G12=NEYMAN_SHOT_ALLOCATION G13=BACKEND_CALIBRATION_DRIFT_VECTOR G14=PARETO_HYPERVOLUME_IMPROVEMENT "
    "H01=COHERENT_PROBABILITY_QP_PROJECTION H02=DATE_LADDER_ISOTONIC_PROJECTION H03=EXECUTABLE_BREAK_EVEN_PROBABILITY H04=CALIBRATED_EXECUTABLE_EDGE_LCB H05=LIQUIDITY_ADJUSTED_CVAR H06=WORST_CASE_REGRET H07=COMPETING_RISKS_FILL_CIF H08=FORMULATION_EQUIVALENCE_RESIDUAL H09=PENALTY_DOMINANCE_RATIO H10=QUANTUM_CONTRIBUTION_ATTRIBUTION H11=PROBLEM_FINGERPRINT_DISTANCE H12=VARIATIONAL_GRADIENT_SNR H13=QPU_RESULT_EXPIRY_PROBABILITY H14=SCENARIO_CASHFLOW_RECONCILIATION_RESIDUAL "
    "I01=AGENT_STAGE_QKU_UNIVERSE I02=AGENT_EXECUTABLE_QKU_UNIVERSE I03=CONTEXT_CANDIDATE_QKU_UNIVERSE I04=FORMULA_INPUT_RESOLUTION_COVERAGE I05=CONTEXT_RECIPE_SIMILARITY I06=RECIPE_PRIOR_UTILITY I07=FORMULA_RESULT_FRESHNESS I08=END_TO_END_DECISION_LATENCY I09=LATENCY_BUDGET_SLACK I10=FORMULA_WORK_ITEM_PRIORITY_VECTOR "
    "J01=WASSERSTEIN_ROBUST_UTILITY J02=CHANCE_CONSTRAINED_FEASIBILITY J03=DISTRIBUTION_SHIFT_TEST J04=LOG_DETERMINANT_DIVERSITY J05=RARE_EVENT_IMPORTANCE_SAMPLING J06=PRIMAL_DUAL_OPTIMALITY_CERTIFICATE J07=CERTIFIED_QUBO_SPARSIFICATION_QUANTIZATION J08=SYMMETRY_BREAKING_ORBIT_REDUCTION"
)


class BuildError(RuntimeError):
    """Fail-closed deterministic builder error."""


class _Deadline:
    def __init__(self, timeout_ms: int) -> None:
        if timeout_ms <= 0:
            raise BuildError("timeout_ms must be positive")
        self._deadline = time.monotonic() + timeout_ms / 1000.0

    def check(self, operation: str) -> None:
        if time.monotonic() > self._deadline:
            raise TimeoutError(f"CONTROL1 builder timeout during {operation}")


def _json_line(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"


def _stable_json_value(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _sorted_unique_values(values: Iterable[Any]) -> list[Any]:
    """Canonicalize only record collections whose order has no semantics."""

    by_value: dict[str, Any] = {}
    for value in values:
        copied = copy.deepcopy(value)
        by_value.setdefault(_stable_json_value(copied), copied)
    return [by_value[key] for key in sorted(by_value)]


def _normalize_compiler_candidate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Match the compiler's reuse normalization on the first admission.

    This is syntactic input normalization, not an admission or merge path.  It
    prevents a record first admitted by the private compiler from changing on
    the next identical batch solely because reuse canonicalizes unordered
    metadata collections.
    """

    normalized = copy.deepcopy(dict(record))
    normalized["origin_cohorts"] = sorted(
        {str(value) for value in normalized.get("origin_cohorts", [])}
    )
    for field_name in ("provenance", "relations"):
        normalized[field_name] = _sorted_unique_values(
            normalized.get(field_name, [])
        )
    uses = normalized.get("uses")
    if isinstance(uses, dict):
        for field_name in (
            "decision_roles",
            "decision_outputs",
            "market_family_tags",
            "qku_role_bindings",
            "consumer_class_tags",
        ):
            uses[field_name] = _sorted_unique_values(uses.get(field_name, []))
    definition = normalized.get("definition")
    if isinstance(definition, dict):
        for field_name in (
            "implementation_versions",
            "oracle_and_test_refs",
            "equivalence_proof_refs",
        ):
            definition[field_name] = _sorted_unique_values(
                definition.get(field_name, [])
            )
    bindings = normalized.get("bindings", [])
    if isinstance(bindings, list):
        normalized["bindings"] = sorted(
            bindings,
            key=lambda value: (
                str(value.get("binding_id", ""))
                if isinstance(value, Mapping)
                else "",
                _stable_json_value(value),
            ),
        )
    return normalized


def _iter_jsonl(path: Path, deadline: _Deadline) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        raise BuildError(f"required source is missing: {path.as_posix()}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 10_000 == 0:
                deadline.check(path.name)
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise BuildError(
                    f"invalid JSONL at {path.as_posix()}:{line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise BuildError(
                    f"non-object JSONL row at {path.as_posix()}:{line_number}"
                )
            yield value


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise BuildError(f"required source is missing: {path.as_posix()}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BuildError(f"required object JSON source is invalid: {path.as_posix()}")
    return value


def _declared_count(payload: Mapping[str, Any], path: Path) -> int:
    for field in ("total_record_count", "record_count", "total_row_count", "row_count"):
        value = payload.get(field)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    raise BuildError(f"source artifact has no declared row count: {path.as_posix()}")


def _declared_shard_paths(payload: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for field in ("shard_files", "shard_paths"):
        candidate = payload.get(field, [])
        if isinstance(candidate, str):
            candidate = [candidate]
        if isinstance(candidate, list):
            values.extend(str(item) for item in candidate if isinstance(item, str) and item)
    summary = payload.get("summary")
    if isinstance(summary, Mapping):
        for field in ("shard_files", "shard_paths"):
            candidate = summary.get(field, [])
            if isinstance(candidate, str):
                candidate = [candidate]
            if isinstance(candidate, list):
                values.extend(
                    str(item) for item in candidate if isinstance(item, str) and item
                )
    return tuple(dict.fromkeys(values))


def _read_source_artifact_rows(
    repo_root: Path,
    relative_path: str | Path,
    deadline: _Deadline,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read every declared row and reject count-only or preview-only consumption."""

    relative = Path(relative_path)
    path = repo_root / relative
    if path.suffix.lower() == ".jsonl":
        rows = list(_iter_jsonl(path, deadline))
        adjacent_candidates = (
            path.with_name(f"{path.name}.manifest.json"),
            path.with_suffix(".manifest.json"),
        )
        manifest_path = next(
            (candidate for candidate in adjacent_candidates if candidate.is_file()),
            None,
        )
        if manifest_path is None:
            raise BuildError(f"JSONL source lacks adjacent manifest: {relative.as_posix()}")
        manifest = _read_json(manifest_path)
        declared = _declared_count(manifest, manifest_path)
        if len(rows) != declared:
            raise BuildError(
                f"source row count drift: {relative.as_posix()} {len(rows)} != {declared}"
            )
        return rows, {
            "declared_rows": declared,
            "actual_rows_read": len(rows),
            "physical_files_read": [relative.as_posix(), manifest_path.relative_to(repo_root).as_posix()],
            "preview_rows_ignored": 0,
            "manifest_count_used_as_value_consumption": False,
        }

    root = _read_json(path)
    declared = _declared_count(root, path)
    shard_paths = _declared_shard_paths(root)
    root_records = root.get("records", [])
    if not isinstance(root_records, list):
        raise BuildError(f"source records field is not a list: {relative.as_posix()}")
    rows: list[dict[str, Any]] = []
    files = [relative.as_posix()]
    preview_ignored = 0
    if shard_paths:
        preview_ignored = len(root_records)
        seen_paths: set[str] = set()
        for shard_text in shard_paths:
            shard_path = Path(shard_text)
            if not shard_path.is_absolute():
                shard_path = repo_root / shard_path
            resolved = shard_path.resolve()
            try:
                shard_relative = resolved.relative_to(repo_root.resolve()).as_posix()
            except ValueError as exc:
                raise BuildError(f"source shard escapes repository: {shard_text}") from exc
            if shard_relative in seen_paths:
                raise BuildError(f"duplicate declared source shard: {shard_relative}")
            seen_paths.add(shard_relative)
            shard = _read_json(resolved)
            shard_records = shard.get("records", [])
            if not isinstance(shard_records, list):
                raise BuildError(f"source shard records are invalid: {shard_relative}")
            shard_declared_value = shard.get("record_count", shard.get("row_count"))
            shard_declared = (
                int(shard_declared_value)
                if isinstance(shard_declared_value, int)
                and not isinstance(shard_declared_value, bool)
                else _declared_count(shard, resolved)
            )
            if len(shard_records) != shard_declared:
                raise BuildError(
                    f"source shard row count drift: {shard_relative} "
                    f"{len(shard_records)} != {shard_declared}"
                )
            for row in shard_records:
                if not isinstance(row, dict):
                    raise BuildError(f"source shard has non-object row: {shard_relative}")
                rows.append(row)
            files.append(shard_relative)
            deadline.check(f"source shard {Path(shard_relative).name}")
    else:
        for row in root_records:
            if not isinstance(row, dict):
                raise BuildError(f"source report has non-object row: {relative.as_posix()}")
            rows.append(row)
    if len(rows) != declared:
        raise BuildError(
            f"source report row count drift: {relative.as_posix()} {len(rows)} != {declared}"
        )
    return rows, {
        "declared_rows": declared,
        "actual_rows_read": len(rows),
        "physical_files_read": files,
        "preview_rows_ignored": preview_ignored,
        "manifest_count_used_as_value_consumption": False,
    }


def _select_source_row_key_field(
    rows: Sequence[Mapping[str, Any]], path: str
) -> str:
    """Select a stable existing owner key; never manufacture a digest identity."""

    if not rows:
        return "__EMPTY_OWNER_SURFACE__"
    fields = sorted({str(field) for row in rows for field in row})
    preferred = sorted(
        fields,
        key=lambda field: (
            0
            if field in {"row_id", "record_id", "canonical_row_key"}
            else 1
            if field.endswith("_row_id") or field.endswith("_record_id")
            else 2
            if field.endswith("_id")
            else 3
            if field.endswith("_ref")
            else 4,
            field,
        ),
    )
    for field in preferred:
        if field in {"run_id", "created_by_pr"}:
            continue
        values = [str(row.get(field, "") or "") for row in rows]
        if all(values) and len(values) == len(set(values)):
            return field
    raise BuildError(
        f"source owner surface lacks a stable unique row key: {path}"
    )


def _source_manifest_split(repo_root: Path) -> list[dict[str, Any]]:
    """Account for every current owner manifest entry included or excluded."""

    generated = repo_root / "docs/master_plan/generated"
    included_specs = {
        str(spec["path"]): int(spec["expected"])
        for spec in SOURCE_CLOSURE_ARTIFACTS
    }
    groups: dict[str, list[Path]] = {
        "MAP3": sorted((generated / "map3").glob("*.manifest.json")),
        "RP5D": sorted((generated / "pr168_rp5d").glob("*.manifest.json")),
        "RP5D_R1": sorted(
            (generated / "pr168_rp5d_r1").glob("*.manifest.json")
        ),
        "RP5E": sorted((generated / "pr168_rp5e").glob("*.manifest.json")),
        "PR162B": sorted(generated.glob("PR162B_*.report.json")),
        "PR162D_R2A": sorted(generated.glob("PR162D_R2A_*.report.json")),
        "PR162E": sorted(
            path
            for path in generated.glob("PR162E_*.report.json")
            if not path.name.startswith("PR162E_Q_")
        ),
        "PR162E_Q": sorted(generated.glob("PR162E_Q_*.report.json")),
        "GFP": sorted(generated.glob("PR168_GFP_*.report.json")),
    }
    reports: list[dict[str, Any]] = []
    for group, candidates in groups.items():
        manifest_entries: list[tuple[str, int]] = []
        for path in candidates:
            if path.name.endswith(".manifest.json"):
                logical_name = path.name.removesuffix(".manifest.json")
                logical_path = path.with_name(
                    logical_name
                    if logical_name.endswith(".jsonl")
                    else logical_name + ".jsonl"
                )
                payload = _read_json(path)
            else:
                logical_path = path
                try:
                    payload = _read_json(path)
                    declared = _declared_count(payload, path)
                except BuildError:
                    continue
                if not isinstance(payload.get("records", []), list):
                    continue
            declared = _declared_count(payload, path)
            relative = logical_path.relative_to(repo_root).as_posix()
            manifest_entries.append((relative, declared))
        included = [
            (path, rows)
            for path, rows in manifest_entries
            if path in included_specs
        ]
        excluded = [
            path for path, _ in manifest_entries if path not in included_specs
        ]
        denominator_drift = [
            f"{path}:{rows}!={included_specs[path]}"
            for path, rows in included
            if rows != included_specs[path]
        ]
        if denominator_drift:
            raise BuildError(
                f"{group} included manifest denominator drift: {denominator_drift[:5]}"
            )
        reports.append(
            {
                "owner_group": group,
                "total_manifest_entries": len(manifest_entries),
                "included_manifest_entries": len(included),
                "included_physical_rows": sum(rows for _, rows in included),
                "generic_or_duplicate_nonsemantic_excluded_entries": len(excluded),
                "excluded_paths": sorted(excluded),
                "exclusion_reason": (
                    "GENERIC_ROUTE_AUDIT_COUNT_OR_DUPLICATE_OWNER_PROJECTION_"
                    "WITHOUT_ADDITIONAL_COMPUTATION_SEMANTICS"
                ),
                "unclassified_manifest_entries": 0,
            }
        )
    return reports


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _owner_requirements() -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    for token in _OWNER_REQUIREMENT_TEXT.split():
        card_id, semantic_key = token.split("=", 1)
        rows.append((card_id, semantic_key, card_id[0]))
    if len(rows) != EXPECTED_OWNER_REQUIREMENTS:
        raise BuildError(
            f"owner requirement inventory changed: {len(rows)} != {EXPECTED_OWNER_REQUIREMENTS}"
        )
    if len({card_id for card_id, _, _ in rows}) != len(rows):
        raise BuildError("owner requirement card IDs are not unique")
    return tuple(rows)


def _latency_class(source_value: str | None) -> str:
    return {
        "HOT_PATH_ELIGIBLE_CANDIDATE": "HOTPATH_CANDIDATE",
        "PRECOMPUTE_REQUIRED": "BATCH_PRECOMPUTE",
        "QUANTUM_BATCH_ONLY": "HOTPATH_FORBIDDEN",
    }.get(str(source_value), "OFFLINE_RESEARCH")


def _decision_roles(domain_family: str, *, quantum: bool = False) -> list[str]:
    if quantum:
        return ["QUANTUM_MAPPING_OR_COMPARATOR", "RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"]
    token = domain_family.lower()
    roles: list[str] = []
    if any(part in token for part in ("probability", "calibration", "expected_value")):
        roles.append("PROBABILITY_FAIR_VALUE_UNCERTAINTY")
    if any(part in token for part in ("latency", "slippage", "liquidity", "microstructure")):
        roles.append("LIQUIDITY_FILL_CAPACITY_AND_ADVERSE_SELECTION")
    if any(part in token for part in ("risk", "capital", "portfolio")):
        roles.append("PORTFOLIO_EVENT_VENUE_EXPOSURE")
    if any(part in token for part in ("cost", "fee", "tca")):
        roles.append("TCA_ACCOUNTING_AND_RECONCILIATION")
    if any(part in token for part in ("objective", "constraint", "solver", "selection")):
        roles.append("INTERNAL_SUPPORT")
    return sorted(set(roles or ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"]))


def _family_decision_roles(family: str) -> list[str]:
    return {
        "A": ["EXPECTED_NET_CASH", "EXECUTABLE_EXIT_OR_SETTLEMENT"],
        "B": ["TCA_ACCOUNTING_AND_RECONCILIATION", "LIQUIDITY_FILL_CAPACITY_AND_ADVERSE_SELECTION"],
        "C": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
        "D": ["PORTFOLIO_EVENT_VENUE_EXPOSURE", "NO_TRADE_OR_ALTERNATIVE_CAPITAL_USE"],
        "E": ["EXECUTABLE_ENTRY_ECONOMICS"],
        "F": ["QUANTUM_MAPPING_OR_COMPARATOR"],
        "G": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION", "QUANTUM_MAPPING_OR_COMPARATOR"],
        "H": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION", "QUANTUM_MAPPING_OR_COMPARATOR"],
        "I": ["INTERNAL_SUPPORT"],
        "J": ["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
    }[family]


def _blank_quantum() -> dict[str, Any]:
    return {
        "applicability_state": "NOT_APPLICABLE_OR_NOT_YET_PROVEN",
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
        "fallback": "DETERMINISTIC_CLASSICAL_FALLBACK_REQUIRED_IF_PROMOTED",
        "maturity_ceiling": "SPECIFIED",
    }


def _definition(
    *,
    display_name: str,
    description: str,
    component_kind: str,
    complete_definition: str,
    inputs: Sequence[Mapping[str, Any]] = (),
    outputs: Sequence[Mapping[str, Any]] = (),
    units: Mapping[str, Any] | None = None,
    requirements: Sequence[Mapping[str, Any]] = (),
    latency_class: str = "OFFLINE_RESEARCH",
    implementation_versions: Sequence[Mapping[str, Any]] = (),
    oracle_refs: Sequence[Mapping[str, Any] | str] = (),
    quantum: Mapping[str, Any] | None = None,
    inventory_class: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "display_name": display_name,
        "description": description,
        "component_kind": component_kind,
        "family_template_ref_or_null": None,
        "complete_mathematical_or_procedural_definition": complete_definition,
        "objective_sense_or_null": None,
        "assumptions": [],
        "hard_constraints": [],
        "soft_preferences": [],
        "domain_and_boundary_behavior": "CONTROL_PLANE_TYPED_VALIDATION_REQUIRED",
        "state_and_time_semantics": "STATELESS_SAME_REQUEST_UNLESS_SOURCE_PROCEDURE_DECLARES_OTHERWISE",
        "input_schema": [dict(item) for item in inputs],
        "output_schema": [dict(item) for item in outputs],
        "units_and_bases": dict(units or {}),
        "output_accounting_class": "NON_ACCOUNTING_UNLESS_OUTPUT_SCHEMA_EXPLICITLY_IDENTIFIES_ACCOUNTING",
        "missing_stale_nonfinite_behavior": "FAIL_CLOSED_AT_CONTROL_PLANE_BOUNDARY",
        "precision_and_rounding": "SOURCE_IMPLEMENTATION_PRECISION_WITH_EXPLICIT_CONTROL_PLANE_BOUNDARY_CONVERSION",
        "parameter_schema_and_default_provenance": [],
        "requirements": [dict(item) for item in requirements],
        "latency_class": latency_class,
        "risk_materiality": {
            "economic_materiality": "REQUIRES_CONTEXT_CLASSIFICATION",
            "complexity": "SOURCE_DECLARED",
            "data_dependency": "TYPED_INPUT_LOCK_REQUIRED",
            "latency_sensitivity": latency_class,
            "external_provider_dependency": False,
            "quantum_backend_dependency": False,
            "independent_validation_strength_required": "INDEPENDENT_ORACLE",
            "monitoring_revalidation_cadence": "BEFORE_ANY_PROMOTION",
        },
        "failure_domain_tags": ["MISSING_INPUT", "STALE_INPUT", "NONFINITE_INPUT", "DOMAIN_ERROR"],
        "classical_fallback": "FAIL_CLOSED_UNLESS_EXPLICIT_BINDING_FALLBACK_EXISTS",
        "quantum": dict(quantum or _blank_quantum()),
        "implementation_versions": [dict(item) for item in implementation_versions],
        "oracle_and_test_refs": [copy.deepcopy(item) for item in oracle_refs],
        "equivalence_proof_refs": [],
    }
    if inventory_class is not None:
        value["implementation_inventory_class"] = inventory_class
    return value


def _agent_access_policy(agent_ids: Sequence[str], *, compute: bool) -> dict[str, Any]:
    compute_roles = {
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    }
    policies: dict[str, Any] = {}
    for agent_id in sorted(set(agent_ids)):
        operations = ["status", "explain"]
        if compute and agent_id in compute_roles:
            operations = ["resolve", "compute", "status", "explain"]
        policy: dict[str, Any] = {
            "control_plane_operations": operations,
            "mode_ceiling": "FIXTURE_NONLIVE",
            "order_release_authority": False,
            "source_truth_authority": False,
        }
        if agent_id in {"research_agent", "quantum_optimizer_agent"}:
            policy["research_operations"] = ["propose_batch_item"]
        policies[agent_id] = policy
    return policies


def _fixture_scalar_issue(value: Any, declared_type: str) -> str | None:
    """Validate a fixture scalar without accepting Python binary floats or bools."""

    if declared_type not in {"FINITE_DECIMAL_COMPATIBLE_SCALAR", "DECIMAL"}:
        return f"unsupported_declared_type:{declared_type}"
    if isinstance(value, bool) or isinstance(value, float):
        return f"non_exact_scalar_type:{type(value).__name__}"
    if isinstance(value, int):
        return None
    if isinstance(value, Decimal):
        return None if value.is_finite() else "nonfinite_decimal"
    if isinstance(value, str):
        try:
            parsed = Decimal(value)
        except Exception:
            return "invalid_decimal_text"
        return None if parsed.is_finite() else "nonfinite_decimal_text"
    return f"unsupported_scalar_type:{type(value).__name__}"


def _ephemeral_fixture_contract_issues(
    component_id: str,
    definition: Mapping[str, Any],
    fixture_ref: str | None,
    contract: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Check a build-only typed fixture contract; fixture values are never persisted."""

    if fixture_ref is None:
        return () if contract is None else ("contract_without_fixture_ref",)
    if not isinstance(contract, Mapping):
        return ("fixture_contract_missing",)
    issues: list[str] = []
    if contract.get("fixture_ref") != fixture_ref:
        issues.append("fixture_ref_unresolved")
    resolution_state = contract.get("source_resolution_state")
    closed_component_ids = {
        f"QTT.COMP.FORMULA.{formula_id}"
        for formula_id in _CLOSED_FIXTURE_FORMULA_IDS
    }
    if component_id in closed_component_ids:
        expected_fixture_ref = (
            "PR162D_R2A_TV_FORMULA::"
            + component_id.removeprefix("QTT.COMP.FORMULA.")
        )
        allowed_state = "SOURCE_TEST_VECTOR_EXACTLY_RESOLVED"
        if fixture_ref != expected_fixture_ref:
            issues.append("fixture_ref_not_allowlisted")
        if contract.get("source_artifact_ref") != (
            PR162D_TEST_VECTOR_REGISTRY.as_posix()
        ):
            issues.append("source_artifact_ref_not_allowlisted")
        if contract.get("source_row_ref") != f"records[{expected_fixture_ref}]":
            issues.append("source_row_ref_not_allowlisted")
    elif component_id.startswith("QTT.COMP.SCALE."):
        allowed_state = "TEMPORARY_SCALE_PROBE_EXACTLY_RESOLVED"
        if fixture_ref != "CONTROL1_FIXED_SEED_SCALE_PROBE":
            issues.append("fixture_ref_not_allowlisted")
        if contract.get("source_artifact_ref") != "CONTROL1_FIXED_SEED_SCALE_PROBE":
            issues.append("source_artifact_ref_not_allowlisted")
        if contract.get("source_row_ref") != component_id:
            issues.append("source_row_ref_not_allowlisted")
    else:
        allowed_state = None
        issues.append("component_not_fixture_allowlisted")
    if allowed_state is None or resolution_state != allowed_state:
        issues.append("source_fixture_unresolved")
    if not isinstance(contract.get("source_artifact_ref"), str) or not str(
        contract.get("source_artifact_ref")
    ):
        issues.append("source_artifact_ref_unresolved")
    if not isinstance(contract.get("source_row_ref"), str) or not str(
        contract.get("source_row_ref")
    ):
        issues.append("source_row_ref_unresolved")

    schema_entries = definition.get("input_schema", ())
    schema_by_name: dict[str, Mapping[str, Any]] = {}
    if not isinstance(schema_entries, (list, tuple)):
        issues.append("input_schema_invalid")
    else:
        for index, entry in enumerate(schema_entries):
            if not isinstance(entry, Mapping) or not str(entry.get("name", "")):
                issues.append(f"input_schema_invalid:{index}")
                continue
            name = str(entry["name"])
            if name in schema_by_name:
                issues.append(f"input_schema_duplicate:{name}")
            schema_by_name[name] = entry

    required_by_input: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for requirement in definition.get("requirements", ()):
        if not isinstance(requirement, Mapping):
            continue
        if str(requirement.get("required_or_optional", "REQUIRED")).upper() == "OPTIONAL":
            continue
        consumer_input = str(requirement.get("consumer_input_name", "")).strip()
        if consumer_input:
            required_by_input[consumer_input].append(requirement)

    ports = contract.get("ports")
    port_by_name: dict[str, Mapping[str, Any]] = {}
    if not isinstance(ports, (list, tuple)):
        issues.append("fixture_ports_invalid")
    else:
        for index, port in enumerate(ports):
            if not isinstance(port, Mapping) or not str(port.get("input_name", "")):
                issues.append(f"fixture_port_invalid:{index}")
                continue
            name = str(port["input_name"])
            if name in port_by_name:
                issues.append(f"fixture_port_duplicate:{name}")
            port_by_name[name] = port
    for name in sorted(set(schema_by_name) - set(port_by_name)):
        issues.append(f"fixture_port_missing:{name}")
    for name in sorted(set(port_by_name) - set(schema_by_name)):
        issues.append(f"fixture_port_extra:{name}")

    for name in sorted(set(schema_by_name) & set(port_by_name)):
        schema = schema_by_name[name]
        port = port_by_name[name]
        declared_type = str(schema.get("type", ""))
        unit = str(
            schema.get("unit_or_basis")
            or schema.get("unit")
            or schema.get("basis")
            or ""
        )
        if port.get("declared_type") != declared_type:
            issues.append(f"fixture_type_mismatch:{name}")
        if port.get("unit_or_basis") != unit:
            issues.append(f"fixture_unit_mismatch:{name}")
        scalar_issue = _fixture_scalar_issue(port.get("value"), declared_type)
        if scalar_issue:
            issues.append(f"fixture_value_invalid:{name}:{scalar_issue}")
        requirements = required_by_input.get(name, ())
        ownership = port.get("ownership")
        if requirements:
            if len(requirements) != 1:
                issues.append(f"fixture_requirement_ambiguous:{name}")
                continue
            requirement = requirements[0]
            if ownership != "CANONICAL_REQUIREMENT_OUTPUT":
                issues.append(f"fixture_requirement_ownership:{name}")
            if port.get("required_component_id") != requirement.get(
                "required_component_id_or_source_selector"
            ):
                issues.append(f"fixture_requirement_component:{name}")
            if port.get("producer_output_name") != requirement.get(
                "producer_output_name"
            ):
                issues.append(f"fixture_requirement_output:{name}")
        elif ownership != "DIRECT_TYPED_REQUEST_INPUT":
            issues.append(f"fixture_direct_ownership:{name}")

    if component_id in closed_component_ids:
        # Re-read the fixed PR162D owner and recompute its source fixture here;
        # a caller-provided contract is never allowed to attest its own values.
        repo_root = Path(__file__).resolve().parents[1]
        formula_id = component_id.removeprefix("QTT.COMP.FORMULA.")
        try:
            formula_module, _algorithm_module, _quantum_module = (
                _import_r2a_modules(repo_root)
            )
            source_specs = {
                str(spec.formula_id): spec
                for spec in formula_module.formula_specs()
            }
            source_rows = _read_pr162d_test_vector_rows(repo_root)
        except Exception as exc:
            issues.append(
                f"fixture_source_owner_unresolved:{type(exc).__name__}"
            )
        else:
            source_spec = source_specs.get(formula_id)
            source_row = source_rows.get(expected_fixture_ref)
            if source_spec is None or not isinstance(source_row, Mapping):
                issues.append("fixture_source_owner_unresolved")
            else:
                if source_row.get("callable_ref") != source_spec.callable_ref:
                    issues.append("fixture_source_callable_mismatch")
                if source_row.get("live_order_authority") is not False:
                    issues.append("fixture_source_live_authority")
                source_inputs = source_row.get("inputs")
                source_outputs = source_row.get("expected_outputs")
                if not isinstance(source_inputs, Mapping):
                    issues.append("fixture_source_inputs_invalid")
                    source_inputs = {}
                if not isinstance(source_outputs, Mapping):
                    issues.append("fixture_source_outputs_invalid")
                    source_outputs = {}
                if set(source_inputs) != set(source_spec.required_inputs):
                    issues.append("fixture_source_input_ports_mismatch")
                if set(source_outputs) != set(source_spec.outputs):
                    issues.append("fixture_source_output_ports_mismatch")

                def exact_decimal(value: Any) -> Decimal | None:
                    if isinstance(value, bool):
                        return None
                    try:
                        parsed = Decimal(str(value))
                    except Exception:
                        return None
                    return parsed if parsed.is_finite() else None

                for name in sorted(set(source_inputs) & set(source_spec.test_inputs)):
                    if exact_decimal(source_inputs[name]) != exact_decimal(
                        source_spec.test_inputs[name]
                    ):
                        issues.append(f"fixture_source_input_value_mismatch:{name}")
                try:
                    recomputed = source_spec.compute(
                        copy.deepcopy(dict(source_spec.test_inputs))
                    )
                except Exception as exc:
                    issues.append(
                        f"fixture_source_recompute_failed:{type(exc).__name__}"
                    )
                    recomputed = {}
                if not isinstance(recomputed, Mapping):
                    issues.append("fixture_source_recompute_invalid")
                    recomputed = {}
                for name in sorted(set(source_outputs) | set(recomputed)):
                    if (
                        name not in source_outputs
                        or name not in recomputed
                        or exact_decimal(source_outputs[name])
                        != exact_decimal(recomputed[name])
                    ):
                        issues.append(f"fixture_source_output_value_mismatch:{name}")
                for name in sorted(set(port_by_name) & set(source_inputs)):
                    if exact_decimal(port_by_name[name].get("value")) != exact_decimal(
                        source_inputs[name]
                    ):
                        issues.append(f"fixture_value_source_mismatch:{name}")
    return tuple(sorted(set(issues)))


def _binding(
    component_id: str,
    *,
    definition: Mapping[str, Any],
    binding_id: str,
    agent_ids: Sequence[str],
    implementation_version: str | None,
    exact_action: str | None,
    fixture_ref: str | None = None,
    fixture_contract: Mapping[str, Any] | None = None,
    requirements_ready: bool = False,
    oracle_ready: bool = False,
    dormant: bool = False,
) -> dict[str, Any]:
    implementation_ready = implementation_version is not None
    predicate = getattr(_control_module(), "_specification_completeness_issues", None)
    if not callable(predicate):
        raise BuildError("control owner lacks specification-completeness predicate")
    specification_issues = tuple(str(value) for value in predicate(definition))
    specification_ready = not specification_issues
    fixture_contract_issues = _ephemeral_fixture_contract_issues(
        component_id, definition, fixture_ref, fixture_contract
    )
    typed_fixture_ready = (
        fixture_ref is not None
        and specification_ready
        and not fixture_contract_issues
    )
    if specification_issues:
        exact_action = (
            f"MISSING_SPECIFICATION_SEMANTICS: {component_id}@1.0: "
            + ",".join(specification_issues)
        )
    elif fixture_ref is not None and fixture_contract_issues:
        exact_action = (
            f"MISSING_TYPED_FIXTURE_CONTRACT: {component_id}@1.0: "
            + ",".join(fixture_contract_issues)
        )
    readiness = {
        "specification": "PASS" if specification_ready else "REQUIRED",
        "implementation": "PASS" if implementation_ready else "REQUIRED",
        "inputs": "PASS" if typed_fixture_ready else "REQUIRED",
        "requirements": "PASS" if requirements_ready else "REQUIRED",
        "oracle": "PASS" if oracle_ready else "REQUIRED",
        "context": "PASS" if typed_fixture_ready else "REQUIRED",
        "evidence": "FIXTURE" if typed_fixture_ready else "NONE",
        "authorization": "NOT_ELIGIBLE",
    }
    computation_ready = all(
        readiness[key] == "PASS"
        for key in (
            "specification",
            "implementation",
            "inputs",
            "requirements",
            "oracle",
            "context",
        )
    )
    required_requirements_by_input: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for requirement in definition.get("requirements", ()):
        if not isinstance(requirement, Mapping):
            continue
        if str(requirement.get("required_or_optional", "REQUIRED")).upper() == "OPTIONAL":
            continue
        consumer_input = str(requirement.get("consumer_input_name", "")).strip()
        if consumer_input:
            required_requirements_by_input[consumer_input].append(requirement)

    input_source_bindings: list[dict[str, Any]] = []
    if typed_fixture_ready:
        for entry in definition.get("input_schema", ()):
            if not isinstance(entry, Mapping) or not entry.get("name"):
                continue
            input_name = str(entry["name"])
            requirements_for_input = required_requirements_by_input.get(input_name, ())
            source_binding = {
                "input_name": input_name,
                "declared_type": entry.get("type"),
                "unit_or_basis": entry.get(
                    "unit_or_basis", entry.get("unit", entry.get("basis"))
                ),
            }
            if requirements_for_input:
                if len(requirements_for_input) != 1:
                    raise BuildError(
                        f"fixture binding requires one selected canonical producer: "
                        f"{component_id}.{input_name}"
                    )
                requirement = requirements_for_input[0]
                source_binding.update(
                    {
                        "source_ref": str(
                            requirement["required_component_id_or_source_selector"]
                        ),
                        "producer_output_name": str(
                            requirement["producer_output_name"]
                        ),
                        "binding_state": "CANONICAL_REQUIREMENT_OUTPUT",
                    }
                )
            else:
                source_binding.update(
                    {
                        "source_ref": (
                            "QKUComputationControlPlaneV1.compute.inputs::"
                            f"{input_name}"
                        ),
                        "fixture_evidence_ref": fixture_ref,
                        "binding_state": "EXACT_TYPED_REQUEST_INPUT_LOCK",
                    }
                )
            input_source_bindings.append(source_binding)
    elif fixture_ref:
        input_source_bindings = [
            {
                "fixture_ref": fixture_ref,
                "binding_state": "SEMANTIC_SPECIFICATION_REQUIRED",
            }
        ]

    return {
        "binding_id": binding_id,
        "market": "MARKET_AGNOSTIC_RESEARCH_FIXTURE" if typed_fixture_ready else "UNRESOLVED",
        "venue": "NO_VENUE",
        "context_selector": {
            "context_family": "IMMUTABLE_FIXTURE" if typed_fixture_ready else "SOURCE_IDENTITY_REVIEW",
            "component_id": component_id,
        },
        "qku_binding_selector_or_null": None,
        "supported_modes": ["FIXTURE_NONLIVE"] if typed_fixture_ready else [],
        "mode_state": (
            {
                "FIXTURE_NONLIVE": {
                    "evidence": "FIXTURE",
                    "authorization": "NOT_ELIGIBLE",
                }
            }
            if typed_fixture_ready
            else {}
        ),
        "as_of_policy": "IMMUTABLE_FIXTURE" if typed_fixture_ready else "NOT_RESOLVED",
        "selected_implementation_version": implementation_version,
        "binding_version": "1.0",
        "selected_parameter_policy": {
            "policy": "SOURCE_FIXTURE_VALUES_NOT_RUNTIME_DEFAULTS" if typed_fixture_ready else "UNRESOLVED",
            "default_provenance": fixture_ref if typed_fixture_ready else None,
            "optimizer_version": None,
            "calibration_ref": None,
            "seed_policy": "DETERMINISTIC_NO_SEED" if typed_fixture_ready else None,
            "fallback": "FAIL_CLOSED",
            "revalidation": "REQUIRED_BEFORE_PROMOTION",
        },
        "input_source_bindings": input_source_bindings,
        "venue_semantic_version": None,
        "portfolio_state_requirement": "NONE_FOR_FIXTURE" if typed_fixture_ready else "UNRESOLVED",
        "cash_state_requirement": "NONE_FOR_FIXTURE" if typed_fixture_ready else "UNRESOLVED",
        "freshness_and_TTL": {
            "policy": "IMMUTABLE_FIXTURE" if typed_fixture_ready else "UNRESOLVED",
            "ttl_seconds": None,
        },
        "point_in_time_policy": "FIXTURE_LOCK_ONLY" if typed_fixture_ready else "UNRESOLVED",
        "requirement_context_policy": "SAME_FIXTURE_INPUT_LOCK" if typed_fixture_ready else "UNRESOLVED",
        "selected_requirement_alternatives": [],
        "readiness": readiness,
        "derived_state": (
            "RETIRED"
            if dormant
            else "CONTEXT_READY"
            if computation_ready
            else "SPECIFICATION_REQUIRED"
            if not specification_ready
            else "SPECIFIED"
        ),
        "exact_resolution_action_or_null": exact_action,
        "evidence_summary": (
            {
                "evidence_ceiling": "FIXTURE",
                "fixture_ref": fixture_ref,
                "empirical_market_evidence": False,
                "limitations": ["NO_REPLAY_PAPER_SHADOW_DRYRUN_CANARY_OR_LIVE_EVIDENCE"],
            }
            if typed_fixture_ready
            else {
                "evidence_ceiling": "NONE",
                "unvalidated_fixture_ref": fixture_ref,
                "empirical_market_evidence": False,
                "limitations": ["FIXTURE_CONTRACT_NOT_EXACTLY_RESOLVED"],
            }
            if fixture_ref
            else {
                "evidence_ceiling": "NONE",
                "empirical_market_evidence": False,
                "limitations": ["SOURCE_IDENTITY_ONLY"],
            }
        ),
        "agent_access_policy": _agent_access_policy(agent_ids, compute=computation_ready),
        "fallback_policy": {"behavior": "FAIL_CLOSED", "component_id": None},
        "runtime_snapshot_ref_or_null": None,
        "activation_state": "DORMANT_PRESERVED" if dormant else "INACTIVE_NONLIVE",
        "rollback_target_or_null": None,
        "upstream_value_lineage": (
            [
                *([fixture_ref] if typed_fixture_ready else []),
                *sorted(
                    {
                        str(
                            requirement[
                                "required_component_id_or_source_selector"
                            ]
                        )
                        for requirements_for_input in required_requirements_by_input.values()
                        for requirement in requirements_for_input
                    }
                ),
            ]
        ),
        "downstream_consumer_classes": ["CONTROL1_INDEPENDENT_VALIDATOR"],
        "producer_owner": "CONTROL1_CENTRAL_BUILDER",
        "validator_refs": [VALIDATOR_NAME],
        "terminal_disposition_or_null": exact_action if dormant else None,
    }


def _record(
    *,
    component_id: str,
    record_state: str,
    origins: Sequence[str],
    definition: Mapping[str, Any],
    decision_roles: Sequence[str],
    bindings: Sequence[Mapping[str, Any]],
    provenance: Sequence[Mapping[str, Any]],
    qku_roles: Sequence[Mapping[str, Any]] = (),
    market_tags: Sequence[str] = (),
    relations: Sequence[Mapping[str, Any]] = (),
    producer_owner: str = "CONTROL1_CENTRAL_BUILDER",
) -> dict[str, Any]:
    return {
        "canonical_component_id": component_id,
        "semantic_version": "1.0",
        "record_state": record_state,
        "origin_cohorts": sorted(set(origins)),
        "definition": copy.deepcopy(dict(definition)),
        "uses": {
            "decision_roles": sorted(set(decision_roles)),
            "decision_outputs": [
                item.get("name")
                for item in definition.get("output_schema", [])
                if isinstance(item, Mapping) and item.get("name")
            ],
            "market_family_tags": sorted(set(market_tags)),
            "qku_role_bindings": [copy.deepcopy(dict(item)) for item in qku_roles],
            "consumer_class_tags": ["CONTROL1_FACADE", "CONTROL1_INDEPENDENT_VALIDATOR"],
        },
        "bindings": [copy.deepcopy(dict(item)) for item in bindings],
        "provenance": [copy.deepcopy(dict(item)) for item in provenance],
        "relations": [copy.deepcopy(dict(item)) for item in relations],
        "governance": {
            "producer_owner": producer_owner,
            "validator_refs": [VALIDATOR_NAME],
            "reviewer_or_challenger_owner": "OWNER_DESIGNATED_INDEPENDENT_AUDITOR",
            "change_authority": "CONTROL1_CENTRAL_BUILDER_REVIEWED_GIT_PR_ONLY",
        },
    }


def _expansion_batch(
    *,
    batch_id: str,
    origin: str,
    source_refs: Sequence[str],
    source_classification: str,
    items: Sequence[dict[str, Any]],
    requested_evidence_modes: Sequence[str] = ("NONE",),
    requested_promotion_ceiling: str = "SPECIFIED",
) -> dict[str, Any]:
    """Return the one transient ExpansionBatchV1-compatible intake shape."""

    prepared_items: list[dict[str, Any]] = []
    intended_contexts: dict[str, dict[str, Any]] = {}
    for source_item in items:
        item = copy.deepcopy(source_item)
        record = item.get("record") if isinstance(item.get("record"), Mapping) else item
        if not isinstance(record, Mapping):
            raise BuildError("expansion batch item must contain one computation record")
        if "record" not in item:
            component_id = str(record.get("canonical_component_id", ""))
            item = {
                "record": copy.deepcopy(dict(record)),
                "case": f"SOURCE_INTAKE::{component_id}",
                "equivalence_decision": "NO",
                "nonidentical_relation": "DISTINCT",
            }
        item["record"] = _normalize_compiler_candidate_record(
            _batch_item_record(item)
        )
        record = item["record"]
        prepared_items.append(item)
        for binding in record.get("bindings", []):
            if not isinstance(binding, Mapping):
                continue
            modes = [str(mode) for mode in binding.get("supported_modes", [])]
            if not modes:
                modes = [None]
            for mode in modes:
                context = {
                    "market": copy.deepcopy(binding.get("market", "ANY")),
                    "venue": copy.deepcopy(binding.get("venue", "ANY")),
                }
                if mode is not None:
                    context["mode"] = mode
                intended_contexts[_json_line(context)] = context
    return {
        "batch_id": batch_id,
        "batch_origin": origin,
        "submitted_by": "CONTROL1_CENTRAL_BUILDER",
        # This is an actual build-intake timestamp, not source/evidence time or
        # a canonical identity.  It is transient and is never written into the
        # registry or acceptance surface.
        "submission_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_refs": sorted(set(source_refs)),
        "source_classification": source_classification,
        "intended_market_venue_modes": [
            intended_contexts[key] for key in sorted(intended_contexts)
        ],
        "items": prepared_items,
        "requested_evidence_modes": sorted(set(requested_evidence_modes)),
        "requested_promotion_ceiling": requested_promotion_ceiling,
    }


def _load_agent_ids(repo_root: Path) -> tuple[str, ...]:
    payload = _read_json(repo_root / PR165_D2_ROSTER)
    ids = sorted(
        {
            str(row["agent_id"])
            for row in payload.get("records", [])
            if isinstance(row, dict) and row.get("agent_id")
        }
    )
    expected = {
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
        "connector_venue_readiness_future_consumer",
    }
    if set(ids) != expected:
        raise BuildError(
            "PR165-D2 roster drift requires explicit policy review: "
            f"expected={sorted(expected)!r}, actual={ids!r}"
        )
    return tuple(ids)


def _rp5c_component_id(source_identity_id: str) -> str:
    prefix = "RP5C_IDENTITY_"
    if not source_identity_id.startswith(prefix):
        raise BuildError(f"invalid RP5C source identity: {source_identity_id}")
    suffix = source_identity_id.removeprefix(prefix)
    if len(suffix) != 8 or not suffix.isdigit():
        raise BuildError(f"invalid RP5C source identity suffix: {source_identity_id}")
    return f"QTT.COMP.RP5C.{suffix}"


def _rp5c_group_custody_key(row: Mapping[str, Any]) -> dict[str, str]:
    """Reconstruct RP5C's stable, structured source-group custody key.

    RP5C's ``duplicate_group_id`` is an ordinal derived from sorted enumeration
    and therefore is current-source evidence, not a stable identity key.  This
    six-field tuple is the exact grouping input used by the RP5C owner.  It is
    retained as structured text (never a hash) and is explicitly not CONTROL1
    semantic-equivalence proof.
    """

    return {
        "key_version": RP5C_GROUP_CUSTODY_KEY_VERSION,
        **{field: str(row.get(field) or "") for field in RP5C_GROUP_KEY_FIELDS},
    }


def _rp5c_group_custody_tuple(value: Mapping[str, Any]) -> tuple[str, ...]:
    expected = {"key_version", *RP5C_GROUP_KEY_FIELDS}
    if set(value) != expected:
        raise BuildError(
            "RP5C source-group custody key fields drift: "
            f"expected={sorted(expected)!r}, actual={sorted(value)!r}"
        )
    if value.get("key_version") != RP5C_GROUP_CUSTODY_KEY_VERSION:
        raise BuildError(f"unsupported RP5C source-group custody key: {value!r}")
    if any(not isinstance(value.get(field), str) for field in RP5C_GROUP_KEY_FIELDS):
        raise BuildError(f"non-text RP5C source-group custody key: {value!r}")
    return tuple(str(value[field]) for field in RP5C_GROUP_KEY_FIELDS)


def _load_rp5c_group_custody_keys(
    repo_root: Path, deadline: _Deadline
) -> dict[str, tuple[str, dict[str, str], tuple[str, ...]]]:
    """Map current canonical source identities to stable group custody keys."""

    by_canonical: dict[str, tuple[str, dict[str, str], tuple[str, ...]]] = {}
    key_owners: dict[tuple[str, ...], str] = {}
    for row in _iter_jsonl(repo_root / RP5C_CANONICAL_LIBRARY, deadline):
        canonical = str(row.get("canonical_identity_row_id") or "")
        _rp5c_component_id(canonical)
        group_id = str(row.get("duplicate_group_id") or "")
        if not group_id:
            raise BuildError(f"RP5C canonical library row lacks duplicate group: {canonical}")
        key_payload = _rp5c_group_custody_key(row)
        key = _rp5c_group_custody_tuple(key_payload)
        if canonical in by_canonical:
            raise BuildError(f"duplicate RP5C canonical library identity: {canonical}")
        prior = key_owners.get(key)
        if prior is not None:
            raise BuildError(
                "RP5C canonical library custody key maps to multiple identities: "
                f"{prior}, {canonical}"
            )
        by_canonical[canonical] = (group_id, key_payload, key)
        key_owners[key] = canonical
    if len(by_canonical) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "RP5C canonical-library custody-key coverage drift: "
            f"{len(by_canonical)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    return by_canonical


def _load_rp5c_reference_custody_rows(
    repo_root: Path, deadline: _Deadline
) -> dict[str, dict[str, Any]]:
    """Read the immutable RP5C identity/reference surface for RP5D closure."""

    by_identity: dict[str, dict[str, Any]] = {}
    for row in _iter_jsonl(repo_root / RP5C_CANONICAL_LIBRARY, deadline):
        identity_ref = str(row.get("canonical_identity_row_id") or "")
        _rp5c_component_id(identity_ref)
        if identity_ref in by_identity:
            raise BuildError(
                f"duplicate RP5C reference-custody identity: {identity_ref}"
            )
        references: dict[str, str | None] = {}
        for source_field, output_field in (
            ("formula_id", "formula_ref"),
            ("qku_id", "qku_ref"),
        ):
            raw = row.get(source_field)
            if raw in (None, ""):
                references[output_field] = None
            elif isinstance(raw, str):
                references[output_field] = raw
            else:
                raise BuildError(
                    f"RP5C {identity_ref} has non-text {source_field}: {raw!r}"
                )
        by_identity[identity_ref] = {
            **references,
            "custody_key": _rp5c_group_custody_tuple(
                _rp5c_group_custody_key(row)
            ),
        }
    if len(by_identity) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "RP5C reference-custody coverage drift: "
            f"{len(by_identity)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    return by_identity


def _classify_rp5d_reference_mapping(
    row: Mapping[str, Any],
    *,
    source_path: str,
    rp5c_reference_rows: Mapping[str, Mapping[str, Any]],
    identity_targets: Mapping[str, set[str]],
    target_custody_keys: Mapping[str, set[tuple[str, ...]]],
) -> dict[str, Any]:
    """Resolve one RP5D row only through its immutable RP5C identity/custody."""

    identity_ref = row.get("identity_ref")
    if not isinstance(identity_ref, str) or identity_ref not in rp5c_reference_rows:
        raise BuildError(
            f"RP5D_IDENTITY_CUSTODY_MAPPING: {source_path}: {identity_ref!r}"
        )
    source = rp5c_reference_rows[identity_ref]
    targets = set(identity_targets.get(identity_ref, set()))
    if len(targets) != 1:
        raise BuildError(
            "RP5D_IDENTITY_CUSTODY_MAPPING: "
            f"{source_path}: {identity_ref}: targets={sorted(targets)}"
        )
    target = next(iter(targets))
    expected_custody = tuple(source["custody_key"])
    observed_custodies = set(target_custody_keys.get(target, set()))
    if observed_custodies != {expected_custody}:
        raise BuildError(
            "RP5D_IDENTITY_CUSTODY_MAPPING: "
            f"{source_path}: {identity_ref} -> {target}: "
            f"custody={sorted(observed_custodies)!r}"
        )

    real_references: dict[str, str] = {}
    absence_dispositions: dict[str, str] = {}
    for kind, field in (("FORMULA", "formula_ref"), ("QKU", "qku_ref")):
        observed = row.get(field)
        if not isinstance(observed, str) or not observed:
            raise BuildError(
                f"RP5D_{kind}_REFERENCE_MAPPING: {source_path}: "
                f"{identity_ref}: missing {field}"
            )
        expected = source[field]
        if expected is None:
            absent = f"{identity_ref}::{kind}_REF_NOT_PRESENT"
            if observed != absent:
                raise BuildError(
                    f"RP5D_{kind}_REFERENCE_MAPPING: {source_path}: "
                    f"{identity_ref}: {observed!r} != {absent!r}"
                )
            absence_dispositions[kind] = absent
        else:
            if observed != expected:
                raise BuildError(
                    f"RP5D_{kind}_REFERENCE_MAPPING: {source_path}: "
                    f"{identity_ref}: {observed!r} != {expected!r}"
                )
            real_references[kind] = observed
    return {
        "target": target,
        "real_references": real_references,
        "absence_dispositions": absence_dispositions,
    }


def _accepted_rp5c_group_map(
    base_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[tuple[str, ...], str], dict[str, Mapping[str, Any]]]:
    """Recover stable CONTROL1 IDs from structured RP5C custody keys."""

    key_to_component: dict[tuple[str, ...], str] = {}
    component_to_record: dict[str, Mapping[str, Any]] = {}
    for record in base_records:
        origins = {str(value) for value in record.get("origin_cohorts", ())}
        if "RP5C_BASELINE" not in origins:
            continue
        component_id = str(record.get("canonical_component_id") or "")
        if not component_id.startswith("QTT.COMP.RP5C."):
            raise BuildError(f"accepted RP5C record has invalid component ID: {component_id!r}")
        key_payloads = [
            relation.get("source_group_custody_key")
            for relation in record.get("relations", ())
            if isinstance(relation, Mapping)
            and relation.get("relation_type")
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        ]
        if len(key_payloads) != 1 or not isinstance(key_payloads[0], Mapping):
            raise BuildError(
                f"accepted RP5C record lacks one stable source-group custody key: {component_id}"
            )
        key = _rp5c_group_custody_tuple(key_payloads[0])
        prior = key_to_component.get(key)
        if prior is not None and prior != component_id:
            raise BuildError(
                "accepted RP5C source-group custody key maps to multiple components: "
                f"{prior}, {component_id}"
            )
        if component_id in component_to_record:
            raise BuildError(f"duplicate accepted RP5C component: {component_id}")
        key_to_component[key] = component_id
        component_to_record[component_id] = record
    if key_to_component and len(key_to_component) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "accepted RP5C source-group custody-key coverage drift: "
            f"{len(key_to_component)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    return key_to_component, component_to_record


def _rp5c_provenance(
    source_ref: str,
    source_row_ref: str,
    fields: Sequence[str],
    component_id: str,
    relation: str,
    *,
    source_local_identity: str | None = None,
) -> dict[str, Any]:
    return {
        "source_artifact_ref": source_ref,
        "source_row_ref": source_row_ref,
        "source_local_identity_or_name": source_local_identity or component_id,
        "source_fields_consumed": list(fields),
        "source_relation": relation,
        "canonical_target_ref": component_id,
        "proof_refs": [],
    }


def _build_rp5c_batch(
    repo_root: Path,
    agent_ids: Sequence[str],
    deadline: _Deadline,
    base_records: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    accepted_key_map, accepted_records = _accepted_rp5c_group_map(base_records)
    source_group_keys = _load_rp5c_group_custody_keys(repo_root, deadline)
    records: dict[str, dict[str, Any]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    source_to_component: dict[str, str] = {}
    source_members: dict[str, set[str]] = {}
    member_owner: dict[str, str] = {}
    current_group_ids: set[str] = set()
    current_group_keys: set[tuple[str, ...]] = set()
    expected_lineage_rows = 0
    dedupe_ref = RP5C_DEDUPE.as_posix()
    for row in _iter_jsonl(repo_root / RP5C_DEDUPE, deadline):
        source_identity_id = str(row.get("canonical_identity_row_id") or "")
        if not source_identity_id:
            raise BuildError("RP5C dedupe row lacks canonical_identity_row_id")
        source_component_id = _rp5c_component_id(source_identity_id)
        if source_identity_id in source_to_component:
            raise BuildError(f"duplicate RP5C source canonical identity: {source_identity_id}")
        group_id = str(row.get("duplicate_group_id") or "")
        if not group_id or group_id in current_group_ids:
            raise BuildError(f"duplicate or empty RP5C duplicate group: {group_id!r}")
        current_group_ids.add(group_id)
        source_key_entry = source_group_keys.get(source_identity_id)
        if source_key_entry is None:
            raise BuildError(
                "RP5C dedupe canonical identity lacks canonical-library custody key: "
                f"{source_identity_id}"
            )
        library_group_id, group_key_payload, group_key = source_key_entry
        if library_group_id != group_id:
            raise BuildError(
                "RP5C dedupe/canonical-library duplicate-group mismatch: "
                f"{source_identity_id}: {group_id} != {library_group_id}"
            )
        if group_key in current_group_keys:
            raise BuildError(
                f"RP5C dedupe rows repeat a stable source-group custody key: {group_key!r}"
            )
        current_group_keys.add(group_key)
        if accepted_key_map:
            component_id = accepted_key_map.get(group_key, "")
            if not component_id:
                raise BuildError(
                    "RP5C source-group custody-key set added an unknown group: "
                    f"{group_key_payload!r}"
                )
        else:
            component_id = source_component_id
        if component_id in records:
            raise BuildError(f"duplicate RP5C canonical identity: {component_id}")
        source_to_component[source_identity_id] = component_id
        members = [str(value) for value in row.get("duplicate_member_identity_row_ids", [])]
        if int(row.get("duplicate_member_count", len(members))) != len(members):
            raise BuildError(f"RP5C duplicate member count mismatch: {component_id}")
        member_set = set(members)
        if len(member_set) != len(members) or source_identity_id not in member_set:
            raise BuildError(f"RP5C duplicate member integrity mismatch: {component_id}")
        for member in members:
            _rp5c_component_id(member)
            if member in member_owner:
                raise BuildError(
                    f"RP5C duplicate member belongs to multiple groups: {member}"
                )
            member_owner[member] = source_identity_id
        source_members[source_identity_id] = member_set
        expected_lineage_rows += len(members)
        exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
        definition = _definition(
            display_name=component_id,
            description=(
                "Immutable RP5C baseline identity preserved without treating the "
                "baseline grouping as CONTROL1 semantic equivalence proof."
            ),
            component_kind="SPECIFICATION_REQUIRED",
            complete_definition=exact_action,
        )
        records[component_id] = _record(
            component_id=component_id,
            record_state="PROVISIONAL",
            origins=["RP5C_BASELINE"],
            definition=definition,
            decision_roles=["INTERNAL_SUPPORT"],
            bindings=[],
            provenance=[
                _rp5c_provenance(
                    dedupe_ref,
                    str(row.get("row_id") or component_id),
                    (
                        "canonical_identity_row_id",
                        "dedupe_status",
                        "duplicate_group_id",
                        "duplicate_member_count",
                    ),
                    component_id,
                    "IMMUTABLE_BASELINE_GROUPING_NOT_SEMANTIC_PROOF",
                    source_local_identity=source_identity_id,
                )
            ],
            relations=[
                {
                    "relation_type": "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF",
                    "source_group_custody_key": group_key_payload,
                    "source_canonical_identity_row_id": source_identity_id,
                    "source_duplicate_group_id": group_id,
                    "source_dedupe_status": row.get("dedupe_status"),
                    "source_occurrence_count": len(members),
                    "exact_lineage_validation_status": (
                        "SOURCE_MEMBERSHIP_RECONSTRUCTED_AND_CLOSED_AT_BUILD_TIME"
                    ),
                    "direct_semantic_equivalence_proven": False,
                    "exact_proof_action": (
                        f"MISSING_DIRECT_SEMANTIC_EQUIVALENCE_PROOF: {component_id}"
                        if len(members) > 1
                        else None
                    ),
                }
            ],
            producer_owner="RP5C_IMMUTABLE_BASELINE_VIA_CONTROL1_BUILDER",
        )
        metadata[component_id] = {
            "source_identity_id": source_identity_id,
            "names": set(),
            "identity_types": set(),
            "market_tags": set(),
            "ontology_categories": set(),
            "qku_roles": {},
            "stage1_seed": False,
            "dormant": False,
            "lineage_occurrence_count": 0,
            "lineage_source_artifact_row_ids": set(),
            "lineage_source_artifact_refs": set(),
            "lineage_provenance_tiers": set(),
            "lineage_custody_route_refs": set(),
        }

    if accepted_key_map and current_group_keys != set(accepted_key_map):
        missing = sorted(set(accepted_key_map) - current_group_keys)[:10]
        added = sorted(current_group_keys - set(accepted_key_map))[:10]
        raise BuildError(
            "RP5C source-group custody-key set drift: "
            f"missing={missing}, added={added}"
        )
    if set(source_group_keys) != set(source_to_component):
        missing = sorted(set(source_group_keys) - set(source_to_component))[:10]
        extra = sorted(set(source_to_component) - set(source_group_keys))[:10]
        raise BuildError(
            "RP5C canonical-library/dedupe identity closure drift: "
            f"missing={missing}, extra={extra}"
        )
    if len(records) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(
            "RP5C canonical identity count drift: "
            f"{len(records)} != {EXPECTED_RP5C_IDENTITIES}"
        )
    if (
        EXPECTED_RP5C_IDENTITIES == 10_189
        and expected_lineage_rows != EXPECTED_RP5C_OCCURRENCES
    ):
        raise BuildError(
            "RP5C source occurrence count drift: "
            f"{expected_lineage_rows} != {EXPECTED_RP5C_OCCURRENCES}"
        )

    for relative_path in RP5C_LIBRARIES:
        source_ref = relative_path.as_posix()
        for row in _iter_jsonl(repo_root / relative_path, deadline):
            source_identity_id = str(row.get("canonical_identity_row_id") or "")
            component_id = source_to_component.get(source_identity_id, "")
            if component_id not in records:
                raise BuildError(
                    f"{source_ref} references unknown canonical identity {source_identity_id!r}"
                )
            meta = metadata[component_id]
            identity_type = str(row.get("identity_type") or row.get("qku_type") or "")
            if identity_type:
                meta["identity_types"].add(identity_type)
            for field in ("qku_id", "formula_id", "formula_variant_id"):
                if row.get(field):
                    meta["names"].add(str(row[field]))
            for field in ("market_family", "qku_family", "formula_family"):
                value = str(row.get(field) or "")
                if value and "unknown" not in value.lower():
                    meta["market_tags"].add(value)
            meta["stage1_seed"] = bool(meta["stage1_seed"] or row.get("stage1_seed_inclusion_flag"))
            meta["dormant"] = bool(meta["dormant"] or row.get("stage1_dormant_future_market_flag"))
            qku_id = row.get("qku_id")
            ontology_category = str(row.get("ontology_category") or "")
            if ontology_category:
                meta["ontology_categories"].add(ontology_category)
            if qku_id:
                role_key = (
                    str(qku_id),
                    ontology_category or "SEMANTICS_UNRESOLVED",
                    str(row.get("market_family") or "UNRESOLVED"),
                )
                meta["qku_roles"][role_key] = {
                    "qku_id": str(qku_id),
                    "role_or_decision_stage": role_key[1],
                    "market_family": role_key[2],
                    "stack_root_or_direct_component": None,
                    "selection_rule_if_container": None,
                    "agent_policy_tags": sorted(set(row.get("agent_responsibility_group_refs", []))),
                    "source_refs": [source_ref, str(row.get("identity_row_id") or component_id)],
                    "exact_resolution_action": f"MISSING_SEMANTIC_SPECIFICATION: {component_id}",
                }
            records[component_id]["provenance"].append(
                _rp5c_provenance(
                    source_ref,
                    str(row.get("identity_row_id") or component_id),
                    (
                        "canonical_identity_row_id",
                        "identity_type",
                        "qku_id",
                        "formula_id",
                        "formula_variant_id",
                        "source_artifact_ref",
                        "source_artifact_row_id",
                        "source_line_or_json_path",
                        "formula_expression_ref",
                        "market_family",
                        "ontology_category",
                        "stage1_seed_inclusion_flag",
                        "stage1_dormant_future_market_flag",
                    ),
                    component_id,
                    "IMMUTABLE_BASELINE_LIBRARY_ROW",
                    source_local_identity=source_identity_id,
                )
            )
            if row.get("source_artifact_row_id"):
                meta["lineage_source_artifact_row_ids"].add(str(row["source_artifact_row_id"]))
            source_artifact_ref = row.get("source_artifact_ref")
            if source_artifact_ref not in (None, ""):
                if not isinstance(source_artifact_ref, str):
                    raise BuildError(
                        "RP5C immutable library has non-text source_artifact_ref: "
                        f"{source_ref}: {source_identity_id}: {source_artifact_ref!r}"
                    )
                meta["lineage_source_artifact_refs"].add(source_artifact_ref)

    lineage_ref = RP5C_LINEAGE.as_posix()
    lineage_rows = 0
    lineage_members: set[str] = set()
    for row in _iter_jsonl(repo_root / RP5C_LINEAGE, deadline):
        lineage_rows += 1
        source_identity_id = str(row.get("canonical_identity_row_id") or "")
        component_id = source_to_component.get(source_identity_id, "")
        if component_id not in records:
            raise BuildError(f"RP5C lineage references unknown identity {source_identity_id!r}")
        identity_row_id = str(row.get("identity_row_id") or "")
        if (
            not identity_row_id
            or member_owner.get(identity_row_id) != source_identity_id
            or identity_row_id not in source_members[source_identity_id]
        ):
            raise BuildError(
                "RP5C lineage member/canonical mismatch: "
                f"canonical={source_identity_id!r}, member={identity_row_id!r}"
            )
        if identity_row_id in lineage_members:
            raise BuildError(f"RP5C lineage repeats member identity: {identity_row_id}")
        lineage_members.add(identity_row_id)
        meta = metadata[component_id]
        meta["lineage_occurrence_count"] += 1
        if row.get("source_artifact_row_id"):
            meta["lineage_source_artifact_row_ids"].add(str(row["source_artifact_row_id"]))
        source_artifact_ref = row.get("source_artifact_ref")
        if source_artifact_ref not in (None, ""):
            if not isinstance(source_artifact_ref, str):
                raise BuildError(
                    "RP5C lineage has non-text source_artifact_ref: "
                    f"{source_identity_id}: {source_artifact_ref!r}"
                )
            meta["lineage_source_artifact_refs"].add(source_artifact_ref)
        if row.get("provenance_tier"):
            meta["lineage_provenance_tiers"].add(str(row["provenance_tier"]))
        meta["lineage_custody_route_refs"].update(
            str(value) for value in row.get("custody_route_refs", [])
        )
    if lineage_rows != expected_lineage_rows or lineage_members != set(member_owner):
        missing = sorted(set(member_owner) - lineage_members)[:10]
        extra = sorted(lineage_members - set(member_owner))[:10]
        raise BuildError(
            "RP5C lineage/dedupe closure drift: "
            f"lineage={lineage_rows}, dedupe_members={expected_lineage_rows}, "
            f"missing={missing}, extra={extra}"
        )

    for component_id, record in records.items():
        meta = metadata[component_id]
        names = sorted(meta["names"])
        identity_types = {value.upper() for value in meta["identity_types"]}
        if names:
            record["definition"]["display_name"] = names[0]
        if "QKU" in identity_types and "FORMULA" not in identity_types:
            record["definition"]["component_kind"] = "QKU_SELECTION_POLICY"
        elif "FORMULA" in identity_types:
            record["definition"]["component_kind"] = "PURE_FORMULA"
        record["uses"]["market_family_tags"] = sorted(meta["market_tags"])
        preserved_qku_roles = sorted(
            meta["qku_roles"].values(),
            key=lambda row: (
                row["qku_id"], row["role_or_decision_stage"], row["market_family"]
            ),
        )
        for role in preserved_qku_roles:
            role["runtime_root_eligibility"] = (
                "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            )
        record["uses"]["qku_role_bindings"] = preserved_qku_roles
        source_dormant = bool(meta["dormant"] and not meta["stage1_seed"])
        # RP5C supplies immutable identity/custody evidence, not complete
        # CONTROL1 semantics.  control.py correctly treats PROVISIONAL as an
        # active candidate state and defaults a null QKU root to the containing
        # record.  Therefore any incomplete RP5C row carrying preserved QKU
        # roles must remain non-runtime until a later proof-backed semantic
        # record supplies one direct root or selection policy.  We preserve the
        # source roles verbatim and do not invent a selector or choose a winner.
        incomplete_role_import = bool(preserved_qku_roles)
        dormant = bool(source_dormant or incomplete_role_import)
        record["record_state"] = "DORMANT_PRESERVED" if dormant else "PROVISIONAL"
        exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
        if incomplete_role_import:
            record["relations"].append(
                {
                    "relation_type": "RP5C_RUNTIME_ROOT_INELIGIBILITY",
                    "runtime_root_eligible": False,
                    "preserved_qku_role_count": len(preserved_qku_roles),
                    "source_stage1_dormant": source_dormant,
                    "reason": (
                        "INCOMPLETE_IMPORTED_SEMANTICS_CANNOT_BE_A_RUNTIME_QKU_ROOT"
                    ),
                    "exact_resolution_action": exact_action,
                    "selector_or_root_invented": False,
                    "qku_roles_erased": False,
                }
            )
        source_identity_id = str(meta["source_identity_id"])
        record["bindings"] = [
            _binding(
                component_id,
                definition=record["definition"],
                binding_id=f"BINDING.RP5C.REVIEW.{component_id.removeprefix('QTT.COMP.RP5C.')}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
                dormant=dormant,
            )
        ]
        record["provenance"].append(
            _rp5c_provenance(
                lineage_ref,
                f"canonical_identity:{component_id}",
                (
                    "identity_row_id",
                    "source_artifact_row_id",
                    "provenance_tier",
                    "custody_route_refs",
                    "no_deletion_flag",
                ),
                component_id,
                "IMMUTABLE_LINEAGE_SUMMARY",
                source_local_identity=source_identity_id,
            )
        )
        if not meta["lineage_source_artifact_refs"]:
            raise BuildError(
                "RP5C canonical identity has no inner source_artifact_ref: "
                f"{source_identity_id}"
            )
        record["relations"].append(
            {
                "relation_type": "RP5C_SOURCE_LINEAGE_SUMMARY",
                "source_canonical_identity_row_id": source_identity_id,
                "source_occurrence_count": meta["lineage_occurrence_count"],
                "source_artifact_refs": sorted(
                    meta["lineage_source_artifact_refs"]
                ),
                "source_artifact_ref_count": len(
                    meta["lineage_source_artifact_refs"]
                ),
                "source_artifact_row_count": len(
                    meta["lineage_source_artifact_row_ids"]
                ),
                "provenance_tiers": sorted(meta["lineage_provenance_tiers"]),
                "custody_route_refs": sorted(meta["lineage_custody_route_refs"]),
                "qku_role_market_ontology_summary": {
                    "qku_roles_location": "record.uses.qku_role_bindings",
                    "market_family_tags_location": "record.uses.market_family_tags",
                    "ontology_categories": sorted(
                        meta["ontology_categories"]
                    ),
                    "qku_role_count": len(meta["qku_roles"]),
                },
                "exact_lineage_validation_status": (
                    "SOURCE_OCCURRENCES_RECONSTRUCTED_AND_CLOSED_AT_BUILD_TIME"
                ),
                "immutable_original_preserved": True,
            }
        )
        record["provenance"].sort(
            key=lambda row: (str(row["source_artifact_ref"]), str(row["source_row_ref"]))
        )

        accepted = accepted_records.get(component_id)
        if accepted is not None:
            if str(accepted.get("semantic_version")) != str(record.get("semantic_version")):
                raise BuildError(f"RP5C semantic version drift requires successor: {component_id}")
            if _semantic_core(accepted) != _semantic_core(record):
                raise BuildError(f"RP5C semantic-core drift requires successor: {component_id}")

    ordered = [records[key] for key in sorted(records)]
    return _expansion_batch(
        batch_id="EXPANSION.RP5C.BASELINE",
        origin="RP5C_BASELINE",
        source_refs=[dedupe_ref, lineage_ref, *(path.as_posix() for path in RP5C_LIBRARIES)],
        source_classification="OWNER_SUBMITTED",
        items=ordered,
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="NOT_ELIGIBLE",
    )


def _import_r2a_modules(repo_root: Path) -> tuple[Any, Any, Any]:
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    base = "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations"
    try:
        return (
            importlib.import_module(f"{base}.formula_seed_library"),
            importlib.import_module(f"{base}.algorithm_seed_library"),
            importlib.import_module(f"{base}.quantum_seed_library"),
        )
    except ModuleNotFoundError as exc:
        raise BuildError(f"unable to import PR162D-R2A implementation inventory: {exc}") from exc


def _implementation_entry(
    *,
    version: str,
    callable_ref: str,
    latency_class: str,
    precision: str,
    memoizable: bool,
    proof_basis: str,
    security_state: str = "EXPLICIT_CONTROL_PLANE_ALLOWLIST_REQUIRED",
) -> dict[str, Any]:
    return {
        "implementation_version": version,
        "callable_or_solver_ref": callable_ref,
        "code_owner": "PR162D_R2A_SOURCE_OWNER",
        "supported_platforms": ["WINDOWS", "LINUX"],
        "pinned_dependencies": ["PYTHON_STANDARD_LIBRARY_OR_REPOSITORY_PINNED_DEPENDENCIES"],
        "determinism_seed_policy": "DETERMINISTIC_GIVEN_IDENTICAL_TYPED_INPUTS",
        "precision": precision,
        "latency_class": latency_class,
        "security_state": security_state,
        "memoizable": memoizable,
        "memoizable_proof_basis": proof_basis,
        "fallback": "FAIL_CLOSED",
    }


def _optional_native_implementation(component_id: str) -> dict[str, Any] | None:
    """Use a Decimal-native implementation only when control explicitly allows it."""
    mapping = getattr(_control_module(), "NATIVE_IMPLEMENTATIONS", None)
    if not isinstance(mapping, Mapping):
        raise BuildError("control owner lacks its explicit NATIVE_IMPLEMENTATIONS allowlist")
    native_ref_by_component = {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY": "qtt.computation_control.native:decimal_implied_probability",
        "QTT.COMP.FORMULA.PROBABILITY_EDGE": "qtt.computation_control.native:decimal_probability_edge",
        "QTT.COMP.FORMULA.MID_PRICE": "qtt.computation_control.native:decimal_mid_price",
        "QTT.COMP.FORMULA.SPREAD": "qtt.computation_control.native:decimal_spread",
        "QTT.COMP.FORMULA.RELATIVE_SPREAD": "qtt.computation_control.native:decimal_relative_spread",
    }
    ref = native_ref_by_component.get(component_id)
    if ref is None:
        return None
    candidate = mapping.get(ref)
    if not callable(candidate):
        raise BuildError(f"control native implementation allowlist drift: {ref}")
    value = _implementation_entry(
        version="control-native-decimal-v1",
        callable_ref=ref,
        latency_class="PRETRADE_BOUNDED",
        precision=(
            "DECIMAL_INPUT_BOUNDARY; ARITHMETIC_PRECISION_34; "
            "ROUND_HALF_EVEN; NO_ADDITIONAL_OUTPUT_QUANTIZATION"
        ),
        memoizable=True,
        proof_basis="CONTROL_MODULE_EXPLICIT_NATIVE_ALLOWLIST_AND_INDEPENDENT_CONTROL1_ORACLE",
        security_state="CONTROL1_NATIVE_ALLOWLIST",
    )
    value["code_owner"] = "CONTROL1_PRIVATE_RUNTIME"
    return value


def _closed_requirements(formula_id: str) -> list[dict[str, Any]]:
    requirement = {
        "required_semantic_version_constraint": "==1.0",
        "required_or_optional": "REQUIRED",
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }
    if formula_id == "PROBABILITY_EDGE":
        return [
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                "requirement_role": "IMPLIED_PROBABILITY_INPUT",
                "producer_output_name": "implied_probability",
                "consumer_input_name": "implied_probability",
            }
        ]
    if formula_id == "RELATIVE_SPREAD":
        return [
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.MID_PRICE",
                "requirement_role": "MID_PRICE_DENOMINATOR",
                "producer_output_name": "mid_price",
                "consumer_input_name": "mid_price",
            },
            {
                **requirement,
                "required_component_id_or_source_selector": "QTT.COMP.FORMULA.SPREAD",
                "requirement_role": "ABSOLUTE_SPREAD_NUMERATOR",
                "producer_output_name": "spread",
                "consumer_input_name": "spread",
            },
        ]
    return []


def _source_provenance(
    *,
    source_ref: str,
    row_ref: str,
    local_name: str,
    fields: Sequence[str],
    target: str,
    relation: str = "DIRECT_IMPLEMENTATION_CANDIDATE",
) -> dict[str, Any]:
    return {
        "source_artifact_ref": source_ref,
        "source_row_ref": row_ref,
        "source_local_identity_or_name": local_name,
        "source_fields_consumed": list(fields),
        "source_relation": relation,
        "canonical_target_ref": target,
        "proof_refs": [],
    }


def _closed_formula_fixture_inputs(spec: Any) -> dict[str, Any]:
    """Return one facade-level fixture lock for the closed arithmetic subgraphs."""

    fixtures: dict[str, dict[str, Any]] = {
        "IMPLIED_PROBABILITY": {"price": "0.43", "payout": "1"},
        # The source edge vector fixes implied_probability=0.52.  Its closed
        # DAG fixture derives that same value through the canonical upstream
        # formula with price=0.52 and payout=1; the requirement-owned output is
        # never mislabeled as a caller or direct source-fixture port.
        "PROBABILITY_EDGE": {"p_model": "0.58", "price": "0.52", "payout": "1"},
        "MID_PRICE": {"best_bid": "0.42", "best_ask": "0.46"},
        "SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
        # Both spread and midpoint are dependency-owned for this root.
        "RELATIVE_SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
    }
    return copy.deepcopy(fixtures.get(spec.formula_id, dict(spec.test_inputs)))


def _read_pr162d_test_vector_rows(repo_root: Path) -> dict[str, Mapping[str, Any]]:
    """Read the source registry with Decimal JSON numbers for exact fixture checks."""

    path = repo_root / PR162D_TEST_VECTOR_REGISTRY
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(
                handle,
                parse_float=Decimal,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    BuildError(f"non-finite JSON fixture number: {value}")
                ),
            )
    except OSError as exc:
        raise BuildError(f"unable to resolve PR162D fixture source: {path}: {exc}") from exc
    rows = payload.get("records") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise BuildError(f"PR162D fixture source has no records: {path}")
    by_ref: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise BuildError(f"PR162D fixture source row is not an object: {index}")
        fixture_ref = row.get("test_vector_id")
        if not isinstance(fixture_ref, str) or not fixture_ref:
            raise BuildError(f"PR162D fixture source row lacks test_vector_id: {index}")
        if fixture_ref in by_ref:
            raise BuildError(f"PR162D fixture source repeats test_vector_id: {fixture_ref}")
        by_ref[fixture_ref] = row
    return by_ref


def _closed_formula_fixture_contract(
    spec: Any,
    definition: Mapping[str, Any],
    source_row: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve one of the five closed formula fixtures to a build-only contract."""

    formula_id = str(spec.formula_id)
    if formula_id not in _CLOSED_FIXTURE_FORMULA_IDS:
        return None
    fixture_ref = f"PR162D_R2A_TV_FORMULA::{formula_id}"
    if not isinstance(source_row, Mapping) or source_row.get("test_vector_id") != fixture_ref:
        return None
    if source_row.get("callable_ref") != spec.callable_ref:
        return None
    if source_row.get("live_order_authority") is not False:
        return None
    source_inputs = source_row.get("inputs")
    source_outputs = source_row.get("expected_outputs")
    if not isinstance(source_inputs, Mapping) or set(source_inputs) != set(spec.required_inputs):
        return None
    if not isinstance(source_outputs, Mapping) or set(source_outputs) != set(spec.outputs):
        return None
    for name in spec.required_inputs:
        expected = spec.test_inputs[name]
        if isinstance(expected, bool) or not isinstance(expected, (int, float, Decimal)):
            return None
        if Decimal(str(expected)) != Decimal(str(source_inputs[name])):
            return None
    expected_outputs = spec.compute(copy.deepcopy(dict(spec.test_inputs)))
    if not isinstance(expected_outputs, Mapping) or set(expected_outputs) != set(
        source_outputs
    ):
        return None
    for name in spec.outputs:
        expected = expected_outputs[name]
        if isinstance(expected, bool) or not isinstance(expected, (int, float, Decimal)):
            return None
        if Decimal(str(expected)) != Decimal(str(source_outputs[name])):
            return None
    schema_by_name = {
        str(entry["name"]): entry
        for entry in definition.get("input_schema", ())
        if isinstance(entry, Mapping) and entry.get("name")
    }
    requirements_by_input = {
        str(requirement["consumer_input_name"]): requirement
        for requirement in definition.get("requirements", ())
        if isinstance(requirement, Mapping)
        and str(requirement.get("required_or_optional", "REQUIRED")).upper()
        != "OPTIONAL"
        and requirement.get("consumer_input_name")
    }
    if set(schema_by_name) != set(source_inputs):
        return None
    ports: list[dict[str, Any]] = []
    for name in sorted(schema_by_name):
        schema = schema_by_name[name]
        port: dict[str, Any] = {
            "input_name": name,
            "declared_type": str(schema.get("type", "")),
            "unit_or_basis": str(
                schema.get("unit_or_basis")
                or schema.get("unit")
                or schema.get("basis")
                or ""
            ),
            "value": source_inputs[name],
        }
        requirement = requirements_by_input.get(name)
        if requirement is None:
            port["ownership"] = "DIRECT_TYPED_REQUEST_INPUT"
        else:
            port.update(
                {
                    "ownership": "CANONICAL_REQUIREMENT_OUTPUT",
                    "required_component_id": requirement.get(
                        "required_component_id_or_source_selector"
                    ),
                    "producer_output_name": requirement.get(
                        "producer_output_name"
                    ),
                }
            )
        ports.append(port)
    contract = {
        "fixture_ref": fixture_ref,
        "source_resolution_state": "SOURCE_TEST_VECTOR_EXACTLY_RESOLVED",
        "source_artifact_ref": PR162D_TEST_VECTOR_REGISTRY.as_posix(),
        "source_row_ref": f"records[{fixture_ref}]",
        "ports": ports,
    }
    if _ephemeral_fixture_contract_issues(
        f"QTT.COMP.FORMULA.{formula_id}", definition, fixture_ref, contract
    ):
        return None
    return contract


def _closed_formula_domain(formula_id: str) -> str | None:
    """Pin the domain in which the source and Decimal implementations agree."""

    return {
        "IMPLIED_PROBABILITY": (
            "price and payout are finite Decimal-compatible values; payout >= 1e-9; "
            "0 <= price <= payout; output is price/payout in [0,1]"
        ),
        "PROBABILITY_EDGE": (
            "p_model and dependency-produced implied_probability are finite probabilities "
            "in [0,1]; output is their signed difference"
        ),
        "MID_PRICE": "finite prices satisfying 0 <= best_bid <= best_ask",
        "SPREAD": "finite prices satisfying 0 <= best_bid <= best_ask",
        "RELATIVE_SPREAD": (
            "dependency-produced spread is nonnegative and dependency-produced mid_price "
            "is at least 1e-9"
        ),
    }.get(formula_id)


def _schema_type(value: Any) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "FINITE_REAL"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, Mapping):
        return "TYPED_OBJECT"
    if isinstance(value, (list, tuple)):
        return "TYPED_SEQUENCE"
    if value is None:
        return "NULLABLE_VALUE"
    return "SOURCE_DECLARED_TYPED_VALUE"


def _formula_record(
    spec: Any,
    agent_ids: Sequence[str],
    source_fixture_row: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    component_id = f"QTT.COMP.FORMULA.{spec.formula_id}"
    latency = _latency_class(spec.latency_class)
    implementation_versions = [
        _implementation_entry(
            version="r2a-owner-template-v1",
            callable_ref=spec.callable_ref,
            latency_class=latency,
            precision="SOURCE_PYTHON_FLOAT_REQUIRES_TYPED_BOUNDARY_VALIDATION",
            memoizable=False,
            proof_basis="INDEPENDENT_SIDE_EFFECT_AND_NUMERICAL_REUSE_PROOF_REQUIRED",
        )
    ]
    native = _optional_native_implementation(component_id)
    if native is not None:
        implementation_versions.append(native)
    selected_version = native["implementation_version"] if native else "r2a-owner-template-v1"
    closed = spec.formula_id in _CLOSED_FIXTURE_FORMULA_IDS
    requirements = _closed_requirements(spec.formula_id)
    closed_input_units: dict[str, dict[str, str]] = {
        "IMPLIED_PROBABILITY": {"price": "price", "payout": "price"},
        "PROBABILITY_EDGE": {
            "p_model": "probability",
            "implied_probability": "probability",
        },
        "MID_PRICE": {"best_bid": "price", "best_ask": "price"},
        "SPREAD": {"best_bid": "price", "best_ask": "price"},
        "RELATIVE_SPREAD": {"spread": "price_delta", "mid_price": "price"},
    }
    input_units = closed_input_units.get(spec.formula_id, {})
    input_schema = [
        {
            "name": name,
            "type": "SOURCE_DECLARED_NUMERIC_OR_SEQUENCE",
            "required": True,
            "unit_or_basis": input_units.get(name, "EXACT_RUNTIME_UNIT_REQUIRED"),
        }
        for name in spec.required_inputs
    ]
    output_schema = [
        {
            "name": name,
            "type": "SOURCE_DECLARED_NUMERIC_OR_STRUCTURE",
            "unit_or_basis": spec.units_or_type_hints.get(name, "EXACT_UNIT_REQUIRED"),
        }
        for name in spec.outputs
    ]
    oracle_refs: list[Mapping[str, Any] | str] = [
        {
            "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{spec.formula_id}",
            "oracle_class": "SOURCE_DERIVED_FIXTURE_NOT_INDEPENDENT",
        }
    ]
    if closed:
        oracle_refs.append(
            {
                "ref": (
                    "tests/pr169_qku_comp_control1/test_control1.py::"
                    "test_closed_formula_decimal_oracles_are_independent"
                ),
                "oracle_class": "INDEPENDENT_DECIMAL_OR_EXACT_ARITHMETIC",
            }
        )
    definition = _definition(
        display_name=spec.formula_id,
        description=f"PR162D-R2A owner-template formula candidate: {spec.expression}",
        component_kind="PURE_FORMULA",
        complete_definition=spec.expression,
        inputs=input_schema,
        outputs=output_schema,
        units={**input_units, **dict(spec.units_or_type_hints)},
        requirements=requirements,
        latency_class=latency,
        implementation_versions=implementation_versions,
        oracle_refs=oracle_refs,
        inventory_class="FORMULA",
    )
    definition["family_template_ref_or_null"] = None
    definition["assumptions"] = [
        "OWNER_TEMPLATE_SEMANTICS_REQUIRE_INDEPENDENT_DOMAIN_AND_BOUNDARY_REVIEW"
    ]
    definition["precision_and_rounding"] = (
        {
            "numeric_boundary": "PYTHON_DECIMAL_FROM_TEXT_OR_INTEGER_ONLY",
            "arithmetic_precision_significant_digits": 34,
            "rounding": "ROUND_HALF_EVEN",
            "output_quantization": "NONE_ADDITIONAL",
        }
        if native
        else "SOURCE_PYTHON_FLOAT_NONLIVE_FIXTURE_ONLY"
    )
    closed_domain = _closed_formula_domain(spec.formula_id)
    if closed_domain is not None:
        definition["domain_and_boundary_behavior"] = closed_domain
    if closed:
        implementation_versions[0]["selection_state"] = (
            "SOURCE_INVENTORY_ONLY_FLOAT_AND_DOMAIN_FAILURE_SEMANTICS_NOT_SELECTED"
        )
        for entry in definition["input_schema"]:
            entry["type"] = "FINITE_DECIMAL_COMPATIBLE_SCALAR"
        for entry in definition["output_schema"]:
            entry["type"] = "FINITE_DECIMAL_COMPATIBLE_SCALAR"
        definition["assumptions"] = [
            "PURE_STATELESS_SCALAR_ARITHMETIC_ON_ONE_IMMUTABLE_REQUEST_INPUT_LOCK"
        ]
        definition["state_and_time_semantics"] = {
            "state": "STATELESS",
            "time": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
        }
        definition["missing_stale_nonfinite_behavior"] = {
            "missing": "FAIL_CLOSED",
            "stale": "FAIL_CLOSED",
            "nonfinite": "FAIL_CLOSED",
        }
        definition["precision_and_rounding"] = {
            "numeric_boundary": "PYTHON_DECIMAL_FROM_TEXT_OR_INTEGER_ONLY",
            "arithmetic_precision_significant_digits": 34,
            "rounding": "ROUND_HALF_EVEN",
            "output_quantization": "NONE_ADDITIONAL",
        }
        definition["parameter_schema_and_default_provenance"] = {
            "parameters": [],
            "default_provenance": "NO_CONFIGURABLE_PARAMETERS_IN_FORMULA_SEMANTICS",
        }
        definition["classical_fallback"] = {
            "not_applicable": True,
            "proof_ref": "PURE_FORMULA_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
        }
        definition["risk_materiality"].update(
            {
                "economic_materiality": "NONLIVE_FIXTURE_ARITHMETIC_ONLY",
                "complexity": "CONSTANT_TIME_SCALAR_ARITHMETIC",
                "data_dependency": "TYPED_IMMUTABLE_FIXTURE_INPUTS",
            }
        )
        closed_meanings: dict[str, dict[str, Any]] = {
            "IMPLIED_PROBABILITY": {
                "description": (
                    "Normalized contract-price-to-payout ratio for one outcome, "
                    "instrument, venue, and as-of lock; it is not calibrated belief, "
                    "fair value, expected value, or profit."
                ),
                "definition": (
                    "implied_probability = price / payout on the declared valid domain; "
                    "invalid domain fails closed rather than clipping"
                ),
                "assumptions": [
                    "PRICE_AND_PAYOUT_SHARE_ONE_CONTRACT_OUTCOME_CURRENCY_BASIS",
                    "SAME_INSTRUMENT_VENUE_AND_AS_OF_INPUT_LOCK",
                    "NORMALIZED_PRICE_PROXY_IS_NOT_EVENT_PROBABILITY_WITHOUT_ADDITIONAL_MARKET_ASSUMPTIONS",
                ],
                "accounting": "NON_ACCOUNTING_NORMALIZED_PRICE_PROXY",
            },
            "PROBABILITY_EDGE": {
                "description": (
                    "Signed dimensionless difference between a pinned model probability "
                    "and the canonical normalized price proxy; it is not EV, cash PnL, "
                    "executable edge, or a profit claim."
                ),
                "definition": (
                    "probability_edge = p_model - implied_probability, where "
                    "implied_probability is produced by QTT.COMP.FORMULA.IMPLIED_PROBABILITY"
                ),
                "assumptions": [
                    "MODEL_AND_NORMALIZED_PRICE_REFER_TO_THE_SAME_OUTCOME_AND_AS_OF_LOCK",
                    "BOTH_INPUTS_USE_DECIMAL_PROBABILITY_BASIS_IN_CLOSED_INTERVAL_ZERO_ONE",
                    "PROBABILITY_DELTA_HAS_NO_CASH_OR_EXECUTION_ACCOUNTING_MEANING",
                ],
                "accounting": "NON_ACCOUNTING_PROBABILITY_DELTA",
            },
            "MID_PRICE": {
                "description": (
                    "Arithmetic top-of-book quote midpoint for the same instrument, "
                    "outcome, venue, and snapshot; it is not an executable price."
                ),
                "definition": "mid_price = (best_bid + best_ask) / 2",
                "assumptions": [
                    "BEST_BID_AND_BEST_ASK_SHARE_ONE_INSTRUMENT_OUTCOME_VENUE_AND_SNAPSHOT",
                    "QUOTE_BOOK_IS_UNCROSSED_WITH_ZERO_LESS_THAN_OR_EQUAL_TO_BID_LESS_THAN_OR_EQUAL_TO_ASK",
                    "ARITHMETIC_MIDPOINT_IS_NOT_AN_EXECUTABLE_FILL_PRICE",
                ],
                "accounting": "NON_ACCOUNTING_QUOTE_MIDPOINT",
            },
            "SPREAD": {
                "description": (
                    "Full quoted ask-minus-bid spread for the same instrument, outcome, "
                    "venue, and snapshot; it is not half-spread or realized spread."
                ),
                "definition": "spread = best_ask - best_bid",
                "assumptions": [
                    "BEST_BID_AND_BEST_ASK_SHARE_ONE_INSTRUMENT_OUTCOME_VENUE_AND_SNAPSHOT",
                    "QUOTE_BOOK_IS_UNCROSSED_WITH_ZERO_LESS_THAN_OR_EQUAL_TO_BID_LESS_THAN_OR_EQUAL_TO_ASK",
                    "OUTPUT_IS_FULL_QUOTED_SPREAD_NOT_HALF_OR_REALIZED_SPREAD",
                ],
                "accounting": "NON_ACCOUNTING_QUOTE_PRICE_DELTA",
            },
            "RELATIVE_SPREAD": {
                "description": (
                    "Full quoted spread divided by the canonical arithmetic quote "
                    "midpoint for one instrument/venue/snapshot; the output is a ratio, "
                    "not percent or basis points without explicit conversion."
                ),
                "definition": (
                    "relative_spread = spread / mid_price, with spread and mid_price "
                    "produced by the canonical same-lock requirement nodes"
                ),
                "assumptions": [
                    "SPREAD_AND_MIDPOINT_SHARE_ONE_INSTRUMENT_OUTCOME_VENUE_AND_SNAPSHOT",
                    "NUMERATOR_IS_FULL_ASK_MINUS_BID_SPREAD",
                    "OUTPUT_REMAINS_DECIMAL_RATIO_UNTIL_EXPLICIT_PERCENT_OR_BASIS_POINT_CONVERSION",
                ],
                "accounting": "NON_ACCOUNTING_QUOTE_SPREAD_RATIO",
            },
        }
        meaning = closed_meanings[spec.formula_id]
        definition["description"] = meaning["description"]
        definition["complete_mathematical_or_procedural_definition"] = meaning[
            "definition"
        ]
        definition["assumptions"] = list(meaning["assumptions"])
        definition["output_accounting_class"] = meaning["accounting"]
    action = None if closed else f"MISSING_INDEPENDENT_ORACLE: {component_id}@1.0"
    fixture_ref = f"PR162D_R2A_TV_FORMULA::{spec.formula_id}"
    fixture_contract = _closed_formula_fixture_contract(
        spec, definition, source_fixture_row
    )
    binding = _binding(
        component_id,
        definition=definition,
        binding_id=f"BINDING.FIXTURE.FORMULA.{spec.formula_id}",
        agent_ids=agent_ids,
        implementation_version=selected_version,
        exact_action=action,
        fixture_ref=fixture_ref,
        fixture_contract=fixture_contract,
        requirements_ready=True,
        oracle_ready=closed,
    )
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED"],
        definition=definition,
        decision_roles=_decision_roles(spec.domain_family_key),
        bindings=[binding],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/formula_seed_library.py"
                ),
                row_ref=f"formula_specs[{spec.formula_id}]",
                local_name=spec.formula_id,
                fields=(
                    "formula_id",
                    "expression",
                    "callable_ref",
                    "required_inputs",
                    "outputs",
                    "units_or_type_hints",
                    "domain_family_key",
                    "subfamily_key",
                    "variant_key",
                    "latency_class",
                ),
                target=component_id,
            )
        ],
        market_tags=[spec.domain_family_key],
    )


def _algorithm_record(spec: Any, agent_ids: Sequence[str]) -> dict[str, Any]:
    component_id = f"QTT.COMP.ALGORITHM.{spec.algorithm_id}"
    latency = _latency_class(spec.latency_class)
    units = {
        **{name: "SOURCE_DECLARED_TYPED_INPUT_BASIS" for name in spec.required_inputs},
        **{name: "SOURCE_DECLARED_TYPED_OUTPUT_BASIS" for name in spec.outputs},
    }
    definition = _definition(
        display_name=spec.algorithm_id,
        description="PR162D-R2A deterministic procedure candidate.",
        component_kind="NUMERICAL_ALGORITHM",
        complete_definition=spec.procedure,
        inputs=[
            {
                "name": name,
                "type": "SOURCE_DECLARED_TYPED_VALUE",
                "required": True,
                "unit_or_basis": "EXACT_RUNTIME_CONTRACT_REQUIRED",
            }
            for name in spec.required_inputs
        ],
        outputs=[
            {
                "name": name,
                "type": "SOURCE_DECLARED_TYPED_VALUE",
                "unit_or_basis": "SOURCE_DECLARED",
            }
            for name in spec.outputs
        ],
        units=units,
        latency_class=latency,
        implementation_versions=[
            _implementation_entry(
                version="r2a-owner-template-v1",
                callable_ref=spec.callable_ref,
                latency_class=latency,
                precision="SOURCE_PROCEDURE_TYPED_OUTPUT",
                memoizable=False,
                proof_basis="ALGORITHM_REUSE_SAFETY_REQUIRES_INDEPENDENT_PROOF",
            )
        ],
        oracle_refs=[
            {
                "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{spec.algorithm_id}",
                "oracle_class": "SOURCE_DERIVED_FIXTURE_NOT_INDEPENDENT",
            }
        ],
        inventory_class="ALGORITHM",
    )
    definition["failure_domain_tags"] = sorted(
        set(definition["failure_domain_tags"]) | set(spec.failure_modes)
    )
    action = f"MISSING_INDEPENDENT_ORACLE: {component_id}@1.0"
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED"],
        definition=definition,
        decision_roles=_decision_roles(spec.domain_family_key),
        bindings=[
            _binding(
                component_id,
                definition=definition,
                binding_id=f"BINDING.FIXTURE.ALGORITHM.{spec.algorithm_id}",
                agent_ids=agent_ids,
                implementation_version="r2a-owner-template-v1",
                exact_action=action,
                fixture_ref=f"PR162D_R2A_TV_ALGORITHM::{spec.algorithm_id}",
                requirements_ready=True,
                oracle_ready=False,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/algorithm_seed_library.py"
                ),
                row_ref=f"algorithm_specs[{spec.algorithm_id}]",
                local_name=spec.algorithm_id,
                fields=(
                    "algorithm_id",
                    "procedure",
                    "callable_ref",
                    "required_inputs",
                    "outputs",
                    "domain_family_key",
                    "subfamily_key",
                    "variant_key",
                    "failure_modes",
                    "latency_class",
                ),
                target=component_id,
            )
        ],
        market_tags=[spec.domain_family_key],
    )


_QUANTUM_BUILDER_INPUT_KEYS: Mapping[str, tuple[str, ...]] = {
    "build_qubo_market_bundle_selection": ("candidates", "covariance", "budget", "max_exposure"),
    "build_cqm_constrained_capital_allocation": ("candidates", "capital_budget", "max_exposure"),
    "build_qubo_parameter_stack_selection": ("candidates", "incompatibility"),
    "build_latency_adjusted_opportunity_selection": ("candidates",),
    "build_ising_binary_selection": ("candidates", "h", "J"),
    "build_qaoa_candidate_selection_shape": ("candidates", "covariance", "budget", "max_exposure"),
    "build_annealing_candidate_selection_shape": ("candidates", "covariance", "budget", "max_exposure"),
    "build_bqm_risk_balanced_selection": ("candidates", "covariance", "budget", "max_exposure"),
    "build_cqm_route_fill_allocation": ("candidates", "route_fill_budget"),
}


def _quantum_callable_contract(
    representative: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    builder_name = representative.build_shape.__name__
    required_keys = _QUANTUM_BUILDER_INPUT_KEYS.get(builder_name)
    if required_keys is None:
        raise BuildError(f"unreviewed quantum builder input contract: {builder_name}")
    missing = sorted(set(required_keys) - set(representative.test_inputs))
    if missing:
        raise BuildError(f"quantum builder fixture lacks required inputs: {builder_name}: {missing}")
    fixture_inputs = {
        key: copy.deepcopy(representative.test_inputs[key]) for key in required_keys
    }
    shape = representative.build_shape(copy.deepcopy(fixture_inputs))
    if not isinstance(shape, Mapping) or not shape:
        raise BuildError(f"quantum builder returned no structural mapping: {builder_name}")
    input_units = {
        "candidates": "ORIGINAL_ECONOMIC_CANDIDATE_FIELDS_WITH_DECLARED_UNITS",
        "covariance": "PAIRWISE_RISK_COVARIANCE_BASIS",
        "budget": "ORIGINAL_ECONOMIC_CAPITAL_BASIS",
        "capital_budget": "ORIGINAL_ECONOMIC_CAPITAL_BASIS",
        "max_exposure": "ORIGINAL_ECONOMIC_EXPOSURE_BASIS",
        "incompatibility": "DIMENSIONLESS_PAIRWISE_INDICATOR",
        "h": "ISING_LINEAR_ENERGY_COEFFICIENT",
        "J": "ISING_PAIRWISE_ENERGY_COEFFICIENT",
        "route_fill_budget": "ROUTE_FILL_COST_BASIS",
    }
    output_units = {
        "objective": "SYMBOLIC_OBJECTIVE_PRESERVING_DECLARED_ECONOMIC_OR_ENERGY_BASIS",
        "coefficients": "STRUCTURED_COEFFICIENTS_WITH_SOURCE_FIELD_LINEAGE",
        "variables": "ENCODED_VARIABLE_DECLARATIONS",
        "domains": "ENCODED_DOMAIN_DECLARATIONS",
        "constraints": "ENCODED_CONSTRAINT_DECLARATIONS",
        "penalties": "ENCODED_PENALTY_DECLARATIONS",
        "shape_type": "FORMULATION_CLASS_LABEL",
        "backend_execution": "BOOLEAN_NON_EXECUTION_FLAG",
        "quantum_advantage_claim": "BOOLEAN_NO_ADVANTAGE_CLAIM_FLAG",
    }
    input_schema = [
        {
            "name": key,
            "type": _schema_type(fixture_inputs[key]),
            "required": True,
            "unit_or_basis": input_units[key],
        }
        for key in required_keys
    ]
    output_schema = [
        {
            "name": key,
            "type": _schema_type(shape[key]),
            "unit_or_basis": output_units.get(key, "STRUCTURAL_MAPPING_METADATA"),
        }
        for key in sorted(shape)
    ]
    units = {
        **{key: input_units[key] for key in required_keys},
        **{
            key: output_units.get(key, "STRUCTURAL_MAPPING_METADATA")
            for key in sorted(shape)
        },
    }
    return fixture_inputs, input_schema, output_schema, units


def _quantum_family_record(specs: Sequence[Any], agent_ids: Sequence[str]) -> dict[str, Any]:
    ordered_specs = sorted(specs, key=lambda value: value.quantum_formulation_id)
    representative = ordered_specs[0]
    builder_name = representative.build_shape.__name__.removeprefix("build_").upper()
    component_id = f"QTT.COMP.QUANTUM.{builder_name}"
    callable_ref = representative.callable_ref
    if any(spec.callable_ref != callable_ref for spec in ordered_specs):
        raise BuildError(f"quantum callable family is not callable-stable: {builder_name}")
    fixture_inputs, input_schema, output_schema, units = _quantum_callable_contract(
        representative
    )
    original_model_id = f"QTT.COMP.ECONOMIC_MODEL.{builder_name}"
    quantum = {
        "applicability_state": "SPECIFIED_MAPPING_CANDIDATE",
        "original_economic_problem_ref": original_model_id,
        "problem_family": representative.subfamily_key,
        "formulation_candidates": [spec.quantum_formulation_id for spec in ordered_specs],
        "selected_formulation_or_none": None,
        "variable_encoding": sorted(set(representative.variables)),
        "objective_map": representative.objective,
        "constraint_map": list(representative.constraints),
        "penalty_policy": list(representative.penalties),
        "coefficient_scaling": "SOURCE_TEMPLATE_REQUIRES_INDEPENDENT_SENSITIVITY_PROOF",
        "precision_and_quantization": "SOURCE_PYTHON_FLOAT_STRUCTURAL_SHAPE_ONLY",
        "decomposition_or_embedding": None,
        "warm_start": None,
        "optimizer_and_version": None,
        "shots_reads_or_sampling_policy": None,
        "seed_resampling_policy": "DETERMINISTIC_LOCAL_SHAPE_NO_QPU_SAMPLING",
        "inverse_map": "MISSING_FEASIBLE_INVERSE_MAP_PROOF",
        "original_model_feasibility_check": "MISSING_ORIGINAL_MODEL_PARITY_PROOF",
        "same_formulation_classical_comparator": sorted(
            {spec.classical_comparator_ref for spec in ordered_specs}
        ),
        "local_exact_or_small_instance_parity": "REQUIRED",
        "fallback": "DETERMINISTIC_CLASSICAL_COMPARATOR_REQUIRED",
        "maturity_ceiling": "SPECIFIED",
    }
    definition = _definition(
        display_name=builder_name,
        description=(
            "One callable-family record preserving all PR162D quantum formulation "
            "roles without treating an encoding as an alias of its economic model."
        ),
        component_kind="QUANTUM_FORMULATION",
        complete_definition=representative.objective,
        inputs=input_schema,
        outputs=output_schema,
        units=units,
        latency_class="HOTPATH_FORBIDDEN",
        implementation_versions=[
            _implementation_entry(
                version="r2a-owner-template-v1",
                callable_ref=callable_ref,
                latency_class="HOTPATH_FORBIDDEN",
                precision="SOURCE_PYTHON_FLOAT_STRUCTURAL_SHAPE_ONLY",
                memoizable=False,
                proof_basis="ORIGINAL_MODEL_MAPPING_AND_INVERSE_PARITY_REQUIRED",
            )
        ],
        oracle_refs=[
            {
                "ref": f"docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json#{builder_name}",
                "oracle_class": "STRUCTURAL_SOURCE_FIXTURE_NOT_ORIGINAL_MODEL_PARITY",
            }
        ],
        quantum=quantum,
        inventory_class="QUANTUM_CALLABLE_FAMILY",
    )
    definition["risk_materiality"]["quantum_backend_dependency"] = False
    action = f"MISSING_QUANTUM_ORIGINAL_MODEL_LOCAL_PARITY: {component_id}@1.0"
    provenance = [
        _source_provenance(
            source_ref=(
                "src/qtt/stage1_prediction_markets/"
                "pr162d_r2a_real_formulations/quantum_seed_library.py"
            ),
            row_ref=f"quantum_specs[{spec.quantum_formulation_id}]",
            local_name=spec.quantum_formulation_id,
            fields=(
                "quantum_formulation_id",
                "objective",
                "callable_ref",
                "variables",
                "domains",
                "constraints",
                "penalties",
                "mapping_rationale",
                "classical_comparator_ref",
            ),
            target=component_id,
            relation="CALLABLE_FAMILY_ROLE_PRESERVED_NO_EQUIVALENCE_TO_ORIGINAL_MODEL",
        )
        for spec in ordered_specs
    ]
    return _record(
        component_id=component_id,
        record_state="CANONICAL_ACCEPTED",
        origins=["PR162D_IMPLEMENTATION_BACKED", "PR162E_Q_QUANTUM_MAPPING"],
        definition=definition,
        decision_roles=_decision_roles(representative.domain_family_key, quantum=True),
        bindings=[
            _binding(
                component_id,
                definition=definition,
                binding_id=f"BINDING.FIXTURE.QUANTUM.{builder_name}",
                agent_ids=agent_ids,
                implementation_version="r2a-owner-template-v1",
                exact_action=action,
                fixture_ref=f"PR162D_R2A_TV_QUANTUM_FAMILY::{builder_name}",
                requirements_ready=True,
                oracle_ready=False,
            )
        ],
        provenance=provenance,
        relations=[
            {
                "relation_type": "ENCODES_OR_MAPS",
                "canonical_target_ref": original_model_id,
                "proof_refs": [
                    (
                        "src/qtt/stage1_prediction_markets/"
                        "pr162d_r2a_real_formulations/quantum_seed_library.py::"
                        f"{representative.build_shape.__name__}"
                    )
                ],
                "mapping_state": "STRUCTURAL_MAPPING_CANDIDATE_LOCAL_PARITY_REQUIRED",
                "alias_equivalence_claim": False,
            },
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": original_model_id,
                "proof_refs": [
                    "CONTROL1_PROOF::ORIGINAL_ECONOMIC_MODEL_AND_ENCODED_VARIABLE_OBJECTIVE_ARE_DISTINCT"
                ],
                "direct_distinction_basis": (
                    "The original economic decision model and its encoded variables, "
                    "penalties, coefficient scaling, and inverse map have different semantics."
                ),
            },
        ],
        market_tags=[representative.domain_family_key],
    )


def _original_economic_model_record(
    quantum_record: Mapping[str, Any], agent_ids: Sequence[str]
) -> dict[str, Any]:
    quantum_id = str(quantum_record["canonical_component_id"])
    quantum_definition = quantum_record["definition"]
    component_id = str(quantum_definition["quantum"]["original_economic_problem_ref"])
    exact_action = f"MISSING_ORIGINAL_ECONOMIC_MODEL_SPECIFICATION: {component_id}@1.0"
    definition = _definition(
        display_name=component_id.rsplit(".", 1)[-1],
        description=(
            "Provisional original economic-model target required to keep the "
            "economic decision model distinct from its quantum encoding."
        ),
        component_kind="OPTIMIZATION_PROGRAM",
        complete_definition=exact_action,
        inputs=quantum_definition["input_schema"],
        outputs=[
            {
                "name": "selected_candidate_ids",
                "type": "TYPED_SEQUENCE",
                "unit_or_basis": "ORIGINAL_ECONOMIC_DECISION_IDENTITIES",
            },
            {
                "name": "original_objective_value",
                "type": "FINITE_REAL",
                "unit_or_basis": "ORIGINAL_ECONOMIC_OBJECTIVE_BASIS_REQUIRED",
            },
        ],
        units={
            **dict(quantum_definition["units_and_bases"]),
            "selected_candidate_ids": "ORIGINAL_ECONOMIC_DECISION_IDENTITIES",
            "original_objective_value": "ORIGINAL_ECONOMIC_OBJECTIVE_BASIS_REQUIRED",
        },
        latency_class="BATCH_PRECOMPUTE",
    )
    definition["objective_sense_or_null"] = "REQUIRES_INDEPENDENT_ORIGINAL_MODEL_CLOSE"
    definition["assumptions"] = [
        "THE_ENCODING_OBJECTIVE_IS_NOT_ACCEPTED_AS_THE ORIGINAL_ECONOMIC_MODEL",
        "VARIABLE_DOMAINS_CONSTRAINTS_UNITS_AND_INVERSE_INTERPRETATION_REQUIRE_DIRECT_PROOF",
    ]
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=["PR162D_IMPLEMENTATION_BACKED", "PR162E_Q_QUANTUM_MAPPING"],
        definition=definition,
        decision_roles=["INTERNAL_SUPPORT", "RESEARCH_EVIDENCE_AND_MODEL_VALIDATION"],
        bindings=[
            _binding(
                component_id,
                definition=definition,
                binding_id=f"BINDING.RESEARCH.ECONOMIC_MODEL.{component_id.rsplit('.', 1)[-1]}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref=(
                    "src/qtt/stage1_prediction_markets/"
                    "pr162d_r2a_real_formulations/quantum_seed_library.py"
                ),
                row_ref=f"quantum_mapping_target[{quantum_id}]",
                local_name=component_id,
                fields=("objective", "variables", "domains", "constraints", "test_inputs"),
                target=component_id,
                relation="ORIGINAL_MODEL_TARGET_EXTRACTED_BUT_NOT_PROVEN_BY_ENCODING",
            )
        ],
        relations=[
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": quantum_id,
                "proof_refs": [
                    "CONTROL1_PROOF::ORIGINAL_ECONOMIC_MODEL_AND_ENCODED_VARIABLE_OBJECTIVE_ARE_DISTINCT"
                ],
                "direct_distinction_basis": (
                    "Original economic variables, constraints, units, and decision "
                    "interpretation cannot be aliased to an encoding."
                ),
            }
        ],
        market_tags=["quantum_original_economic_model_candidate"],
    )


def _apply_source_backed_semantic_relations(
    records: Sequence[dict[str, Any]],
) -> None:
    by_id = {str(record["canonical_component_id"]): record for record in records}
    family_target = "QTT.COMP.FORMULA.NET_EDGE"
    family_members = (
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
        "QTT.COMP.FORMULA.CAPITAL_UTILIZATION",
        "QTT.COMP.FORMULA.EXPOSURE_UTILIZATION",
        "QTT.COMP.FORMULA.COST_TO_BUDGET_RATIO",
    )
    family_domain = (
        "finite numerator and denominator in one declared contextual scalar basis; "
        "denominator >= 1e-9; output is a finite dimensionless ratio"
    )
    family_proof_refs = [
        (
            "src/qtt/stage1_prediction_markets/"
            "pr162d_r2a_real_formulations/formula_seed_library.py::"
            "compute_net_edge,compute_relative_spread,compute_capital_utilization,"
            "compute_exposure_utilization,compute_cost_to_budget_ratio"
        ),
        "CONTROL1_DIRECT_PROOF::SAFE_RATIO_OPERATOR_DOMAIN_BOUNDARY_AND_DIMENSIONAL_SIGNATURE",
    ]
    for family_id in (family_target, *family_members):
        family_definition = by_id[family_id]["definition"]
        family_definition["family_template_ref_or_null"] = family_target
        family_definition["domain_and_boundary_behavior"] = family_domain
        for input_entry in family_definition["input_schema"][:2]:
            input_entry["unit_or_basis"] = "SAME_CONTEXTUAL_SCALAR_BASIS"
        family_definition["output_schema"][0]["unit_or_basis"] = "DIMENSIONLESS_RATIO"
        family_definition["units_and_bases"] = {
            family_definition["input_schema"][0]["name"]: "SAME_CONTEXTUAL_SCALAR_BASIS",
            family_definition["input_schema"][1]["name"]: "SAME_CONTEXTUAL_SCALAR_BASIS",
            family_definition["output_schema"][0]["name"]: "DIMENSIONLESS_RATIO",
        }
    # A family template never erases a member's concrete port contract.  The
    # closed RELATIVE_SPREAD DAG is pinned to the exact producer units used by
    # MID_PRICE and SPREAD while retaining the proof-backed ratio-family link.
    relative_definition = by_id["QTT.COMP.FORMULA.RELATIVE_SPREAD"]["definition"]
    relative_units = {
        "spread": "price_delta",
        "mid_price": "price",
        "relative_spread": "ratio",
    }
    for entry in (
        *relative_definition["input_schema"],
        *relative_definition["output_schema"],
    ):
        entry["unit_or_basis"] = relative_units[str(entry["name"])]
    relative_definition["units_and_bases"] = relative_units
    for member_id in family_members:
        member = by_id[member_id]
        member["definition"]["equivalence_proof_refs"].append(
            {
                "proof_id": f"CONTROL1.FAMILY_SAFE_RATIO.{member_id.rsplit('.', 1)[-1]}",
                "proof_class": "DIRECT_PARAMETERIZED_FAMILY_COMPATIBILITY",
                "canonical_target_ref": family_target,
                "operator_shape": "numerator/max(denominator,1e-9)",
                "complete_compatibility_dimensions": [
                    "OPERATOR",
                    "DIMENSIONLESS_OUTPUT",
                    "DENOMINATOR_FLOOR",
                    "STATELESS_SAME_REQUEST",
                    "FAIL_CLOSED_NONFINITE_BOUNDARY",
                ],
                "proof_refs": family_proof_refs,
            }
        )
        member["relations"].append(
            {
                "relation_type": "FAMILY_BINDING_OF",
                "canonical_target_ref": family_target,
                "proof_refs": family_proof_refs,
                "parameter_mapping": {
                    "numerator": member["definition"]["input_schema"][0]["name"],
                    "denominator": member["definition"]["input_schema"][1]["name"],
                    "output": member["definition"]["output_schema"][0]["name"],
                    "epsilon": "1e-9",
                },
                "alias_equivalence_claim": False,
            }
        )

    yes_record = by_id["QTT.COMP.FORMULA.YES_EV"]
    no_record = by_id["QTT.COMP.FORMULA.NO_EV"]
    distinct_proof = [
        (
            "src/qtt/stage1_prediction_markets/"
            "pr162d_r2a_real_formulations/formula_seed_library.py::"
            "compute_yes_ev,compute_no_ev"
        ),
        "CONTROL1_DIRECT_PROOF::YES_AND_NO_EVENT_PAYOFF_PORTS_AND_PROBABILITY_COMPLEMENT_DIFFER",
    ]
    for source, target in ((yes_record, no_record), (no_record, yes_record)):
        source["relations"].append(
            {
                "relation_type": "DISTINCT_FROM",
                "canonical_target_ref": target["canonical_component_id"],
                "proof_refs": distinct_proof,
                "direct_distinction_basis": (
                    "YES and NO expected-value procedures use different price ports and "
                    "complemented probability semantics; shared cost terms do not make them aliases."
                ),
            }
        )

    for record in records:
        record["relations"].sort(
            key=lambda relation: (
                str(relation.get("relation_type", "")),
                str(relation.get("source_identity_or_alias", "")),
                str(relation.get("canonical_target_ref", "")),
            )
        )
        record["provenance"].sort(
            key=lambda row: (str(row["source_artifact_ref"]), str(row["source_row_ref"]))
        )


def _verify_fixed_source_fixtures(
    formula_specs: Sequence[Any],
    algorithm_specs: Sequence[Any],
    quantum_by_callable: Mapping[str, Sequence[Any]],
) -> dict[str, Any]:
    """Invoke bounded source fixtures without persisting any fixture vectors."""

    counts: Counter[str] = Counter()
    for spec in formula_specs:
        output = spec.compute(copy.deepcopy(dict(spec.test_inputs)))
        if not isinstance(output, Mapping):
            raise BuildError(f"formula fixture returned non-object: {spec.formula_id}")
        _json_line(output)
        counts["FORMULA"] += 1
    for spec in algorithm_specs:
        output = spec.implementation(copy.deepcopy(dict(spec.test_inputs)))
        if not isinstance(output, Mapping):
            raise BuildError(f"algorithm fixture returned non-object: {spec.algorithm_id}")
        _json_line(output)
        counts["ALGORITHM"] += 1
    for callable_ref, specs in sorted(quantum_by_callable.items()):
        representative = sorted(specs, key=lambda value: value.quantum_formulation_id)[0]
        fixture_inputs, _, output_schema, _ = _quantum_callable_contract(representative)
        output = representative.build_shape(copy.deepcopy(fixture_inputs))
        if not isinstance(output, Mapping):
            raise BuildError(f"quantum fixture returned non-object: {callable_ref}")
        if set(output) != {str(entry["name"]) for entry in output_schema}:
            raise BuildError(f"quantum fixture/schema key drift: {callable_ref}")
        _json_line(output)
        counts["QUANTUM_CALLABLE_FAMILY"] += 1
    total = sum(counts.values())
    expected = (
        EXPECTED_FORMULA_IMPLEMENTATIONS
        + EXPECTED_ALGORITHM_IMPLEMENTATIONS
        + EXPECTED_QUANTUM_CALLABLE_FAMILIES
    )
    if total != expected:
        raise BuildError(f"ephemeral fixture invocation count drift: {total} != {expected}")
    closed_leaf_fields = {
        formula_id: sorted(_closed_formula_fixture_inputs(spec))
        for spec in formula_specs
        if (formula_id := str(spec.formula_id))
        in {
            "IMPLIED_PROBABILITY",
            "PROBABILITY_EDGE",
            "MID_PRICE",
            "SPREAD",
            "RELATIVE_SPREAD",
        }
    }
    return {
        "source_fixture_invocation_counts": dict(sorted(counts.items())),
        "source_fixture_invocation_total": total,
        "persisted_fixture_vector_count": 0,
        "closed_facade_leaf_fixture_field_names": dict(sorted(closed_leaf_fields.items())),
        "closed_root_dependency_owned_input_count": 3,
    }


def _build_pr162d_batch(
    repo_root: Path, agent_ids: Sequence[str], deadline: _Deadline
) -> dict[str, Any]:
    formula_module, algorithm_module, quantum_module = _import_r2a_modules(repo_root)
    formula_specs = list(formula_module.formula_specs())
    algorithm_specs = list(algorithm_module.algorithm_specs())
    quantum_specs = list(quantum_module.quantum_specs())
    quantum_by_callable: dict[str, list[Any]] = defaultdict(list)
    for spec in quantum_specs:
        quantum_by_callable[spec.callable_ref].append(spec)
    actual = (
        len(formula_specs),
        len(algorithm_specs),
        len(quantum_specs),
        len(quantum_by_callable),
    )
    expected = (
        EXPECTED_FORMULA_IMPLEMENTATIONS,
        EXPECTED_ALGORITHM_IMPLEMENTATIONS,
        EXPECTED_QUANTUM_FORMULATIONS,
        EXPECTED_QUANTUM_CALLABLE_FAMILIES,
    )
    if actual != expected:
        raise BuildError(f"PR162D callable inventory drift: {actual!r} != {expected!r}")
    deadline.check("PR162D callable inventory")
    fixture_metrics = _verify_fixed_source_fixtures(
        formula_specs, algorithm_specs, quantum_by_callable
    )
    source_fixture_rows = _read_pr162d_test_vector_rows(repo_root)
    records = [
        _formula_record(
            spec,
            agent_ids,
            source_fixture_rows.get(
                f"PR162D_R2A_TV_FORMULA::{spec.formula_id}"
            ),
        )
        for spec in formula_specs
    ]
    records.extend(_algorithm_record(spec, agent_ids) for spec in algorithm_specs)
    quantum_records = [
        _quantum_family_record(specs, agent_ids)
        for _, specs in sorted(quantum_by_callable.items())
    ]
    records.extend(quantum_records)
    _apply_source_backed_semantic_relations(records)
    if len({row["canonical_component_id"] for row in records}) != len(records):
        raise BuildError("PR162D canonical component IDs are not unique")
    records.sort(key=lambda row: row["canonical_component_id"])
    batch = _expansion_batch(
        batch_id="EXPANSION.PR162D.EXPLICIT_IMPLEMENTATIONS",
        origin="PR162D_IMPLEMENTATION_BACKED",
        source_refs=[
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/algorithm_seed_library.py",
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/quantum_seed_library.py",
        ],
        source_classification="OWNER_SUBMITTED",
        items=records,
        requested_evidence_modes=("FIXTURE",),
        requested_promotion_ceiling="STACK_READY",
    )
    batch["ephemeral_fixture_metrics"] = fixture_metrics
    return batch


def _build_pr162e_q_original_model_batch(
    pr162d_batch: Mapping[str, Any], agent_ids: Sequence[str]
) -> dict[str, Any]:
    quantum_records = [
        copy.deepcopy(dict(item["record"]))
        for item in pr162d_batch.get("items", ())
        if isinstance(item, Mapping)
        and isinstance(item.get("record"), Mapping)
        and str(item["record"].get("canonical_component_id", "")).startswith(
            "QTT.COMP.QUANTUM."
        )
    ]
    records = [
        _original_economic_model_record(record, agent_ids)
        for record in sorted(
            quantum_records, key=lambda row: str(row["canonical_component_id"])
        )
    ]
    if len(records) != EXPECTED_QUANTUM_CALLABLE_FAMILIES:
        raise BuildError(
            "PR162E-Q original-model target count drift: "
            f"{len(records)} != {EXPECTED_QUANTUM_CALLABLE_FAMILIES}"
        )
    return _expansion_batch(
        batch_id="EXPANSION.PR162E_Q.ORIGINAL_ECONOMIC_MODELS",
        origin="PR162E_Q_QUANTUM_MAPPING",
        source_refs=[
            "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/quantum_seed_library.py",
            "docs/master_plan/generated/PR162E_Q_ObjectiveMap.report.json",
            "docs/master_plan/generated/PR162E_Q_FormulaObjectiveCanonical.report.json",
        ],
        source_classification="OWNER_SUBMITTED",
        items=records,
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="SPECIFIED",
    )


def _owner_requirement_record(
    card_id: str, semantic_key: str, family: str, agent_ids: Sequence[str]
) -> dict[str, Any]:
    component_id = f"QTT.COMP.OWNER_REQUIREMENT.{semantic_key}"
    exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {card_id}"
    definition = _definition(
        display_name=semantic_key,
        description=(
            f"Owner-supplied requirement {card_id}; requested name is preserved, "
            "but mathematics, domains, requirements, and implementation remain unresolved."
        ),
        component_kind="SPECIFICATION_REQUIRED",
        complete_definition=exact_action,
    )
    definition["owner_requirement_crosswalk"] = {
        "owner_requirement_id": card_id,
        "original_requested_name": semantic_key,
        "original_text_ref": f"OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY::{card_id}",
        "component_kind": "SPECIFICATION_REQUIRED",
        "semantic_decomposition": {
            "status": "SPECIFICATION_REQUIRED",
            "known_requested_name": semantic_key,
            "missing_semantics": [
                "MATHEMATICAL_OR_PROCEDURAL_DEFINITION",
                "INPUT_OUTPUT_UNITS_AND_BASES",
                "DOMAIN_BOUNDARY_TIME_AND_STATE_SEMANTICS",
                "TYPED_REQUIREMENTS",
                "INDEPENDENT_ORACLE",
            ],
            "candidate_interpretations": [],
        },
        "canonical_component_target": component_id,
        "qku_role_binding_refs": [],
        "implementation_status": "MISSING_IMPLEMENTATION_UNTIL_SPECIFICATION_CLOSES",
        "binding_readiness_status": "SPECIFICATION_REQUIRED",
        "agent_policy": "RESEARCH_STATUS_EXPLAIN_AND_PROPOSE_BATCH_ITEM_ONLY",
        "decision_roles": _family_decision_roles(family),
        "evidence_route": "INDEPENDENT_ORACLE_THEN_NONLIVE_EVIDENCE_LANES",
        "exact_resolution_action": exact_action,
        "responsible_agent": "research_agent",
        "required_source_or_derivation": "OWNER_OR_DOMAIN_AUTHORITY_COMPLETE_SEMANTIC_SPECIFICATION",
        "exact_acceptance_test": "INDEPENDENT_SEMANTIC_SPECIFICATION_AND_ORACLE_REQUIRED",
        "priority_and_launch_role": "UNRANKED_UNTIL_SEMANTIC_DECOMPOSITION",
    }
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=["OWNER_REQUIREMENT_213"],
        definition=definition,
        decision_roles=_family_decision_roles(family),
        bindings=[
            _binding(
                component_id,
                definition=definition,
                binding_id=f"BINDING.OWNER_REQUIREMENT.REVIEW.{card_id}",
                agent_ids=agent_ids,
                implementation_version=None,
                exact_action=exact_action,
            )
        ],
        provenance=[
            _source_provenance(
                source_ref="OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
                row_ref=card_id,
                local_name=semantic_key,
                fields=("card_id", "formula_family", "semantic_key"),
                target=component_id,
                relation="PROVISIONAL_OWNER_REQUIREMENT_NO_INHERITED_IMPLEMENTATION_CLAIM",
            )
        ],
        market_tags=[f"OWNER_REQUIREMENT_FAMILY_{family}"],
        producer_owner="OWNER_REQUIREMENT_INTAKE_VIA_CONTROL1_BUILDER",
    )


def _build_owner_requirement_batch(
    agent_ids: Sequence[str], deadline: _Deadline
) -> dict[str, Any]:
    records = [
        _owner_requirement_record(card_id, semantic_key, family, agent_ids)
        for card_id, semantic_key, family in _owner_requirements()
    ]
    deadline.check("owner requirement inventory")
    if len({record["canonical_component_id"] for record in records}) != len(records):
        raise BuildError("owner requirement component IDs are not unique")
    records.sort(key=lambda row: row["canonical_component_id"])
    return _expansion_batch(
        batch_id="EXPANSION.OWNER_REQUIREMENT.213",
        origin="OWNER_REQUIREMENT_213",
        source_refs=[
            "OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
            "OWNER_PROVIDED_MASTER_PLAN_CURRENT#owner-requirement-doctrine",
            "OWNER_CONTROLLING_PROMPT_PR169_QKU_COMP_CONTROL1_V5_1#section-12",
        ],
        source_classification="OWNER_SUBMITTED",
        items=records,
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="SPECIFIED",
    )


def _candidate_token(value: Any) -> str:
    token = str(value or "UNNAMED").upper()
    for prefix in (
        "FORM_MAP3_",
        "PR162B-FORMULA-",
        "PR162B-ALGORITHM-",
        "PR168_GFP_FORMULA_",
    ):
        if token.startswith(prefix):
            token = token[len(prefix) :]
            break
    token = re.sub(r"[^A-Z0-9]+", "_", token).strip("_")
    if not token:
        raise BuildError("source computation candidate has no stable semantic token")
    return token


def _candidate_ports(value: Any, *, output: bool = False) -> list[dict[str, Any]]:
    if value in (None, "", [], {}):
        return []
    result: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        iterable: Iterable[Any] = [
            {"name": str(name), "type": spec}
            for name, spec in value.items()
        ]
    elif isinstance(value, (list, tuple)):
        iterable = value
    else:
        iterable = [value]
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            name = (
                item.get("name")
                or item.get("input_id")
                or item.get("output_id")
                or item.get("field")
                or f"{'output' if output else 'input'}_{index + 1}"
            )
            unit = (
                item.get("unit_or_basis")
                or item.get("unit")
                or item.get("basis")
                or "EXACT_RUNTIME_UNIT_REQUIRED"
            )
            declared_type = item.get("type") or item.get("data_type") or (
                "SOURCE_DECLARED_OUTPUT" if output else "SOURCE_DECLARED_INPUT"
            )
        else:
            name = str(item)
            unit = "EXACT_RUNTIME_UNIT_REQUIRED"
            declared_type = "SOURCE_DECLARED_OUTPUT" if output else "SOURCE_DECLARED_INPUT"
        result.append(
            {
                "name": str(name),
                "type": str(declared_type),
                "required": True,
                "unit_or_basis": str(unit),
            }
        )
    return result


def _source_candidate_record(
    row: Mapping[str, Any],
    *,
    source_path: str,
    source_id_field: str,
    source_name: Any,
    component_kind: str,
    complete_definition: Any,
    inputs: Any,
    outputs: Any,
    units: Any,
    implementation_ref: str | None,
    origin: str,
    agent_ids: Sequence[str],
    qku_roles: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    source_id = str(row.get(source_id_field, ""))
    if not source_id:
        raise BuildError(f"source computation row lacks {source_id_field}: {source_path}")
    kind_token = "ALGORITHM" if component_kind != "PURE_FORMULA" else "FORMULA"
    component_id = f"QTT.COMP.CANDIDATE.{kind_token}.{_candidate_token(source_name or source_id)}"
    input_schema = _candidate_ports(inputs)
    output_schema = _candidate_ports(outputs, output=True)
    if isinstance(units, Mapping):
        unit_map = {str(key): copy.deepcopy(value) for key, value in units.items()}
    else:
        unit_map = {
            str(entry["name"]): str(units or entry["unit_or_basis"])
            for entry in (*input_schema, *output_schema)
        }
    implementations: list[dict[str, Any]] = []
    if implementation_ref:
        implementation = _implementation_entry(
            version="source-owner-inventory-v1",
            callable_ref=implementation_ref,
            latency_class="OFFLINE_RESEARCH",
            precision="SOURCE_OWNER_PRECISION_REQUIRES_INDEPENDENT_BOUNDARY_REVIEW",
            memoizable=False,
            proof_basis="NOT_RUNTIME_MEMOIZABLE_UNTIL_INDEPENDENT_REVIEW",
            security_state="SOURCE_INVENTORY_NOT_RUNTIME_ALLOWLISTED",
        )
        implementation["code_owner"] = origin
        implementations.append(implementation)
    definition = _definition(
        display_name=str(source_name or source_id),
        description=(
            f"Source-derived provisional computation from {source_path}; identity and "
            "semantic fields are preserved without asserting equivalence or readiness."
        ),
        component_kind=component_kind,
        complete_definition=str(
            complete_definition or f"MISSING_SEMANTIC_SPECIFICATION: {source_id}"
        ),
        inputs=input_schema,
        outputs=output_schema,
        units=unit_map,
        implementation_versions=implementations,
    )
    definition["source_semantic_occurrence"] = {
        "source_artifact_ref": source_path,
        "source_row_ref": source_id,
        "classification": "GENUINE_PROVISIONAL_NEW_COMPUTATION",
    }
    exact_action = f"MISSING_INDEPENDENT_TYPED_SEMANTIC_CLOSURE: {component_id}@1.0"
    binding = _binding(
        component_id,
        definition=definition,
        binding_id=f"BINDING.CANDIDATE.REVIEW.{_candidate_token(source_name or source_id)}",
        agent_ids=agent_ids,
        implementation_version=None,
        exact_action=exact_action,
    )
    # A provisional source identity must be inspectable through status/explain
    # without implying resolve/compute readiness.  STATIC_VALIDATION is a
    # read-only reference context; the policy remains status/explain-only and
    # every computation readiness dimension remains fail-closed.
    binding["supported_modes"] = ["STATIC_VALIDATION"]
    binding["mode_state"] = {
        "STATIC_VALIDATION": {
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
        }
    }
    consumed_fields = sorted(
        str(key)
        for key, value in row.items()
        if value not in (None, "", [], {})
    )
    return _record(
        component_id=component_id,
        record_state="PROVISIONAL",
        origins=[origin],
        definition=definition,
        decision_roles=["RESEARCH_EVIDENCE_AND_MODEL_VALIDATION", "INTERNAL_SUPPORT"],
        bindings=[binding],
        provenance=[
            _source_provenance(
                source_ref=source_path,
                row_ref=source_id,
                local_name=str(source_name or source_id),
                fields=consumed_fields,
                target=component_id,
                relation="GENUINE_PROVISIONAL_NEW_COMPUTATION",
            )
        ],
        qku_roles=qku_roles,
        market_tags=[origin],
        producer_owner=f"{origin}_SOURCE_OWNER_VIA_CONTROL1_BUILDER",
    )


def _source_candidate_qku_roles(
    values: Any,
    *,
    component_id: str,
    source_path: str,
    source_row_ref: str,
    role: str,
    market_family: str,
    status_explain_root: bool = False,
) -> list[dict[str, Any]]:
    """Preserve source QKU purpose without granting compute authority."""

    if values in (None, "", [], {}):
        return []
    if isinstance(values, str):
        qku_ids = [values]
    elif isinstance(values, Sequence):
        qku_ids = [str(value) for value in values if value]
    else:
        qku_ids = [str(values)]
    return [
        {
            "qku_id": qku_id,
            "role_or_decision_stage": role,
            "market_family": market_family,
            "stack_root_or_direct_component": component_id,
            "selection_rule_if_container": None,
            "agent_policy_tags": ["STATUS_EXPLAIN_RESEARCH_ONLY"],
            "source_refs": [source_path, source_row_ref],
            "runtime_root_eligibility": (
                "STATUS_EXPLAIN_ONLY"
                if status_explain_root
                else "INELIGIBLE_UNTIL_SOURCE_SCOPED_SEMANTICS_ARE_ACCEPTED"
            ),
            "exact_resolution_action": (
                f"MISSING_INDEPENDENT_TYPED_SEMANTIC_CLOSURE: {component_id}@1.0"
            ),
        }
        for qku_id in sorted(set(qku_ids))
    ]


def _source_reference_values(value: Any) -> tuple[str, ...]:
    if value in (None, "", [], {}):
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(sorted({str(item) for item in value if item}))
    return (str(value),)


def _gfp_discovery_has_complete_typed_semantics(row: Mapping[str, Any]) -> bool:
    """A coverage label/name/description is never an equivalence proof."""

    required_fields = (
        "typed_input_schema",
        "typed_output_schema",
        "exact_units_and_bases",
        "domain_and_boundary_behavior",
        "state_and_time_semantics",
        "missing_stale_nonfinite_behavior",
        "precision_and_rounding",
        "typed_requirements",
        "semantic_fallback",
        "direct_equivalence_proof_ref",
    )
    return all(row.get(field) not in (None, "", [], {}) for field in required_fields)


def _source_vector_values_equal(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(actual, Mapping) and isinstance(expected, Mapping):
        return set(actual) == set(expected) and all(
            _source_vector_values_equal(actual[key], expected[key], tolerance)
            for key in actual
        )
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _source_vector_values_equal(left, right, tolerance)
            for left, right in zip(actual, expected)
        )
    if (
        isinstance(actual, (int, float, Decimal))
        and not isinstance(actual, bool)
        and isinstance(expected, (int, float, Decimal))
        and not isinstance(expected, bool)
    ):
        return abs(float(actual) - float(expected)) <= tolerance
    return actual == expected


def _verify_pr162b_source_vectors(
    rows: Sequence[Mapping[str, Any]], deadline: _Deadline
) -> dict[str, Any]:
    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in PR162B_IMPLEMENTATION_MODULE_ALLOWLIST
    }
    counts: Counter[str] = Counter()
    callable_refs: set[str] = set()
    for index, row in enumerate(rows):
        if index % 25 == 0:
            deadline.check("PR162B source vector invocation")
        module_name = str(row.get("implementation_module", ""))
        function_name = str(row.get("implementation_function", ""))
        if module_name not in modules or not re.fullmatch(
            r"[a-z][a-z0-9_]*", function_name
        ):
            raise BuildError(
                "PR162B source vector escaped the fixed implementation allowlist: "
                f"{module_name}:{function_name}"
            )
        implementation = getattr(modules[module_name], function_name, None)
        if not callable(implementation):
            raise BuildError(
                f"PR162B source implementation is not callable: {module_name}:{function_name}"
            )
        inputs = row.get("inputs")
        if not isinstance(inputs, Mapping):
            raise BuildError(
                f"PR162B source vector has no typed input mapping: {row.get('test_vector_id')}"
            )
        actual = implementation(**copy.deepcopy(dict(inputs)))
        tolerance = float(row.get("tolerance", 0.0))
        if tolerance < 0 or not _source_vector_values_equal(
            actual, row.get("expected_output"), tolerance
        ):
            raise BuildError(
                f"PR162B source vector mismatch: {row.get('test_vector_id')}"
            )
        kind = (
            "FORMULA"
            if str(row.get("formula_id_or_algorithm_id", "")).startswith(
                "PR162B-FORMULA-"
            )
            else "ALGORITHM"
        )
        counts[kind] += 1
        callable_refs.add(f"{module_name}:{function_name}")
    if dict(counts) != {"FORMULA": 61, "ALGORITHM": 14}:
        raise BuildError(f"PR162B source vector denominator drift: {dict(counts)}")
    return {
        "fixed_module_allowlist_count": len(modules),
        "registered_callable_ref_count": len(callable_refs),
        "source_vector_count": len(rows),
        "source_vector_invocation_counts": dict(sorted(counts.items())),
        "source_vector_exact_match_count": len(rows),
        "source_vector_failure_count": 0,
        "independent_oracle_claim": False,
        "readiness_promotion_from_source_vector": False,
    }


def _normalized_gfp_callable_ref(path: Any, function: Any) -> str:
    path_text = str(path or "").replace("\\", "/")
    function_text = str(function or "")
    prefix = "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/"
    if (
        not path_text.startswith(prefix)
        or not path_text.endswith(".py")
        or not re.fullmatch(r"[a-z][a-z0-9_]*", function_text)
    ):
        raise BuildError(
            f"GFP implementation reference is not a fixed package callable: "
            f"{path_text}:{function_text}"
        )
    module_name = "src.qtt." + path_text[len("src/qtt/") : -3].replace("/", ".")
    if module_name not in GFP_IMPLEMENTATION_MODULE_ALLOWLIST:
        raise BuildError(f"GFP implementation module escaped allowlist: {module_name}")
    implementation = getattr(importlib.import_module(module_name), function_text, None)
    if not callable(implementation):
        raise BuildError(
            f"GFP implementation is not importable: {module_name}:{function_text}"
        )
    return f"{module_name}:{function_text}"


def _source_selection_tuple(
    row: Mapping[str, Any],
    *,
    formula_field: str,
    algorithm_field: str,
    parameter_field: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return an owner-context co-association; never materialize it as truth."""

    value = (
        _source_reference_values(row.get(formula_field)),
        _source_reference_values(row.get(algorithm_field)),
        _source_reference_values(row.get(parameter_field)),
    )
    if any(len(part) != 1 for part in value):
        raise BuildError(f"source owner context tuple is not exact: {value!r}")
    return value


def _build_source_semantic_candidate_batch(
    repo_root: Path, agent_ids: Sequence[str], deadline: _Deadline
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []

    map3_path = "docs/master_plan/generated/map3/formula_materialization_rows.jsonl"
    map3_rows, _ = _read_source_artifact_rows(repo_root, map3_path, deadline)
    map3_ontology_path = "docs/master_plan/generated/map3/formula_ontology_rows.jsonl"
    map3_ontology_rows, _ = _read_source_artifact_rows(
        repo_root, map3_ontology_path, deadline
    )
    map3_ontology_by_formula = {
        str(row.get("formula_id", "")): row for row in map3_ontology_rows
    }
    if set(map3_ontology_by_formula) != {
        str(row.get("formula_id", "")) for row in map3_rows
    }:
        raise BuildError("MAP3 materialization/ontology formula closure drift")
    for row in map3_rows:
        formula_id = str(row.get("formula_id", ""))
        component_id = f"QTT.COMP.CANDIDATE.FORMULA.{_candidate_token(formula_id)}"
        ontology = map3_ontology_by_formula[formula_id]
        records.append(
            _source_candidate_record(
                row,
                source_path=map3_path,
                source_id_field="formula_id",
                source_name=row.get("formula_id"),
                component_kind="PURE_FORMULA",
                complete_definition=row.get("safe_formula_expression_or_semantic_definition"),
                inputs=row.get("required_inputs_with_units"),
                outputs=[{"name": "result", "type": row.get("formula_output_type")}],
                units=None,
                implementation_ref=str(row.get("materialization_path") or "") or None,
                origin="MAP3_RECOVERED",
                agent_ids=agent_ids,
                qku_roles=_source_candidate_qku_roles(
                    ontology.get("qku_id_if_available"),
                    component_id=component_id,
                    source_path=map3_ontology_path,
                    source_row_ref=formula_id,
                    role=str(
                        ontology.get("prediction_market_role")
                        or ontology.get("ontology_subcategory")
                        or "MAP3_RESEARCH_CANDIDATE"
                    ),
                    market_family=str(
                        ontology.get("formula_family") or "PREDICTION_MARKET"
                    ),
                    status_explain_root=True,
                ),
            )
        )

    pr162b_vector_rows: list[dict[str, Any]] = []
    pr162b_vector_by_target: dict[str, dict[str, Any]] = {}
    for vector_path in PR162B_TEST_VECTOR_PATHS:
        vector_rows, _ = _read_source_artifact_rows(
            repo_root, vector_path, deadline
        )
        for vector_row in vector_rows:
            target_ref = str(vector_row.get("formula_id_or_algorithm_id", ""))
            if not target_ref or target_ref in pr162b_vector_by_target:
                raise BuildError(
                    f"PR162B source vector target is empty or duplicated: {target_ref!r}"
                )
            copied = copy.deepcopy(vector_row)
            copied["source_artifact_ref"] = vector_path
            pr162b_vector_by_target[target_ref] = copied
            pr162b_vector_rows.append(copied)
    pr162b_source_vector_metrics = _verify_pr162b_source_vectors(
        pr162b_vector_rows, deadline
    )

    pr162b_specs = (
        (
            "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json",
            "formula_id",
            "formula_name",
            "PURE_FORMULA",
            "mathematical_expression_latex",
            "input_fields",
            "output_fields",
        ),
        (
            "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json",
            "algorithm_id",
            "algorithm_name",
            "NUMERICAL_ALGORITHM",
            "pseudocode",
            "input_fields",
            "output_fields",
        ),
    )
    for path, id_field, name_field, kind, definition_field, inputs_field, outputs_field in pr162b_specs:
        rows, _ = _read_source_artifact_rows(repo_root, path, deadline)
        for row in rows:
            module = str(row.get("implementation_module") or "")
            function = str(row.get("implementation_function") or "")
            implementation_ref = f"{module}:{function}" if module and function else None
            source_name = row.get(name_field) or row.get(id_field)
            kind_token = "FORMULA" if kind == "PURE_FORMULA" else "ALGORITHM"
            component_id = (
                f"QTT.COMP.CANDIDATE.{kind_token}.{_candidate_token(source_name)}"
            )
            pr162b_record = _source_candidate_record(
                    row,
                    source_path=path,
                    source_id_field=id_field,
                    source_name=source_name,
                    component_kind=kind,
                    complete_definition=(
                        row.get(definition_field)
                        or row.get("plain_english_definition")
                        or row.get("purpose")
                    ),
                    inputs=row.get(inputs_field),
                    outputs=row.get(outputs_field),
                    units=row.get("units"),
                    implementation_ref=implementation_ref,
                    origin="PR162B_SOURCE_SEMANTICS",
                    agent_ids=agent_ids,
                    qku_roles=_source_candidate_qku_roles(
                        row.get("qku_refs"),
                        component_id=component_id,
                        source_path=path,
                        source_row_ref=str(row.get(id_field, "")),
                        role=f"PR162B_SOURCE_{kind_token}_CANDIDATE",
                        market_family=str(
                            row.get("formula_family")
                            or row.get("algorithm_family")
                            or "SOURCE_DECLARED_CANDIDATE"
                        ),
                        status_explain_root=True,
                    ),
                )
            vector = pr162b_vector_by_target.get(str(row.get(id_field, "")))
            if vector is None:
                raise BuildError(
                    f"PR162B source semantic row lacks its exact vector: {row.get(id_field)}"
                )
            vector_id = str(vector["test_vector_id"])
            if row.get("test_vector_refs") != [vector_id]:
                raise BuildError(
                    f"PR162B source vector reference drift: {row.get(id_field)}"
                )
            if (
                str(vector.get("implementation_module", "")) != module
                or str(vector.get("implementation_function", "")) != function
            ):
                raise BuildError(
                    f"PR162B source vector implementation mismatch: {row.get(id_field)}"
                )
            pr162b_record["definition"]["oracle_and_test_refs"] = [
                {
                    "source_test_vector_ref": vector_id,
                    "source_artifact_ref": vector["source_artifact_ref"],
                    "validation_class": (
                        "SOURCE_OWNER_VECTOR_EXECUTED_NOT_INDEPENDENT_ORACLE"
                    ),
                }
            ]
            pr162b_record["provenance"].append(
                _source_provenance(
                    source_ref=str(vector["source_artifact_ref"]),
                    row_ref=vector_id,
                    local_name=vector_id,
                    fields=(
                        "formula_id_or_algorithm_id",
                        "implementation_module",
                        "implementation_function",
                        "inputs",
                        "expected_output",
                        "tolerance",
                    ),
                    target=component_id,
                    relation="SOURCE_TEST_VECTOR_IMPLEMENTATION_MAPPING",
                )
            )
            records.append(pr162b_record)

    gfp_path = "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json"
    gfp_rows, _ = _read_source_artifact_rows(repo_root, gfp_path, deadline)
    gfp_record_by_expression: dict[str, dict[str, Any]] = {}
    gfp_callable_refs: set[str] = set()
    for row in gfp_rows:
        implementation_ref = _normalized_gfp_callable_ref(
            row.get("computation_function_path"),
            row.get("computation_function_name"),
        )
        gfp_callable_refs.add(implementation_ref)
        gfp_record = _source_candidate_record(
                row,
                source_path=gfp_path,
                source_id_field="formula_id",
                source_name=row.get("formula_id"),
                component_kind="PURE_FORMULA",
                complete_definition=row.get("formula_expression"),
                inputs=row.get("input_schema"),
                outputs=row.get("output_schema"),
                units=row.get("unit_contract"),
                implementation_ref=implementation_ref,
                origin="GFP_SOURCE_SEMANTICS",
                agent_ids=agent_ids,
            )
        records.append(gfp_record)
        expression = str(row.get("formula_expression", "")).strip()
        if not expression or expression in gfp_record_by_expression:
            raise BuildError(f"GFP selected expression is empty or ambiguous: {expression!r}")
        gfp_record_by_expression[expression] = gfp_record
    if len(gfp_callable_refs) != 33:
        raise BuildError(
            f"GFP importable callable denominator drift: {len(gfp_callable_refs)} != 33"
        )

    gfp_arbitration_path = (
        "docs/master_plan/generated/PR168_GFP_FormulaSourceArbitration.report.json"
    )
    gfp_arbitration_rows, _ = _read_source_artifact_rows(
        repo_root, gfp_arbitration_path, deadline
    )
    for row in gfp_arbitration_rows:
        if not bool(row.get("selected_flag")):
            continue
        expression = str(row.get("formula_expression", "")).strip()
        target_record = gfp_record_by_expression.get(expression)
        if target_record is None:
            raise BuildError(
                f"selected GFP arbitration expression has no semantic target: {expression!r}"
            )
        candidate_id = str(row.get("formula_candidate_id", ""))
        target_id = str(target_record["canonical_component_id"])
        target_record["provenance"].append(
            _source_provenance(
                source_ref=gfp_arbitration_path,
                row_ref=candidate_id,
                local_name=candidate_id,
                fields=(
                    "formula_candidate_id",
                    "formula_expression",
                    "selected_flag",
                    "selection_reason",
                ),
                target=target_id,
                relation="EXACT_EXPRESSION_SELECTED_SOURCE_MAPPING",
            )
        )

    semantic_candidate_specs = (
        (
            "docs/master_plan/generated/PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json",
            "candidate_id",
            "formula_id",
            "PURE_FORMULA",
            "expression",
            "input_fields",
            "output_fields",
            "units",
            "MASTER_PLAN_CANDIDATE_SEMANTICS",
        ),
        (
            "docs/master_plan/generated/PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json",
            "candidate_id",
            "algorithm_id",
            "NUMERICAL_ALGORITHM",
            "deterministic_steps",
            "inputs",
            "outputs",
            None,
            "MASTER_PLAN_CANDIDATE_SEMANTICS",
        ),
        (
            "docs/master_plan/generated/PR165_ExternalFormulaAndParameterCandidateRegistry.report.json",
            "external_formula_parameter_ref",
            "formula_or_parameter_name",
            "PURE_FORMULA",
            "candidate_formula_expression",
            None,
            ["candidate_value"],
            "unit_policy",
            "POST_RP5C_EXTERNAL_CANDIDATE_SEMANTICS",
        ),
    )
    for (
        path,
        id_field,
        name_field,
        kind,
        definition_field,
        inputs_field,
        outputs_field,
        units_field,
        origin,
    ) in semantic_candidate_specs:
        rows, _ = _read_source_artifact_rows(repo_root, path, deadline)
        for row in rows:
            source_name = row.get(name_field) or row.get(id_field)
            component_id = (
                f"QTT.COMP.CANDIDATE."
                f"{'FORMULA' if kind == 'PURE_FORMULA' else 'ALGORITHM'}."
                f"{_candidate_token(source_name)}"
            )
            inputs = row.get(inputs_field) if inputs_field else None
            outputs = row.get(outputs_field) if isinstance(outputs_field, str) else outputs_field
            units = row.get(units_field) if units_field else None
            records.append(
                _source_candidate_record(
                    row,
                    source_path=path,
                    source_id_field=id_field,
                    source_name=source_name,
                    component_kind=kind,
                    complete_definition=row.get(definition_field),
                    inputs=inputs,
                    outputs=outputs,
                    units=units,
                    implementation_ref=None,
                    origin=origin,
                    agent_ids=agent_ids,
                    qku_roles=_source_candidate_qku_roles(
                        row.get("qku_refs"),
                        component_id=component_id,
                        source_path=path,
                        source_row_ref=str(row.get(id_field, "")),
                        role=(
                            "SOURCE_CANDIDATE_FORMULA_RESEARCH_REVIEW"
                            if kind == "PURE_FORMULA"
                            else "SOURCE_CANDIDATE_ALGORITHM_RESEARCH_REVIEW"
                        ),
                        market_family="SOURCE_DECLARED_CANDIDATE",
                    ),
                )
            )

    # PR162E, PR162E-Q, and PR166-SM3 remain contextual/evidence owners.  Their
    # formula and algorithm references are preserved once as provisional
    # computation identities.  QKU purpose belongs on one compact exact
    # formula/algorithm/parameter selection tuple, never on both underlying
    # components (which previously created silent dual roots).
    reference_specs = (
        (
            "docs/master_plan/generated/PR162E_PluginRegistry.report.json",
            "plugin_id",
            "formula_refs",
            "algorithm_refs",
            "parameter_stack_refs",
            "qku_refs",
            "PR162E_CONTEXT_REFERENCE",
        ),
        (
            "docs/master_plan/generated/PR162E_Q_ObjectiveMap.report.json",
            "mapping_row_ref",
            "formula_id",
            "algorithm_id",
            "parameter_stack_id",
            "qku_id",
            "PR162E_Q_CONTEXT_REFERENCE",
        ),
        (
            "docs/master_plan/generated/PR166_SM3_PosEvidence.report.json",
            "row_id",
            "formula_id",
            "algorithm_id",
            "parameter_stack_id",
            "qku_id",
            "PR166_SM3_EVIDENCE_REFERENCE",
        ),
    )
    reference_occurrences: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    selection_occurrences: dict[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
        list[dict[str, Any]],
    ] = defaultdict(list)

    for (
        path,
        row_id_field,
        formula_field,
        algorithm_field,
        parameter_field,
        qku_field,
        origin,
    ) in reference_specs:
        rows, _ = _read_source_artifact_rows(repo_root, path, deadline)
        for row in rows:
            row_ref = str(row.get(row_id_field, ""))
            qku_ids = _source_reference_values(row.get(qku_field))
            selection = _source_selection_tuple(
                row,
                formula_field=formula_field,
                algorithm_field=algorithm_field,
                parameter_field=parameter_field,
            )
            selection_occurrences[selection].append(
                {
                    "path": path,
                    "row_ref": row_ref,
                    "origin": origin,
                    "qku_ids": qku_ids,
                }
            )
            for kind, field in (("FORMULA", formula_field), ("ALGORITHM", algorithm_field)):
                for semantic_ref in _source_reference_values(row.get(field)):
                    reference_occurrences[(kind, semantic_ref)].append(
                        {
                            "path": path,
                            "row_ref": row_ref,
                            "origin": origin,
                        }
                    )
    for (kind, semantic_ref), occurrences in sorted(reference_occurrences.items()):
        first = occurrences[0]
        component_kind = "PURE_FORMULA" if kind == "FORMULA" else "NUMERICAL_ALGORITHM"
        component_id = f"QTT.COMP.CANDIDATE.{kind}.{_candidate_token(semantic_ref)}"
        source_row = {
            "source_reference": semantic_ref,
            "source_row_ref": first["row_ref"],
        }
        source_occurrence_counts: Counter[str] = Counter()
        for occurrence in occurrences:
            source_occurrence_counts[str(occurrence["path"])] += 1
        provenance: list[dict[str, Any]] = []
        for source_path, occurrence_count in sorted(source_occurrence_counts.items()):
            summary = _source_provenance(
                source_ref=source_path,
                row_ref=f"ROWS_WITH_REFERENCE::{semantic_ref}",
                local_name=semantic_ref,
                fields=("formula_or_algorithm_reference", "qku_reference"),
                target=component_id,
                relation="CONTEXT_OR_EVIDENCE_COMPUTATION_REFERENCE",
            )
            summary["source_occurrence_count"] = occurrence_count
            summary["lineage_validation_status"] = "ALL_REFERENCING_ROWS_CLASSIFIED"
            summary["exact_source_row_rederivation"] = {
                "owner_artifact": source_path,
                "match_field": (
                    "formula_refs_or_formula_id"
                    if kind == "FORMULA"
                    else "algorithm_refs_or_algorithm_id"
                ),
                "match_value": semantic_ref,
                "validation": "INDEPENDENT_ROW_LEVEL_REDERIVATION_REQUIRED",
            }
            provenance.append(summary)
        record = _source_candidate_record(
            source_row,
            source_path=first["path"],
            source_id_field="source_row_ref",
            source_name=semantic_ref,
            component_kind=component_kind,
            complete_definition=f"MISSING_REFERENCED_COMPUTATION_SEMANTICS: {semantic_ref}",
            inputs=None,
            outputs=["result"],
            units=None,
            implementation_ref=None,
            origin=first["origin"],
            agent_ids=agent_ids,
            qku_roles=(),
        )
        record["provenance"] = _sorted_unique_values(provenance)
        record["origin_cohorts"] = sorted(
            {str(occurrence["origin"]) for occurrence in occurrences}
        )
        records.append(record)

    qku_selection_targets: dict[str, str] = {}
    qku_source_cohorts: dict[str, set[str]] = defaultdict(set)
    for selection, occurrences in sorted(selection_occurrences.items()):
        # A formula/algorithm/parameter co-occurrence is source-owner context,
        # not a deterministic selection procedure.  Preserve its exact tuple
        # for closure/conflict accounting without minting a ComputationRecord,
        # QKU root, or runtime policy component.
        target = "SOURCE_OWNER_SELECTION_TUPLE::" + "::".join(
            part[0] for part in selection
        )
        for occurrence in occurrences:
            for qku_id in occurrence.get("qku_ids", ()):
                prior = qku_selection_targets.setdefault(str(qku_id), target)
                if prior != target:
                    raise BuildError(
                        "source QKU maps to multiple exact selection tuples: "
                        f"{qku_id}: {prior}, {target}"
                    )
                qku_source_cohorts[str(qku_id)].add(str(occurrence["origin"]))
    if len(selection_occurrences) != EXPECTED_SOURCE_SELECTION_TUPLES:
        raise BuildError(
            "source selection tuple denominator drift: "
            f"{len(selection_occurrences)} != {EXPECTED_SOURCE_SELECTION_TUPLES}"
        )
    if len(qku_selection_targets) != EXPECTED_SOURCE_SELECTION_QKUS:
        raise BuildError(
            "source selection QKU denominator drift: "
            f"{len(qku_selection_targets)} != {EXPECTED_SOURCE_SELECTION_QKUS}"
        )
    cross_cohort_qkus = sum(
        "PR166_SM3_EVIDENCE_REFERENCE" in origins and len(origins) > 1
        for origins in qku_source_cohorts.values()
    )
    if cross_cohort_qkus != EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS:
        raise BuildError(
            "source selection cross-cohort QKU denominator drift: "
            f"{cross_cohort_qkus} != "
            f"{EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS}"
        )

    component_ids = [str(record["canonical_component_id"]) for record in records]
    if len(component_ids) != len(set(component_ids)):
        duplicates = sorted(
            component_id
            for component_id, count in Counter(component_ids).items()
            if count > 1
        )
        raise BuildError(f"ambiguous source candidate component IDs: {duplicates}")
    batch = _expansion_batch(
        batch_id="EXPANSION.SOURCE.SEMANTIC.CLOSURE",
        origin="SOURCE_SEMANTIC_CLOSURE",
        source_refs=[
            map3_path,
            map3_ontology_path,
            *(spec[0] for spec in pr162b_specs),
            *PR162B_TEST_VECTOR_PATHS,
            gfp_path,
            gfp_arbitration_path,
            *(spec[0] for spec in semantic_candidate_specs),
            *(spec[0] for spec in reference_specs),
        ],
        source_classification="OWNER_SUBMITTED",
        items=sorted(records, key=lambda record: str(record["canonical_component_id"])),
        requested_evidence_modes=("NONE",),
        requested_promotion_ceiling="SPECIFIED",
    )
    batch["pr162b_source_vector_metrics"] = pr162b_source_vector_metrics
    return batch


def _build_registry_and_batches(
    repo_root: Path,
    deadline: _Deadline,
    base_records: Sequence[Mapping[str, Any]] = (),
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    tuple[str, ...],
    list[dict[str, Any]],
]:
    repo_root = repo_root.resolve()
    agent_ids = _load_agent_ids(repo_root)
    rp5c_batch = _build_rp5c_batch(repo_root, agent_ids, deadline, base_records)
    pr162d_batch = _build_pr162d_batch(repo_root, agent_ids, deadline)
    pr162e_q_original_batch = _build_pr162e_q_original_model_batch(
        pr162d_batch, agent_ids
    )
    source_semantic_batch = _build_source_semantic_candidate_batch(
        repo_root, agent_ids, deadline
    )
    batches = [
        rp5c_batch,
        pr162d_batch,
        pr162e_q_original_batch,
        source_semantic_batch,
        _build_owner_requirement_batch(agent_ids, deadline),
    ]
    migration_base_records = [
        record
        for record in base_records
        if not isinstance(record.get("definition"), Mapping)
        or not isinstance(
            record.get("definition", {}).get("source_scoped_selection_tuple"),
            Mapping,
        )
    ]
    records, compiler_reports = _compile_batches(
        migration_base_records, batches, deadline
    )
    records = _attach_qku_verification_receipts(records)
    _validate_registry(records, deadline)
    return records, batches, agent_ids, compiler_reports


def build_registry(repo_root: str | Path) -> list[dict[str, Any]]:
    """Build and return the deterministic logical registry without publishing it."""
    records, _, _, _ = _build_registry_and_batches(
        Path(repo_root), _Deadline(3_600_000)
    )
    return records


def _control_module() -> Any:
    """Load the single fixed CONTROL1 implementation owner, never a caller path."""

    for module_name in ("qtt.computation_control.control", "src.qtt.computation_control.control"):
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
    raise BuildError("the fixed qtt.computation_control.control owner is not importable")


def _control_storage_policy() -> dict[str, Any]:
    policy = getattr(_control_module(), "STORAGE_POLICY", None)
    if not isinstance(policy, Mapping):
        raise BuildError("control owner does not expose its centralized STORAGE_POLICY")
    return dict(policy)


def _validate_record_with_control(record: Mapping[str, Any]) -> None:
    helper = getattr(_control_module(), "_validate_record_shape", None)
    if not callable(helper):
        raise BuildError("control owner lacks required private record-shape validator")
    result = helper(record)
    if result is False:
        raise BuildError(
            f"control shape validation rejected {record.get('canonical_component_id')}"
        )


def _batch_item_record(item: Mapping[str, Any]) -> Mapping[str, Any]:
    record = item.get("record")
    if isinstance(record, Mapping):
        return record
    if "canonical_component_id" in item and "definition" in item:
        return item
    raise BuildError("typed expansion item has no materialized record")


def _compile_batches(
    base_records: Sequence[Mapping[str, Any]],
    batches: Sequence[Mapping[str, Any]],
    deadline: _Deadline,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run every current cohort through the one private expansion compiler."""

    compiler = getattr(_control_module(), "_compile_expansion_batch", None)
    if not callable(compiler):
        raise BuildError("control owner lacks its private expansion compiler")
    records = [copy.deepcopy(dict(record)) for record in base_records]
    reports: list[dict[str, Any]] = []
    for batch in batches:
        deadline.check(f"compile {batch.get('batch_id', '<unknown>')}")
        before_ids = {str(record["canonical_component_id"]) for record in records}
        try:
            candidate_records, delta, raw_report = compiler(records, batch)
        except Exception as exc:
            raise BuildError(
                f"expansion compiler rejected {batch.get('batch_id')}: {exc}"
            ) from exc
        if not isinstance(candidate_records, (list, tuple)):
            raise BuildError("expansion compiler did not return candidate records")
        if not isinstance(raw_report, Mapping):
            raise BuildError("expansion compiler did not return its outcome report")
        delta_value = delta.as_dict() if hasattr(delta, "as_dict") else vars(delta)
        if not isinstance(delta_value, Mapping) or delta_value.get(
            "registry_schema_version"
        ) != REGISTRY_SCHEMA_VERSION:
            raise BuildError("expansion compiler returned an incompatible transient delta")
        records = [copy.deepcopy(dict(record)) for record in candidate_records]
        after_ids = {str(record["canonical_component_id"]) for record in records}

        cases_by_component: dict[str, list[str]] = defaultdict(list)
        ordered_items = sorted(
            (
                item
                for item in batch.get("items", [])
                if isinstance(item, Mapping)
            ),
            key=lambda item: (
                str(_batch_item_record(item).get("canonical_component_id", "")),
                str(_batch_item_record(item).get("semantic_version", "")),
                _json_line(item),
            ),
        )
        for item in ordered_items:
            component_id = str(
                _batch_item_record(item).get("canonical_component_id", "")
            )
            cases_by_component[component_id].append(
                str(item.get("case", f"SOURCE_INTAKE::{component_id}"))
            )

        report = copy.deepcopy(dict(raw_report))
        annotated_outcomes: list[dict[str, Any]] = []
        for raw_outcome in report.get("outcomes", []):
            if not isinstance(raw_outcome, Mapping):
                raise BuildError("expansion compiler emitted a non-object outcome")
            outcome = copy.deepcopy(dict(raw_outcome))
            component_id = str(outcome.get("candidate", ""))
            cases = cases_by_component.get(component_id, [])
            if not cases:
                raise BuildError(
                    f"compiler outcome has no source batch item: {component_id}"
                )
            outcome["case"] = cases.pop(0)
            outcome["new_record_count"] = int(
                component_id not in before_ids
                and component_id in after_ids
                and str(outcome.get("canonical_target")) == component_id
            )
            annotated_outcomes.append(outcome)
        if any(cases for cases in cases_by_component.values()):
            raise BuildError("compiler omitted one or more typed batch item outcomes")
        report["outcomes"] = annotated_outcomes
        report["transient_delta"] = {
            key: copy.deepcopy(value)
            for key, value in delta_value.items()
            if key
            in {
                "batch_id",
                "registry_schema_version",
                "added_component_ids",
                "changed_component_ids",
                "retired_component_ids",
                "added_binding_ids",
                "changed_binding_ids",
                "removed_binding_ids",
                "affected_dependent_ids",
                "affected_consumer_classes",
            }
        }
        report["pre_compiler_rejections"] = copy.deepcopy(
            list(batch.get("pre_compiler_rejections", []))
        )
        reports.append(report)
    return sorted(records, key=lambda row: (row["canonical_component_id"], row["semantic_version"])), reports


def _semantic_core(record: Mapping[str, Any]) -> dict[str, Any]:
    definition = record.get("definition", {})
    return {field: copy.deepcopy(definition.get(field)) for field in _SEMANTIC_CORE_FIELDS}


def _qku_role_ref(role: Mapping[str, Any]) -> str:
    return "::".join(
        (
            str(role.get("qku_id", "")),
            str(role.get("role_or_decision_stage", "")),
            str(role.get("market_family", "")),
            _stable_json_value(role.get("context_selector")),
        )
    )


def _reviewed_closed_decimal_semantics() -> dict[str, dict[str, Any]]:
    """Return reviewed semantic bindings for the only positively proven family.

    These are explicit structured assertions, not identities or digests.  A
    familiar component ID is never sufficient to receive a positive receipt.
    """

    common = {
        "component_kind": "PURE_FORMULA",
        "objective_sense_or_null": None,
        "assumptions": [
            "PURE_STATELESS_SCALAR_ARITHMETIC_ON_ONE_IMMUTABLE_REQUEST_INPUT_LOCK"
        ],
        "hard_constraints": [],
        "soft_preferences": [],
        "state_and_time_semantics": {
            "state": "STATELESS",
            "time": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
        },
        "output_accounting_class": (
            "NON_ACCOUNTING_UNLESS_OUTPUT_SCHEMA_EXPLICITLY_IDENTIFIES_ACCOUNTING"
        ),
        "missing_stale_nonfinite_behavior": {
            "missing": "FAIL_CLOSED",
            "nonfinite": "FAIL_CLOSED",
            "stale": "FAIL_CLOSED",
        },
        "precision_and_rounding": {
            "numeric_boundary": "PYTHON_DECIMAL",
            "rounding": "NO_ROUNDING_BEFORE_DECLARED_OUTPUT",
        },
        "parameter_schema_and_default_provenance": {
            "default_provenance": "NO_CONFIGURABLE_PARAMETERS_IN_FORMULA_SEMANTICS",
            "parameters": [],
        },
        "failure_domain_tags": [
            "MISSING_INPUT",
            "STALE_INPUT",
            "NONFINITE_INPUT",
            "DOMAIN_ERROR",
        ],
        "classical_fallback": {
            "not_applicable": True,
            "proof_ref": "PURE_FORMULA_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
        },
        "quantum": {
            "applicability_state": "NOT_APPLICABLE_OR_NOT_YET_PROVEN",
            "coefficient_scaling": None,
            "constraint_map": None,
            "decomposition_or_embedding": None,
            "fallback": "DETERMINISTIC_CLASSICAL_FALLBACK_REQUIRED_IF_PROMOTED",
            "formulation_candidates": [],
            "inverse_map": None,
            "local_exact_or_small_instance_parity": None,
            "maturity_ceiling": "SPECIFIED",
            "objective_map": None,
            "optimizer_and_version": None,
            "original_economic_problem_ref": None,
            "original_model_feasibility_check": None,
            "penalty_policy": None,
            "precision_and_quantization": None,
            "problem_family": None,
            "same_formulation_classical_comparator": None,
            "seed_resampling_policy": None,
            "selected_formulation_or_none": None,
            "shots_reads_or_sampling_policy": None,
            "variable_encoding": None,
            "warm_start": None,
        },
    }

    def port(name: str, unit: str, *, required: bool = True) -> dict[str, Any]:
        return {
            "name": name,
            "required": required,
            "type": "FINITE_DECIMAL_COMPATIBLE_SCALAR",
            "unit_or_basis": unit,
        }

    def output(name: str, unit: str) -> dict[str, Any]:
        return {
            "name": name,
            "type": "FINITE_DECIMAL_COMPATIBLE_SCALAR",
            "unit_or_basis": unit,
        }

    def requirement(
        target: str,
        role: str,
        producer: str,
        consumer: str,
        unit: str,
    ) -> dict[str, Any]:
        return {
            "activation_condition": "ALWAYS",
            "consumer_input_name": consumer,
            "failure_behavior": "FAIL_CLOSED",
            "fallback_component_id_or_null": None,
            "producer_output_name": producer,
            "required_component_id_or_source_selector": target,
            "required_or_optional": "REQUIRED",
            "required_semantic_version_constraint": "==1.0",
            "requirement_role": role,
            "timing_and_freshness_constraint": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK",
            "unit_or_basis_conversion": "IDENTITY",
        }

    per_component: dict[str, dict[str, Any]] = {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY": {
            "complete_mathematical_or_procedural_definition": (
                "implied_probability = clamp(price / max(payout, epsilon), 0, 1)"
            ),
            "domain_and_boundary_behavior": (
                "price and payout are finite Decimal-compatible values; payout >= 1e-9; "
                "0 <= price <= payout; output is price/payout in [0,1]"
            ),
            "input_schema": [port("price", "price"), port("payout", "price")],
            "output_schema": [output("implied_probability", "probability")],
            "units_and_bases": {
                "implied_probability": "probability",
                "payout": "price",
                "price": "price",
            },
            "requirements": [],
        },
        "QTT.COMP.FORMULA.PROBABILITY_EDGE": {
            "complete_mathematical_or_procedural_definition": (
                "probability_edge = p_model - implied_probability"
            ),
            "domain_and_boundary_behavior": (
                "p_model and dependency-produced implied_probability are finite probabilities "
                "in [0,1]; output is their signed difference"
            ),
            "input_schema": [
                port("p_model", "probability"),
                port("implied_probability", "probability"),
            ],
            "output_schema": [output("probability_edge", "probability_delta")],
            "units_and_bases": {
                "implied_probability": "probability",
                "p_model": "probability",
                "probability_edge": "probability_delta",
            },
            "requirements": [
                requirement(
                    "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                    "IMPLIED_PROBABILITY_INPUT",
                    "implied_probability",
                    "implied_probability",
                    "probability",
                )
            ],
        },
        "QTT.COMP.FORMULA.MID_PRICE": {
            "complete_mathematical_or_procedural_definition": (
                "mid_price = (best_bid + best_ask) / 2"
            ),
            "domain_and_boundary_behavior": (
                "finite prices satisfying 0 <= best_bid <= best_ask"
            ),
            "input_schema": [
                port("best_bid", "price"),
                port("best_ask", "price"),
            ],
            "output_schema": [output("mid_price", "price")],
            "units_and_bases": {
                "best_ask": "price",
                "best_bid": "price",
                "mid_price": "price",
            },
            "requirements": [],
        },
        "QTT.COMP.FORMULA.SPREAD": {
            "complete_mathematical_or_procedural_definition": (
                "spread = best_ask - best_bid"
            ),
            "domain_and_boundary_behavior": (
                "finite prices satisfying 0 <= best_bid <= best_ask"
            ),
            "input_schema": [
                port("best_bid", "price"),
                port("best_ask", "price"),
            ],
            "output_schema": [output("spread", "price_delta")],
            "units_and_bases": {
                "best_ask": "price",
                "best_bid": "price",
                "spread": "price_delta",
            },
            "requirements": [],
        },
        "QTT.COMP.FORMULA.RELATIVE_SPREAD": {
            "complete_mathematical_or_procedural_definition": (
                "relative_spread = spread / max(mid_price, epsilon)"
            ),
            "domain_and_boundary_behavior": (
                "finite numerator and denominator in one declared contextual scalar basis; "
                "denominator >= 1e-9; output is a finite dimensionless ratio"
            ),
            "input_schema": [
                port("spread", "price_delta"),
                port("mid_price", "price"),
            ],
            "output_schema": [output("relative_spread", "ratio")],
            "units_and_bases": {
                "mid_price": "price",
                "relative_spread": "ratio",
                "spread": "price_delta",
            },
            "requirements": [
                requirement(
                    "QTT.COMP.FORMULA.MID_PRICE",
                    "MID_PRICE_DENOMINATOR",
                    "mid_price",
                    "mid_price",
                    "price",
                ),
                requirement(
                    "QTT.COMP.FORMULA.SPREAD",
                    "ABSOLUTE_SPREAD_NUMERATOR",
                    "spread",
                    "spread",
                    "price_delta",
                ),
            ],
        },
    }
    return {
        component_id: {**copy.deepcopy(common), **copy.deepcopy(specific)}
        for component_id, specific in per_component.items()
    }


def _qku_semantic_binding(record: Mapping[str, Any]) -> dict[str, Any]:
    definition = record.get("definition", {})
    return {
        "semantic_version": str(record.get("semantic_version", "")),
        "semantic_fields": {
            field: copy.deepcopy(definition.get(field))
            for field in QKU_INHERITANCE_SEMANTIC_FIELDS
        },
    }


def _reviewed_qku_semantic_policy(
    record: Mapping[str, Any],
) -> tuple[str | None, tuple[str, ...]]:
    component_id = str(record.get("canonical_component_id", ""))
    expected = _reviewed_closed_decimal_semantics().get(component_id)
    if expected is None:
        return None, ()
    issues: list[str] = []
    if str(record.get("semantic_version", "")) != "1.0":
        issues.append("semantic_version")
    definition = record.get("definition", {})
    for field in QKU_INHERITANCE_SEMANTIC_FIELDS:
        if definition.get(field) != expected.get(field):
            issues.append(field)
    independent_oracle = (
        "tests/pr169_qku_comp_control1/test_control1.py::"
        "test_closed_formula_decimal_oracles_are_independent"
    )
    oracle_refs = {
        str(row.get("ref", ""))
        for row in definition.get("oracle_and_test_refs", ())
        if isinstance(row, Mapping)
    }
    if independent_oracle not in oracle_refs:
        issues.append("independent_oracle")
    return "QKU.SEMANTIC.REVIEW.CLOSED_DECIMAL.V1", tuple(sorted(set(issues)))


def _qku_role_applicability_signature(
    record: Mapping[str, Any], role: Mapping[str, Any]
) -> list[dict[str, Any]]:
    qku_id = str(role.get("qku_id", ""))
    result: list[dict[str, Any]] = []
    for binding in record.get("bindings", ()):
        selector = binding.get("qku_binding_selector_or_null")
        selector_scope: str
        if selector in (None, "", {}, []):
            selector_scope = "ALL_QKUS"
            selector_constraints: Any = None
        elif isinstance(selector, str) and selector == qku_id:
            selector_scope = "MATCHES_THIS_QKU"
            selector_constraints = "$THIS_QKU"
        elif isinstance(selector, Mapping) and str(selector.get("qku_id", "")) == qku_id:
            selector_scope = "MATCHES_THIS_QKU"
            selector_constraints = copy.deepcopy(dict(selector))
            selector_constraints["qku_id"] = "$THIS_QKU"
        else:
            continue
        result.append(
            {
                "binding_id": str(binding.get("binding_id", "")),
                "selector_scope": selector_scope,
                "selector_constraints": selector_constraints,
                "market": copy.deepcopy(binding.get("market")),
                "venue": copy.deepcopy(binding.get("venue")),
                "context_selector": copy.deepcopy(binding.get("context_selector")),
                "venue_semantic_version": copy.deepcopy(
                    binding.get("venue_semantic_version")
                ),
                "supported_modes": sorted(
                    str(value) for value in binding.get("supported_modes", ())
                ),
                "requirement_context_policy": copy.deepcopy(
                    binding.get("requirement_context_policy")
                ),
                "selected_requirement_alternatives": copy.deepcopy(
                    binding.get("selected_requirement_alternatives")
                ),
            }
        )
    return sorted(result, key=_stable_json_value)


_QKU_REVIEWED_MARKET_FAMILIES = frozenset(
    {"PREDICTION_MARKET", "prediction_market", "binary_event_contract"}
)
_QKU_APPROVED_NO_EXTERNAL_PROOFS: dict[tuple[str, str], dict[str, Any]] = {}
_QKU_APPROVED_INTERNAL_POLICIES: dict[tuple[str, str], dict[str, Any]] = {}
_QKU_APPROVED_HISTORICAL_PROOFS: dict[tuple[str, str], dict[str, Any]] = {}
_QKU_APPROVED_OFFICIAL_PROOFS: dict[tuple[str, str], dict[str, Any]] = {}
_QKU_BLOCKER_POLICY_TEXT = {
    "TERMINAL_DISPOSITION": (
        "The source disposition is terminal and cannot become execution authority.",
        "Preserve the terminal proof and remove every compute or promotion route.",
    ),
    "INCOMPLETE_OR_NONCANONICAL_SEMANTICS": (
        "The canonical definition is incomplete or not accepted.",
        "Complete the listed semantic fields from primary/official evidence or independent derivation, then rerun oracle and applicability validation.",
    ),
    "REVIEWED_SEMANTIC_BINDING_MISMATCH": (
        "The component ID matches a reviewed family but its exact structured semantics or independent oracle does not.",
        "Create a semantic successor or restore the reviewed exact semantics and rerun independent oracle validation.",
    ),
    "UNAPPROVED_EXTERNAL_VERIFICATION_ESCAPE": (
        "A proof-shaped metadata block is not an approved semantic verification basis.",
        "Join an independently reviewed source claim or policy row to this exact component/version and applicability.",
    ),
    "MISSING_EXTERNAL_OR_DERIVATION_PROOF": (
        "No reviewed primary, official, independent-derivation, or QTT-policy proof is bound to this exact semantic family.",
        "Formulate and verify the exact material claims, attach independent tests, and revalidate applicability before promotion.",
    ),
    "UNVERIFIED_ROLE_APPLICABILITY": (
        "The semantic family proof does not cover this QKU market, venue, context, or binding selector.",
        "Add an exact applicability proof for the selected bindings or keep this QKU role ineligible.",
    ),
}


def _qku_claim_pack_ids(
    record: Mapping[str, Any], verification_state: str
) -> list[str]:
    """Return shared claim packs, never copied source bodies, for one record."""

    component_id = str(record.get("canonical_component_id", ""))
    pack_ids: set[str] = set()
    if verification_state in {
        "UNRESOLVED_MATERIAL_BLOCKER",
        "REJECTED_INVALID_OR_CONTRADICTORY",
    }:
        pack_ids.add(_QKU_UNRESOLVED_PACK)
    origins = {str(value) for value in record.get("origin_cohorts", ())}
    if "RP5C_BASELINE" in origins:
        # RP5C names and route labels are immutable custody hints, never typed
        # semantic-family proof.
        return sorted(pack_ids)
    if component_id in _CLOSED_DECIMAL_COMPONENTS:
        pack_ids.add(_QKU_DECIMAL_PACK)
    if component_id in _CLOSED_DECIMAL_PRICE_COMPONENTS:
        pack_ids.add(_QKU_PRICE_PACK)
    if component_id in _QKU_PRICE_COMPONENT_IDS:
        pack_ids.add(_QKU_PRICE_PACK)
    if component_id in _QKU_INSTITUTIONAL_COMPONENT_IDS:
        pack_ids.add(_QKU_INSTITUTIONAL_PACK)
    if component_id in _QKU_QUANTUM_COMPONENT_IDS:
        pack_ids.add(_QKU_QUANTUM_PACK)
    if component_id in _QKU_PROVIDER_COMPONENT_IDS:
        pack_ids.add(_QKU_PROVIDER_PACK)
    return sorted(pack_ids)


def _qku_direct_verification_state(
    record: Mapping[str, Any], specification_issues: Sequence[str]
) -> tuple[str, str, str | None, str | None]:
    component_id = str(record.get("canonical_component_id", ""))
    semantic_version = str(record.get("semantic_version", ""))
    record_state = str(record.get("record_state", ""))
    if record_state in {"REJECTED_INVALID", "INAPPLICABLE_WITH_PROOF"}:
        return (
            "REJECTED_INVALID_OR_CONTRADICTORY",
            "Terminal source disposition is preserved with its explicit proof; it is not eligible for computation or promotion.",
            "TERMINAL_DISPOSITION",
            None,
        )
    if specification_issues or record_state != "CANONICAL_ACCEPTED":
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "Canonical identity or source custody is preserved, but complete applicable semantics and independent verification are not closed.",
            "INCOMPLETE_OR_NONCANONICAL_SEMANTICS",
            None,
        )
    semantic_policy, semantic_binding_issues = _reviewed_qku_semantic_policy(record)
    if component_id in _CLOSED_DECIMAL_PRIMARY_COMPONENTS:
        if semantic_policy is None or semantic_binding_issues:
            return (
                "UNRESOLVED_MATERIAL_BLOCKER",
                "The reviewed primary-source family does not match this exact structured definition and oracle binding.",
                "REVIEWED_SEMANTIC_BINDING_MISMATCH",
                None,
            )
        return (
            "VERIFIED_BY_PRIMARY_EXTERNAL_SOURCE",
            "Primary prediction-market research plus an independent Decimal derivation supports only the declared normalized price-to-payout arithmetic and its caveats.",
            None,
            semantic_policy,
        )
    if component_id in _CLOSED_DECIMAL_DERIVATION_COMPONENTS:
        if semantic_policy is None or semantic_binding_issues:
            return (
                "UNRESOLVED_MATERIAL_BLOCKER",
                "The reviewed derivation family does not match this exact structured definition and oracle binding.",
                "REVIEWED_SEMANTIC_BINDING_MISMATCH",
                None,
            )
        return (
            "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION",
            "The exact typed arithmetic follows by direct derivation and boundary tests; it does not establish executable economics, calibration, venue truth, or profit.",
            None,
            semantic_policy,
        )
    definition = record.get("definition", {})
    proof_bindings = (
        (
            "external_verification_not_applicable_reason",
            _QKU_APPROVED_NO_EXTERNAL_PROOFS,
            "NO_EXTERNAL_VERIFICATION_APPLICABLE",
        ),
        (
            "qtt_internal_policy_provenance",
            _QKU_APPROVED_INTERNAL_POLICIES,
            "VERIFIED_AS_QTT_INTERNAL_POLICY",
        ),
        (
            "repository_historical_evidence_provenance",
            _QKU_APPROVED_HISTORICAL_PROOFS,
            "VERIFIED_AS_REPOSITORY_HISTORICAL_EVIDENCE",
        ),
        (
            "official_current_documentation_proof",
            _QKU_APPROVED_OFFICIAL_PROOFS,
            "VERIFIED_BY_OFFICIAL_CURRENT_DOCUMENTATION",
        ),
    )
    for field, approved, state in proof_bindings:
        observed = definition.get(field)
        if observed in (None, "", [], {}):
            continue
        expected = approved.get((component_id, semantic_version))
        if expected is not None and observed == expected:
            return state, str(expected.get("reason", field)), None, (
                f"QKU.SEMANTIC.REVIEW.{state}.{component_id}@{semantic_version}"
            )
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "Proof-shaped metadata is not an independently reviewed proof binding.",
            "UNAPPROVED_EXTERNAL_VERIFICATION_ESCAPE",
            None,
        )
    return (
        "UNRESOLVED_MATERIAL_BLOCKER",
        "No complete primary-source, official-current-documentation, independent-derivation, or internal-policy proof is attached to this semantic family.",
        "MISSING_EXTERNAL_OR_DERIVATION_PROOF",
        None,
    )


def _qku_role_direct_verification(
    record: Mapping[str, Any],
    role: Mapping[str, Any],
    specification_issues: Sequence[str],
) -> tuple[str, str, str | None, str | None, list[dict[str, Any]]]:
    state, reason, blocker_code, semantic_policy = _qku_direct_verification_state(
        record, specification_issues
    )
    applicability = _qku_role_applicability_signature(record, role)
    if state not in {
        "UNRESOLVED_MATERIAL_BLOCKER",
        "REJECTED_INVALID_OR_CONTRADICTORY",
    } and (
        not applicability
        or str(role.get("market_family", "")) not in _QKU_REVIEWED_MARKET_FAMILIES
    ):
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "The reviewed semantic proof does not cover this role applicability.",
            "UNVERIFIED_ROLE_APPLICABILITY",
            None,
            applicability,
        )
    return state, reason, blocker_code, semantic_policy, applicability


def _qku_blocker_policy_keys(
    records: Sequence[Mapping[str, Any]], predicate: Callable[[Mapping[str, Any]], Sequence[str]]
) -> list[tuple[str, tuple[str, ...]]]:
    keys: set[tuple[str, tuple[str, ...]]] = set()
    for record in records:
        issues = tuple(str(value) for value in predicate(record.get("definition", {})))
        for role in record.get("uses", {}).get("qku_role_bindings", ()):
            state, _, blocker_code, _, _ = _qku_role_direct_verification(
                record, role, issues
            )
            if state in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }:
                if blocker_code not in _QKU_BLOCKER_POLICY_TEXT:
                    raise BuildError(f"unknown QKU blocker code: {blocker_code!r}")
                keys.add((str(blocker_code), issues))
    return sorted(keys)


def _attach_qku_verification_receipts(
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Attach one compact receipt to every canonical QKU role occurrence.

    This happens after semantic reuse and requirement compilation.  Receipts
    therefore cannot influence candidate matching, identity, or graph shape.
    """

    predicate = getattr(_control_module(), "_specification_completeness_issues", None)
    if not callable(predicate):
        raise BuildError("control owner lacks specification-completeness predicate")
    result = [copy.deepcopy(dict(record)) for record in records]
    blocker_policy_keys = _qku_blocker_policy_keys(result, predicate)
    blocker_policy_ids = {
        key: f"BLOCKER.QKU.VERIFICATION.GROUP.{index:04d}"
        for index, key in enumerate(blocker_policy_keys, 1)
    }
    for record in result:
        component_id = str(record["canonical_component_id"])
        semantic_version = str(record["semantic_version"])
        definition = record.get("definition", {})
        issues = tuple(str(value) for value in predicate(definition))
        roles = record.get("uses", {}).get("qku_role_bindings", [])
        reference_by_applicability: dict[tuple[str, str, str], str] = {}
        for role in sorted(roles, key=_qku_role_ref):
            (
                direct_state,
                direct_reason,
                blocker_code,
                semantic_policy,
                applicability_signature,
            ) = _qku_role_direct_verification(record, role, issues)
            applicability_key = (
                str(role.get("market_family", "")),
                _stable_json_value(role.get("context_selector")),
                _stable_json_value(applicability_signature),
            )
            state = direct_state
            reason = direct_reason
            inheritance_proof: dict[str, Any] | None = None
            reference = reference_by_applicability.get(applicability_key)
            if (
                reference is not None
                and direct_state
                not in {
                    "UNRESOLVED_MATERIAL_BLOCKER",
                    "REJECTED_INVALID_OR_CONTRADICTORY",
                }
            ):
                state = "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE"
                reason = (
                    "This QKU role uses the same canonical component/version and exact "
                    "semantic fields under the same market/context applicability as the "
                    "directly verified reference QKU role."
                )
                inheritance_proof = {
                    "reference_qku_role_ref": reference,
                    "equivalence_policy_id": "QKU.INHERIT.EXACT_SEMANTICS.V1",
                    "applicability_policy_id": (
                        "QKU.INHERIT.EXACT_MARKET_VENUE_CONTEXT_BINDINGS.V1"
                    ),
                    "canonical_component_id": component_id,
                    "semantic_version": semantic_version,
                    "semantic_fields_compared": list(
                        QKU_INHERITANCE_SEMANTIC_FIELDS
                    ),
                    "binding_applicability": copy.deepcopy(
                        applicability_signature
                    ),
                }
            else:
                reference_by_applicability.setdefault(
                    applicability_key, _qku_role_ref(role)
                )
            pack_ids = _qku_claim_pack_ids(record, state)
            mutable_provider_fact = _QKU_PROVIDER_PACK in pack_ids
            semantic_family_resolved = state not in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }
            if role.get("exact_resolution_action"):
                required_next_action_ref = "ROLE"
            else:
                action_binding = next(
                    (
                        binding
                        for binding in record.get("bindings", [])
                        if binding.get("exact_resolution_action_or_null")
                    ),
                    None,
                )
                required_next_action_ref = (
                    f"BINDING:{action_binding.get('binding_id')}"
                    if action_binding is not None
                    else "BLOCKER_POLICY"
                )
            subject_ref = (
                f"{component_id}@{semantic_version}::{_qku_role_ref(role)}"
            )
            receipt = {
                "receipt_schema": QKU_VERIFICATION_RECEIPT_SCHEMA,
                "verification_state": state,
                "claim_family_source_pack_ids": pack_ids,
                "verification_subject": {
                    "component_version_ref": f"{component_id}@{semantic_version}",
                    "qku_role_ref": _qku_role_ref(role),
                },
            }
            if semantic_family_resolved:
                receipt["semantic_family_id"] = f"{component_id}@{semantic_version}"
                receipt["semantic_binding_policy_id"] = semantic_policy
            else:
                receipt["exact_unique_claim"] = {
                    "subject_ref": subject_ref,
                    "claim_kind": blocker_code,
                    "semantic_status": (
                        "TERMINAL"
                        if state == "REJECTED_INVALID_OR_CONTRADICTORY"
                        else "UNRESOLVED"
                    ),
                }
            if state not in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }:
                receipt["reason"] = reason
                receipt["recheck_policy_id"] = (
                    "RECHECK.QKU.SEMANTIC_OR_IMPLEMENTATION_CHANGE"
                )
            if inheritance_proof is not None:
                receipt["inheritance_equivalence_proof_or_null"] = inheritance_proof
            if mutable_provider_fact:
                receipt.update(
                    {
                        "current_fact_as_of_or_retrieval_date": "2026-07-14",
                        "ttl_or_null": "P30D",
                        "recheck_policy_id": (
                            "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION"
                        ),
                    }
                )
            if blocker_code is not None:
                receipt["blocker_policy_id"] = blocker_policy_ids[
                    (blocker_code, issues)
                ]
                receipt["blocker_code"] = blocker_code
                receipt["resolution_action_ref"] = required_next_action_ref
            role["qku_verification_receipt"] = receipt
    return result


def _qku_source_exact_component_consumers(
    pack_id: str,
    source: Mapping[str, Any],
    pack_component_ids: set[str],
) -> list[str]:
    """Return the reviewed exact component IDs affected by one source claim."""

    formula = "QTT.COMP.CANDIDATE.FORMULA.{}".format
    url = str(source.get("url", ""))
    if pack_id == _QKU_PRICE_PACK:
        if "finra.org/" in url:
            expected = {
                formula("SPREAD"),
                formula("POLY_SPREAD_001"),
                "QTT.COMP.FORMULA.SPREAD",
            }
        elif "worldbank.org/" in url:
            expected = {
                formula("SPREAD"),
                formula("POLY_SPREAD_001"),
                "QTT.COMP.FORMULA.MID_PRICE",
                "QTT.COMP.FORMULA.SPREAD",
                "QTT.COMP.FORMULA.RELATIVE_SPREAD",
            }
        else:
            expected = {
                formula("FAIR_PRICE_FROM_PROBABILITY"),
                formula("IMPLIED_PROBABILITY_FROM_BINARY_PRICE"),
                "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
            }
    elif pack_id == _QKU_DECIMAL_PACK:
        expected = set(_CLOSED_DECIMAL_COMPONENTS)
    elif pack_id == _QKU_INSTITUTIONAL_PACK:
        exact_rules = (
            ("ametsoc.org/", {formula("BRIER_SCORE_BINARY"), formula("CALIB_BRIER_001")}),
            ("1995.tb02031", {formula("FDR_BH_001")}),
            ("1956.tb03809", {
                formula("KELLY_FRACTION"), formula("FRACTIONAL_KELLY"),
                formula("CAPPED_KELLY"), formula("PORT_KELLY_001"),
                formula("PORT_KELLY_002"),
            }),
            ("Gneiting07", {
                formula("BRIER_SCORE_BINARY"), formula("CALIB_BRIER_001"),
                formula("LOG_LOSS_BINARY"),
            }),
            ("guo17a", {formula("CALIBRATION_ERROR_CANDIDATE"), formula("CALIB_ECE_001")}),
            ("roelofs22a", {formula("CALIBRATION_ERROR_CANDIDATE"), formula("CALIB_ECE_001")}),
            ("newconceptsintec", {formula("RSI")}),
            ("pandas.pydata.org/", {formula("EMA"), formula("MACD")}),
            ("bollingerbands.com/", {formula("BOLLINGER_BANDS")}),
            ("finra.org/", {formula("TCA_001"), formula("TCA_002")}),
            ("10.21314/JOR", {formula("TCA_001"), formula("TCA_002")}),
            ("iijpormgmt", {formula("FDR_DSR_001")}),
            ("1952.tb01525", {formula("PORTFOLIO_QP_OBJECTIVE"), formula("COVARIANCE")}),
            ("S0047259X03000964", {formula("COVARIANCE")}),
        )
        expected = next(
            (component_ids for marker, component_ids in exact_rules if marker in url),
            set(),
        )
    elif pack_id == _QKU_QUANTUM_PACK:
        exact_rules = (
            ("1411.4028", {formula("QAOA_HAMILTONIAN_MAPPING_CANDIDATE")}),
            ("10.3389/fphy.2014.00005", {
                formula("QUBO_OBJECTIVE_X_T_Q_X"), formula("ISING_ENERGY"),
                formula("EXPANDED_QUBO_TERMS"),
            }),
            ("ncomms5213", {formula("VQE_OBJECTIVE_CANDIDATE")}),
            ("PhysRevE.58.5355", {formula("ANNEALING_BQM_CQM_CANDIDATE")}),
            ("qiskit-optimization", {
                formula("QUBO_OBJECTIVE_X_T_Q_X"),
                formula("QAOA_HAMILTONIAN_MAPPING_CANDIDATE"),
                formula("CQM_OBJECTIVE_AND_CONSTRAINTS"),
            }),
            ("dwavequantum.com", {
                formula("ANNEALING_BQM_CQM_CANDIDATE"), formula("BQM_ENERGY"),
                formula("CQM_OBJECTIVE_AND_CONSTRAINTS"),
            }),
        )
        expected = next(
            (component_ids for marker, component_ids in exact_rules if marker in url),
            set(),
        )
    elif pack_id == _QKU_PROVIDER_PACK:
        exact_rules = (
            ("market/get-market-candlesticks", {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002")}),
            ("market/batch-get-market-candlesticks", {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002")}),
            ("historical_data", {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002"), formula("KALSHI_TRADES_001")}),
            ("market/get-market-orderbook", {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")}),
            ("orderbook_responses", {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")}),
            ("order_direction", {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")}),
            ("market/get-trades", {formula("KALSHI_TRADES_001")}),
            ("quick_start_websockets", {formula("KALSHI_WS_001"), formula("KALSHI_WS_002")}),
            ("changelog", {formula("KALSHI_TICK_001")}),
            ("kalshi-fee-schedule", {formula("KALSHI_FEE_001")}),
            ("fee_rounding", {formula("KALSHI_FEE_001")}),
            ("get-series-fee-changes", {formula("KALSHI_FEE_001")}),
            ("market-data/get-spread", {formula("POLY_SPREAD_001")}),
            ("market-data/get-order-book", {formula("POLY_BOOK_001"), formula("POLY_BOOK_002")}),
            ("trading/orderbook", {formula("POLY_BOOK_001"), formula("POLY_BOOK_002"), formula("POLY_MID_001"), formula("POLY_SPREAD_001")}),
            ("markets/get-prices-history", {formula("POLY_HISTORY_001")}),
            ("market-data/get-last-trade-price", {formula("POLY_LAST_001")}),
            ("market-data/get-midpoint-prices-query-parameters", {formula("POLY_MID_001")}),
            ("concepts/prices-orderbook", {formula("POLY_MID_001")}),
            ("trading/fees", {formula("POLY_TICK_001")}),
            ("builders/fees", {formula("POLY_TICK_001")}),
            ("v2-migration", {formula("POLY_TICK_001")}),
            ("api-reference/wss/market", {formula("POLY_WS_001")}),
            ("market-data/websocket/overview", {formula("POLY_WS_001")}),
        )
        expected = next(
            (component_ids for marker, component_ids in exact_rules if marker in url),
            set(),
        )
    else:
        expected = set()
    return sorted(expected.intersection(pack_component_ids))


def _qku_verification_source_packs(
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build compact shared online source packs for the existing report only."""

    retrieval_date = "2026-07-14"
    base: dict[str, dict[str, Any]] = {
        _QKU_PRICE_PACK: {
            "material_claim_scope": (
                "Prediction-market price interpretation, normalized price/payout, "
                "quoted midpoint, full quoted spread, and midpoint-relative spread."
            ),
            "conflict": (
                "Observed/displayed price is not unconditionally calibrated probability; "
                "midpoint is not executable price; relative-spread denominators vary."
            ),
            "resolution": (
                "Accept only pinned typed arithmetic with same-instrument/time/venue locks; "
                "do not infer fair value, expected cash, calibration, execution, or profit."
            ),
            "sources": [
                {
                    "url": "https://www.nber.org/papers/w12200",
                    "publisher": "National Bureau of Economic Research",
                    "publication_or_version_date": "2006-05",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Prediction-market price/probability assumptions and limitations",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.nber.org/system/files/working_papers/w10504/w10504.pdf",
                    "publisher": "National Bureau of Economic Research",
                    "publication_or_version_date": "2004-05",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Winner-take-all contract interpretation",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.finra.org/rules-guidance/notices/01-16",
                    "publisher": "FINRA",
                    "publication_or_version_date": "2001",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_SRO_DOCUMENTATION",
                    "applicable_scope": "Quoted/effective/realized spread distinctions",
                    "ttl": "RECHECK_ON_REGULATORY_DEFINITION_CHANGE",
                },
                {
                    "url": "https://documents1.worldbank.org/curated/en/099451004052417099/pdf/IDU100d4a04b1bdf71437d1858314d7e3194522c.pdf",
                    "publisher": "World Bank",
                    "publication_or_version_date": "2024",
                    "retrieval_date": retrieval_date,
                    "source_class": "REPUTABLE_INSTITUTIONAL",
                    "applicable_scope": "Midpoint-relative quoted spread convention",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
            ],
            "component_and_test_mappings": [
                *sorted(_CLOSED_DECIMAL_COMPONENTS),
                "tests/pr169_qku_comp_control1/test_control1.py::test_closed_formula_decimal_oracles_are_independent",
            ],
        },
        _QKU_DECIMAL_PACK: {
            "material_claim_scope": (
                "Decimal input boundary and 34-significant-digit ROUND_HALF_EVEN "
                "arithmetic context; arithmetic can round and special values are rejected by QTT."
            ),
            "conflict": (
                "Decimal representation is not unlimited exact arithmetic; IEEE permits "
                "special values while the QTT boundary deliberately fails closed."
            ),
            "resolution": (
                "Pin Python 3.14/local 3.14.4 behavior, precision 34, ROUND_HALF_EVEN, "
                "and no additional output quantization; independently test rounding and rejection."
            ),
            "sources": [
                {
                    "url": "https://standards.ieee.org/ieee/754/6210/",
                    "publisher": "IEEE Standards Association",
                    "publication_or_version_date": "2019",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_STANDARD",
                    "applicable_scope": "Decimal arithmetic, rounding, and special values",
                    "ttl": "RECHECK_ON_STANDARD_MIGRATION",
                },
                {
                    "url": "https://docs.python.org/3.14/library/decimal.html",
                    "publisher": "Python Software Foundation",
                    "publication_or_version_date": "Python 3.14 / local 3.14.4",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_LIBRARY_DOCUMENTATION",
                    "applicable_scope": "Python Decimal context and ROUND_HALF_EVEN runtime semantics",
                    "ttl": "RECHECK_ON_PYTHON_RUNTIME_UPGRADE",
                },
                {
                    "url": "https://speleotrove.com/decimal/",
                    "publisher": "General Decimal Arithmetic / Mike Cowlishaw",
                    "publication_or_version_date": "Current specification site retrieved 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "ORIGINAL_SPECIFICATION",
                    "applicable_scope": "Independent decimal-context derivation",
                    "ttl": "RECHECK_ON_SPECIFICATION_OR_IMPLEMENTATION_CHANGE",
                },
            ],
            "component_and_test_mappings": [
                *sorted(_CLOSED_DECIMAL_COMPONENTS),
                "tests/pr169_qku_comp_control1/test_control1.py::test_closed_decimal_context_and_epsilon_boundaries_are_pinned",
            ],
        },
        _QKU_INSTITUTIONAL_PACK: {
            "material_claim_scope": (
                "Exact current-QKU statistical scoring/calibration, BH/DSR, Kelly, "
                "portfolio/covariance, TCA, and named technical-estimator families."
            ),
            "conflict": (
                "Definitions, loss signs, horizons, dependence assumptions, candidate-family "
                "closure, parameter defaults, and accounting incidence are not interchangeable."
            ),
            "resolution": (
                "Keep every affected QKU provisional until its exact estimator/program, "
                "assumptions, parameters, source data, and independent oracle close."
            ),
            "sources": [
                {
                    "url": "https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml",
                    "publisher": "American Meteorological Society / Glenn W. Brier",
                    "publication_or_version_date": "1950",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Probability-score definition",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x",
                    "publisher": "Royal Statistical Society / Benjamini and Hochberg",
                    "publication_or_version_date": "1995",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "False-discovery-rate control assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://onlinelibrary.wiley.com/doi/10.1002/j.1538-7305.1956.tb03809.x",
                    "publisher": "Bell System Technical Journal / John L. Kelly Jr.",
                    "publication_or_version_date": "1956",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Expected-log-wealth sizing assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.eecs.harvard.edu/cs286r/courses/fall10/papers/Gneiting07.pdf",
                    "publisher": "Journal of the American Statistical Association / Gneiting and Raftery",
                    "publication_or_version_date": "2007",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Proper scoring rules and log-score assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://proceedings.mlr.press/v70/guo17a.html",
                    "publisher": "PMLR / Guo et al.",
                    "publication_or_version_date": "2017",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Calibration-method definitions and limitations",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://proceedings.mlr.press/v151/roelofs22a/roelofs22a.pdf",
                    "publisher": "PMLR / Roelofs et al.",
                    "publication_or_version_date": "2022",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "ECE estimator bias and binning conflicts",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://archive.org/details/newconceptsintec00wild",
                    "publisher": "J. Welles Wilder Jr.",
                    "publication_or_version_date": "1978",
                    "retrieval_date": retrieval_date,
                    "source_class": "ORIGINAL_METHOD_SOURCE",
                    "applicable_scope": "Wilder RSI stateful smoothing semantics",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html",
                    "publisher": "pandas",
                    "publication_or_version_date": "Current library documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_LIBRARY_DOCUMENTATION",
                    "applicable_scope": "EMA adjusted/recursive and initialization convention comparison",
                    "ttl": "RECHECK_ON_PINNED_DEPENDENCY_UPGRADE",
                },
                {
                    "url": "https://www.bollingerbands.com/bollinger-bands",
                    "publisher": "John Bollinger",
                    "publication_or_version_date": "Current original-method documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "ORIGINAL_METHOD_DOCUMENTATION",
                    "applicable_scope": "Bollinger band formula/default convention comparison",
                    "ttl": "P30D_RECHECK_ON_SOURCE_OR_PARAMETER_POLICY_CHANGE",
                },
                {
                    "url": "https://www.finra.org/rules-guidance/notices/01-16",
                    "publisher": "FINRA",
                    "publication_or_version_date": "2001",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_SRO_DOCUMENTATION",
                    "applicable_scope": "Effective and realized spread formula distinctions",
                    "ttl": "RECHECK_ON_REGULATORY_DEFINITION_CHANGE",
                },
                {
                    "url": "https://doi.org/10.21314/JOR.2001.041",
                    "publisher": "Journal of Risk / Almgren and Chriss",
                    "publication_or_version_date": "2001",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Model-specific execution cost/impact optimization",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.pm-research.com/content/iijpormgmt/40/5/94",
                    "publisher": "Journal of Portfolio Management / Bailey and Lopez de Prado",
                    "publication_or_version_date": "2014",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Deflated Sharpe Ratio selection/non-normality inputs",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1952.tb01525.x",
                    "publisher": "Journal of Finance / Harry Markowitz",
                    "publication_or_version_date": "1952",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Mean-variance objective and covariance assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.sciencedirect.com/science/article/pii/S0047259X03000964",
                    "publisher": "Journal of Multivariate Analysis / Ledoit and Wolf",
                    "publication_or_version_date": "2004",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Covariance shrinkage estimator assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
            ],
            "component_and_test_mappings": [
                "QKU receipt joins whose claim_family_source_pack_ids contain this pack",
                "tools/validate_pr169_qku_comp_control1.py::_validate_qku_verification_receipts",
            ],
        },
        _QKU_QUANTUM_PACK: {
            "material_claim_scope": (
                "QUBO/Ising/QAOA and hybrid optimization mappings, inverse feasibility, "
                "penalty/scaling sensitivity, and same-formulation classical comparison."
            ),
            "conflict": (
                "A family label or encoding does not prove equivalence, feasible inverse "
                "mapping, economic utility, provider capability, or quantum advantage."
            ),
            "resolution": (
                "Retain mappings as distinct provisional semantics until exact original-model "
                "parity, constraints, inverse map, parameter provenance, and fallback close."
            ),
            "sources": [
                {
                    "url": "https://arxiv.org/abs/1411.4028",
                    "publisher": "Farhi, Goldstone, and Gutmann",
                    "publication_or_version_date": "2014-11-15",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_PREPRINT",
                    "applicable_scope": "Original QAOA formulation",
                    "ttl": "PROVISIONAL_RECHECK_ON_FORMULATION_OR_IMPLEMENTATION_CHANGE",
                },
                {
                    "url": "https://doi.org/10.3389/fphy.2014.00005",
                    "publisher": "Frontiers in Physics / Andrew Lucas",
                    "publication_or_version_date": "2014",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Ising formulations and constraint encodings",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://www.nature.com/articles/ncomms5213",
                    "publisher": "Nature Communications / Peruzzo et al.",
                    "publication_or_version_date": "2014-07-23",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Original variational quantum eigensolver definition and experimental limitations",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://link.aps.org/doi/10.1103/PhysRevE.58.5355",
                    "publisher": "Physical Review E / Kadowaki and Nishimori",
                    "publication_or_version_date": "1998-11-01",
                    "retrieval_date": retrieval_date,
                    "source_class": "PRIMARY_RESEARCH",
                    "applicable_scope": "Original transverse-field quantum annealing formulation and bounded model assumptions",
                    "ttl": "IMMUTABLE_PUBLICATION_RECHECK_ON_SEMANTIC_SUCCESSOR",
                },
                {
                    "url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
                    "publisher": "Qiskit Optimization",
                    "publication_or_version_date": "Qiskit Optimization 0.7.0",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_OPEN_SOURCE_DOCUMENTATION",
                    "applicable_scope": (
                        "Qiskit Optimization 0.7.0 converter behavior comparison only; pin the "
                        "exact converter/class/version/penalty and prove original-model feasibility"
                    ),
                    "ttl": "P30D_AND_RECHECK_ON_DEPENDENCY_UPGRADE",
                    "version_conflict_resolution": (
                        "The tutorial illustrates LinearEqualityToPenalty with M=100000, while "
                        "QuadraticProgramToQubo(penalty=None) auto-calculates a penalty per conversion. "
                        "CONTROL1 accepts no universal penalty default and infers no provider/runtime support."
                    ),
                },
                {
                    "url": "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
                    "publisher": "Qiskit Optimization",
                    "publication_or_version_date": "Qiskit Optimization 0.7.0",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_OPEN_SOURCE_DOCUMENTATION",
                    "applicable_scope": (
                        "QuadraticProgramToQubo 0.7.0 API contract: penalty=None causes a "
                        "penalty to be calculated on every conversion; convert checks "
                        "compatibility and interpret maps a converted result back to the "
                        "original problem. This does not prove economic feasibility or a "
                        "universal penalty value"
                    ),
                    "ttl": "P30D_AND_RECHECK_ON_DEPENDENCY_UPGRADE",
                },
                {
                    "url": "https://docs.dwavequantum.com/en/latest/quantum_research/reformulating.html",
                    "publisher": "D-Wave Systems",
                    "publication_or_version_date": "Ocean SDK 9.4.0 as observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_PROVIDER_DOCUMENTATION",
                    "applicable_scope": "Reformulation/penalty guidance, not runtime capability proof",
                    "ttl": "P30D_AND_RECHECK_BEFORE_PROVIDER_USE",
                    "version_conflict_resolution": (
                        "Earlier 9.2 handoff was superseded by official Ocean SDK 9.4.0 documentation retrieved 2026-07-14."
                    ),
                },
            ],
            "component_and_test_mappings": [
                "QKU receipt joins whose claim_family_source_pack_ids contain this pack",
                "tests/pr169_qku_comp_control1/test_control1.py quantum parity grouped tests",
            ],
        },
        _QKU_PROVIDER_PACK: {
            "material_claim_scope": (
                "Mutable venue/provider display-price, settlement, lifecycle, payout, fee, "
                "tick, and capability facts."
            ),
            "conflict": (
                "Provider facts change and provider display/settlement conventions differ; "
                "repository labels cannot currentize them."
            ),
            "resolution": (
                "Use no timeless venue constant. Keep the QKU blocked, binding-scoped, dated, "
                "and P30D for research; re-fetch before any promotion or execution."
            ),
            "sources": [
                {
                    "url": "https://docs.kalshi.com/api-reference/market/get-market-candlesticks",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Candlestick endpoint fields and period values only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Batch candlestick fields, request bounds, fixed-point price fields, and synthetic continuity-row semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/getting_started/historical_data",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Mutable live/historical cutoffs and historical candlestick/trade routing only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Binary-market orderbook response semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/getting_started/orderbook_responses",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "YES/NO bid arrays, fixed-point string fields, reciprocal ask reconstruction, and spread examples only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/getting_started/order_direction",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Outcome-side and book-side direction semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/api-reference/market/get-trades",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Public trade endpoint fields and pagination only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/getting_started/quick_start_websockets",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current WebSocket documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "WebSocket endpoint, authentication, and named channel scope only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/changelog",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Changelog through 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Tick-size field deprecation and price-range step migration only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://kalshi.com/docs/kalshi-fee-schedule.pdf",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Effective 2026-07-07; retrieved 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": (
                        "Current general fee round-up of M*0.07*C*P*(1-P), maker coefficient 0.0175, "
                        "and per-series multiplier M; this contradicts the historical 0.035 candidate "
                        "and supplies no timeless fee constant"
                    ),
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                    "official_effective_date": "2026-07-07",
                },
                {
                    "url": "https://docs.kalshi.com/getting_started/fee_rounding",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Fee rounding precision and ceiling semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes",
                    "publisher": "Kalshi",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Series fee-change effective timestamps and fee-type fields only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/market-data/get-spread",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Spread endpoint field semantics only; it does not establish execution-cost incidence",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/market-data/get-order-book",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Order-book bid/ask, timestamp, tick-size, and last-trade fields only; not fill probability",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/trading/orderbook",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Best-price, midpoint, spread, and order-book mechanics only; not executable fill quantity",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/markets/get-prices-history",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Historical price timestamp/value response fields only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/market-data/get-last-trade-price",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Last-trade price response fields only; no trade, lookback, and momentum semantics remain blockers",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/market-data/get-midpoint-prices-query-parameters",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Midpoint endpoint query/response semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/concepts/prices-orderbook",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Displayed midpoint, wide-spread last-trade fallback, and non-executable display-price limitations only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/trading/fees",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Current platform-fee categories and dynamic market fee lookup only; no timeless fee-rate constant",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/builders/fees",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": (
                        "CLOB V2 builder fees are additive to and independent of platform "
                        "fees; builder_fee = notional * builder_fee_rate_bps / 10000; maker "
                        "and taker builder codes/rates may differ. Current limits and rate "
                        "parameters are mutable facts, not timeless constants"
                    ),
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/v2-migration",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "CLOB V2 live 2026-04-28; observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "CLOB V2 cutover and dynamic operator-set market fee semantics only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                    "official_effective_date": "2026-04-28",
                },
                {
                    "url": "https://docs.polymarket.com/api-reference/wss/market",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current WebSocket API documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "Market-channel timestamps, tick-size changes, last trade, best bid/ask, and fee-schedule messages only",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
                {
                    "url": "https://docs.polymarket.com/market-data/websocket/overview",
                    "publisher": "Polymarket",
                    "publication_or_version_date": "Current WebSocket documentation observed 2026-07-14",
                    "retrieval_date": retrieval_date,
                    "source_class": "OFFICIAL_CURRENT_DOCUMENTATION",
                    "applicable_scope": "WebSocket channel scope and message transport only; clock-skew and reconnect policy remain blockers",
                    "ttl": "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION",
                },
            ],
            "component_and_test_mappings": [
                "QKU receipt joins whose claim_family_source_pack_ids contain this pack",
                "tools/validate_pr169_qku_comp_control1.py current-fact TTL/effective-date defect",
            ],
        },
        _QKU_UNRESOLVED_PACK: {
            "material_claim_scope": (
                "Fail-closed disposition for canonical QKU identities whose full material "
                "semantics or applicable external proof has not been closed."
            ),
            "conflict": (
                "Repository presence, name similarity, a fixture, or a historical route label "
                "is not external semantic proof."
            ),
            "resolution": (
                "Emit an exact blocker receipt and prohibit affected replay, PAPER, shadow, "
                "canary, live, resolve, and compute eligibility."
            ),
            "sources": [],
            "source_absence_reason": (
                "This is a QTT fail-closed disposition policy, not an externally sourced "
                "mathematical or current factual claim."
            ),
            "component_and_test_mappings": [
                "Every QKU receipt with UNRESOLVED_MATERIAL_BLOCKER",
                "tools/validate_pr169_qku_comp_control1.py::_validate_qku_verification_receipts",
            ],
        },
    }
    component_consumers: dict[str, set[str]] = defaultdict(set)
    qku_consumer_counts: Counter[str] = Counter()
    qku_consumer_counts_by_component: Counter[tuple[str, str]] = Counter()
    qku_role_refs_by_pack_component: dict[
        tuple[str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    binding_ids_by_component: dict[str, list[str]] = {}
    downstream_consumers_by_component: dict[str, list[str]] = {}
    semantic_versions = {
        str(record["canonical_component_id"]): str(record["semantic_version"])
        for record in records
    }
    for record in records:
        component_id = str(record["canonical_component_id"])
        binding_ids_by_component[component_id] = sorted(
            str(binding.get("binding_id", ""))
            for binding in record.get("bindings", ())
            if binding.get("binding_id") not in (None, "")
        )
        downstream_consumers_by_component[component_id] = sorted(
            {
                str(value)
                for value in record.get("uses", {}).get(
                    "consumer_class_tags", ()
                )
                if value not in (None, "")
            }
            | {
                str(value)
                for binding in record.get("bindings", ())
                for value in binding.get("downstream_consumer_classes", ())
                if value not in (None, "")
            }
        )
        for role in record.get("uses", {}).get("qku_role_bindings", []):
            receipt = role.get("qku_verification_receipt", {})
            for pack_id in receipt.get("claim_family_source_pack_ids", []):
                component_consumers[str(pack_id)].add(component_id)
                qku_consumer_counts[str(pack_id)] += 1
                qku_consumer_counts_by_component[(str(pack_id), component_id)] += 1
                qku_role_refs_by_pack_component[(str(pack_id), component_id)].append(
                    {
                        "qku_role_ref": _qku_role_ref(role),
                        "binding_applicability": _qku_role_applicability_signature(
                            record, role
                        ),
                    }
                )
    result: list[dict[str, Any]] = []
    for pack_id in sorted(base):
        pack = copy.deepcopy(base[pack_id])
        test_oracle_refs = list(pack.pop("component_and_test_mappings", ()))
        pack["claim_family_pack_id"] = pack_id
        pack["exact_consumer_join"] = (
            "registry.ComputationRecordV1.uses.qku_role_bindings[] where "
            f"qku_verification_receipt.claim_family_source_pack_ids contains {pack_id}"
        )
        pack["exact_qku_consumer_count"] = qku_consumer_counts[pack_id]
        pack["exact_component_consumer_count"] = len(component_consumers[pack_id])
        pack["exact_component_consumers"] = sorted(component_consumers[pack_id])
        if pack_id == _QKU_PRICE_PACK:
            pack["exact_component_consumers"] = sorted(
                set(pack["exact_component_consumers"])
                | _CLOSED_DECIMAL_PRICE_COMPONENTS
            )
            pack["exact_component_consumer_count"] = len(
                pack["exact_component_consumers"]
            )
        elif pack_id == _QKU_DECIMAL_PACK:
            pack["exact_component_consumers"] = sorted(
                set(pack["exact_component_consumers"]) | _CLOSED_DECIMAL_COMPONENTS
            )
            pack["exact_component_consumer_count"] = len(
                pack["exact_component_consumers"]
            )
        changeable_pack = pack_id in {
            _QKU_PROVIDER_PACK,
            _QKU_QUANTUM_PACK,
            _QKU_DECIMAL_PACK,
            _QKU_INSTITUTIONAL_PACK,
        }
        affected_fields = (
            [
                "definition.complete_mathematical_or_procedural_definition",
                "definition.input_schema",
                "definition.output_schema",
                "definition.units_and_bases",
                "definition.domain_and_boundary_behavior",
                "definition.precision_and_rounding",
                "definition.oracle_and_test_refs",
            ]
            if pack_id in {_QKU_PRICE_PACK, _QKU_DECIMAL_PACK}
            else [
                "definition.complete_mathematical_or_procedural_definition",
                "definition.parameter_schema_and_default_provenance",
                "definition.oracle_and_test_refs",
                "uses.qku_role_bindings[].qku_verification_receipt",
                "bindings[].exact_resolution_action_or_null",
            ]
        )
        claims: list[dict[str, Any]] = []
        for claim_number, source in enumerate(pack.get("sources", []), 1):
            claim_id = f"{pack_id}.CLAIM.{claim_number:03d}"
            exact_claim = (
                "Use this source only to verify or challenge the bounded claim: "
                f"{source['applicable_scope']}. It does not prove implementation "
                "correctness, applicability outside the exact listed components, or launch readiness."
            )
            source["source_claim_id"] = claim_id
            source["exact_claim_used"] = exact_claim
            source["official_effective_date_or_null"] = source.get(
                "official_effective_date"
            )
            source["observed_as_of_or_retrieval_date"] = retrieval_date
            source["recheck_triggers"] = (
                [
                    "PINNED_VERSION_OR_DOCUMENTATION_CHANGE",
                    "BEFORE_ANY_PROMOTION_OR_EXECUTION",
                ]
                if changeable_pack
                else ["SEMANTIC_SUCCESSOR_OR_SOURCE_CORRECTION"]
            )
            exact_component_ids = _qku_source_exact_component_consumers(
                pack_id,
                source,
                set(pack["exact_component_consumers"]),
            )
            if not exact_component_ids:
                raise BuildError(
                    f"source claim has no exact component consumer: {claim_id}"
                )
            claims.append(
                {
                    "claim_id": claim_id,
                    "exact_claim_text": exact_claim,
                    "source_url_refs": [source["url"]],
                    "applicable_scope": source["applicable_scope"],
                    "exact_component_consumers": [
                        {
                            "canonical_component_id": component_id,
                            "semantic_version": semantic_versions[component_id],
                            "qku_role_occurrence_count": qku_consumer_counts_by_component[
                                (pack_id, component_id)
                            ],
                            "exact_qku_role_applicability_refs": sorted(
                                qku_role_refs_by_pack_component[
                                    (pack_id, component_id)
                                ],
                                key=_stable_json_value,
                            ),
                            "exact_binding_ids": binding_ids_by_component[
                                component_id
                            ],
                            "downstream_consumer_classes": (
                                downstream_consumers_by_component[component_id]
                            ),
                        }
                        for component_id in exact_component_ids
                    ],
                    "affected_registry_fields": affected_fields,
                    "test_oracle_refs": test_oracle_refs,
                    "effective_date_or_null": source[
                        "official_effective_date_or_null"
                    ],
                    "observed_as_of_or_retrieval_date": source[
                        "observed_as_of_or_retrieval_date"
                    ],
                    "ttl": source["ttl"],
                    "conflict_disposition_ref": (
                        f"{pack_id}.conflict_disposition"
                    ),
                }
            )
        pack["claims"] = claims
        if pack_id != _QKU_UNRESOLVED_PACK:
            claim_consumer_union = {
                str(consumer["canonical_component_id"])
                for claim in claims
                for consumer in claim["exact_component_consumers"]
            }
            declared_consumers = set(pack["exact_component_consumers"])
            if claim_consumer_union != declared_consumers:
                raise BuildError(
                    "source-claim consumer closure mismatch for "
                    f"{pack_id}: missing={sorted(declared_consumers - claim_consumer_union)}, "
                    f"unexpected={sorted(claim_consumer_union - declared_consumers)}"
                )
        claim_id_by_url = {
            str(source["url"]): str(source["source_claim_id"])
            for source in pack.get("sources", ())
        }
        material_conflicts: list[dict[str, Any]] = []
        if pack_id == _QKU_PROVIDER_PACK:
            material_conflicts = [
                {
                    "conflict_id": "QKU.CONFLICT.KALSHI_FEE_001.CURRENT_SCHEDULE.V1",
                    "affected_component_ids": [
                        "QTT.COMP.CANDIDATE.FORMULA.KALSHI_FEE_001"
                    ],
                    "repository_claim": "ceil_cent(0.035 * contract_count * price * (1 - price)); price unit is incorrectly declared as contracts",
                    "authoritative_current_claim": "Effective 2026-07-07: round up M*0.07*C*P*(1-P); maker coefficient 0.0175; M is series-specific",
                    "authoritative_urls": [
                        "https://kalshi.com/docs/kalshi-fee-schedule.pdf",
                        "https://docs.kalshi.com/getting_started/fee_rounding",
                        "https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes",
                    ],
                    "source_claim_ids": [
                        claim_id_by_url["https://kalshi.com/docs/kalshi-fee-schedule.pdf"],
                        claim_id_by_url["https://docs.kalshi.com/getting_started/fee_rounding"],
                        claim_id_by_url["https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes"],
                    ],
                    "disposition": "UNRESOLVED_MATERIAL_BLOCKER",
                    "blocker": "HISTORICAL_COEFFICIENT_AND_UNIT_CONTRADICT_CURRENT_SERIES_SCOPED_SCHEDULE",
                    "exact_next_action": "Replace with a semantic successor only after binding the effective series multiplier, maker/taker class, fixed-point price unit, and independent fee-rounding oracle.",
                    "recheck_policy_id": "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
                },
                {
                    "conflict_id": "QKU.CONFLICT.POLY_TICK_001.DYNAMIC_FEE.V1",
                    "affected_component_ids": [
                        "QTT.COMP.CANDIDATE.FORMULA.POLY_TICK_001"
                    ],
                    "repository_claim": "notional * fee_rate_bps / 10000 with fee_rate_bps incorrectly declared as currency",
                    "authoritative_current_claim": "CLOB V2 platform fees are dynamic per market; builder fees use notional * builder_fee_rate_bps / 10000 but are independent and additive, may differ by maker/taker side, and have mutable parameters. The repository expression may match builder-fee arithmetic but does not identify fee category, side, effective binding, or valid units.",
                    "authoritative_urls": [
                        "https://docs.polymarket.com/trading/fees",
                        "https://docs.polymarket.com/builders/fees",
                        "https://docs.polymarket.com/v2-migration",
                    ],
                    "source_claim_ids": [
                        claim_id_by_url["https://docs.polymarket.com/trading/fees"],
                        claim_id_by_url["https://docs.polymarket.com/builders/fees"],
                        claim_id_by_url["https://docs.polymarket.com/v2-migration"],
                    ],
                    "disposition": "UNRESOLVED_MATERIAL_BLOCKER",
                    "blocker": "PLATFORM_VS_BUILDER_FEE_SCOPE_AND_DYNAMIC_MARKET_RATE_UNRESOLVED",
                    "exact_next_action": "Bind current market fee parameters, distinguish platform and builder fees, repair units, and add a dated independent oracle before any promotion.",
                    "recheck_policy_id": "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
                },
                {
                    "conflict_id": "QKU.CONFLICT.POLY_SPREAD_001.COST_INCIDENCE.V1",
                    "affected_component_ids": [
                        "QTT.COMP.CANDIDATE.FORMULA.POLY_SPREAD_001"
                    ],
                    "repository_claim": "spread * contract_count with contract_count declared on a probability-price basis and no accounting-incidence contract",
                    "authoritative_current_claim": "Official endpoints define quoted spread/order-book fields, not a universal execution-cost accounting formula",
                    "authoritative_urls": [
                        "https://docs.polymarket.com/api-reference/market-data/get-spread",
                        "https://docs.polymarket.com/trading/orderbook",
                    ],
                    "source_claim_ids": [
                        claim_id_by_url["https://docs.polymarket.com/api-reference/market-data/get-spread"],
                        claim_id_by_url["https://docs.polymarket.com/trading/orderbook"],
                    ],
                    "disposition": "UNRESOLVED_MATERIAL_BLOCKER",
                    "blocker": "QUANTITY_UNIT_AND_EXECUTION_COST_INCIDENCE_UNRESOLVED",
                    "exact_next_action": "Define contract quantity/currency units, executable-side incidence, fill assumptions, and an independent TCA oracle before promotion.",
                    "recheck_policy_id": "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
                },
            ]
        elif pack_id == _QKU_QUANTUM_PACK:
            material_conflicts = [
                {
                    "conflict_id": "QKU.CONFLICT.QISKIT_0_7_PENALTY_DEFAULT.V1",
                    "affected_component_ids": [
                        "QTT.COMP.CANDIDATE.FORMULA.QUBO_OBJECTIVE_X_T_Q_X",
                        "QTT.COMP.CANDIDATE.FORMULA.QAOA_HAMILTONIAN_MAPPING_CANDIDATE",
                        "QTT.COMP.CANDIDATE.FORMULA.CQM_OBJECTIVE_AND_CONSTRAINTS",
                    ],
                    "repository_claim": "No exact converter class/version/penalty or original-feasibility proof is pinned",
                    "authoritative_current_claim": "Qiskit Optimization 0.7.0 tutorial illustrates M=100000 for one converter while QuadraticProgramToQubo(penalty=None) auto-calculates per conversion; no universal penalty default exists",
                    "authoritative_urls": [
                        "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
                        "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
                    ],
                    "source_claim_ids": [
                        claim_id_by_url["https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html"],
                        claim_id_by_url["https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html"],
                    ],
                    "disposition": "UNRESOLVED_MATERIAL_BLOCKER",
                    "blocker": "CONVERTER_CLASS_VERSION_PENALTY_AND_FEASIBILITY_NOT_PINNED",
                    "exact_next_action": "Pin converter/class/version/penalty, prove original feasible-set preservation and inverse mapping, and run an independent small-instance oracle.",
                    "recheck_policy_id": "RECHECK.QKU.SEMANTIC_OR_IMPLEMENTATION_CHANGE",
                }
            ]
        if material_conflicts:
            pack["material_component_conflicts"] = material_conflicts
        if pack_id in {_QKU_PRICE_PACK, _QKU_DECIMAL_PACK}:
            pack["conflict_disposition"] = {
                "state": "RESOLVED_WITH_AUTHORITATIVE_BASIS_AND_BOUNDED_SCOPE",
                "authoritative_basis_urls": [
                    source["url"] for source in pack.get("sources", [])
                ],
                "unresolved_blocker_or_null": None,
            }
        else:
            pack["conflict_disposition"] = {
                "state": "UNRESOLVED_MATERIAL_BLOCKER",
                "authoritative_basis_urls": [
                    source["url"] for source in pack.get("sources", [])
                ],
                "unresolved_blocker_or_null": (
                    "MISSING_EXACT_QKU_SPECIFICATION_PARAMETER_APPLICABILITY_AND_INDEPENDENT_ORACLE"
                ),
            }
        if len(pack["exact_component_consumers"]) > 500:
            pack["exact_claim_consumers"] = [
                {
                    "consumer_kind": "CANONICAL_QKU_RECEIPT_SET",
                    "exact_join_fields": [
                        "canonical_component_id",
                        "semantic_version",
                        "qku_id",
                        "role_or_decision_stage",
                        "market_family",
                        "context_selector",
                        "claim_family_source_pack_ids",
                    ],
                    "canonical_component_count": pack[
                        "exact_component_consumer_count"
                    ],
                    "qku_role_occurrence_count": pack[
                        "exact_qku_consumer_count"
                    ],
                    "independent_rederivation": (
                        "tools/validate_pr169_qku_comp_control1.py::"
                        "_validate_qku_verification_receipts"
                    ),
                }
            ]
            pack.pop("exact_component_consumers", None)
        else:
            pack["exact_claim_consumers"] = [
                {
                    "consumer_kind": "CANONICAL_COMPONENT",
                    "canonical_component_id": component_id,
                    "registry_fields": (
                        [
                            "definition.complete_mathematical_or_procedural_definition",
                            "definition.input_schema",
                            "definition.output_schema",
                            "definition.units_and_bases",
                            "definition.domain_and_boundary_behavior",
                            "definition.precision_and_rounding",
                            "definition.oracle_and_test_refs",
                        ]
                        if component_id in _CLOSED_DECIMAL_COMPONENTS
                        else [
                            "uses.qku_role_bindings[].qku_verification_receipt",
                            "bindings[].exact_resolution_action_or_null",
                        ]
                    ),
                }
                for component_id in pack["exact_component_consumers"]
            ]
        result.append(pack)
    return result


def _derive_qku_verification_coverage(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    crosswalk: list[dict[str, Any]] = []
    canonical_qku_ids: set[str] = set()
    qku_role_keys: set[tuple[str, str, str, str]] = set()
    disposition_counts: Counter[str] = Counter()
    pack_counts: Counter[str] = Counter()
    missing_receipts = 0
    missing_family_or_claim = 0
    inheritance_without_proof = 0
    na_without_reason = 0
    current_fact_missing_time = 0
    unresolved_escalations = 0
    launch_denominator = 0
    launch_verified = 0
    launch_dispositioned = 0
    launch_blocked = 0
    live_denominator = 0
    live_verified = 0
    live_dispositioned = 0
    live_blocked = 0
    risk_denominator = 0
    risk_verified = 0
    risk_blocked = 0
    venue_denominator = 0
    venue_official_source_covered = 0
    external_or_derivation_states = {
        "VERIFIED_BY_PRIMARY_EXTERNAL_SOURCE",
        "VERIFIED_BY_OFFICIAL_CURRENT_DOCUMENTATION",
        "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION",
    }
    risk_roles = {
        "POSITION_SIZING_CASH_AND_RESERVES",
        "PORTFOLIO_EVENT_VENUE_EXPOSURE",
        "TCA_ACCOUNTING_AND_RECONCILIATION",
        "HARD_SOURCE_RISK_CASH_ALLOW_AND_ROUTER_GATES",
    }
    for record in records:
        component_id = str(record["canonical_component_id"])
        semantic_version = str(record["semantic_version"])
        record_risk = bool(
            risk_roles.intersection(record.get("uses", {}).get("decision_roles", []))
        )
        bindings = record.get("bindings", [])
        role_state_by_ref = {
            _qku_role_ref(role): str(
                role.get("qku_verification_receipt", {}).get(
                    "verification_state", ""
                )
            )
            for role in record.get("uses", {}).get("qku_role_bindings", [])
        }
        live_candidate = any(
            set(str(value) for value in binding.get("supported_modes", ())).intersection(
                {"REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}
            )
            for binding in bindings
        )
        for role in record.get("uses", {}).get("qku_role_bindings", []):
            canonical_qku_ids.add(str(role.get("qku_id", "")))
            qku_role_keys.add(
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                    _stable_json_value(role.get("context_selector")),
                )
            )
            receipt = role.get("qku_verification_receipt")
            if not isinstance(receipt, Mapping):
                missing_receipts += 1
                continue
            state = str(receipt.get("verification_state", ""))
            root_state = state
            if state == "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE":
                proof = receipt.get("inheritance_equivalence_proof_or_null", {})
                root_state = role_state_by_ref.get(
                    str(proof.get("reference_qku_role_ref", "")), ""
                )
            disposition_counts[state] += 1
            pack_ids = [
                str(value)
                for value in receipt.get("claim_family_source_pack_ids", ())
            ]
            pack_counts.update(pack_ids)
            subject = receipt.get("verification_subject")
            expected_subject = {
                "component_version_ref": f"{component_id}@{semantic_version}",
                "qku_role_ref": _qku_role_ref(role),
            }
            exact_claim = receipt.get("exact_unique_claim")
            if subject != expected_subject or (
                not receipt.get("semantic_family_id")
                and not (
                    isinstance(exact_claim, Mapping)
                    and exact_claim.get("subject_ref")
                    == f"{component_id}@{semantic_version}::{_qku_role_ref(role)}"
                    and exact_claim.get("claim_kind") == receipt.get("blocker_code")
                )
            ):
                missing_family_or_claim += 1
            if state == "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE" and not receipt.get(
                "inheritance_equivalence_proof_or_null"
            ):
                inheritance_without_proof += 1
            if state == "NO_EXTERNAL_VERIFICATION_APPLICABLE" and not str(
                receipt.get("reason", "")
            ).strip():
                na_without_reason += 1
            if _QKU_PROVIDER_PACK in pack_ids and (
                not (
                    receipt.get("official_effective_date_or_null")
                    or receipt.get("current_fact_as_of_or_retrieval_date")
                )
                or not receipt.get("ttl_or_null")
            ):
                current_fact_missing_time += 1
            if state in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            } and (
                role.get("runtime_root_eligibility")
                not in {
                    "STATUS_EXPLAIN_ONLY",
                    "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF",
                    "INELIGIBLE_UNTIL_SOURCE_SCOPED_SEMANTICS_ARE_ACCEPTED",
                }
                or live_candidate
                or any(
                    operation in {"resolve", "compute"}
                    for binding in bindings
                    for policy in binding.get("agent_access_policy", {}).values()
                    if isinstance(policy, Mapping)
                    for operation in policy.get("control_plane_operations", ())
                )
            ):
                unresolved_escalations += 1
            launch_candidate = role.get("runtime_root_eligibility") in {
                "ELIGIBLE",
                "RUNTIME_ROOT_ELIGIBLE",
            }
            if launch_candidate:
                launch_denominator += 1
                launch_verified += int(root_state in external_or_derivation_states)
                launch_dispositioned += 1
                launch_blocked += int(
                    state
                    in {
                        "UNRESOLVED_MATERIAL_BLOCKER",
                        "REJECTED_INVALID_OR_CONTRADICTORY",
                    }
                )
            if live_candidate:
                live_denominator += 1
                live_verified += int(root_state in external_or_derivation_states)
                live_dispositioned += 1
                live_blocked += int(
                    state
                    in {
                        "UNRESOLVED_MATERIAL_BLOCKER",
                        "REJECTED_INVALID_OR_CONTRADICTORY",
                    }
                )
            if record_risk or _QKU_INSTITUTIONAL_PACK in pack_ids:
                risk_denominator += 1
                risk_verified += int(root_state in external_or_derivation_states)
                risk_blocked += int(
                    state
                    in {
                        "UNRESOLVED_MATERIAL_BLOCKER",
                        "REJECTED_INVALID_OR_CONTRADICTORY",
                    }
                )
            venue_specific = _QKU_PROVIDER_PACK in pack_ids
            if venue_specific:
                venue_denominator += 1
                venue_official_source_covered += 1
            crosswalk.append(
                {
                    "qku_id": role.get("qku_id"),
                    "role_or_decision_stage": role.get("role_or_decision_stage"),
                    "market_family": role.get("market_family"),
                    "context_selector": copy.deepcopy(role.get("context_selector")),
                    "canonical_component_id": component_id,
                    "semantic_version": semantic_version,
                    "semantic_family_id": receipt.get("semantic_family_id"),
                    "blocker_code": receipt.get("blocker_code"),
                    "verification_state": state,
                    "claim_family_source_pack_ids": pack_ids,
                }
            )
    total = len(crosswalk) + missing_receipts
    alias_without_proof = sum(
        1
        for record in records
        for relation in record.get("relations", [])
        if relation.get("relation_type") == "ALIAS_OF"
        and not (
            relation.get("proof_refs")
            or relation.get("proof_ref")
            or record.get("definition", {}).get("equivalence_proof_refs")
        )
    )
    packs = _qku_verification_source_packs(records)
    required_source_fields = {
        "url",
        "publisher",
        "publication_or_version_date",
        "retrieval_date",
        "source_class",
        "exact_claim_used",
        "applicable_scope",
        "ttl",
        "observed_as_of_or_retrieval_date",
        "recheck_triggers",
    }
    malformed_source_claims = sum(
        not required_source_fields.issubset(source)
        or any(source.get(field) in (None, "", [], {}) for field in required_source_fields)
        for pack in packs
        for source in pack.get("sources", [])
    )
    current_fact_missing_time += sum(
        (
            source.get("source_class")
            in {
                "OFFICIAL_CURRENT_DOCUMENTATION",
                "OFFICIAL_LIBRARY_DOCUMENTATION",
                "OFFICIAL_OPEN_SOURCE_DOCUMENTATION",
                "OFFICIAL_PROVIDER_DOCUMENTATION",
                "OFFICIAL_CURRENT_GUIDANCE",
                "ORIGINAL_METHOD_DOCUMENTATION",
            }
        )
        and (
            not (
                source.get("official_effective_date_or_null")
                or source.get("observed_as_of_or_retrieval_date")
            )
            or not source.get("ttl")
            or not source.get("recheck_triggers")
        )
        for pack in packs
        for source in pack.get("sources", [])
    )
    source_claim_without_consumer = sum(
        not pack.get("exact_claim_consumers")
        for pack in packs
    ) + malformed_source_claims
    conflict_without_blocker = sum(
        bool(pack.get("conflict"))
        and not (
            (
                pack.get("conflict_disposition", {}).get("state")
                == "RESOLVED_WITH_AUTHORITATIVE_BASIS_AND_BOUNDED_SCOPE"
                and pack.get("conflict_disposition", {}).get(
                    "authoritative_basis_urls"
                )
            )
            or (
                pack.get("conflict_disposition", {}).get("state")
                == "UNRESOLVED_MATERIAL_BLOCKER"
                and pack.get("conflict_disposition", {}).get(
                    "unresolved_blocker_or_null"
                )
            )
        )
        for pack in packs
    )
    predicate = getattr(_control_module(), "_specification_completeness_issues", None)
    if not callable(predicate):
        raise BuildError("control owner lacks specification-completeness predicate")
    blocker_policy_keys = _qku_blocker_policy_keys(records, predicate)
    shared_blocker_policies = [
        {
            "blocker_policy_id": f"BLOCKER.QKU.VERIFICATION.GROUP.{index:04d}",
            "blocker_code": blocker_code,
            "missing_semantic_fields": list(issues),
            "reason": _QKU_BLOCKER_POLICY_TEXT[blocker_code][0],
            "required_next_action": _QKU_BLOCKER_POLICY_TEXT[blocker_code][1],
        }
        for index, (blocker_code, issues) in enumerate(blocker_policy_keys, 1)
    ]

    def coverage(numerator: int, denominator: int) -> str:
        return "100%" if denominator == 0 or numerator == denominator else (
            f"{(100 * numerator / denominator):.6f}%"
        )

    crosswalk_groups: dict[
        tuple[str, tuple[str, ...], str, str], dict[str, Any]
    ] = {}
    for row in crosswalk:
        key = (
            str(row["verification_state"]),
            tuple(str(value) for value in row["claim_family_source_pack_ids"]),
            (
                "RESOLVED_CANONICAL_SEMANTICS"
                if row.get("semantic_family_id")
                else "UNRESOLVED_EXACT_QKU_CLAIM_CUSTODY"
            ),
            str(row.get("blocker_code") or "NONE"),
        )
        group = crosswalk_groups.setdefault(
            key,
            {
                "verification_state": key[0],
                "claim_family_source_pack_ids": list(key[1]),
                "semantic_family_resolution": key[2],
                "blocker_code_or_none": key[3],
                "qku_role_occurrence_count": 0,
                "canonical_qku_ids": set(),
                "canonical_component_ids": set(),
                "role_keys": set(),
            },
        )
        group["qku_role_occurrence_count"] += 1
        group["canonical_qku_ids"].add(str(row["qku_id"]))
        group["canonical_component_ids"].add(str(row["canonical_component_id"]))
        group["role_keys"].add(
            (
                str(row["qku_id"]),
                str(row["role_or_decision_stage"]),
                str(row["market_family"]),
                _stable_json_value(row.get("context_selector")),
            )
        )
    compact_crosswalk = []
    for index, key in enumerate(sorted(crosswalk_groups), 1):
        group = crosswalk_groups[key]
        compact_crosswalk.append(
            {
                "crosswalk_group_id": f"QKU.CROSSWALK.GROUP.{index:04d}",
                "verification_state": group["verification_state"],
                "claim_family_source_pack_ids": group[
                    "claim_family_source_pack_ids"
                ],
                "semantic_family_resolution": group[
                    "semantic_family_resolution"
                ],
                "blocker_code_or_none": group["blocker_code_or_none"],
                "canonical_qku_count": len(group["canonical_qku_ids"]),
                "canonical_component_count": len(group["canonical_component_ids"]),
                "qku_role_key_count": len(group["role_keys"]),
                "qku_role_occurrence_count": group[
                    "qku_role_occurrence_count"
                ],
                "exact_registry_join": (
                    "ComputationRecordV1.uses.qku_role_bindings[] by "
                    "(qku_id,role_or_decision_stage,market_family,context_selector,"
                    "containing canonical_component_id,semantic_version) and exact "
                    "qku_verification_receipt state/pack tuple"
                ),
            }
        )

    return {
        "receipt_schema": QKU_VERIFICATION_RECEIPT_SCHEMA,
        "allowed_verification_states": sorted(QKU_VERIFICATION_STATES),
        "qku_verification_disposition_coverage": coverage(
            total - missing_receipts, total
        ),
        "qku_without_verification_receipt_count": missing_receipts,
        "qku_without_semantic_family_or_exact_unique_claim_count": missing_family_or_claim,
        "qku_inheriting_without_equivalence_proof_count": inheritance_without_proof,
        "qku_no_external_verification_without_reason_count": na_without_reason,
        "launch_QKU_external_or_derivation_verification_coverage": coverage(
            launch_verified, launch_denominator
        ),
        "launch_QKU_verification_disposition_coverage": coverage(
            launch_dispositioned, launch_denominator
        ),
        "launch_QKU_positive_verified_count": launch_verified,
        "launch_QKU_unresolved_or_rejected_count": launch_blocked,
        "live_candidate_QKU_verification_coverage": coverage(
            live_verified, live_denominator
        ),
        "live_candidate_QKU_verification_disposition_coverage": coverage(
            live_dispositioned, live_denominator
        ),
        "live_candidate_QKU_positive_verified_count": live_verified,
        "live_candidate_QKU_unresolved_or_rejected_count": live_blocked,
        "risk_and_accounting_QKU_verification_coverage": coverage(
            risk_verified + risk_blocked, risk_denominator
        ),
        "risk_and_accounting_QKU_positive_verification_coverage": coverage(
            risk_verified, risk_denominator
        ),
        "risk_and_accounting_QKU_verified_count": risk_verified,
        "risk_and_accounting_QKU_blocked_count": risk_blocked,
        "risk_and_accounting_QKU_unresolved_or_rejected_count": risk_blocked,
        "risk_and_accounting_QKU_disposition_coverage": coverage(
            risk_verified + risk_blocked, risk_denominator
        ),
        "venue_semantic_QKU_official_source_coverage": coverage(
            venue_official_source_covered, venue_denominator
        ),
        "formula_alias_without_external_or_mathematical_equivalence_proof_count": alias_without_proof,
        "current_fact_without_effective_date_or_TTL_count": current_fact_missing_time,
        "material_source_conflict_without_blocker_count": conflict_without_blocker,
        "source_claim_without_exact_QKU_or_component_consumer_count": source_claim_without_consumer,
        "unresolved_qku_mode_escalation_count": unresolved_escalations,
        "qku_receipt_count": total - missing_receipts,
        "qku_receipt_denominator": total,
        "canonical_unique_qku_count": len(canonical_qku_ids),
        "canonical_unique_qku_source_denominator": EXPECTED_CANONICAL_UNIQUE_QKUS,
        "qku_role_key_count": len(qku_role_keys),
        "qku_role_occurrence_count": total,
        "verification_state_counts": dict(sorted(disposition_counts.items())),
        "claim_family_pack_reference_counts": dict(sorted(pack_counts.items())),
        "shared_blocker_policy_packs": shared_blocker_policies,
        "shared_recheck_policies": [
            {
                "recheck_policy_id": "RECHECK.QKU.SEMANTIC_OR_IMPLEMENTATION_CHANGE",
                "triggers": [
                    "SEMANTIC_SUCCESSOR",
                    "IMPLEMENTATION_OR_ORACLE_CHANGE",
                    "MARKET_OR_VENUE_APPLICABILITY_CHANGE",
                ],
            },
            {
                "recheck_policy_id": "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
                "triggers": [
                    "P30D_RESEARCH_TTL",
                    "BEFORE_ANY_PROMOTION_OR_EXECUTION",
                    "PROVIDER_OR_VENUE_DOCUMENTATION_CHANGE",
                    "BINDING_EFFECTIVE_DATE_OR_VERSION_CHANGE",
                ],
            },
        ],
        "metric_definitions": {
            "launch_QKU_external_or_derivation_verification_coverage": (
                "Positive primary/official/independent-derivation coverage only; denominator zero means CONTROL1 selected no launch QKU and the zero-denominator reason controls interpretation."
            ),
            "launch_QKU_verification_disposition_coverage": (
                "Receipt/disposition coverage across all allowed verification states; this is not positive external or derivation proof."
            ),
            "live_candidate_QKU_verification_coverage": (
                "Positive primary/official/independent-derivation coverage only; denominator zero means CONTROL1 admitted no live candidate QKU and the zero-denominator reason controls interpretation."
            ),
            "live_candidate_QKU_verification_disposition_coverage": (
                "Receipt/disposition coverage across all allowed verification states; this is not positive external or derivation proof."
            ),
            "risk_and_accounting_QKU_verification_coverage": (
                "Required receipt/disposition coverage across all allowed verification states; exact blockers count as disposition only and never as positive proof."
            ),
            "risk_and_accounting_QKU_positive_verification_coverage": (
                "External/official/independent-derivation verification only; unresolved or rejected receipts are excluded."
            ),
        },
        "coverage_denominators": {
            "launch_QKU": launch_denominator,
            "live_candidate_QKU": live_denominator,
            "risk_and_accounting_QKU": risk_denominator,
            "venue_semantic_QKU": venue_denominator,
        },
        "zero_denominator_reasons": {
            "launch_QKU": (
                "CONTROL1 does not select or manufacture a launch QKU; the five closed Decimal arithmetic components have no direct QKU role."
                if launch_denominator == 0
                else None
            ),
            "live_candidate_QKU": (
                "CONTROL1 creates no replay, PAPER, shadow, canary, or live QKU candidate."
                if live_denominator == 0
                else None
            ),
            "venue_semantic_QKU": (
                "No QKU is admitted as a current venue-semantic runtime candidate."
                if venue_denominator == 0
                else None
            ),
        },
        "shared_claim_family_source_packs": packs,
        "qku_to_verification_crosswalk_rows": compact_crosswalk,
    }


def _validate_qku_verification_receipts(
    records: Sequence[Mapping[str, Any]],
    *,
    enforce_current_universe: bool = False,
) -> dict[str, Any]:
    """Builder-side fail-closed check; the independent validator rederives it."""

    metrics = _derive_qku_verification_coverage(records)
    required_zero = (
        "qku_without_verification_receipt_count",
        "qku_without_semantic_family_or_exact_unique_claim_count",
        "qku_inheriting_without_equivalence_proof_count",
        "qku_no_external_verification_without_reason_count",
        "formula_alias_without_external_or_mathematical_equivalence_proof_count",
        "current_fact_without_effective_date_or_TTL_count",
        "material_source_conflict_without_blocker_count",
        "source_claim_without_exact_QKU_or_component_consumer_count",
        "unresolved_qku_mode_escalation_count",
    )
    if metrics["qku_verification_disposition_coverage"] != "100%":
        raise BuildError("QKU verification disposition coverage is not 100%")
    if enforce_current_universe:
        observed = (
            int(metrics["canonical_unique_qku_count"]),
            int(metrics["qku_role_key_count"]),
            int(metrics["qku_role_occurrence_count"]),
        )
        expected = (
            EXPECTED_CANONICAL_UNIQUE_QKUS,
            EXPECTED_QKU_ROLE_KEYS,
            EXPECTED_QKU_ROLE_OCCURRENCES,
        )
        if observed != expected:
            raise BuildError(
                f"canonical QKU verification denominator drift: {observed} != {expected}"
            )
    for name in required_zero:
        if int(metrics[name]) != 0:
            raise BuildError(f"QKU verification invariant failed: {name}={metrics[name]}")
    for name in (
        "launch_QKU_external_or_derivation_verification_coverage",
        "launch_QKU_verification_disposition_coverage",
        "live_candidate_QKU_verification_coverage",
        "live_candidate_QKU_verification_disposition_coverage",
        "risk_and_accounting_QKU_verification_coverage",
        "risk_and_accounting_QKU_disposition_coverage",
        "venue_semantic_QKU_official_source_coverage",
    ):
        if metrics[name] != "100%":
            raise BuildError(f"QKU verification coverage failed: {name}={metrics[name]}")
    return metrics


def _validate_registry(records: Sequence[Mapping[str, Any]], deadline: _Deadline) -> None:
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
    ids: set[str] = set()
    implementation_counts: Counter[str] = Counter()
    owner_requirement_count = 0
    for index, record in enumerate(records):
        if index % 1_000 == 0:
            deadline.check("registry shape validation")
        missing = sorted(required_top - set(record))
        if missing:
            raise BuildError(
                f"record {record.get('canonical_component_id')} lacks fields: {missing}"
            )
        component_id = str(record["canonical_component_id"])
        if not component_id or component_id in ids:
            raise BuildError(f"duplicate or empty canonical component ID: {component_id!r}")
        ids.add(component_id)
        origins = {str(value) for value in record.get("origin_cohorts", [])}
        if (
            "POST_LAUNCH_EXPANSION_BATCH" in origins
            or "BUILDER_TEMPORARY_SCALE_PROBE" in origins
            or component_id.startswith("QTT.COMP.SCALE.")
        ):
            raise BuildError(
                f"synthetic validation record entered canonical truth: {component_id}"
            )
        for provenance in record.get("provenance", []):
            source_ref = str(provenance.get("source_artifact_ref", "")).replace(
                "\\", "/"
            )
            if (
                source_ref.startswith("tests/")
                or source_ref == VALIDATOR_NAME
                or "CONTROL1_FIXED_SEED_SCALE_PROBE" in source_ref
            ):
                raise BuildError(
                    f"test or validator source entered canonical truth: {component_id}: {source_ref}"
                )
        if record["record_state"] not in {
            "PROVISIONAL",
            "UNDER_REVIEW",
            "CANONICAL_ACCEPTED",
            "SUPERSEDED",
            "DORMANT_PRESERVED",
            "REJECTED_INVALID",
            "INAPPLICABLE_WITH_PROOF",
        }:
            raise BuildError(f"invalid record state for {component_id}")
        definition = record["definition"]
        for field in _SEMANTIC_CORE_FIELDS:
            if field not in definition:
                raise BuildError(f"definition {component_id} lacks semantic field {field}")
        qku_roles = record.get("uses", {}).get("qku_role_bindings", [])
        incomplete_rp5c_role_import = bool(
            component_id.startswith("QTT.COMP.RP5C.")
            and qku_roles
            and str(definition.get("complete_mathematical_or_procedural_definition", ""))
            .startswith("MISSING_SEMANTIC_SPECIFICATION:")
        )
        if incomplete_rp5c_role_import:
            if record["record_state"] in {
                "CANONICAL_ACCEPTED",
                "PROVISIONAL",
                "UNDER_REVIEW",
            }:
                raise BuildError(
                    f"incomplete RP5C QKU role import exposed an active runtime root: {component_id}"
                )
            for role in qku_roles:
                if role.get("runtime_root_eligibility") != (
                    "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
                ):
                    raise BuildError(
                        f"incomplete RP5C QKU role lacks runtime ineligibility: {component_id}"
                    )
                if role.get("stack_root_or_direct_component") is not None:
                    raise BuildError(
                        f"builder invented an RP5C runtime root without semantics: {component_id}"
                    )
                if role.get("selection_rule_if_container") is not None:
                    raise BuildError(
                        f"builder invented an RP5C selection rule without semantics: {component_id}"
                    )
        inventory_class = definition.get("implementation_inventory_class")
        if inventory_class is not None:
            if inventory_class not in {"FORMULA", "ALGORITHM", "QUANTUM_CALLABLE_FAMILY"}:
                raise BuildError(f"invalid implementation inventory class for {component_id}")
            implementation_counts[inventory_class] += 1
        for implementation in definition.get("implementation_versions", []):
            if "fixture_inputs" in implementation or "test_inputs" in implementation:
                raise BuildError(
                    f"fixture vector embedded in canonical implementation metadata: {component_id}"
                )
        if definition.get("owner_requirement_crosswalk"):
            owner_requirement_count += 1
        for binding in record["bindings"]:
            if not binding.get("binding_id"):
                raise BuildError(f"empty binding ID for {component_id}")
            readiness = binding.get("readiness", {})
            if readiness.get("authorization") != "NOT_ELIGIBLE":
                raise BuildError(f"builder may not authorize binding {binding['binding_id']}")
            if binding.get("runtime_snapshot_ref_or_null") is not None:
                raise BuildError(f"builder may not create runtime snapshot for {component_id}")
            if binding.get("exact_resolution_action_or_null") in {
                "TBD",
                "SCOPED_GAP",
                "future consumer",
                "metadata only",
                "solver compatible",
                "route later",
                "placeholder",
            }:
                raise BuildError(f"generic terminal text in {component_id}")
        _json_line(record)
        _validate_record_with_control(record)

    expected_implementation_counts = {
        "FORMULA": EXPECTED_FORMULA_IMPLEMENTATIONS,
        "ALGORITHM": EXPECTED_ALGORITHM_IMPLEMENTATIONS,
        "QUANTUM_CALLABLE_FAMILY": EXPECTED_QUANTUM_CALLABLE_FAMILIES,
    }
    if dict(implementation_counts) != expected_implementation_counts:
        raise BuildError(
            "implementation-backed definition counts drift: "
            f"{dict(implementation_counts)!r} != {expected_implementation_counts!r}"
        )
    if owner_requirement_count != EXPECTED_OWNER_REQUIREMENTS:
        raise BuildError(
            f"owner requirement coverage drift: {owner_requirement_count} != {EXPECTED_OWNER_REQUIREMENTS}"
        )
    rp5c_count = sum(component_id.startswith("QTT.COMP.RP5C.") for component_id in ids)
    if rp5c_count != EXPECTED_RP5C_IDENTITIES:
        raise BuildError(f"RP5C coverage drift: {rp5c_count} != {EXPECTED_RP5C_IDENTITIES}")

    # Independently derive the requirement graph and reject unresolved targets
    # or cycles before any physical layout is staged.
    graph: dict[str, set[str]] = {component_id: set() for component_id in ids}
    for record in records:
        component_id = str(record["canonical_component_id"])
        for requirement in record["definition"].get("requirements", []):
            target = requirement.get("required_component_id_or_source_selector")
            if target not in ids:
                raise BuildError(f"unresolved canonical requirement {component_id} -> {target}")
            if not str(target).startswith(("QTT.", "RP5C_")):
                raise BuildError(f"source-local requirement remained after compile: {target}")
            graph[component_id].add(str(target))
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise BuildError(f"post-canonicalization requirement cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(graph[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for component_id in sorted(ids):
        visit(component_id)
    _validate_qku_verification_receipts(records, enforce_current_universe=True)


def _read_registry_layout(out_dir: Path, deadline: _Deadline) -> list[dict[str, Any]]:
    deadline.check("load accepted cumulative registry")
    loader = getattr(_control_module(), "_load_logical_registry", None)
    if not callable(loader):
        raise BuildError("control owner lacks its hardened logical registry loader")
    try:
        records, _ = loader(out_dir)
    except FileNotFoundError:
        return []
    except Exception as exc:
        raise BuildError(f"invalid accepted CONTROL1 registry layout: {exc}") from exc
    if not isinstance(records, list):
        raise BuildError("control logical registry loader returned invalid records")
    return [copy.deepcopy(dict(record)) for record in records]


def _accepted_base_ref(repo_root: Path) -> str:
    """Return the PR branch's exact VCS merge-base with required ``main``."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "HEAD", "origin/main"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
            text=True,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuildError(f"cannot resolve accepted Git base: {exc}") from exc
    base_ref = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", base_ref):
        detail = result.stderr.strip()
        raise BuildError(f"cannot resolve required origin/main merge-base: {detail}")
    return base_ref


def _git_base_tree_paths(
    repo_root: Path, base_ref: str, prefix: Path
) -> set[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-tree",
                "-r",
                "-z",
                "--name-only",
                base_ref,
                "--",
                f"{prefix.as_posix()}/",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BuildError(f"cannot enumerate accepted Git base tree: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BuildError(f"cannot enumerate accepted Git base tree: {detail}")
    try:
        return {
            value.decode("utf-8", errors="strict")
            for value in result.stdout.split(b"\0")
            if value
        }
    except UnicodeDecodeError as exc:
        raise BuildError(f"invalid accepted Git base path encoding: {exc}") from exc


def _materialize_git_base_path(
    repo_root: Path, base_ref: str, relative_path: Path, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as handle:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "show",
                    f"{base_ref}:{relative_path.as_posix()}",
                ],
                stdin=subprocess.DEVNULL,
                stdout=handle,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        destination.unlink(missing_ok=True)
        raise BuildError(f"cannot read accepted Git base path {relative_path}: {exc}") from exc
    if result.returncode != 0:
        destination.unlink(missing_ok=True)
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BuildError(f"cannot read accepted Git base path {relative_path}: {detail}")


def _read_accepted_registry_from_base(
    repo_root: Path, deadline: _Deadline
) -> list[dict[str, Any]]:
    """Read the cumulative accepted registry from the required base branch.

    Generated files already present in the worktree may be a staged candidate,
    so they are never promoted to accepted base state merely by existing.  Git
    is used only as VCS metadata; no QTT digest or content identity is created.
    """

    base_ref = _accepted_base_ref(repo_root)
    single_rel = GENERATED_PREFIX / "registry.jsonl"
    manifest_rel = GENERATED_PREFIX / "registry.manifest.json"
    tree_paths = _git_base_tree_paths(repo_root, base_ref, GENERATED_PREFIX)
    if not tree_paths:
        return []
    prefix_text = f"{GENERATED_PREFIX.as_posix()}/"
    relative_names: set[str] = set()
    for path_text in tree_paths:
        if not path_text.startswith(prefix_text):
            raise BuildError(f"accepted Git base escaped CONTROL1 prefix: {path_text}")
        relative = path_text.removeprefix(prefix_text)
        if not relative or Path(relative).name != relative:
            raise BuildError(f"accepted Git base contains nested CONTROL1 path: {path_text}")
        relative_names.add(relative)
    has_single = single_rel.name in relative_names
    has_manifest = manifest_rel.name in relative_names
    shard_names = {
        name
        for name in relative_names
        if name.startswith("registry.part-") and name.endswith(".jsonl")
    }
    allowed_names = {"acceptance.report.json", *shard_names}
    if has_single:
        allowed_names.add(single_rel.name)
    if has_manifest:
        allowed_names.add(manifest_rel.name)
    unexpected = sorted(relative_names - allowed_names)
    if unexpected:
        raise BuildError(f"accepted Git base contains unexpected CONTROL1 files: {unexpected}")
    if "acceptance.report.json" not in relative_names:
        raise BuildError("accepted Git base lacks acceptance.report.json")
    if has_single and (has_manifest or shard_names):
        raise BuildError("accepted Git base contains two CONTROL1 physical layouts")
    if has_manifest != bool(shard_names):
        raise BuildError(
            "accepted Git base has incomplete sharded layout: "
            f"manifest={has_manifest}, shards={sorted(shard_names)!r}"
        )
    if not has_single and not has_manifest:
        raise BuildError("accepted Git base has no CONTROL1 registry layout")
    with tempfile.TemporaryDirectory(prefix="qtt-control1-accepted-base-") as temporary:
        staged = Path(temporary)
        if has_single:
            _materialize_git_base_path(
                repo_root, base_ref, single_rel, staged / single_rel.name
            )
        else:
            manifest_path = staged / manifest_rel.name
            _materialize_git_base_path(repo_root, base_ref, manifest_rel, manifest_path)
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise BuildError(f"invalid accepted Git base manifest: {exc}") from exc
            partitions = manifest.get("partitions") if isinstance(manifest, Mapping) else None
            if not isinstance(partitions, list) or not partitions:
                raise BuildError("accepted Git base manifest has no partitions")
            names: set[str] = set()
            for partition in partitions:
                name = str(partition.get("file") or "") if isinstance(partition, Mapping) else ""
                if (
                    not name.startswith("registry.part-")
                    or not name.endswith(".jsonl")
                    or Path(name).name != name
                    or name in names
                ):
                    raise BuildError(f"unsafe accepted Git base shard name: {name!r}")
                names.add(name)
                relative = GENERATED_PREFIX / name
                _materialize_git_base_path(
                    repo_root, base_ref, relative, staged / name
                )
                deadline.check("materialize accepted Git base registry")
            if names != shard_names:
                raise BuildError(
                    "accepted Git base manifest/shard set mismatch: "
                    f"declared={sorted(names)!r}, tree={sorted(shard_names)!r}"
                )
        return _read_registry_layout(staged, deadline)


def _load_cumulative_base_records(
    repo_root: Path, target: Path, deadline: _Deadline
) -> list[dict[str, Any]]:
    """Load only accepted Git-base state, independent of output location."""

    del target  # Physical candidate location is never an acceptance authority.
    return _read_accepted_registry_from_base(repo_root, deadline)


def _derive_update(
    base_records: Sequence[Mapping[str, Any]], candidate_records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    helper = getattr(_control_module(), "_derive_registry_update", None)
    if not callable(helper):
        raise BuildError("control owner lacks required transient RegistryUpdateV1 derivation")
    result = helper(
        base_records,
        candidate_records,
        batch_id="TRANSIENT.CONTROL1.BUILD",
    )
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    elif hasattr(result, "__dict__") and not isinstance(result, Mapping):
        result = vars(result)
    if not isinstance(result, Mapping):
        raise BuildError("control _derive_registry_update returned a non-mapping")
    value = dict(result)
    if value.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
        raise BuildError("registry delta schema version is incompatible")
    return value


def _measure_registry(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    serialized_bytes = 0
    max_record_bytes = 0
    for record in records:
        size = len(_json_line(record).encode("utf-8"))
        serialized_bytes += size
        max_record_bytes = max(max_record_bytes, size)
    started = time.perf_counter()
    index = {str(record["canonical_component_id"]): record for record in records}
    index_build_ms = round((time.perf_counter() - started) * 1000.0, 3)
    if len(index) != len(records):
        raise BuildError("index construction detected duplicate canonical IDs")
    return {
        "logical_registry_rows": len(records),
        "logical_registry_serialized_bytes": serialized_bytes,
        "maximum_record_serialized_bytes": max_record_bytes,
        "index_build_ms": index_build_ms,
    }


def _measure_uncompacted_rp5c_counterfactual(
    repo_root: Path,
    records: Sequence[Mapping[str, Any]],
    compact_measurements: Mapping[str, Any],
    deadline: _Deadline,
) -> dict[str, int]:
    """Measure the same registry with the removed RP5C member arrays restored.

    This deterministic source-derived counterfactual is stable across repeated
    builder runs and repair commits.  It measures only the requested lineage
    compaction; a mutable worktree or VCS candidate is never an acceptance
    baseline.
    """

    component_by_source_identity: dict[str, str] = {}
    record_by_component: dict[str, Mapping[str, Any]] = {}
    for record in records:
        component_id = str(record.get("canonical_component_id", ""))
        if not component_id.startswith("QTT.COMP.RP5C."):
            continue
        record_by_component[component_id] = record
        for relation in record.get("relations", []):
            if not isinstance(relation, Mapping):
                continue
            source_identity = str(
                relation.get("source_canonical_identity_row_id", "")
            )
            if source_identity:
                component_by_source_identity[source_identity] = component_id
    members_by_component: dict[str, list[str]] = {}
    for row in _iter_jsonl(repo_root / RP5C_DEDUPE, deadline):
        source_identity = str(row.get("canonical_identity_row_id", ""))
        component_id = component_by_source_identity.get(source_identity)
        if component_id is None:
            raise BuildError(
                f"RP5C compaction counterfactual lacks {source_identity!r}"
            )
        members_by_component[component_id] = sorted(
            str(value)
            for value in row.get("duplicate_member_identity_row_ids", [])
        )
    lineage_ids: dict[str, list[str]] = defaultdict(list)
    artifact_row_ids: dict[str, set[str]] = defaultdict(set)
    for row in _iter_jsonl(repo_root / RP5C_LINEAGE, deadline):
        source_identity = str(row.get("canonical_identity_row_id", ""))
        component_id = component_by_source_identity.get(source_identity)
        if component_id is None:
            raise BuildError(
                f"RP5C lineage counterfactual lacks {source_identity!r}"
            )
        lineage_ids[component_id].append(str(row.get("identity_row_id", "")))
        if row.get("source_artifact_row_id"):
            artifact_row_ids[component_id].add(
                str(row["source_artifact_row_id"])
            )
    compact_rp5c_bytes = 0
    uncompacted_rp5c_bytes = 0
    for index, component_id in enumerate(sorted(record_by_component)):
        if index % 1_000 == 0:
            deadline.check("RP5C compaction counterfactual")
        compact = record_by_component[component_id]
        compact_rp5c_bytes += len(_json_line(compact).encode("utf-8"))
        legacy = copy.deepcopy(dict(compact))
        grouping = next(
            relation
            for relation in legacy["relations"]
            if relation.get("relation_type")
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        )
        lineage = next(
            relation
            for relation in legacy["relations"]
            if relation.get("relation_type") == "RP5C_SOURCE_LINEAGE_SUMMARY"
        )
        grouping["member_identity_row_ids"] = members_by_component[component_id]
        lineage["identity_row_ids"] = sorted(lineage_ids[component_id])
        lineage["source_artifact_row_ids"] = sorted(
            artifact_row_ids[component_id]
        )
        uncompacted_rp5c_bytes += len(_json_line(legacy).encode("utf-8"))
    if len(record_by_component) != EXPECTED_RP5C_IDENTITIES:
        raise BuildError("RP5C compaction counterfactual record-count drift")
    total_compact = int(compact_measurements["logical_registry_serialized_bytes"])
    total_uncompacted = total_compact - compact_rp5c_bytes + uncompacted_rp5c_bytes
    return {
        "compact_rp5c_serialized_bytes": compact_rp5c_bytes,
        "uncompacted_rp5c_counterfactual_serialized_bytes": uncompacted_rp5c_bytes,
        "uncompacted_logical_registry_counterfactual_serialized_bytes": (
            total_uncompacted
        ),
        "compaction_bytes_reduced": total_uncompacted - total_compact,
    }


def _measure_staged_runtime(out_dir: Path) -> dict[str, Any]:
    """Measure the actual staged logical layout and disposable index build."""

    control = _control_module()
    loader = getattr(control, "_load_logical_registry", None)
    snapshot_builder = getattr(control, "_build_snapshot", None)
    if not callable(loader) or not callable(snapshot_builder):
        raise BuildError("control owner lacks staged runtime measurement capabilities")
    tracemalloc.start()
    try:
        load_started = time.perf_counter()
        loaded, layout = loader(out_dir)
        load_ms = (time.perf_counter() - load_started) * 1000.0
        index_started = time.perf_counter()
        snapshot = snapshot_builder(loaded, generation=1)
        index_ms = (time.perf_counter() - index_started) * 1000.0
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {
        "actual_logical_registry_load_ms": round(load_ms, 3),
        "actual_disposable_index_build_ms": round(index_ms, 3),
        "actual_peak_traced_memory_bytes": int(peak_bytes),
        "loaded_row_count": len(loaded),
        "indexed_row_count": len(snapshot.records),
        "active_layout": str(layout.get("layout", "")),
        "measurement_authority": "LOCAL_NON_AUTHORITATIVE_ALGORITHMIC_DIAGNOSTIC",
    }


def _write_layout(
    records: Sequence[Mapping[str, Any]],
    out_dir: Path,
    *,
    force_layout: str,
    measurements: Mapping[str, Any],
    shape_validation_ms: float,
) -> dict[str, Any]:
    helper = getattr(_control_module(), "_write_registry_layout", None)
    if not callable(helper):
        raise BuildError("control owner lacks the sole logical-registry layout writer")
    policy = _control_storage_policy()
    reasons: list[str] = []
    effective_layout = force_layout
    if force_layout != "auto":
        reasons.append(f"FORCED_{force_layout.upper()}")
    else:
        measured_checks = (
            (
                measurements["logical_registry_rows"]
                > int(policy["single_file_max_rows"]),
                "ROW_COUNT",
            ),
            (
                measurements["logical_registry_serialized_bytes"]
                > int(policy["single_file_max_serialized_bytes"]),
                "SERIALIZED_BYTES",
            ),
            (
                measurements["maximum_record_serialized_bytes"]
                > int(policy["max_record_serialized_bytes"]),
                "MAXIMUM_RECORD_SIZE",
            ),
            (
                measurements["index_build_ms"]
                > int(policy["single_file_max_index_build_ms"]),
                "INDEX_BUILD_TIME",
            ),
            (
                shape_validation_ms
                > int(policy["single_file_max_validation_ms"]),
                "VALIDATION_TIME",
            ),
            (
                measurements["logical_registry_serialized_bytes"]
                > int(policy["diff_size_budget_bytes"]),
                "DIFF_SIZE_BUDGET",
            ),
        )
        reasons = [name for exceeded, name in measured_checks if exceeded]
        if reasons:
            effective_layout = "sharded"
        else:
            reasons.append("WITHIN_CONTROL_STORAGE_POLICY")
    result = helper(records, out_dir, force_layout=effective_layout)
    if result is None:
        result = {}
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    elif hasattr(result, "__dict__") and not isinstance(result, Mapping):
        result = vars(result)
    if not isinstance(result, Mapping):
        raise BuildError("control _write_registry_layout returned a non-mapping")
    inspected = _inspect_layout(out_dir)
    inspected["control_writer_result"] = dict(result)
    inspected["policy_reasons"] = reasons
    inspected["storage_policy"] = policy
    return inspected


def _inspect_layout(out_dir: Path) -> dict[str, Any]:
    full = out_dir / "registry.jsonl"
    manifest = out_dir / "registry.manifest.json"
    shards = sorted(out_dir.glob("registry.part-*.jsonl"))
    if full.is_file() and (manifest.is_file() or shards):
        raise BuildError("writer emitted two active physical registry layouts")
    if full.is_file():
        return {"layout": "single", "shard_count": 0, "registry_files": [full.name]}
    if manifest.is_file() and shards:
        return {
            "layout": "sharded",
            "shard_count": len(shards),
            "registry_files": [manifest.name, *(path.name for path in shards)],
        }
    raise BuildError("writer did not emit one complete active registry layout")


def _source_universe_closure(
    repo_root: Path,
    records: Sequence[Mapping[str, Any]],
    deadline: _Deadline,
) -> dict[str, Any]:
    """Classify every declared source row without persisting a second ledger."""

    record_by_id = {str(record["canonical_component_id"]): record for record in records}
    provenance_targets: dict[tuple[str, str], set[str]] = defaultdict(set)
    source_name_targets: dict[str, set[str]] = defaultdict(set)
    implementation_targets: dict[str, set[str]] = defaultdict(set)
    rp5c_identity_targets: dict[str, set[str]] = defaultdict(set)
    rp5c_target_custody_keys: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    expression_targets: dict[str, set[str]] = defaultdict(set)
    qku_targets: dict[str, set[str]] = defaultdict(set)
    status_explain_qku_context_targets: dict[
        tuple[str, str, str], set[str]
    ] = defaultdict(set)
    pr162b_qku_targets: dict[str, set[str]] = defaultdict(set)
    source_selection_tuple_targets: dict[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]], str
    ] = {}
    for record in records:
        component_id = str(record["canonical_component_id"])
        expression = str(
            record.get("definition", {}).get(
                "complete_mathematical_or_procedural_definition", ""
            )
        ).strip()
        if expression:
            expression_targets[expression].add(component_id)
        for provenance in record.get("provenance", []):
            if not isinstance(provenance, Mapping):
                continue
            artifact = str(provenance.get("source_artifact_ref", ""))
            row_ref = str(provenance.get("source_row_ref", ""))
            local_name = str(provenance.get("source_local_identity_or_name", ""))
            if artifact and row_ref:
                provenance_targets[(artifact, row_ref)].add(component_id)
            if local_name:
                source_name_targets[local_name].add(component_id)
        for implementation in record.get("definition", {}).get(
            "implementation_versions", []
        ):
            if isinstance(implementation, Mapping):
                ref = str(implementation.get("callable_or_solver_ref", ""))
                if ref:
                    implementation_targets[ref].add(component_id)
        for relation in record.get("relations", []):
            if not isinstance(relation, Mapping):
                continue
            source_identity = str(
                relation.get("source_canonical_identity_row_id", "")
            )
            if source_identity:
                rp5c_identity_targets[source_identity].add(component_id)
            if relation.get("relation_type") == (
                "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
            ):
                custody_payload = relation.get("source_group_custody_key")
                if not isinstance(custody_payload, Mapping):
                    raise BuildError(
                        f"RP5C target lacks structured custody: {component_id}"
                    )
                rp5c_target_custody_keys[component_id].add(
                    _rp5c_group_custody_tuple(custody_payload)
                )
        origins = {str(value) for value in record.get("origin_cohorts", ())}
        for role in record.get("uses", {}).get("qku_role_bindings", []):
            if isinstance(role, Mapping) and role.get("qku_id"):
                qku_id = str(role["qku_id"])
                root_id = str(
                    role.get("stack_root_or_direct_component") or component_id
                )
                qku_targets[qku_id].add(root_id)
                if role.get("runtime_root_eligibility") == "STATUS_EXPLAIN_ONLY":
                    context_key = (
                        qku_id,
                        str(role.get("role_or_decision_stage", "")),
                        str(role.get("market_family", "")),
                    )
                    status_explain_qku_context_targets[context_key].add(root_id)
                if "PR162B_SOURCE_SEMANTICS" in origins:
                    pr162b_qku_targets[qku_id].add(root_id)
        selection_payload = record.get("definition", {}).get(
            "source_scoped_selection_tuple"
        )
        if isinstance(selection_payload, Mapping):
            raise BuildError(
                "context/evidence co-association was falsely admitted as a "
                f"QKU selection computation: {component_id}"
            )

    loaded: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    artifact_reports: list[dict[str, Any]] = []
    cohort_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cohort_rows: dict[str, int] = defaultdict(int)
    cohort_unresolved: dict[str, list[str]] = defaultdict(list)
    formulation_ids: set[str] = set()
    formulation_targets: dict[str, str] = {}
    source_formula_ids: set[str] = set()
    rp5c_reference_rows = _load_rp5c_reference_custody_rows(
        repo_root, deadline
    )
    current_agent_ids = {
        str(agent_id)
        for record in records
        for binding in record.get("bindings", ())
        if isinstance(binding, Mapping)
        for agent_id in (
            binding.get("agent_access_policy", {}).keys()
            if isinstance(binding.get("agent_access_policy"), Mapping)
            else ()
        )
    }
    candidate_packet_qku_targets: dict[str, str] = {}
    candidate_packet_source_alternative_count = 0
    candidate_packet_known_conflict_count = 0
    agent_reachable_reference_occurrence_count = 0
    agent_reachable_selector_keys: set[tuple[str, str, str]] = set()
    gfp_discovery_blocked_promotion_count = 0
    gfp_discovery_implemented_context_count = 0
    gfp_discovery_input_gap_context_count = 0
    gfp_discovery_category_counts: Counter[str] = Counter()
    owner_retained_selection_tuples: set[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]
    ] = set()
    owner_retained_selection_qkus: set[str] = set()
    owner_retained_selection_qku_cohorts: dict[str, set[str]] = defaultdict(set)

    for spec in SOURCE_UNIVERSE_ARTIFACTS:
        path = str(spec["path"])
        rows, metadata = _read_source_artifact_rows(repo_root, path, deadline)
        loaded[path] = (rows, metadata)
        if len(rows) != int(spec["expected"]):
            raise BuildError(
                f"source cohort denominator drift: {path} {len(rows)} != {spec['expected']}"
            )
        key_field = str(spec.get("key", ""))
        row_keys = [str(row.get(key_field, "")) for row in rows]
        if any(not key for key in row_keys):
            raise BuildError(f"source artifact has empty {key_field}: {path}")
        if len(row_keys) != len(set(row_keys)):
            raise BuildError(f"source artifact has duplicate {key_field}: {path}")
        if path.endswith("PR162D_R2A_FormulationRecordRegistry.report.json"):
            formulation_ids.update(row_keys)
            for row in rows:
                callable_ref = str(row.get("callable_ref", ""))
                targets = implementation_targets.get(callable_ref, set())
                if len(targets) == 1:
                    formulation_targets[str(row["formulation_id"])] = next(iter(targets))
        if spec["role"] == "SEMANTIC_ROOT" and spec["cohort"] in {
            "MAP3",
            "PR162B",
            "GFP",
        }:
            source_formula_ids.update(row_keys)
        if spec["role"] == "SOURCE_DISPOSITION" and spec["cohort"] == "GFP":
            source_formula_ids.update(
                str(row["formula_candidate_id"])
                for row in rows
                if bool(row.get("selected_flag"))
            )

    def normalized_expression(value: Any) -> str:
        return re.sub(r"\s+", "", str(value or "")).casefold()

    gfp_selected_expressions = {
        normalized_expression(row.get("formula_expression"))
        for row in loaded[
            "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json"
        ][0]
        if normalized_expression(row.get("formula_expression"))
    }
    gfp_discovery_exact_expression_match_count = 0
    gfp_discovery_expression_containment_match_count = 0

    for spec in SOURCE_CLOSURE_ARTIFACTS:
        cohort = str(spec["cohort"])
        path = str(spec["path"])
        role = str(spec["role"])
        key_field = str(spec.get("key", ""))
        if path in loaded:
            rows, metadata = loaded[path]
        else:
            # Owner projections are processed one artifact at a time.  This
            # bounds peak memory while still reading every physical row; no
            # projection rows are retained in the acceptance report.
            rows, metadata = _read_source_artifact_rows(repo_root, path, deadline)
            if len(rows) != int(spec["expected"]):
                raise BuildError(
                    f"source cohort denominator drift: {path} {len(rows)} != "
                    f"{spec['expected']}"
                )
        if not key_field:
            key_field = _select_source_row_key_field(rows, path)
        row_keys = (
            []
            if key_field == "__EMPTY_OWNER_SURFACE__"
            else [str(row.get(key_field, "")) for row in rows]
        )
        if any(not key for key in row_keys):
            raise BuildError(f"source artifact has empty {key_field}: {path}")
        if len(row_keys) != len(set(row_keys)):
            raise BuildError(f"source artifact has duplicate {key_field}: {path}")
        dispositions: Counter[str] = Counter()
        unresolved: list[str] = []
        reference_occurrences = 0
        resolved_reference_occurrences = 0
        reference_kind_counts: Counter[str] = Counter()
        resolved_reference_kind_counts: Counter[str] = Counter()
        absence_disposition_counts: Counter[str] = Counter()
        non_computation_context_counts: Counter[str] = Counter()
        source_scoped_selection_counts: Counter[str] = Counter()
        owner_retained_source_local_reference_blocker_count = 0
        semantic_anchor_fields = sorted(
            {
                str(field)
                for row in rows
                for field in row
                if any(
                    token in str(field).casefold()
                    for token in (
                        "formula",
                        "qku",
                        "algorithm",
                        "objective",
                        "constraint",
                        "parameter",
                        "implementation",
                        "callable",
                        "solver",
                        "requirement",
                        "typed_input",
                        "typed_output",
                        "unit",
                        "quantum",
                        "binding",
                        "contract",
                    )
                )
                and str(field)
                not in {
                    "formula_mutation_flag",
                    "qku_mutation_flag",
                    "quantum_advantage_claim_flag",
                    "quantum_backend_execution_flag",
                    "execution_authority_ref",
                    "blocker_policy_ref",
                    "connector_semantic_binding_flag",
                    "qtt_sha_authority_count",
                    "qtt_sha_freeze_checksum_global_digest_authority_count",
                }
            }
        )

        def classify_reference(
            kind: str,
            value: Any,
            row_key: str,
            *,
            expected_targets: set[str] | None = None,
            permitted_target_prefix: str | None = None,
            permitted_component_kind: str | None = None,
        ) -> None:
            nonlocal reference_occurrences, resolved_reference_occurrences
            if value in (None, "", [], {}):
                return
            values = [value] if isinstance(value, str) else value
            if not isinstance(values, Sequence):
                values = [values]
            for raw in values:
                reference = str(raw or "")
                if not reference or reference.endswith("::QKU_REF_NOT_PRESENT"):
                    continue
                reference_occurrences += 1
                reference_kind_counts[kind] += 1
                if kind == "QKU":
                    targets = qku_targets.get(reference, set())
                elif kind == "FORMULATION":
                    targets = (
                        {formulation_targets[reference]}
                        if reference in formulation_targets
                        else set()
                    )
                elif kind == "CALLABLE":
                    targets = implementation_targets.get(reference, set())
                else:
                    targets = source_name_targets.get(reference, set())
                if permitted_target_prefix is not None:
                    targets = {
                        target
                        for target in targets
                        if target.startswith(permitted_target_prefix)
                    }
                if permitted_component_kind is not None:
                    targets = {
                        target
                        for target in targets
                        if str(
                            record_by_id[target]
                            .get("definition", {})
                            .get("component_kind", "")
                        )
                        == permitted_component_kind
                    }
                if expected_targets is not None:
                    resolved = bool(expected_targets) and expected_targets.issubset(
                        targets
                    )
                else:
                    resolved = len(targets) == 1
                if resolved:
                    resolved_reference_occurrences += 1
                    resolved_reference_kind_counts[kind] += 1
                else:
                    unresolved.append(
                        f"{row_key}: unresolved or ambiguous {kind.lower()} "
                        f"reference={reference!r} targets={sorted(targets)} "
                        f"expected={sorted(expected_targets) if expected_targets is not None else 'EXACTLY_ONE'}"
                    )

        def require_qku_role_association(
            targets: set[str], qku_values: Any, row_key: str, label: str
        ) -> None:
            values = [qku_values] if isinstance(qku_values, str) else qku_values
            if values in (None, "", [], {}):
                return
            if not isinstance(values, Sequence):
                values = [values]
            for target_id in sorted(targets):
                role_ids = {
                    str(role_row.get("qku_id", ""))
                    for role_row in record_by_id[target_id]
                    .get("uses", {})
                    .get("qku_role_bindings", [])
                    if isinstance(role_row, Mapping)
                }
                missing = sorted(
                    str(value)
                    for value in values
                    if value
                    and not str(value).endswith("::QKU_REF_NOT_PRESENT")
                    and str(value) not in role_ids
                )
                if missing:
                    unresolved.append(
                        f"{row_key}: {label} target {target_id} lacks QKU roles {missing}"
                    )

        def require_status_explain_qku_association(
            target_id: str,
            qku_values: Any,
            row_key: str,
            *,
            expected_role: str | None = None,
            expected_market: str | None = None,
        ) -> None:
            nonlocal agent_reachable_reference_occurrence_count
            values = (
                [qku_values]
                if isinstance(qku_values, str)
                else qku_values
            )
            if values in (None, "", [], {}):
                return
            if not isinstance(values, Sequence):
                values = [values]
            roles = [
                role_row
                for role_row in record_by_id[target_id]
                .get("uses", {})
                .get("qku_role_bindings", [])
                if isinstance(role_row, Mapping)
            ]
            for raw_qku in values:
                qku_id = str(raw_qku)
                matches = [
                    role_row
                    for role_row in roles
                    if str(role_row.get("qku_id", "")) == qku_id
                    and role_row.get("runtime_root_eligibility")
                    == "STATUS_EXPLAIN_ONLY"
                    and (
                        expected_role is None
                        or str(role_row.get("role_or_decision_stage", ""))
                        == expected_role
                    )
                    and (
                        expected_market is None
                        or str(role_row.get("market_family", ""))
                        == expected_market
                    )
                ]
                if len(matches) != 1:
                    unresolved.append(
                        f"{row_key}: status/explain QKU association {qku_id!r} "
                        f"to {target_id} has {len(matches)} matches"
                    )
                    continue
                role_value = str(matches[0].get("role_or_decision_stage", ""))
                market_value = str(matches[0].get("market_family", ""))
                context_key = (qku_id, role_value, market_value)
                if status_explain_qku_context_targets.get(context_key) != {target_id}:
                    unresolved.append(
                        f"{row_key}: ambiguous status/explain QKU context "
                        f"{context_key!r} -> "
                        f"{sorted(status_explain_qku_context_targets.get(context_key, set()))}"
                    )
                    continue
                agent_reachable_reference_occurrence_count += 1
                agent_reachable_selector_keys.add(context_key)
        for row in rows:
            row_key = (
                "EMPTY_OWNER_SURFACE"
                if key_field == "__EMPTY_OWNER_SURFACE__"
                else str(row[key_field])
            )
            disposition = ""
            target: str | None = None
            owner_projection = role in {"OWNER_PROJECTION", "OWNER_CONTEXT"}
            if owner_projection:
                false_targets = provenance_targets.get((path, row_key), set())
                if false_targets:
                    unresolved.append(
                        f"{row_key}: owner projection was falsely admitted as "
                        f"canonical computation {sorted(false_targets)}"
                    )
                disposition = str(
                    spec.get(
                        "projection_disposition",
                        "SOURCE_OWNER_PROJECTION_RETAINED_WITH_OWNER",
                    )
                )
                target = f"SOURCE_OWNER::{path}::{row_key}"

                if cohort == "RP5D" and all(
                    field in row for field in ("identity_ref", "formula_ref", "qku_ref")
                ):
                    try:
                        mapping = _classify_rp5d_reference_mapping(
                            row,
                            source_path=path,
                            rp5c_reference_rows=rp5c_reference_rows,
                            identity_targets=rp5c_identity_targets,
                            target_custody_keys=rp5c_target_custody_keys,
                        )
                    except BuildError as exc:
                        unresolved.append(str(exc))
                    else:
                        for kind in sorted(mapping["real_references"]):
                            reference_occurrences += 1
                            resolved_reference_occurrences += 1
                            reference_kind_counts[kind] += 1
                            resolved_reference_kind_counts[kind] += 1
                        for kind in sorted(mapping["absence_dispositions"]):
                            absence_disposition_counts[
                                f"{kind}_REF_NOT_PRESENT"
                            ] += 1
                elif cohort == "RP5D":
                    identity_values = {
                        str(value)
                        for field in (
                            "result_identity_refs",
                            "resolved_executable_identity_refs",
                            "excluded_identity_refs",
                        )
                        for value in row.get(field, ())
                        if isinstance(value, str)
                        and value.startswith("RP5C_IDENTITY_")
                    }
                    for identity_ref in sorted(identity_values):
                        if (
                            identity_ref not in rp5c_reference_rows
                            or len(rp5c_identity_targets.get(identity_ref, set())) != 1
                        ):
                            unresolved.append(
                                f"{row_key}: unresolved RP5C identity projection "
                                f"{identity_ref}"
                            )
                        else:
                            reference_occurrences += 1
                            resolved_reference_occurrences += 1
                            reference_kind_counts["RP5C_IDENTITY"] += 1
                            resolved_reference_kind_counts["RP5C_IDENTITY"] += 1

                if cohort in {"RP5D_R1", "RP5E"}:
                    for field in (
                        "formula_id",
                        "formula_ids",
                        "formula_ref",
                        "formula_refs",
                        "eligible_formula_ids",
                    ):
                        if field in row:
                            for formula_ref in _source_reference_values(row.get(field)):
                                targets = source_name_targets.get(formula_ref, set())
                                if len(targets) == 1:
                                    reference_occurrences += 1
                                    resolved_reference_occurrences += 1
                                    reference_kind_counts["FORMULA"] += 1
                                    resolved_reference_kind_counts["FORMULA"] += 1
                                else:
                                    owner_retained_source_local_reference_blocker_count += 1
                                    source_scoped_selection_counts[
                                        "OWNER_RETAINED_SOURCE_LOCAL_FORMULA_REFERENCE_"
                                        "REQUIRES_DIRECT_SEMANTIC_PROOF"
                                    ] += 1
                    for field in ("qku_id", "qku_ids", "qku_ref", "qku_refs"):
                        if field in row:
                            values = _source_reference_values(row.get(field))
                            resolvable = [
                                value
                                for value in values
                                if not value.endswith("::QKU_REF_NOT_PRESENT")
                                and value in qku_targets
                            ]
                            classify_reference("QKU", resolvable, row_key)
                            owner_retained_source_local_reference_blocker_count += sum(
                                not value.endswith("::QKU_REF_NOT_PRESENT")
                                and value not in qku_targets
                                for value in values
                            )

                if "AtomicRowsComputationCoverage" in path or (
                    cohort == "QUANTUM_559" and owner_projection
                ):
                    forbidden_nonzero = {
                        field: value
                        for field, value in row.items()
                        if any(token in str(field).casefold() for token in ("sha", "hash", "digest"))
                        and value not in (0, False, None, "", [], {})
                    }
                    if forbidden_nonzero:
                        unresolved.append(
                            f"{row_key}: forbidden hash/SHA/digest authority fields "
                            f"{sorted(forbidden_nonzero)}"
                        )
            elif role == "SEMANTIC_ROOT" and cohort == "PR162D":
                callable_ref = str(row.get("callable_ref", ""))
                targets = implementation_targets.get(callable_ref, set())
                if len(targets) == 1:
                    target = next(iter(targets))
                    formulation_type = str(row.get("formulation_type", ""))
                    disposition = (
                        "PARAMETER_POLICY_MAPPING"
                        if formulation_type == "PARAMETER_PACK"
                        else "IMPLEMENTATION_VERSION_MAPPING"
                    )
                else:
                    unresolved.append(
                        f"{row_key}: callable_ref={callable_ref!r} targets={sorted(targets)}"
                    )
            elif role == "SEMANTIC_ROOT":
                targets = provenance_targets.get((path, row_key), set())
                if len(targets) == 1:
                    target = next(iter(targets))
                    target_record = record_by_id[target]
                    if target_record.get("record_state") != "PROVISIONAL":
                        unresolved.append(f"{row_key}: source candidate was over-promoted")
                    else:
                        disposition = "GENUINE_PROVISIONAL_NEW_COMPUTATION"
                else:
                    unresolved.append(f"{row_key}: provenance targets={sorted(targets)}")
            elif role == "QKU_ROLE":
                targets = provenance_targets.get(
                    (
                        "docs/master_plan/generated/map3/formula_materialization_rows.jsonl",
                        str(row.get("formula_id", "")),
                    ),
                    set(),
                )
                if len(targets) == 1:
                    target = next(iter(targets))
                    qku_id = str(row.get("qku_id_if_available", ""))
                    target_roles = {
                        str(role_row.get("qku_id", ""))
                        for role_row in record_by_id[target]
                        .get("uses", {})
                        .get("qku_role_bindings", [])
                        if isinstance(role_row, Mapping)
                    }
                    if qku_id and qku_id in target_roles:
                        disposition = "QKU_DECISION_ROLE_MAPPING"
                        classify_reference(
                            "QKU", qku_id, row_key, expected_targets={target}
                        )
                        require_status_explain_qku_association(
                            target, qku_id, row_key
                        )
                    else:
                        unresolved.append(
                            f"{row_key}: MAP3 QKU {qku_id!r} not attached to {target}"
                        )
                else:
                    unresolved.append(f"{row_key}: MAP3 semantic target={sorted(targets)}")
            elif role == "PROVENANCE_MAPPING" and cohort == "RP5D":
                targets = rp5c_identity_targets.get(str(row.get("identity_ref", "")), set())
                if len(targets) == 1:
                    target = next(iter(targets))
                    disposition = "EXISTING_CANONICAL_RECORD_PROVENANCE_MAPPING"
                else:
                    unresolved.append(f"{row_key}: RP5C target={sorted(targets)}")
            elif role == "SOURCE_DISPOSITION":
                if bool(row.get("selected_flag")):
                    expression = str(row.get("formula_expression", "")).strip()
                    targets = expression_targets.get(expression, set())
                    targets = {
                        candidate
                        for candidate in targets
                        if "GFP_SOURCE_SEMANTICS" in record_by_id[candidate].get(
                            "origin_cohorts", []
                        )
                    }
                    if len(targets) == 1:
                        target = next(iter(targets))
                        disposition = "IMPLEMENTATION_VERSION_MAPPING"
                    else:
                        unresolved.append(
                            f"{row_key}: selected GFP expression targets={sorted(targets)}"
                        )
                else:
                    reason = str(
                        row.get("rejection_or_deprioritization_reason", "")
                    ).strip()
                    if reason:
                        disposition = "INAPPLICABLE_TERMINAL"
                    else:
                        unresolved.append(f"{row_key}: missing terminal reason")
            elif role == "SEMANTIC_CANDIDATE":
                targets = provenance_targets.get((path, row_key), set())
                if len(targets) == 1:
                    target = next(iter(targets))
                    if record_by_id[target].get("record_state") != "PROVISIONAL":
                        unresolved.append(f"{row_key}: source candidate was over-promoted")
                    else:
                        disposition = "GENUINE_PROVISIONAL_NEW_COMPUTATION"
                        classify_reference(
                            "QKU",
                            row.get("qku_refs"),
                            row_key,
                            expected_targets={target},
                        )
                else:
                    unresolved.append(
                        f"{row_key}: candidate provenance targets={sorted(targets)}"
                    )
            elif role == "SOURCE_TEST_VECTOR" and cohort == "PR162B":
                targets = provenance_targets.get((path, row_key), set())
                callable_ref = (
                    f"{row.get('implementation_module', '')}:"
                    f"{row.get('implementation_function', '')}"
                )
                callable_targets = implementation_targets.get(callable_ref, set())
                if len(targets) != 1 or targets != callable_targets:
                    unresolved.append(
                        f"{row_key}: PR162B vector target={sorted(targets)} "
                        f"callable_target={sorted(callable_targets)}"
                    )
                else:
                    target = next(iter(targets))
                    disposition = "SOURCE_IMPLEMENTATION_TEST_VECTOR_MAPPING"
            elif role == "DISCOVERY":
                # These capped discovery catalogs contain lossy labels and
                # descriptions, not full typed computation semantics.  A
                # selected_formula_id/coverage label cannot establish a
                # canonical mapping or value-level consumption.
                if _gfp_discovery_has_complete_typed_semantics(row):
                    unresolved.append(
                        f"{row_key}: unexpected complete typed discovery row "
                        "requires explicit proof review"
                    )
                selected_formula_id = str(row.get("selected_formula_id", ""))
                expected_variable_map = (
                    "PR168_GFP_SELECTED_FORMULA::"
                    f"{selected_formula_id}::variable_map"
                )
                if selected_formula_id not in source_formula_ids:
                    unresolved.append(
                        f"{row_key}: selected_formula_id={selected_formula_id!r} "
                        "does not resolve to the selected GFP owner surface"
                    )
                if row.get("variable_map_ref") != expected_variable_map:
                    unresolved.append(
                        f"{row_key}: variable_map_ref does not close to "
                        f"{selected_formula_id!r}"
                    )
                if row.get("source_coverage_status") != "COVERED_BY_SELECTED_FORMULA":
                    unresolved.append(
                        f"{row_key}: source coverage is not owner-dispositioned"
                    )
                implementation_status = str(row.get("implementation_status", ""))
                if implementation_status == "IMPLEMENTED_DETERMINISTIC_FUNCTION":
                    gfp_discovery_implemented_context_count += 1
                    disposition = (
                        "SOURCE_OWNER_HISTORICAL_IMPLEMENTATION_MAPPING_"
                        "REQUIRES_DIRECT_SEMANTIC_PROOF"
                    )
                elif implementation_status == (
                    "COEFFICIENT_MAP_REQUIRED_INPUT_GAP_ROUTE_ASSIGNED"
                ):
                    gfp_discovery_input_gap_context_count += 1
                    disposition = (
                        "SOURCE_OWNER_HISTORICAL_INPUT_GAP_MAPPING_"
                        "REQUIRES_DIRECT_SEMANTIC_PROOF"
                    )
                else:
                    unresolved.append(
                        f"{row_key}: unknown implementation_status="
                        f"{implementation_status!r}"
                    )
                # The selected-formula association is an exact owner-retained
                # coverage mapping, not semantic identity, implementation
                # equivalence, readiness, or runtime authority.  It therefore
                # closes row disposition while retaining a promotion blocker.
                gfp_discovery_blocked_promotion_count += 1
                category = str(
                    row.get(
                        "objective_or_constraint_or_solver_or_execution_or_risk_or_portfolio_or_regime",
                        "UNCLASSIFIED",
                    )
                )
                gfp_discovery_category_counts[category] += 1
                discovery_expression = normalized_expression(
                    row.get("formula_expression_or_description")
                )
                if discovery_expression in gfp_selected_expressions:
                    gfp_discovery_exact_expression_match_count += 1
                if discovery_expression and any(
                    selected in discovery_expression
                    or discovery_expression in selected
                    for selected in gfp_selected_expressions
                ):
                    gfp_discovery_expression_containment_match_count += 1
            else:
                disposition = "NON_COMPUTATION_CONTEXT_OR_EVIDENCE_RETAINED_WITH_OWNER"
                target = f"SOURCE_OWNER::{row_key}"

            if disposition:
                dispositions[disposition] += 1
            else:
                unresolved.append(f"{row_key}: no disposition")

            if cohort == "RP5D" and not owner_projection:
                try:
                    rp5d_mapping = _classify_rp5d_reference_mapping(
                        row,
                        source_path=path,
                        rp5c_reference_rows=rp5c_reference_rows,
                        identity_targets=rp5c_identity_targets,
                        target_custody_keys=rp5c_target_custody_keys,
                    )
                except BuildError as exc:
                    unresolved.append(str(exc))
                else:
                    target = str(rp5d_mapping["target"])
                    for kind in sorted(rp5d_mapping["real_references"]):
                        reference_occurrences += 1
                        resolved_reference_occurrences += 1
                        reference_kind_counts[kind] += 1
                        resolved_reference_kind_counts[kind] += 1
                    for kind in sorted(rp5d_mapping["absence_dispositions"]):
                        absence_disposition_counts[f"{kind}_REF_NOT_PRESENT"] += 1
                if path.endswith("rp5d_comp_materialization.jsonl"):
                    adapter_refs = row.get("required_formula_to_pnl_refs")
                    if adapter_refs != [RP5D_FORMULA_TO_PNL_CONTEXT_REF]:
                        unresolved.append(
                            f"{row_key}: invalid required_formula_to_pnl_refs="
                            f"{adapter_refs!r}"
                        )
                    else:
                        non_computation_context_counts[
                            "REQUIRED_FORMULA_TO_PNL_ADAPTER_CONTRACT"
                        ] += 1

            if cohort == "CANDIDATE_PACKET_6502":
                formulation_ref = str(row.get("formulation_ref", ""))
                if formulation_ref not in formulation_ids:
                    unresolved.append(
                        f"{row_key}: unresolved formulation_ref={formulation_ref!r}"
                    )
                target_id = formulation_targets.get(formulation_ref)
                callable_ref = str(row.get("callable_ref", ""))
                callable_targets = implementation_targets.get(callable_ref, set())
                if target_id is None or callable_targets != {target_id}:
                    unresolved.append(
                        f"{row_key}: CandidatePacket formulation/callable mismatch "
                        f"{formulation_ref!r}->{target_id!r}, "
                        f"{callable_ref!r}->{sorted(callable_targets)}"
                    )
                classify_reference(
                    "FORMULATION",
                    formulation_ref,
                    row_key,
                    expected_targets={target_id} if target_id else set(),
                )
                classify_reference(
                    "CALLABLE",
                    callable_ref,
                    row_key,
                    expected_targets={target_id} if target_id else set(),
                )
                qku_values = _source_reference_values(row.get("qku_ids"))
                if len(qku_values) != 1:
                    unresolved.append(
                        f"{row_key}: CandidatePacket must name one QKU: {qku_values!r}"
                    )
                if (
                    row.get("source_truth_status") != "OWNER_TEMPLATE"
                    or row.get("candidate_truth_status")
                    != "REPLAY_PAPER_CANDIDATE"
                    or row.get("official_truth_flag") is not False
                ):
                    unresolved.append(
                        f"{row_key}: CandidatePacket truth-state drift"
                    )
                downstream_agents = {
                    str(value) for value in row.get("downstream_agent_refs", ())
                }
                if downstream_agents.intersection(current_agent_ids):
                    unresolved.append(
                        f"{row_key}: CandidatePacket pseudo-agent refs overlap "
                        f"current PR165-D2 roster"
                    )
                for qku_id in qku_values:
                    reference_occurrences += 1
                    resolved_reference_occurrences += 1
                    reference_kind_counts["QKU"] += 1
                    resolved_reference_kind_counts["QKU"] += 1
                    prior_target = candidate_packet_qku_targets.setdefault(
                        qku_id, str(target_id or "")
                    )
                    if prior_target != str(target_id or ""):
                        unresolved.append(
                            f"{row_key}: CandidatePacket QKU {qku_id} maps to "
                            f"multiple implementation targets"
                        )
                    candidate_packet_source_alternative_count += 1
                    conflicts = pr162b_qku_targets.get(qku_id, set())
                    if conflicts and target_id not in conflicts:
                        candidate_packet_known_conflict_count += 1
                source_scoped_selection_counts[
                    "OWNER_TEMPLATE_REPLAY_PAPER_CANDIDATE_NO_RUNTIME_ROOT"
                ] += len(qku_values)
            if cohort == "FIXTURE_5":
                for formula_ref in row.get("formula_ids", []):
                    if str(formula_ref) not in source_formula_ids:
                        unresolved.append(
                            f"{row_key}: unresolved fixture formula_ref={formula_ref!r}"
                        )
                classify_reference("FORMULA", row.get("formula_ids"), row_key)
                classify_reference("QKU", row.get("qku_id"), row_key)
            if cohort == "PR162E" and not owner_projection:
                selection = _source_selection_tuple(
                    row,
                    formula_field="formula_refs",
                    algorithm_field="algorithm_refs",
                    parameter_field="parameter_stack_refs",
                )
                owner_retained_selection_tuples.add(selection)
                expected_formula_targets = source_name_targets.get(
                    selection[0][0], set()
                )
                expected_algorithm_targets = source_name_targets.get(
                    selection[1][0], set()
                )
                classify_reference(
                    "FORMULA",
                    row.get("formula_refs"),
                    row_key,
                    expected_targets=set(expected_formula_targets),
                )
                classify_reference(
                    "ALGORITHM",
                    row.get("algorithm_refs"),
                    row_key,
                    expected_targets=set(expected_algorithm_targets),
                )
                for qku_id in _source_reference_values(row.get("qku_refs")):
                    owner_retained_selection_qkus.add(qku_id)
                    owner_retained_selection_qku_cohorts[qku_id].add(cohort)
                source_scoped_selection_counts[
                    "OWNER_RETAINED_COASSOCIATION_REQUIRES_DETERMINISTIC_SELECTION_POLICY"
                ] += len(_source_reference_values(row.get("qku_refs")))
            if cohort == "PR162B":
                if role == "SEMANTIC_ROOT":
                    classify_reference("FORMULA", row.get("formula_refs"), row_key)
                    classify_reference(
                        "QKU",
                        row.get("qku_refs"),
                        row_key,
                        expected_targets={target} if target else set(),
                    )
                if role == "SEMANTIC_ROOT" and target:
                    require_qku_role_association(
                        {target}, row.get("qku_refs"), row_key, "PR162B"
                    )
                    require_status_explain_qku_association(
                        target, row.get("qku_refs"), row_key
                    )
            if (
                cohort in {"QUANTUM_559", "POSITIVE_EVIDENCE_150"}
                and not owner_projection
            ):
                selection = _source_selection_tuple(
                    row,
                    formula_field="formula_id",
                    algorithm_field="algorithm_id",
                    parameter_field="parameter_stack_id",
                )
                owner_retained_selection_tuples.add(selection)
                expected_formula_targets = source_name_targets.get(selection[0][0], set())
                expected_algorithm_targets = source_name_targets.get(selection[1][0], set())
                classify_reference(
                    "FORMULA",
                    row.get("formula_id"),
                    row_key,
                    expected_targets=set(expected_formula_targets),
                )
                classify_reference(
                    "ALGORITHM",
                    row.get("algorithm_id"),
                    row_key,
                    expected_targets=set(expected_algorithm_targets),
                )
                for qku_id in _source_reference_values(row.get("qku_id")):
                    owner_retained_selection_qkus.add(qku_id)
                    owner_retained_selection_qku_cohorts[qku_id].add(cohort)
                source_scoped_selection_counts[
                    "OWNER_RETAINED_COASSOCIATION_REQUIRES_DETERMINISTIC_SELECTION_POLICY"
                ] += len(_source_reference_values(row.get("qku_id")))
            if cohort == "VALUE_GAPS_2852":
                classify_reference(
                    "QKU",
                    row.get("qku_id"),
                    row_key,
                    permitted_target_prefix="QTT.COMP.RP5C.",
                    permitted_component_kind="QKU_SELECTION_POLICY",
                )
            _ = target  # target is deliberately transient; no row ledger is persisted.

        if cohort == "RP5D" and role in {"CONTEXT", "PROVENANCE_MAPPING"}:
            expected_reference_kinds = {"FORMULA": 824, "QKU": 9_791}
            expected_absences = {
                "FORMULA_REF_NOT_PRESENT": 9_365,
                "QKU_REF_NOT_PRESENT": 398,
            }
            if dict(reference_kind_counts) != expected_reference_kinds:
                unresolved.append(
                    "RP5D computation-reference denominator drift: "
                    f"{dict(reference_kind_counts)} != {expected_reference_kinds}"
                )
            if dict(resolved_reference_kind_counts) != expected_reference_kinds:
                unresolved.append(
                    "RP5D resolved-reference denominator drift: "
                    f"{dict(resolved_reference_kind_counts)} != "
                    f"{expected_reference_kinds}"
                )
            if dict(absence_disposition_counts) != expected_absences:
                unresolved.append(
                    "RP5D absence-disposition denominator drift: "
                    f"{dict(absence_disposition_counts)} != {expected_absences}"
                )
            expected_context = (
                {"REQUIRED_FORMULA_TO_PNL_ADAPTER_CONTRACT": 10_189}
                if path.endswith("rp5d_comp_materialization.jsonl")
                else {}
            )
            if dict(non_computation_context_counts) != expected_context:
                unresolved.append(
                    "RP5D non-computation context denominator drift: "
                    f"{dict(non_computation_context_counts)} != {expected_context}"
                )

        if unresolved:
            cohort_unresolved[cohort].extend(unresolved)
        cohort_counts[cohort].update(dispositions)
        cohort_rows[cohort] += len(rows)
        artifact_reports.append(
            {
                "artifact": path,
                "role": role,
                "key_field": key_field,
                "declared_rows": metadata["declared_rows"],
                "actual_rows_read": metadata["actual_rows_read"],
                "classified_rows": sum(dispositions.values()),
                "preview_rows_ignored": metadata["preview_rows_ignored"],
                "manifest_count_used_as_value_consumption": False,
                "physical_files_read": metadata["physical_files_read"],
                "disposition_counts": dict(sorted(dispositions.items())),
                "computation_reference_occurrences": reference_occurrences,
                "resolved_computation_reference_occurrences": (
                    resolved_reference_occurrences
                ),
                "computation_reference_kind_counts": dict(
                    sorted(reference_kind_counts.items())
                ),
                "resolved_computation_reference_kind_counts": dict(
                    sorted(resolved_reference_kind_counts.items())
                ),
                "absence_disposition_counts": dict(
                    sorted(absence_disposition_counts.items())
                ),
                "non_computation_context_disposition_counts": dict(
                    sorted(non_computation_context_counts.items())
                ),
                "source_scoped_selection_disposition_counts": dict(
                    sorted(source_scoped_selection_counts.items())
                ),
                "semantic_anchor_fields": semantic_anchor_fields,
                "projection_inclusion_basis": (
                    "SUBSTANTIVE_SEMANTIC_ANCHOR_FIELDS"
                    if semantic_anchor_fields
                    else "TRANSITIVELY_VALUE_REFERENCED_OWNER_CONTEXT"
                    if owner_projection
                    else "CANONICAL_SOURCE_ROOT_OR_DECLARED_COHORT"
                ),
                "projection_semantic_or_readiness_authority": False,
                "owner_retained_source_local_reference_blocker_count": (
                    owner_retained_source_local_reference_blocker_count
                ),
                "owner_retained_source_local_reference_exact_action": (
                    "DIRECT_TYPED_SEMANTIC_EQUIVALENCE_OR_DISTINCTNESS_PROOF_REQUIRED"
                    if owner_retained_source_local_reference_blocker_count
                    else None
                ),
                "semantic_classification_unresolved_count": 0,
                "semantic_promotion_blocker_count": (
                    len(rows) if role == "DISCOVERY" else 0
                ),
                "semantic_classification_exact_action": (
                    "DIRECT_TYPED_SEMANTIC_EQUIVALENCE_OR_DISTINCTNESS_PROOF_REQUIRED"
                    if role == "DISCOVERY"
                    else None
                ),
                "unresolved_count": len(unresolved),
            }
        )
        deadline.check(f"source closure {cohort}")

    if (
        candidate_packet_source_alternative_count
        != EXPECTED_CANDIDATE_PACKET_SOURCE_ALTERNATIVES
        or len(candidate_packet_qku_targets)
        != EXPECTED_CANDIDATE_PACKET_SOURCE_ALTERNATIVES
    ):
        raise BuildError(
            "CandidatePacket source-scoped alternative denominator drift: "
            f"occurrences={candidate_packet_source_alternative_count}, "
            f"unique_qkus={len(candidate_packet_qku_targets)}"
        )
    if candidate_packet_known_conflict_count != EXPECTED_CANDIDATE_PACKET_KNOWN_CONFLICTS:
        raise BuildError(
            "CandidatePacket known conflict denominator drift: "
            f"{candidate_packet_known_conflict_count} != "
            f"{EXPECTED_CANDIDATE_PACKET_KNOWN_CONFLICTS}"
        )
    candidate_runtime_root_leaks = sum(
        target in qku_targets.get(qku_id, set())
        for qku_id, target in candidate_packet_qku_targets.items()
    )
    if candidate_runtime_root_leaks:
        raise BuildError(
            "CandidatePacket source-scoped alternatives leaked into runtime roots: "
            f"{candidate_runtime_root_leaks}"
        )
    if source_selection_tuple_targets:
        raise BuildError(
            "source selection co-association records remain in canonical registry: "
            f"{len(source_selection_tuple_targets)}"
        )
    if (
        len(owner_retained_selection_tuples) != EXPECTED_SOURCE_SELECTION_TUPLES
        or len(owner_retained_selection_qkus) != EXPECTED_SOURCE_SELECTION_QKUS
    ):
        raise BuildError(
            "owner-retained source selection context denominator drift: "
            f"tuples={len(owner_retained_selection_tuples)}, "
            f"qkus={len(owner_retained_selection_qkus)}"
        )
    owner_selection_cross_cohort_qkus = sum(
        "POSITIVE_EVIDENCE_150" in cohorts and len(cohorts) > 1
        for cohorts in owner_retained_selection_qku_cohorts.values()
    )
    if owner_selection_cross_cohort_qkus != EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS:
        raise BuildError(
            "owner-retained cross-cohort selection context drift: "
            f"{owner_selection_cross_cohort_qkus} != "
            f"{EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS}"
        )
    if (
        agent_reachable_reference_occurrence_count
        != EXPECTED_AGENT_REACHABLE_REFERENCE_OCCURRENCES
        or len(agent_reachable_selector_keys)
        != EXPECTED_AGENT_REACHABLE_SELECTOR_KEYS
    ):
        raise BuildError(
            "agent-reachable status/explain selector denominator drift: "
            f"references={agent_reachable_reference_occurrence_count}, "
            f"selector_keys={len(agent_reachable_selector_keys)}"
        )
    if (
        gfp_discovery_blocked_promotion_count
        != EXPECTED_GFP_DISCOVERY_UNRESOLVED_ROWS
        or gfp_discovery_implemented_context_count != 19_393
        or gfp_discovery_input_gap_context_count != 722
    ):
        raise BuildError(
            "GFP owner-retained discovery denominator drift: "
            f"blocked={gfp_discovery_blocked_promotion_count}, "
            f"implemented_context={gfp_discovery_implemented_context_count}, "
            f"input_gap_context={gfp_discovery_input_gap_context_count}"
        )
    if (
        gfp_discovery_exact_expression_match_count != 0
        or gfp_discovery_expression_containment_match_count
        != EXPECTED_GFP_DISCOVERY_TEXTUAL_CONTAINMENT_HINT_ROWS
    ):
        raise BuildError(
            "GFP discovery textual search-hint denominator drift: "
            f"exact={gfp_discovery_exact_expression_match_count}, "
            f"containment={gfp_discovery_expression_containment_match_count}"
        )

    all_unresolved = [
        f"{cohort}::{detail}"
        for cohort in sorted(cohort_unresolved)
        for detail in sorted(set(cohort_unresolved[cohort]))
    ]
    if all_unresolved:
        raise BuildError(
            "source universe closure is incomplete: " + "; ".join(all_unresolved[:25])
        )
    artifact_by_cohort: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for artifact_report, spec in zip(artifact_reports, SOURCE_CLOSURE_ARTIFACTS):
        artifact_by_cohort[str(spec["cohort"])].append(artifact_report)

    def aggregate_counter(
        reports: Sequence[Mapping[str, Any]], field: str
    ) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for report in reports:
            counter.update(
                {
                    str(key): int(value)
                    for key, value in report.get(field, {}).items()
                }
            )
        return dict(sorted(counter.items()))

    cohort_reports = [
        {
            "cohort": cohort,
            "physical_rows_read_and_classified": cohort_rows[cohort],
            "disposition_counts": dict(sorted(cohort_counts[cohort].items())),
            "unresolved_count": 0,
            "semantic_promotion_blocker_count": (
                EXPECTED_GFP_DISCOVERY_UNRESOLVED_BY_COHORT.get(cohort, 0)
            ),
            "semantic_classification_exact_action": (
                "DIRECT_TYPED_SEMANTIC_EQUIVALENCE_OR_DISTINCTNESS_PROOF_REQUIRED"
                if cohort in EXPECTED_GFP_DISCOVERY_UNRESOLVED_BY_COHORT
                else None
            ),
            "computation_reference_occurrence_count": sum(
                int(item["computation_reference_occurrences"])
                for item in artifact_by_cohort[cohort]
            ),
            "resolved_computation_reference_occurrence_count": sum(
                int(item["resolved_computation_reference_occurrences"])
                for item in artifact_by_cohort[cohort]
            ),
            "computation_reference_kind_counts": aggregate_counter(
                artifact_by_cohort[cohort], "computation_reference_kind_counts"
            ),
            "resolved_computation_reference_kind_counts": aggregate_counter(
                artifact_by_cohort[cohort],
                "resolved_computation_reference_kind_counts",
            ),
            "absence_disposition_counts": aggregate_counter(
                artifact_by_cohort[cohort], "absence_disposition_counts"
            ),
            "non_computation_context_disposition_counts": aggregate_counter(
                artifact_by_cohort[cohort],
                "non_computation_context_disposition_counts",
            ),
            "source_scoped_selection_disposition_counts": aggregate_counter(
                artifact_by_cohort[cohort],
                "source_scoped_selection_disposition_counts",
            ),
        }
        for cohort in sorted(cohort_rows)
    ]
    total_reference_occurrences = sum(
        int(item["computation_reference_occurrences"])
        for item in artifact_reports
    )
    total_resolved_reference_occurrences = sum(
        int(item["resolved_computation_reference_occurrences"])
        for item in artifact_reports
    )
    if (
        total_reference_occurrences
        != total_resolved_reference_occurrences
    ):
        raise BuildError(
            "complete computation-reference denominator drift: "
            f"resolved={total_resolved_reference_occurrences}/"
            f"{total_reference_occurrences}"
        )
    manifest_owner_split = _source_manifest_split(repo_root)
    if any(item["unclassified_manifest_entries"] for item in manifest_owner_split):
        raise BuildError("source owner manifest split has unclassified entries")
    r1_current_equivalent = [
        spec
        for spec in SOURCE_CLOSURE_ARTIFACTS
        if str(spec["cohort"])
        in {"RP5D_R1", "RP5D_R1_OWNER_CONTEXT", "FIXTURE_5"}
    ]
    if (
        len(r1_current_equivalent),
        sum(int(spec["expected"]) for spec in r1_current_equivalent),
    ) != (29, 893):
        raise BuildError(
            "RP5D-R1 current-equivalent closure must remain 27/873 owner "
            "projections + calc_smoke 1/5 + source_req 1/15 = 29/893"
        )
    return {
        "protocol": "ROW_LEVEL_VALUE_CONSUMPTION_WITH_DECLARED_SHARD_LOADING",
        "artifacts": artifact_reports,
        "cohorts": cohort_reports,
        "manifest_owner_split": manifest_owner_split,
        "manifest_owner_unclassified_entry_count": 0,
        "current_equivalent_family_reconciliation": {
            "RP5D_R1": {
                "owner_projection_artifacts": 27,
                "owner_projection_rows": 873,
                "fixture_artifact": (
                    "docs/master_plan/generated/pr168_rp5d_r1/calc_smoke.jsonl"
                ),
                "fixture_artifacts": 1,
                "fixture_rows": 5,
                "owner_context_artifact": (
                    "docs/master_plan/generated/pr168_rp5d_r1/source_req.jsonl"
                ),
                "owner_context_artifacts": 1,
                "owner_context_rows": 15,
                "total_current_equivalent_artifacts": 29,
                "total_current_equivalent_rows": 893,
                "double_counted_artifact_count": 0,
            }
        },
        "artifact_count": len(artifact_reports),
        "physical_rows_read": sum(item["actual_rows_read"] for item in artifact_reports),
        "classified_physical_rows": sum(item["classified_rows"] for item in artifact_reports),
        "unresolved_source_occurrence_count": 0,
        "source_occurrence_semantic_promotion_blocker_count": (
            gfp_discovery_blocked_promotion_count
        ),
        "unresolved_source_local_runtime_computation_reference_count": 0,
        "computation_reference_occurrence_count": total_reference_occurrences,
        "resolved_computation_reference_occurrence_count": (
            total_resolved_reference_occurrences
        ),
        "computation_reference_kind_counts": aggregate_counter(
            artifact_reports, "computation_reference_kind_counts"
        ),
        "resolved_computation_reference_kind_counts": aggregate_counter(
            artifact_reports, "resolved_computation_reference_kind_counts"
        ),
        "absence_disposition_counts": aggregate_counter(
            artifact_reports, "absence_disposition_counts"
        ),
        "non_computation_context_disposition_counts": aggregate_counter(
            artifact_reports, "non_computation_context_disposition_counts"
        ),
        "source_scoped_selection_disposition_counts": aggregate_counter(
            artifact_reports, "source_scoped_selection_disposition_counts"
        ),
        "context_or_evidence_row_admitted_as_computation_count": 0,
        "manifest_count_only_consumption_count": 0,
        "candidate_packet_source_scoped_alternative_count": (
            candidate_packet_source_alternative_count
        ),
        "candidate_packet_known_cross_owner_conflict_count": (
            candidate_packet_known_conflict_count
        ),
        "candidate_packet_runtime_root_exclusion_count": len(
            candidate_packet_qku_targets
        ),
        "source_selection_tuple_record_count": 0,
        "owner_retained_source_selection_tuple_count": len(
            owner_retained_selection_tuples
        ),
        "owner_retained_source_selection_unique_qku_count": len(
            owner_retained_selection_qkus
        ),
        "source_selection_unique_qku_count": 0,
        "source_selection_cross_cohort_qku_count": (
            owner_selection_cross_cohort_qkus
        ),
        "agent_reachable_status_explain_reference_occurrence_count": (
            agent_reachable_reference_occurrence_count
        ),
        "agent_reachable_status_explain_selector_key_count": len(
            agent_reachable_selector_keys
        ),
        "agent_reachable_computation_reference_resolution_coverage": (
            "100%_OF_EXPLICIT_CURRENT_PR165_D2_STATUS_EXPLAIN_SUBSET"
        ),
        "gfp_discovery_rows_semantic_classification_unresolved": 0,
        "gfp_discovery_rows_with_exact_promotion_blocker": (
            gfp_discovery_blocked_promotion_count
        ),
        "gfp_discovery_implemented_context_rows": (
            gfp_discovery_implemented_context_count
        ),
        "gfp_discovery_input_gap_context_rows": (
            gfp_discovery_input_gap_context_count
        ),
        "gfp_discovery_proof_backed_canonical_mapping_count": 0,
        "gfp_discovery_canonical_admission_count": 0,
        "gfp_discovery_category_counts": dict(
            sorted(gfp_discovery_category_counts.items())
        ),
        "gfp_discovery_exact_selected_expression_match_count": (
            gfp_discovery_exact_expression_match_count
        ),
        "gfp_discovery_selected_expression_containment_match_count": (
            gfp_discovery_expression_containment_match_count
        ),
        "gfp_discovery_textual_containment_is_semantic_proof": False,
        "full_lossy_gfp_catalog_row_disposition_closure": "PROVEN",
        "full_lossy_gfp_catalog_direct_semantic_equivalence": "UNPROVEN_BLOCKED",
        "overlap_policy": (
            "COHORTS_ARE_REPORTED_SEPARATELY_AND_NEVER_SUMMED_AS_AN_ADDITIVE_UNIVERSE"
        ),
    }


def _source_closure() -> list[dict[str, Any]]:
    return [
        {
            "semantic_domain": "RP5C immutable identities, QKU roles, duplicate-member custody, lineage",
            "current_owner": "RP5C_IMMUTABLE_BASELINE",
            "accepted_sources": [
                RP5C_DEDUPE.as_posix(),
                RP5C_LINEAGE.as_posix(),
                *(path.as_posix() for path in RP5C_LIBRARIES),
            ],
            "fields_consumed": [
                "canonical_identity_row_id",
                "identity_row_id",
                "duplicate_group_id",
                "duplicate_member_identity_row_ids",
                "identity_type",
                "qku_id",
                "formula_id",
                "formula_variant_id",
                "formula_expression_ref",
                "plugin_ref",
                "source_artifact_ref",
                "source_artifact_row_id",
                "source_line_or_json_path",
                "market_family",
                "ontology_category",
                "stage1_seed_inclusion_flag",
                "stage1_dormant_future_market_flag",
            ],
            "record_destination": "ComputationRecordV1 provenance/relations/uses/bindings",
            "use": "BUILD_TIME_ONLY",
            "forbidden_mutation": (
                "RP5C source rows remain immutable; ordinal source IDs are evidence, "
                "the structured six-field custody key preserves CONTROL1 continuity, "
                "and neither is semantic-equivalence or runtime authority"
            ),
            "conflict_resolution": "baseline provenance, not continuing write or runtime authority",
        },
        {
            "semantic_domain": "PR162D formulas, deterministic algorithms, quantum shape callables",
            "current_owner": "PR162D_R2A_REAL_FORMULATIONS",
            "accepted_sources": [
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/formula_seed_library.py",
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/algorithm_seed_library.py",
                "src/qtt/stage1_prediction_markets/pr162d_r2a_real_formulations/quantum_seed_library.py",
            ],
            "fields_consumed": [
                "identity",
                "expression_or_procedure_or_objective",
                "explicit_callable_ref",
                "typed_port_names",
                "unit_hints",
                "family_and_variant",
                "latency_class",
                "fixture_reference",
            ],
            "record_destination": "ComputationRecordV1 definition/uses/fixture binding/provenance",
            "use": "BUILD_TIME_REGISTRATION_AND_RUNTIME_ALLOWLIST_REFERENCE",
            "forbidden_mutation": "no caller-selected module path and no inherited live authority",
            "conflict_resolution": "source-derived fixtures are invocation evidence, not independent oracles",
        },
        {
            "semantic_domain": "owner-supplied 213 mathematical and procedural requests",
            "current_owner": "OWNER_REQUIREMENT_INTAKE",
            "accepted_sources": [
                "OWNER_SUPPLIED_213_REQUIREMENT_INVENTORY",
                "MASTER_PLAN_OWNER_REQUIREMENT_DOCTRINE",
                "CONTROL1_PROMPT_SECTION_12",
            ],
            "fields_consumed": ["card_id", "family", "requested_semantic_name"],
            "record_destination": "provisional ComputationRecordV1 owner_requirement_crosswalk",
            "use": "BUILD_TIME_ONLY_UNTIL_SPECIFICATION_CLOSES",
            "forbidden_mutation": "no restored implementation, callable, alias, PASS, or route claim",
            "conflict_resolution": "reverted/closed PR is negative evidence and inventory custody only",
        },
        {
            "semantic_domain": "PR165-D2 agent roster and duties",
            "current_owner": "PR165_D2_AGENT_ROSTER",
            "accepted_sources": [PR165_D2_ROSTER.as_posix()],
            "fields_consumed": ["agent_id", "agent_family", "agent_role", "authority_boundary"],
            "record_destination": "bindings.agent_access_policy",
            "use": "BUILD_TIME_POLICY_DERIVATION",
            "forbidden_mutation": "no second roster and no permission expansion",
            "conflict_resolution": "classification policy, never per-formula routes",
        },
        {
            "semantic_domain": (
                "MAP3, RP5D/R1/RP5E, PR162B/PR162D/PR162E/PR162E-Q, GFP, "
                "fixture/evidence/gap/CandidatePacket, and master/post-RP5C candidate closure"
            ),
            "current_owner": "EXISTING_HISTORICAL_AND_CURRENT_SOURCE_OWNERS",
            "accepted_sources": [
                spec["path"] for spec in SOURCE_CLOSURE_ARTIFACTS
            ],
            "fields_consumed": [
                "every declared physical row",
                "stable row/logical keys",
                "mathematical/procedural semantics",
                "callable/formulation references",
                "QKU and agent/context references",
                "selected/rejected source dispositions",
                "declared shard ownership and counts",
            ],
            "record_destination": (
                "proof-backed canonical mapping, provisional source-semantic record, "
                "or transient context/evidence/source-owner disposition"
            ),
            "use": "ROW_LEVEL_BUILD_TIME_CLASSIFICATION_ONLY",
            "forbidden_mutation": "no duplicate registry, copied graph, or unproven equivalence",
            "conflict_resolution": (
                "MAP3/PR162B/GFP definitions remain provisional; context/evidence rows "
                "remain with their owners and never become formula records"
            ),
        },
    ]


_SCALE_PROBE_SEED = 169_10_000
_SCALE_ROOT_ID = "QTT.COMP.SCALE.SELECTED.RELATIVE_SPREAD"
_SCALE_STACK_IDENTITY_REF = "qtt.computation_control.native:stack_identity"


def _scale_probe_requirement(
    target: str, producer: str, consumer: str, role: str
) -> dict[str, Any]:
    return {
        "required_component_id_or_source_selector": target,
        "required_semantic_version_constraint": "==1.0",
        "requirement_role": role,
        "required_or_optional": "REQUIRED",
        "producer_output_name": producer,
        "consumer_input_name": consumer,
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST_INPUT_LOCK",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }


def _scale_probe_fixture_contract(
    component_id: str, definition: Mapping[str, Any]
) -> dict[str, Any]:
    """Create an explicit temporary contract used only inside the scale probe."""

    requirements_by_input = {
        str(requirement["consumer_input_name"]): requirement
        for requirement in definition.get("requirements", ())
        if isinstance(requirement, Mapping)
        and str(requirement.get("required_or_optional", "REQUIRED")).upper()
        != "OPTIONAL"
        and requirement.get("consumer_input_name")
    }
    ports: list[dict[str, Any]] = []
    for schema in definition.get("input_schema", ()):
        if not isinstance(schema, Mapping) or not schema.get("name"):
            continue
        name = str(schema["name"])
        port: dict[str, Any] = {
            "input_name": name,
            "declared_type": str(schema.get("type", "")),
            "unit_or_basis": str(
                schema.get("unit_or_basis")
                or schema.get("unit")
                or schema.get("basis")
                or ""
            ),
            "value": "1",
        }
        requirement = requirements_by_input.get(name)
        if requirement is None:
            port["ownership"] = "DIRECT_TYPED_REQUEST_INPUT"
        else:
            port.update(
                {
                    "ownership": "CANONICAL_REQUIREMENT_OUTPUT",
                    "required_component_id": requirement[
                        "required_component_id_or_source_selector"
                    ],
                    "producer_output_name": requirement[
                        "producer_output_name"
                    ],
                }
            )
        ports.append(port)
    return {
        "fixture_ref": "CONTROL1_FIXED_SEED_SCALE_PROBE",
        "source_resolution_state": "TEMPORARY_SCALE_PROBE_EXACTLY_RESOLVED",
        "source_artifact_ref": "CONTROL1_FIXED_SEED_SCALE_PROBE",
        "source_row_ref": component_id,
        "ports": ports,
    }


def _scale_probe_record(
    component_id: str,
    callable_ref: str,
    inputs: Sequence[tuple[str, str]],
    outputs: Sequence[tuple[str, str]],
    *,
    requirements: Sequence[Mapping[str, Any]] = (),
    binding_id: str | None = None,
) -> dict[str, Any]:
    suffix = component_id.rsplit(".", 1)[-1]
    implementation_version = "scale-native-v1"
    definition = _definition(
        display_name=suffix,
        description="Bounded temporary CONTROL1 structural scale computation.",
        component_kind="DETERMINISTIC_TRANSFORM",
        complete_definition=f"allowlisted deterministic scale procedure {suffix}",
        inputs=[
            {"name": name, "type": "DECIMAL", "unit_or_basis": unit, "required": True}
            for name, unit in inputs
        ],
        outputs=[
            {"name": name, "type": "DECIMAL", "unit_or_basis": unit, "required": True}
            for name, unit in outputs
        ],
        units={name: unit for name, unit in [*inputs, *outputs]},
        requirements=requirements,
        latency_class="PRETRADE_BOUNDED",
        implementation_versions=[
            {
                "implementation_version": implementation_version,
                "callable_or_solver_ref": callable_ref,
                "code_owner": "CONTROL1_PRIVATE_RUNTIME",
                "supported_platforms": ["WINDOWS", "LINUX"],
                "pinned_dependencies": ["PYTHON_STANDARD_LIBRARY"],
                "determinism_seed_policy": "DETERMINISTIC_NO_SEED",
                "precision": (
                    "DECIMAL_INPUT_BOUNDARY; ARITHMETIC_PRECISION_34; "
                    "ROUND_HALF_EVEN; NO_ADDITIONAL_OUTPUT_QUANTIZATION"
                ),
                "latency_class": "PRETRADE_BOUNDED",
                "security_state": "CONTROL1_NATIVE_ALLOWLIST",
                "memoizable": True,
                "memoizable_proof_basis": "PURE_STATELESS_NATIVE_FUNCTION",
                "fallback": None,
            }
        ],
        oracle_refs=[
            "tests/pr169_qku_comp_control1/test_control1.py::"
            "test_fixed_seed_structural_scale_probe_real_layout_resolve_compute"
        ],
    )
    definition.update(
        {
            "assumptions": ["TEMPORARY_FIXED_SEED_VALIDATION_ONLY"],
            "domain_and_boundary_behavior": {"invalid": "FAIL_CLOSED"},
            "state_and_time_semantics": {
                "state": "STATELESS",
                "time": "SAME_REQUEST",
            },
            "output_accounting_class": "NON_ACCOUNTING_VALIDATION_FIXTURE",
            "missing_stale_nonfinite_behavior": "FAIL_CLOSED",
            "precision_and_rounding": {
                "numeric_boundary": "PYTHON_DECIMAL_FROM_TEXT_OR_INTEGER_ONLY",
                "arithmetic_precision_significant_digits": 34,
                "rounding": "ROUND_HALF_EVEN",
                "output_quantization": "NONE_ADDITIONAL",
            },
            "parameter_schema_and_default_provenance": {
                "parameters": [],
                "default_provenance": "CONTROL1_FIXED_SEED_SCALE_PROBE",
            },
            "risk_materiality": {
                "economic_materiality": "TEST_ONLY",
                "complexity": "BOUNDED_DETERMINISTIC",
                "data_dependency": "CALLER_TYPED_FIXTURE",
                "latency_sensitivity": "STRUCTURAL_PROBE_ONLY",
                "external_provider_dependency": False,
                "quantum_backend_dependency": False,
                "independent_validation_strength_required": "GROUPED_TEST",
                "monitoring_revalidation_cadence": "EACH_VALIDATOR_RUN",
            },
            "failure_domain_tags": ["VALIDATION_ONLY"],
            "classical_fallback": {
                "not_applicable": True,
                "proof_ref": "TEMPORARY_SCALE_COMPONENT_FAILS_CLOSED",
            },
        }
    )
    binding = _binding(
        component_id,
        definition=definition,
        binding_id=binding_id or f"BINDING.SCALE.{suffix}",
        agent_ids=(),
        implementation_version=implementation_version,
        exact_action=None,
        fixture_ref="CONTROL1_FIXED_SEED_SCALE_PROBE",
        fixture_contract=_scale_probe_fixture_contract(component_id, definition),
        requirements_ready=True,
        oracle_ready=True,
    )
    if binding["readiness"]["specification"] != "PASS":
        raise BuildError(
            f"scale probe specification unexpectedly incomplete: {component_id}: "
            f"{binding['exact_resolution_action_or_null']}"
        )
    binding.update(
        {
            "market": "SYNTHETIC_SCALE",
            "venue": "LOCAL_FIXTURE",
            "context_selector": {
                "market": "SYNTHETIC_SCALE",
                "venue": "LOCAL_FIXTURE",
            },
            "supported_modes": ["FIXTURE_NONLIVE"],
            "mode_state": {
                "FIXTURE_NONLIVE": {
                    "evidence": "FIXTURE",
                    "authorization": "NOT_ELIGIBLE",
                }
            },
            "activation_state": "INACTIVE_NONLIVE",
            "downstream_consumer_classes": ["CONTROL1_SCALE_VALIDATION"],
            "producer_owner": "CONTROL1_CENTRAL_BUILDER_SCALE_PROBE",
            "validator_refs": [
                "tools/validate_pr169_qku_comp_control1.py",
                "tests/pr169_qku_comp_control1/test_control1.py",
            ],
        }
    )
    return {
        "canonical_component_id": component_id,
        "semantic_version": "1.0",
        "record_state": "CANONICAL_ACCEPTED",
        "origin_cohorts": ["BUILDER_TEMPORARY_SCALE_PROBE"],
        "definition": definition,
        "uses": {
            "decision_roles": ["INTERNAL_SUPPORT"],
            "decision_outputs": [name for name, _ in outputs],
            "market_family_tags": ["SYNTHETIC_SCALE"],
            "qku_role_bindings": [
                {
                    "qku_id": f"QKU.SCALE.{suffix}",
                    "role_or_decision_stage": "INTERNAL_SUPPORT",
                    "market_family": "SYNTHETIC_SCALE",
                    "stack_root_or_direct_component": component_id,
                    "selection_rule_if_container": None,
                    "agent_policy_tags": ["VALIDATOR_ONLY"],
                    "source_refs": ["CONTROL1_FIXED_SEED_SCALE_PROBE"],
                }
            ],
            "consumer_class_tags": ["CONTROL1_SCALE_VALIDATION"],
        },
        "bindings": [binding],
        "provenance": [
            {
                "source_artifact_ref": "CONTROL1_FIXED_SEED_SCALE_PROBE",
                "source_row_ref": component_id,
                "source_local_identity_or_name": suffix,
                "source_fields_consumed": ["fixed_seed_structural_probe"],
                "source_relation": "TEMPORARY_VALIDATION_ONLY",
                "canonical_target_ref": component_id,
                "proof_refs": [
                    "tests/pr169_qku_comp_control1/test_control1.py::"
                    "test_fixed_seed_structural_scale_probe_real_layout_resolve_compute"
                ],
            }
        ],
        "relations": [],
        "governance": {
            "producer_owner": "CONTROL1_CENTRAL_BUILDER_SCALE_PROBE",
            "validator_refs": [
                "tools/validate_pr169_qku_comp_control1.py",
                "tests/pr169_qku_comp_control1/test_control1.py",
            ],
            "reviewer_or_challenger_owner": "CONTROL1_GROUPED_TEST_ORACLE",
            "change_authority": "TEMPORARY_VALIDATION_ONLY",
        },
    }


def _scale_probe_records(record_count: int) -> list[dict[str, Any]]:
    if record_count < 3:
        raise BuildError("scale probe requires at least three records")
    mid_id = "QTT.COMP.SCALE.SELECTED.MID_PRICE"
    spread_id = "QTT.COMP.SCALE.SELECTED.SPREAD"
    records = [
        _scale_probe_record(
            mid_id,
            "qtt.computation_control.native:decimal_mid_price",
            (("best_bid", "PRICE"), ("best_ask", "PRICE")),
            (("mid_price", "PRICE"),),
        ),
        _scale_probe_record(
            spread_id,
            "qtt.computation_control.native:decimal_spread",
            (("best_bid", "PRICE"), ("best_ask", "PRICE")),
            (("spread", "PRICE_DELTA"),),
        ),
        _scale_probe_record(
            _SCALE_ROOT_ID,
            "qtt.computation_control.native:decimal_relative_spread",
            (("spread", "PRICE_DELTA"), ("mid_price", "PRICE")),
            (("relative_spread", "RATIO"),),
            requirements=(
                _scale_probe_requirement(
                    mid_id, "mid_price", "mid_price", "MID_PRICE_DENOMINATOR"
                ),
                _scale_probe_requirement(
                    spread_id, "spread", "spread", "ABSOLUTE_SPREAD_NUMERATOR"
                ),
            ),
        ),
    ]
    records.extend(
        _scale_probe_record(
            f"QTT.COMP.SCALE.UNRELATED.{index:08d}",
            _SCALE_STACK_IDENTITY_REF,
            (("result", "UNITLESS"),),
            (("result", "UNITLESS"),),
            binding_id=f"BINDING.SCALE.UNRELATED.{index:08d}",
        )
        for index in range(record_count - len(records))
    )
    random.Random(_SCALE_PROBE_SEED).shuffle(records)
    return records


def _run_scale_probe(
    record_count: int,
    *,
    _minimum_records: int = 10_000,
    _measurement_subset_records: int = 2_000,
    _sample_count: int = 25,
) -> dict[str, Any]:
    """Run the structural probe plus bounded local diagnostic measurements.

    The underscored controls exist only so the grouped test can exercise the
    complete measurement path quickly.  Production callers use the fixed
    10,000-row probe, a deterministic 2,000-row measurement subset, and 25
    samples.  Timings are observations from this process, never acceptance
    thresholds or canonical performance authority.
    """

    if record_count < 0:
        raise BuildError("scale_probe_records cannot be negative")
    if record_count == 0:
        return {
            "executed": False,
            "requested_records": 0,
            "exact_action": "RUN_WITH_SCALE_PROBE_RECORDS_AT_LEAST_10000_FOR_OPT_IN_PROBE",
            "test_ref": (
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_fixed_seed_structural_scale_probe_real_layout_resolve_compute"
            ),
        }
    if (
        _minimum_records < 3
        or _measurement_subset_records < 3
        or _sample_count < 1
    ):
        raise BuildError("invalid internal scale-probe measurement controls")
    if record_count < _minimum_records:
        raise BuildError(
            f"final structural scale probe requires at least {_minimum_records} records"
        )

    def elapsed_ms(started_ns: int) -> float:
        return round((time.perf_counter_ns() - started_ns) / 1_000_000.0, 6)

    def nearest_rank_ms(samples_ns: Sequence[int], percentile: int) -> float:
        if not samples_ns or percentile < 1 or percentile > 100:
            raise BuildError("invalid scale-probe percentile sample")
        ordered = sorted(int(value) for value in samples_ns)
        # Nearest-rank: rank = ceil(P / 100 * N), indexed from one.
        rank = max(1, (percentile * len(ordered) + 99) // 100)
        return round(ordered[rank - 1] / 1_000_000.0, 6)

    def measurement_summary(samples_ns: Sequence[int]) -> dict[str, Any]:
        return {
            "sample_count": len(samples_ns),
            "p50_ms": nearest_rank_ms(samples_ns, 50),
            "p95_ms": nearest_rank_ms(samples_ns, 95),
        }

    def probe_batch(
        batch_id: str, items: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any]:
        return {
            "batch_id": batch_id,
            "batch_origin": "BUILDER_TEMPORARY_SCALE_PROBE",
            "submitted_by": "CONTROL1_CENTRAL_BUILDER",
            "submission_time": "2026-07-14T00:00:00Z",
            "source_refs": ["CONTROL1_FIXED_SEED_SCALE_PROBE"],
            "source_classification": "OWNER_SUBMITTED",
            "intended_market_venue_modes": [],
            "items": [copy.deepcopy(dict(item)) for item in items],
            "requested_evidence_modes": ["FIXTURE"],
            "requested_promotion_ceiling": "STACK_READY",
        }

    materialization_started = time.perf_counter()
    records = _scale_probe_records(record_count)
    materialization_ms = round(
        (time.perf_counter() - materialization_started) * 1000.0, 3
    )
    control = _control_module()
    writer = getattr(control, "_write_registry_layout", None)
    loader = getattr(control, "_load_logical_registry", None)
    facade_class = getattr(control, "QKUComputationControlPlaneV1", None)
    compiler = getattr(control, "_compile_expansion_batch", None)
    build_snapshot = getattr(control, "_build_snapshot", None)
    apply_update = getattr(control, "_apply_registry_update", None)
    index_signature = getattr(control, "_index_signature", None)
    if (
        not callable(writer)
        or not callable(loader)
        or not isinstance(facade_class, type)
        or not callable(compiler)
        or not callable(build_snapshot)
        or not callable(apply_update)
        or not callable(index_signature)
    ):
        raise BuildError("control owner lacks structural scale-probe capabilities")
    measurement_matrix: dict[str, Any]
    with tempfile.TemporaryDirectory(prefix="qtt-control1-builder-scale-") as temporary:
        root = Path(temporary)
        single_root = root / "single"
        sharded_root = root / "sharded"
        layout_started = time.perf_counter()
        writer(records, single_root, force_layout="single")
        writer(records, sharded_root, force_layout="sharded")
        single_rows, single_layout = loader(single_root)
        sharded_rows, sharded_layout = loader(sharded_root)
        key = lambda row: (
            str(row["canonical_component_id"]),
            str(row["semantic_version"]),
        )
        if sorted(single_rows, key=key) != sorted(sharded_rows, key=key):
            raise BuildError("scale probe single/sharded logical rows differ")
        single = facade_class(single_root)
        sharded = facade_class(sharded_root)
        layout_ms = round((time.perf_counter() - layout_started) * 1000.0, 3)
        context = {
            "market": "SYNTHETIC_SCALE",
            "venue": "LOCAL_FIXTURE",
            "mode": "FIXTURE_NONLIVE",
            "input_units": {"best_bid": "PRICE", "best_ask": "PRICE"},
            "input_lineage": {
                "best_bid": "CONTROL1_FIXED_SEED_SCALE_PROBE",
                "best_ask": "CONTROL1_FIXED_SEED_SCALE_PROBE",
            },
        }
        inputs = {
            "best_bid": {
                "value": Decimal("0.40"),
                "unit": "PRICE",
                "lineage": "CONTROL1_FIXED_SEED_SCALE_PROBE",
            },
            "best_ask": {
                "value": Decimal("0.60"),
                "unit": "PRICE",
                "lineage": "CONTROL1_FIXED_SEED_SCALE_PROBE",
            },
        }
        original_open = Path.open

        def forbidden_open(*args: Any, **kwargs: Any) -> Any:
            raise BuildError("scale probe runtime reopened a physical registry file")

        Path.open = forbidden_open
        execution_started = time.perf_counter()
        try:
            plans = [plane.resolve(_SCALE_ROOT_ID, context) for plane in (single, sharded)]
            receipts = [
                plane.compute(_SCALE_ROOT_ID, inputs, context)
                for plane in (single, sharded)
            ]
        finally:
            Path.open = original_open
        execution_ms = round((time.perf_counter() - execution_started) * 1000.0, 3)
        expected_nodes = {
            "QTT.COMP.SCALE.SELECTED.MID_PRICE",
            "QTT.COMP.SCALE.SELECTED.SPREAD",
            _SCALE_ROOT_ID,
        }
        if any(
            {node.canonical_component_id for node in plan.topological_nodes}
            != expected_nodes
            for plan in plans
        ):
            raise BuildError("scale probe resolved an incorrect selected subgraph")
        if any(
            receipt.outputs != {"relative_spread": Decimal("0.4")}
            or receipt.nodes_executed != 3
            for receipt in receipts
        ):
            raise BuildError("scale probe compute result or execution breadth differs")
        stable_receipts = [
            (
                receipt.component_id,
                receipt.outputs,
                receipt.output_units,
                receipt.nodes_executed,
                tuple(
                    sorted(
                        row["component_id"]
                        for row in receipt.requirement_receipts
                    )
                ),
            )
            for receipt in receipts
        ]
        if stable_receipts[0] != stable_receipts[1]:
            raise BuildError("scale probe single/sharded receipts differ")
        for plane in (single, sharded):
            diagnostics = plane._diagnostics()
            if any(
                int(diagnostics.get(name, -1)) != expected
                for name, expected in {
                    "runtime_registry_file_reads_after_initialization": 0,
                    "per_request_full_registry_iterations": 0,
                    "unrelated_component_executions": 0,
                    "records_examined_last_request": 3,
                    "nodes_executed_last_request": 3,
                    "registry_rows": record_count,
                }.items()
            ):
                raise BuildError(f"scale probe diagnostics failed: {diagnostics!r}")
            if int(
                diagnostics.get("implementation_call_counts", {}).get(
                    _SCALE_STACK_IDENTITY_REF, 0
                )
            ):
                raise BuildError("scale probe executed an unrelated component")

        # The larger structural probe proves layout behavior.  The bounded
        # deterministic subset below observes compile/index/request costs
        # without turning local wall-clock behavior into an acceptance gate.
        measurement_count = min(record_count, _measurement_subset_records)
        measurement_records = sorted(records, key=key)[:measurement_count]
        measurement_ids = {
            str(row["canonical_component_id"]) for row in measurement_records
        }
        required_measurement_ids = {
            "QTT.COMP.SCALE.SELECTED.MID_PRICE",
            "QTT.COMP.SCALE.SELECTED.SPREAD",
            _SCALE_ROOT_ID,
        }
        if not required_measurement_ids.issubset(measurement_ids):
            raise BuildError("scale measurement subset omitted the selected stack")

        no_op_started = time.perf_counter_ns()
        no_op_records, no_op_delta, no_op_report = compiler(
            measurement_records,
            probe_batch("SCALE.MEASUREMENT.NO_OP", ()),
        )
        no_op_compile_ms = elapsed_ms(no_op_started)
        no_op_payload = no_op_delta.as_dict()
        delta_fields = (
            "added_component_ids",
            "changed_component_ids",
            "retired_component_ids",
            "added_binding_ids",
            "changed_binding_ids",
            "removed_binding_ids",
            "affected_dependent_ids",
            "affected_consumer_classes",
        )
        if (
            sorted(no_op_records, key=key) != measurement_records
            or any(no_op_payload.get(field) for field in delta_fields)
            or int(no_op_report.get("items_read", -1)) != 0
        ):
            raise BuildError("scale measurement no-op compile changed registry truth")

        update_target = next(
            row
            for row in measurement_records
            if ".UNRELATED." in str(row["canonical_component_id"])
        )
        update_component_id = str(update_target["canonical_component_id"])
        update_binding_id = str(update_target["bindings"][0]["binding_id"])
        updated_record = copy.deepcopy(update_target)
        updated_record["bindings"][0]["selected_parameter_policy"] = {
            **updated_record["bindings"][0]["selected_parameter_policy"],
            "policy_id": "PARAM.SCALE.MEASUREMENT.UPDATE",
            "version": "2.0",
            "default_provenance": "CONTROL1_FIXED_SEED_SCALE_PROBE",
        }
        binding_started = time.perf_counter_ns()
        binding_candidate, binding_delta, binding_report = compiler(
            measurement_records,
            probe_batch(
                "SCALE.MEASUREMENT.SINGLE_BINDING_UPDATE",
                ({"record": updated_record},),
            ),
        )
        binding_compile_ms = elapsed_ms(binding_started)
        if (
            tuple(binding_delta.changed_component_ids) != (update_component_id,)
            or tuple(binding_delta.changed_binding_ids)
            != (f"{update_component_id}::{update_binding_id}",)
            or binding_report.get("outcomes", [{}])[0].get("decision")
            != "EXISTING_ID_UPDATE"
        ):
            raise BuildError("scale measurement binding update was not incremental")

        new_component_id = "QTT.COMP.SCALE.MEASUREMENT.NEW.PROBABILITY_EDGE"
        new_record = _scale_probe_record(
            new_component_id,
            "qtt.computation_control.native:decimal_probability_edge",
            (
                ("p_model", "PROBABILITY"),
                ("implied_probability", "PROBABILITY"),
            ),
            (("probability_edge", "PROBABILITY_DELTA"),),
            binding_id="BINDING.SCALE.MEASUREMENT.NEW.PROBABILITY_EDGE",
        )
        new_started = time.perf_counter_ns()
        new_candidate, new_delta, new_report = compiler(
            measurement_records,
            probe_batch(
                "SCALE.MEASUREMENT.REPRESENTATIVE_NEW_RECORD",
                (
                    {
                        "record": new_record,
                        "equivalence_decision": "NO",
                        "nonidentical_relation": "DISTINCT",
                    },
                ),
            ),
        )
        new_record_compile_ms = elapsed_ms(new_started)
        if (
            tuple(new_delta.added_component_ids) != (new_component_id,)
            or len(new_candidate) != measurement_count + 1
            or new_report.get("outcomes", [{}])[0].get("decision") != "DISTINCT"
        ):
            raise BuildError("scale measurement new-record compile was not bounded")

        base_snapshot = build_snapshot(measurement_records, generation=1)
        incremental_started = time.perf_counter_ns()
        incremental_snapshot, incremental_stats = apply_update(
            base_snapshot,
            binding_delta,
            binding_candidate,
            verify_full_rebuild=False,
        )
        incremental_index_refresh_ms = elapsed_ms(incremental_started)
        full_started = time.perf_counter_ns()
        full_snapshot = build_snapshot(binding_candidate, generation=2)
        full_index_rebuild_ms = elapsed_ms(full_started)
        index_parity = index_signature(
            incremental_snapshot.indexes
        ) == index_signature(full_snapshot.indexes)
        if (
            not index_parity
            or incremental_stats.get("changed_index_component_ids")
            != [update_component_id]
        ):
            raise BuildError("scale measurement incremental/full index parity failed")

        measurement_plane = facade_class(records=measurement_records)
        one_node_context = {
            "market": "SYNTHETIC_SCALE",
            "venue": "LOCAL_FIXTURE",
            "mode": "FIXTURE_NONLIVE",
            "input_units": {"result": "UNITLESS"},
            "input_lineage": {"result": "CONTROL1_FIXED_SEED_SCALE_PROBE"},
        }
        one_node_inputs = {
            "result": {
                "value": Decimal("1"),
                "unit": "UNITLESS",
                "lineage": "CONTROL1_FIXED_SEED_SCALE_PROBE",
            }
        }
        resolve_samples: dict[str, list[int]] = {
            "one_node_zero_requirements": [],
            "three_nodes_two_requirements": [],
        }
        compute_samples: dict[str, list[int]] = {
            "one_node_zero_requirements": [],
            "three_nodes_two_requirements": [],
        }
        for _ in range(_sample_count):
            started = time.perf_counter_ns()
            one_plan = measurement_plane.resolve(update_component_id, one_node_context)
            resolve_samples["one_node_zero_requirements"].append(
                time.perf_counter_ns() - started
            )
            if len(one_plan.topological_nodes) != 1:
                raise BuildError("scale measurement one-node resolve breadth changed")

            started = time.perf_counter_ns()
            one_receipt = measurement_plane.compute(
                update_component_id, one_node_inputs, one_node_context
            )
            compute_samples["one_node_zero_requirements"].append(
                time.perf_counter_ns() - started
            )
            if one_receipt.outputs != {"result": Decimal("1")}:
                raise BuildError("scale measurement one-node compute result changed")

            started = time.perf_counter_ns()
            stack_plan = measurement_plane.resolve(_SCALE_ROOT_ID, context)
            resolve_samples["three_nodes_two_requirements"].append(
                time.perf_counter_ns() - started
            )
            if len(stack_plan.topological_nodes) != 3:
                raise BuildError("scale measurement stack resolve breadth changed")

            started = time.perf_counter_ns()
            stack_receipt = measurement_plane.compute(_SCALE_ROOT_ID, inputs, context)
            compute_samples["three_nodes_two_requirements"].append(
                time.perf_counter_ns() - started
            )
            if (
                stack_receipt.outputs != {"relative_spread": Decimal("0.4")}
                or stack_receipt.nodes_executed != 3
            ):
                raise BuildError("scale measurement stack compute result changed")

        from src.qtt.agents.pr169_agent_orch1_resolvers import (
            AgentComputationCapabilityV1,
            invoke_computation_capability,
        )
        from src.qtt.pretrade.pr169_pretrade1_resolvers import compute_computation
        from src.qtt.readiness.pr169_readiness1_resolvers import (
            project_computation_status,
        )
        from src.qtt.service.pr169_svc1_resolvers import DashboardReadModelService

        projection_plane = facade_class(records=binding_candidate)
        delta_payload = binding_delta.as_dict()
        owner_refresh_ms: dict[str, float] = {}
        started = time.perf_counter_ns()
        readiness_rows = project_computation_status(
            projection_plane,
            [update_component_id],
            one_node_context,
            registry_update=delta_payload,
        )
        owner_refresh_ms["READINESS1"] = elapsed_ms(started)
        if (
            len(readiness_rows) != 1
            or readiness_rows[0].get("selector") != update_component_id
        ):
            raise BuildError("scale measurement READINESS1 refresh failed")

        started = time.perf_counter_ns()
        pretrade_receipt = compute_computation(
            projection_plane,
            update_component_id,
            one_node_inputs,
            one_node_context,
            consumer="CONTROL1_SCALE_VALIDATION",
            mode="FIXTURE_NONLIVE",
        )
        owner_refresh_ms["PRETRADE1"] = elapsed_ms(started)
        if pretrade_receipt.outputs != {"result": Decimal("1")}:
            raise BuildError("scale measurement PRETRADE1 refresh failed")

        started = time.perf_counter_ns()
        agent_status = invoke_computation_capability(
            projection_plane,
            AgentComputationCapabilityV1.from_mapping(
                {
                    "operation": "status",
                    "selector": update_component_id,
                    "context": one_node_context,
                    "input_contract": {},
                    "policy": {},
                }
            ),
        )
        owner_refresh_ms["AGENT_ORCH1"] = elapsed_ms(started)
        if agent_status.get("binding_id") != update_binding_id:
            raise BuildError("scale measurement AGENT-ORCH1 refresh failed")

        service = DashboardReadModelService(
            root / "unused-service-artifacts",
            computation_control=projection_plane,
        )
        started = time.perf_counter_ns()
        service_status = service.computation_status(
            update_component_id, one_node_context
        )
        owner_refresh_ms["SVC1"] = elapsed_ms(started)
        if service_status.get("binding_id") != update_binding_id:
            raise BuildError("scale measurement SVC1 refresh failed")

        measurement_diagnostics = measurement_plane._diagnostics()
        if any(
            int(measurement_diagnostics.get(name, -1)) != 0
            for name in (
                "runtime_registry_file_reads_after_initialization",
                "per_request_full_registry_iterations",
                "unrelated_component_executions",
            )
        ):
            raise BuildError(
                f"scale measurement runtime diagnostics failed: {measurement_diagnostics!r}"
            )

        measurement_matrix = {
            "authority": "LOCAL_NON_AUTHORITATIVE_DIAGNOSTIC_ONLY",
            "deterministic_subset_policy": (
                "CANONICAL_COMPONENT_ID_ASCENDING_FIRST_N_INCLUDING_SELECTED_STACK"
            ),
            "measurement_registry_records": measurement_count,
            "fixed_seed": _SCALE_PROBE_SEED,
            "timing_thresholds_applied": False,
            "percentile_method": "NEAREST_RANK",
            "compile_ms": {
                "no_op_expansion": no_op_compile_ms,
                "single_binding_update": binding_compile_ms,
                "representative_new_record": new_record_compile_ms,
            },
            "compile_proofs": {
                "no_op_delta_empty": True,
                "single_binding_changed_component_ids": [update_component_id],
                "representative_new_record_added_component_ids": [new_component_id],
            },
            "index_ms": {
                "incremental_refresh": incremental_index_refresh_ms,
                "full_rebuild": full_index_rebuild_ms,
            },
            "incremental_index_full_rebuild_semantic_parity": index_parity,
            "request_ms_by_selected_subgraph": {
                "one_node_zero_requirements": {
                    "selected_nodes": 1,
                    "selected_requirements": 0,
                    "resolve": measurement_summary(
                        resolve_samples["one_node_zero_requirements"]
                    ),
                    "compute": measurement_summary(
                        compute_samples["one_node_zero_requirements"]
                    ),
                },
                "three_nodes_two_requirements": {
                    "selected_nodes": 3,
                    "selected_requirements": 2,
                    "resolve": measurement_summary(
                        resolve_samples["three_nodes_two_requirements"]
                    ),
                    "compute": measurement_summary(
                        compute_samples["three_nodes_two_requirements"]
                    ),
                },
            },
            "changed_projection_refresh_ms": owner_refresh_ms,
            "changed_projection_owners": [
                "READINESS1",
                "PRETRADE1",
                "AGENT_ORCH1",
                "SVC1",
            ],
            "runtime_registry_file_reads_after_initialization": 0,
            "per_request_full_registry_iterations": 0,
            "unrelated_component_executions": 0,
        }
    return {
        "executed": True,
        "requested_records": record_count,
        "fixed_seed": _SCALE_PROBE_SEED,
        "serialized_layouts": [
            str(single_layout.get("layout")),
            str(sharded_layout.get("layout")),
        ],
        "facade_initialization_count": 2,
        "indexed_root_and_binding_lookup": True,
        "selected_subgraph_nodes": 3,
        "selected_subgraph_compute": True,
        "single_shard_logical_and_receipt_parity": True,
        "runtime_registry_file_reads_after_initialization": 0,
        "per_request_full_registry_iterations": 0,
        "unrelated_component_executions": 0,
        "test_ref": (
            "tests/pr169_qku_comp_control1/test_control1.py::"
            "test_fixed_seed_structural_scale_probe_real_layout_resolve_compute"
        ),
        "validator_ref": "tools/validate_pr169_qku_comp_control1.py::_scale_probe",
        "persistent_artifact_created": False,
        "latency_or_profit_claim": False,
        "timing_threshold_authority": False,
        "local_non_authoritative_measurements_ms": {
            "record_materialization": materialization_ms,
            "both_layout_write_load_and_facade_initialization": layout_ms,
            "resolve_and_compute": execution_ms,
        },
        "local_non_authoritative_measurement_matrix": measurement_matrix,
    }


def _delta_summary(delta: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "added_component_ids",
        "changed_component_ids",
        "retired_component_ids",
        "added_binding_ids",
        "changed_binding_ids",
        "removed_binding_ids",
        "affected_dependent_ids",
    )
    summary = {f"{field}_count": len(delta.get(field, [])) for field in fields}
    summary["affected_consumer_classes"] = sorted(
        set(delta.get("affected_consumer_classes", []))
    )
    summary["registry_schema_version"] = delta.get("registry_schema_version")
    summary["persistent_delta_written"] = False
    return summary


def _no_orphan_diagnostics(
    records: Sequence[Mapping[str, Any]],
    source_universe_closure: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive producer/consumer/validator/lifecycle and source-row closure."""

    def present(value: Any) -> bool:
        return value is not None and bool(str(value).strip())

    orphan_ids: list[str] = []
    covered_count = 0
    terminal_disposition_count = 0
    fake_audit_runtime_consumer_count = 0
    in_scope_count = 0
    for record in records:
        qku_roles = record.get("uses", {}).get("qku_role_bindings", ())
        agent_reachable = bool(qku_roles) or any(
            bool(policy.get("control_plane_operations"))
            for binding in record.get("bindings", ())
            if isinstance(binding, Mapping)
            for policy in (
                binding.get("agent_access_policy", {}).values()
                if isinstance(binding.get("agent_access_policy"), Mapping)
                else ()
            )
            if isinstance(policy, Mapping)
        )
        active = record.get("record_state") in {
            "CANONICAL_ACCEPTED",
            "PROVISIONAL",
            "UNDER_REVIEW",
        }
        if not active and not agent_reachable:
            continue
        in_scope_count += 1
        governance = record.get("governance", {})
        bindings = [
            binding
            for binding in record.get("bindings", ())
            if isinstance(binding, Mapping)
        ]
        producer_ok = present(governance.get("producer_owner")) and all(
            present(binding.get("producer_owner")) for binding in bindings
        )
        validator_ok = bool(governance.get("validator_refs")) and all(
            binding.get("validator_refs") for binding in bindings
        )
        consumers = {
            str(value)
            for value in record.get("uses", {}).get("consumer_class_tags", ())
            if str(value).strip()
        }
        consumers.update(
            str(value)
            for binding in bindings
            for value in binding.get("downstream_consumer_classes", ())
            if str(value).strip()
        )
        real_consumers = {
            value
            for value in consumers
            if "VALIDATOR" not in value.upper() and "AUDIT" not in value.upper()
        }
        consumer_ok = bool(real_consumers)
        if active:
            lifecycle_ok = bool(bindings) and all(
                present(binding.get("activation_state"))
                for binding in bindings
            )
        else:
            lifecycle_ok = bool(bindings) and all(
                present(binding.get("terminal_disposition_or_null"))
                for binding in bindings
            )
            if lifecycle_ok:
                terminal_disposition_count += 1
        audit_only = any(
            "AUDIT_ONLY" in str(provenance.get("source_relation", "")).upper()
            for provenance in record.get("provenance", ())
            if isinstance(provenance, Mapping)
        )
        if audit_only and real_consumers:
            fake_audit_runtime_consumer_count += 1
        if producer_ok and consumer_ok and validator_ok and lifecycle_ok and not (
            audit_only and real_consumers
        ):
            covered_count += 1
        else:
            orphan_ids.append(str(record.get("canonical_component_id", "")))

    artifacts = [
        artifact
        for artifact in source_universe_closure.get("artifacts", ())
        if isinstance(artifact, Mapping)
    ]
    unclassified_artifact_count = sum(
        int(artifact.get("classified_rows", -1))
        != int(artifact.get("actual_rows_read", -2))
        or int(artifact.get("unresolved_count", 0)) != 0
        for artifact in artifacts
    )
    if orphan_ids or unclassified_artifact_count or fake_audit_runtime_consumer_count:
        raise BuildError(
            "no-orphan closure failed: "
            f"orphans={orphan_ids[:10]} unclassified_artifacts="
            f"{unclassified_artifact_count} fake_audit_consumers="
            f"{fake_audit_runtime_consumer_count}"
        )
    return {
        "active_agent_reachable_record_count": in_scope_count,
        "producer_consumer_validator_lifecycle_covered_count": covered_count,
        "producer_consumer_validator_lifecycle_coverage": "100%",
        "active_agent_reachable_orphan_count": 0,
        "declared_source_artifact_count": len(artifacts),
        "unclassified_in_scope_upstream_artifact_count": 0,
        "terminal_record_with_exact_disposition_count": terminal_disposition_count,
        "fake_audit_only_runtime_consumer_count": 0,
    }


def _acceptance_report(
    records: Sequence[Mapping[str, Any]],
    batches: Sequence[Mapping[str, Any]],
    compiler_reports: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    layout: Mapping[str, Any],
    measurements: Mapping[str, Any],
    runtime_measurements: Mapping[str, Any],
    delta: Mapping[str, Any],
    scale_probe: Mapping[str, Any],
    source_universe_closure: Mapping[str, Any],
    *,
    base_record_count: int,
    base_registry_serialized_bytes: int,
    rp5c_compaction_measurements: Mapping[str, int],
    shape_validation_ms: float,
    total_build_ms: float,
) -> dict[str, Any]:
    state_counts = Counter(str(row["record_state"]) for row in records)
    origin_counts: Counter[str] = Counter()
    inventory_counts: Counter[str] = Counter()
    decision_role_counts: Counter[str] = Counter()
    exact_actions: Counter[str] = Counter()
    semantic_relation_counts: Counter[str] = Counter()
    provenance_relation_counts: Counter[str] = Counter()
    native_implementation_count = 0
    qku_role_count = 0
    requirements_count = 0
    for record in records:
        origin_counts.update(record.get("origin_cohorts", []))
        inventory_class = record.get("definition", {}).get("implementation_inventory_class")
        if inventory_class:
            inventory_counts[str(inventory_class)] += 1
        decision_role_counts.update(record.get("uses", {}).get("decision_roles", []))
        qku_role_count += len(record.get("uses", {}).get("qku_role_bindings", []))
        requirements_count += len(record.get("definition", {}).get("requirements", []))
        for implementation in record.get("definition", {}).get("implementation_versions", []):
            if implementation.get("code_owner") == "CONTROL1_PRIVATE_RUNTIME":
                native_implementation_count += 1
        for relation in record.get("relations", []):
            relation_type = str(relation.get("relation_type", ""))
            if relation_type in {
                "ALIAS_OF",
                "FAMILY_BINDING_OF",
                "SUCCESSOR_OF",
                "ENCODES_OR_MAPS",
                "DISTINCT_FROM",
                "SUPERSEDES",
            }:
                semantic_relation_counts[relation_type] += 1
        provenance_relation_counts.update(
            str(entry.get("source_relation", ""))
            for entry in record.get("provenance", [])
        )
        for binding in record.get("bindings", []):
            action = binding.get("exact_resolution_action_or_null")
            if action:
                exact_actions[str(action).split(":", 1)[0]] += 1
    owner_records = [
        row for row in records if row.get("definition", {}).get("owner_requirement_crosswalk")
    ]
    rp5c_records = [
        row for row in records if str(row["canonical_component_id"]).startswith("QTT.COMP.RP5C.")
    ]
    rp5c_occurrence_count = sum(
        int(relation.get("source_occurrence_count", 0))
        for row in rp5c_records
        for relation in row.get("relations", [])
        if relation.get("relation_type")
        == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
    )
    forbidden_rp5c_lineage_array_count = sum(
        key in relation
        for row in rp5c_records
        for relation in row.get("relations", [])
        for key in (
            "member_identity_row_ids",
            "identity_row_ids",
            "source_artifact_row_ids",
        )
    )
    rp5c_inner_source_ref_summaries = [
        relation
        for row in rp5c_records
        for relation in row.get("relations", [])
        if relation.get("relation_type") == "RP5C_SOURCE_LINEAGE_SUMMARY"
        and isinstance(relation.get("source_artifact_refs"), list)
        and relation.get("source_artifact_refs")
        and relation.get("source_artifact_ref_count")
        == len(relation["source_artifact_refs"])
    ]
    rp5c_incomplete_role_records = [
        row
        for row in rp5c_records
        if row.get("uses", {}).get("qku_role_bindings")
        and str(
            row.get("definition", {}).get(
                "complete_mathematical_or_procedural_definition", ""
            )
        ).startswith("MISSING_SEMANTIC_SPECIFICATION:")
    ]
    active_rp5c_qku_contexts: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in rp5c_records:
        if row.get("record_state") not in {
            "CANONICAL_ACCEPTED",
            "PROVISIONAL",
            "UNDER_REVIEW",
        }:
            continue
        for role in row.get("uses", {}).get("qku_role_bindings", []):
            active_rp5c_qku_contexts[
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                )
            ].add(str(row["canonical_component_id"]))
    ambiguous_active_rp5c_context_count = sum(
        len(root_ids) > 1 for root_ids in active_rp5c_qku_contexts.values()
    )
    fixture_ready = [
        row["canonical_component_id"]
        for row in records
        if any(binding.get("derived_state") == "CONTEXT_READY" for binding in row.get("bindings", []))
    ]
    pr162d_fixture_metrics = next(
        (
            dict(batch["ephemeral_fixture_metrics"])
            for batch in batches
            if batch.get("batch_id") == "EXPANSION.PR162D.EXPLICIT_IMPLEMENTATIONS"
        ),
        {},
    )
    pr162b_source_vector_metrics = next(
        (
            dict(batch["pr162b_source_vector_metrics"])
            for batch in batches
            if batch.get("batch_id") == "EXPANSION.SOURCE.SEMANTIC.CLOSURE"
            and isinstance(batch.get("pr162b_source_vector_metrics"), Mapping)
        ),
        {},
    )
    pr162b_source_records = [
        row
        for row in records
        if "PR162B_SOURCE_SEMANTICS" in row.get("origin_cohorts", ())
    ]
    gfp_source_records = [
        row
        for row in records
        if "GFP_SOURCE_SEMANTICS" in row.get("origin_cohorts", ())
    ]
    gfp_registered_callable_refs = {
        str(implementation.get("callable_or_solver_ref", ""))
        for row in gfp_source_records
        for implementation in row.get("definition", {}).get(
            "implementation_versions", ()
        )
        if implementation.get("callable_or_solver_ref")
    }
    compiler_batch_summaries = []
    for report in compiler_reports:
        decision_counts = Counter(
            str(outcome.get("decision", ""))
            for outcome in report.get("outcomes", [])
            if isinstance(outcome, Mapping)
        )
        transient_delta = report.get("transient_delta", {})
        compiler_batch_summaries.append(
            {
                "batch_id": report.get("batch_id"),
                "items_read": report.get("items_read"),
                "bounded_candidate_bucket_count": report.get(
                    "bounded_candidate_bucket_count"
                ),
                "all_pairs_proof_attempted": report.get(
                    "all_pairs_proof_attempted"
                ),
                "outcome_decision_counts": dict(sorted(decision_counts.items())),
                "delta_counts": {
                    field: len(transient_delta.get(field, []))
                    for field in (
                        "added_component_ids",
                        "changed_component_ids",
                        "retired_component_ids",
                        "added_binding_ids",
                        "changed_binding_ids",
                        "removed_binding_ids",
                        "affected_dependent_ids",
                        "affected_consumer_classes",
                    )
                },
            }
        )
    qku_verification = _validate_qku_verification_receipts(
        records, enforce_current_universe=True
    )
    no_orphan = _no_orphan_diagnostics(records, source_universe_closure)
    return {
        "report_type": "PR169_QKU_COMP_CONTROL1_ACCEPTANCE_REPORT",
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "builder": BUILDER_NAME,
        "independent_validator": VALIDATOR_NAME,
        "overall_acceptance_authority": "INDEPENDENT_VALIDATOR_AND_OWNER_AUDIT_REQUIRED",
        "builder_authored_overall_pass": False,
        "source_closure": _source_closure(),
        "computation_universe_row_level_closure": copy.deepcopy(
            dict(source_universe_closure)
        ),
        "qku_verification": qku_verification,
        "no_orphan": no_orphan,
        "source_precedence_conflict_resolutions": [
            {
                "conflict": "RP5C described a permanent identity/write authority",
                "resolution": "RP5C IDs and lineage are immutable baseline provenance inside the one CONTROL1 registry; runtime direct access is absent",
            },
            {
                "conflict": "historical dedupe/family labels resemble semantic proof",
                "resolution": "all RP5C groups remain provisional or dormant and explicitly lack CONTROL1 direct equivalence proof",
            },
            {
                "conflict": "PR162D expected vectors are produced by source implementations",
                "resolution": "fixture invocation is preserved but independent oracle remains REQUIRED except the five exact closed-stack arithmetic nodes",
            },
            {
                "conflict": "reverted implementation claimed all 213 callable",
                "resolution": "only owner card IDs/families/names survive; all 213 are provisional with MISSING_SEMANTIC_SPECIFICATION actions",
            },
            {
                "conflict": "25 quantum rows share nine builder callables",
                "resolution": "nine callable-family records preserve every source formulation role; no encoding is aliased to an original economic model",
            },
        ],
        "expansion_batches": [
            {
                "batch_id": batch["batch_id"],
                "batch_origin": batch["batch_origin"],
                "source_classification": batch["source_classification"],
                "source_refs": batch["source_refs"],
                "item_count": len(batch["items"]),
                "promotion_ceiling": batch["requested_promotion_ceiling"],
            }
            for batch in batches
        ],
        "expansion_compiler": {
            "continuing_intake_path_count": 1,
            "parallel_merge_or_admission_path_count": 0,
            "batch_summaries": compiler_batch_summaries,
        },
        "counts": {
            "logical_registry_rows": len(records),
            "base_registry_rows_loaded": base_record_count,
            "record_state_counts": dict(sorted(state_counts.items())),
            "origin_cohort_counts": dict(sorted(origin_counts.items())),
            "decision_role_counts": dict(sorted(decision_role_counts.items())),
            "qku_role_binding_count": qku_role_count,
            "canonical_requirement_count": requirements_count,
            "exact_action_class_counts": dict(sorted(exact_actions.items())),
        },
        "rp5c_baseline": {
            "canonical_identity_records": len(rp5c_records),
            "expected_canonical_identity_records": EXPECTED_RP5C_IDENTITIES,
            "source_occurrence_count": rp5c_occurrence_count,
            "expected_source_occurrence_count": EXPECTED_RP5C_OCCURRENCES,
            "lineage_closure_coverage": "100%",
            "canonical_component_id_churn_count": 0,
            "qku_role_loss_count": 0,
            "inner_source_artifact_ref_set_coverage": (
                f"{len(rp5c_inner_source_ref_summaries)}/"
                f"{len(rp5c_records)}"
            ),
            "inner_source_artifact_ref_total": sum(
                int(relation["source_artifact_ref_count"])
                for relation in rp5c_inner_source_ref_summaries
            ),
            "forbidden_runtime_lineage_array_count": forbidden_rp5c_lineage_array_count,
            "accepted_runtime_identity_authority_created": False,
            "direct_runtime_rp5c_access_created": False,
            "preserved_qku_role_binding_count": sum(
                len(row.get("uses", {}).get("qku_role_bindings", []))
                for row in rp5c_records
            ),
            "incomplete_qku_role_record_count": len(rp5c_incomplete_role_records),
            "incomplete_qku_role_active_runtime_root_count": sum(
                row.get("record_state")
                in {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"}
                for row in rp5c_incomplete_role_records
            ),
            "ambiguous_active_qku_context_count": ambiguous_active_rp5c_context_count,
            "selector_or_root_invented_for_incomplete_import_count": sum(
                bool(
                    role.get("stack_root_or_direct_component")
                    or role.get("selection_rule_if_container")
                )
                for row in rp5c_incomplete_role_records
                for role in row.get("uses", {}).get("qku_role_bindings", [])
            ),
            "record_states": dict(
                sorted(Counter(row["record_state"] for row in rp5c_records).items())
            ),
        },
        "implementation_registration": {
            "definition_inventory_counts": dict(sorted(inventory_counts.items())),
            "expected_formula_count": EXPECTED_FORMULA_IMPLEMENTATIONS,
            "expected_algorithm_count": EXPECTED_ALGORITHM_IMPLEMENTATIONS,
            "source_quantum_formulation_count": EXPECTED_QUANTUM_FORMULATIONS,
            "expected_quantum_callable_family_count": EXPECTED_QUANTUM_CALLABLE_FAMILIES,
            "explicit_allowlist_required": True,
            "control_native_implementation_append_count": native_implementation_count,
            "fixture_context_ready_component_ids": sorted(fixture_ready),
            "source_fixture_is_independent_oracle": False,
            "ephemeral_fixture_validation": pr162d_fixture_metrics,
            "pr162b_provisional_implementation_record_count": len(
                pr162b_source_records
            ),
            "pr162b_source_vector_validation": pr162b_source_vector_metrics,
            "pr162b_source_vectors_are_independent_oracles": False,
            "pr162b_context_ready_from_source_vector_count": 0,
            "gfp_provisional_implementation_record_count": len(
                gfp_source_records
            ),
            "gfp_importable_registered_callable_ref_count": len(
                gfp_registered_callable_refs
            ),
            "gfp_complete_typed_source_vector_count": 0,
            "gfp_eligible_central_fixture_invocation_count": 0,
            "gfp_exact_action": "MISSING_COMPLETE_TYPED_TEST_VECTOR",
            "persisted_fixture_vector_count": 0,
        },
        "semantic_reuse": {
            "direct_relation_counts": dict(sorted(semantic_relation_counts.items())),
            "source_disposition_kind_count": len(provenance_relation_counts),
            "exact_duplicate_reuse_count": provenance_relation_counts[
                "EXACT_DUPLICATE_REUSED_PROVENANCE_ONLY"
            ],
            "provenance_only_reuse_count": provenance_relation_counts[
                "PROVENANCE_ONLY_REUSE_NO_NEW_RECORD"
            ],
            "canonical_registry_synthetic_proof_record_count": 0,
            "canonical_registry_test_or_validator_source_count": 0,
            "synthetic_expansion_proof_location": (
                "tests/pr169_qku_comp_control1/test_control1.py::"
                "test_synthetic_expansion_proof_stays_temporary_and_reaches_generic_owners"
            ),
            "successor_claim_count": semantic_relation_counts["SUCCESSOR_OF"],
            "qku_role_proposal_rejected_without_synthetic_qku_count": provenance_relation_counts[
                "QKU_ROLE_PROPOSAL_REJECTED_PENDING_EXISTING_QKU_AUTHORITY_AND_DIRECT_ROLE_PROOF"
            ],
        },
        "owner_requirement_213": {
            "inventory_count": len(owner_records),
            "coverage_denominator": EXPECTED_OWNER_REQUIREMENTS,
            "provisional_count": sum(row["record_state"] == "PROVISIONAL" for row in owner_records),
            "inherited_prior_implementation_claim_count": 0,
            "inherited_prior_alias_or_pass_claim_count": 0,
            "exact_action": "MISSING_SEMANTIC_SPECIFICATION_PER_CARD",
        },
        "requirements_compiled_dag": {
            "persistent_dag_written": False,
            "canonical_requirement_count": requirements_count,
            "source_local_selector_count": 0,
            "cycle_count": 0,
            "closed_fixture_roots": [
                "QTT.COMP.FORMULA.PROBABILITY_EDGE",
                "QTT.COMP.FORMULA.RELATIVE_SPREAD",
            ],
            "closed_fixture_upstreams": [
                "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                "QTT.COMP.FORMULA.MID_PRICE",
                "QTT.COMP.FORMULA.SPREAD",
            ],
        },
        "quantum": {
            "source_formulations": EXPECTED_QUANTUM_FORMULATIONS,
            "callable_family_records": inventory_counts["QUANTUM_CALLABLE_FAMILY"],
            "distinct_original_economic_model_target_count": sum(
                str(row["canonical_component_id"]).startswith("QTT.COMP.ECONOMIC_MODEL.")
                for row in records
            ),
            "encodes_or_maps_relation_count": semantic_relation_counts["ENCODES_OR_MAPS"],
            "maturity_ceiling": "SPECIFIED",
            "local_original_model_parity_claim_count": 0,
            "qpu_backend_call_count": 0,
            "quantum_advantage_claim_count": 0,
            "exact_action": "MISSING_QUANTUM_ORIGINAL_MODEL_LOCAL_PARITY_PER_CALLABLE_FAMILY",
        },
        "pr165_d2_agent_policy": {
            "source_ref": PR165_D2_ROSTER.as_posix(),
            "agent_ids": list(agent_ids),
            "policy_basis": "CLASSIFICATION_BASED_NO_PER_FORMULA_ROUTE",
            "mode_ceiling": "FIXTURE_NONLIVE",
            "order_release_authority_count": 0,
            "source_truth_authority_count": 0,
        },
        "storage": {
            **dict(measurements),
            "actual_staged_runtime_measurements": dict(runtime_measurements),
            "accepted_base_registry_serialized_bytes": base_registry_serialized_bytes,
            "rp5c_compaction_measurement_basis": (
                "SOURCE_DERIVED_SAME_REGISTRY_WITH_REMOVED_LINEAGE_ARRAYS_RESTORED"
            ),
            **dict(rp5c_compaction_measurements),
            "material_registry_size_reduction": bool(
                int(rp5c_compaction_measurements["compaction_bytes_reduced"]) > 0
            ),
            "active_physical_layout": layout.get("layout"),
            "active_physical_layout_count": 1,
            "shard_count": layout.get("shard_count", 0),
            "registry_files": sorted(layout.get("registry_files", [])),
            "policy_reasons": layout.get("policy_reasons", []),
            "storage_policy": _control_storage_policy(),
            "simultaneous_full_and_sharded_layout_count": 0,
            "qtt_generated_hash_checksum_or_digest_count": 0,
        },
        "transient_registry_update": _delta_summary(delta),
        "scale_probe": dict(scale_probe),
        "measurements": {
            "shape_validation_ms": round(shape_validation_ms, 3),
            "total_build_and_stage_ms": round(total_build_ms, 3),
        },
        "acceptance_diagnostics": {
            "public_control_plane_facade_count_created_by_builder": 0,
            "logical_decision_computation_registry_count": 1,
            "canonical_persistent_record_type_count": 1,
            "persistent_dag_registry_count": 0,
            "persistent_duplicate_equivalence_registry_count": 0,
            "persistent_registry_update_event_log_count": 0,
            "parallel_formula_library_count": 0,
            "runtime_direct_historical_library_access_count": 0,
            "embedded_bulk_evidence_payload_count": 0,
            "persisted_fixture_vector_count": 0,
            "connector_private_state_call_count": 0,
            "order_release_count": 0,
            "replay_execution_count": 0,
            "paper_execution_count": 0,
            "shadow_execution_count": 0,
            "live_execution_count": 0,
            "profit_or_quantum_advantage_claim_count": 0,
            "active_agent_reachable_orphan_count": no_orphan[
                "active_agent_reachable_orphan_count"
            ],
            "unclassified_in_scope_upstream_artifact_count": no_orphan[
                "unclassified_in_scope_upstream_artifact_count"
            ],
            "fake_audit_only_runtime_consumer_count": no_orphan[
                "fake_audit_only_runtime_consumer_count"
            ],
        },
        "truthful_limitations": [
            "RP5C baseline rows preserve identity and custody but generally lack complete computation semantics.",
            "PR162D source callables commonly use Python float and require typed Decimal/accounting boundaries before financial use.",
            "PR162D source-derived expected vectors are fixture invocation evidence, not independent production oracles; only five Decimal-native arithmetic records have complete specification, exact typed fixture binding, independent oracle, and compute access.",
            "Only implied-probability/probability-edge and mid/spread/relative-spread fixture subgraphs are closed here.",
            "MAP3, PR162B, and GFP semantic rows are preserved as provisional source-semantic candidates; no source name, fixture, implementation label, or selected status proves equivalence or readiness. PR162B's 75 source vectors prove callable inventory execution but are not independent oracles.",
            "RP5D readiness tiers, R1 smoke values, RP5E previews, evidence combinations, and value gaps remain context/evidence at their current owners and are not inflated into formulas; their classified computation references are resolved separately.",
            "All 6,502 CandidatePackets remain source-scoped OWNER_TEMPLATE/REPLAY_PAPER_CANDIDATE alternatives with no runtime root; 63 conflict with stronger PR162B QKU semantics and all require accepted source-specific selection proof.",
            "The 20,115 capped GFP discovery rows are value-read and retained at their owner, but none supplies complete typed semantics or direct equivalence proof. Five generic descriptions are textual containment search hints and zero are exact selected-expression matches; neither is semantic proof. Their underlying computation-semantic denominator and closure remain UNPROVEN; no selected-formula label creates a mapping.",
            "The 80 master-plan formula candidates, 42 algorithm-family candidates, and 20 external candidates are provisional CONTROL1 records with source provenance, status/explain-only policy, and exact missing-semantic actions; none is compute-ready.",
            "No replay, PAPER, shadow, dry-run, canary, live, private-state, connector, QPU, cash, fill, PnL, or order evidence is created.",
            "No source record is promoted merely from a count, name, source ID, family label, or fixture result.",
        ],
    }


def _resolve_safe_output_target(repo_root: Path, out_dir: str | Path) -> Path:
    """Confine publication to the owned canonical root or an empty temp target."""

    target = Path(out_dir)
    if not target.is_absolute():
        target = repo_root / target
    target = target.resolve()
    if target == repo_root or any(part.lower() == ".codex_inputs" for part in target.parts):
        raise BuildError(f"unsafe CONTROL1 output directory: {target}")
    canonical = (repo_root / GENERATED_PREFIX).resolve()
    if target == canonical:
        return target
    try:
        target.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise BuildError(
            "non-canonical CONTROL1 output may not create or replace repository paths: "
            f"{target}"
        )
    temp_root = Path(tempfile.gettempdir()).resolve()
    try:
        target.relative_to(temp_root)
    except ValueError as exc:
        raise BuildError(
            "non-canonical CONTROL1 output must be a disposable temporary path: "
            f"{target}"
        ) from exc
    if target == temp_root:
        raise BuildError("refusing to publish over the system temporary root")
    if target.exists():
        if not target.is_dir() or any(target.iterdir()):
            raise BuildError(
                "non-canonical CONTROL1 temporary output must not replace existing content: "
                f"{target}"
            )
    return target


def _publish_directory(staged: Path, target: Path) -> None:
    parent = target.parent.resolve()
    target_resolved = target.resolve()
    if target_resolved == parent:
        raise BuildError("refusing to publish over output parent")
    backup = parent / f".{target.name}.previous"
    if backup.exists():
        raise BuildError(f"stale CONTROL1 publication backup requires review: {backup}")
    if not target.exists():
        os.replace(staged, target)
        return
    os.replace(target, backup)
    try:
        os.replace(staged, target)
    except BaseException:
        os.replace(backup, target)
        raise
    shutil.rmtree(backup)


def build(
    repo_root: str | Path,
    out_dir: str | Path = GENERATED_PREFIX,
    *,
    timeout_ms: int = 3_600_000,
    force_layout: str = "auto",
    scale_probe_records: int = 0,
) -> dict[str, Any]:
    """Build, validate, and atomically publish the CONTROL1 generated surface."""
    started = time.perf_counter()
    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise BuildError(f"repository root does not exist: {root}")
    root_text = str(root)
    if root_text not in sys.path:
        # Direct ``python tools/...`` execution places only ``tools`` on
        # sys.path.  Add the fixed reviewed repository root before loading the
        # single CONTROL1 owner; no caller-selected module path is accepted.
        sys.path.insert(0, root_text)
    target = _resolve_safe_output_target(root, out_dir)
    deadline = _Deadline(timeout_ms)
    lock_path = target.parent / f".{target.name}.writer.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise BuildError(f"concurrent or stale CONTROL1 writer lock: {lock_path}") from exc
    os.close(lock_fd)
    staged: Path | None = None
    try:
        base_records = _load_cumulative_base_records(root, target, deadline)
        base_measurements = _measure_registry(base_records) if base_records else {
            "logical_registry_serialized_bytes": 0
        }
        records, batches, agent_ids, compiler_reports = _build_registry_and_batches(
            root,
            deadline,
            base_records,
        )
        validation_started = time.perf_counter()
        _validate_registry(records, deadline)
        shape_validation_ms = (time.perf_counter() - validation_started) * 1000.0
        measurements = _measure_registry(records)
        rp5c_compaction_measurements = _measure_uncompacted_rp5c_counterfactual(
            root, records, measurements, deadline
        )
        delta = _derive_update(base_records, records)
        if delta.get("registry_schema_version") != REGISTRY_SCHEMA_VERSION:
            raise BuildError("transient RegistryUpdateV1 schema mismatch")
        source_universe_closure = _source_universe_closure(root, records, deadline)
        scale_probe = _run_scale_probe(scale_probe_records)
        deadline.check("pre-publication staging")
        staged = Path(
            tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=str(target.parent))
        )
        # The layout writer owns creation of its output directory.  The
        # tempfile name itself is untracked and never becomes a generated file.
        staged.rmdir()
        layout = _write_layout(
            records,
            staged,
            force_layout=force_layout,
            measurements=measurements,
            shape_validation_ms=shape_validation_ms,
        )
        layout = {**layout, **_inspect_layout(staged)}
        runtime_measurements = _measure_staged_runtime(staged)
        report = _acceptance_report(
            records,
            batches,
            compiler_reports,
            agent_ids,
            layout,
            measurements,
            runtime_measurements,
            delta,
            scale_probe,
            source_universe_closure,
            base_record_count=len(base_records),
            base_registry_serialized_bytes=int(
                base_measurements["logical_registry_serialized_bytes"]
            ),
            rp5c_compaction_measurements=rp5c_compaction_measurements,
            shape_validation_ms=shape_validation_ms,
            total_build_ms=(time.perf_counter() - started) * 1000.0,
        )
        _write_json(staged / "acceptance.report.json", report)
        actual_files = sorted(path.name for path in staged.iterdir() if path.is_file())
        expected_files = sorted([*layout["registry_files"], "acceptance.report.json"])
        if actual_files != expected_files:
            raise BuildError(
                f"unexpected CONTROL1 generated surface: {actual_files!r} != {expected_files!r}"
            )
        deadline.check("atomic publication")
        _publish_directory(staged, target)
        staged = None
        return {
            "output_dir": str(target),
            "logical_registry_rows": len(records),
            "active_physical_layout": layout["layout"],
            "shard_count": layout["shard_count"],
            "registry_files": layout["registry_files"],
            "acceptance_report": "acceptance.report.json",
            "transient_registry_update": _delta_summary(delta),
            "independent_validation_required": True,
        }
    finally:
        if staged is not None and staged.exists():
            shutil.rmtree(staged)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=GENERATED_PREFIX)
    parser.add_argument("--timeout-ms", type=int, default=3_600_000)
    parser.add_argument(
        "--force-layout",
        choices=("auto", "single", "sharded"),
        default="auto",
    )
    parser.add_argument("--scale-probe-records", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = build(
        args.repo_root,
        args.out_dir,
        timeout_ms=args.timeout_ms,
        force_layout=args.force_layout,
        scale_probe_records=args.scale_probe_records,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
