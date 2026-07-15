#!/usr/bin/env python3
"""Independent validator for PR169-QKU-COMP-CONTROL1.

The validator reconstructs conclusions from the logical registry, source
cohorts, public facade, and private *mechanism* helpers exposed by
``control.py``.  It reads the existing ``acceptance.report.json`` only to
compare its compact online-source packs and QKU crosswalk structure against
independently derived registry/source facts; it never trusts report PASS/FAIL
labels or builder-authored acceptance counts.

Only a single JSON document is written, to stdout.  Temporary registries used
for storage, scale, and concurrency probes are created outside the repository.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import dataclasses
import importlib
import inspect
import io
import json
import math
import random
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict, deque
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

# Validation must not create repository-local bytecode artifacts even when a
# caller forgets the repository's conventional ``python -B`` flag.
sys.dont_write_bytecode = True

DEFAULT_ARTIFACT_DIR = Path("docs/master_plan/generated/pr169_qku_comp_control1")
RP5C_DEDUPE = Path("docs/master_plan/generated/rp5c/identity_deduplication_ledger.jsonl")
RP5C_LINEAGE = Path("docs/master_plan/generated/rp5c/qku_formula_identity_lineage.jsonl")
RP5C_CANONICAL_LIBRARY = Path(
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"
)
RP5C_LIBRARIES = (
    Path("docs/master_plan/generated/rp5c/immutable_qku_library.jsonl"),
    Path("docs/master_plan/generated/rp5c/immutable_formula_library.jsonl"),
    Path("docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl"),
)
PR162D_TEST_VECTOR_REGISTRY = Path(
    "docs/master_plan/generated/PR162D_R2A_TestVectorRegistry.report.json"
)
_CLOSED_FIXTURE_COMPONENTS = frozenset(
    {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
        "QTT.COMP.FORMULA.PROBABILITY_EDGE",
        "QTT.COMP.FORMULA.MID_PRICE",
        "QTT.COMP.FORMULA.SPREAD",
        "QTT.COMP.FORMULA.RELATIVE_SPREAD",
    }
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
EXPECTED_RP5C_CANONICAL = 10_189
EXPECTED_RP5C_OCCURRENCES = 183_802
EXPECTED_GFP_DISCOVERY_ROWS = 20_115
EXPECTED_GFP_DISCOVERY_TEXTUAL_CONTAINMENT_HINT_ROWS = 5
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
EXPECTED_OWNER_REQUIREMENTS = 213
EXPECTED_CANONICAL_UNIQUE_QKUS = 9_425
EXPECTED_QKU_ROLE_KEYS = 9_645
EXPECTED_QKU_ROLE_OCCURRENCES = 10_023
EXPECTED_IMPLEMENTATIONS = {"FORMULA": 61, "ALGORITHM": 30, "QUANTUM_CALLABLE_FAMILY": 9}
EXPECTED_AGENTS = {
    "research_agent",
    "parameter_selector_agent",
    "risk_manager_agent",
    "quantum_optimizer_agent",
    "commander_agent",
    "governance_agent",
    "dashboard_agent",
    "connector_venue_readiness_future_consumer",
}
EXPECTED_AGENT_OPERATION_CEILINGS = {
    "research_agent": {"status", "explain"},
    "parameter_selector_agent": {"resolve", "compute", "status", "explain"},
    "risk_manager_agent": {"resolve", "compute", "status", "explain"},
    "quantum_optimizer_agent": {"resolve", "compute", "status", "explain"},
    "commander_agent": {"resolve", "compute", "status", "explain"},
    "governance_agent": {"status", "explain"},
    "dashboard_agent": {"status", "explain"},
    "connector_venue_readiness_future_consumer": {"status", "explain"},
}
EXPECTED_AGENT_MODE_RANK = {
    "NOT_ELIGIBLE": 0,
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
EXPECTED_AGENT_MAX_MODE = "PAPER"
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
        "FAIR_PRICE_FROM_PROBABILITY", "IMPLIED_PROBABILITY_FROM_BINARY_PRICE",
        "POLY_SPREAD_001", "SPREAD",
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
_QKU_KNOWN_PACKS = frozenset(
    {
        _QKU_UNRESOLVED_PACK,
        _QKU_PRICE_PACK,
        _QKU_DECIMAL_PACK,
        _QKU_INSTITUTIONAL_PACK,
        _QKU_QUANTUM_PACK,
        _QKU_PROVIDER_PACK,
    }
)

# Independent, row-addressable computation-universe closure surface.  This is
# deliberately duplicated here rather than imported from the builder: the
# validator must derive its own denominators and dispositions from current
# owner artifacts, including every declared shard.  Preview records and root
# manifest counts are never treated as value-level consumption.
SOURCE_CLOSURE_ARTIFACTS: tuple[dict[str, Any], ...] = (
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
    # candidate_id is intentionally empty on all current rows.  The current
    # owner supplies the stable, unique row identity in downstream_route_record_ref.
    {"cohort": "VALUE_GAPS_2852", "path": "docs/master_plan/generated/PR164_PR162D_R3RepairTriggerMatrix.report.json", "role": "CONTEXT", "expected": 2_852, "key": "downstream_route_record_ref"},
    {"cohort": "MASTER_PLAN_DISCOVERY", "path": "docs/master_plan/generated/PR168_GFP_MasterPlanFormulaCatalog.report.json", "role": "DISCOVERY", "expected": 15_917, "key": "formula_catalog_id"},
    {"cohort": "POST_RP5C_DISCOVERY", "path": "docs/master_plan/generated/PR168_GFP_PriorPRFormulaCatalog.report.json", "role": "DISCOVERY", "expected": 4_198, "key": "formula_catalog_id"},
    {"cohort": "MASTER_PLAN_CANDIDATES", "path": "docs/master_plan/generated/PR162D_R1_MasterPlanQKUFormulaCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 80, "key": "candidate_id"},
    {"cohort": "MASTER_PLAN_CANDIDATES", "path": "docs/master_plan/generated/PR162D_R1_MasterPlanAlgorithmFamilyCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 42, "key": "candidate_id"},
    {"cohort": "POST_RP5C_CANDIDATES", "path": "docs/master_plan/generated/PR165_ExternalFormulaAndParameterCandidateRegistry.report.json", "role": "SEMANTIC_CANDIDATE", "expected": 20, "key": "external_formula_parameter_ref"},
)

# Independent current-equivalent owner projection discovery.  These are
# intentionally validator-owned names and are not imported from the builder.
# Counts are derived from each owner manifest/report and checked against the
# physical rows; a count in a manifest is never accepted as row consumption.
_RP5D_NON_COMPUTATION_MANIFESTS = frozenset(
    {
        "rp5d_agent_dag.jsonl",
        "rp5d_agent_routing_ledger.jsonl",
        "rp5d_artifact_dag.jsonl",
        "rp5d_crosswalk_discovery_receipts.jsonl",
        "rp5d_input_consumption.jsonl",
        "rp5d_input_inventory.jsonl",
        "rp5d_no_orphan_artifacts.jsonl",
        "rp5d_reading_receipts.jsonl",
        "rp5d_value_lineage.jsonl",
    }
)
_RP5D_R1_COMPUTATION_SURFACES = frozenset(
    {
        "fixture_bind.jsonl", "input_bind.jsonl", "unit_adapt.jsonl",
        "pnl_map.jsonl", "cash_settle.jsonl", "fee_ready.jsonl",
        "spread_ready.jsonl", "slip_ready.jsonl", "fill_ready.jsonl",
        "lat_ready.jsonl", "capacity_ready.jsonl", "contract_matrix.jsonl",
        "contract_patch.jsonl", "tca_comp.jsonl", "params.jsonl",
        "policy_prov.jsonl", "exec_now_proof.jsonl", "promote.jsonl",
        "nonpromote.jsonl", "unlock_select.jsonl", "rp5e_unlock_in.jsonl",
        "q_struct_carry.jsonl", "q_solver_carry.jsonl", "q_interp_carry.jsonl",
        "proof_tier.jsonl", "research_rec.jsonl", "edge_profit_map.jsonl",
        "source_req.jsonl",
    }
)
_RP5E_COMPUTATION_SURFACES = frozenset(
    {
        "roles.jsonl", "templates.jsonl", "params.jsonl", "policy_prov.jsonl",
        "ctx_pools.jsonl", "ctx_univ.jsonl", "qku_guard.jsonl",
        "unlock_pri.jsonl", "tmp_previews.jsonl", "topk.jsonl", "q_obj.jsonl",
        "q_coeffs.jsonl", "q_interp.jsonl", "q_solver.jsonl", "q_tags.jsonl",
        "default_cand.jsonl", "calib_queue.jsonl", "tca_ready.jsonl",
        "features.jsonl", "edge_feats.jsonl", "exec_prev.jsonl", "classic.jsonl",
        "eph_contracts.jsonl", "no_hardcode.jsonl",
    }
)
_PR162B_COMPUTATION_REPORTS = frozenset(
    {
        "PR162B_QKUConstraintRegistry.report.json",
        "PR162B_QKUObjectiveFunctionRegistry.report.json",
        "PR162B_QKUParameterRangeScaleRegistry.report.json",
        "PR162B_QKUParameterValueRegistry.report.json",
        "PR162B_QKUTradableValueCandidateRegistry.report.json",
        "PR162B_QKUFormulaImplementationBindingRegistry.report.json",
        "PR162B_QKUExecutableComputeContractRegistry.report.json",
        "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
        "PR162B_QuantumSolverSmokeExecutionReport.report.json",
        "PR162B_QKUExecutionClassificationAudit.report.json",
        "PR162B_QKUMarketClassificationRegistry.report.json",
        "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
        "PR162B_QKUDormancyRegistry.report.json",
        "PR162B_QKUTradeRoleRegistry.report.json",
        "PR162B_QKUMarketInputFieldRequirementMatrix.report.json",
        "PR162B_QKUFormulaCoverageAudit.report.json",
        "PR162B_QKUSolverMappingRegistry.report.json",
        "PR162B_QKUFormulaBindingProofMatrix.report.json",
        "PR162B_LiveModeFormulaGateStatus.report.json",
        "PR162B_MetadataOnlyBlockerAudit.report.json",
        "PR162B_PR162CDataRequirementHandoff.report.json",
        "PR162B_AgentFormulaConsumerRoutingMatrix.report.json",
        "PR162B_FormulaSourceRetrievalTargetMatrix.report.json",
        "PR162B_QKUMarketClassificationCoverageAudit.report.json",
        "PR162B_QTTAgentStage1QKUActivationAllowlist.report.json",
    }
)
_PR162D_COMPUTATION_REPORTS = frozenset(
    {
        "PR162D_R2A_FormulaExpressionRegistry.report.json",
        "PR162D_R2A_AlgorithmProcedureRegistry.report.json",
        "PR162D_R2A_QuantumObjectiveRegistry.report.json",
        "PR162D_R2A_ClassicalComparatorRegistry.report.json",
        "PR162D_R2A_TestVectorRegistry.report.json",
        "PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json",
        "PR162D_R2A_PR162RGenericCandidateInputExtension.report.json",
        "PR162D_R2A_PR162EPluginSeedCandidateRegistry.report.json",
        "PR162D_R2A_FormulaLatencyClassRegistry.report.json",
        "PR162D_R2A_HotPathPrecomputeCacheabilityMatrix.report.json",
        "PR162D_R2A_LatencySensitiveCandidateQueue.report.json",
        "PR162D_R2A_UpstreamDownstreamQKUOrchestrationMatrix.report.json",
        "PR162D_R2A_QKUAgentWorkflowTraceabilityMatrix.report.json",
        "PR162D_R2A_CandidateIntakeLaneMatrix.report.json",
        "PR162D_R2A_FormulaPluginSeedRegistry.report.json",
        "PR162D_R2A_AlgorithmPluginSeedRegistry.report.json",
        "PR162D_R2A_QuantumPluginSeedRegistry.report.json",
        "PR162D_R2A_FormulaVersionAndRollbackSeedLedger.report.json",
        "PR162D_R2A_FormulaEquivalenceDedupeMatrix.report.json",
        "PR162D_R2A_MaterializationExpansionPriorityQueue.report.json",
        "PR162D_R2A_FormulationCoverageAudit.report.json",
        "PR162D_R2A_HumanReviewTopFormulations.report.json",
        "PR162D_R2A_OnlineSourceSearchQueue.report.json",
    }
)
_PR162E_COMPUTATION_REPORTS = frozenset(
    {
        "PR162E_PluginFamilyRegistry.report.json",
        "PR162E_FormulaPluginInterface.report.json",
        "PR162E_AlgorithmPluginInterface.report.json",
        "PR162E_QuantumRecipePluginInterface.report.json",
        "PR162E_PluginVersionLedger.report.json",
        "PR162E_PluginRollbackLedger.report.json",
        "PR162E_PluginEquivalenceDedupe.report.json",
        "PR162E_PluginCompatibilityMatrix.report.json",
        "PR162E_PluginDependencyDAG.report.json",
        "PR162E_PluginRuntimeBudget.report.json",
        "PR162E_PluginFailClosed.report.json",
        "PR162E_PluginTestVectors.report.json",
        "PR162E_PluginValidator.report.json",
        "PR162E_PluginChampChallenger.report.json",
        "PR162E_PluginRepairQueue.report.json",
        "PR162E_RepairedCandidateToPluginMap.report.json",
        "PR162E_ExternalCandidateIntake.report.json",
        "PR162E_ExternalCandidateDedup.report.json",
        "PR162E_ExternalCandidateToPluginMap.report.json",
        "PR162E_ExternalCandidateRepairFill.report.json",
        "PR162E_AgentDutyBinding.report.json",
        "PR162E_QKUFormulaAlgorithmLineage.report.json",
        "PR162E_ValueLineageMap.report.json",
        "PR162E_ExternalCandidateLineage.report.json",
    }
)
_PR162E_Q_COMPUTATION_REPORTS = frozenset(
    {
        *(f"PR162E_Q_{name}.report.json" for name in (
            "MapEligibility", "FormulaObjectiveCanonical", "UnitNorm",
            "ModelFamilySelection", "VariableEncoding", "SolutionInterpretBack",
            "ConstraintMap", "PenaltyMap", "CoeffScaling", "QUBORecipe",
            "BQMRecipe", "IsingRecipe", "CQMRecipe", "DQMRecipe",
            "QuadProgramRecipe", "HybridRecipe", "TestVectors", "MapProof",
            "FeasibilityChecks", "ComplexityEstimate", "SparsityEmbedding",
            "MapQuality", "MapSensitivityStress", "EdgeAttribution",
            "MapFairnessNorm", "ExecutionAdjustedMapRank", "TCAMapImpact",
            "OverfitFDRMapRisk", "PortfolioUtilityMap", "ChampChallengerMap",
            "RegimeMapMemory", "StillNegativeMapRepair", "ReplayPaperRetestMap",
            "OpenTradeSimMap", "OwnerDashboardMapReview", "ConnectorRouteReady",
            "MarketPortability",
        )),
        "PR162E_Q_SourceMapParams.report.json",
        "PR162E_Q_MapBudget.report.json",
    }
)
_GFP_COMPUTATION_REPORTS = frozenset(
    {
        "PR168_GFP_FormulaFamilySearchMatrix.report.json",
        "PR168_GFP_FormulaDiscoveryCoverageAudit.report.json",
        "PR168_GFP_RequiredFormulaSetMap.report.json",
        "PR168_GFP_MasterPlanFormulaCoverageAudit.report.json",
        "PR168_GFP_MasterPlanFormulaToSelectedFormulaCrosswalk.report.json",
        "PR168_GFP_MasterPlanQuantumFormulaCatalog.report.json",
        "PR168_GFP_FormulaAssignmentMatrix.report.json",
        "PR168_GFP_QKUComputationCoverage.report.json",
        "PR168_GFP_CandidatePacketV1ComputationCoverage.report.json",
        "PR168_GFP_AtomicRowsComputationCoverage.report.json",
        "PR168_GFP_CanonicalRowKeyMap.report.json",
    }
)

TOP_LEVEL_REQUIRED = {
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
DEFINITION_REQUIRED = {
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
USES_REQUIRED = {
    "decision_roles",
    "decision_outputs",
    "market_family_tags",
    "qku_role_bindings",
    "consumer_class_tags",
}
BINDING_REQUIRED = {
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
READINESS_REQUIRED = {
    "specification",
    "implementation",
    "inputs",
    "requirements",
    "oracle",
    "context",
    "evidence",
    "authorization",
}
PROVENANCE_REQUIRED = {
    "source_artifact_ref",
    "source_row_ref",
    "source_local_identity_or_name",
    "source_fields_consumed",
    "source_relation",
    "canonical_target_ref",
    "proof_refs",
}
GOVERNANCE_REQUIRED = {
    "producer_owner",
    "validator_refs",
    "reviewer_or_challenger_owner",
    "change_authority",
}
REQUIREMENT_REQUIRED = {
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
RECORD_STATES = {
    "PROVISIONAL",
    "UNDER_REVIEW",
    "CANONICAL_ACCEPTED",
    "SUPERSEDED",
    "DORMANT_PRESERVED",
    "REJECTED_INVALID",
    "INAPPLICABLE_WITH_PROOF",
}
ACCEPTED_STATES = {"CANONICAL_ACCEPTED", "SUPERSEDED", "DORMANT_PRESERVED"}
RUNTIME_ACTIVE_RECORD_STATES = {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"}
DERIVED_STATES = {
    "SPECIFICATION_REQUIRED",
    "SPECIFIED",
    "VERIFIED",
    "CONTEXT_READY",
    "STACK_READY",
    "EVIDENCED",
    "AUTHORIZED",
    "RETIRED",
    "INVALID",
}
SPEC_STATES = {"PASS", "REQUIRED", "INVALID"}
EVIDENCE_STATES = {"NONE", "FIXTURE", "REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}
AUTH_STATES = {"NOT_ELIGIBLE", "ELIGIBLE", "ALLOW_PENDING", "AUTHORIZED"}
RELATION_TYPES = {
    "ALIAS_OF",
    "FAMILY_BINDING_OF",
    "SUCCESSOR_OF",
    "ENCODES_OR_MAPS",
    "DISTINCT_FROM",
    "SUPERSEDES",
}
ALGORITHM_KINDS = {
    "STATISTICAL_ESTIMATOR",
    "STATISTICAL_TEST",
    "OPTIMIZATION_PROGRAM",
    "ALLOCATION_OR_SIZING_POLICY",
    "NUMERICAL_ALGORITHM",
    "SOLVER_PROCEDURE",
    "EXECUTION_POLICY",
    "EXIT_POLICY",
    "QKU_SELECTION_POLICY",
    "COMPUTATION_STACK",
}
PLACEHOLDERS = {"TBD", "SCOPED_GAP", "FUTURE CONSUMER", "METADATA ONLY", "SOLVER COMPATIBLE", "ROUTE LATER", "PLACEHOLDER"}
BULK_KEY_TOKENS = {
    "order_book",
    "raw_fills",
    "fill_ledger",
    "replay_history",
    "replay_rows",
    "trial_rows",
    "bootstrap_samples",
    "qpu_samples",
    "time_series",
    "timeseries",
    "source_document",
    "tca_ledger",
    "campaign_ledger",
}
FORBIDDEN_CALL_TOKENS = {
    "eval",
    "exec",
    "__import__",
    "importlib",
    "pickle",
    "marshal",
    "subprocess",
    "os.system",
    "powershell",
    "cmd.exe",
}
FORBIDDEN_AGENT_OPERATIONS = {
    "compile",
    "write_registry",
    "mutate_registry",
    "activate",
    "authorize",
    "release_order",
    "submit_order",
    "read_private_state",
    "qpu_execute",
    "live_execute",
}
ALLOWED_QUANTUM_CEILINGS = {
    "NONE",
    "SPECIFIED",
    "MAPPED",
    "LOCAL_EXACT_PARITY",
    "CLASSICAL_COMPARATOR_READY",
}
RP5C_ID_RE = re.compile(r"^RP5C_IDENTITY_\d{8}$")
SEMVER_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9._-]+)?$")
CALLABLE_RE = re.compile(r"^(?:src\.)?qtt\.[A-Za-z_][A-Za-z0-9_.]*(?::|\.)[A-Za-z_][A-Za-z0-9_]*$")


class InvariantError(RuntimeError):
    """A named independent invariant failure."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class Deadline:
    def __init__(self, timeout_ms: int) -> None:
        self.started = time.perf_counter()
        self.limit = self.started + max(1, timeout_ms) / 1000.0

    def check(self, where: str) -> None:
        if time.perf_counter() > self.limit:
            raise InvariantError("VALIDATION_TIMEOUT", where)

    @property
    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.started) * 1000)


class Audit:
    def __init__(self, deadline: Deadline) -> None:
        self.deadline = deadline
        self.checks: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}
        self.errors: list[dict[str, str]] = []
        self.error_count = 0

    def fail(self, code: str, detail: str) -> None:
        self.error_count += 1
        if len(self.errors) < 200:
            self.errors.append({"code": code, "detail": detail[:2000]})

    def require(self, name: str, condition: bool, detail: str) -> None:
        self.checks[name] = bool(condition)
        if not condition:
            self.fail(name, detail)

    def capture(self, name: str, function: Callable[[], Any]) -> Any:
        self.deadline.check(name)
        before = self.error_count
        try:
            value = function()
        except InvariantError as exc:
            self.fail(exc.code, exc.detail)
            value = None
        except Exception as exc:  # fail closed, while keeping stdout machine-readable
            self.fail(name, f"{type(exc).__name__}: {exc}")
            value = None
        self.checks[name] = self.error_count == before
        return value


def _plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_plain(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _plain(value.to_dict())
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return {str(key): _plain(item) for key, item in vars(value).items() if not key.startswith("__")}
    return value


def _canonical_json(value: Any, *, strip_volatile: bool = False) -> str:
    volatile = {
        "receipt_id",
        "start_time",
        "end_time",
        "started_at",
        "ended_at",
        "latency_ms",
        "generation",
        "snapshot_generation",
        "trace_id",
    }

    def clean(item: Any) -> Any:
        item = _plain(item)
        if isinstance(item, dict):
            return {
                key: clean(value)
                for key, value in sorted(item.items())
                if not (strip_volatile and key.lower() in volatile)
            }
        if isinstance(item, list):
            return [clean(value) for value in item]
        return item

    return json.dumps(clean(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _rp5c_group_custody_key(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "key_version": RP5C_GROUP_CUSTODY_KEY_VERSION,
        **{field: str(row.get(field) or "") for field in RP5C_GROUP_KEY_FIELDS},
    }


def _rp5c_group_custody_tuple(
    value: Mapping[str, Any], *, code: str = "RP5C_SOURCE_GROUP_KEY_INVALID"
) -> tuple[str, ...]:
    expected = {"key_version", *RP5C_GROUP_KEY_FIELDS}
    if (
        set(value) != expected
        or value.get("key_version") != RP5C_GROUP_CUSTODY_KEY_VERSION
        or any(not isinstance(value.get(field), str) for field in RP5C_GROUP_KEY_FIELDS)
    ):
        raise InvariantError(code, repr(value))
    return tuple(str(value[field]) for field in RP5C_GROUP_KEY_FIELDS)


def _walk(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))


def _forbidden_mapping_key_paths(
    value: Any, forbidden_keys: set[str]
) -> tuple[str, ...]:
    return tuple(
        ".".join(path)
        for path, _ in _walk(value)
        if path and path[-1] in forbidden_keys
    )


def _strings(value: Any) -> Iterator[str]:
    for _, item in _walk(value):
        if isinstance(item, str):
            yield item


def _nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _independent_unresolved_semantic(value: str) -> bool:
    normalized = value.strip().upper()
    if not normalized or normalized in {
            "ANY",
            "TBD",
            "TBC",
            "TODO",
            "UNKNOWN",
            "UNSPECIFIED",
            "UNRESOLVED",
            "NOT_RESOLVED",
            "NOT_SPECIFIED",
            "SPECIFICATION_REQUIRED",
            "TO_BE_DETERMINED",
            "CONTROL_PLANE_TYPED_VALIDATION_REQUIRED",
            "EXACT_RUNTIME_UNIT_REQUIRED",
            "EXACT_RUNTIME_CONTRACT_REQUIRED",
            "EXACT_UNIT_REQUIRED",
            "REQUIRES_CONTEXT_CLASSIFICATION",
        }:
        return True
    tokens = {
        token for token in re.split(r"[^A-Z0-9]+", normalized) if token
    }
    return bool(
        tokens.intersection(
            {
                "TBD",
                "TBC",
                "TODO",
                "UNKNOWN",
                "UNSPECIFIED",
                "UNRESOLVED",
                "PENDING",
            }
        )
    ) or (
        normalized.startswith(
            (
                "TBD",
                "TBC",
                "TODO",
                "UNKNOWN",
                "UNSPECIFIED",
                "UNRESOLVED",
                "MISSING_",
                "REQUIRES_",
                "SOURCE_DECLARED",
                "SOURCE_IMPLEMENTATION",
                "SOURCE_PROCEDURE",
                "EXACT_RUNTIME",
            )
        )
        or "TO_BE_" in normalized
        or normalized.endswith("_REQUIRED")
        or "_REQUIRED_" in normalized
        or "SOURCE_PROCEDURE_DECLARES_OTHERWISE" in normalized
    )


def _independent_unresolved_semantic_key(value: Any) -> bool:
    normalized = str(value).strip().upper()
    if not normalized:
        return True
    tokens = {
        token for token in re.split(r"[^A-Z0-9]+", normalized) if token
    }
    return bool(
        tokens.intersection(
            {
                "TBD",
                "TBC",
                "TODO",
                "UNKNOWN",
                "UNSPECIFIED",
                "UNRESOLVED",
                "PENDING",
            }
        )
        or normalized.startswith(
            ("TBD", "TBC", "TODO", "UNKNOWN", "UNSPECIFIED", "UNRESOLVED")
        )
        or "TO_BE_" in normalized
    )


_INDEPENDENT_NOT_APPLICABLE_PROOF_REFS = {
    "PURE_FORMULA_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
    "TEMPORARY_SCALE_COMPONENT_FAILS_CLOSED",
    "TEST_COMPONENT_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
}


def _independent_explicit_na(value: Any) -> bool:
    proof = value.get("proof_ref", value.get("proof")) if isinstance(value, Mapping) else None
    return (
        isinstance(value, Mapping)
        and value.get("not_applicable") is True
        and isinstance(proof, str)
        and proof.strip() in _INDEPENDENT_NOT_APPLICABLE_PROOF_REFS
    )


def _independent_semantic_value_issues(value: Any, path: str) -> list[str]:
    if value is None:
        return [path]
    if isinstance(value, str):
        return [path] if _independent_unresolved_semantic(value) else []
    if isinstance(value, Mapping):
        if not value:
            return [path]
        if value.get("not_applicable") is True:
            issues = [] if _independent_explicit_na(value) else [f"{path}.proof_ref"]
            for key, item in value.items():
                if key == "not_applicable":
                    continue
                if _independent_unresolved_semantic_key(key):
                    issues.append(f"{path}.{key}.__key__")
                issues.extend(
                    _independent_semantic_value_issues(item, f"{path}.{key}")
                )
            return issues
        issues: list[str] = []
        for key, item in value.items():
            if _independent_unresolved_semantic_key(key):
                issues.append(f"{path}.{key}.__key__")
            issues.extend(
                _independent_semantic_value_issues(item, f"{path}.{key}")
            )
        return issues
    if isinstance(value, (list, tuple)):
        if not value:
            return [path]
        return [
            issue
            for index, item in enumerate(value)
            for issue in _independent_semantic_value_issues(
                item, f"{path}[{index}]"
            )
        ]
    return []


def _independent_schema_type_family(value: Any) -> str | None:
    if not isinstance(value, str) or _independent_unresolved_semantic(value):
        return None
    declared = value.strip().upper().replace(" ", "_")
    if "NUMERIC_OR_SEQUENCE" in declared:
        return "NUMERIC_OR_SEQUENCE"
    if "NUMERIC_OR_STRUCTURE" in declared:
        return "NUMERIC_OR_STRUCTURE"
    if any(token in declared for token in ("ARRAY", "LIST", "SEQUENCE", "TUPLE")):
        return "SEQUENCE"
    if any(
        token in declared
        for token in ("OBJECT", "MAPPING", "DICT", "RECORD", "STRUCTURE")
    ):
        return "MAPPING"
    if "BOOL" in declared:
        return "BOOLEAN"
    if any(
        token in declared
        for token in (
            "STRING",
            "TEXT",
            "IDENTIFIER",
            "DATE",
            "TIME",
            "ENUM",
            "CATEGORY",
        )
    ):
        return "STRING"
    if "INTEGER" in declared or declared == "INT":
        return "INTEGER"
    if any(
        token in declared
        for token in (
            "NUMBER",
            "NUMERIC",
            "DECIMAL",
            "FLOAT",
            "REAL",
            "PROBABILITY",
            "PRICE",
            "CURRENCY",
            "CASH",
            "QUANTITY",
            "RATIO",
            "RATE",
            "SCORE",
            "EDGE",
            "FEE",
            "COST",
            "PNL",
            "VALUE",
        )
    ):
        return "NUMERIC"
    return None


def _independent_specification_issues(
    definition: Mapping[str, Any]
) -> tuple[str, ...]:
    semantic_fields = (
        "complete_mathematical_or_procedural_definition",
        "input_schema",
        "output_schema",
        "units_and_bases",
        "domain_and_boundary_behavior",
        "state_and_time_semantics",
        "missing_stale_nonfinite_behavior",
        "precision_and_rounding",
        "parameter_schema_and_default_provenance",
        "requirements",
        "classical_fallback",
        "risk_materiality",
    )
    issues: list[str] = []
    for field in semantic_fields:
        if field not in definition:
            issues.append(field)
            continue
        value = definition[field]
        if field in {"input_schema", "output_schema"}:
            if not isinstance(value, list):
                issues.append(field)
                continue
            if not value:
                proof_name = (
                    "zero_input_proof" if field == "input_schema" else "zero_output_proof"
                )
                proof = definition.get(proof_name)
                if not isinstance(proof, str) or _independent_unresolved_semantic(
                    proof
                ):
                    issues.append(field)
                continue
            for index, entry in enumerate(value):
                if not isinstance(entry, Mapping):
                    issues.append(f"{field}[{index}]")
                    continue
                for name in ("name", "type"):
                    if name not in entry:
                        issues.append(f"{field}[{index}].{name}")
                if "type" in entry and _independent_schema_type_family(
                    entry.get("type")
                ) is None:
                    issues.append(f"{field}[{index}].type")
                if not any(
                    name in entry
                    for name in ("unit", "units", "unit_or_basis", "basis")
                ):
                    issues.append(f"{field}[{index}].unit_or_basis")
                issues.extend(
                    _independent_semantic_value_issues(
                        entry, f"{field}[{index}]"
                    )
                )
            continue
        if field == "units_and_bases":
            schema_names = {
                str(entry.get("name"))
                for schema_name in ("input_schema", "output_schema")
                for entry in definition.get(schema_name, ())
                if isinstance(entry, Mapping) and entry.get("name")
            }
            zero_ports = all(
                isinstance(definition.get(name), str)
                and not _independent_unresolved_semantic(str(definition[name]))
                for name in ("zero_input_proof", "zero_output_proof")
            )
            if not isinstance(value, Mapping) or (
                not value and (bool(schema_names) or not zero_ports)
            ):
                issues.append(field)
                continue
            if not value and zero_ports:
                continue
            issues.extend(
                f"units_and_bases.{name}"
                for name in sorted(schema_names - {str(key) for key in value})
            )
        if field == "requirements":
            if not isinstance(value, list):
                issues.append(field)
                continue
            for index, requirement in enumerate(value):
                if not isinstance(requirement, Mapping):
                    issues.append(f"requirements[{index}]")
                    continue
                missing = REQUIREMENT_REQUIRED - set(requirement)
                issues.extend(
                    f"requirements[{index}].{name}" for name in sorted(missing)
                )
                for key, item in requirement.items():
                    if key == "required_or_optional" or (
                        key == "fallback_component_id_or_null" and item is None
                    ):
                        continue
                    issues.extend(
                        _independent_semantic_value_issues(
                            item, f"requirements[{index}].{key}"
                        )
                    )
            continue
        if field == "parameter_schema_and_default_provenance":
            if isinstance(value, (list, tuple)) and not value:
                issues.append(field)
                continue
            declared_parameters = value.get("parameters") if isinstance(value, Mapping) else None
            if (
                isinstance(value, Mapping)
                and isinstance(declared_parameters, (Mapping, list, tuple))
                and not declared_parameters
            ):
                provenance = value.get("default_provenance")
                if not isinstance(provenance, str) or _independent_unresolved_semantic(
                    provenance
                ):
                    issues.append(f"{field}.default_provenance")
                for key, item in value.items():
                    if key == "parameters":
                        continue
                    issues.extend(
                        _independent_semantic_value_issues(
                            item, f"{field}.{key}"
                        )
                    )
                continue
        issues.extend(_independent_semantic_value_issues(value, field))
    return tuple(sorted(set(issues)))


def _independent_schema_unit(schema: Mapping[str, Any]) -> str:
    return str(
        schema.get("unit_or_basis")
        or schema.get("unit")
        or schema.get("basis")
        or schema.get("units")
        or ""
    )


def _independent_input_source_binding_issues(
    definition: Mapping[str, Any], binding: Mapping[str, Any]
) -> tuple[str, ...]:
    input_schema = definition.get("input_schema")
    if not isinstance(input_schema, (list, tuple)):
        return ("input_schema",)
    schema_by_name: dict[str, Mapping[str, Any]] = {}
    issues: list[str] = []
    for index, entry in enumerate(input_schema):
        if not isinstance(entry, Mapping):
            issues.append(f"input_schema[{index}]")
            continue
        name = str(entry.get("name", "")).strip()
        if not name:
            issues.append(f"input_schema[{index}].name")
            continue
        if name in schema_by_name:
            issues.append(f"input_schema[{index}].duplicate:{name}")
        schema_by_name[name] = entry

    configured = binding.get("input_source_bindings")
    configured_by_name: dict[str, Any] = {}
    if isinstance(configured, Mapping):
        configured_by_name = {str(key): value for key, value in configured.items()}
    elif isinstance(configured, (list, tuple)):
        for index, entry in enumerate(configured):
            if not isinstance(entry, Mapping):
                issues.append(f"input_source_bindings[{index}]")
                continue
            name = str(entry.get("input_name", entry.get("name")) or "").strip()
            if not name:
                issues.append(f"input_source_bindings[{index}].input_name")
                continue
            if name in configured_by_name:
                issues.append(f"input_source_bindings[{index}].duplicate:{name}")
            configured_by_name[name] = entry
    else:
        return ("input_source_bindings",)

    required_requirements_by_input: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    requirements = definition.get("requirements", ())
    if isinstance(requirements, (list, tuple)):
        for requirement in requirements:
            if not isinstance(requirement, Mapping):
                continue
            if str(requirement.get("required_or_optional", "REQUIRED")).upper() == "OPTIONAL":
                continue
            consumer_input = str(requirement.get("consumer_input_name", "")).strip()
            if consumer_input:
                required_requirements_by_input[consumer_input].append(requirement)

    schema_names = set(schema_by_name)
    configured_names = set(configured_by_name)
    issues.extend(
        f"input_source_bindings.missing:{name}"
        for name in sorted(schema_names - configured_names)
    )
    issues.extend(
        f"input_source_bindings.undeclared:{name}"
        for name in sorted(configured_names - schema_names)
    )
    for name in sorted(schema_names & configured_names):
        schema = schema_by_name[name]
        configured_entry = configured_by_name[name]
        source: Any = configured_entry
        if isinstance(configured_entry, Mapping):
            source = configured_entry.get(
                "source",
                configured_entry.get(
                    "source_ref", configured_entry.get("binding_ref")
                ),
            )
            if str(configured_entry.get("declared_type", "")) != str(
                schema.get("type", "")
            ):
                issues.append(f"input_source_bindings.{name}.declared_type")
            if str(
                configured_entry.get(
                    "unit_or_basis",
                    configured_entry.get("unit", configured_entry.get("basis", "")),
                )
            ) != _independent_schema_unit(schema):
                issues.append(f"input_source_bindings.{name}.unit_or_basis")
            requirements_for_input = required_requirements_by_input.get(name, ())
            binding_state = str(configured_entry.get("binding_state", ""))
            if requirements_for_input:
                targets = {
                    str(requirement.get("required_component_id_or_source_selector", ""))
                    for requirement in requirements_for_input
                }
                if binding_state != "CANONICAL_REQUIREMENT_OUTPUT":
                    issues.append(
                        f"input_source_bindings.{name}.requirement_binding_state"
                    )
                if not isinstance(source, str) or source not in targets:
                    issues.append(
                        f"input_source_bindings.{name}.requirement_component"
                    )
                else:
                    matching = [
                        requirement
                        for requirement in requirements_for_input
                        if str(
                            requirement.get(
                                "required_component_id_or_source_selector", ""
                            )
                        )
                        == source
                    ]
                    producer_output = str(
                        configured_entry.get("producer_output_name", "")
                    )
                    if not any(
                        producer_output
                        == str(requirement.get("producer_output_name", ""))
                        for requirement in matching
                    ):
                        issues.append(
                            f"input_source_bindings.{name}.requirement_output"
                        )
            elif binding_state == "CANONICAL_REQUIREMENT_OUTPUT":
                issues.append(
                    f"input_source_bindings.{name}.unexpected_requirement_binding"
                )
        elif required_requirements_by_input.get(name):
            issues.append(f"input_source_bindings.{name}.requirement_binding_shape")
        if isinstance(source, str):
            if _independent_unresolved_semantic(source):
                issues.append(f"input_source_bindings.{name}.source_ref")
        elif isinstance(source, (Mapping, list, tuple)):
            issues.extend(
                _independent_semantic_value_issues(
                    source, f"input_source_bindings.{name}.source_ref"
                )
            )
        else:
            issues.append(f"input_source_bindings.{name}.source_ref")
    return tuple(sorted(set(issues)))


def _independent_fixture_number_issue(value: Any) -> str | None:
    if isinstance(value, bool) or isinstance(value, float):
        return f"non_exact_numeric_type:{type(value).__name__}"
    if isinstance(value, int):
        return None
    if isinstance(value, Decimal):
        return None if value.is_finite() else "nonfinite_decimal"
    return f"unsupported_numeric_type:{type(value).__name__}"


def _read_pr162d_fixture_rows(
    repo_root: Path,
) -> dict[str, Mapping[str, Any]]:
    path = repo_root / PR162D_TEST_VECTOR_REGISTRY
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(
                handle,
                parse_float=Decimal,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    InvariantError(
                        "CLOSED_FIXTURE_SOURCE_NONFINITE", str(value)
                    )
                ),
            )
    except OSError as exc:
        raise InvariantError(
            "CLOSED_FIXTURE_SOURCE_UNRESOLVED", f"{path}: {exc}"
        ) from exc
    rows = payload.get("records") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise InvariantError(
            "CLOSED_FIXTURE_SOURCE_UNRESOLVED", f"{path}: records"
        )
    by_ref: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise InvariantError(
                "CLOSED_FIXTURE_SOURCE_UNRESOLVED", f"row {index}"
            )
        fixture_ref = row.get("test_vector_id")
        if not isinstance(fixture_ref, str) or not fixture_ref:
            raise InvariantError(
                "CLOSED_FIXTURE_SOURCE_UNRESOLVED", f"row {index}: test_vector_id"
            )
        if fixture_ref in by_ref:
            raise InvariantError(
                "CLOSED_FIXTURE_SOURCE_UNRESOLVED", f"duplicate {fixture_ref}"
            )
        by_ref[fixture_ref] = row
    return by_ref


def _independent_closed_fixture_contract_issues(
    record: Mapping[str, Any],
    source_row: Mapping[str, Any] | None,
    records_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    """Reconstruct one closed source fixture contract without builder metadata."""

    component_id = str(record.get("canonical_component_id", ""))
    if component_id not in _CLOSED_FIXTURE_COMPONENTS:
        return ("component_not_fixture_allowlisted",)
    fixture_ref = (
        "PR162D_R2A_TV_FORMULA::" + component_id.removeprefix(
            "QTT.COMP.FORMULA."
        )
    )
    issues: list[str] = []
    definition = record.get("definition")
    if not isinstance(definition, Mapping):
        return ("definition",)
    bindings = record.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 1 or not isinstance(
        bindings[0], Mapping
    ):
        return ("binding",)
    binding = bindings[0]
    if not isinstance(source_row, Mapping) or source_row.get("test_vector_id") != fixture_ref:
        issues.append("source_fixture_unresolved")
        return tuple(issues)
    if source_row.get("live_order_authority") is not False:
        issues.append("source_live_authority")

    formula_id = component_id.removeprefix("QTT.COMP.FORMULA.")
    try:
        from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library import (
            formula_specs as source_formula_specs,
        )

        source_spec = next(
            spec
            for spec in source_formula_specs()
            if str(spec.formula_id) == formula_id
        )
    except (ImportError, StopIteration) as exc:
        issues.append(f"source_formula_owner_unresolved:{type(exc).__name__}")
        source_spec = None

    implementations = {
        _implementation_ref(entry)
        for entry in definition.get("implementation_versions", ())
        if isinstance(entry, Mapping)
    }
    if source_row.get("callable_ref") not in implementations:
        issues.append("source_callable_unregistered")
    input_schema = _schema_specs(definition.get("input_schema", ()))
    output_schema = _schema_specs(definition.get("output_schema", ()))
    source_inputs = source_row.get("inputs")
    source_outputs = source_row.get("expected_outputs")
    if not isinstance(source_inputs, Mapping):
        issues.append("source_inputs_invalid")
        source_inputs = {}
    if set(source_inputs) != set(input_schema):
        issues.append("source_input_ports")
    if not isinstance(source_outputs, Mapping):
        issues.append("source_outputs_invalid")
        source_outputs = {}
    if set(source_outputs) != set(output_schema):
        issues.append("source_output_ports")

    def exact_source_decimal(value: Any) -> Decimal | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None
        return parsed if parsed.is_finite() else None

    if source_spec is not None:
        if source_row.get("callable_ref") != source_spec.callable_ref:
            issues.append("source_callable_owner_mismatch")
        for name in sorted(set(source_inputs) | set(source_spec.test_inputs)):
            if (
                name not in source_inputs
                or name not in source_spec.test_inputs
                or exact_source_decimal(source_inputs[name])
                != exact_source_decimal(source_spec.test_inputs[name])
            ):
                issues.append(f"source_input_value_mismatch:{name}")
        try:
            source_recomputed = source_spec.compute(
                copy.deepcopy(dict(source_spec.test_inputs))
            )
        except Exception as exc:
            issues.append(f"source_fixture_recompute_failed:{type(exc).__name__}")
            source_recomputed = {}
        if not isinstance(source_recomputed, Mapping):
            issues.append("source_fixture_recompute_invalid")
            source_recomputed = {}
        for name in sorted(set(source_outputs) | set(source_recomputed)):
            if (
                name not in source_outputs
                or name not in source_recomputed
                or exact_source_decimal(source_outputs[name])
                != exact_source_decimal(source_recomputed[name])
            ):
                issues.append(f"source_output_value_mismatch:{name}")
    for name, value in source_inputs.items():
        numeric_issue = _independent_fixture_number_issue(value)
        if numeric_issue:
            issues.append(f"source_input_value:{name}:{numeric_issue}")
        schema = input_schema.get(str(name), {})
        if str(schema.get("type", "")) != "FINITE_DECIMAL_COMPATIBLE_SCALAR":
            issues.append(f"source_input_type:{name}")
        if not _independent_schema_unit(schema):
            issues.append(f"source_input_unit:{name}")
    for name, value in source_outputs.items():
        numeric_issue = _independent_fixture_number_issue(value)
        if numeric_issue:
            issues.append(f"source_output_value:{name}:{numeric_issue}")
        schema = output_schema.get(str(name), {})
        if str(schema.get("type", "")) != "FINITE_DECIMAL_COMPATIBLE_SCALAR":
            issues.append(f"source_output_type:{name}")
        if not _independent_schema_unit(schema):
            issues.append(f"source_output_unit:{name}")

    issues.extend(_independent_input_source_binding_issues(definition, binding))
    required_by_input: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for requirement in definition.get("requirements", ()):
        if not isinstance(requirement, Mapping):
            continue
        if str(requirement.get("required_or_optional", "REQUIRED")).upper() == "OPTIONAL":
            continue
        required_by_input[str(requirement.get("consumer_input_name", ""))].append(
            requirement
        )
    configured_by_input = {
        str(entry.get("input_name", "")): entry
        for entry in binding.get("input_source_bindings", ())
        if isinstance(entry, Mapping) and entry.get("input_name")
    }
    for input_name in sorted(input_schema):
        configured = configured_by_input.get(input_name)
        if not isinstance(configured, Mapping):
            continue
        if required_by_input.get(input_name):
            if configured.get("binding_state") != "CANONICAL_REQUIREMENT_OUTPUT":
                issues.append(f"requirement_binding_state:{input_name}")
            if "fixture_evidence_ref" in configured:
                issues.append(f"requirement_mislabeled_as_fixture:{input_name}")
        else:
            if configured.get("binding_state") != "EXACT_TYPED_REQUEST_INPUT_LOCK":
                issues.append(f"direct_binding_state:{input_name}")
            if configured.get("source_ref") != (
                "QKUComputationControlPlaneV1.compute.inputs::" + input_name
            ):
                issues.append(f"direct_source_ref:{input_name}")
            if configured.get("fixture_evidence_ref") != fixture_ref:
                issues.append(f"direct_fixture_ref:{input_name}")
    for input_name, requirements in required_by_input.items():
        if len(requirements) != 1:
            issues.append(f"requirement_ambiguous:{input_name}")
            continue
        requirement = requirements[0]
        target_id = str(
            requirement.get("required_component_id_or_source_selector", "")
        )
        target = records_by_id.get(target_id)
        if not isinstance(target, Mapping):
            issues.append(f"requirement_target_unresolved:{input_name}")
            continue
        producer_outputs = _schema_specs(
            target.get("definition", {}).get("output_schema", ())
        )
        producer_name = str(requirement.get("producer_output_name", ""))
        producer = producer_outputs.get(producer_name)
        consumer = input_schema.get(input_name)
        if not isinstance(producer, Mapping) or not isinstance(consumer, Mapping):
            issues.append(f"requirement_port_unresolved:{input_name}")
            continue
        if str(producer.get("type", "")) != str(consumer.get("type", "")):
            issues.append(f"requirement_type_mismatch:{input_name}")
        if (
            requirement.get("unit_or_basis_conversion") == "IDENTITY"
            and _independent_schema_unit(producer)
            != _independent_schema_unit(consumer)
        ):
            issues.append(f"requirement_unit_mismatch:{input_name}")

    readiness = binding.get("readiness", {})
    for dimension in (
        "specification",
        "implementation",
        "inputs",
        "requirements",
        "oracle",
        "context",
    ):
        if readiness.get(dimension) != "PASS":
            issues.append(f"readiness_not_pass:{dimension}")
    evidence = binding.get("evidence_summary", {})
    if not isinstance(evidence, Mapping) or evidence.get("fixture_ref") != fixture_ref:
        issues.append("binding_fixture_ref")
    operations = _independent_policy_operations(binding.get("agent_access_policy"))
    if not {"resolve", "compute"}.issubset(operations):
        issues.append("agent_compute_missing")
    return tuple(sorted(set(issues)))


def _validate_closed_fixture_source_contracts(
    repo_root: Path, records: Sequence[Mapping[str, Any]]
) -> dict[str, int]:
    rows = _read_pr162d_fixture_rows(repo_root)
    records_by_id = {
        str(record.get("canonical_component_id", "")): record for record in records
    }
    for component_id in sorted(_CLOSED_FIXTURE_COMPONENTS):
        record = records_by_id.get(component_id)
        fixture_ref = (
            "PR162D_R2A_TV_FORMULA::"
            + component_id.removeprefix("QTT.COMP.FORMULA.")
        )
        if not isinstance(record, Mapping):
            raise InvariantError("CLOSED_FIXTURE_RECORD_MISSING", component_id)
        issues = _independent_closed_fixture_contract_issues(
            record, rows.get(fixture_ref), records_by_id
        )
        if issues:
            raise InvariantError(
                "CLOSED_FIXTURE_CONTRACT", f"{component_id}: {list(issues)}"
            )

    fixture_ready_pr162d: set[str] = set()
    for record in records:
        if "PR162D_IMPLEMENTATION_BACKED" not in {
            str(value) for value in record.get("origin_cohorts", ())
        }:
            continue
        for binding in record.get("bindings", ()):
            if not isinstance(binding, Mapping):
                continue
            readiness = binding.get("readiness", {})
            if (
                readiness.get("inputs") == "PASS"
                or readiness.get("context") == "PASS"
            ):
                fixture_ready_pr162d.add(
                    str(record.get("canonical_component_id", ""))
                )
    if fixture_ready_pr162d != set(_CLOSED_FIXTURE_COMPONENTS):
        raise InvariantError(
            "CLOSED_FIXTURE_READY_SET",
            f"observed={sorted(fixture_ready_pr162d)!r}",
        )
    return {
        "source_resolved_contracts": len(_CLOSED_FIXTURE_COMPONENTS),
        "direct_and_requirement_owned_ports_classified": sum(
            len(records_by_id[component_id]["definition"]["input_schema"])
            for component_id in _CLOSED_FIXTURE_COMPONENTS
        ),
        "persisted_fixture_vectors": 0,
    }


def _independent_policy_operations(policy: Any) -> set[str]:
    operations: set[str] = set()
    if isinstance(policy, Mapping):
        values = policy.get(
            "control_plane_operations", policy.get("allowed_operations")
        )
        if isinstance(values, list):
            operations.update(str(value) for value in values)
        for value in policy.values():
            if isinstance(value, (Mapping, list)):
                operations.update(_independent_policy_operations(value))
    elif isinstance(policy, list):
        for value in policy:
            operations.update(_independent_policy_operations(value))
    return operations


def _require_keys(value: Any, required: set[str], code: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvariantError(code, f"{label} must be an object")
    missing = sorted(required - set(value))
    if missing:
        raise InvariantError(code, f"{label} missing {missing}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InvariantError("REGISTRY_JSON_INVALID", f"{path}:{line_number}: {exc}") from exc
            if not isinstance(row, dict):
                raise InvariantError("REGISTRY_ROW_NOT_OBJECT", f"{path}:{line_number}")
            rows.append(row)
    return rows


def _closure_read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InvariantError("SOURCE_CLOSURE_MISSING", path.as_posix())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvariantError("SOURCE_CLOSURE_JSON", f"{path.as_posix()}: {exc}") from exc
    if not isinstance(value, dict):
        raise InvariantError("SOURCE_CLOSURE_JSON", f"{path.as_posix()}: root is not an object")
    return value


def _closure_declared_count(
    payload: Mapping[str, Any], path: Path, *, shard_local: bool = False
) -> int:
    # A shard can also carry the root total.  Its local record_count/row_count
    # is therefore authoritative for the physical rows in that shard.
    fields = (
        ("record_count", "row_count", "total_record_count", "total_row_count")
        if shard_local
        else ("total_record_count", "total_row_count", "record_count", "row_count")
    )
    for field in fields:
        value = payload.get(field)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    raise InvariantError(
        "SOURCE_CLOSURE_DECLARED_COUNT", f"{path.as_posix()}: no integer declared count"
    )


def _closure_declared_shards(payload: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for owner in (payload, payload.get("summary")):
        if not isinstance(owner, Mapping):
            continue
        for field in ("shard_files", "shard_paths"):
            candidate = owner.get(field, [])
            if isinstance(candidate, str):
                candidate = [candidate]
            if isinstance(candidate, list):
                values.extend(
                    str(item) for item in candidate if isinstance(item, str) and item
                )
    return tuple(dict.fromkeys(values))


def _closure_read_rows(
    repo_root: Path, relative_path: str, deadline: Deadline
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read actual rows from one current owner, never a count/preview substitute."""

    relative = Path(relative_path)
    path = (repo_root / relative).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise InvariantError("SOURCE_CLOSURE_PATH_ESCAPE", relative_path) from exc

    if path.suffix.lower() == ".jsonl":
        if not path.is_file():
            raise InvariantError("SOURCE_CLOSURE_MISSING", relative_path)
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, 1):
                if line_number % 1_000 == 0:
                    deadline.check(f"source closure {relative.name}")
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InvariantError(
                        "SOURCE_CLOSURE_JSON",
                        f"{relative_path}:{line_number}: {exc}",
                    ) from exc
                if not isinstance(row, dict):
                    raise InvariantError(
                        "SOURCE_CLOSURE_ROW_SHAPE", f"{relative_path}:{line_number}"
                    )
                rows.append(row)
        manifest_candidates = (
            path.with_name(f"{path.name}.manifest.json"),
            path.with_suffix(".manifest.json"),
        )
        manifest_path = next(
            (candidate for candidate in manifest_candidates if candidate.is_file()), None
        )
        if manifest_path is None:
            raise InvariantError(
                "SOURCE_CLOSURE_MANIFEST_MISSING", relative_path
            )
        manifest = _closure_read_json(manifest_path)
        declared = _closure_declared_count(manifest, manifest_path)
        if len(rows) != declared:
            raise InvariantError(
                "SOURCE_CLOSURE_DENOMINATOR",
                f"{relative_path}: actual={len(rows)} declared={declared}",
            )
        return rows, {
            "declared_rows": declared,
            "actual_rows_read": len(rows),
            "physical_files_read": [
                relative.as_posix(),
                manifest_path.relative_to(repo_root).as_posix(),
            ],
            "preview_rows_ignored": 0,
            "manifest_count_used_as_value_consumption": False,
        }

    root = _closure_read_json(path)
    declared = _closure_declared_count(root, path)
    root_records = root.get("records", [])
    if not isinstance(root_records, list):
        raise InvariantError("SOURCE_CLOSURE_ROW_SHAPE", f"{relative_path}: records")
    shard_names = _closure_declared_shards(root)
    rows = []
    files = [relative.as_posix()]
    preview_ignored = 0
    if shard_names:
        preview_ignored = len(root_records)
        seen: set[str] = set()
        for shard_name in shard_names:
            raw = Path(shard_name)
            shard_path = raw if raw.is_absolute() else repo_root / raw
            shard_path = shard_path.resolve()
            try:
                shard_relative = shard_path.relative_to(repo_root.resolve()).as_posix()
            except ValueError as exc:
                raise InvariantError(
                    "SOURCE_CLOSURE_PATH_ESCAPE", shard_name
                ) from exc
            if shard_relative in seen:
                raise InvariantError("SOURCE_CLOSURE_SHARD_DUPLICATE", shard_relative)
            seen.add(shard_relative)
            shard = _closure_read_json(shard_path)
            shard_rows = shard.get("records", [])
            if not isinstance(shard_rows, list) or any(
                not isinstance(row, dict) for row in shard_rows
            ):
                raise InvariantError(
                    "SOURCE_CLOSURE_ROW_SHAPE", f"{shard_relative}: records"
                )
            shard_declared = _closure_declared_count(
                shard, shard_path, shard_local=True
            )
            if len(shard_rows) != shard_declared:
                raise InvariantError(
                    "SOURCE_CLOSURE_SHARD_DENOMINATOR",
                    f"{shard_relative}: actual={len(shard_rows)} declared={shard_declared}",
                )
            rows.extend(shard_rows)
            files.append(shard_relative)
            deadline.check(f"source closure shard {Path(shard_relative).name}")
    else:
        if any(not isinstance(row, dict) for row in root_records):
            raise InvariantError(
                "SOURCE_CLOSURE_ROW_SHAPE", f"{relative_path}: records"
            )
        rows.extend(root_records)
    if len(rows) != declared:
        raise InvariantError(
            "SOURCE_CLOSURE_DENOMINATOR",
            f"{relative_path}: actual={len(rows)} declared={declared}",
        )
    return rows, {
        "declared_rows": declared,
        "actual_rows_read": len(rows),
        "physical_files_read": files,
        "preview_rows_ignored": preview_ignored,
        "manifest_count_used_as_value_consumption": False,
    }


def _independent_source_row_key_field(
    rows: Sequence[Mapping[str, Any]], relative_path: str
) -> str:
    """Choose an existing unique owner key without manufacturing identity."""

    if not rows:
        return "__EMPTY_OWNER_SURFACE__"
    fields = sorted({str(field) for row in rows for field in row})
    ordered = sorted(
        fields,
        key=lambda field: (
            0 if field in {"row_id", "record_id", "canonical_row_key"}
            else 1 if field.endswith(("_row_id", "_record_id"))
            else 2 if field.endswith("_id")
            else 3 if field.endswith("_ref")
            else 4,
            field,
        ),
    )
    for field in ordered:
        if field in {"run_id", "created_by_pr"}:
            continue
        values = [str(row.get(field, "") or "") for row in rows]
        if all(values) and len(values) == len(set(values)):
            return field
    raise InvariantError(
        "SOURCE_CLOSURE_STABLE_OWNER_KEY",
        f"{relative_path}: no existing non-hash unique row key",
    )


def _independent_validate_owner_projection_row(
    row: Mapping[str, Any],
    *,
    path: str,
    row_key: str,
    canonical_provenance_targets: Iterable[str],
    reject_hash_authority: bool,
) -> None:
    targets = sorted(set(canonical_provenance_targets))
    if targets:
        raise InvariantError(
            "SOURCE_OWNER_PROJECTION_FALSE_CANONICAL_ADMISSION",
            f"{path}:{row_key} -> {targets}",
        )
    if not reject_hash_authority:
        return
    forbidden: list[str] = []
    for field_path, value in _walk(row):
        field = field_path[-1] if field_path else ""
        if (
            any(token in field.casefold() for token in ("sha", "hash", "digest"))
            and value not in (0, False, None, "", [], {})
        ):
            forbidden.append(".".join(field_path))
    if forbidden:
        raise InvariantError(
            "SOURCE_OWNER_HASH_DIGEST_AUTHORITY",
            f"{path}:{row_key}: {sorted(forbidden)}",
        )


def _independent_declared_rows(repo_root: Path, relative_path: str) -> int:
    path = repo_root / relative_path
    if path.suffix.lower() == ".jsonl":
        candidates = (
            path.with_name(f"{path.name}.manifest.json"),
            path.with_suffix(".manifest.json"),
        )
        manifest = next((item for item in candidates if item.is_file()), None)
        if manifest is None:
            raise InvariantError("SOURCE_CLOSURE_MANIFEST_MISSING", relative_path)
        return _closure_declared_count(_closure_read_json(manifest), manifest)
    return _closure_declared_count(_closure_read_json(path), path)


def _independent_source_closure_artifacts(
    repo_root: Path, deadline: Deadline
) -> tuple[tuple[dict[str, Any], ...], list[dict[str, Any]]]:
    """Discover the complete current computation-bearing owner surface.

    Discovery is deliberately separate from builder constants.  Every owner
    manifest/report in the declared families is assigned either to the
    row-level closure or to a named generic/transitive exclusion.  This makes
    a newly added or omitted owner surface visible instead of silently relying
    on a historical count.
    """

    root_specs = [dict(spec) for spec in SOURCE_CLOSURE_ARTIFACTS]
    root_paths = {str(spec["path"]) for spec in root_specs}
    generated = repo_root / "docs/master_plan/generated"
    candidates: dict[str, list[Path]] = {
        "MAP3": sorted((generated / "map3").glob("*.manifest.json")),
        "RP5D": sorted((generated / "pr168_rp5d").glob("*.manifest.json")),
        "RP5D_R1": sorted((generated / "pr168_rp5d_r1").glob("*.manifest.json")),
        "RP5E": sorted((generated / "pr168_rp5e").glob("*.manifest.json")),
        "PR162B": sorted(generated.glob("PR162B_*.report.json")),
        "PR162D": sorted(generated.glob("PR162D_R2A_*.report.json")),
        "PR162E": sorted(
            path
            for path in generated.glob("PR162E_*.report.json")
            if not path.name.startswith("PR162E_Q_")
        ),
        "QUANTUM_559": sorted(generated.glob("PR162E_Q_*.report.json")),
        "GFP": sorted(generated.glob("PR168_GFP_*.report.json")),
    }
    report_sets = {
        "PR162B": _PR162B_COMPUTATION_REPORTS,
        "PR162D": _PR162D_COMPUTATION_REPORTS,
        "PR162E": _PR162E_COMPUTATION_REPORTS,
        "QUANTUM_559": _PR162E_Q_COMPUTATION_REPORTS,
        "GFP": _GFP_COMPUTATION_REPORTS,
    }
    additions: list[dict[str, Any]] = []
    manifest_split: list[dict[str, Any]] = []
    for group, paths in candidates.items():
        included: list[tuple[str, int]] = []
        excluded: list[str] = []
        row_bearing_entries = 0
        for index, source_path in enumerate(paths):
            if index % 100 == 0:
                deadline.check(f"source owner discovery {group}")
            if source_path.name.endswith(".manifest.json"):
                logical_name = source_path.name.removesuffix(".manifest.json")
                logical_path = source_path.with_name(
                    logical_name
                    if logical_name.endswith(".jsonl")
                    else logical_name + ".jsonl"
                )
                payload = _closure_read_json(source_path)
                declared = _closure_declared_count(payload, source_path)
            else:
                try:
                    payload = _closure_read_json(source_path)
                    declared = _closure_declared_count(payload, source_path)
                except InvariantError:
                    # Summary-only reports are still classified by their owner,
                    # but they have no row-level computation denominator.
                    continue
                if not isinstance(payload.get("records", []), list):
                    continue
                logical_path = source_path
            row_bearing_entries += 1
            relative = logical_path.relative_to(repo_root).as_posix()
            include = False
            disposition = "SOURCE_OWNER_CONTEXT_OR_EVIDENCE_PROJECTION"
            role = "OWNER_PROJECTION"
            if relative in root_paths:
                include = False
            elif group == "MAP3":
                include = True
                disposition = "SOURCE_OWNER_SEMANTIC_PROJECTION"
            elif group == "RP5D":
                include = logical_path.name not in _RP5D_NON_COMPUTATION_MANIFESTS
                disposition = "SOURCE_OWNER_CONTEXTUAL_READINESS_PROJECTION"
            elif group == "RP5D_R1":
                include = logical_path.name in _RP5D_R1_COMPUTATION_SURFACES
                disposition = (
                    "SOURCE_READINESS_BLOCKER_RETAINED_WITH_OWNER"
                    if logical_path.name == "source_req.jsonl"
                    else "SOURCE_OWNER_CONTEXTUAL_BINDING_OR_EVIDENCE_PROJECTION"
                )
                role = "OWNER_CONTEXT" if logical_path.name == "source_req.jsonl" else role
            elif group == "RP5E":
                include = logical_path.name in _RP5E_COMPUTATION_SURFACES
                disposition = "SOURCE_OWNER_POLICY_OR_CONTEXT_PROJECTION"
            else:
                include = logical_path.name in report_sets[group]
                disposition = {
                    "PR162B": "SOURCE_OWNER_QKU_SEMANTIC_PROJECTION",
                    "PR162D": "SOURCE_OWNER_IMPLEMENTATION_OR_CONTEXT_PROJECTION",
                    "PR162E": "SOURCE_OWNER_PLUGIN_PROJECTION",
                    "QUANTUM_559": "SOURCE_OWNER_QUANTUM_MAPPING_PROJECTION",
                    "GFP": "SOURCE_OWNER_DISCOVERY_CROSSWALK_PROJECTION",
                }[group]
            if relative in root_paths:
                continue
            if include:
                additions.append(
                    {
                        "cohort": (
                            "RP5D_R1_OWNER_CONTEXT"
                            if group == "RP5D_R1"
                            and logical_path.name == "source_req.jsonl"
                            else group
                        ),
                        "path": relative,
                        "role": role,
                        "expected": declared,
                        "key": "",
                        "projection_disposition": disposition,
                    }
                )
                included.append((relative, declared))
            else:
                excluded.append(relative)
        manifest_split.append(
            {
                "owner_group": group,
                "row_bearing_manifest_or_report_entries": row_bearing_entries,
                "independently_included_owner_projection_entries": len(included),
                "independently_included_physical_rows": sum(
                    rows for _, rows in included
                ),
                "generic_transitive_or_duplicate_owner_entries": len(excluded),
                "generic_transitive_or_duplicate_owner_paths": sorted(excluded),
                "exclusion_reason": (
                    "GENERIC_ROUTE_AUDIT_OR_DUPLICATE_TRANSITIVE_OWNER_"
                    "PROJECTION_WITHOUT_ADDITIONAL_COMPUTATION_SEMANTICS"
                ),
                "unclassified_manifest_entries": 0,
            }
        )
    specs = tuple(root_specs + sorted(additions, key=lambda item: str(item["path"])))
    paths = [str(spec["path"]) for spec in specs]
    if len(paths) != len(set(paths)):
        raise InvariantError("SOURCE_CLOSURE_DUPLICATE_ARTIFACT", "duplicate path")
    # Current-equivalent denominator locks derived independently from owner
    # manifests.  Drift requires deliberate reclassification, not a count edit.
    expected_group_denominators = {
        "MAP3": (63, 3_301),
        "RP5D": (55, 133_233),
        "RP5D_R1": (27, 873),
        "RP5D_R1_OWNER_CONTEXT": (1, 15),
        "RP5E": (24, 791),
        "PR162B": (29, 86_519),
        "PR162D": (24, 28_369),
        "PR162E": (25, 8_777),
        "QUANTUM_559": (40, 21_255),
        "GFP": (13, 92_560),
    }
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in specs:
        by_group[str(spec["cohort"])].append(spec)
    for group, (expected_artifacts, expected_rows) in expected_group_denominators.items():
        observed = by_group[group]
        actual = (len(observed), sum(int(spec["expected"]) for spec in observed))
        if actual != (expected_artifacts, expected_rows):
            raise InvariantError(
                "SOURCE_CLOSURE_OWNER_DENOMINATOR",
                f"{group}: {actual} != {(expected_artifacts, expected_rows)}",
            )
    r1_current_equivalent = [
        spec
        for spec in specs
        if str(spec["cohort"])
        in {"RP5D_R1", "RP5D_R1_OWNER_CONTEXT", "FIXTURE_5"}
    ]
    r1_denominator = (
        len(r1_current_equivalent),
        sum(int(spec["expected"]) for spec in r1_current_equivalent),
    )
    if r1_denominator != (29, 893):
        raise InvariantError(
            "SOURCE_CLOSURE_RP5D_R1_CURRENT_EQUIVALENT_DENOMINATOR",
            f"{r1_denominator} != (29, 893); calc_smoke must remain explicit",
        )
    return specs, manifest_split


def _manifest_files(manifest: Mapping[str, Any]) -> list[str]:
    candidates = manifest.get("shards") or manifest.get("partitions") or manifest.get("files")
    if not isinstance(candidates, list):
        raise InvariantError("SHARD_MANIFEST_INVALID", "manifest has no shards/partitions list")
    names: list[str] = []
    for item in candidates:
        if isinstance(item, str):
            name = item
        elif isinstance(item, Mapping):
            name = next(
                (
                    str(item[key])
                    for key in ("file_name", "filename", "file", "path", "shard_file")
                    if _nonempty(item.get(key))
                ),
                "",
            )
        else:
            name = ""
        if not name:
            raise InvariantError("SHARD_MANIFEST_INVALID", f"invalid shard entry {item!r}")
        names.append(name)
    if len(names) != len(set(names)):
        raise InvariantError("SHARD_MANIFEST_DUPLICATE", "manifest repeats a shard")
    return names


def _validate_manifest_declared_ranges(
    artifact_dir: Path, manifest: Mapping[str, Any]
) -> None:
    """Independently prove every shard row lies in its declared canonical range."""

    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise InvariantError(
            "SHARD_MANIFEST_DECLARED_RANGE", "manifest has no partitions"
        )
    resolved_root = artifact_dir.resolve()
    for partition in partitions:
        if not isinstance(partition, Mapping):
            raise InvariantError(
                "SHARD_MANIFEST_DECLARED_RANGE", "partition is not an object"
            )
        file_name = partition.get("file")
        range_start = partition.get("range_start")
        range_end = partition.get("range_end")
        if not all(
            isinstance(value, str) and bool(value)
            for value in (file_name, range_start, range_end)
        ) or str(range_start) > str(range_end):
            raise InvariantError(
                "SHARD_MANIFEST_DECLARED_RANGE", f"invalid partition: {partition!r}"
            )
        shard_path = (artifact_dir / str(file_name)).resolve()
        try:
            shard_path.relative_to(resolved_root)
        except ValueError as exc:
            raise InvariantError(
                "SHARD_MANIFEST_DECLARED_RANGE", str(file_name)
            ) from exc
        if not shard_path.is_file():
            raise InvariantError(
                "SHARD_MANIFEST_DECLARED_RANGE", f"missing shard: {file_name}"
            )
        observed_rows = 0
        with shard_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                observed_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InvariantError(
                        "SHARD_MANIFEST_DECLARED_RANGE",
                        f"{file_name}:{line_number}: invalid JSON",
                    ) from exc
                component_id = (
                    row.get("canonical_component_id")
                    if isinstance(row, Mapping)
                    else None
                )
                if not isinstance(component_id, str) or not (
                    str(range_start) <= component_id <= str(range_end)
                ):
                    raise InvariantError(
                        "SHARD_MANIFEST_DECLARED_RANGE",
                        f"{file_name}:{line_number}: {component_id!r} outside "
                        f"[{range_start!r}, {range_end!r}]",
                    )
        row_count = partition.get("row_count")
        if (
            isinstance(row_count, bool)
            or not isinstance(row_count, int)
            or row_count != observed_rows
        ):
            raise InvariantError(
                "SHARD_MANIFEST_DECLARED_RANGE",
                f"{file_name}: declared rows={row_count!r}, observed={observed_rows}",
            )


def _detect_layout(artifact_dir: Path) -> tuple[str, list[Path], Mapping[str, Any] | None]:
    single = artifact_dir / "registry.jsonl"
    manifest_path = artifact_dir / "registry.manifest.json"
    shards = sorted(artifact_dir.glob("registry.part-*.jsonl"), key=lambda path: path.name)
    single_active = single.is_file()
    sharded_active = manifest_path.is_file() or bool(shards)
    if single_active == sharded_active:
        raise InvariantError(
            "ACTIVE_LAYOUT_COUNT",
            f"single={single_active}, manifest={manifest_path.is_file()}, shard_count={len(shards)}",
        )
    if single_active:
        return "SINGLE", [single], None
    if not manifest_path.is_file() or not shards:
        raise InvariantError("SHARDED_LAYOUT_INCOMPLETE", "manifest and at least one shard are both required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise InvariantError("SHARD_MANIFEST_INVALID", "manifest root is not an object")
    for path, value in _walk(manifest):
        key = path[-1].lower() if path else ""
        if any(token in key for token in ("hash", "sha", "checksum", "digest")):
            raise InvariantError("QTT_DIGEST_AUTHORITY", f"manifest key {'.'.join(path)}")
        if isinstance(value, str) and ("sha256" in value.lower() or "checksum" in value.lower()):
            raise InvariantError("QTT_DIGEST_AUTHORITY", f"manifest value at {'.'.join(path)}")
    declared = _manifest_files(manifest)
    resolved: list[Path] = []
    for name in declared:
        candidate = (artifact_dir / name).resolve()
        try:
            candidate.relative_to(artifact_dir.resolve())
        except ValueError as exc:
            raise InvariantError("SHARD_PATH_ESCAPE", name) from exc
        if not candidate.is_file():
            raise InvariantError("SHARD_MISSING", name)
        resolved.append(candidate)
    actual = {path.resolve() for path in shards}
    if set(resolved) != actual:
        raise InvariantError(
            "SHARD_MANIFEST_MISMATCH",
            f"declared={sorted(path.name for path in resolved)}, actual={sorted(path.name for path in actual)}",
        )
    _validate_manifest_declared_ranges(artifact_dir, manifest)
    return "SHARDED", resolved, manifest


def _validate_canonical_artifact_surface(
    artifact_dir: Path, layout: str, registry_files: Sequence[Path]
) -> None:
    if not artifact_dir.is_dir():
        raise InvariantError("CANONICAL_ARTIFACT_SURFACE", f"missing directory: {artifact_dir}")
    children = list(artifact_dir.iterdir())
    directories = sorted(path.name for path in children if path.is_dir())
    if directories:
        raise InvariantError("CANONICAL_ARTIFACT_SURFACE", f"unexpected directories: {directories}")
    expected = {path.name for path in registry_files} | {"acceptance.report.json"}
    if layout == "SHARDED":
        expected.add("registry.manifest.json")
    actual = {path.name for path in children if path.is_file()}
    if actual != expected:
        raise InvariantError(
            "CANONICAL_ARTIFACT_SURFACE",
            f"layout={layout}, missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}",
        )


def _unwrap_records(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, (list, tuple)) and all(isinstance(row, Mapping) for row in value):
        if not value or all("canonical_component_id" in row for row in value):
            return [row if isinstance(row, dict) else dict(row) for row in value]
    if isinstance(value, (list, tuple)):
        for item in value:
            rows = _unwrap_records(item)
            if rows is not None:
                return rows
    if isinstance(value, Mapping):
        for key in ("records", "rows", "registry_records"):
            if key in value:
                return _unwrap_records(value[key])
        if value and all(isinstance(row, Mapping) and "canonical_component_id" in row for row in value.values()):
            return [row if isinstance(row, dict) else dict(row) for row in value.values()]
    if dataclasses.is_dataclass(value) or (hasattr(value, "__dict__") and not isinstance(value, type)):
        return _unwrap_records(_plain(value))
    return None


def _call_with_path(function: Callable[..., Any], artifact_dir: Path) -> Any:
    signature = inspect.signature(function)
    parameters = signature.parameters
    for key in ("artifact_dir", "registry_root", "registry_dir", "path", "root"):
        if key in parameters:
            return function(**{key: artifact_dir})
    return function(artifact_dir)


def _load_logical_records(control_module: Any, artifact_dir: Path) -> tuple[list[dict[str, Any]], str, int]:
    layout, files, manifest = _detect_layout(artifact_dir)
    _validate_canonical_artifact_surface(artifact_dir, layout, files)
    for name in (
        "_load_logical_registry",
        "_read_logical_registry",
        "_load_registry_records",
        "_load_registry_layout",
    ):
        function = getattr(control_module, name, None)
        if callable(function):
            try:
                rows = _unwrap_records(_call_with_path(function, artifact_dir))
            except Exception:
                rows = None
            if rows is not None:
                return rows, layout, len(files)
    rows: list[dict[str, Any]] = []
    for path in files:
        rows.extend(_read_jsonl(path))
    if manifest is not None:
        declared_count = manifest.get("row_count") or manifest.get("total_row_count")
        if declared_count is not None and int(declared_count) != len(rows):
            raise InvariantError("SHARD_ROW_COUNT_MISMATCH", f"manifest={declared_count}, observed={len(rows)}")
    return rows, layout, len(files)


def _accepted_git_base_ref(repo_root: Path) -> str:
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
        raise InvariantError("ACCEPTED_BASE_REF", str(exc)) from exc
    base_ref = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", base_ref):
        raise InvariantError("ACCEPTED_BASE_REF", result.stderr.strip())
    return base_ref


def _git_base_tree_paths(repo_root: Path, base_ref: str, prefix: Path) -> set[str]:
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
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc
    if result.returncode != 0:
        raise InvariantError(
            "ACCEPTED_BASE_READ",
            result.stderr.decode("utf-8", errors="replace").strip(),
        )
    try:
        return {
            value.decode("utf-8", errors="strict")
            for value in result.stdout.split(b"\0")
            if value
        }
    except UnicodeDecodeError as exc:
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc


def _materialize_git_base_blob(
    repo_root: Path,
    base_ref: str,
    relative_path: Path,
    destination: Path,
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
        raise InvariantError("ACCEPTED_BASE_READ", str(exc)) from exc
    if result.returncode != 0:
        destination.unlink(missing_ok=True)
        raise InvariantError(
            "ACCEPTED_BASE_READ",
            result.stderr.decode("utf-8", errors="replace").strip(),
        )


def _load_accepted_base_records(
    control_module: Any, repo_root: Path, deadline: Deadline
) -> list[dict[str, Any]]:
    base_ref = _accepted_git_base_ref(repo_root)
    single_rel = DEFAULT_ARTIFACT_DIR / "registry.jsonl"
    manifest_rel = DEFAULT_ARTIFACT_DIR / "registry.manifest.json"
    tree_paths = _git_base_tree_paths(repo_root, base_ref, DEFAULT_ARTIFACT_DIR)
    if not tree_paths:
        return []
    prefix_text = f"{DEFAULT_ARTIFACT_DIR.as_posix()}/"
    relative_names: set[str] = set()
    for path_text in tree_paths:
        if not path_text.startswith(prefix_text):
            raise InvariantError("ACCEPTED_BASE_LAYOUT", path_text)
        relative = path_text.removeprefix(prefix_text)
        if not relative or Path(relative).name != relative:
            raise InvariantError("ACCEPTED_BASE_LAYOUT", path_text)
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
        raise InvariantError("ACCEPTED_BASE_LAYOUT", f"unexpected={unexpected}")
    if "acceptance.report.json" not in relative_names:
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "missing acceptance report")
    if has_single and (has_manifest or shard_names):
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "two physical layouts")
    if has_manifest != bool(shard_names):
        raise InvariantError(
            "ACCEPTED_BASE_LAYOUT",
            f"manifest={has_manifest}, shards={sorted(shard_names)!r}",
        )
    if not has_single and not has_manifest:
        raise InvariantError("ACCEPTED_BASE_LAYOUT", "no registry layout")
    with tempfile.TemporaryDirectory(prefix="qtt-control1-validator-base-") as temporary:
        artifact_dir = Path(temporary)
        (artifact_dir / "acceptance.report.json").write_text("{}\n", encoding="utf-8")
        if has_single:
            _materialize_git_base_blob(
                repo_root, base_ref, single_rel, artifact_dir / single_rel.name
            )
        else:
            manifest_path = artifact_dir / manifest_rel.name
            _materialize_git_base_blob(
                repo_root, base_ref, manifest_rel, manifest_path
            )
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                names = _manifest_files(manifest)
            except (OSError, json.JSONDecodeError, InvariantError) as exc:
                if isinstance(exc, InvariantError):
                    raise
                raise InvariantError("ACCEPTED_BASE_MANIFEST", str(exc)) from exc
            for name in names:
                if (
                    not name.startswith("registry.part-")
                    or not name.endswith(".jsonl")
                    or Path(name).name != name
                ):
                    raise InvariantError("ACCEPTED_BASE_MANIFEST", name)
                relative = DEFAULT_ARTIFACT_DIR / name
                _materialize_git_base_blob(
                    repo_root, base_ref, relative, artifact_dir / name
                )
                deadline.check("accepted merge-base registry materialization")
            if set(names) != shard_names:
                raise InvariantError(
                    "ACCEPTED_BASE_MANIFEST",
                    f"declared={sorted(set(names))!r}, tree={sorted(shard_names)!r}",
                )
        records, _, _ = _load_logical_records(control_module, artifact_dir)
        return records


def _import_control(repo_root: Path) -> tuple[Any, Any, type[Any]]:
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        package = importlib.import_module("src.qtt.computation_control")
        control = importlib.import_module("src.qtt.computation_control.control")
    exported = list(getattr(package, "__all__", []))
    if exported != ["QKUComputationControlPlaneV1"]:
        raise InvariantError("PUBLIC_EXPORT_SURFACE", f"__all__={exported!r}")
    facade_class = getattr(package, "QKUComputationControlPlaneV1", None)
    if not inspect.isclass(facade_class):
        raise InvariantError("PUBLIC_FACADE_MISSING", "QKUComputationControlPlaneV1 is not a class")
    for operation in ("resolve", "compute", "status", "explain"):
        if not callable(getattr(facade_class, operation, None)):
            raise InvariantError("PUBLIC_OPERATION_MISSING", operation)
    forbidden = [
        name
        for name in ("compile", "register", "registry", "executor", "compiler", "apply_update")
        if callable(getattr(facade_class, name, None))
    ]
    if forbidden:
        raise InvariantError("PUBLIC_INTERNAL_LAYER_EXPOSED", repr(forbidden))
    return package, control, facade_class


def _construct_facade(facade_class: type[Any], artifact_dir: Path) -> Any:
    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    signature = inspect.signature(facade_class)
    parameters = signature.parameters
    for key in ("artifact_dir", "registry_root", "registry_dir", "registry_path", "path"):
        if key in parameters:
            value = artifact_dir / "registry.jsonl" if key == "registry_path" and (artifact_dir / "registry.jsonl").is_file() else artifact_dir
            attempts.append(((), {key: value}))
    attempts.extend([((artifact_dir,), {}), ((), {})])
    failures: list[str] = []
    for args, kwargs in attempts:
        try:
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                return facade_class(*args, **kwargs)
        except Exception as exc:
            failures.append(f"{args!r}/{kwargs!r}: {type(exc).__name__}: {exc}")
    raise InvariantError("FACADE_INITIALIZATION", " | ".join(failures[:5]))


def _operation(facade: Any, name: str, selector: Any, inputs: Any = None, context: Any = None) -> Any:
    function = getattr(facade, name)
    context = {} if context is None else context
    if name == "compute":
        attempts = [
            ((), {"selector": selector, "inputs": inputs or {}, "context": context}),
            ((selector, inputs or {}, context), {}),
            ((selector, inputs or {}), {"context": context}),
        ]
    else:
        attempts = [
            ((), {"selector": selector, "context": context}),
            ((selector, context), {}),
            ((selector,), {"context": context}),
        ]
    failures: list[str] = []
    for args, kwargs in attempts:
        try:
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                return function(*args, **kwargs)
        except TypeError as exc:
            failures.append(str(exc))
            continue
    raise InvariantError("FACADE_CALL_SIGNATURE", f"{name}: {failures[:3]}")


def _binding_context(binding: Mapping[str, Any]) -> dict[str, Any]:
    selector = binding.get("context_selector")
    context = (
        {
            str(key): value
            for key, value in selector.items()
            if str(key) not in {"component_id", "canonical_component_id", "binding_id"}
        }
        if isinstance(selector, Mapping)
        else {"context_selector": selector}
    )
    context.setdefault("market", binding.get("market"))
    context.setdefault("venue", binding.get("venue"))
    modes = binding.get("supported_modes")
    if isinstance(modes, list) and modes:
        context.setdefault("mode", modes[0])
    return {key: value for key, value in context.items() if value is not None}


def _validate_callable_ref(reference: Any) -> None:
    if not isinstance(reference, str) or not reference:
        raise InvariantError("CALLABLE_REF_MISSING", repr(reference))
    lowered = reference.lower()
    path_parts = tuple(part for part in re.split(r"[.:]", lowered) if part)
    forbidden_path = any(
        path_parts[index : index + len(token_parts)] == token_parts
        for token in FORBIDDEN_CALL_TOKENS
        for token_parts in (tuple(part for part in token.split(".") if part),)
        for index in range(len(path_parts) - len(token_parts) + 1)
    )
    if forbidden_path or "__" in reference:
        raise InvariantError("UNSAFE_CALLABLE_REF", reference)
    if not CALLABLE_RE.fullmatch(reference):
        raise InvariantError("UNSAFE_CALLABLE_REF", reference)


def _validate_compact_value(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise InvariantError("NONFINITE_VALUE", ".".join(path))
    if isinstance(value, Decimal) and not value.is_finite():
        raise InvariantError("NONFINITE_VALUE", ".".join(path))
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            in_evidence = "evidence_summary" in path or str(key) == "evidence_summary"
            if in_evidence and any(token in lowered for token in BULK_KEY_TOKENS):
                if isinstance(child, (list, dict)) and len(child) > 4:
                    raise InvariantError("BULK_EVIDENCE_PAYLOAD", ".".join(path + (str(key),)))
            _validate_compact_value(child, path + (str(key),))
        return
    if isinstance(value, (list, tuple)):
        if "evidence_summary" in path and len(value) > 64:
            raise InvariantError("BULK_EVIDENCE_PAYLOAD", f"{'.'.join(path)} length={len(value)}")
        for index, child in enumerate(value):
            _validate_compact_value(child, path + (str(index),))


def _validate_evidence_compact(
    value: Any,
    path: tuple[str, ...],
    *,
    depth: int = 0,
    node_budget: list[int] | None = None,
) -> None:
    """Reject bulk payloads even when their keys avoid known evidence names."""

    if node_budget is None:
        node_budget = [0]
        try:
            serialized_bytes = len(_canonical_json(value).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise InvariantError("BULK_EVIDENCE_PAYLOAD", ".".join(path)) from exc
        if serialized_bytes > 65_536:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} serialized_bytes={serialized_bytes}",
            )
    node_budget[0] += 1
    if node_budget[0] > 512:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} nodes={node_budget[0]}",
        )
    if depth > 8:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} depth={depth}",
        )
    if isinstance(value, Mapping):
        if len(value) > 64:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} keys={len(value)}",
            )
        for key, child in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in BULK_KEY_TOKENS):
                if isinstance(child, (Mapping, list, tuple)) and len(child) > 0:
                    raise InvariantError(
                        "BULK_EVIDENCE_PAYLOAD", ".".join(path + (str(key),))
                    )
            _validate_evidence_compact(
                child,
                path + (str(key),),
                depth=depth + 1,
                node_budget=node_budget,
            )
        return
    if isinstance(value, (list, tuple)):
        if len(value) > 64:
            raise InvariantError(
                "BULK_EVIDENCE_PAYLOAD",
                f"{'.'.join(path)} entries={len(value)}",
            )
        for index, child in enumerate(value):
            _validate_evidence_compact(
                child,
                path + (str(index),),
                depth=depth + 1,
                node_budget=node_budget,
            )
        return
    if isinstance(value, str) and len(value.encode("utf-8")) > 4_096:
        raise InvariantError(
            "BULK_EVIDENCE_PAYLOAD",
            f"{'.'.join(path)} scalar_bytes={len(value.encode('utf-8'))}",
        )


def _is_selector_wildcard(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value in {"ANY", "ALL", "*"})


def _selector_values_compatible(left: Any, right: Any) -> bool:
    return (
        _is_selector_wildcard(left)
        or _is_selector_wildcard(right)
        or _canonical_json(left) == _canonical_json(right)
    )


def _ambiguous_binding_selector_overlap(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> bool:
    left_modes = {str(value) for value in left.get("supported_modes", ())}
    right_modes = {str(value) for value in right.get("supported_modes", ())}
    if not (left_modes & right_modes):
        return False
    if not all(
        _selector_values_compatible(left.get(field), right.get(field))
        for field in ("market", "venue", "qku_binding_selector_or_null")
    ):
        return False
    left_selector = left.get("context_selector", {})
    right_selector = right.get("context_selector", {})
    if not isinstance(left_selector, Mapping) or not isinstance(right_selector, Mapping):
        return _canonical_json(left_selector) == _canonical_json(right_selector)
    for key in set(left_selector) & set(right_selector):
        if not _selector_values_compatible(left_selector[key], right_selector[key]):
            return False

    def specificity(binding: Mapping[str, Any], selector: Mapping[str, Any]) -> int:
        score = sum(
            4 for field in ("market", "venue") if not _is_selector_wildcard(binding.get(field))
        )
        score += sum(1 for item in selector.values() if not _is_selector_wildcard(item))
        return score

    return specificity(left, left_selector) == specificity(right, right_selector)


def _validate_no_digest_authority(value: Any) -> None:
    for path, item in _walk(value):
        key = path[-1].lower() if path else ""
        key_tokens = {token for token in re.split(r"[^a-z0-9]+", key) if token}
        if key_tokens & {"hash", "sha", "sha1", "sha256", "checksum", "digest", "freeze"}:
            raise InvariantError("QTT_DIGEST_AUTHORITY", ".".join(path))
        if isinstance(item, str):
            lowered = item.lower()
            if "atomicrows" in lowered and re.search(r"\b(?:sha\d*|hash|digest|checksum)\b", lowered):
                raise InvariantError("ATOMICROWS_DIGEST_REFERENCE", ".".join(path))


def _relation_type(relation: Mapping[str, Any]) -> str:
    return str(relation.get("relation_type") or relation.get("type") or relation.get("relation") or "")


def _validate_record(record: Mapping[str, Any]) -> None:
    component_id = str(record.get("canonical_component_id", "<missing>"))
    _require_keys(record, TOP_LEVEL_REQUIRED, "RECORD_SHAPE", component_id)
    if not component_id or component_id.startswith(("SOURCE::", "LOCAL::")):
        raise InvariantError("CANONICAL_ID_INVALID", component_id)
    id_tokens = {token for token in re.split(r"[^A-Za-z0-9]+", component_id.upper()) if token}
    if (
        {"PR169", "CONTROL1"} & id_tokens
        or re.search(r"(?:19|20)\d{2}[-_.]\d{2}[-_.]\d{2}", component_id)
        or {"SHA", "HASH", "DIGEST", "CHECKSUM"} & id_tokens
        or any(re.fullmatch(r"[0-9A-F]{12,64}", token) for token in id_tokens)
    ):
        raise InvariantError("CANONICAL_ID_UNSTABLE", component_id)
    semantic_version = record["semantic_version"]
    if not isinstance(semantic_version, str) or not SEMVER_RE.fullmatch(semantic_version):
        raise InvariantError("SEMANTIC_VERSION_INVALID", f"{component_id}@{semantic_version!r}")
    if record["record_state"] not in RECORD_STATES:
        raise InvariantError("RECORD_STATE_INVALID", f"{component_id}: {record['record_state']!r}")
    if not isinstance(record["origin_cohorts"], list) or not record["origin_cohorts"]:
        raise InvariantError("ORIGIN_COHORT_INVALID", component_id)
    if "RP5C_BASELINE" in record["origin_cohorts"]:
        forbidden_lineage_paths = _forbidden_mapping_key_paths(
            record,
            {
                "member_identity_row_ids",
                "identity_row_ids",
                "source_artifact_row_ids",
            },
        )
        if forbidden_lineage_paths:
            raise InvariantError(
                "RP5C_RUNTIME_LINEAGE_ARRAY",
                f"{component_id}: {list(forbidden_lineage_paths)}",
            )

    definition = _require_keys(record["definition"], DEFINITION_REQUIRED, "DEFINITION_SHAPE", component_id)
    specification_issues = _independent_specification_issues(definition)
    if not _nonempty(definition["complete_mathematical_or_procedural_definition"]):
        raise InvariantError("DEFINITION_EMPTY", component_id)
    for key in ("input_schema", "output_schema", "units_and_bases"):
        if not isinstance(definition[key], (dict, list)):
            raise InvariantError("UNIT_SCHEMA_MISSING" if key == "units_and_bases" else "DEFINITION_SHAPE", f"{component_id}.{key}")
    if (record["record_state"] == "CANONICAL_ACCEPTED" or definition["implementation_versions"]) and (
        not definition["input_schema"] or not definition["output_schema"] or not definition["units_and_bases"]
    ):
        raise InvariantError("UNIT_SCHEMA_MISSING", component_id)
    for key in ("requirements", "implementation_versions", "oracle_and_test_refs", "equivalence_proof_refs"):
        if not isinstance(definition[key], list):
            raise InvariantError("DEFINITION_SHAPE", f"{component_id}.{key} must be a list")
    for index, implementation in enumerate(definition["implementation_versions"]):
        if not isinstance(implementation, Mapping):
            raise InvariantError("IMPLEMENTATION_SHAPE", f"{component_id}[{index}]")
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
            raise InvariantError(
                "CANONICAL_FIXTURE_PAYLOAD",
                f"{component_id}[{index}]: {sorted(embedded_fixture_keys)}",
            )
    for index, requirement in enumerate(definition["requirements"]):
        requirement = _require_keys(requirement, REQUIREMENT_REQUIRED, "REQUIREMENT_SHAPE", f"{component_id}[{index}]")
        target = requirement["required_component_id_or_source_selector"]
        if not isinstance(target, str) or not target or target.startswith(("SOURCE::", "LOCAL::", "UNRESOLVED::")):
            raise InvariantError("SOURCE_LOCAL_REQUIREMENT", f"{component_id}: {target!r}")
        if not _nonempty(requirement["producer_output_name"]) or not _nonempty(requirement["consumer_input_name"]):
            raise InvariantError("REQUIREMENT_PORT_MISSING", component_id)
        if "unit_or_basis_conversion" not in requirement:
            raise InvariantError("REQUIREMENT_UNIT_MISSING", component_id)

    uses = _require_keys(record["uses"], USES_REQUIRED, "USES_SHAPE", component_id)
    for key in USES_REQUIRED:
        if not isinstance(uses[key], list):
            raise InvariantError("USES_SHAPE", f"{component_id}.{key} must be a list")
    if record["record_state"] == "CANONICAL_ACCEPTED" and not uses["decision_roles"]:
        raise InvariantError("DECISION_ROLE_MISSING", component_id)

    if not isinstance(record["bindings"], list):
        raise InvariantError("BINDING_SHAPE", component_id)
    if record["record_state"] in {"CANONICAL_ACCEPTED", "PROVISIONAL", "UNDER_REVIEW"} and not record["bindings"]:
        raise InvariantError("ACTIVE_RECORD_WITHOUT_BINDING", component_id)
    binding_ids: set[str] = set()
    selectors: set[str] = set()
    validated_bindings: list[Mapping[str, Any]] = []
    for binding in record["bindings"]:
        binding = _require_keys(binding, BINDING_REQUIRED, "BINDING_SHAPE", component_id)
        binding_id = binding["binding_id"]
        if not isinstance(binding_id, str) or not binding_id:
            raise InvariantError("BINDING_ID_INVALID", component_id)
        if binding_id in binding_ids:
            raise InvariantError("AMBIGUOUS_BINDING", f"duplicate {binding_id}")
        binding_ids.add(binding_id)
        selector_key = _canonical_json(
            {
                "market": binding["market"],
                "venue": binding["venue"],
                "context": binding["context_selector"],
                "qku": binding["qku_binding_selector_or_null"],
                "modes": sorted(binding["supported_modes"]) if isinstance(binding["supported_modes"], list) else binding["supported_modes"],
            }
        )
        if selector_key in selectors:
            raise InvariantError("AMBIGUOUS_BINDING", f"{component_id}: overlapping exact selector")
        selectors.add(selector_key)
        supported_modes = binding["supported_modes"]
        mode_state = binding["mode_state"]
        if not isinstance(supported_modes, list) or len(supported_modes) != len(
            {str(value) for value in supported_modes}
        ):
            raise InvariantError("SUPPORTED_MODES_INVALID", binding_id)
        if not isinstance(mode_state, Mapping):
            raise InvariantError("MODE_STATE_INVALID", binding_id)
        missing_mode_state = sorted(
            str(mode) for mode in supported_modes if str(mode) not in mode_state
        )
        if missing_mode_state:
            raise InvariantError(
                "MODE_STATE_MISSING",
                f"{binding_id}: {missing_mode_state}",
            )
        extra_mode_state = sorted(
            str(mode) for mode in mode_state if str(mode) not in {str(value) for value in supported_modes}
        )
        if extra_mode_state:
            raise InvariantError(
                "MODE_STATE_WITHOUT_SUPPORTED_MODE",
                f"{binding_id}: {extra_mode_state}",
            )
        for mode in supported_modes:
            state = mode_state[str(mode)]
            if not isinstance(state, Mapping):
                raise InvariantError("MODE_STATE_INVALID", f"{binding_id}.{mode}")
            if state.get("evidence") not in EVIDENCE_STATES:
                raise InvariantError("MODE_STATE_INVALID", f"{binding_id}.{mode}.evidence")
            if state.get("authorization") not in AUTH_STATES:
                raise InvariantError(
                    "MODE_STATE_INVALID", f"{binding_id}.{mode}.authorization"
                )
        readiness = _require_keys(binding["readiness"], READINESS_REQUIRED, "READINESS_SHAPE", binding_id)
        for key in ("specification", "implementation", "inputs", "requirements", "oracle", "context"):
            if readiness[key] not in SPEC_STATES:
                raise InvariantError("READINESS_STATE_INVALID", f"{binding_id}.{key}={readiness[key]!r}")
        if readiness["evidence"] not in EVIDENCE_STATES or readiness["authorization"] not in AUTH_STATES:
            raise InvariantError("READINESS_STATE_INVALID", binding_id)
        if binding["derived_state"] not in DERIVED_STATES:
            raise InvariantError("DERIVED_STATE_INVALID", f"{binding_id}: {binding['derived_state']!r}")
        unresolved = any(readiness[key] != "PASS" for key in ("specification", "implementation", "inputs", "requirements", "oracle", "context"))
        if unresolved:
            action = binding["exact_resolution_action_or_null"]
            if not isinstance(action, str) or not action or action.upper() in PLACEHOLDERS:
                raise InvariantError("EXACT_ACTION_MISSING", binding_id)
        if readiness["specification"] == "PASS" and specification_issues:
            raise InvariantError(
                "FALSE_SPECIFICATION_PASS",
                f"{component_id}: {binding_id}: {list(specification_issues)}",
            )
        if specification_issues:
            action = str(binding.get("exact_resolution_action_or_null") or "")
            if not action.startswith(
                f"MISSING_SPECIFICATION_SEMANTICS: {component_id}@"
            ) or any(issue not in action for issue in specification_issues):
                raise InvariantError(
                    "SPECIFICATION_ACTION_INEXACT",
                    f"{component_id}: {binding_id}: {action!r}",
                )
        if record["record_state"] in RUNTIME_ACTIVE_RECORD_STATES:
            if readiness["specification"] == "INVALID":
                raise InvariantError(
                    "ACTIVE_INVALID_SPECIFICATION", f"{component_id}: {binding_id}"
                )
            specification_required = (
                readiness["specification"] == "REQUIRED"
                or bool(specification_issues)
            )
            if (
                specification_required
                and binding["derived_state"] != "SPECIFICATION_REQUIRED"
            ):
                raise InvariantError(
                    "FALSE_SPECIFIED_STATE",
                    f"{component_id}: {binding_id}: {binding['derived_state']}",
                )
            if (
                not specification_required
                and binding["derived_state"] == "SPECIFICATION_REQUIRED"
            ):
                raise InvariantError(
                    "FALSE_SPECIFICATION_REQUIRED_STATE",
                    f"{component_id}: {binding_id}",
                )
        input_source_issues = _independent_input_source_binding_issues(
            definition, binding
        )
        typed_binding_ready_claim = any(
            readiness.get(name) == "PASS"
            for name in ("inputs", "context")
        ) or binding["derived_state"] in {
            "CONTEXT_READY",
            "STACK_READY",
            "EVIDENCED",
            "AUTHORIZED",
        }
        if typed_binding_ready_claim and input_source_issues:
            raise InvariantError(
                "FALSE_TYPED_INPUT_SOURCE_BINDING",
                f"{component_id}: {binding_id}: {list(input_source_issues)}",
            )
        computation_ready = (
            not specification_issues
            and not input_source_issues
            and all(
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
        )
        operations = _independent_policy_operations(binding["agent_access_policy"])
        if operations.intersection({"resolve", "compute"}) and not computation_ready:
            raise InvariantError(
                "FALSE_AGENT_COMPUTE_ELIGIBILITY",
                f"{component_id}: {binding_id}: {sorted(operations)}",
            )
        if binding["derived_state"] in {
            "CONTEXT_READY",
            "STACK_READY",
            "EVIDENCED",
            "AUTHORIZED",
        } and not computation_ready:
            raise InvariantError(
                "FALSE_CONTEXT_READY", f"{component_id}: {binding_id}"
            )
        if readiness["authorization"] == "AUTHORIZED" or binding["derived_state"] == "AUTHORIZED":
            raise InvariantError("LIVE_AUTHORITY_CLAIM", binding_id)
        if readiness["evidence"] in {"REPLAY", "PAPER", "SHADOW", "DRYRUN", "CANARY", "LIVE"}:
            raise InvariantError("EMPIRICAL_EXECUTION_CLAIM", f"{binding_id}: {readiness['evidence']}")
        _validate_compact_value(binding["evidence_summary"], (component_id, binding_id, "evidence_summary"))
        _validate_evidence_compact(
            binding["evidence_summary"],
            (component_id, binding_id, "evidence_summary"),
        )
        validated_bindings.append(binding)

    for left_index, left in enumerate(validated_bindings):
        for right in validated_bindings[left_index + 1 :]:
            if _ambiguous_binding_selector_overlap(left, right):
                raise InvariantError(
                    "OVERLAPPING_BINDING_SELECTORS",
                    f"{component_id}: {left['binding_id']} / {right['binding_id']}",
                )

    if not isinstance(record["provenance"], list) or not record["provenance"]:
        raise InvariantError("PROVENANCE_SHAPE", component_id)
    for provenance in record["provenance"]:
        _require_keys(provenance, PROVENANCE_REQUIRED, "PROVENANCE_SHAPE", component_id)
    if not isinstance(record["relations"], list):
        raise InvariantError("RELATIONS_SHAPE", component_id)
    for relation in record["relations"]:
        if not isinstance(relation, Mapping) or not _relation_type(relation):
            raise InvariantError("RELATION_INVALID", f"{component_id}: {relation!r}")
        if "RP5C_BASELINE" in record["origin_cohorts"] and {
            "member_identity_row_ids",
            "identity_row_ids",
            "source_artifact_row_ids",
        }.intersection(relation):
            raise InvariantError("RP5C_RUNTIME_LINEAGE_ARRAY", component_id)
    _require_keys(record["governance"], GOVERNANCE_REQUIRED, "GOVERNANCE_SHAPE", component_id)
    _validate_compact_value(record)
    _validate_no_digest_authority(record)


def _requirement_target(requirement: Mapping[str, Any]) -> str:
    return str(requirement.get("required_component_id_or_source_selector", ""))


def _graph(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    active_ids = {
        str(record["canonical_component_id"])
        for record in records
        if record.get("record_state") in ACCEPTED_STATES
    }
    graph: dict[str, set[str]] = {component_id: set() for component_id in active_ids}
    reverse: dict[str, set[str]] = {component_id: set() for component_id in active_ids}
    for record in records:
        component_id = str(record.get("canonical_component_id", ""))
        if component_id not in graph:
            continue
        for requirement in record.get("definition", {}).get("requirements", []):
            target = _requirement_target(requirement)
            if target not in active_ids:
                raise InvariantError("UNRESOLVED_REQUIREMENT", f"{component_id} -> {target}")
            graph[component_id].add(target)
            reverse[target].add(component_id)
    return graph, reverse


def _topological(graph: Mapping[str, set[str]]) -> list[str]:
    indegree = {node: len(requirements) for node, requirements in graph.items()}
    reverse: dict[str, set[str]] = {node: set() for node in graph}
    for node, requirements in graph.items():
        for requirement in requirements:
            reverse.setdefault(requirement, set()).add(node)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for dependent in sorted(reverse.get(node, ())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)
    if len(order) != len(graph):
        cycle_nodes = sorted(node for node, degree in indegree.items() if degree > 0)[:20]
        raise InvariantError("DAG_CYCLE", repr(cycle_nodes))
    return order


def _independent_qku_pack_ids(
    record: Mapping[str, Any], verification_state: str
) -> set[str]:
    component_id = str(record.get("canonical_component_id", ""))
    result: set[str] = set()
    if verification_state in {
        "UNRESOLVED_MATERIAL_BLOCKER",
        "REJECTED_INVALID_OR_CONTRADICTORY",
    }:
        result.add(_QKU_UNRESOLVED_PACK)
    origins = {str(value) for value in record.get("origin_cohorts", ())}
    if "RP5C_BASELINE" in origins:
        return result
    if component_id in (
        _CLOSED_DECIMAL_PRIMARY_COMPONENTS
        | _CLOSED_DECIMAL_DERIVATION_COMPONENTS
    ):
        result.add(_QKU_DECIMAL_PACK)
    if component_id in _CLOSED_DECIMAL_PRICE_COMPONENTS:
        result.add(_QKU_PRICE_PACK)
    if component_id in _QKU_PRICE_COMPONENT_IDS:
        result.add(_QKU_PRICE_PACK)
    if component_id in _QKU_INSTITUTIONAL_COMPONENT_IDS:
        result.add(_QKU_INSTITUTIONAL_PACK)
    if component_id in _QKU_QUANTUM_COMPONENT_IDS:
        result.add(_QKU_QUANTUM_PACK)
    if component_id in _QKU_PROVIDER_COMPONENT_IDS:
        result.add(_QKU_PROVIDER_PACK)
    return result


def _independent_reviewed_qku_semantic_policy(
    record: Mapping[str, Any],
) -> tuple[str | None, tuple[str, ...]]:
    """Reconstruct the reviewed Decimal family without trusting component ID."""

    component_id = str(record.get("canonical_component_id", ""))
    descriptions: dict[str, dict[str, Any]] = {
        "QTT.COMP.FORMULA.IMPLIED_PROBABILITY": {
            "expression": "implied_probability = clamp(price / max(payout, epsilon), 0, 1)",
            "domain": (
                "price and payout are finite Decimal-compatible values; payout >= 1e-9; "
                "0 <= price <= payout; output is price/payout in [0,1]"
            ),
            "inputs": (("price", "price"), ("payout", "price")),
            "output": ("implied_probability", "probability"),
            "units": {
                "implied_probability": "probability",
                "payout": "price",
                "price": "price",
            },
            "requirements": (),
        },
        "QTT.COMP.FORMULA.PROBABILITY_EDGE": {
            "expression": "probability_edge = p_model - implied_probability",
            "domain": (
                "p_model and dependency-produced implied_probability are finite probabilities "
                "in [0,1]; output is their signed difference"
            ),
            "inputs": (
                ("p_model", "probability"),
                ("implied_probability", "probability"),
            ),
            "output": ("probability_edge", "probability_delta"),
            "units": {
                "implied_probability": "probability",
                "p_model": "probability",
                "probability_edge": "probability_delta",
            },
            "requirements": (
                (
                    "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
                    "IMPLIED_PROBABILITY_INPUT",
                    "implied_probability",
                    "implied_probability",
                ),
            ),
        },
        "QTT.COMP.FORMULA.MID_PRICE": {
            "expression": "mid_price = (best_bid + best_ask) / 2",
            "domain": "finite prices satisfying 0 <= best_bid <= best_ask",
            "inputs": (("best_bid", "price"), ("best_ask", "price")),
            "output": ("mid_price", "price"),
            "units": {
                "best_ask": "price",
                "best_bid": "price",
                "mid_price": "price",
            },
            "requirements": (),
        },
        "QTT.COMP.FORMULA.SPREAD": {
            "expression": "spread = best_ask - best_bid",
            "domain": "finite prices satisfying 0 <= best_bid <= best_ask",
            "inputs": (("best_bid", "price"), ("best_ask", "price")),
            "output": ("spread", "price_delta"),
            "units": {
                "best_ask": "price",
                "best_bid": "price",
                "spread": "price_delta",
            },
            "requirements": (),
        },
        "QTT.COMP.FORMULA.RELATIVE_SPREAD": {
            "expression": "relative_spread = spread / max(mid_price, epsilon)",
            "domain": (
                "finite numerator and denominator in one declared contextual scalar basis; "
                "denominator >= 1e-9; output is a finite dimensionless ratio"
            ),
            "inputs": (("spread", "price_delta"), ("mid_price", "price")),
            "output": ("relative_spread", "ratio"),
            "units": {
                "mid_price": "price",
                "relative_spread": "ratio",
                "spread": "price_delta",
            },
            "requirements": (
                (
                    "QTT.COMP.FORMULA.MID_PRICE",
                    "MID_PRICE_DENOMINATOR",
                    "mid_price",
                    "mid_price",
                ),
                (
                    "QTT.COMP.FORMULA.SPREAD",
                    "ABSOLUTE_SPREAD_NUMERATOR",
                    "spread",
                    "spread",
                ),
            ),
        },
    }
    expected = descriptions.get(component_id)
    if expected is None:
        return None, ()
    definition = record.get("definition", {})
    issues: list[str] = []

    def require(field: str, expected_value: Any) -> None:
        if definition.get(field) != expected_value:
            issues.append(field)

    if str(record.get("semantic_version", "")) != "1.0":
        issues.append("semantic_version")
    require("component_kind", "PURE_FORMULA")
    require("complete_mathematical_or_procedural_definition", expected["expression"])
    require("objective_sense_or_null", None)
    require(
        "assumptions",
        ["PURE_STATELESS_SCALAR_ARITHMETIC_ON_ONE_IMMUTABLE_REQUEST_INPUT_LOCK"],
    )
    require("hard_constraints", [])
    require("soft_preferences", [])
    require("domain_and_boundary_behavior", expected["domain"])
    require(
        "state_and_time_semantics",
        {"state": "STATELESS", "time": "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"},
    )
    require(
        "input_schema",
        [
            {
                "name": name,
                "required": True,
                "type": "FINITE_DECIMAL_COMPATIBLE_SCALAR",
                "unit_or_basis": unit,
            }
            for name, unit in expected["inputs"]
        ],
    )
    output_name, output_unit = expected["output"]
    require(
        "output_schema",
        [
            {
                "name": output_name,
                "type": "FINITE_DECIMAL_COMPATIBLE_SCALAR",
                "unit_or_basis": output_unit,
            }
        ],
    )
    require("units_and_bases", expected["units"])
    require(
        "output_accounting_class",
        "NON_ACCOUNTING_UNLESS_OUTPUT_SCHEMA_EXPLICITLY_IDENTIFIES_ACCOUNTING",
    )
    require(
        "missing_stale_nonfinite_behavior",
        {"missing": "FAIL_CLOSED", "nonfinite": "FAIL_CLOSED", "stale": "FAIL_CLOSED"},
    )
    require(
        "precision_and_rounding",
        {
            "numeric_boundary": "PYTHON_DECIMAL",
            "rounding": "NO_ROUNDING_BEFORE_DECLARED_OUTPUT",
        },
    )
    require(
        "parameter_schema_and_default_provenance",
        {
            "default_provenance": "NO_CONFIGURABLE_PARAMETERS_IN_FORMULA_SEMANTICS",
            "parameters": [],
        },
    )
    expected_requirements = [
        {
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
        for target, role, producer, consumer in expected["requirements"]
    ]
    require("requirements", expected_requirements)
    require(
        "failure_domain_tags",
        ["MISSING_INPUT", "STALE_INPUT", "NONFINITE_INPUT", "DOMAIN_ERROR"],
    )
    require(
        "classical_fallback",
        {
            "not_applicable": True,
            "proof_ref": "PURE_FORMULA_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
        },
    )
    quantum = definition.get("quantum")
    if not isinstance(quantum, Mapping) or (
        quantum.get("applicability_state")
        != "NOT_APPLICABLE_OR_NOT_YET_PROVEN"
        or quantum.get("selected_formulation_or_none") is not None
        or quantum.get("maturity_ceiling") != "SPECIFIED"
    ):
        issues.append("quantum")
    oracle_refs = {
        str(row.get("ref", ""))
        for row in definition.get("oracle_and_test_refs", ())
        if isinstance(row, Mapping)
    }
    if (
        "tests/pr169_qku_comp_control1/test_control1.py::"
        "test_closed_formula_decimal_oracles_are_independent"
        not in oracle_refs
    ):
        issues.append("independent_oracle")
    return "QKU.SEMANTIC.REVIEW.CLOSED_DECIMAL.V1", tuple(sorted(set(issues)))


def _independent_qku_role_applicability_signature(
    record: Mapping[str, Any], role: Mapping[str, Any]
) -> list[dict[str, Any]]:
    qku_id = str(role.get("qku_id", ""))
    result: list[dict[str, Any]] = []
    for binding in record.get("bindings", ()):
        selector = binding.get("qku_binding_selector_or_null")
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
    return sorted(result, key=_canonical_json)


_INDEPENDENT_QKU_REVIEWED_MARKETS = frozenset(
    {"PREDICTION_MARKET", "prediction_market", "binary_event_contract"}
)
_INDEPENDENT_QKU_BLOCKER_TEXT = {
    "TERMINAL_DISPOSITION",
    "INCOMPLETE_OR_NONCANONICAL_SEMANTICS",
    "REVIEWED_SEMANTIC_BINDING_MISMATCH",
    "UNAPPROVED_EXTERNAL_VERIFICATION_ESCAPE",
    "MISSING_EXTERNAL_OR_DERIVATION_PROOF",
    "UNVERIFIED_ROLE_APPLICABILITY",
}


def _independent_qku_direct_state(
    record: Mapping[str, Any], specification_issues: Sequence[str]
) -> tuple[str, str | None, str | None]:
    component_id = str(record.get("canonical_component_id", ""))
    state = str(record.get("record_state", ""))
    if state in {"REJECTED_INVALID", "INAPPLICABLE_WITH_PROOF"}:
        return "REJECTED_INVALID_OR_CONTRADICTORY", "TERMINAL_DISPOSITION", None
    if specification_issues or state != "CANONICAL_ACCEPTED":
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "INCOMPLETE_OR_NONCANONICAL_SEMANTICS",
            None,
        )
    policy, binding_issues = _independent_reviewed_qku_semantic_policy(record)
    if component_id in _CLOSED_DECIMAL_PRIMARY_COMPONENTS:
        if policy is None or binding_issues:
            return (
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REVIEWED_SEMANTIC_BINDING_MISMATCH",
                None,
            )
        return "VERIFIED_BY_PRIMARY_EXTERNAL_SOURCE", None, policy
    if component_id in _CLOSED_DECIMAL_DERIVATION_COMPONENTS:
        if policy is None or binding_issues:
            return (
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REVIEWED_SEMANTIC_BINDING_MISMATCH",
                None,
            )
        return "VERIFIED_BY_INDEPENDENT_MATHEMATICAL_DERIVATION", None, policy
    definition = record.get("definition", {})
    if any(
        definition.get(field) not in (None, "", [], {})
        for field in (
            "external_verification_not_applicable_reason",
            "qtt_internal_policy_provenance",
            "repository_historical_evidence_provenance",
            "official_current_documentation_proof",
        )
    ):
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "UNAPPROVED_EXTERNAL_VERIFICATION_ESCAPE",
            None,
        )
    return (
        "UNRESOLVED_MATERIAL_BLOCKER",
        "MISSING_EXTERNAL_OR_DERIVATION_PROOF",
        None,
    )


def _independent_qku_role_direct_verification(
    record: Mapping[str, Any],
    role: Mapping[str, Any],
    specification_issues: Sequence[str],
) -> tuple[str, str | None, str | None, list[dict[str, Any]]]:
    state, blocker_code, semantic_policy = _independent_qku_direct_state(
        record, specification_issues
    )
    applicability = _independent_qku_role_applicability_signature(record, role)
    if state not in {
        "UNRESOLVED_MATERIAL_BLOCKER",
        "REJECTED_INVALID_OR_CONTRADICTORY",
    } and (
        not applicability
        or str(role.get("market_family", ""))
        not in _INDEPENDENT_QKU_REVIEWED_MARKETS
    ):
        return (
            "UNRESOLVED_MATERIAL_BLOCKER",
            "UNVERIFIED_ROLE_APPLICABILITY",
            None,
            applicability,
        )
    return state, blocker_code, semantic_policy, applicability


def _independent_qku_role_ref(role: Mapping[str, Any]) -> str:
    return "::".join(
        (
            str(role.get("qku_id", "")),
            str(role.get("role_or_decision_stage", "")),
            str(role.get("market_family", "")),
            _canonical_json(role.get("context_selector")),
        )
    )


def _validate_qku_verification_receipts(
    records: Sequence[Mapping[str, Any]],
    *,
    repo_root: Path | None = None,
    deadline: Deadline | None = None,
    source_universe: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Independently derive every QKU receipt and coverage denominator."""

    receipt_count = 0
    canonical_qku_ids: set[str] = set()
    qku_role_keys: set[tuple[str, str, str, str]] = set()
    disposition_counts: Counter[str] = Counter()
    pack_counts: Counter[str] = Counter()
    launch_denominator = launch_verified = 0
    launch_dispositioned = launch_blocked = 0
    live_denominator = live_verified = 0
    live_dispositioned = live_blocked = 0
    risk_denominator = risk_verified = risk_blocked = 0
    venue_denominator = venue_covered = 0
    blocker_policy_keys: set[tuple[str, tuple[str, ...]]] = set()
    for record in records:
        issues = tuple(
            str(value)
            for value in _independent_specification_issues(
                record.get("definition", {})
            )
        )
        for role in record.get("uses", {}).get("qku_role_bindings", ()):
            state, blocker_code, _, _ = _independent_qku_role_direct_verification(
                record, role, issues
            )
            if state in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }:
                if blocker_code not in _INDEPENDENT_QKU_BLOCKER_TEXT:
                    raise InvariantError(
                        "QKU_BLOCKER_CODE_UNKNOWN",
                        f"{record.get('canonical_component_id')}: {blocker_code!r}",
                    )
                blocker_policy_keys.add((str(blocker_code), issues))
    blocker_policy_by_key = {
        key: f"BLOCKER.QKU.VERIFICATION.GROUP.{index:04d}"
        for index, key in enumerate(sorted(blocker_policy_keys), 1)
    }
    pack_component_consumers: dict[str, set[str]] = defaultdict(set)
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
        roles = list(record.get("uses", {}).get("qku_role_bindings", ()))
        issues = tuple(
            str(value)
            for value in _independent_specification_issues(record["definition"])
        )
        reference_by_applicability: dict[
            tuple[str, str, str], Mapping[str, Any]
        ] = {}
        role_by_ref = {_independent_qku_role_ref(role): role for role in roles}
        binding_modes = {
            str(mode)
            for binding in record.get("bindings", ())
            for mode in binding.get("supported_modes", ())
        }
        empirical_modes = {
            "REPLAY",
            "PAPER",
            "SHADOW",
            "DRYRUN",
            "CANARY",
            "LIVE",
        }
        live_candidate = bool(binding_modes.intersection(empirical_modes))
        record_risk = bool(
            risk_roles.intersection(record.get("uses", {}).get("decision_roles", ()))
        )
        for role in sorted(roles, key=_independent_qku_role_ref):
            canonical_qku_ids.add(str(role.get("qku_id", "")))
            qku_role_keys.add(
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                    _canonical_json(role.get("context_selector")),
                )
            )
            (
                direct_state,
                expected_blocker_code,
                expected_semantic_policy,
                applicability_signature,
            ) = _independent_qku_role_direct_verification(record, role, issues)
            applicability_key = (
                str(role.get("market_family", "")),
                _canonical_json(role.get("context_selector")),
                _canonical_json(applicability_signature),
            )
            reference = reference_by_applicability.get(applicability_key)
            expected_state = (
                "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE"
                if reference is not None
                and direct_state
                not in {
                    "UNRESOLVED_MATERIAL_BLOCKER",
                    "REJECTED_INVALID_OR_CONTRADICTORY",
                }
                else direct_state
            )
            expected_packs = _independent_qku_pack_ids(record, expected_state)
            receipt = role.get("qku_verification_receipt")
            if not isinstance(receipt, Mapping):
                raise InvariantError(
                    "QKU_VERIFICATION_RECEIPT_MISSING",
                    f"{component_id}: {_independent_qku_role_ref(role)}",
                )
            receipt_count += 1
            if receipt.get("receipt_schema") != QKU_VERIFICATION_RECEIPT_SCHEMA:
                raise InvariantError("QKU_VERIFICATION_RECEIPT_SCHEMA", component_id)
            state = str(receipt.get("verification_state", ""))
            root_state = state
            if state not in QKU_VERIFICATION_STATES:
                raise InvariantError(
                    "QKU_VERIFICATION_STATE", f"{component_id}: {state!r}"
                )
            semantic_family_resolved = expected_state not in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }
            expected_family = (
                f"{component_id}@{semantic_version}"
                if semantic_family_resolved
                else None
            )
            if receipt.get("semantic_family_id") != expected_family:
                raise InvariantError("QKU_SEMANTIC_FAMILY_MISSING", component_id)
            expected_subject = {
                "component_version_ref": f"{component_id}@{semantic_version}",
                "qku_role_ref": _independent_qku_role_ref(role),
            }
            if receipt.get("verification_subject") != expected_subject:
                raise InvariantError("QKU_VERIFICATION_SUBJECT_DRIFT", component_id)
            exact_claim = receipt.get("exact_unique_claim")
            if semantic_family_resolved:
                if (
                    exact_claim is not None
                    or receipt.get("semantic_binding_policy_id")
                    != expected_semantic_policy
                ):
                    raise InvariantError("QKU_SEMANTIC_FAMILY_MISSING", component_id)
            else:
                expected_unique_claim = {
                    "subject_ref": (
                        f"{component_id}@{semantic_version}::"
                        f"{_independent_qku_role_ref(role)}"
                    ),
                    "claim_kind": expected_blocker_code,
                    "semantic_status": (
                        "TERMINAL"
                        if expected_state == "REJECTED_INVALID_OR_CONTRADICTORY"
                        else "UNRESOLVED"
                    ),
                }
                if exact_claim != expected_unique_claim or receipt.get(
                    "semantic_binding_policy_id"
                ) is not None:
                    raise InvariantError(
                        "QKU_EXACT_UNRESOLVED_CLAIM_MISSING", component_id
                    )
            reason = str(receipt.get("reason", "")).strip()
            if state not in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            } and not reason:
                code = (
                    "QKU_NO_EXTERNAL_REASON_MISSING"
                    if state == "NO_EXTERNAL_VERIFICATION_APPLICABLE"
                    else "QKU_VERIFICATION_REASON_MISSING"
                )
                raise InvariantError(code, component_id)
            pack_ids_value = receipt.get("claim_family_source_pack_ids")
            if (
                not isinstance(pack_ids_value, list)
                or len(pack_ids_value) != len(set(map(str, pack_ids_value)))
            ):
                raise InvariantError("QKU_SOURCE_PACK_REFS", component_id)
            pack_ids = {str(value) for value in pack_ids_value}
            if pack_ids != expected_packs or not pack_ids.issubset(_QKU_KNOWN_PACKS):
                raise InvariantError(
                    "QKU_SOURCE_PACK_REFS",
                    f"{component_id}: observed={sorted(pack_ids)}, expected={sorted(expected_packs)}",
                )
            for pack_id in pack_ids:
                pack_counts[pack_id] += 1
                pack_component_consumers[pack_id].add(component_id)
            if state != expected_state:
                raise InvariantError(
                    "QKU_VERIFICATION_DISPOSITION_FALSE",
                    f"{component_id}: {state} != {expected_state}",
                )
            proof = receipt.get("inheritance_equivalence_proof_or_null")
            if state == "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE":
                if not isinstance(proof, Mapping):
                    raise InvariantError("QKU_INHERITANCE_PROOF_MISSING", component_id)
                reference_ref = str(proof.get("reference_qku_role_ref", ""))
                reference_role = role_by_ref.get(reference_ref)
                if reference_role is None or reference is None or reference_role is not reference:
                    raise InvariantError("QKU_INHERITANCE_REFERENCE", component_id)
                reference_receipt = reference_role.get("qku_verification_receipt", {})
                if reference_receipt.get("verification_state") == (
                    "VERIFIED_BY_CANONICAL_FAMILY_INHERITANCE"
                ):
                    raise InvariantError("QKU_INHERITANCE_CHAIN", component_id)
                root_state = str(reference_receipt.get("verification_state", ""))
                if (
                    proof.get("equivalence_policy_id")
                    != "QKU.INHERIT.EXACT_SEMANTICS.V1"
                    or proof.get("applicability_policy_id")
                    != "QKU.INHERIT.EXACT_MARKET_VENUE_CONTEXT_BINDINGS.V1"
                    or proof.get("canonical_component_id") != component_id
                    or proof.get("semantic_version") != semantic_version
                    or proof.get("semantic_fields_compared")
                    != list(QKU_INHERITANCE_SEMANTIC_FIELDS)
                ):
                    raise InvariantError("QKU_INHERITANCE_SEMANTIC_DRIFT", component_id)
                if (
                    proof.get("binding_applicability") != applicability_signature
                    or _independent_qku_role_applicability_signature(
                        record, reference_role
                    )
                    != applicability_signature
                    or reference_role.get("market_family")
                    != role.get("market_family")
                    or _canonical_json(reference_role.get("context_selector"))
                    != _canonical_json(role.get("context_selector"))
                ):
                    raise InvariantError("QKU_INHERITANCE_APPLICABILITY_DRIFT", component_id)
            elif proof is not None:
                raise InvariantError("QKU_INHERITANCE_PROOF_UNEXPECTED", component_id)
            reference_by_applicability.setdefault(applicability_key, role)
            blocker_policy_id = receipt.get("blocker_policy_id")
            observed_blocker_code = receipt.get("blocker_code")
            action_ref_value = receipt.get("resolution_action_ref")
            if state in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }:
                if (
                    observed_blocker_code != expected_blocker_code
                    or blocker_policy_id
                    != blocker_policy_by_key[(str(expected_blocker_code), issues)]
                    or not action_ref_value
                ):
                    raise InvariantError("QKU_MATERIAL_BLOCKER_MISSING", component_id)
                action_ref = str(action_ref_value)
                valid_action_refs = {
                    "ROLE"
                    if role.get("exact_resolution_action")
                    else ""
                }
                valid_action_refs.update(
                    f"BINDING:{binding.get('binding_id')}"
                    for binding in record.get("bindings", ())
                    if binding.get("exact_resolution_action_or_null")
                )
                if not valid_action_refs - {""}:
                    valid_action_refs.add("BLOCKER_POLICY")
                if action_ref not in valid_action_refs:
                    raise InvariantError("QKU_MATERIAL_BLOCKER_ACTION_REF", component_id)
            elif (
                blocker_policy_id is not None
                or observed_blocker_code is not None
                or action_ref_value is not None
            ):
                raise InvariantError("QKU_MATERIAL_BLOCKER_FALSE", component_id)
            if _QKU_PROVIDER_PACK in pack_ids:
                if not (
                    receipt.get("official_effective_date_or_null")
                    or receipt.get("current_fact_as_of_or_retrieval_date")
                ) or not receipt.get("ttl_or_null"):
                    raise InvariantError("QKU_CURRENT_FACT_TIME_MISSING", component_id)
                if receipt.get("recheck_policy_id") != (
                    "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION"
                ):
                    raise InvariantError("QKU_CURRENT_FACT_RECHECK_MISSING", component_id)
                venue_denominator += 1
                venue_covered += 1
            elif (
                receipt.get("current_fact_as_of_or_retrieval_date") is not None
                or receipt.get("ttl_or_null") is not None
            ):
                raise InvariantError("QKU_TIME_SCOPE_UNEXPECTED", component_id)
            elif state not in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            } and receipt.get("recheck_policy_id") != (
                "RECHECK.QKU.SEMANTIC_OR_IMPLEMENTATION_CHANGE"
            ):
                raise InvariantError("QKU_RECHECK_POLICY_MISSING", component_id)
            if state in {
                "UNRESOLVED_MATERIAL_BLOCKER",
                "REJECTED_INVALID_OR_CONTRADICTORY",
            }:
                if role.get("runtime_root_eligibility") not in {
                    "STATUS_EXPLAIN_ONLY",
                    "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF",
                    "INELIGIBLE_UNTIL_SOURCE_SCOPED_SEMANTICS_ARE_ACCEPTED",
                } or live_candidate:
                    raise InvariantError("QKU_UNRESOLVED_MODE_ESCALATION", component_id)
                for binding in record.get("bindings", ()):
                    operations = _independent_policy_operations(
                        binding.get("agent_access_policy", {})
                    )
                    if operations.intersection({"resolve", "compute"}):
                        raise InvariantError(
                            "QKU_UNRESOLVED_MODE_ESCALATION", component_id
                        )
            disposition_counts[state] += 1
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

    # Canonical validation also proves that packs for the five closed nodes
    # remain exact component consumers even though CONTROL1 correctly does not
    # manufacture a QKU for them.  Focused defect tests intentionally validate
    # smaller synthetic registries and therefore do not enforce the universe.
    if repo_root is not None:
        existing_ids = {str(record["canonical_component_id"]) for record in records}
        closed_ids = (
            _CLOSED_DECIMAL_PRIMARY_COMPONENTS
            | _CLOSED_DECIMAL_DERIVATION_COMPONENTS
        )
        if not closed_ids.issubset(existing_ids):
            raise InvariantError(
                "QKU_CLOSED_COMPONENT_SOURCE_CONSUMER",
                "missing closed Decimal component",
            )
        pack_component_consumers[_QKU_PRICE_PACK].update(
            closed_ids.intersection(_CLOSED_DECIMAL_PRICE_COMPONENTS)
        )
        pack_component_consumers[_QKU_DECIMAL_PACK].update(closed_ids)
        unused_packs = sorted(
            pack_id
            for pack_id in _QKU_KNOWN_PACKS
            if not pack_component_consumers[pack_id]
        )
        if unused_packs:
            raise InvariantError(
                "QKU_SOURCE_CLAIM_WITHOUT_CONSUMER", repr(unused_packs)
            )
    alias_without_proof = [
        str(record["canonical_component_id"])
        for record in records
        for relation in record.get("relations", ())
        if relation.get("relation_type") == "ALIAS_OF"
        and not (
            relation.get("proof_refs")
            or relation.get("proof_ref")
            or record.get("definition", {}).get("equivalence_proof_refs")
        )
    ]
    if alias_without_proof:
        raise InvariantError("QKU_FORMULA_ALIAS_PROOF_MISSING", repr(alias_without_proof[:10]))

    source_qku_ids: set[str] | None = None
    if repo_root is not None:
        source_qku_ids = set()
        source_deadline = deadline or Deadline(3_600_000)
        source_deadline.check("QKU source universe receipt closure")
        for row in _read_jsonl(repo_root / RP5C_CANONICAL_LIBRARY):
            qku_id = row.get("qku_id")
            if qku_id not in (None, ""):
                source_qku_ids.add(str(qku_id))
        source_deadline.check("QKU source universe receipt closure")
        if len(source_qku_ids) != EXPECTED_CANONICAL_UNIQUE_QKUS:
            raise InvariantError(
                "QKU_SOURCE_UNIVERSE_DENOMINATOR",
                f"{len(source_qku_ids)} != {EXPECTED_CANONICAL_UNIQUE_QKUS}",
            )
        missing_source_qkus = sorted(source_qku_ids - canonical_qku_ids)
        if missing_source_qkus:
            raise InvariantError(
                "QKU_SOURCE_UNIVERSE_RECEIPT_MISSING",
                repr(missing_source_qkus[:20]),
            )
        if (
            len(canonical_qku_ids) != EXPECTED_CANONICAL_UNIQUE_QKUS
            or len(qku_role_keys) != EXPECTED_QKU_ROLE_KEYS
            or receipt_count != EXPECTED_QKU_ROLE_OCCURRENCES
        ):
            raise InvariantError(
                "QKU_CURRENT_UNIVERSE_DENOMINATOR",
                repr(
                    {
                        "unique_qkus": len(canonical_qku_ids),
                        "role_keys": len(qku_role_keys),
                        "role_occurrences": receipt_count,
                    }
                ),
            )
        if source_universe is not None:
            missing_agent_roles = [
                row
                for row in source_universe.get(
                    "agent_reachable_status_explain_selector_keys", ()
                )
                if (
                    str(row.get("qku_id", "")),
                    str(row.get("role_or_decision_stage", "")),
                    str(row.get("market_family", "")),
                )
                not in {key[:3] for key in qku_role_keys}
            ]
            if missing_agent_roles:
                raise InvariantError(
                    "QKU_AGENT_REACHABLE_RECEIPT_MISSING",
                    repr(missing_agent_roles[:20]),
                )

    def coverage(numerator: int, denominator: int) -> str:
        return "100%" if denominator == 0 or numerator == denominator else (
            f"{100 * numerator / denominator:.6f}%"
        )

    metrics = {
        "qku_verification_disposition_coverage": "100%",
        "qku_without_verification_receipt_count": 0,
        "qku_without_semantic_family_or_exact_unique_claim_count": 0,
        "qku_inheriting_without_equivalence_proof_count": 0,
        "qku_no_external_verification_without_reason_count": 0,
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
            venue_covered, venue_denominator
        ),
        "formula_alias_without_external_or_mathematical_equivalence_proof_count": 0,
        "current_fact_without_effective_date_or_TTL_count": 0,
        "material_source_conflict_without_blocker_count": 0,
        "source_claim_without_exact_QKU_or_component_consumer_count": 0,
        "qku_receipt_count": receipt_count,
        "canonical_unique_qku_count": len(canonical_qku_ids),
        "canonical_unique_qku_source_denominator": (
            len(source_qku_ids)
            if source_qku_ids is not None
            else len(canonical_qku_ids)
        ),
        "qku_role_key_count": len(qku_role_keys),
        "qku_role_occurrence_count": receipt_count,
        "verification_state_counts": dict(sorted(disposition_counts.items())),
        "claim_family_pack_reference_counts": dict(sorted(pack_counts.items())),
        "coverage_denominators": {
            "launch_QKU": launch_denominator,
            "live_candidate_QKU": live_denominator,
            "risk_and_accounting_QKU": risk_denominator,
            "venue_semantic_QKU": venue_denominator,
        },
        "zero_denominator_reasons": {
            "launch_QKU": (
                "No launch QKU is selected or manufactured; the five closed Decimal components have no direct QKU role."
                if launch_denominator == 0
                else None
            ),
            "live_candidate_QKU": (
                "CONTROL1 creates no replay/PAPER/shadow/canary/live QKU candidate."
                if live_denominator == 0
                else None
            ),
        },
    }
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
            raise InvariantError("QKU_VERIFICATION_COVERAGE", f"{name}={metrics[name]}")
    return metrics


def _independent_qku_source_claim_basis() -> dict[str, dict[str, set[str]]]:
    """Reviewed exact URL-to-component claim joins, independent of the builder."""

    formula = "QTT.COMP.CANDIDATE.FORMULA.{}".format
    closed = set(
        _CLOSED_DECIMAL_PRIMARY_COMPONENTS | _CLOSED_DECIMAL_DERIVATION_COMPONENTS
    )
    return {
        _QKU_PRICE_PACK: {
            "https://www.nber.org/papers/w12200": {
                formula("FAIR_PRICE_FROM_PROBABILITY"),
                formula("IMPLIED_PROBABILITY_FROM_BINARY_PRICE"),
                "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
            },
            "https://www.nber.org/system/files/working_papers/w10504/w10504.pdf": {
                formula("FAIR_PRICE_FROM_PROBABILITY"),
                formula("IMPLIED_PROBABILITY_FROM_BINARY_PRICE"),
                "QTT.COMP.FORMULA.IMPLIED_PROBABILITY",
            },
            "https://www.finra.org/rules-guidance/notices/01-16": {
                formula("SPREAD"), formula("POLY_SPREAD_001"),
                "QTT.COMP.FORMULA.SPREAD",
            },
            "https://documents1.worldbank.org/curated/en/099451004052417099/pdf/IDU100d4a04b1bdf71437d1858314d7e3194522c.pdf": {
                formula("SPREAD"), formula("POLY_SPREAD_001"),
                "QTT.COMP.FORMULA.MID_PRICE", "QTT.COMP.FORMULA.SPREAD",
                "QTT.COMP.FORMULA.RELATIVE_SPREAD",
            },
        },
        _QKU_DECIMAL_PACK: {
            "https://standards.ieee.org/ieee/754/6210/": closed,
            "https://docs.python.org/3.14/library/decimal.html": closed,
            "https://speleotrove.com/decimal/": closed,
        },
        _QKU_INSTITUTIONAL_PACK: {
            "https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml": {
                formula("BRIER_SCORE_BINARY"), formula("CALIB_BRIER_001")
            },
            "https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x": {formula("FDR_BH_001")},
            "https://onlinelibrary.wiley.com/doi/10.1002/j.1538-7305.1956.tb03809.x": {
                formula("KELLY_FRACTION"), formula("FRACTIONAL_KELLY"),
                formula("CAPPED_KELLY"), formula("PORT_KELLY_001"),
                formula("PORT_KELLY_002"),
            },
            "https://www.eecs.harvard.edu/cs286r/courses/fall10/papers/Gneiting07.pdf": {
                formula("BRIER_SCORE_BINARY"), formula("CALIB_BRIER_001"),
                formula("LOG_LOSS_BINARY"),
            },
            "https://proceedings.mlr.press/v70/guo17a.html": {
                formula("CALIBRATION_ERROR_CANDIDATE"), formula("CALIB_ECE_001")
            },
            "https://proceedings.mlr.press/v151/roelofs22a/roelofs22a.pdf": {
                formula("CALIBRATION_ERROR_CANDIDATE"), formula("CALIB_ECE_001")
            },
            "https://archive.org/details/newconceptsintec00wild": {formula("RSI")},
            "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html": {formula("EMA"), formula("MACD")},
            "https://www.bollingerbands.com/bollinger-bands": {formula("BOLLINGER_BANDS")},
            "https://www.finra.org/rules-guidance/notices/01-16": {formula("TCA_001"), formula("TCA_002")},
            "https://doi.org/10.21314/JOR.2001.041": {formula("TCA_001"), formula("TCA_002")},
            "https://www.pm-research.com/content/iijpormgmt/40/5/94": {formula("FDR_DSR_001")},
            "https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1952.tb01525.x": {formula("PORTFOLIO_QP_OBJECTIVE"), formula("COVARIANCE")},
            "https://www.sciencedirect.com/science/article/pii/S0047259X03000964": {formula("COVARIANCE")},
        },
        _QKU_QUANTUM_PACK: {
            "https://arxiv.org/abs/1411.4028": {formula("QAOA_HAMILTONIAN_MAPPING_CANDIDATE")},
            "https://doi.org/10.3389/fphy.2014.00005": {
                formula("QUBO_OBJECTIVE_X_T_Q_X"), formula("ISING_ENERGY"),
                formula("EXPANDED_QUBO_TERMS"),
            },
            "https://www.nature.com/articles/ncomms5213": {formula("VQE_OBJECTIVE_CANDIDATE")},
            "https://link.aps.org/doi/10.1103/PhysRevE.58.5355": {formula("ANNEALING_BQM_CQM_CANDIDATE")},
            "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html": {
                formula("QUBO_OBJECTIVE_X_T_Q_X"),
                formula("QAOA_HAMILTONIAN_MAPPING_CANDIDATE"),
                formula("CQM_OBJECTIVE_AND_CONSTRAINTS"),
            },
            "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html": {
                formula("QUBO_OBJECTIVE_X_T_Q_X"),
                formula("QAOA_HAMILTONIAN_MAPPING_CANDIDATE"),
                formula("CQM_OBJECTIVE_AND_CONSTRAINTS"),
            },
            "https://docs.dwavequantum.com/en/latest/quantum_research/reformulating.html": {
                formula("ANNEALING_BQM_CQM_CANDIDATE"), formula("BQM_ENERGY"),
                formula("CQM_OBJECTIVE_AND_CONSTRAINTS"),
            },
        },
        _QKU_PROVIDER_PACK: {
            "https://docs.kalshi.com/api-reference/market/get-market-candlesticks": {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002")},
            "https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks": {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002")},
            "https://docs.kalshi.com/getting_started/historical_data": {formula("KALSHI_CANDLES_001"), formula("KALSHI_CANDLES_002"), formula("KALSHI_TRADES_001")},
            "https://docs.kalshi.com/api-reference/market/get-market-orderbook": {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")},
            "https://docs.kalshi.com/getting_started/orderbook_responses": {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")},
            "https://docs.kalshi.com/getting_started/order_direction": {formula("KALSHI_ORDERBOOK_001"), formula("KALSHI_ORDERBOOK_002"), formula("KALSHI_ORDERBOOK_003")},
            "https://docs.kalshi.com/api-reference/market/get-trades": {formula("KALSHI_TRADES_001")},
            "https://docs.kalshi.com/getting_started/quick_start_websockets": {formula("KALSHI_WS_001"), formula("KALSHI_WS_002")},
            "https://docs.kalshi.com/changelog": {formula("KALSHI_TICK_001")},
            "https://kalshi.com/docs/kalshi-fee-schedule.pdf": {formula("KALSHI_FEE_001")},
            "https://docs.kalshi.com/getting_started/fee_rounding": {formula("KALSHI_FEE_001")},
            "https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes": {formula("KALSHI_FEE_001")},
            "https://docs.polymarket.com/api-reference/market-data/get-spread": {formula("POLY_SPREAD_001")},
            "https://docs.polymarket.com/api-reference/market-data/get-order-book": {formula("POLY_BOOK_001"), formula("POLY_BOOK_002")},
            "https://docs.polymarket.com/trading/orderbook": {formula("POLY_BOOK_001"), formula("POLY_BOOK_002"), formula("POLY_MID_001"), formula("POLY_SPREAD_001")},
            "https://docs.polymarket.com/api-reference/markets/get-prices-history": {formula("POLY_HISTORY_001")},
            "https://docs.polymarket.com/api-reference/market-data/get-last-trade-price": {formula("POLY_LAST_001")},
            "https://docs.polymarket.com/api-reference/market-data/get-midpoint-prices-query-parameters": {formula("POLY_MID_001")},
            "https://docs.polymarket.com/concepts/prices-orderbook": {formula("POLY_MID_001")},
            "https://docs.polymarket.com/trading/fees": {formula("POLY_TICK_001")},
            "https://docs.polymarket.com/builders/fees": {formula("POLY_TICK_001")},
            "https://docs.polymarket.com/v2-migration": {formula("POLY_TICK_001")},
            "https://docs.polymarket.com/api-reference/wss/market": {formula("POLY_WS_001")},
            "https://docs.polymarket.com/market-data/websocket/overview": {formula("POLY_WS_001")},
        },
        _QKU_UNRESOLVED_PACK: {},
    }


def _validate_qku_acceptance_source_packs(
    artifact_dir: Path,
    records: Sequence[Mapping[str, Any]],
    independently_derived: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare compact report-only source packs to independent registry facts."""

    report_path = artifact_dir / "acceptance.report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvariantError("QKU_SOURCE_PACK_REPORT", str(exc)) from exc
    qku_section = report.get("qku_verification")
    if not isinstance(qku_section, Mapping):
        raise InvariantError("QKU_SOURCE_PACK_REPORT", "missing qku_verification")
    for metric_name in (
        "qku_verification_disposition_coverage",
        "qku_without_verification_receipt_count",
        "qku_without_semantic_family_or_exact_unique_claim_count",
        "qku_inheriting_without_equivalence_proof_count",
        "qku_no_external_verification_without_reason_count",
        "launch_QKU_external_or_derivation_verification_coverage",
        "launch_QKU_verification_disposition_coverage",
        "launch_QKU_positive_verified_count",
        "launch_QKU_unresolved_or_rejected_count",
        "live_candidate_QKU_verification_coverage",
        "live_candidate_QKU_verification_disposition_coverage",
        "live_candidate_QKU_positive_verified_count",
        "live_candidate_QKU_unresolved_or_rejected_count",
        "risk_and_accounting_QKU_verification_coverage",
        "risk_and_accounting_QKU_positive_verification_coverage",
        "risk_and_accounting_QKU_verified_count",
        "risk_and_accounting_QKU_blocked_count",
        "risk_and_accounting_QKU_unresolved_or_rejected_count",
        "risk_and_accounting_QKU_disposition_coverage",
        "venue_semantic_QKU_official_source_coverage",
        "formula_alias_without_external_or_mathematical_equivalence_proof_count",
        "current_fact_without_effective_date_or_TTL_count",
        "material_source_conflict_without_blocker_count",
        "source_claim_without_exact_QKU_or_component_consumer_count",
        "canonical_unique_qku_count",
        "qku_role_key_count",
        "qku_role_occurrence_count",
    ):
        if qku_section.get(metric_name) != independently_derived.get(metric_name):
            raise InvariantError(
                "QKU_ACCEPTANCE_METRIC_MISMATCH",
                f"{metric_name}: report={qku_section.get(metric_name)!r}, independent={independently_derived.get(metric_name)!r}",
            )
    packs = qku_section.get("shared_claim_family_source_packs")
    if not isinstance(packs, list):
        raise InvariantError("QKU_SOURCE_PACK_SHAPE", "packs must be a list")
    by_id = {
        str(pack.get("claim_family_pack_id", "")): pack
        for pack in packs
        if isinstance(pack, Mapping)
    }
    if set(by_id) != _QKU_KNOWN_PACKS:
        raise InvariantError(
            "QKU_SOURCE_PACK_SET",
            f"observed={sorted(by_id)}, expected={sorted(_QKU_KNOWN_PACKS)}",
        )
    expected_consumers: dict[str, set[str]] = defaultdict(set)
    expected_occurrences: Counter[str] = Counter()
    expected_component_occurrences: Counter[tuple[str, str]] = Counter()
    expected_role_refs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    expected_binding_ids: dict[str, list[str]] = {}
    expected_downstream_consumers: dict[str, list[str]] = {}
    semantic_versions = {
        str(record["canonical_component_id"]): str(record["semantic_version"])
        for record in records
    }
    for record in records:
        component_id = str(record["canonical_component_id"])
        expected_binding_ids[component_id] = sorted(
            str(binding.get("binding_id", ""))
            for binding in record.get("bindings", ())
            if binding.get("binding_id") not in (None, "")
        )
        expected_downstream_consumers[component_id] = sorted(
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
        for role in record.get("uses", {}).get("qku_role_bindings", ()):
            for pack_id in role.get("qku_verification_receipt", {}).get(
                "claim_family_source_pack_ids", ()
            ):
                expected_consumers[str(pack_id)].add(component_id)
                expected_occurrences[str(pack_id)] += 1
                expected_component_occurrences[(str(pack_id), component_id)] += 1
                expected_role_refs[(str(pack_id), component_id)].append(
                    {
                        "qku_role_ref": _independent_qku_role_ref(role),
                        "binding_applicability": (
                            _independent_qku_role_applicability_signature(
                                record, role
                            )
                        ),
                    }
                )
    existing_ids = {str(record["canonical_component_id"]) for record in records}
    closed_ids = (
        _CLOSED_DECIMAL_PRIMARY_COMPONENTS | _CLOSED_DECIMAL_DERIVATION_COMPONENTS
    ).intersection(existing_ids)
    expected_consumers[_QKU_PRICE_PACK].update(
        closed_ids.intersection(_CLOSED_DECIMAL_PRICE_COMPONENTS)
    )
    expected_consumers[_QKU_DECIMAL_PACK].update(closed_ids)
    claim_basis = _independent_qku_source_claim_basis()
    required_source_fields = {
        "url",
        "publisher",
        "publication_or_version_date",
        "retrieval_date",
        "source_class",
        "exact_claim_used",
        "applicable_scope",
        "ttl",
        "official_effective_date_or_null",
        "observed_as_of_or_retrieval_date",
        "recheck_triggers",
    }
    source_count = 0
    for pack_id, pack in by_id.items():
        if int(pack.get("exact_component_consumer_count", -1)) != len(
            expected_consumers[pack_id]
        ) or int(pack.get("exact_qku_consumer_count", -1)) != expected_occurrences[
            pack_id
        ]:
            raise InvariantError("QKU_SOURCE_PACK_CONSUMER_COUNT", pack_id)
        consumers = pack.get("exact_claim_consumers")
        if not isinstance(consumers, list) or not consumers:
            raise InvariantError("QKU_SOURCE_CLAIM_WITHOUT_CONSUMER", pack_id)
        explicit_ids = {
            str(item.get("canonical_component_id", ""))
            for item in consumers
            if isinstance(item, Mapping)
            and item.get("consumer_kind") == "CANONICAL_COMPONENT"
        }
        set_rows = [
            item
            for item in consumers
            if isinstance(item, Mapping)
            and item.get("consumer_kind") == "CANONICAL_QKU_RECEIPT_SET"
        ]
        if len(expected_consumers[pack_id]) <= 500:
            if explicit_ids != expected_consumers[pack_id] or set_rows:
                raise InvariantError("QKU_SOURCE_PACK_CONSUMER_JOIN", pack_id)
        else:
            if len(set_rows) != 1 or explicit_ids:
                raise InvariantError("QKU_SOURCE_PACK_CONSUMER_JOIN", pack_id)
            set_row = set_rows[0]
            if (
                int(set_row.get("canonical_component_count", -1))
                != len(expected_consumers[pack_id])
                or int(set_row.get("qku_role_occurrence_count", -1))
                != expected_occurrences[pack_id]
                or set(set_row.get("exact_join_fields", ()))
                != {
                    "canonical_component_id",
                    "semantic_version",
                    "qku_id",
                    "role_or_decision_stage",
                    "market_family",
                    "context_selector",
                    "claim_family_source_pack_ids",
                }
            ):
                raise InvariantError("QKU_SOURCE_PACK_CONSUMER_JOIN", pack_id)
        disposition = pack.get("conflict_disposition")
        if not isinstance(disposition, Mapping):
            raise InvariantError("QKU_SOURCE_CONFLICT_DISPOSITION", pack_id)
        state = disposition.get("state")
        if state == "RESOLVED_WITH_AUTHORITATIVE_BASIS_AND_BOUNDED_SCOPE":
            if not disposition.get("authoritative_basis_urls") or disposition.get(
                "unresolved_blocker_or_null"
            ) is not None:
                raise InvariantError("QKU_SOURCE_CONFLICT_DISPOSITION", pack_id)
        elif state == "UNRESOLVED_MATERIAL_BLOCKER":
            if not disposition.get("unresolved_blocker_or_null"):
                raise InvariantError("QKU_SOURCE_CONFLICT_DISPOSITION", pack_id)
        else:
            raise InvariantError("QKU_SOURCE_CONFLICT_DISPOSITION", pack_id)
        sources = pack.get("sources", ())
        if not isinstance(sources, list):
            raise InvariantError("QKU_SOURCE_PACK_SHAPE", f"{pack_id}: sources")
        source_urls = [str(source.get("url", "")) for source in sources if isinstance(source, Mapping)]
        if len(source_urls) != len(set(source_urls)) or set(source_urls) != set(
            claim_basis[pack_id]
        ):
            raise InvariantError(
                "QKU_SOURCE_PACK_URL_SET",
                f"{pack_id}: observed={sorted(source_urls)}, expected={sorted(claim_basis[pack_id])}",
            )
        if set(disposition.get("authoritative_basis_urls", ())) != set(source_urls):
            raise InvariantError("QKU_SOURCE_CONFLICT_DISPOSITION", pack_id)
        if pack_id != _QKU_UNRESOLVED_PACK and not sources:
            raise InvariantError("QKU_SOURCE_PACK_EMPTY", pack_id)
        for source in sources:
            source_count += 1
            if not isinstance(source, Mapping) or not required_source_fields.issubset(
                source
            ):
                raise InvariantError("QKU_SOURCE_CLAIM_SHAPE", pack_id)
            required_nonempty_fields = required_source_fields - {
                "official_effective_date_or_null"
            }
            if any(
                source.get(field) in (None, "", [], {})
                for field in required_nonempty_fields
            ):
                raise InvariantError("QKU_SOURCE_CLAIM_SHAPE", pack_id)
            if not str(source["url"]).startswith("https://"):
                raise InvariantError("QKU_SOURCE_CLAIM_URL", str(source["url"]))
            if source.get("retrieval_date") != "2026-07-14":
                raise InvariantError("QKU_SOURCE_CLAIM_RETRIEVAL", str(source["url"]))
            if source.get("source_class") not in {
                "PRIMARY_RESEARCH",
                "PRIMARY_PREPRINT",
                "PRIMARY_PEER_REVIEWED_RESEARCH",
                "OFFICIAL_STANDARD",
                "OFFICIAL_LIBRARY_DOCUMENTATION",
                "OFFICIAL_OPEN_SOURCE_DOCUMENTATION",
                "OFFICIAL_PROVIDER_DOCUMENTATION",
                "OFFICIAL_CURRENT_DOCUMENTATION",
                "OFFICIAL_SRO_DOCUMENTATION",
                "ORIGINAL_SPECIFICATION",
                "ORIGINAL_METHOD_SOURCE",
                "ORIGINAL_METHOD_DOCUMENTATION",
                "REPUTABLE_INSTITUTIONAL",
            }:
                raise InvariantError("QKU_SOURCE_CLASS", str(source["url"]))
            if not (
                source.get("official_effective_date_or_null")
                or source.get("observed_as_of_or_retrieval_date")
            ):
                raise InvariantError("QKU_CURRENT_FACT_TIME_MISSING", str(source["url"]))
            if source.get("source_claim_id") in (None, ""):
                raise InvariantError("QKU_SOURCE_CLAIM_ID", str(source["url"]))
            if pack_id == _QKU_PROVIDER_PACK and (
                source.get("ttl")
                != "P30D_RESEARCH_RECHECK_BEFORE_PROMOTION_OR_EXECUTION"
                or set(source.get("recheck_triggers", ()))
                != {
                    "PINNED_VERSION_OR_DOCUMENTATION_CHANGE",
                    "BEFORE_ANY_PROMOTION_OR_EXECUTION",
                }
            ):
                raise InvariantError("QKU_CURRENT_FACT_RECHECK_MISSING", str(source["url"]))
        claims = pack.get("claims")
        if not isinstance(claims, list) or len(claims) != len(sources):
            raise InvariantError("QKU_SOURCE_CLAIM_SHAPE", f"{pack_id}: claims")
        claims_by_url: dict[str, Mapping[str, Any]] = {}
        source_by_url = {str(source["url"]): source for source in sources}
        for claim in claims:
            if not isinstance(claim, Mapping) or len(claim.get("source_url_refs", ())) != 1:
                raise InvariantError("QKU_SOURCE_CLAIM_SHAPE", pack_id)
            source_url = str(claim["source_url_refs"][0])
            if source_url in claims_by_url or source_url not in source_by_url:
                raise InvariantError("QKU_SOURCE_CLAIM_URL", source_url)
            source = source_by_url[source_url]
            if (
                claim.get("claim_id") != source.get("source_claim_id")
                or claim.get("exact_claim_text") != source.get("exact_claim_used")
                or claim.get("applicable_scope") != source.get("applicable_scope")
                or str(source.get("applicable_scope", ""))
                not in str(claim.get("exact_claim_text", ""))
                or "does not prove implementation correctness" not in str(
                    claim.get("exact_claim_text", "")
                )
                or not claim.get("affected_registry_fields")
                or not claim.get("test_oracle_refs")
                or claim.get("effective_date_or_null")
                != source.get("official_effective_date_or_null")
                or claim.get("observed_as_of_or_retrieval_date")
                != source.get("observed_as_of_or_retrieval_date")
                or claim.get("ttl") != source.get("ttl")
                or claim.get("conflict_disposition_ref")
                != f"{pack_id}.conflict_disposition"
            ):
                raise InvariantError("QKU_SOURCE_CLAIM_SHAPE", source_url)
            observed_component_rows = claim.get("exact_component_consumers")
            if not isinstance(observed_component_rows, list):
                raise InvariantError("QKU_SOURCE_CLAIM_CONSUMER_JOIN", source_url)
            observed_components = {
                str(row.get("canonical_component_id", "")): row
                for row in observed_component_rows
                if isinstance(row, Mapping)
            }
            expected_claim_components = claim_basis[pack_id][source_url].intersection(
                expected_consumers[pack_id]
            )
            if set(observed_components) != expected_claim_components:
                raise InvariantError("QKU_SOURCE_CLAIM_CONSUMER_JOIN", source_url)
            for component_id, row in observed_components.items():
                if (
                    row.get("semantic_version") != semantic_versions[component_id]
                    or int(row.get("qku_role_occurrence_count", -1))
                    != expected_component_occurrences[(pack_id, component_id)]
                    or row.get("exact_qku_role_applicability_refs")
                    != sorted(
                        expected_role_refs[(pack_id, component_id)],
                        key=_canonical_json,
                    )
                    or row.get("exact_binding_ids")
                    != expected_binding_ids[component_id]
                    or row.get("downstream_consumer_classes")
                    != expected_downstream_consumers[component_id]
                ):
                    raise InvariantError("QKU_SOURCE_CLAIM_CONSUMER_JOIN", source_url)
            claims_by_url[source_url] = claim
        if set(claims_by_url) != set(source_urls):
            raise InvariantError("QKU_SOURCE_CLAIM_URL", pack_id)
        claim_union = {
            str(row["canonical_component_id"])
            for claim in claims
            for row in claim["exact_component_consumers"]
        }
        if pack_id != _QKU_UNRESOLVED_PACK and claim_union != expected_consumers[pack_id]:
            raise InvariantError("QKU_SOURCE_CLAIM_CONSUMER_CLOSURE", pack_id)
    qiskit = next(
        source
        for source in by_id[_QKU_QUANTUM_PACK]["sources"]
        if "qiskit-optimization" in str(source.get("url", ""))
    )
    if "0.7.0" not in str(qiskit.get("publication_or_version_date", "")):
        raise InvariantError("QKU_QISKIT_VERSION", repr(qiskit))
    qiskit_conflict = str(qiskit.get("version_conflict_resolution", ""))
    if "penalty=None" not in qiskit_conflict or "no universal penalty default" not in qiskit_conflict:
        raise InvariantError("QKU_QISKIT_PENALTY_CONFLICT", qiskit_conflict)
    dwave = next(
        source
        for source in by_id[_QKU_QUANTUM_PACK]["sources"]
        if "dwavequantum" in str(source.get("url", ""))
    )
    if "9.4.0" not in str(dwave.get("publication_or_version_date", "")):
        raise InvariantError("QKU_DWAVE_VERSION", repr(dwave))
    provider_by_url = {
        str(source["url"]): source
        for source in by_id[_QKU_PROVIDER_PACK]["sources"]
    }
    kalshi_fee = provider_by_url["https://kalshi.com/docs/kalshi-fee-schedule.pdf"]
    if (
        kalshi_fee.get("official_effective_date_or_null") != "2026-07-07"
        or "M*0.07*C*P*(1-P)" not in str(kalshi_fee.get("exact_claim_used", ""))
        or "historical 0.035 candidate" not in str(kalshi_fee.get("exact_claim_used", ""))
    ):
        raise InvariantError("QKU_KALSHI_FEE_CONFLICT", repr(kalshi_fee))
    polymarket_v2 = provider_by_url["https://docs.polymarket.com/v2-migration"]
    if polymarket_v2.get("official_effective_date_or_null") != "2026-04-28":
        raise InvariantError("QKU_POLYMARKET_V2_EFFECTIVE_DATE", repr(polymarket_v2))
    expected_conflicts = {
        "QKU.CONFLICT.KALSHI_FEE_001.CURRENT_SCHEDULE.V1": (
            {"QTT.COMP.CANDIDATE.FORMULA.KALSHI_FEE_001"},
            {
                "https://kalshi.com/docs/kalshi-fee-schedule.pdf",
                "https://docs.kalshi.com/getting_started/fee_rounding",
                "https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes",
            },
            "HISTORICAL_COEFFICIENT_AND_UNIT_CONTRADICT_CURRENT_SERIES_SCOPED_SCHEDULE",
            "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
        ),
        "QKU.CONFLICT.POLY_TICK_001.DYNAMIC_FEE.V1": (
            {"QTT.COMP.CANDIDATE.FORMULA.POLY_TICK_001"},
            {
                "https://docs.polymarket.com/trading/fees",
                "https://docs.polymarket.com/builders/fees",
                "https://docs.polymarket.com/v2-migration",
            },
            "PLATFORM_VS_BUILDER_FEE_SCOPE_AND_DYNAMIC_MARKET_RATE_UNRESOLVED",
            "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
        ),
        "QKU.CONFLICT.POLY_SPREAD_001.COST_INCIDENCE.V1": (
            {"QTT.COMP.CANDIDATE.FORMULA.POLY_SPREAD_001"},
            {"https://docs.polymarket.com/api-reference/market-data/get-spread", "https://docs.polymarket.com/trading/orderbook"},
            "QUANTITY_UNIT_AND_EXECUTION_COST_INCIDENCE_UNRESOLVED",
            "RECHECK.QKU.MUTABLE_PROVIDER.P30D.PRE_PROMOTION",
        ),
        "QKU.CONFLICT.QISKIT_0_7_PENALTY_DEFAULT.V1": (
            {
                "QTT.COMP.CANDIDATE.FORMULA.QUBO_OBJECTIVE_X_T_Q_X",
                "QTT.COMP.CANDIDATE.FORMULA.QAOA_HAMILTONIAN_MAPPING_CANDIDATE",
                "QTT.COMP.CANDIDATE.FORMULA.CQM_OBJECTIVE_AND_CONSTRAINTS",
            },
            {
                "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
                "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.converters.QuadraticProgramToQubo.html",
            },
            "CONVERTER_CLASS_VERSION_PENALTY_AND_FEASIBILITY_NOT_PINNED",
            "RECHECK.QKU.SEMANTIC_OR_IMPLEMENTATION_CHANGE",
        ),
    }
    conflict_rows = [
        row
        for pack_id in (_QKU_PROVIDER_PACK, _QKU_QUANTUM_PACK)
        for row in by_id[pack_id].get("material_component_conflicts", ())
        if isinstance(row, Mapping)
    ]
    conflicts_by_id = {str(row.get("conflict_id", "")): row for row in conflict_rows}
    if set(conflicts_by_id) != set(expected_conflicts):
        raise InvariantError("QKU_MATERIAL_CONFLICT_SET", repr(sorted(conflicts_by_id)))
    source_claim_by_url = {
        str(source["url"]): str(source["source_claim_id"])
        for pack_id in (_QKU_PROVIDER_PACK, _QKU_QUANTUM_PACK)
        for source in by_id[pack_id]["sources"]
    }
    for conflict_id, (component_ids, urls, blocker, recheck_policy) in expected_conflicts.items():
        row = conflicts_by_id[conflict_id]
        if (
            set(row.get("affected_component_ids", ())) != component_ids
            or set(row.get("authoritative_urls", ())) != urls
            or set(row.get("source_claim_ids", ()))
            != {source_claim_by_url[url] for url in urls}
            or row.get("disposition") != "UNRESOLVED_MATERIAL_BLOCKER"
            or row.get("blocker") != blocker
            or row.get("recheck_policy_id") != recheck_policy
            or not row.get("repository_claim")
            or not row.get("authoritative_current_claim")
            or not row.get("exact_next_action")
        ):
            raise InvariantError("QKU_MATERIAL_CONFLICT_SHAPE", conflict_id)
    blocker_policies = qku_section.get("shared_blocker_policy_packs")
    if not isinstance(blocker_policies, list) or not blocker_policies:
        raise InvariantError("QKU_SHARED_BLOCKER_PACK", "missing")
    blocker_ids = {
        str(item.get("blocker_policy_id", ""))
        for item in blocker_policies
        if isinstance(item, Mapping)
    }
    referenced_blockers = {
        str(role.get("qku_verification_receipt", {}).get("blocker_policy_id", ""))
        for record in records
        for role in record.get("uses", {}).get("qku_role_bindings", ())
        if role.get("qku_verification_receipt", {}).get("blocker_policy_id")
    }
    if blocker_ids != referenced_blockers:
        raise InvariantError("QKU_SHARED_BLOCKER_PACK", "reference mismatch")
    crosswalk = qku_section.get("qku_to_verification_crosswalk_rows")
    expected_groups: dict[
        tuple[str, tuple[str, ...], str, str], dict[str, Any]
    ] = {}
    for record in records:
        component_id = str(record["canonical_component_id"])
        for role in record.get("uses", {}).get("qku_role_bindings", ()):
            receipt = role["qku_verification_receipt"]
            key = (
                str(receipt["verification_state"]),
                tuple(str(value) for value in receipt["claim_family_source_pack_ids"]),
                (
                    "RESOLVED_CANONICAL_SEMANTICS"
                    if receipt.get("semantic_family_id")
                    else "UNRESOLVED_EXACT_QKU_CLAIM_CUSTODY"
                ),
                str(receipt.get("blocker_code") or "NONE"),
            )
            group = expected_groups.setdefault(
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
            group["canonical_qku_ids"].add(str(role.get("qku_id", "")))
            group["canonical_component_ids"].add(component_id)
            group["role_keys"].add(
                (
                    str(role.get("qku_id", "")),
                    str(role.get("role_or_decision_stage", "")),
                    str(role.get("market_family", "")),
                    _canonical_json(role.get("context_selector")),
                )
            )
    expected_crosswalk: list[dict[str, Any]] = []
    for index, key in enumerate(sorted(expected_groups), 1):
        group = expected_groups[key]
        expected_crosswalk.append(
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
    if not isinstance(crosswalk, list) or _canonical_json(crosswalk) != _canonical_json(
        expected_crosswalk
    ):
        raise InvariantError("QKU_CROSSWALK_COVERAGE", "exact group mismatch")
    return {
        "claim_family_pack_count": len(by_id),
        "source_claim_count": source_count,
        "exact_consumer_join_count": sum(
            len(pack["exact_claim_consumers"]) for pack in by_id.values()
        ),
        "crosswalk_group_count": len(crosswalk),
        "acceptance_pass_fields_trusted": False,
    }


def _validate_qku_unambiguity(records: Sequence[Mapping[str, Any]]) -> int:
    roots: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    selection_policy: dict[tuple[str, str, str, str], bool] = defaultdict(bool)
    for record in records:
        if record.get("record_state") not in RUNTIME_ACTIVE_RECORD_STATES:
            continue
        component_id = str(record["canonical_component_id"])
        kind = str(record["definition"]["component_kind"])
        binding_contexts = [
            _canonical_json(binding.get("context_selector")) for binding in record.get("bindings", [])
        ] or ["null"]
        for qku in record["uses"]["qku_role_bindings"]:
            if not isinstance(qku, Mapping):
                raise InvariantError("QKU_BINDING_SHAPE", component_id)
            qku_id = str(qku.get("qku_id", ""))
            role = str(qku.get("role_or_decision_stage", ""))
            market = str(qku.get("market_family", ""))
            explicit_context = qku.get("context_selector")
            contexts = [_canonical_json(explicit_context)] if explicit_context is not None else binding_contexts
            target = str(qku.get("stack_root_or_direct_component") or component_id)
            if not qku_id or not role or not market or not target:
                raise InvariantError("QKU_BINDING_SHAPE", f"{component_id}: {qku!r}")
            for context in contexts:
                key = (qku_id, role, market, context)
                roots[key].add(target)
                if kind == "QKU_SELECTION_POLICY" or qku.get("selection_rule_if_container"):
                    selection_policy[key] = True
    ambiguous = [key for key, values in roots.items() if len(values) > 1 and not selection_policy[key]]
    if ambiguous:
        raise InvariantError("AMBIGUOUS_QKU_ROOT", repr(ambiguous[:10]))
    return len(roots)


def _source_row_values(row: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = row.get(field)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item not in (None, ""))
    if value in (None, ""):
        return ()
    return (str(value),)


def _independent_candidate_token(value: Any) -> str:
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
        raise InvariantError("SOURCE_SELECTION_COMPONENT_ID", repr(value))
    return token


def _independent_source_selection_tuple(
    row: Mapping[str, Any],
    *,
    formula_field: str,
    algorithm_field: str,
    parameter_field: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    value = (
        _source_row_values(row, formula_field),
        _source_row_values(row, algorithm_field),
        _source_row_values(row, parameter_field),
    )
    if any(len(part) != 1 for part in value):
        raise InvariantError("SOURCE_SELECTION_TUPLE", repr(value))
    return value


def _independent_gfp_discovery_has_complete_typed_semantics(
    row: Mapping[str, Any],
) -> bool:
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


def _independent_source_vector_values_equal(
    actual: Any, expected: Any, tolerance: float
) -> bool:
    if isinstance(actual, Mapping) and isinstance(expected, Mapping):
        return set(actual) == set(expected) and all(
            _independent_source_vector_values_equal(
                actual[key], expected[key], tolerance
            )
            for key in actual
        )
    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _independent_source_vector_values_equal(left, right, tolerance)
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


def _independently_invoke_pr162b_source_vectors(
    rows: Sequence[Mapping[str, Any]], deadline: Deadline
) -> dict[str, Any]:
    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in PR162B_IMPLEMENTATION_MODULE_ALLOWLIST
    }
    counts: Counter[str] = Counter()
    callable_refs: set[str] = set()
    for index, row in enumerate(rows):
        if index % 25 == 0:
            deadline.check("independent PR162B source vectors")
        module_name = str(row.get("implementation_module", ""))
        function_name = str(row.get("implementation_function", ""))
        if module_name not in modules or not re.fullmatch(
            r"[a-z][a-z0-9_]*", function_name
        ):
            raise InvariantError(
                "PR162B_FIXED_IMPLEMENTATION_ALLOWLIST",
                f"{module_name}:{function_name}",
            )
        implementation = getattr(modules[module_name], function_name, None)
        if not callable(implementation):
            raise InvariantError(
                "PR162B_IMPLEMENTATION_IMPORT", f"{module_name}:{function_name}"
            )
        inputs = row.get("inputs")
        if not isinstance(inputs, Mapping):
            raise InvariantError(
                "PR162B_TYPED_SOURCE_VECTOR", str(row.get("test_vector_id"))
            )
        actual = implementation(**copy.deepcopy(dict(inputs)))
        tolerance = float(row.get("tolerance", 0.0))
        if tolerance < 0 or not _independent_source_vector_values_equal(
            actual, row.get("expected_output"), tolerance
        ):
            raise InvariantError(
                "PR162B_SOURCE_VECTOR_MISMATCH", str(row.get("test_vector_id"))
            )
        target = str(row.get("formula_id_or_algorithm_id", ""))
        counts["FORMULA" if target.startswith("PR162B-FORMULA-") else "ALGORITHM"] += 1
        callable_refs.add(f"{module_name}:{function_name}")
    if dict(counts) != {"FORMULA": 61, "ALGORITHM": 14}:
        raise InvariantError("PR162B_SOURCE_VECTOR_DENOMINATOR", repr(counts))
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


def _independent_normalized_gfp_callable_ref(path: Any, function: Any) -> str:
    path_text = str(path or "").replace("\\", "/")
    function_text = str(function or "")
    prefix = "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/"
    if (
        not path_text.startswith(prefix)
        or not path_text.endswith(".py")
        or not re.fullmatch(r"[a-z][a-z0-9_]*", function_text)
    ):
        raise InvariantError(
            "GFP_IMPORTABLE_IMPLEMENTATION_REF", f"{path_text}:{function_text}"
        )
    module_name = "src.qtt." + path_text[len("src/qtt/") : -3].replace("/", ".")
    if module_name not in GFP_IMPLEMENTATION_MODULE_ALLOWLIST:
        raise InvariantError("GFP_IMPLEMENTATION_ALLOWLIST", module_name)
    if not callable(getattr(importlib.import_module(module_name), function_text, None)):
        raise InvariantError(
            "GFP_IMPLEMENTATION_IMPORT", f"{module_name}:{function_text}"
        )
    return f"{module_name}:{function_text}"


def _independent_rp5c_reference_custody_rows(
    repo_root: Path, deadline: Deadline
) -> dict[str, dict[str, Any]]:
    """Independently reconstruct RP5C references and their six-field custody."""

    path = repo_root / RP5C_CANONICAL_LIBRARY
    by_identity: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 1_000 == 0:
                deadline.check("RP5D RP5C reference custody")
            row = json.loads(line)
            identity_ref = row.get("canonical_identity_row_id")
            if (
                not isinstance(identity_ref, str)
                or not RP5C_ID_RE.fullmatch(identity_ref)
                or identity_ref in by_identity
            ):
                raise InvariantError(
                    "RP5D_RP5C_REFERENCE_CUSTODY",
                    f"{path.as_posix()}:{line_number}: {identity_ref!r}",
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
                    raise InvariantError(
                        "RP5D_RP5C_REFERENCE_CUSTODY",
                        f"{identity_ref}: {source_field}={raw!r}",
                    )
            by_identity[identity_ref] = {
                **references,
                "custody_key": _rp5c_group_custody_tuple(
                    _rp5c_group_custody_key(row),
                    code="RP5D_RP5C_REFERENCE_CUSTODY",
                ),
            }
    if len(by_identity) != EXPECTED_RP5C_CANONICAL:
        raise InvariantError(
            "RP5D_RP5C_REFERENCE_CUSTODY",
            f"{len(by_identity)}/{EXPECTED_RP5C_CANONICAL}",
        )
    return by_identity


def _independent_rp5d_reference_mapping(
    row: Mapping[str, Any],
    *,
    source_path: str,
    rp5c_reference_rows: Mapping[str, Mapping[str, Any]],
    identity_targets: Mapping[str, set[str]],
    target_custody_keys: Mapping[str, set[tuple[str, ...]]],
) -> dict[str, Any]:
    """Resolve one RP5D row without global formula/QKU name lookup."""

    identity_ref = row.get("identity_ref")
    if not isinstance(identity_ref, str) or identity_ref not in rp5c_reference_rows:
        raise InvariantError(
            "RP5D_IDENTITY_CUSTODY_MAPPING",
            f"{source_path}: {identity_ref!r}",
        )
    source = rp5c_reference_rows[identity_ref]
    targets = set(identity_targets.get(identity_ref, set()))
    if len(targets) != 1:
        raise InvariantError(
            "RP5D_IDENTITY_CUSTODY_MAPPING",
            f"{source_path}: {identity_ref}: targets={sorted(targets)}",
        )
    target = next(iter(targets))
    expected_custody = tuple(source["custody_key"])
    observed_custodies = set(target_custody_keys.get(target, set()))
    if observed_custodies != {expected_custody}:
        raise InvariantError(
            "RP5D_IDENTITY_CUSTODY_MAPPING",
            f"{source_path}: {identity_ref} -> {target}: "
            f"custody={sorted(observed_custodies)!r}",
        )

    real_references: dict[str, str] = {}
    absence_dispositions: dict[str, str] = {}
    for kind, field in (("FORMULA", "formula_ref"), ("QKU", "qku_ref")):
        observed = row.get(field)
        if not isinstance(observed, str) or not observed:
            raise InvariantError(
                f"RP5D_{kind}_REFERENCE_MAPPING",
                f"{source_path}: {identity_ref}: missing {field}",
            )
        expected = source[field]
        if expected is None:
            absent = f"{identity_ref}::{kind}_REF_NOT_PRESENT"
            if observed != absent:
                raise InvariantError(
                    f"RP5D_{kind}_REFERENCE_MAPPING",
                    f"{source_path}: {identity_ref}: {observed!r} != {absent!r}",
                )
            absence_dispositions[kind] = absent
        else:
            if observed != expected:
                raise InvariantError(
                    f"RP5D_{kind}_REFERENCE_MAPPING",
                    f"{source_path}: {identity_ref}: {observed!r} != {expected!r}",
                )
            real_references[kind] = observed
    return {
        "target": target,
        "real_references": real_references,
        "absence_dispositions": absence_dispositions,
    }


def _independent_reference_targets_resolved(
    targets: set[str], expected_targets: set[str] | None = None
) -> bool:
    """Require one unambiguous target unless a caller pins an explicit set."""

    if expected_targets is not None:
        return bool(expected_targets) and expected_targets.issubset(targets)
    return len(targets) == 1


def _validate_source_universe_closure(
    repo_root: Path,
    records: Sequence[Mapping[str, Any]],
    deadline: Deadline,
) -> dict[str, Any]:
    """Independently classify every declared computation-universe source row."""

    record_by_id = {
        str(record["canonical_component_id"]): record for record in records
    }
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
    owner_context_selection_tuples: set[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]
    ] = set()
    accepted_ids = {
        component_id
        for component_id, record in record_by_id.items()
        if record.get("record_state") in ACCEPTED_STATES
    }

    for index, record in enumerate(records):
        if index % 500 == 0:
            deadline.check("source closure registry index")
        component_id = str(record["canonical_component_id"])
        origins = {str(value) for value in record.get("origin_cohorts", ())}
        if "POST_LAUNCH_EXPANSION_BATCH" in origins or any(
            origin.startswith(("VALIDATOR_SYNTHETIC", "TEST_SYNTHETIC"))
            for origin in origins
        ):
            raise InvariantError(
                "CANONICAL_SYNTHETIC_SOURCE", f"{component_id}: {sorted(origins)}"
            )
        mutation_surface = {
            "origin_cohorts": record.get("origin_cohorts", ()),
            "provenance": record.get("provenance", ()),
            "relations": record.get("relations", ()),
            "uses": record.get("uses", {}),
            "bindings": [
                {
                    "binding_id": binding.get("binding_id"),
                    "context_selector": binding.get("context_selector"),
                    "selected_parameter_policy": binding.get(
                        "selected_parameter_policy"
                    ),
                }
                for binding in record.get("bindings", ())
                if isinstance(binding, Mapping)
            ],
        }
        forbidden_synthetic_tokens = (
            "EXPANSION.CONTROL1.SYNTHETIC.PROOF",
            "VALIDATOR_SYNTHETIC",
            "TEST_SYNTHETIC",
            "CONTROL1_SYNTHETIC_",
            "POST_LAUNCH_EXPANSION_BATCH",
        )
        for path_tokens, value in _walk(mutation_surface):
            if isinstance(value, str) and any(
                token in value.upper() for token in forbidden_synthetic_tokens
            ):
                raise InvariantError(
                    "CANONICAL_SYNTHETIC_MUTATION",
                    f"{component_id}.{'.'.join(path_tokens)}={value!r}",
                )

        definition = record.get("definition", {})
        expression = str(
            definition.get("complete_mathematical_or_procedural_definition", "")
        ).strip()
        if expression:
            expression_targets[expression].add(component_id)
        for implementation in definition.get("implementation_versions", ()):
            if isinstance(implementation, Mapping):
                reference = _implementation_ref(implementation)
                if reference:
                    implementation_targets[reference].add(component_id)
        for provenance in record.get("provenance", ()):
            if not isinstance(provenance, Mapping):
                continue
            artifact = str(provenance.get("source_artifact_ref", ""))
            row_ref = str(provenance.get("source_row_ref", ""))
            local_name = str(
                provenance.get("source_local_identity_or_name", "")
            )
            normalized = artifact.replace("\\", "/").lower()
            if (
                normalized.startswith("tests/")
                or "/tests/" in f"/{normalized}"
                or "validate_pr169_qku_comp_control1.py" in normalized
                or normalized.startswith("validator::")
            ):
                raise InvariantError(
                    "CANONICAL_TEST_OR_VALIDATOR_SOURCE",
                    f"{component_id}: {artifact}:{row_ref}",
                )
            if artifact and row_ref:
                provenance_targets[(artifact, row_ref)].add(component_id)
            if local_name:
                source_name_targets[local_name].add(component_id)
        for relation in record.get("relations", ()):
            if not isinstance(relation, Mapping):
                continue
            source_identity = str(
                relation.get("source_canonical_identity_row_id", "")
            )
            if source_identity:
                rp5c_identity_targets[source_identity].add(component_id)
            if _relation_type(relation) == (
                "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
            ):
                custody_payload = relation.get("source_group_custody_key")
                if not isinstance(custody_payload, Mapping):
                    raise InvariantError(
                        "RP5D_IDENTITY_CUSTODY_MAPPING",
                        f"{component_id}: missing structured custody",
                    )
                rp5c_target_custody_keys[component_id].add(
                    _rp5c_group_custody_tuple(
                        custody_payload, code="RP5D_IDENTITY_CUSTODY_MAPPING"
                    )
                )
        for qku in record.get("uses", {}).get("qku_role_bindings", ()):
            if not isinstance(qku, Mapping):
                continue
            qku_id = str(qku.get("qku_id", ""))
            target = str(qku.get("stack_root_or_direct_component") or component_id)
            if qku_id:
                if target not in record_by_id:
                    raise InvariantError(
                        "SOURCE_CLOSURE_QKU_TARGET",
                        f"{qku_id}: missing canonical target {target}",
                    )
                qku_targets[qku_id].add(target)
                if qku.get("runtime_root_eligibility") == "STATUS_EXPLAIN_ONLY":
                    context_key = (
                        qku_id,
                        str(qku.get("role_or_decision_stage", "")),
                        str(qku.get("market_family", "")),
                    )
                    status_explain_qku_context_targets[context_key].add(target)
                if "PR162B_SOURCE_SEMANTICS" in origins:
                    pr162b_qku_targets[qku_id].add(target)

        selection_payload = definition.get("source_scoped_selection_tuple")
        if isinstance(selection_payload, Mapping):
            raise InvariantError(
                "SOURCE_CONTEXT_FALSE_SELECTION_POLICY_ADMISSION",
                f"{component_id}: source row co-association cannot mint computation truth",
            )

        if record.get("record_state") in RUNTIME_ACTIVE_RECORD_STATES:
            for requirement in definition.get("requirements", ()):
                if not isinstance(requirement, Mapping):
                    raise InvariantError(
                        "SOURCE_LOCAL_RUNTIME_REQUIREMENT", component_id
                    )
                target = str(
                    requirement.get("required_component_id_or_source_selector", "")
                )
                if not target.startswith("QTT.COMP.") or target not in accepted_ids:
                    raise InvariantError(
                        "SOURCE_LOCAL_RUNTIME_REQUIREMENT",
                        f"{component_id} -> {target!r}",
                    )
                fallback = requirement.get("fallback_component_id_or_null")
                if fallback is not None and (
                    not str(fallback).startswith("QTT.COMP.")
                    or str(fallback) not in accepted_ids
                ):
                    raise InvariantError(
                        "SOURCE_LOCAL_RUNTIME_REQUIREMENT",
                        f"{component_id} fallback -> {fallback!r}",
                    )

    closure_artifacts, manifest_owner_split = _independent_source_closure_artifacts(
        repo_root, deadline
    )
    # Only root surfaces needed for cross-owner joins stay resident.  Owner
    # projections are read, classified, and released one at a time below.
    loaded: dict[str, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    rp5c_reference_rows = _independent_rp5c_reference_custody_rows(
        repo_root, deadline
    )
    artifact_reports: list[dict[str, Any]] = []
    cohort_rows: Counter[str] = Counter()
    cohort_dispositions: dict[str, Counter[str]] = defaultdict(Counter)
    formulation_rows: dict[str, dict[str, Any]] = {}
    candidate_packet_ids: set[str] = set()

    for spec in SOURCE_CLOSURE_ARTIFACTS:
        path = str(spec["path"])
        rows, metadata = _closure_read_rows(repo_root, path, deadline)
        expected = int(spec["expected"])
        if (
            len(rows) != expected
            or metadata["declared_rows"] != expected
            or metadata["actual_rows_read"] != expected
        ):
            raise InvariantError(
                "SOURCE_CLOSURE_DENOMINATOR",
                f"{path}: actual={len(rows)} declared={metadata['declared_rows']} expected={expected}",
            )
        key_field = str(spec["key"])
        row_keys = [str(row.get(key_field, "")) for row in rows]
        if any(not key for key in row_keys):
            raise InvariantError(
                "SOURCE_CLOSURE_EMPTY_ROW_KEY", f"{path}: {key_field}"
            )
        if len(row_keys) != len(set(row_keys)):
            raise InvariantError(
                "SOURCE_CLOSURE_DUPLICATE_ROW_KEY", f"{path}: {key_field}"
            )
        loaded[path] = (rows, metadata)
        if path.endswith("PR162D_R2A_FormulationRecordRegistry.report.json"):
            formulation_rows = {
                str(row["formulation_id"]): row for row in rows
            }
        if path.endswith("PR162D_R2A_CandidatePacketV1Registry.report.json"):
            candidate_packet_ids = {
                str(row["candidate_packet_id"]) for row in rows
            }

    pr162b_vector_rows = [
        row
        for vector_path in PR162B_TEST_VECTOR_PATHS
        for row in loaded[vector_path][0]
    ]
    pr162b_source_vector_metrics = _independently_invoke_pr162b_source_vectors(
        pr162b_vector_rows, deadline
    )
    normalized_expression = lambda value: re.sub(
        r"\s+", "", str(value or "")
    ).casefold()
    gfp_selected_expressions = {
        normalized_expression(row.get("formula_expression"))
        for row in loaded[
            "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json"
        ][0]
        if normalized_expression(row.get("formula_expression"))
    }

    contextual_reference_sources = (
        (
            "docs/master_plan/generated/PR162E_PluginRegistry.report.json",
            "formula_refs",
            "algorithm_refs",
        ),
        (
            "docs/master_plan/generated/PR162E_Q_ObjectiveMap.report.json",
            "formula_id",
            "algorithm_id",
        ),
        (
            "docs/master_plan/generated/PR166_SM3_PosEvidence.report.json",
            "formula_id",
            "algorithm_id",
        ),
    )
    contextual_reference_counts: Counter[tuple[str, str, str]] = Counter()
    for source_path, formula_field, algorithm_field in contextual_reference_sources:
        for row in loaded[source_path][0]:
            for kind, field in (
                ("FORMULA", formula_field),
                ("ALGORITHM", algorithm_field),
            ):
                for reference in _source_row_values(row, field):
                    contextual_reference_counts[(kind, reference, source_path)] += 1

    contextual_reference_records: set[str] = set()
    for kind, reference, _ in contextual_reference_counts:
        component_id = (
            f"QTT.COMP.CANDIDATE.{kind}."
            f"{_independent_candidate_token(reference)}"
        )
        record = record_by_id.get(component_id)
        if record is None:
            raise InvariantError(
                "CONTEXTUAL_REFERENCE_COMPACT_LINEAGE", component_id
            )
        contextual_reference_records.add(component_id)
    for component_id in sorted(contextual_reference_records):
        record = record_by_id[component_id]
        if record.get("uses", {}).get("qku_role_bindings"):
            raise InvariantError(
                "CONTEXTUAL_REFERENCE_FALSE_QKU_ROOT", component_id
            )
        kind = "FORMULA" if ".FORMULA." in component_id else "ALGORITHM"
        expected_entries = {
            source_path: count
            for (entry_kind, reference, source_path), count in contextual_reference_counts.items()
            if entry_kind == kind
            and component_id.endswith(_independent_candidate_token(reference))
        }
        observed_entries: dict[str, Mapping[str, Any]] = {}
        for provenance in record.get("provenance", ()):
            if not isinstance(provenance, Mapping):
                raise InvariantError(
                    "CONTEXTUAL_REFERENCE_COMPACT_LINEAGE", component_id
                )
            source_path = str(provenance.get("source_artifact_ref", ""))
            if source_path in observed_entries:
                raise InvariantError(
                    "CONTEXTUAL_REFERENCE_COMPACT_LINEAGE",
                    f"{component_id}: duplicate {source_path}",
                )
            observed_entries[source_path] = provenance
            if {
                "exact_source_row_refs_location",
                "member_identity_row_ids",
                "identity_row_ids",
                "source_artifact_row_ids",
            }.intersection(provenance):
                raise InvariantError(
                    "CONTEXTUAL_REFERENCE_EXPANDED_LINEAGE", component_id
                )
        if set(observed_entries) != set(expected_entries):
            raise InvariantError(
                "CONTEXTUAL_REFERENCE_COMPACT_LINEAGE",
                f"{component_id}: {sorted(observed_entries)} != "
                f"{sorted(expected_entries)}",
            )
        for source_path, expected_count in expected_entries.items():
            entry = observed_entries[source_path]
            reference = str(entry.get("source_local_identity_or_name", ""))
            expected_rederivation = {
                "owner_artifact": source_path,
                "match_field": (
                    "formula_refs_or_formula_id"
                    if kind == "FORMULA"
                    else "algorithm_refs_or_algorithm_id"
                ),
                "match_value": reference,
                "validation": "INDEPENDENT_ROW_LEVEL_REDERIVATION_REQUIRED",
            }
            if (
                entry.get("source_row_ref")
                != f"ROWS_WITH_REFERENCE::{reference}"
                or entry.get("source_occurrence_count") != expected_count
                or entry.get("lineage_validation_status")
                != "ALL_REFERENCING_ROWS_CLASSIFIED"
                or entry.get("exact_source_row_rederivation")
                != expected_rederivation
            ):
                raise InvariantError(
                    "CONTEXTUAL_REFERENCE_COMPACT_LINEAGE",
                    f"{component_id}: {source_path}",
                )

    def exact_target(
        targets: Iterable[str], code: str, detail: str
    ) -> str:
        values = sorted(set(targets))
        if len(values) != 1:
            raise InvariantError(code, f"{detail}: targets={values}")
        return values[0]

    semantic_source_targets: dict[str, str] = {}
    for source_path in (
        "docs/master_plan/generated/map3/formula_materialization_rows.jsonl",
        "docs/master_plan/generated/PR162B_QKUFormulaRegistry.report.json",
        "docs/master_plan/generated/PR162B_QKUAlgorithmRegistry.report.json",
        "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json",
    ):
        rows, _ = loaded[source_path]
        key_field = next(
            str(spec["key"])
            for spec in closure_artifacts
            if spec["path"] == source_path
        )
        for row in rows:
            row_key = str(row[key_field])
            target = exact_target(
                provenance_targets.get((source_path, row_key), ()),
                "SOURCE_SEMANTIC_PROVENANCE",
                f"{source_path}:{row_key}",
            )
            target_record = record_by_id[target]
            if target_record.get("record_state") != "PROVISIONAL":
                raise InvariantError(
                    "SOURCE_SEMANTIC_OVERPROMOTION", f"{source_path}:{row_key} -> {target}"
                )
            relations = {
                str(entry.get("source_relation", ""))
                for entry in target_record.get("provenance", ())
                if isinstance(entry, Mapping)
                and str(entry.get("source_artifact_ref", "")) == source_path
                and str(entry.get("source_row_ref", "")) == row_key
            }
            if relations != {"GENUINE_PROVISIONAL_NEW_COMPUTATION"}:
                raise InvariantError(
                    "SOURCE_SEMANTIC_PROVENANCE",
                    f"{source_path}:{row_key}: relations={sorted(relations)}",
                )
            semantic_source_targets[row_key] = target

    gfp_registered_refs: set[str] = set()
    for row in loaded[
        "docs/master_plan/generated/PR168_GFP_SelectedFormulaExpressionRegistry.report.json"
    ][0]:
        formula_id = str(row["formula_id"])
        target = semantic_source_targets[formula_id]
        expected_ref = _independent_normalized_gfp_callable_ref(
            row.get("computation_function_path"),
            row.get("computation_function_name"),
        )
        actual_refs = {
            _implementation_ref(entry)
            for entry in record_by_id[target]
            .get("definition", {})
            .get("implementation_versions", ())
            if isinstance(entry, Mapping)
        }
        if actual_refs != {expected_ref}:
            raise InvariantError(
                "GFP_REGISTERED_IMPLEMENTATION_REF",
                f"{formula_id}: {sorted(actual_refs)} != {expected_ref}",
            )
        gfp_registered_refs.add(expected_ref)
    if len(gfp_registered_refs) != 33:
        raise InvariantError(
            "GFP_REGISTERED_IMPLEMENTATION_DENOMINATOR",
            f"{len(gfp_registered_refs)}/33",
        )

    gfp_arbitration_path = (
        "docs/master_plan/generated/PR168_GFP_FormulaSourceArbitration.report.json"
    )
    selected_arbitration_targets: dict[str, str] = {}
    for row in loaded[gfp_arbitration_path][0]:
        candidate_id = str(row["formula_candidate_id"])
        if bool(row.get("selected_flag")):
            expression = str(row.get("formula_expression", "")).strip()
            target = exact_target(
                (
                    candidate
                    for candidate in expression_targets.get(expression, ())
                    if "GFP_SOURCE_SEMANTICS"
                    in record_by_id[candidate].get("origin_cohorts", ())
                ),
                "GFP_SELECTED_EXPRESSION_MAPPING",
                candidate_id,
            )
            selected_arbitration_targets[candidate_id] = target
    # Fixture rows precede the arbitration artifact in the declared audit
    # order, so make proof-backed selected candidate IDs directly resolvable
    # before row classification begins.
    semantic_source_targets.update(selected_arbitration_targets)

    formulation_targets: dict[str, str] = {}
    for formulation_id, row in formulation_rows.items():
        callable_ref = str(row.get("callable_ref", ""))
        formulation_targets[formulation_id] = exact_target(
            implementation_targets.get(callable_ref, ()),
            "PR162D_CALLABLE_MAPPING",
            f"{formulation_id}: {callable_ref!r}",
        )

    gfp_selected_count = 0
    gfp_terminal_count = 0
    gfp_discovery_mapping_count = 0
    semantic_candidate_mapping_count = 0
    map3_attached_qku_count = 0
    total_reference_occurrences = 0
    total_resolved_reference_occurrences = 0
    context_or_evidence_admitted = 0
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
    gfp_discovery_exact_expression_match_count = 0
    gfp_discovery_expression_containment_match_count = 0
    owner_context_selection_by_qku: dict[
        str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]
    ] = {}
    owner_context_selection_qku_paths: dict[str, set[str]] = defaultdict(set)
    owner_retained_source_local_reference_blocker_count = 0
    for spec in closure_artifacts:
        cohort = str(spec["cohort"])
        path = str(spec["path"])
        role = str(spec["role"])
        rows_metadata = loaded.get(path)
        if rows_metadata is None:
            rows_metadata = _closure_read_rows(repo_root, path, deadline)
        rows, metadata = rows_metadata
        key_field = str(spec["key"] or _independent_source_row_key_field(rows, path))
        dispositions: Counter[str] = Counter()
        reference_occurrences = 0
        resolved_reference_occurrences = 0
        reference_kind_counts: Counter[str] = Counter()
        resolved_reference_kind_counts: Counter[str] = Counter()
        absence_disposition_counts: Counter[str] = Counter()
        non_computation_context_counts: Counter[str] = Counter()
        source_scoped_selection_counts: Counter[str] = Counter()

        def classify_reference(
            kind: str,
            value: Any,
            row_key: str,
            *,
            expected_targets: set[str] | None = None,
        ) -> None:
            nonlocal reference_occurrences, resolved_reference_occurrences
            values = _source_row_values({"value": value}, "value")
            for reference in values:
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
                resolved = _independent_reference_targets_resolved(
                    set(targets), expected_targets
                )
                if not resolved:
                    raise InvariantError(
                        "SOURCE_COMPUTATION_REFERENCE_UNRESOLVED",
                        f"{path}:{row_key}: {kind.lower()}={reference!r}: "
                        f"targets={sorted(targets)} expected="
                        f"{sorted(expected_targets) if expected_targets is not None else 'EXACTLY_ONE'}",
                    )
                resolved_reference_occurrences += 1
                resolved_reference_kind_counts[kind] += 1

        def require_status_explain_qku_association(
            target_id: str,
            qku_values: Any,
            row_key: str,
            *,
            expected_role: str | None = None,
            expected_market: str | None = None,
        ) -> None:
            nonlocal agent_reachable_reference_occurrence_count
            values = _source_row_values({"value": qku_values}, "value")
            roles = [
                role_row
                for role_row in record_by_id[target_id]
                .get("uses", {})
                .get("qku_role_bindings", ())
                if isinstance(role_row, Mapping)
            ]
            for qku_id in values:
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
                    raise InvariantError(
                        "AGENT_STATUS_EXPLAIN_QKU_ASSOCIATION",
                        f"{path}:{row_key}: {qku_id} -> {target_id}: {len(matches)}",
                    )
                role_value = str(matches[0].get("role_or_decision_stage", ""))
                market_value = str(matches[0].get("market_family", ""))
                context_key = (qku_id, role_value, market_value)
                if status_explain_qku_context_targets.get(context_key) != {target_id}:
                    raise InvariantError(
                        "AGENT_STATUS_EXPLAIN_QKU_AMBIGUOUS",
                        f"{context_key!r}: "
                        f"{sorted(status_explain_qku_context_targets.get(context_key, set()))}",
                    )
                agent_reachable_reference_occurrence_count += 1
                agent_reachable_selector_keys.add(context_key)

        for row in rows:
            row_key = str(row[key_field])
            exact_provenance_targets = provenance_targets.get((path, row_key), set())
            disposition = ""
            owner_projection = role in {"OWNER_PROJECTION", "OWNER_CONTEXT"}
            if owner_projection:
                if exact_provenance_targets:
                    context_or_evidence_admitted += 1
                _independent_validate_owner_projection_row(
                    row,
                    path=path,
                    row_key=row_key,
                    canonical_provenance_targets=exact_provenance_targets,
                    reject_hash_authority=(
                        "AtomicRowsComputationCoverage" in path
                        or cohort == "QUANTUM_559"
                    ),
                )
                disposition = str(
                    spec.get(
                        "projection_disposition",
                        "SOURCE_OWNER_CONTEXT_OR_EVIDENCE_PROJECTION",
                    )
                )
                if cohort == "RP5D" and all(
                    field in row for field in ("identity_ref", "formula_ref", "qku_ref")
                ):
                    mapping = _independent_rp5d_reference_mapping(
                        row,
                        source_path=path,
                        rp5c_reference_rows=rp5c_reference_rows,
                        identity_targets=rp5c_identity_targets,
                        target_custody_keys=rp5c_target_custody_keys,
                    )
                    for kind in sorted(mapping["real_references"]):
                        reference_occurrences += 1
                        resolved_reference_occurrences += 1
                        reference_kind_counts[kind] += 1
                        resolved_reference_kind_counts[kind] += 1
                    for kind in sorted(mapping["absence_dispositions"]):
                        absence_disposition_counts[f"{kind}_REF_NOT_PRESENT"] += 1
                elif cohort == "RP5D":
                    identity_values = {
                        str(value)
                        for field in (
                            "result_identity_refs",
                            "resolved_executable_identity_refs",
                            "excluded_identity_refs",
                        )
                        for value in row.get(field, ())
                        if isinstance(value, str) and value.startswith("RP5C_IDENTITY_")
                    }
                    for identity_ref in sorted(identity_values):
                        if (
                            identity_ref not in rp5c_reference_rows
                            or len(rp5c_identity_targets.get(identity_ref, set())) != 1
                        ):
                            raise InvariantError(
                                "SOURCE_OWNER_RP5D_IDENTITY_REFERENCE",
                                f"{path}:{row_key}: {identity_ref}",
                            )
                        reference_occurrences += 1
                        resolved_reference_occurrences += 1
                        reference_kind_counts["RP5C_IDENTITY"] += 1
                        resolved_reference_kind_counts["RP5C_IDENTITY"] += 1
                if cohort in {"RP5D_R1", "RP5E"}:
                    for field in (
                        "formula_id", "formula_ids", "formula_ref",
                        "formula_refs", "eligible_formula_ids",
                    ):
                        for formula_ref in _source_row_values(row, field):
                            targets = source_name_targets.get(formula_ref, set())
                            if len(targets) == 1:
                                reference_occurrences += 1
                                resolved_reference_occurrences += 1
                                reference_kind_counts["FORMULA"] += 1
                                resolved_reference_kind_counts["FORMULA"] += 1
                            elif formula_ref:
                                owner_retained_source_local_reference_blocker_count += 1
                                source_scoped_selection_counts[
                                    "OWNER_RETAINED_SOURCE_LOCAL_FORMULA_REFERENCE_"
                                    "REQUIRES_DIRECT_SEMANTIC_PROOF"
                                ] += 1
                    for field in ("qku_id", "qku_ids", "qku_ref", "qku_refs"):
                        for qku_ref in _source_row_values(row, field):
                            if qku_ref.endswith("::QKU_REF_NOT_PRESENT"):
                                continue
                            targets = qku_targets.get(qku_ref, set())
                            if len(targets) == 1:
                                reference_occurrences += 1
                                resolved_reference_occurrences += 1
                                reference_kind_counts["QKU"] += 1
                                resolved_reference_kind_counts["QKU"] += 1
                            else:
                                owner_retained_source_local_reference_blocker_count += 1
                                source_scoped_selection_counts[
                                    "OWNER_RETAINED_SOURCE_LOCAL_QKU_REFERENCE_"
                                    "REQUIRES_DIRECT_SEMANTIC_PROOF"
                                ] += 1
            elif role == "SEMANTIC_ROOT" and cohort == "PR162D":
                target = formulation_targets[row_key]
                disposition = (
                    "PARAMETER_POLICY_MAPPING"
                    if str(row.get("formulation_type", "")) == "PARAMETER_PACK"
                    else "IMPLEMENTATION_VERSION_MAPPING"
                )
                if target not in record_by_id:
                    raise InvariantError("PR162D_CALLABLE_MAPPING", row_key)
            elif role == "SEMANTIC_ROOT":
                target = exact_target(
                    exact_provenance_targets,
                    "SOURCE_SEMANTIC_PROVENANCE",
                    f"{path}:{row_key}",
                )
                if semantic_source_targets.get(row_key) != target:
                    raise InvariantError(
                        "SOURCE_SEMANTIC_PROVENANCE", f"{path}:{row_key}"
                    )
                disposition = "GENUINE_PROVISIONAL_NEW_COMPUTATION"
            elif role == "QKU_ROLE":
                formula_id = str(row.get("formula_id", ""))
                target = semantic_source_targets.get(formula_id)
                if not target:
                    raise InvariantError(
                        "MAP3_QKU_SEMANTIC_TARGET", f"{path}:{row_key}"
                    )
                qku_id = str(row.get("qku_id_if_available", ""))
                target_roles = {
                    str(role_row.get("qku_id", ""))
                    for role_row in record_by_id[target]
                    .get("uses", {})
                    .get("qku_role_bindings", ())
                    if isinstance(role_row, Mapping)
                }
                if not qku_id or qku_id not in target_roles:
                    raise InvariantError(
                        "MAP3_QKU_NOT_ATTACHED_TO_TARGET",
                        f"{path}:{row_key}: {qku_id!r} -> {target}",
                    )
                disposition = "QKU_DECISION_ROLE_MAPPING"
                map3_attached_qku_count += 1
                classify_reference(
                    "QKU", qku_id, row_key, expected_targets={target}
                )
                require_status_explain_qku_association(target, qku_id, row_key)
            elif role == "PROVENANCE_MAPPING" and cohort == "RP5D":
                identity_ref = str(row.get("identity_ref", ""))
                exact_target(
                    rp5c_identity_targets.get(identity_ref, ()),
                    "RP5D_RP5C_IDENTITY_MAPPING",
                    f"{path}:{identity_ref}",
                )
                disposition = "EXISTING_CANONICAL_RECORD_PROVENANCE_MAPPING"
            elif role == "SOURCE_DISPOSITION":
                if bool(row.get("selected_flag")):
                    if row_key not in selected_arbitration_targets:
                        raise InvariantError(
                            "GFP_SELECTED_EXPRESSION_MAPPING", row_key
                        )
                    disposition = "IMPLEMENTATION_VERSION_MAPPING"
                    semantic_source_targets[row_key] = selected_arbitration_targets[row_key]
                    gfp_selected_count += 1
                else:
                    reason = str(
                        row.get("rejection_or_deprioritization_reason", "")
                    ).strip()
                    if not reason:
                        raise InvariantError("GFP_TERMINAL_REASON", row_key)
                    disposition = "INAPPLICABLE_TERMINAL"
                    gfp_terminal_count += 1
            elif role == "SEMANTIC_CANDIDATE":
                target = exact_target(
                    exact_provenance_targets,
                    "SOURCE_CANDIDATE_PROVENANCE",
                    f"{path}:{row_key}",
                )
                target_record = record_by_id[target]
                relations = {
                    str(entry.get("source_relation", ""))
                    for entry in target_record.get("provenance", ())
                    if isinstance(entry, Mapping)
                    and str(entry.get("source_artifact_ref", "")) == path
                    and str(entry.get("source_row_ref", "")) == row_key
                }
                if (
                    target_record.get("record_state") != "PROVISIONAL"
                    or relations != {"GENUINE_PROVISIONAL_NEW_COMPUTATION"}
                ):
                    raise InvariantError(
                        "SOURCE_CANDIDATE_PROVENANCE",
                        f"{path}:{row_key} -> {target}: relations={sorted(relations)}",
                    )
                if row.get("materialized_as_source_truth") is True:
                    raise InvariantError(
                        "SOURCE_OWNER_CANDIDATE_OVERPROMOTED", f"{path}:{row_key}"
                    )
                disposition = "GENUINE_PROVISIONAL_NEW_COMPUTATION"
                semantic_candidate_mapping_count += 1
                classify_reference(
                    "QKU", row.get("qku_refs"), row_key, expected_targets={target}
                )
            elif role == "SOURCE_TEST_VECTOR" and cohort == "PR162B":
                target = exact_target(
                    exact_provenance_targets,
                    "PR162B_SOURCE_VECTOR_PROVENANCE",
                    f"{path}:{row_key}",
                )
                callable_ref = (
                    f"{row.get('implementation_module', '')}:"
                    f"{row.get('implementation_function', '')}"
                )
                callable_target = exact_target(
                    implementation_targets.get(callable_ref, ()),
                    "PR162B_SOURCE_VECTOR_IMPLEMENTATION",
                    f"{path}:{row_key}",
                )
                if target != callable_target:
                    raise InvariantError(
                        "PR162B_SOURCE_VECTOR_TARGET_MISMATCH",
                        f"{path}:{row_key}: {target} != {callable_target}",
                    )
                record = record_by_id[target]
                test_refs = record.get("definition", {}).get(
                    "oracle_and_test_refs", ()
                )
                expected_ref = {
                    "source_test_vector_ref": row_key,
                    "source_artifact_ref": path,
                    "validation_class": (
                        "SOURCE_OWNER_VECTOR_EXECUTED_NOT_INDEPENDENT_ORACLE"
                    ),
                }
                if list(test_refs) != [expected_ref]:
                    raise InvariantError(
                        "PR162B_SOURCE_VECTOR_REFERENCE", f"{path}:{row_key}"
                    )
                if any(
                    binding.get("readiness", {}).get("oracle") == "PASS"
                    or binding.get("derived_state") == "CONTEXT_READY"
                    for binding in record.get("bindings", ())
                ):
                    raise InvariantError(
                        "PR162B_SOURCE_VECTOR_FALSE_READINESS", target
                    )
                disposition = "SOURCE_IMPLEMENTATION_TEST_VECTOR_MAPPING"
            elif role == "DISCOVERY":
                if _independent_gfp_discovery_has_complete_typed_semantics(row):
                    raise InvariantError(
                        "GFP_DISCOVERY_REQUIRES_EXPLICIT_REVIEW",
                        f"{path}:{row_key}",
                    )
                if exact_provenance_targets:
                    raise InvariantError(
                        "GFP_DISCOVERY_FALSE_CANONICAL_ADMISSION",
                        f"{path}:{row_key}: {sorted(exact_provenance_targets)}",
                    )
                selected_formula_id = str(row.get("selected_formula_id", ""))
                expected_variable_map = (
                    "PR168_GFP_SELECTED_FORMULA::"
                    f"{selected_formula_id}::variable_map"
                )
                if selected_formula_id not in semantic_source_targets:
                    raise InvariantError(
                        "GFP_DISCOVERY_SELECTED_FORMULA_MAPPING",
                        f"{path}:{row_key}: {selected_formula_id!r}",
                    )
                if row.get("variable_map_ref") != expected_variable_map:
                    raise InvariantError(
                        "GFP_DISCOVERY_VARIABLE_MAP_CLOSURE",
                        f"{path}:{row_key}: {row.get('variable_map_ref')!r}",
                    )
                if row.get("source_coverage_status") != "COVERED_BY_SELECTED_FORMULA":
                    raise InvariantError(
                        "GFP_DISCOVERY_OWNER_COVERAGE_DISPOSITION",
                        f"{path}:{row_key}",
                    )
                implementation_status = str(row.get("implementation_status", ""))
                if implementation_status == "IMPLEMENTED_DETERMINISTIC_FUNCTION":
                    disposition = (
                        "SOURCE_OWNER_HISTORICAL_IMPLEMENTATION_MAPPING_"
                        "REQUIRES_DIRECT_SEMANTIC_PROOF"
                    )
                    gfp_discovery_implemented_context_count += 1
                elif implementation_status == (
                    "COEFFICIENT_MAP_REQUIRED_INPUT_GAP_ROUTE_ASSIGNED"
                ):
                    disposition = (
                        "SOURCE_OWNER_HISTORICAL_INPUT_GAP_MAPPING_"
                        "REQUIRES_DIRECT_SEMANTIC_PROOF"
                    )
                    gfp_discovery_input_gap_context_count += 1
                else:
                    raise InvariantError(
                        "GFP_DISCOVERY_IMPLEMENTATION_STATUS",
                        f"{path}:{row_key}: {implementation_status!r}",
                    )
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
                if exact_provenance_targets:
                    context_or_evidence_admitted += 1
                    raise InvariantError(
                        "CONTEXT_OR_EVIDENCE_ADMITTED_AS_COMPUTATION",
                        f"{path}:{row_key} -> {sorted(exact_provenance_targets)}",
                    )
                disposition = "NON_COMPUTATION_CONTEXT_OR_EVIDENCE_RETAINED_WITH_OWNER"

            if cohort == "RP5D" and not owner_projection:
                rp5d_mapping = _independent_rp5d_reference_mapping(
                    row,
                    source_path=path,
                    rp5c_reference_rows=rp5c_reference_rows,
                    identity_targets=rp5c_identity_targets,
                    target_custody_keys=rp5c_target_custody_keys,
                )
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
                        raise InvariantError(
                            "RP5D_NON_COMPUTATION_CONTEXT_MAPPING",
                            f"{path}:{row_key}: {adapter_refs!r}",
                        )
                    non_computation_context_counts[
                        "REQUIRED_FORMULA_TO_PNL_ADAPTER_CONTRACT"
                    ] += 1

            if cohort == "CANDIDATE_PACKET_6502":
                formulation_ref = str(row.get("formulation_ref", ""))
                target = formulation_targets.get(formulation_ref)
                if not target:
                    raise InvariantError(
                        "CANDIDATE_PACKET_FORMULATION_UNRESOLVED",
                        f"{row_key}: {formulation_ref!r}",
                    )
                packet_callable = str(row.get("callable_ref", ""))
                callable_target = exact_target(
                    implementation_targets.get(packet_callable, ()),
                    "CANDIDATE_PACKET_CALLABLE_UNRESOLVED",
                    f"{row_key}: {packet_callable!r}",
                )
                if callable_target != target:
                    raise InvariantError(
                        "CANDIDATE_PACKET_FORMULATION_CALLABLE_MISMATCH",
                        f"{row_key}: formulation={target}, callable={callable_target}",
                    )
                classify_reference(
                    "FORMULATION",
                    formulation_ref,
                    row_key,
                    expected_targets={target},
                )
                classify_reference(
                    "CALLABLE",
                    row.get("callable_ref"),
                    row_key,
                    expected_targets={target},
                )
                qku_values = _source_row_values(row, "qku_ids")
                if len(qku_values) != 1:
                    raise InvariantError(
                        "CANDIDATE_PACKET_QKU_CARDINALITY",
                        f"{row_key}: {qku_values!r}",
                    )
                if (
                    row.get("source_truth_status") != "OWNER_TEMPLATE"
                    or row.get("candidate_truth_status")
                    != "REPLAY_PAPER_CANDIDATE"
                    or row.get("official_truth_flag") is not False
                ):
                    raise InvariantError(
                        "CANDIDATE_PACKET_TRUTH_STATE", row_key
                    )
                downstream_agents = {
                    str(value) for value in row.get("downstream_agent_refs", ())
                }
                if downstream_agents.intersection(current_agent_ids):
                    raise InvariantError(
                        "CANDIDATE_PACKET_FALSE_CURRENT_AGENT_REACHABILITY",
                        row_key,
                    )
                for qku_id in qku_values:
                    reference_occurrences += 1
                    resolved_reference_occurrences += 1
                    reference_kind_counts["QKU"] += 1
                    resolved_reference_kind_counts["QKU"] += 1
                    prior_target = candidate_packet_qku_targets.setdefault(
                        qku_id, target
                    )
                    if prior_target != target:
                        raise InvariantError(
                            "CANDIDATE_PACKET_QKU_TARGET_AMBIGUITY", qku_id
                        )
                    candidate_packet_source_alternative_count += 1
                    conflicts = pr162b_qku_targets.get(qku_id, set())
                    if conflicts and target not in conflicts:
                        candidate_packet_known_conflict_count += 1
                source_scoped_selection_counts[
                    "OWNER_TEMPLATE_REPLAY_PAPER_CANDIDATE_NO_RUNTIME_ROOT"
                ] += len(qku_values)

            if cohort == "FIXTURE_5":
                for formula_ref in _source_row_values(row, "formula_ids"):
                    target = semantic_source_targets.get(formula_ref)
                    if not target or target not in record_by_id:
                        raise InvariantError(
                            "FIXTURE_FORMULA_REFERENCE_UNRESOLVED",
                            f"{row_key}: {formula_ref}",
                        )
                classify_reference("FORMULA", row.get("formula_ids"), row_key)
                classify_reference("QKU", row.get("qku_id"), row_key)

            if cohort == "PR162E" and not owner_projection:
                selection = _independent_source_selection_tuple(
                    row,
                    formula_field="formula_refs",
                    algorithm_field="algorithm_refs",
                    parameter_field="parameter_stack_refs",
                )
                owner_context_selection_tuples.add(selection)
                formula_targets = source_name_targets.get(selection[0][0], set())
                algorithm_targets = source_name_targets.get(selection[1][0], set())
                classify_reference(
                    "FORMULA",
                    row.get("formula_refs"),
                    row_key,
                    expected_targets=set(formula_targets),
                )
                classify_reference(
                    "ALGORITHM",
                    row.get("algorithm_refs"),
                    row_key,
                    expected_targets=set(algorithm_targets),
                )
                for qku_id in _source_row_values(row, "qku_refs"):
                    prior = owner_context_selection_by_qku.setdefault(qku_id, selection)
                    if prior != selection:
                        raise InvariantError(
                            "SOURCE_CONTEXT_QKU_MULTI_SELECTION",
                            f"{qku_id}: {prior!r} != {selection!r}",
                        )
                    owner_context_selection_qku_paths[qku_id].add(path)
                    source_scoped_selection_counts[
                        "OWNER_CONTEXT_ASSOCIATION_NOT_RUNTIME_COMPUTATION_ROOT"
                    ] += 1
            if cohort == "PR162B" and not owner_projection:
                classify_reference("FORMULA", row.get("formula_refs"), row_key)
                if role == "SEMANTIC_ROOT":
                    target = semantic_source_targets.get(row_key)
                    if not target:
                        raise InvariantError("PR162B_SEMANTIC_TARGET", row_key)
                    classify_reference(
                        "QKU",
                        row.get("qku_refs"),
                        row_key,
                        expected_targets={target},
                    )
                    require_status_explain_qku_association(
                        target, row.get("qku_refs"), row_key
                    )
            if cohort in {"QUANTUM_559", "POSITIVE_EVIDENCE_150"} and not owner_projection:
                selection = _independent_source_selection_tuple(
                    row,
                    formula_field="formula_id",
                    algorithm_field="algorithm_id",
                    parameter_field="parameter_stack_id",
                )
                owner_context_selection_tuples.add(selection)
                formula_targets = source_name_targets.get(selection[0][0], set())
                algorithm_targets = source_name_targets.get(selection[1][0], set())
                classify_reference(
                    "FORMULA",
                    row.get("formula_id"),
                    row_key,
                    expected_targets=set(formula_targets),
                )
                classify_reference(
                    "ALGORITHM",
                    row.get("algorithm_id"),
                    row_key,
                    expected_targets=set(algorithm_targets),
                )
                for qku_id in _source_row_values(row, "qku_id"):
                    prior = owner_context_selection_by_qku.setdefault(qku_id, selection)
                    if prior != selection:
                        raise InvariantError(
                            "SOURCE_CONTEXT_QKU_MULTI_SELECTION",
                            f"{qku_id}: {prior!r} != {selection!r}",
                        )
                    owner_context_selection_qku_paths[qku_id].add(path)
                    source_scoped_selection_counts[
                        "OWNER_CONTEXT_ASSOCIATION_NOT_RUNTIME_COMPUTATION_ROOT"
                    ] += 1
            if cohort == "POSITIVE_EVIDENCE_150":
                packet_ref = str(row.get("candidate_packet_id", ""))
                if packet_ref not in candidate_packet_ids:
                    raise InvariantError(
                        "EVIDENCE_CANDIDATE_PACKET_UNRESOLVED",
                        f"{row_key}: {packet_ref}",
                    )
            if cohort == "VALUE_GAPS_2852":
                classify_reference("QKU", row.get("qku_id"), row_key)

            if not disposition:
                raise InvariantError(
                    "SOURCE_CLOSURE_UNCLASSIFIED", f"{path}:{row_key}"
                )
            dispositions[disposition] += 1

        if cohort == "RP5D" and role != "OWNER_PROJECTION":
            expected_reference_kinds = {"FORMULA": 824, "QKU": 9_791}
            expected_absences = {
                "FORMULA_REF_NOT_PRESENT": 9_365,
                "QKU_REF_NOT_PRESENT": 398,
            }
            if dict(reference_kind_counts) != expected_reference_kinds:
                raise InvariantError(
                    "RP5D_REFERENCE_DENOMINATOR",
                    f"{path}: {dict(reference_kind_counts)} != "
                    f"{expected_reference_kinds}",
                )
            if dict(resolved_reference_kind_counts) != expected_reference_kinds:
                raise InvariantError(
                    "RP5D_RESOLVED_REFERENCE_DENOMINATOR",
                    f"{path}: {dict(resolved_reference_kind_counts)} != "
                    f"{expected_reference_kinds}",
                )
            if dict(absence_disposition_counts) != expected_absences:
                raise InvariantError(
                    "RP5D_ABSENCE_DISPOSITION_DENOMINATOR",
                    f"{path}: {dict(absence_disposition_counts)} != "
                    f"{expected_absences}",
                )
            expected_context = (
                {"REQUIRED_FORMULA_TO_PNL_ADAPTER_CONTRACT": 10_189}
                if path.endswith("rp5d_comp_materialization.jsonl")
                else {}
            )
            if dict(non_computation_context_counts) != expected_context:
                raise InvariantError(
                    "RP5D_NON_COMPUTATION_CONTEXT_DENOMINATOR",
                    f"{path}: {dict(non_computation_context_counts)} != "
                    f"{expected_context}",
                )

        if sum(dispositions.values()) != len(rows):
            raise InvariantError(
                "SOURCE_CLOSURE_CLASSIFIED_DENOMINATOR",
                f"{path}: classified={sum(dispositions.values())} actual={len(rows)}",
            )
        cohort_rows[cohort] += len(rows)
        cohort_dispositions[cohort].update(dispositions)
        total_reference_occurrences += reference_occurrences
        total_resolved_reference_occurrences += resolved_reference_occurrences
        artifact_reports.append(
            {
                "artifact": path,
                "role": role,
                "row_key": key_field,
                "declared_rows": metadata["declared_rows"],
                "actual_rows_read": metadata["actual_rows_read"],
                "classified_rows": sum(dispositions.values()),
                "preview_rows_ignored": metadata["preview_rows_ignored"],
                "physical_file_count": len(metadata["physical_files_read"]),
                "manifest_count_used_as_value_consumption": False,
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
                "semantic_classification_unresolved_count": 0,
                "semantic_promotion_blocked_pending_direct_proof_count": (
                    len(rows) if role == "DISCOVERY" else 0
                ),
                "semantic_classification_exact_action": (
                    "PROVE_COMPLETE_TYPED_SEMANTICS_AND_DIRECT_EQUIVALENCE_"
                    "BEFORE_CANONICAL_PROMOTION"
                    if role == "DISCOVERY"
                    else None
                ),
            }
        )
        deadline.check(f"source closure classify {cohort}")

    if (gfp_selected_count, gfp_terminal_count) != (35, 9):
        raise InvariantError(
            "GFP_SOURCE_DISPOSITION_COUNTS",
            f"selected={gfp_selected_count}, terminal={gfp_terminal_count}",
        )
    if gfp_discovery_mapping_count != 0:
        raise InvariantError(
            "GFP_DISCOVERY_MAPPING_COUNT",
            f"{gfp_discovery_mapping_count}/0",
        )
    if semantic_candidate_mapping_count != 142:
        raise InvariantError(
            "SOURCE_CANDIDATE_MAPPING_COUNT",
            f"{semantic_candidate_mapping_count}/142",
        )
    if map3_attached_qku_count != 47:
        raise InvariantError(
            "MAP3_QKU_ATTACHMENT_COUNT", f"{map3_attached_qku_count}/47"
        )
    contextual_reference_origins = {
        "PR162E_CONTEXT_REFERENCE",
        "PR162E_Q_CONTEXT_REFERENCE",
        "PR166_SM3_EVIDENCE_REFERENCE",
    }
    leaked_underlying_qku_roles = [
        str(record["canonical_component_id"])
        for record in records
        if contextual_reference_origins.intersection(record.get("origin_cohorts", ()))
        and str(record.get("definition", {}).get("component_kind", ""))
        in {"PURE_FORMULA", "NUMERICAL_ALGORITHM"}
        and record.get("uses", {}).get("qku_role_bindings")
    ]
    if leaked_underlying_qku_roles:
        raise InvariantError(
            "SOURCE_SELECTION_UNDERLYING_COMPONENT_QKU_ROLE_LEAK",
            repr(leaked_underlying_qku_roles),
        )
    if (
        candidate_packet_source_alternative_count
        != EXPECTED_CANDIDATE_PACKET_SOURCE_ALTERNATIVES
        or len(candidate_packet_qku_targets)
        != EXPECTED_CANDIDATE_PACKET_SOURCE_ALTERNATIVES
    ):
        raise InvariantError(
            "CANDIDATE_PACKET_SOURCE_ALTERNATIVE_DENOMINATOR",
            f"occurrences={candidate_packet_source_alternative_count}, "
            f"qkus={len(candidate_packet_qku_targets)}",
        )
    if candidate_packet_known_conflict_count != EXPECTED_CANDIDATE_PACKET_KNOWN_CONFLICTS:
        raise InvariantError(
            "CANDIDATE_PACKET_KNOWN_CONFLICT_DENOMINATOR",
            f"{candidate_packet_known_conflict_count}/"
            f"{EXPECTED_CANDIDATE_PACKET_KNOWN_CONFLICTS}",
        )
    candidate_runtime_root_leaks = sum(
        target in qku_targets.get(qku_id, set())
        for qku_id, target in candidate_packet_qku_targets.items()
    )
    if candidate_runtime_root_leaks:
        raise InvariantError(
            "CANDIDATE_PACKET_RUNTIME_ROOT_LEAK",
            str(candidate_runtime_root_leaks),
        )
    if len(owner_context_selection_tuples) != EXPECTED_SOURCE_SELECTION_TUPLES:
        raise InvariantError(
            "SOURCE_CONTEXT_SELECTION_TUPLE_DENOMINATOR",
            f"{len(owner_context_selection_tuples)}/{EXPECTED_SOURCE_SELECTION_TUPLES}",
        )
    if len(owner_context_selection_by_qku) != EXPECTED_SOURCE_SELECTION_QKUS:
        raise InvariantError(
            "SOURCE_CONTEXT_SELECTION_QKU_DENOMINATOR",
            f"{len(owner_context_selection_by_qku)}/{EXPECTED_SOURCE_SELECTION_QKUS}",
        )
    positive_evidence_path = (
        "docs/master_plan/generated/PR166_SM3_PosEvidence.report.json"
    )
    source_selection_cross_cohort_qkus = sum(
        positive_evidence_path in paths and len(paths) > 1
        for paths in owner_context_selection_qku_paths.values()
    )
    if (
        source_selection_cross_cohort_qkus
        != EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS
    ):
        raise InvariantError(
            "SOURCE_SELECTION_CROSS_COHORT_QKU_DENOMINATOR",
            f"{source_selection_cross_cohort_qkus}/"
            f"{EXPECTED_SOURCE_SELECTION_CROSS_COHORT_QKUS}",
        )
    if (
        agent_reachable_reference_occurrence_count
        != EXPECTED_AGENT_REACHABLE_REFERENCE_OCCURRENCES
        or len(agent_reachable_selector_keys)
        != EXPECTED_AGENT_REACHABLE_SELECTOR_KEYS
    ):
        raise InvariantError(
            "AGENT_STATUS_EXPLAIN_SELECTOR_DENOMINATOR",
            f"references={agent_reachable_reference_occurrence_count}, "
            f"selectors={len(agent_reachable_selector_keys)}",
        )
    if (
        gfp_discovery_blocked_promotion_count != EXPECTED_GFP_DISCOVERY_ROWS
        or gfp_discovery_implemented_context_count != 19_393
        or gfp_discovery_input_gap_context_count != 722
    ):
        raise InvariantError(
            "GFP_DISCOVERY_EXACT_BLOCKER_DENOMINATOR",
            f"blocked={gfp_discovery_blocked_promotion_count}/"
            f"{EXPECTED_GFP_DISCOVERY_ROWS}, implemented="
            f"{gfp_discovery_implemented_context_count}/19393, input_gap="
            f"{gfp_discovery_input_gap_context_count}/722",
        )
    if (
        gfp_discovery_exact_expression_match_count != 0
        or gfp_discovery_expression_containment_match_count
        != EXPECTED_GFP_DISCOVERY_TEXTUAL_CONTAINMENT_HINT_ROWS
    ):
        raise InvariantError(
            "GFP_DISCOVERY_TEXTUAL_HINT_DENOMINATOR",
            f"exact={gfp_discovery_exact_expression_match_count}, "
            f"containment={gfp_discovery_expression_containment_match_count}",
        )
    if total_resolved_reference_occurrences != total_reference_occurrences:
        raise InvariantError(
            "SOURCE_COMPUTATION_REFERENCE_COVERAGE",
            f"resolved={total_resolved_reference_occurrences}/"
            f"{total_reference_occurrences}",
        )
    physical_rows = sum(item["actual_rows_read"] for item in artifact_reports)
    classified_rows = sum(item["classified_rows"] for item in artifact_reports)
    if physical_rows != classified_rows:
        raise InvariantError(
            "SOURCE_CLOSURE_CLASSIFIED_DENOMINATOR",
            f"physical={physical_rows}, classified={classified_rows}",
        )
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

    artifact_by_cohort: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for report, spec in zip(artifact_reports, closure_artifacts):
        artifact_by_cohort[str(spec["cohort"])].append(report)
    cohort_reports = [
        {
            "cohort": cohort,
            "physical_rows_read_and_classified": cohort_rows[cohort],
            "disposition_counts": dict(sorted(cohort_dispositions[cohort].items())),
            "unresolved_count": 0,
            "semantic_classification_exact_action": (
                "PROVE_COMPLETE_TYPED_SEMANTICS_AND_DIRECT_EQUIVALENCE_"
                "BEFORE_CANONICAL_PROMOTION"
                if cohort in {"MASTER_PLAN_DISCOVERY", "POST_RP5C_DISCOVERY"}
                else None
            ),
            "computation_reference_occurrence_count": sum(
                int(item["computation_reference_occurrences"])
                for item, item_spec in zip(
                    artifact_reports, closure_artifacts
                )
                if str(item_spec["cohort"]) == cohort
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
    return {
        "protocol": "INDEPENDENT_ROW_LEVEL_DECLARED_SHARD_VALUE_CONSUMPTION",
        "artifact_count": len(artifact_reports),
        "physical_rows_read": physical_rows,
        "classified_physical_rows": classified_rows,
        "artifacts": artifact_reports,
        "cohorts": cohort_reports,
        "manifest_owner_split": manifest_owner_split,
        "manifest_owner_unclassified_entry_count": sum(
            int(item["unclassified_manifest_entries"])
            for item in manifest_owner_split
        ),
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
        "gfp_selected_expression_mappings": gfp_selected_count,
        "gfp_terminal_dispositions": gfp_terminal_count,
        "gfp_discovery_selected_formula_mappings": gfp_discovery_mapping_count,
        "semantic_candidate_control1_provenance_mappings": (
            semantic_candidate_mapping_count
        ),
        "map3_qku_roles_attached_to_mapped_target": map3_attached_qku_count,
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
        "agent_reachable_computation_references_resolved": (
            agent_reachable_reference_occurrence_count
        ),
        "unresolved_source_occurrence_count": 0,
        "unresolved_source_local_runtime_computation_reference_count": 0,
        "context_or_evidence_row_admitted_as_computation_count": context_or_evidence_admitted,
        "manifest_count_only_consumption_count": 0,
        "canonical_test_or_validator_source_count": 0,
        "canonical_post_launch_synthetic_source_count": 0,
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
        "source_context_selection_tuple_count": len(owner_context_selection_tuples),
        "source_context_selection_unique_qku_count": len(owner_context_selection_by_qku),
        "source_selection_cross_cohort_qku_count": (
            source_selection_cross_cohort_qkus
        ),
        "agent_reachable_status_explain_reference_occurrence_count": (
            agent_reachable_reference_occurrence_count
        ),
        "agent_reachable_status_explain_selector_key_count": len(
            agent_reachable_selector_keys
        ),
        "agent_reachable_status_explain_selector_keys": [
            {
                "qku_id": key[0],
                "role_or_decision_stage": key[1],
                "market_family": key[2],
                "canonical_component_id": sorted(
                    status_explain_qku_context_targets[key]
                )[0],
            }
            for key in sorted(agent_reachable_selector_keys)
        ],
        "agent_reachable_computation_reference_resolution_coverage": (
            "100%_OF_EXPLICIT_CURRENT_PR165_D2_STATUS_EXPLAIN_SUBSET"
        ),
        "gfp_discovery_rows_semantic_classification_unresolved": 0,
        "gfp_discovery_rows_promotion_blocked_pending_direct_proof": (
            gfp_discovery_blocked_promotion_count
        ),
        "gfp_discovery_implemented_context_count": (
            gfp_discovery_implemented_context_count
        ),
        "gfp_discovery_input_gap_context_count": (
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
        "full_lossy_gfp_catalog_direct_semantic_equivalence": (
            "BLOCKED_PENDING_COMPLETE_TYPED_SEMANTICS_AND_DIRECT_PROOF"
        ),
        "pr162b_source_vector_validation": pr162b_source_vector_metrics,
        "gfp_importable_registered_callable_ref_count": len(gfp_registered_refs),
        "gfp_complete_typed_source_vector_count": 0,
        "gfp_eligible_central_fixture_invocation_count": 0,
        "gfp_exact_action": "MISSING_COMPLETE_TYPED_TEST_VECTOR",
        "compact_contextual_reference_lineage": {
            "record_count": len(contextual_reference_records),
            "source_occurrence_count": sum(contextual_reference_counts.values()),
            "embedded_source_row_array_count": 0,
            "qku_role_count_on_underlying_contextual_records": 0,
            "rederivation_policy": (
                "OWNER_ARTIFACT_MATCH_FIELD_VALUE_REDERIVED_INDEPENDENTLY"
            ),
        },
        "owner_retained_source_local_reference_blocker_count": (
            owner_retained_source_local_reference_blocker_count
        ),
        "overlap_policy": "COHORTS_REMAIN_NON_ADDITIVE_AND_ARE_CLASSIFIED_INDEPENDENTLY",
    }


def _validate_no_orphan_closure(
    records: Sequence[Mapping[str, Any]], source_universe: Mapping[str, Any]
) -> dict[str, Any]:
    """Independently derive active/agent and upstream source no-orphan closure."""

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
        active = record.get("record_state") in RUNTIME_ACTIVE_RECORD_STATES
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
        for artifact in source_universe.get("artifacts", ())
        if isinstance(artifact, Mapping)
    ]
    unclassified_artifacts = [
        str(artifact.get("artifact", ""))
        for artifact in artifacts
        if int(artifact.get("classified_rows", -1))
        != int(artifact.get("actual_rows_read", -2))
        or int(artifact.get("unresolved_count", 0)) != 0
    ]
    if fake_audit_runtime_consumer_count:
        raise InvariantError(
            "FAKE_AUDIT_ONLY_RUNTIME_CONSUMER",
            str(fake_audit_runtime_consumer_count),
        )
    if orphan_ids:
        raise InvariantError(
            "ACTIVE_AGENT_REACHABLE_ORPHAN", repr(orphan_ids[:20])
        )
    if unclassified_artifacts:
        raise InvariantError(
            "UNCLASSIFIED_IN_SCOPE_UPSTREAM_ARTIFACT",
            repr(unclassified_artifacts[:20]),
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


def _validate_status_explain_only_qku_surface(
    facade_class: type[Any],
    records: Sequence[Mapping[str, Any]],
    source_universe: Mapping[str, Any],
    deadline: Deadline,
) -> dict[str, Any]:
    """Exercise every declared research-only QKU selector through the facade.

    These selectors preserve current-owner QKU purpose without becoming
    execution roots.  The independent probe therefore requires status and
    explain to resolve the exact contextual root while resolve and compute
    reject the same selector before any implementation can run.
    """

    raw_selectors = source_universe.get(
        "agent_reachable_status_explain_selector_keys", ()
    )
    if not isinstance(raw_selectors, Sequence) or isinstance(
        raw_selectors, (str, bytes)
    ):
        raise InvariantError(
            "STATUS_EXPLAIN_SELECTOR_PROBE_INPUT", type(raw_selectors).__name__
        )
    if len(raw_selectors) != EXPECTED_AGENT_REACHABLE_SELECTOR_KEYS:
        raise InvariantError(
            "STATUS_EXPLAIN_SELECTOR_PROBE_DENOMINATOR",
            f"{len(raw_selectors)}/{EXPECTED_AGENT_REACHABLE_SELECTOR_KEYS}",
        )

    plane = facade_class(records=records)
    context = {
        "mode": "STATIC_VALIDATION",
        "market": "UNRESOLVED",
        "venue": "NO_VENUE",
        "context_family": "SOURCE_IDENTITY_REVIEW",
    }
    status_count = 0
    explain_count = 0
    resolve_denial_count = 0
    compute_denial_count = 0
    for index, row in enumerate(raw_selectors):
        if index % 100 == 0:
            deadline.check("status/explain-only QKU facade probe")
        if not isinstance(row, Mapping):
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_PROBE_INPUT", repr(row)
            )
        expected_target = str(row.get("canonical_component_id", ""))
        selector = {
            "qku_id": str(row.get("qku_id", "")),
            "role_or_decision_stage": str(
                row.get("role_or_decision_stage", "")
            ),
            "market_family": str(row.get("market_family", "")),
        }
        if not expected_target or any(not value for value in selector.values()):
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_PROBE_INPUT", repr(row)
            )

        status = plane.status(
            selector,
            context,
            agent_id="research_agent",
        )
        if str(status.get("canonical_component_id")) != expected_target:
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_TARGET",
                f"{selector!r}: {status.get('canonical_component_id')} != "
                f"{expected_target}",
            )
        readiness = status.get("binding_readiness", {})
        if (
            not isinstance(readiness, Mapping)
            or readiness.get("specification") != "REQUIRED"
            or status.get("derived_state") != "SPECIFICATION_REQUIRED"
            or not status.get("exact_resolution_action")
        ):
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_FALSE_READINESS",
                f"{selector!r}: {status!r}",
            )
        research_policy = status.get("agent_access", {}).get("research_agent", {})
        if (
            not isinstance(research_policy, Mapping)
            or set(research_policy.get("control_plane_operations", ()))
            != {"status", "explain"}
            or set(research_policy.get("research_operations", ()))
            != {"propose_batch_item"}
        ):
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_AGENT_POLICY",
                f"{selector!r}: {research_policy!r}",
            )
        status_count += 1

        explanation = plane.explain(
            selector,
            context,
            agent_id="research_agent",
        )
        if (
            str(explanation.get("identity", {}).get("canonical_component_id"))
            != expected_target
            or explanation.get("no_new_numerical_output") is not True
            or not explanation.get("exact_next_action")
        ):
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_EXPLANATION",
                f"{selector!r}: {explanation!r}",
            )
        explain_count += 1

        resolve_code = _runtime_error_code(
            lambda selector=selector: plane.resolve(
                selector,
                context,
                agent_id="research_agent",
            )
        )
        if resolve_code != "SELECTOR_NOT_RESOLVED":
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_RESOLVE_DENIAL",
                f"{selector!r}: {resolve_code}",
            )
        resolve_denial_count += 1

        compute_code = _runtime_error_code(
            lambda selector=selector: plane.compute(
                selector,
                {},
                context,
                agent_id="research_agent",
                consumer="INDEPENDENT_VALIDATOR",
            )
        )
        if compute_code != "SELECTOR_NOT_RESOLVED":
            raise InvariantError(
                "STATUS_EXPLAIN_SELECTOR_COMPUTE_DENIAL",
                f"{selector!r}: {compute_code}",
            )
        compute_denial_count += 1

    diagnostics = plane._diagnostics()
    if (
        diagnostics.get("runtime_registry_file_reads_after_initialization") != 0
        or diagnostics.get("per_request_full_registry_iterations") != 0
        or diagnostics.get("unrelated_component_executions") != 0
    ):
        raise InvariantError(
            "STATUS_EXPLAIN_SELECTOR_INDEXED_RUNTIME",
            repr(diagnostics),
        )
    return {
        "selector_count": len(raw_selectors),
        "status_exact_target_count": status_count,
        "explain_exact_target_count": explain_count,
        "resolve_denial_count": resolve_denial_count,
        "compute_denial_count": compute_denial_count,
        "runtime_registry_file_reads_after_initialization": 0,
        "per_request_full_registry_iterations": 0,
        "unrelated_component_executions": 0,
    }


def _rp5c_source(
    repo_root: Path, deadline: Deadline
) -> tuple[dict[str, dict[str, Any]], int]:
    path = repo_root / RP5C_DEDUPE
    groups: dict[str, dict[str, Any]] = {}
    duplicate_group_ids: set[str] = set()
    member_owner: dict[str, str] = {}
    member_count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 1000 == 0:
                deadline.check("rp5c_source")
            row = json.loads(line)
            canonical = row.get("canonical_identity_row_id")
            members = row.get("duplicate_member_identity_row_ids")
            group_id = row.get("duplicate_group_id")
            if not isinstance(canonical, str) or not RP5C_ID_RE.fullmatch(canonical):
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: canonical")
            if not isinstance(group_id, str) or not group_id or group_id in duplicate_group_ids:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: duplicate group")
            duplicate_group_ids.add(group_id)
            if not isinstance(members, list) or len(members) != row.get("duplicate_member_count"):
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: members")
            member_set = set(members)
            if len(member_set) != len(members) or canonical not in member_set:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: member uniqueness")
            if canonical in groups:
                raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: duplicate canonical")
            for member in members:
                if not isinstance(member, str) or not RP5C_ID_RE.fullmatch(member):
                    raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: member identity")
                if member in member_owner:
                    raise InvariantError("RP5C_SOURCE_INVALID", f"line {line_number}: repeated member")
                member_owner[member] = canonical
            groups[canonical] = {
                "duplicate_group_id": group_id,
                "dedupe_status": row.get("dedupe_status"),
                "members": member_set,
                "source_artifact_refs": {RP5C_DEDUPE.as_posix()},
                "inner_source_artifact_refs": set(),
                "source_artifact_row_ids": set(),
                "provenance_tiers": set(),
                "custody_route_refs": set(),
                "identity_types": set(),
                "market_family_tags": set(),
                "ontology_categories": set(),
                "qku_roles": set(),
            }
            member_count += len(members)
    if len(groups) != EXPECTED_RP5C_CANONICAL or member_count < len(groups):
        raise InvariantError("RP5C_SOURCE_COUNT", f"groups={len(groups)}, members={member_count}")
    if (
        EXPECTED_RP5C_CANONICAL == 10_189
        and member_count != EXPECTED_RP5C_OCCURRENCES
    ):
        raise InvariantError(
            "RP5C_SOURCE_COUNT",
            f"occurrences={member_count}/{EXPECTED_RP5C_OCCURRENCES}",
        )

    custody_key_owners: dict[tuple[str, ...], str] = {}
    canonical_library_rows: set[str] = set()
    for relative_path in RP5C_LIBRARIES:
        with (repo_root / relative_path).open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line_number % 1000 == 0:
                    deadline.check("rp5c_library_source")
                row = json.loads(line)
                canonical = row.get("canonical_identity_row_id")
                if canonical not in groups:
                    raise InvariantError(
                        "RP5C_LIBRARY_INVALID",
                        f"{relative_path.as_posix()} line {line_number}: canonical",
                    )
                if relative_path == RP5C_CANONICAL_LIBRARY:
                    if canonical in canonical_library_rows:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_COLLISION",
                            f"repeated canonical library row: {canonical}",
                        )
                    canonical_library_rows.add(str(canonical))
                    source_group = groups[str(canonical)]
                    if row.get("duplicate_group_id") != source_group["duplicate_group_id"]:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_INVALID",
                            f"{canonical}: canonical-library/ledger group mismatch",
                        )
                    key_payload = _rp5c_group_custody_key(row)
                    key = _rp5c_group_custody_tuple(key_payload)
                    prior = custody_key_owners.get(key)
                    if prior is not None:
                        raise InvariantError(
                            "RP5C_SOURCE_GROUP_KEY_COLLISION",
                            f"{prior} <> {canonical}",
                        )
                    custody_key_owners[key] = str(canonical)
                    source_group["source_group_custody_key"] = key_payload
                    source_group["source_group_custody_tuple"] = key
                groups[canonical]["source_artifact_refs"].add(
                    relative_path.as_posix()
                )
                source_artifact_ref = row.get("source_artifact_ref")
                if source_artifact_ref not in (None, ""):
                    if not isinstance(source_artifact_ref, str):
                        raise InvariantError(
                            "RP5C_LIBRARY_INVALID",
                            f"{relative_path.as_posix()} line {line_number}: "
                            "non-text source_artifact_ref",
                        )
                    groups[canonical]["inner_source_artifact_refs"].add(
                        source_artifact_ref
                    )
                source_artifact_row_id = row.get("source_artifact_row_id")
                if source_artifact_row_id:
                    groups[canonical]["source_artifact_row_ids"].add(
                        str(source_artifact_row_id)
                    )
                identity_type = row.get("identity_type", row.get("qku_type"))
                if identity_type:
                    groups[canonical]["identity_types"].add(str(identity_type))
                for field in ("market_family", "qku_family", "formula_family"):
                    value = str(row.get(field) or "")
                    if value and "unknown" not in value.lower():
                        groups[canonical]["market_family_tags"].add(value)
                ontology = str(row.get("ontology_category") or "")
                if ontology:
                    groups[canonical]["ontology_categories"].add(ontology)
                if row.get("qku_id"):
                    groups[canonical]["qku_roles"].add(
                        (
                            str(row["qku_id"]),
                            ontology or "SEMANTICS_UNRESOLVED",
                            str(row.get("market_family") or "UNRESOLVED"),
                        )
                    )
    if canonical_library_rows != set(groups) or len(custody_key_owners) != len(groups):
        missing = sorted(set(groups) - canonical_library_rows)[:10]
        extra = sorted(canonical_library_rows - set(groups))[:10]
        raise InvariantError(
            "RP5C_SOURCE_GROUP_KEY_CLOSURE",
            f"keys={len(custody_key_owners)}, groups={len(groups)}, missing={missing}, extra={extra}",
        )

    lineage_members: set[str] = set()
    with (repo_root / RP5C_LINEAGE).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number % 1000 == 0:
                deadline.check("rp5c_lineage_source")
            row = json.loads(line)
            canonical = row.get("canonical_identity_row_id")
            member = row.get("identity_row_id")
            if (
                not isinstance(canonical, str)
                or canonical not in groups
                or not isinstance(member, str)
                or member not in groups[canonical]["members"]
            ):
                raise InvariantError("RP5C_LINEAGE_INVALID", f"line {line_number}: canonical/member")
            if member in lineage_members:
                raise InvariantError("RP5C_LINEAGE_INVALID", f"line {line_number}: repeated member")
            lineage_members.add(member)
            groups[canonical]["source_artifact_refs"].add(
                RP5C_LINEAGE.as_posix()
            )
            source_artifact_ref = row.get("source_artifact_ref")
            if source_artifact_ref not in (None, ""):
                if not isinstance(source_artifact_ref, str):
                    raise InvariantError(
                        "RP5C_LINEAGE_INVALID",
                        f"line {line_number}: non-text source_artifact_ref",
                    )
                groups[canonical]["inner_source_artifact_refs"].add(
                    source_artifact_ref
                )
            source_artifact_row_id = row.get("source_artifact_row_id")
            if source_artifact_row_id:
                groups[canonical]["source_artifact_row_ids"].add(
                    str(source_artifact_row_id)
                )
            provenance_tier = row.get("provenance_tier")
            if provenance_tier:
                groups[canonical]["provenance_tiers"].add(str(provenance_tier))
            groups[canonical]["custody_route_refs"].update(
                str(value) for value in row.get("custody_route_refs", ())
            )
    missing_inner_refs = sorted(
        canonical
        for canonical, group in groups.items()
        if not group["inner_source_artifact_refs"]
    )
    if missing_inner_refs:
        raise InvariantError(
            "RP5C_INNER_SOURCE_REF_MISSING",
            f"canonical identities without refs: {missing_inner_refs[:10]}",
        )
    expected_members = set(member_owner)
    if lineage_members != expected_members:
        missing = sorted(expected_members - lineage_members)[:10]
        extra = sorted(lineage_members - expected_members)[:10]
        raise InvariantError(
            "RP5C_LINEAGE_CLOSURE",
            f"lineage={len(lineage_members)}, dedupe_members={member_count}, missing={missing}, extra={extra}",
        )
    return groups, member_count


def _registry_rp5c_group_map(
    records: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, ...], str]:
    key_to_component: dict[tuple[str, ...], str] = {}
    baseline_components: set[str] = set()
    for record in records:
        if "RP5C_BASELINE" not in {str(value) for value in record.get("origin_cohorts", ())}:
            continue
        component_id = str(record.get("canonical_component_id") or "")
        baseline_components.add(component_id)
        key_payloads = [
            relation.get("source_group_custody_key")
            for relation in record.get("relations", ())
            if isinstance(relation, Mapping)
            and _relation_type(relation)
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        ]
        if len(key_payloads) != 1 or not isinstance(key_payloads[0], Mapping):
            raise InvariantError("RP5C_STABLE_GROUP_KEY", component_id)
        key = _rp5c_group_custody_tuple(
            key_payloads[0], code="RP5C_STABLE_GROUP_KEY"
        )
        prior = key_to_component.get(key)
        if prior is not None and prior != component_id:
            raise InvariantError(
                "RP5C_STABLE_GROUP_COLLISION", f"{key!r}: {prior} <> {component_id}"
            )
        key_to_component[key] = component_id
    if (
        len(baseline_components) != EXPECTED_RP5C_CANONICAL
        or len(key_to_component) != EXPECTED_RP5C_CANONICAL
    ):
        raise InvariantError(
            "RP5C_STABLE_GROUP_COUNT",
            f"records={len(baseline_components)}, groups={len(key_to_component)}",
        )
    return key_to_component


def _validate_rp5c_nonruntime_qku_roles(record: Mapping[str, Any]) -> int:
    component_id = str(record.get("canonical_component_id") or "")
    roles = record.get("uses", {}).get("qku_role_bindings", ())
    if not roles:
        return 0
    exact_action = f"MISSING_SEMANTIC_SPECIFICATION: {component_id}"
    if record.get("record_state") != "DORMANT_PRESERVED":
        raise InvariantError("RP5C_QKU_ROLE_RUNTIME_ACTIVATION", component_id)
    for role in roles:
        if (
            not isinstance(role, Mapping)
            or role.get("stack_root_or_direct_component") is not None
            or role.get("selection_rule_if_container") is not None
            or role.get("runtime_root_eligibility")
            != "INELIGIBLE_UNTIL_COMPLETE_SEMANTICS_AND_DIRECT_ROOT_PROOF"
            or role.get("exact_resolution_action") != exact_action
        ):
            raise InvariantError("RP5C_QKU_ROLE_RUNTIME_ROOT", component_id)
    ineligibility = [
        relation
        for relation in record.get("relations", ())
        if isinstance(relation, Mapping)
        and _relation_type(relation) == "RP5C_RUNTIME_ROOT_INELIGIBILITY"
    ]
    if len(ineligibility) != 1:
        raise InvariantError("RP5C_QKU_ROLE_INELIGIBILITY_PROOF", component_id)
    proof = ineligibility[0]
    if (
        proof.get("runtime_root_eligible") is not False
        or proof.get("selector_or_root_invented") is not False
        or proof.get("qku_roles_erased") is not False
        or proof.get("preserved_qku_role_count") != len(roles)
        or proof.get("exact_resolution_action") != exact_action
    ):
        raise InvariantError("RP5C_QKU_ROLE_INELIGIBILITY_PROOF", component_id)
    if any(
        _relation_type(relation) == "ALIAS_OF"
        for relation in record.get("relations", ())
        if isinstance(relation, Mapping)
    ):
        raise InvariantError("RP5C_CUSTODY_KEY_FALSE_EQUIVALENCE", component_id)
    bindings = record.get("bindings", ())
    if not bindings or any(
        not isinstance(binding, Mapping)
        or binding.get("activation_state") != "DORMANT_PRESERVED"
        or bool(binding.get("supported_modes"))
        or binding.get("selected_implementation_version") is not None
        or binding.get("readiness", {}).get("authorization") != "NOT_ELIGIBLE"
        for binding in bindings
    ):
        raise InvariantError("RP5C_QKU_ROLE_RUNTIME_BINDING", component_id)
    return len(roles)


def _validate_rp5c_import(
    records: Sequence[Mapping[str, Any]],
    groups: Mapping[str, Mapping[str, Any]],
    deadline: Deadline,
    accepted_group_map: Mapping[tuple[str, ...], str] | None = None,
) -> tuple[int, int]:
    expected_member_count = sum(len(group["members"]) for group in groups.values())
    by_group_id = {
        str(group["duplicate_group_id"]): (canonical, group)
        for canonical, group in groups.items()
    }
    by_custody_key = {
        tuple(group["source_group_custody_tuple"]): (canonical, group)
        for canonical, group in groups.items()
    }
    if len(by_custody_key) != len(groups):
        raise InvariantError("RP5C_SOURCE_GROUP_KEY_COLLISION", "source key map")
    exact_group_records: dict[str, set[str]] = defaultdict(set)
    exact_lineage_records: dict[str, set[str]] = defaultdict(set)
    current_group_ids = set(by_group_id)
    for index, record in enumerate(records):
        if index % 1000 == 0:
            deadline.check("rp5c_registry_scan")
        origins = {str(value) for value in record.get("origin_cohorts", [])}
        if "RP5C_BASELINE" not in origins:
            continue
        component_id = str(record["canonical_component_id"])
        _validate_rp5c_nonruntime_qku_roles(record)
        for relation in record.get("relations", ()):
            if not isinstance(relation, Mapping):
                continue
            relation_type = _relation_type(relation)
            if relation_type == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF":
                group_id = str(relation.get("source_duplicate_group_id") or "")
                if group_id not in current_group_ids:
                    raise InvariantError(
                        "RP5C_REGISTRY_UNKNOWN_GROUP", f"{component_id}: {group_id}"
                    )
                source_canonical, source_group = by_group_id[group_id]
                key_payload = relation.get("source_group_custody_key")
                custody_key = tuple(source_group["source_group_custody_tuple"])
                accepted_component_id = (
                    accepted_group_map.get(custody_key)
                    if accepted_group_map is not None
                    else None
                )
                expected_component_id = accepted_component_id or (
                    "QTT.COMP.RP5C."
                    f"{source_canonical.removeprefix('RP5C_IDENTITY_')}"
                )
                if component_id != expected_component_id:
                    raise InvariantError(
                        "RP5C_STABLE_CANONICAL_ID",
                        f"{source_canonical}: {component_id} != {expected_component_id}",
                    )
                observed_role_rows = [
                    role
                    for role in record.get("uses", {}).get(
                        "qku_role_bindings", ()
                    )
                    if isinstance(role, Mapping)
                ]
                observed_role_tuples = {
                    (
                        str(role.get("qku_id", "")),
                        str(role.get("role_or_decision_stage", "")),
                        str(role.get("market_family", "")),
                    )
                    for role in observed_role_rows
                }
                if (
                    len(observed_role_tuples) != len(observed_role_rows)
                    or observed_role_tuples != set(source_group["qku_roles"])
                ):
                    raise InvariantError(
                        "RP5C_QKU_ROLE_TUPLE_CLOSURE",
                        f"{component_id}: observed={len(observed_role_tuples)} "
                        f"source={len(source_group['qku_roles'])}",
                    )
                if (
                    isinstance(key_payload, Mapping)
                    and _rp5c_group_custody_tuple(
                        key_payload, code="RP5C_REGISTRY_GROUP_KEY_INVALID"
                    )
                    == tuple(source_group["source_group_custody_tuple"])
                    and relation.get("source_canonical_identity_row_id")
                    == source_canonical
                    and relation.get("source_occurrence_count")
                    == len(source_group["members"])
                    and relation.get("source_dedupe_status")
                    == source_group["dedupe_status"]
                    and relation.get("exact_lineage_validation_status")
                    == "SOURCE_MEMBERSHIP_RECONSTRUCTED_AND_CLOSED_AT_BUILD_TIME"
                    and relation.get("direct_semantic_equivalence_proven") is False
                    and not {
                        "member_identity_row_ids",
                        "identity_row_ids",
                        "source_artifact_row_ids",
                    }.intersection(relation)
                ):
                    exact_group_records[group_id].add(component_id)
            elif relation_type == "RP5C_SOURCE_LINEAGE_SUMMARY":
                canonical = str(relation.get("source_canonical_identity_row_id") or "")
                source_group = groups.get(canonical)
                if source_group is None:
                    continue
                record_provenance_refs = {
                    str(entry.get("source_artifact_ref", ""))
                    for entry in record.get("provenance", ())
                    if isinstance(entry, Mapping)
                    and entry.get("source_artifact_ref")
                }
                expected_provenance_refs = set(
                    source_group["source_artifact_refs"]
                )
                uses = record.get("uses", {})
                observed_market_tags = {
                    str(value) for value in uses.get("market_family_tags", ())
                }
                if (
                    relation.get("source_occurrence_count")
                    == len(source_group["members"])
                    and relation.get("source_artifact_refs")
                    == sorted(source_group["inner_source_artifact_refs"])
                    and relation.get("source_artifact_ref_count")
                    == len(source_group["inner_source_artifact_refs"])
                    and record_provenance_refs == expected_provenance_refs
                    and relation.get("source_artifact_row_count")
                    == len(source_group["source_artifact_row_ids"])
                    and set(relation.get("provenance_tiers", ()))
                    == set(source_group["provenance_tiers"])
                    and set(relation.get("custody_route_refs", ()))
                    == set(source_group["custody_route_refs"])
                    and relation.get("qku_role_market_ontology_summary")
                    == {
                        "qku_roles_location": "record.uses.qku_role_bindings",
                        "market_family_tags_location": (
                            "record.uses.market_family_tags"
                        ),
                        "ontology_categories": sorted(
                            source_group["ontology_categories"]
                        ),
                        "qku_role_count": len(source_group["qku_roles"]),
                    }
                    and observed_market_tags
                    == set(source_group["market_family_tags"])
                    and relation.get("exact_lineage_validation_status")
                    == "SOURCE_OCCURRENCES_RECONSTRUCTED_AND_CLOSED_AT_BUILD_TIME"
                    and relation.get("immutable_original_preserved") is True
                    and not {
                        "member_identity_row_ids",
                        "identity_row_ids",
                        "source_artifact_row_ids",
                    }.intersection(relation)
                ):
                    exact_lineage_records[canonical].add(component_id)

    missing_groups = [group_id for group_id in current_group_ids if not exact_group_records[group_id]]
    ambiguous_groups = [
        group_id for group_id in current_group_ids if len(exact_group_records[group_id]) != 1
    ]
    missing_lineage = [canonical for canonical in groups if not exact_lineage_records[canonical]]
    ambiguous_lineage = [
        canonical for canonical in groups if len(exact_lineage_records[canonical]) != 1
    ]
    if missing_groups or ambiguous_groups or missing_lineage or ambiguous_lineage:
        raise InvariantError(
            "RP5C_CANONICAL_IMPORT",
            "missing_groups="
            f"{missing_groups[:10]}, ambiguous_groups={ambiguous_groups[:10]}, "
            f"missing_lineage={missing_lineage[:10]}, ambiguous_lineage={ambiguous_lineage[:10]}",
        )

    covered = 0
    stable_mismatches: list[str] = []
    for index, (canonical, source_group) in enumerate(groups.items()):
        if index % 1000 == 0:
            deadline.check("rp5c_member_coverage")
        group_id = str(source_group["duplicate_group_id"])
        custody_key = tuple(source_group["source_group_custody_tuple"])
        target = next(iter(exact_group_records[group_id]))
        if exact_lineage_records[canonical] != {target}:
            stable_mismatches.append(f"{group_id}: grouping/lineage target mismatch")
        if accepted_group_map is not None and accepted_group_map.get(custody_key) != target:
            stable_mismatches.append(
                f"{custody_key!r}: {accepted_group_map.get(custody_key)!r} -> {target!r}"
            )
        covered += len(source_group["members"])
    if stable_mismatches or covered != expected_member_count:
        raise InvariantError(
            "RP5C_DUPLICATE_MEMBER_COVERAGE",
            f"covered={covered}/{expected_member_count}, stable_mismatches={stable_mismatches[:10]}",
        )
    return len(groups), covered


def _validate_rp5c_inner_source_ref_mutations(
    records: Sequence[Mapping[str, Any]],
    groups: Mapping[str, Mapping[str, Any]],
    deadline: Deadline,
    accepted_group_map: Mapping[tuple[str, ...], str] | None = None,
) -> int:
    """Prove both missing and extra compact inner lineage refs fail closed."""

    selected_index = -1
    for index, record in enumerate(records):
        for relation in record.get("relations", ()):
            if (
                isinstance(relation, Mapping)
                and _relation_type(relation) == "RP5C_SOURCE_LINEAGE_SUMMARY"
                and relation.get("source_artifact_refs")
            ):
                selected_index = index
                break
        if selected_index >= 0:
            break
    if selected_index < 0:
        raise InvariantError(
            "RP5C_INNER_SOURCE_REF_FIXTURE_MISSING", "no nonempty compact ref set"
        )

    def mutated(extra: bool) -> list[Mapping[str, Any]]:
        candidate = list(records)
        changed = copy.deepcopy(records[selected_index])
        summary = next(
            relation
            for relation in changed["relations"]
            if _relation_type(relation) == "RP5C_SOURCE_LINEAGE_SUMMARY"
        )
        refs = list(summary["source_artifact_refs"])
        if extra:
            refs.append("VALIDATOR_INJECTED_NON_SOURCE_REF")
        else:
            refs.pop()
        summary["source_artifact_refs"] = sorted(refs)
        summary["source_artifact_ref_count"] = len(refs)
        candidate[selected_index] = changed
        return candidate

    for extra in (False, True):
        _expect_defect(
            "RP5C_CANONICAL_IMPORT",
            lambda extra=extra: _validate_rp5c_import(
                mutated(extra), groups, deadline, accepted_group_map
            ),
        )
    return 2


def _rp5c_compaction_counterfactual_once(
    records: Sequence[Mapping[str, Any]],
    groups: Mapping[str, Mapping[str, Any]],
    deadline: Deadline,
) -> dict[str, int]:
    total_compact_bytes = sum(
        len((_canonical_json(record) + "\n").encode("utf-8"))
        for record in records
    )
    compact_rp5c_bytes = 0
    uncompacted_rp5c_bytes = 0
    rp5c_record_count = 0
    for index, record in enumerate(records):
        if "RP5C_BASELINE" not in {
            str(value) for value in record.get("origin_cohorts", ())
        }:
            continue
        if index % 1_000 == 0:
            deadline.check("RP5C independent compaction counterfactual")
        rp5c_record_count += 1
        compact_rp5c_bytes += len(
            (_canonical_json(record) + "\n").encode("utf-8")
        )
        legacy = copy.deepcopy(dict(record))
        grouping = [
            relation
            for relation in legacy.get("relations", ())
            if isinstance(relation, Mapping)
            and _relation_type(relation)
            == "RP5C_BASELINE_GROUPING_NOT_CONTROL1_EQUIVALENCE_PROOF"
        ]
        lineage = [
            relation
            for relation in legacy.get("relations", ())
            if isinstance(relation, Mapping)
            and _relation_type(relation) == "RP5C_SOURCE_LINEAGE_SUMMARY"
        ]
        if len(grouping) != 1 or len(lineage) != 1:
            raise InvariantError(
                "RP5C_COMPACTION_COUNTERFACTUAL_SHAPE",
                str(record.get("canonical_component_id", "")),
            )
        source_identity = str(
            grouping[0].get("source_canonical_identity_row_id", "")
        )
        source_group = groups.get(source_identity)
        if source_group is None:
            raise InvariantError(
                "RP5C_COMPACTION_COUNTERFACTUAL_SOURCE", source_identity
            )
        grouping[0]["member_identity_row_ids"] = sorted(source_group["members"])
        lineage[0]["identity_row_ids"] = sorted(source_group["members"])
        lineage[0]["source_artifact_row_ids"] = sorted(
            source_group["source_artifact_row_ids"]
        )
        uncompacted_rp5c_bytes += len(
            (_canonical_json(legacy) + "\n").encode("utf-8")
        )
    if rp5c_record_count != EXPECTED_RP5C_CANONICAL:
        raise InvariantError(
            "RP5C_COMPACTION_COUNTERFACTUAL_COUNT",
            f"{rp5c_record_count}/{EXPECTED_RP5C_CANONICAL}",
        )
    total_uncompacted = (
        total_compact_bytes - compact_rp5c_bytes + uncompacted_rp5c_bytes
    )
    return {
        "compact_rp5c_serialized_bytes": compact_rp5c_bytes,
        "uncompacted_rp5c_counterfactual_serialized_bytes": (
            uncompacted_rp5c_bytes
        ),
        "compact_logical_registry_serialized_bytes": total_compact_bytes,
        "uncompacted_logical_registry_counterfactual_serialized_bytes": (
            total_uncompacted
        ),
        "compaction_bytes_reduced": total_uncompacted - total_compact_bytes,
    }


def _validate_rp5c_compaction_counterfactual(
    records: Sequence[Mapping[str, Any]],
    groups: Mapping[str, Mapping[str, Any]],
    deadline: Deadline,
) -> dict[str, Any]:
    first = _rp5c_compaction_counterfactual_once(records, groups, deadline)
    second = _rp5c_compaction_counterfactual_once(records, groups, deadline)
    if first != second:
        raise InvariantError(
            "RP5C_COMPACTION_COUNTERFACTUAL_NONDETERMINISTIC",
            f"first={first}, second={second}",
        )
    if (
        first["compaction_bytes_reduced"] <= 0
        or first["uncompacted_rp5c_counterfactual_serialized_bytes"]
        <= first["compact_rp5c_serialized_bytes"]
    ):
        raise InvariantError(
            "RP5C_COMPACTION_NOT_POSITIVE", repr(first)
        )
    return {
        **first,
        "counterfactual_source": "RP5C_DEDUPE_AND_LINEAGE_ROWS",
        "counterfactual_idempotent": True,
        "compaction_positive": True,
    }


def _owner_requirement_coverage(records: Sequence[Mapping[str, Any]]) -> int:
    mapping: dict[str, set[str]] = defaultdict(set)
    for record in records:
        component_id = str(record["canonical_component_id"])
        for path, value in _walk(record):
            if not path:
                continue
            key = path[-1]
            if key == "owner_requirement_id" and isinstance(value, str) and value:
                mapping[value].add(component_id)
            elif key == "owner_requirement_ids" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item:
                        mapping[item].add(component_id)
    ambiguous = {key: sorted(values) for key, values in mapping.items() if len(values) != 1}
    if len(mapping) != EXPECTED_OWNER_REQUIREMENTS or ambiguous:
        raise InvariantError(
            "OWNER_REQUIREMENT_COVERAGE",
            f"unique={len(mapping)}, ambiguous={dict(list(ambiguous.items())[:10])}",
        )
    return len(mapping)


def _implementation_ref(entry: Mapping[str, Any]) -> str:
    return str(
        entry.get("callable_or_solver_ref")
        or entry.get("callable_ref")
        or entry.get("implementation_ref")
        or ""
    )


def _implementation_class(record: Mapping[str, Any]) -> str:
    definition = record["definition"]
    explicit = str(
        definition.get("implementation_inventory_class")
        or definition.get("implementation_class")
        or ""
    ).upper()
    if explicit in EXPECTED_IMPLEMENTATIONS:
        return explicit
    for entry in definition.get("implementation_versions", []):
        if isinstance(entry, Mapping):
            explicit = str(entry.get("implementation_inventory_class") or entry.get("inventory_class") or "").upper()
            if explicit in EXPECTED_IMPLEMENTATIONS:
                return explicit
    # Component kind and origin do not prove that source inventory metadata is
    # a verified runtime implementation.  Only an explicit inventory class may
    # enter the executable inventory below.
    return ""


def _validate_nonruntime_source_inventory_record(
    record: Mapping[str, Any], implementations: Sequence[Mapping[str, Any]]
) -> int:
    component_id = str(record.get("canonical_component_id", ""))
    if record.get("record_state") == "CANONICAL_ACCEPTED":
        raise InvariantError(
            "SOURCE_INVENTORY_RUNTIME_ELIGIBILITY", component_id
        )
    versions: set[str] = set()
    for entry in implementations:
        version = str(entry.get("implementation_version", ""))
        if not version or version in versions:
            raise InvariantError(
                "SOURCE_INVENTORY_VERSION_SHAPE", f"{component_id}@{version!r}"
            )
        versions.add(version)
        if entry.get("security_state") != "SOURCE_INVENTORY_NOT_RUNTIME_ALLOWLISTED":
            raise InvariantError(
                "SOURCE_INVENTORY_SECURITY_STATE",
                f"{component_id}@{version}",
            )
    for binding in record.get("bindings", []):
        selected = binding.get("selected_implementation_version")
        if selected not in (None, ""):
            raise InvariantError(
                "SOURCE_INVENTORY_RUNTIME_SELECTION",
                f"{component_id}: {binding.get('binding_id')} -> {selected}",
            )
        readiness = binding.get("readiness", {})
        if (
            readiness.get("specification") != "REQUIRED"
            or readiness.get("implementation") != "REQUIRED"
            or binding.get("derived_state")
            in {"CONTEXT_READY", "STACK_READY", "EVIDENCED", "AUTHORIZED"}
        ):
            raise InvariantError(
                "SOURCE_INVENTORY_FALSE_READINESS",
                f"{component_id}: {binding.get('binding_id')}",
            )
        for agent_id, policy in _policy_entries(binding.get("agent_access_policy")):
            operations = policy.get("control_plane_operations") or policy.get(
                "allowed_operations"
            ) or []
            if not isinstance(operations, list) or not set(
                map(str, operations)
            ) <= {"status", "explain"}:
                raise InvariantError(
                    "SOURCE_INVENTORY_AGENT_COMPUTE_ACCESS",
                    f"{component_id}: {agent_id}",
                )
    return len(implementations)


def _validate_implementation_inventory(
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, int], list[Mapping[str, Any]]]:
    counts: Counter[str] = Counter()
    implementation_records: list[Mapping[str, Any]] = []
    callable_refs: set[str] = set()
    source_inventory_versions = 0
    for record in records:
        implementations = record["definition"].get("implementation_versions", [])
        if not implementations:
            continue
        inventory_class = _implementation_class(record)
        if not inventory_class:
            if not all(isinstance(entry, Mapping) for entry in implementations):
                raise InvariantError(
                    "IMPLEMENTATION_SHAPE", str(record["canonical_component_id"])
                )
            source_inventory_versions += _validate_nonruntime_source_inventory_record(
                record, implementations
            )
            continue
        counts[inventory_class] += 1
        implementation_records.append(record)
        for entry in implementations:
            if not isinstance(entry, Mapping):
                raise InvariantError("IMPLEMENTATION_SHAPE", str(record["canonical_component_id"]))
            reference = _implementation_ref(entry)
            _validate_callable_ref(reference)
            callable_refs.add(reference)
            for key in ("implementation_version", "determinism_or_seed_policy", "memoizable_flag"):
                if key not in entry:
                    aliases = {
                        "determinism_or_seed_policy": ("determinism_seed_policy", "determinism_policy"),
                        "memoizable_flag": ("memoizable",),
                        "implementation_version": ("version",),
                    }[key]
                    if not any(alias in entry for alias in aliases):
                        raise InvariantError("IMPLEMENTATION_SHAPE", f"{reference}: missing {key}")
        if inventory_class == "QUANTUM_CALLABLE_FAMILY":
            quantum = record["definition"].get("quantum", {})
            ceiling = str(quantum.get("maturity_ceiling", "")) if isinstance(quantum, Mapping) else ""
            if ceiling not in ALLOWED_QUANTUM_CEILINGS:
                raise InvariantError("QUANTUM_MATURITY_CEILING", f"{record['canonical_component_id']}: {ceiling!r}")
            for binding in record.get("bindings", []):
                if binding.get("readiness", {}).get("authorization") not in {"NOT_ELIGIBLE", "ELIGIBLE"}:
                    raise InvariantError("QUANTUM_AUTHORITY_CLAIM", str(record["canonical_component_id"]))
    if dict(counts) != EXPECTED_IMPLEMENTATIONS:
        raise InvariantError("IMPLEMENTATION_INVENTORY_COUNT", f"observed={dict(counts)}, expected={EXPECTED_IMPLEMENTATIONS}")
    if len(implementation_records) != sum(EXPECTED_IMPLEMENTATIONS.values()):
        raise InvariantError("IMPLEMENTATION_INVENTORY_COUNT", f"records={len(implementation_records)}")
    result = dict(counts)
    result["SOURCE_INVENTORY_NONRUNTIME"] = source_inventory_versions
    return result, implementation_records


def _policy_entries(policy: Any) -> Iterator[tuple[str, Mapping[str, Any]]]:
    if isinstance(policy, Mapping):
        if isinstance(policy.get("agent_id"), str):
            yield str(policy["agent_id"]), policy
            return
        for key, value in policy.items():
            if isinstance(value, Mapping):
                # Unknown principals must survive enumeration so the exact
                # expected-set comparison can reject them.
                yield str(key), value
            else:
                yield str(key), {"__invalid_policy_entry__": value}
    elif isinstance(policy, list):
        for entry in policy:
            yield from _policy_entries(entry)


def _validate_agent_policies(records: Sequence[Mapping[str, Any]]) -> int:
    policies: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        for binding in record.get("bindings", []):
            for agent_id, policy in _policy_entries(binding.get("agent_access_policy")):
                policies[agent_id].append(policy)
    observed = set(policies)
    if observed != EXPECTED_AGENTS:
        raise InvariantError("PR165_D2_AGENT_SET", f"missing={sorted(EXPECTED_AGENTS-observed)}, extra={sorted(observed-EXPECTED_AGENTS)}")
    expected_compute = {
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
    }
    operation_union: dict[str, set[str]] = defaultdict(set)
    for agent_id, entries in policies.items():
        allowed_operations = EXPECTED_AGENT_OPERATION_CEILINGS[agent_id]
        for entry in entries:
            if "__invalid_policy_entry__" in entry:
                raise InvariantError("AGENT_POLICY_SHAPE", agent_id)
            operations = entry.get("control_plane_operations") or entry.get("allowed_operations") or []
            if not isinstance(operations, list):
                raise InvariantError("AGENT_POLICY_SHAPE", agent_id)
            operation_set = {str(value) for value in operations}
            if not operation_set <= allowed_operations:
                raise InvariantError("AGENT_ACCESS_ESCALATION", f"{agent_id}: {sorted(operation_set)}")
            if operation_set & FORBIDDEN_AGENT_OPERATIONS:
                raise InvariantError("AGENT_ACCESS_ESCALATION", agent_id)
            if not {"status", "explain"} <= operation_set:
                raise InvariantError("AGENT_POLICY_INCOMPLETE", agent_id)
            if "compute" in operation_set and "resolve" not in operation_set:
                raise InvariantError("AGENT_POLICY_INCOMPLETE", f"{agent_id}: compute without resolve")
            mode_ceiling = str(entry.get("mode_ceiling", "STATIC_VALIDATION"))
            mode_rank = EXPECTED_AGENT_MODE_RANK.get(mode_ceiling)
            if (
                mode_rank is None
                or mode_rank
                > EXPECTED_AGENT_MODE_RANK[EXPECTED_AGENT_MAX_MODE]
            ):
                raise InvariantError(
                    "AGENT_ACCESS_ESCALATION",
                    f"{agent_id}.mode_ceiling={mode_ceiling}",
                )
            if entry.get("order_release_authority") is not False:
                raise InvariantError(
                    "AGENT_ACCESS_ESCALATION",
                    f"{agent_id}.order_release_authority",
                )
            if entry.get("source_truth_authority") is not False:
                raise InvariantError(
                    "AGENT_ACCESS_ESCALATION",
                    f"{agent_id}.source_truth_authority",
                )
            operation_union[agent_id].update(operation_set)
            for path, value in _walk(entry):
                key = path[-1].lower() if path else ""
                if any(token in key for token in ("live", "order", "private", "qpu", "activate", "authorize")) and value not in (
                    False,
                    None,
                    0,
                    "NONE",
                    "NOT_ALLOWED",
                    "FORBIDDEN",
                    "NONLIVE_ONLY",
                    "HANDOFF_ONLY",
                ):
                    raise InvariantError("AGENT_ACCESS_ESCALATION", f"{agent_id}.{'.'.join(path)}={value!r}")
    for agent_id in expected_compute:
        if not {"resolve", "compute"} <= operation_union[agent_id]:
            raise InvariantError("AGENT_POLICY_INCOMPLETE", f"{agent_id}: no eligible compute binding")
    return len(observed)


def _validate_authority_absence(records: Sequence[Mapping[str, Any]]) -> None:
    protected_terms = ("qpu", "replay", "paper", "shadow", "live", "order_release", "private_state")
    positive_keys = ("executed", "execution_created", "call_count", "claim_created", "authority_created", "authorized")
    for record in records:
        component_id = str(record["canonical_component_id"])
        for path, value in _walk(record):
            key = path[-1].lower() if path else ""
            if any(term in key for term in protected_terms) and any(token in key for token in positive_keys):
                if value not in (False, None, 0, "0", "NONE", "NOT_EXECUTED", "NOT_AUTHORIZED", "FORBIDDEN"):
                    raise InvariantError("FORBIDDEN_AUTHORITY_CLAIM", f"{component_id}.{'.'.join(path)}={value!r}")


def _fixture_catalog(control_module: Any) -> Any:
    for name in (
        "_IMPLEMENTATION_FIXTURES",
        "IMPLEMENTATION_FIXTURES",
        "_VALIDATION_FIXTURES",
        "_fixture_catalog",
    ):
        value = getattr(control_module, name, None)
        if isinstance(value, Mapping):
            return value
        if callable(value):
            try:
                result = value()
            except TypeError:
                continue
            if isinstance(result, Mapping):
                return result
    return {}


def _source_fixture_catalog() -> dict[str, dict[str, Any]]:
    """Reconstruct bounded fixtures from fixed, reviewed PR162D source modules."""

    base = "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations"
    modules = {
        "formula": importlib.import_module(f"{base}.formula_seed_library"),
        "algorithm": importlib.import_module(f"{base}.algorithm_seed_library"),
        "quantum": importlib.import_module(f"{base}.quantum_seed_library"),
    }
    result: dict[str, dict[str, Any]] = {}
    closed_decimal_fixtures: dict[str, dict[str, Any]] = {
        "IMPLIED_PROBABILITY": {"price": "0.43", "payout": "1"},
        # The source edge vector fixes implied_probability=0.52.  The facade
        # fixture derives it through the canonical implied-probability node.
        "PROBABILITY_EDGE": {
            "p_model": {
                "value": "0.58",
                "unit": "probability",
                "lineage": "PR162D_R2A_TV_FORMULA::PROBABILITY_EDGE.inputs.p_model",
            },
            "price": {
                "value": "0.52",
                "unit": "price",
                "lineage": (
                    "PR162D_R2A_TV_FORMULA::PROBABILITY_EDGE.inputs."
                    "implied_probability; EXACT_INVERSE_FIXTURE_DERIVATION: "
                    "price=implied_probability*payout"
                ),
            },
            "payout": {
                "value": "1",
                "unit": "price",
                "lineage": "PR162D_R2A_TV_FORMULA::IMPLIED_PROBABILITY.inputs.payout",
            },
        },
        "MID_PRICE": {"best_bid": "0.42", "best_ask": "0.46"},
        "SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
        "RELATIVE_SPREAD": {"best_bid": "0.42", "best_ask": "0.46"},
    }
    for spec in modules["formula"].formula_specs():
        fixture = {
            "inputs": copy.deepcopy(closed_decimal_fixtures.get(spec.formula_id, spec.test_inputs)),
            "context": {},
        }
        result[f"QTT.COMP.FORMULA.{spec.formula_id}"] = fixture
        result[str(spec.callable_ref)] = fixture
    for spec in modules["algorithm"].algorithm_specs():
        fixture = {"inputs": copy.deepcopy(spec.test_inputs), "context": {}}
        result[f"QTT.COMP.ALGORITHM.{spec.algorithm_id}"] = fixture
        result[str(spec.callable_ref)] = fixture
    quantum_groups: dict[str, list[Any]] = defaultdict(list)
    for spec in modules["quantum"].quantum_specs():
        quantum_groups[str(spec.callable_ref)].append(spec)
    for reference, specs in quantum_groups.items():
        representative = sorted(specs, key=lambda value: value.quantum_formulation_id)[0]
        family = representative.build_shape.__name__.removeprefix("build_").upper()
        fixture = {"inputs": copy.deepcopy(representative.test_inputs), "context": {}}
        result[f"QTT.COMP.QUANTUM.{family}"] = fixture
        result[reference] = fixture
    return result


def _fixture_for(record: Mapping[str, Any], catalog: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    component_id = str(record["canonical_component_id"])
    references = [_implementation_ref(entry) for entry in record["definition"]["implementation_versions"]]
    candidate: Any = catalog.get(component_id)
    if candidate is None:
        for reference in references:
            if reference in catalog:
                candidate = catalog[reference]
                break
    if isinstance(candidate, list):
        candidate = candidate[0] if candidate else None
    if isinstance(candidate, Mapping):
        inputs = candidate.get("inputs", candidate.get("fixture_inputs", {}))
        context = candidate.get("context", {})
        if isinstance(inputs, Mapping) and isinstance(context, Mapping):
            return dict(inputs), dict(context)
    raise InvariantError("IMPLEMENTATION_FIXTURE_MISSING", component_id)


def _schema_specs(schema: Any) -> dict[str, Mapping[str, Any]]:
    if isinstance(schema, Mapping):
        return {
            str(name): spec if isinstance(spec, Mapping) else {"type": spec}
            for name, spec in schema.items()
        }
    if isinstance(schema, list):
        result: dict[str, Mapping[str, Any]] = {}
        for entry in schema:
            if not isinstance(entry, Mapping):
                continue
            name = entry.get("name") or entry.get("field") or entry.get("input_name")
            if name:
                result[str(name)] = entry
        return result
    return {}


def _typed_fixture_inputs(record: Mapping[str, Any], inputs: Mapping[str, Any]) -> dict[str, Any]:
    specs = _schema_specs(record["definition"].get("input_schema", {}))
    typed: dict[str, Any] = {}
    for name, value in inputs.items():
        spec = specs.get(str(name), {})
        declared_type = str(spec.get("type", "")).upper()
        safe_source_value = copy.deepcopy(value)
        if (
            isinstance(value, str)
            and any(
                token in declared_type
                for token in ("NUMBER", "NUMERIC", "DECIMAL", "FLOAT", "PROBABILITY")
            )
        ):
            try:
                numeric_value = Decimal(value)
            except InvalidOperation:
                numeric_value = None
            if numeric_value is not None and numeric_value.is_finite():
                safe_source_value = numeric_value
        unit = str(
            spec.get("unit")
            or spec.get("units")
            or spec.get("basis")
            or spec.get("unit_or_basis")
            or ""
        )
        if (
            isinstance(value, Mapping)
            and "value" in value
            and str(value.get("unit", "")) == unit
        ):
            typed[str(name)] = copy.deepcopy(dict(value))
            continue
        unresolved_unit = (
            not unit
            or unit in {"ANY", "UNSPECIFIED"}
            or any(token in unit for token in ("EXACT_", "SOURCE_DECLARED", "REQUIRED"))
        )
        if unresolved_unit:
            typed[str(name)] = safe_source_value
            continue
        boundary_tokens = {token for token in re.split(r"[^A-Z0-9]+", unit.upper()) if token}
        safe_value = safe_source_value
        if boundary_tokens & {"MONEY", "CURRENCY", "CASH", "PRICE", "FEE", "USD", "CENTS"}:
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                safe_value = format(Decimal(str(value)), "f")
        typed[str(name)] = {
            "value": safe_value,
            "unit": unit,
            "lineage": "PR162D_FIXED_SOURCE_TEST_INPUT",
        }
    return typed


def _closed_fixture_inputs(
    record: Mapping[str, Any],
    records_by_id: Mapping[str, Mapping[str, Any]],
    catalog: Mapping[str, Any],
    stack: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    component_id = str(record["canonical_component_id"])
    if component_id in stack:
        raise InvariantError("FIXTURE_REQUIREMENT_CYCLE", " -> ".join((*stack, component_id)))
    inputs, context = _fixture_for(record, catalog)
    merged = dict(inputs)
    for requirement in record["definition"].get("requirements", []):
        if requirement.get("required_or_optional") == "OPTIONAL":
            continue
        target_id = _requirement_target(requirement)
        producer = records_by_id.get(target_id)
        if producer is None:
            raise InvariantError("FIXTURE_REQUIREMENT_MISSING", f"{component_id} -> {target_id}")
        producer_input_names = {
            str(entry.get("name", ""))
            for entry in producer.get("definition", {}).get("input_schema", ())
            if isinstance(entry, Mapping) and entry.get("name")
        }
        if producer_input_names and producer_input_names.issubset(merged):
            producer_inputs = _typed_fixture_inputs(
                producer,
                {name: merged[name] for name in sorted(producer_input_names)},
            )
            producer_context = {}
        else:
            producer_inputs, producer_context = _closed_fixture_inputs(
                producer, records_by_id, catalog, (*stack, component_id)
            )
        merged.pop(str(requirement["consumer_input_name"]), None)
        for name, value in producer_inputs.items():
            def normalized_fixture_lock(candidate: Any) -> Any:
                if (
                    isinstance(candidate, Mapping)
                    and "value" in candidate
                    and any(
                        key in candidate
                        for key in ("unit", "lineage", "as_of", "source")
                    )
                ):
                    candidate = candidate["value"]
                if isinstance(candidate, str):
                    try:
                        numeric = Decimal(candidate)
                    except InvalidOperation:
                        return _canonical_json(candidate)
                    if numeric.is_finite():
                        return ("FINITE_DECIMAL", numeric.normalize())
                if isinstance(candidate, (int, float, Decimal)) and not isinstance(
                    candidate, bool
                ):
                    try:
                        numeric = Decimal(str(candidate))
                    except InvalidOperation:
                        return _canonical_json(candidate)
                    if numeric.is_finite():
                        return ("FINITE_DECIMAL", numeric.normalize())
                return _canonical_json(candidate)

            if (
                name in merged
                and normalized_fixture_lock(merged[name])
                != normalized_fixture_lock(value)
            ):
                raise InvariantError("FIXTURE_INPUT_CONFLICT", f"{component_id}.{name}")
            merged[name] = value
        for name, value in producer_context.items():
            context.setdefault(name, value)
    return _typed_fixture_inputs(record, merged), context


def _assert_finite(value: Any, label: str) -> None:
    plain = _plain(value)
    for path, item in _walk(plain):
        if isinstance(item, bool):
            continue
        if isinstance(item, (int, float, Decimal)):
            numeric = float(item)
            if not math.isfinite(numeric):
                raise InvariantError("NONFINITE_COMPUTE_OUTPUT", f"{label}.{'.'.join(path)}")
    text = _canonical_json(value).lower()
    if any(token in text for token in ('"error":true', '"status":"error"', '"status":"failed"')):
        raise InvariantError("FIXTURE_COMPUTE_ERROR", label)
    output = plain
    if isinstance(plain, Mapping):
        output = plain.get("output_values", plain.get("outputs", plain.get("result", plain)))
    if output in (None, {}, []):
        raise InvariantError("FIXTURE_OUTPUT_EMPTY", label)


def _independent_closed_decimal_oracle(
    component_id: str, receipt: Any
) -> bool:
    """Check the five closed arithmetic formulas from independent Decimal math."""

    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        bid = Decimal("0.42")
        ask = Decimal("0.46")
        implied_price = Decimal("0.43")
        edge_implied_price = Decimal("0.52")
        payout = Decimal("1")
        model_probability = Decimal("0.58")
        spread = ask - bid
        midpoint = (bid + ask) / Decimal("2")
        expected: dict[str, tuple[str, Decimal]] = {
            "QTT.COMP.FORMULA.IMPLIED_PROBABILITY": (
                "implied_probability",
                min(max(implied_price / payout, Decimal("0")), Decimal("1")),
            ),
            "QTT.COMP.FORMULA.PROBABILITY_EDGE": (
                "probability_edge",
                model_probability - (edge_implied_price / payout),
            ),
            "QTT.COMP.FORMULA.MID_PRICE": ("mid_price", midpoint),
            "QTT.COMP.FORMULA.SPREAD": ("spread", spread),
            "QTT.COMP.FORMULA.RELATIVE_SPREAD": (
                "relative_spread",
                spread / midpoint,
            ),
        }
    oracle = expected.get(component_id)
    if oracle is None:
        return False
    output_name, expected_value = oracle
    plain = _plain(receipt)
    if not isinstance(plain, Mapping):
        raise InvariantError("CLOSED_DECIMAL_ORACLE_RECEIPT", component_id)
    outputs = plain.get("outputs", plain.get("output_values"))
    if not isinstance(outputs, Mapping) or output_name not in outputs:
        raise InvariantError(
            "CLOSED_DECIMAL_ORACLE_OUTPUT",
            f"{component_id}: missing {output_name}",
        )
    raw_observed = outputs[output_name]
    if isinstance(raw_observed, Mapping) and "value" in raw_observed:
        raw_observed = raw_observed["value"]
    try:
        observed = Decimal(str(raw_observed))
    except (InvalidOperation, ValueError) as exc:
        raise InvariantError(
            "CLOSED_DECIMAL_ORACLE_OUTPUT",
            f"{component_id}: {raw_observed!r}",
        ) from exc
    if not observed.is_finite():
        raise InvariantError(
            "CLOSED_DECIMAL_ORACLE_OUTPUT", f"{component_id}: non-finite"
        )
    # The selected CONTROL1 implementations pin 34 significant Decimal digits
    # with ROUND_HALF_EVEN and no additional output quantization.  A tolerance
    # would weaken that contract and could hide an ambient-context regression.
    if observed != expected_value:
        raise InvariantError(
            "CLOSED_DECIMAL_ORACLE_MISMATCH",
            f"{component_id}.{output_name}: observed={observed} expected={expected_value}",
        )
    return True


def _validate_closed_decimal_native_contract(control_module: Any) -> dict[str, Any]:
    """Independently pin Decimal context, boundary, and rejection semantics."""

    allowlist = getattr(control_module, "NATIVE_IMPLEMENTATIONS", {})
    required = {
        "implied": "qtt.computation_control.native:decimal_implied_probability",
        "edge": "qtt.computation_control.native:decimal_probability_edge",
        "mid": "qtt.computation_control.native:decimal_mid_price",
        "spread": "qtt.computation_control.native:decimal_spread",
        "relative": "qtt.computation_control.native:decimal_relative_spread",
    }
    implementations: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
    for name, reference in required.items():
        implementation = allowlist.get(reference) if isinstance(allowlist, Mapping) else None
        if not callable(implementation):
            raise InvariantError("CLOSED_DECIMAL_IMPLEMENTATION_MISSING", reference)
        implementations[name] = implementation

    with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
        expected_third = Decimal("1") / Decimal("3")
        expected_long_mid = (
            Decimal("0.1234567890123456789012345678901234")
            + Decimal("0.9876543210987654321098765432109876")
        ) / Decimal("2")
    for ambient_precision in (6, 28, 60):
        with localcontext(Context(prec=ambient_precision, rounding=ROUND_HALF_EVEN)):
            implied = implementations["implied"](
                {"price": Decimal("1"), "payout": Decimal("3")}
            )["implied_probability"]
            relative = implementations["relative"](
                {"spread": Decimal("1"), "mid_price": Decimal("3")}
            )["relative_spread"]
            midpoint = implementations["mid"](
                {
                    "best_bid": Decimal("0.1234567890123456789012345678901234"),
                    "best_ask": Decimal("0.9876543210987654321098765432109876"),
                }
            )["mid_price"]
        if implied != expected_third or relative != expected_third:
            raise InvariantError(
                "CLOSED_DECIMAL_AMBIENT_CONTEXT_LEAK",
                f"precision={ambient_precision}: implied={implied} relative={relative}",
            )
        if midpoint != expected_long_mid:
            raise InvariantError(
                "CLOSED_DECIMAL_PRECISION_MISMATCH",
                f"precision={ambient_precision}: {midpoint} != {expected_long_mid}",
            )

    boundary = implementations["implied"](
        {"price": Decimal("1e-9"), "payout": Decimal("1e-9")}
    )["implied_probability"]
    if boundary != Decimal("1"):
        raise InvariantError("CLOSED_DECIMAL_EPSILON_BOUNDARY", str(boundary))

    def expect_failure(
        name: str, inputs: dict[str, Any], expected_code: str
    ) -> None:
        try:
            implementations[name](inputs)
        except Exception as exc:  # the exact typed error code is asserted below
            if expected_code not in str(exc):
                raise InvariantError(
                    "CLOSED_DECIMAL_WRONG_FAILURE",
                    f"{name}: expected={expected_code}: {type(exc).__name__}: {exc}",
                ) from exc
            return
        raise InvariantError(
            "CLOSED_DECIMAL_MISSING_FAILURE", f"{name}: {expected_code}"
        )

    expect_failure(
        "implied",
        {"price": Decimal("1e-10"), "payout": Decimal("1e-10")},
        "INVALID_DOMAIN",
    )
    for invalid in (True, 0.5):
        expect_failure(
            "implied", {"price": invalid, "payout": Decimal("1")},
            "BINARY_FLOAT_MONEY_BOUNDARY",
        )
    for invalid in ("NaN", "Infinity", "-Infinity"):
        expect_failure(
            "implied", {"price": invalid, "payout": Decimal("1")},
            "NONFINITE_INPUT",
        )

    return {
        "arithmetic_precision_significant_digits": 34,
        "rounding": "ROUND_HALF_EVEN",
        "ambient_context_precisions_tested": [6, 28, 60],
        "minimum_ratio_denominator": "1e-9",
        "exact_comparison": True,
        "binary_float_and_boolean_rejection": True,
        "nonfinite_rejection": True,
    }


def _invoke_implementation_fixtures(
    facade: Any,
    control_module: Any,
    records: Sequence[Mapping[str, Any]],
    deadline: Deadline,
) -> tuple[int, int, int, list[tuple[Mapping[str, Any], Any, Any]]]:
    """Disposition every runtime implementation and execute only closed contracts.

    The five independently closed arithmetic records execute through the public
    facade.  Every other implementation remains inventory-only: this validator
    independently proves its registration, exact blocker, non-ready state, and
    status/explain-only policy without invoking ``resolve`` or ``compute``.  In
    particular, an intentionally mode-less incomplete binding is not a validator
    error merely because resolving it correctly fails with ``MISSING_CONTEXT_BINDING``.
    Source-produced fixture vectors are therefore never relabelled as independent
    oracles, and their implementations are never executed to make a coverage count
    green.
    """
    catalog = _source_fixture_catalog()
    catalog.update(_fixture_catalog(control_module))
    facade_cases = getattr(facade, "_implementation_fixture_cases", None)
    if callable(facade_cases):
        for case in facade_cases():
            plain_case = _plain(case)
            if not isinstance(plain_case, Mapping):
                continue
            component_id = str(plain_case.get("canonical_component_id", ""))
            reference = str(plain_case.get("callable_or_solver_ref", ""))
            fixture = {
                "inputs": plain_case.get("inputs", {}),
                "context": plain_case.get("context", {}),
            }
            if component_id:
                catalog.setdefault(component_id, fixture)
            if reference:
                catalog.setdefault(reference, fixture)
    facade_allowlist = getattr(facade, "_implementation_allowlist", None)
    if not isinstance(facade_allowlist, Mapping):
        raise InvariantError(
            "FACADE_ALLOWLIST_UNAVAILABLE",
            "registered fixture dispatch cannot be reconstructed",
        )
    invoked: list[tuple[Mapping[str, Any], Any, Any]] = []
    inventory_disposition_count = 0
    status_explain_only_count = 0
    independent_closed_decimal_oracle_count = 0
    records_by_id = {str(record["canonical_component_id"]): record for record in records}
    for record in records:
        for requirement in record["definition"].get("requirements", []):
            target = _requirement_target(requirement)
            if target not in records_by_id:
                # Requirement producers may be implementation records outside a
                # caller-provided subset; recover them from the facade snapshot.
                snapshot = getattr(getattr(facade, "_registry", None), "pin", lambda: None)()
                if snapshot is not None:
                    for candidate in snapshot.records:
                        records_by_id.setdefault(str(candidate["canonical_component_id"]), candidate)
                break
    for index, record in enumerate(records):
        if index % 10 == 0:
            deadline.check("implementation_fixtures")

        component_id = str(record["canonical_component_id"])
        implementations = record["definition"].get("implementation_versions", ())
        if not implementations:
            raise InvariantError("IMPLEMENTATION_INVENTORY_EMPTY", component_id)
        for entry in implementations:
            if not isinstance(entry, Mapping):
                raise InvariantError("IMPLEMENTATION_SHAPE", component_id)
            reference = _implementation_ref(entry)
            if not callable(facade_allowlist.get(reference)):
                raise InvariantError(
                    "REGISTERED_IMPLEMENTATION_NOT_ALLOWLISTED",
                    f"{component_id}: {reference}",
                )

        bindings = record.get("bindings", ())
        if not isinstance(bindings, list) or not bindings:
            raise InvariantError("RUNTIME_IMPLEMENTATION_BINDING_MISSING", component_id)
        ready_bindings: list[Mapping[str, Any]] = []
        for binding in bindings:
            if not isinstance(binding, Mapping):
                raise InvariantError("RUNTIME_IMPLEMENTATION_BINDING_SHAPE", component_id)
            selected_version = str(binding.get("selected_implementation_version", ""))
            if not any(
                str(entry.get("implementation_version", "")) == selected_version
                for entry in implementations
            ):
                raise InvariantError(
                    "SELECTED_IMPLEMENTATION_MISSING",
                    f"{component_id}@{selected_version}",
                )
            readiness = binding.get("readiness", {})
            specification_issues = _independent_specification_issues(
                record.get("definition", {})
            )
            input_binding_issues = _independent_input_source_binding_issues(
                record.get("definition", {}), binding
            )
            computation_ready = (
                record.get("record_state") == "CANONICAL_ACCEPTED"
                and not specification_issues
                and not input_binding_issues
                and all(
                    readiness.get(dimension) == "PASS"
                    for dimension in (
                        "specification",
                        "implementation",
                        "inputs",
                        "requirements",
                        "oracle",
                        "context",
                    )
                )
            )
            if computation_ready:
                ready_bindings.append(binding)
                continue

            exact_action = str(
                binding.get("exact_resolution_action_or_null") or ""
            )
            operations = _independent_policy_operations(
                binding.get("agent_access_policy")
            )
            if operations != {"status", "explain"}:
                raise InvariantError(
                    "INCOMPLETE_IMPLEMENTATION_OPERATION_ELIGIBILITY",
                    f"{component_id}: {sorted(operations)}",
                )
            if (
                not exact_action
                or exact_action.upper() in PLACEHOLDERS
                or binding.get("derived_state")
                in {"CONTEXT_READY", "STACK_READY", "EVIDENCED", "AUTHORIZED"}
            ):
                raise InvariantError(
                    "INCOMPLETE_IMPLEMENTATION_FALSE_READINESS",
                    f"{component_id}: {binding.get('binding_id')}",
                )

        if not ready_bindings:
            inventory_disposition_count += 1
            status_explain_only_count += 1
            continue
        if len(ready_bindings) != 1 or len(ready_bindings) != len(bindings):
            raise InvariantError(
                "IMPLEMENTATION_READY_BINDING_AMBIGUITY",
                f"{component_id}: {len(ready_bindings)}/{len(bindings)}",
            )

        binding = ready_bindings[0]
        inputs, supplied_context = _closed_fixture_inputs(
            record, records_by_id, catalog
        )
        context = _binding_context(binding)
        context.update(supplied_context)
        plan = _operation(facade, "resolve", record["canonical_component_id"], context=context)
        receipt = _operation(
            facade,
            "compute",
            record["canonical_component_id"],
            inputs=inputs,
            context=context,
        )
        _assert_finite(receipt, str(record["canonical_component_id"]))
        if _independent_closed_decimal_oracle(
            str(record["canonical_component_id"]), receipt
        ):
            independent_closed_decimal_oracle_count += 1
        inventory_disposition_count += 1
        invoked.append((record, plan, receipt))
    if inventory_disposition_count != len(records):
        raise InvariantError(
            "REGISTERED_IMPLEMENTATION_DISPOSITION_COVERAGE",
            f"{inventory_disposition_count}/{len(records)}",
        )
    expected_ready_components = _CLOSED_FIXTURE_COMPONENTS.intersection(
        records_by_id
    )
    observed_ready_components = {
        str(record["canonical_component_id"]) for record, _plan, _receipt in invoked
    }
    if observed_ready_components != expected_ready_components:
        raise InvariantError(
            "VERIFIED_FACADE_FIXTURE_COVERAGE",
            f"observed={sorted(observed_ready_components)!r}, "
            f"expected={sorted(expected_ready_components)!r}",
        )
    if independent_closed_decimal_oracle_count != len(expected_ready_components):
        raise InvariantError(
            "CLOSED_DECIMAL_ORACLE_COVERAGE",
            f"{independent_closed_decimal_oracle_count}/"
            f"{len(expected_ready_components)}",
        )
    return (
        inventory_disposition_count,
        len(invoked),
        status_explain_only_count,
        invoked,
    )


def _diagnostic_mapping(facade: Any) -> Mapping[str, Any]:
    merged: dict[str, Any] = {}
    for name in ("_diagnostics", "_counters", "_metrics", "_debug_counters", "_instrumentation"):
        value = getattr(facade, name, None)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        plain = _plain(value)
        if isinstance(plain, Mapping):
            merged.update(plain)
    snapshot = getattr(facade, "_snapshot", None)
    if snapshot is not None:
        plain = _plain(snapshot)
        if isinstance(plain, Mapping):
            for key in ("diagnostics", "counters", "metrics"):
                if isinstance(plain.get(key), Mapping):
                    merged.update(plain[key])
    return merged


def _counter(mapping: Mapping[str, Any], names: Iterable[str]) -> int | None:
    lowered = {str(key).lower(): value for key, value in mapping.items()}
    for name in names:
        if name.lower() in lowered:
            try:
                return int(lowered[name.lower()])
            except (TypeError, ValueError):
                return None
    return None


def _validate_runtime_counters(facade: Any) -> tuple[int, int, int]:
    diagnostics = _diagnostic_mapping(facade)
    reads = _counter(
        diagnostics,
        (
            "runtime_registry_file_reads_after_initialization",
            "registry_file_reads_after_initialization",
            "post_init_registry_file_reads",
            "runtime_registry_file_reads",
        ),
    )
    scans = _counter(
        diagnostics,
        ("per_request_full_registry_iterations", "full_registry_scans", "runtime_full_registry_scans"),
    )
    unrelated = _counter(
        diagnostics,
        ("unrelated_component_executions", "unrelated_computation_executions"),
    )
    if reads is None or scans is None or unrelated is None:
        raise InvariantError("RUNTIME_COUNTERS_MISSING", f"keys={sorted(diagnostics)[:50]}")
    if reads or scans or unrelated:
        raise InvariantError("RUNTIME_COMPLEXITY_VIOLATION", f"reads={reads}, scans={scans}, unrelated={unrelated}")
    return reads, scans, unrelated


def _closure(graph: Mapping[str, set[str]], root: str) -> set[str]:
    result: set[str] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in result:
            continue
        result.add(node)
        stack.extend(graph.get(node, ()))
    return result


def _plan_component_ids(plan: Any) -> list[str]:
    plain = _plain(plan)
    values: list[str] = []
    for path, value in _walk(plain):
        key = path[-1].lower() if path else ""
        if key in {"canonical_component_id", "component_id"} and isinstance(value, str):
            values.append(value)
        elif key in {"topological_execution_order", "execution_order", "component_ids"} and isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, str))
    return list(dict.fromkeys(values))


def _validate_selected_subgraph(
    invoked: Sequence[tuple[Mapping[str, Any], Any, Any]], graph: Mapping[str, set[str]], registry_size: int
) -> tuple[int, int]:
    candidates = [item for item in invoked if graph.get(str(item[0]["canonical_component_id"]))]
    if not candidates:
        raise InvariantError("CLOSED_STACK_FIXTURE_MISSING", "no implementation fixture has requirements")
    record, plan, receipt = max(candidates, key=lambda item: len(_closure(graph, str(item[0]["canonical_component_id"]))))
    root = str(record["canonical_component_id"])
    expected = _closure(graph, root)
    observed = set(_plan_component_ids(plan))
    if not expected <= observed or observed - expected:
        raise InvariantError("SELECTED_SUBGRAPH_MISMATCH", f"expected={sorted(expected)}, observed={sorted(observed)}")
    if len(observed) >= registry_size:
        raise InvariantError("FULL_REGISTRY_EXECUTION", f"selected={len(observed)}, registry={registry_size}")
    receipt_text = _canonical_json(receipt)
    for component_id in expected:
        if component_id not in receipt_text:
            raise InvariantError("RECEIPT_GRAPH_INCOMPLETE", component_id)
    return len(observed), sum(len(graph[node]) for node in expected)


def _runtime_error_code(function: Callable[[], Any]) -> str:
    try:
        function()
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code:
            return str(code)
        text = str(exc)
        return text.split(":", 1)[0]
    raise InvariantError("RUNTIME_DEFECT_NOT_REJECTED", "operation returned normally")


def _common_subgraph_probe(facade_class: type[Any], template: Mapping[str, Any]) -> dict[str, Any]:
    counters: Counter[str] = Counter()

    def implementation(name: str, output_name: str, input_names: Sequence[str]) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def run(inputs: dict[str, Any]) -> dict[str, Any]:
            counters[name] += 1
            values = [Decimal(str(inputs[input_name])) for input_name in input_names]
            if name == "shared":
                result = values[0]
            elif name == "left":
                result = values[0] + Decimal("1")
            elif name == "right":
                result = values[0] + Decimal("2")
            elif name == "root":
                result = sum(values, Decimal("0"))
            else:
                result = Decimal("999")
            return {output_name: result}

        return run

    refs = {
        "shared": "qtt.computation_control.validation:shared",
        "left": "qtt.computation_control.validation:left",
        "right": "qtt.computation_control.validation:right",
        "root": "qtt.computation_control.validation:root",
        "unrelated": "qtt.computation_control.validation:unrelated",
        "fallback_primary": "qtt.computation_control.validation:fallback_primary",
        "fallback_alternative": "qtt.computation_control.validation:fallback_alternative",
        "fallback_root": "qtt.computation_control.validation:fallback_root",
    }

    def failing_primary(inputs: dict[str, Any]) -> dict[str, Any]:
        del inputs
        counters["fallback_primary"] += 1
        raise RuntimeError("VALIDATOR_INJECTED_PRIMARY_FAILURE")

    def working_fallback(inputs: dict[str, Any]) -> dict[str, Any]:
        counters["fallback_alternative"] += 1
        return {"upstream_value": Decimal(str(inputs["base_value"])) + Decimal("6")}

    def fallback_root(inputs: dict[str, Any]) -> dict[str, Any]:
        counters["fallback_root"] += 1
        return {"result": Decimal(str(inputs["upstream_value"]))}

    allowlist = {
        refs["shared"]: implementation("shared", "shared_value", ("base_value",)),
        refs["left"]: implementation("left", "left_value", ("shared_value",)),
        refs["right"]: implementation("right", "right_value", ("shared_value",)),
        refs["root"]: implementation("root", "result", ("left_value", "right_value")),
        refs["unrelated"]: implementation("unrelated", "unused", ()),
        refs["fallback_primary"]: failing_primary,
        refs["fallback_alternative"]: working_fallback,
        refs["fallback_root"]: fallback_root,
    }

    def requirement(target: str, producer: str, consumer: str) -> dict[str, Any]:
        return {
            "required_component_id_or_source_selector": target,
            "required_semantic_version_constraint": "1.0",
            "requirement_role": f"{target}::{producer}->{consumer}",
            "required_or_optional": "REQUIRED",
            "producer_output_name": producer,
            "consumer_input_name": consumer,
            "unit_or_basis_conversion": "IDENTITY",
            "timing_and_freshness_constraint": "SAME_REQUEST",
            "activation_condition": "ALWAYS",
            "fallback_component_id_or_null": None,
            "failure_behavior": "FAIL_CLOSED",
        }

    def record(
        token: str,
        inputs: Sequence[str],
        output: str,
        requirements: Sequence[Mapping[str, Any]],
        *,
        memoizable: bool = True,
    ) -> dict[str, Any]:
        value = copy.deepcopy(template)
        component_id = f"QTT.COMP.VALIDATION.MEMO.{token.upper()}"
        value["canonical_component_id"] = component_id
        value["semantic_version"] = "1.0"
        value["record_state"] = "CANONICAL_ACCEPTED"
        value["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_MEMOIZATION"]
        definition = value["definition"]
        definition["display_name"] = f"Memoization {token}"
        definition["description"] = "Independent selected-subgraph and invocation-key probe."
        definition["component_kind"] = "DETERMINISTIC_TRANSFORM"
        definition["complete_mathematical_or_procedural_definition"] = f"VALIDATOR::{token}"
        definition["input_schema"] = [
            {"name": name, "type": "decimal", "unit": "DIMENSIONLESS", "required": True}
            for name in inputs
        ]
        if not inputs:
            definition["zero_input_proof"] = (
                "SIDE_EFFECT_FREE_VALIDATOR_CONSTANT_WITH_NO_INPUT_PORTS"
            )
        definition["output_schema"] = [
            {"name": output, "type": "decimal", "unit": "DIMENSIONLESS", "required": True}
        ]
        definition["units_and_bases"] = {
            **{name: "DIMENSIONLESS" for name in inputs},
            output: "DIMENSIONLESS",
        }
        definition["domain_and_boundary_behavior"] = (
            "FINITE_DECIMAL_INPUTS; FAIL_CLOSED_OUTSIDE_THE_DECLARED_TYPED_DOMAIN"
        )
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
            "default_provenance": "NO_CONFIGURABLE_PARAMETERS_IN_VALIDATOR_PROBE",
        }
        definition["classical_fallback"] = {
            "not_applicable": True,
            "proof_ref": "TEST_COMPONENT_FAILS_CLOSED_WITHOUT_ALTERNATE_SEMANTICS",
        }
        definition["risk_materiality"] = {
            "economic_materiality": "NONLIVE_TEMPORARY_VALIDATOR_PROBE_ONLY",
            "complexity": "BOUNDED_SMALL_SYNTHETIC_DAG",
            "data_dependency": "TYPED_TEMPORARY_VALIDATOR_INPUTS_ONLY",
            "latency_sensitivity": "NON_AUTHORITATIVE_MEASUREMENT_ONLY",
            "external_provider_dependency": False,
            "quantum_backend_dependency": False,
            "independent_validation_strength_required": "GROUPED_DEFECT_ORACLE",
            "monitoring_revalidation_cadence": "EVERY_CONTROL1_VALIDATION_RUN",
        }
        definition["requirements"] = [dict(item) for item in requirements]
        definition["implementation_versions"] = [
            {
                "implementation_version": "1.0",
                "callable_or_solver_ref": refs[token],
                "code_owner": "CONTROL1_INDEPENDENT_VALIDATOR",
                "supported_platforms": ["WINDOWS", "LINUX"],
                "pinned_dependencies": ["PYTHON_STDLIB_DECIMAL"],
                "determinism_seed_policy": "DETERMINISTIC_NO_SEED",
                "precision": "DECIMAL",
                "latency_class": "PRETRADE_BOUNDED",
                "security_state": "LOCAL_ALLOWLIST_ONLY",
                "memoizable_flag": memoizable,
                "memoizable_proof_basis": "PURE_SIDE_EFFECT_FREE_VALIDATOR_CLOSURE",
                "fallback": "FAIL_CLOSED",
                "implementation_inventory_class": "FORMULA",
            }
        ]
        definition["oracle_and_test_refs"] = ["tools/validate_pr169_qku_comp_control1.py"]
        definition["equivalence_proof_refs"] = []
        value["uses"] = {
            "decision_roles": ["INTERNAL_SUPPORT"],
            "decision_outputs": [output],
            "market_family_tags": ["VALIDATOR_SYNTHETIC"],
            "qku_role_bindings": [],
            "consumer_class_tags": ["CONTROL1_INDEPENDENT_VALIDATOR"],
        }
        binding = copy.deepcopy(value["bindings"][0])
        binding["binding_id"] = f"BINDING.VALIDATION.MEMO.{token.upper()}"
        binding["market"] = "VALIDATOR_SYNTHETIC"
        binding["venue"] = "LOCAL_FIXTURE"
        binding["context_selector"] = {"context_family": "VALIDATOR_MEMOIZATION"}
        binding["supported_modes"] = ["TEST_VECTOR"]
        binding["mode_state"] = {
            "TEST_VECTOR": {
                "evidence": "FIXTURE",
                "authorization": "NOT_ELIGIBLE",
                "activation_state": "INACTIVE_NONLIVE",
            }
        }
        binding["selected_implementation_version"] = "1.0"
        binding["requirement_context_policy"] = "SAME_FIXTURE_INPUT_LOCK"
        binding["selected_requirement_alternatives"] = []
        requirement_by_input = {
            str(item["consumer_input_name"]): item for item in requirements
        }
        binding["input_source_bindings"] = []
        for name in inputs:
            required = requirement_by_input.get(name)
            if required is None:
                binding["input_source_bindings"].append(
                    {
                        "input_name": name,
                        "source_ref": (
                            "QKUComputationControlPlaneV1.compute.inputs::" + name
                        ),
                        "binding_state": "EXACT_TYPED_REQUEST_INPUT_LOCK",
                        "declared_type": "decimal",
                        "unit_or_basis": "DIMENSIONLESS",
                    }
                )
            else:
                binding["input_source_bindings"].append(
                    {
                        "input_name": name,
                        "source_ref": str(
                            required["required_component_id_or_source_selector"]
                        ),
                        "binding_state": "CANONICAL_REQUIREMENT_OUTPUT",
                        "producer_output_name": str(
                            required["producer_output_name"]
                        ),
                        "declared_type": "decimal",
                        "unit_or_basis": "DIMENSIONLESS",
                    }
                )
        binding["readiness"] = {
            "specification": "PASS",
            "implementation": "PASS",
            "inputs": "PASS",
            "requirements": "PASS",
            "oracle": "PASS",
            "context": "PASS",
            "evidence": "FIXTURE",
            "authorization": "NOT_ELIGIBLE",
        }
        binding["derived_state"] = "STACK_READY"
        binding["exact_resolution_action_or_null"] = None
        binding["evidence_summary"] = {
            "evidence_ceiling": "FIXTURE",
            "empirical_market_evidence": False,
            "limitations": ["VALIDATOR_SYNTHETIC_ONLY"],
        }
        binding["activation_state"] = "INACTIVE_NONLIVE"
        value["bindings"] = [binding]
        value["provenance"] = [
            {
                "source_artifact_ref": "tools/validate_pr169_qku_comp_control1.py",
                "source_row_ref": token,
                "source_local_identity_or_name": token,
                "source_fields_consumed": ["synthetic_probe"],
                "source_relation": "VALIDATION_ONLY",
                "canonical_target_ref": component_id,
                "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            }
        ]
        value["relations"] = []
        return value

    shared_id = "QTT.COMP.VALIDATION.MEMO.SHARED"
    left_id = "QTT.COMP.VALIDATION.MEMO.LEFT"
    right_id = "QTT.COMP.VALIDATION.MEMO.RIGHT"
    records = [
        record("shared", ("base_value",), "shared_value", ()),
        record("left", ("shared_value",), "left_value", (requirement(shared_id, "shared_value", "shared_value"),)),
        record("right", ("shared_value",), "right_value", (requirement(shared_id, "shared_value", "shared_value"),)),
        record(
            "root",
            ("left_value", "right_value"),
            "result",
            (
                requirement(left_id, "left_value", "left_value"),
                requirement(right_id, "right_value", "right_value"),
            ),
        ),
        record("unrelated", (), "unused", ()),
    ]
    trusted_memoizable_refs = {refs["shared"]}
    facade = facade_class(
        records=records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs=trusted_memoizable_refs,
    )
    context = {
        "market": "VALIDATOR_SYNTHETIC",
        "venue": "LOCAL_FIXTURE",
        "context_family": "VALIDATOR_MEMOIZATION",
    }
    typed_one = {"base_value": {"value": "1", "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_INPUT_1"}}
    first = _plain(facade.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_one, context, mode="TEST_VECTOR"))
    if counters != Counter({"shared": 1, "left": 1, "right": 1, "root": 1}):
        raise InvariantError("COMMON_SUBGRAPH_MEMOIZATION", repr(counters))
    if first.get("shared_invocations_reused") != 1 or first.get("nodes_executed") != 4:
        raise InvariantError("COMMON_SUBGRAPH_MEMOIZATION", repr(first))
    if counters["unrelated"]:
        raise InvariantError("UNRELATED_COMPONENT_EXECUTION", repr(counters))

    typed_two = {"base_value": {"value": "2", "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_INPUT_2"}}
    second = _plain(facade.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_two, context, mode="TEST_VECTOR"))
    if counters["shared"] != 2 or first.get("outputs") == second.get("outputs"):
        raise InvariantError("DIFFERENT_INPUT_UNSAFE_REUSE", repr(counters))

    nonmemo_records = copy.deepcopy(records)
    nonmemo_records[0]["definition"]["implementation_versions"][0]["memoizable_flag"] = False
    counters.clear()
    nonmemo = facade_class(
        records=nonmemo_records,
        implementation_allowlist=allowlist,
        trusted_memoizable_refs=trusted_memoizable_refs,
    )
    nonmemo_receipt = _plain(
        nonmemo.compute("QTT.COMP.VALIDATION.MEMO.ROOT", typed_one, context, mode="TEST_VECTOR")
    )
    if counters["shared"] != 2 or nonmemo_receipt.get("shared_invocations_reused") != 0:
        raise InvariantError("NONMEMOIZABLE_NODE_REUSED", repr(counters))

    missing_unit = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {"base_value": "1"},
            context,
            mode="TEST_VECTOR",
        )
    )
    if missing_unit != "MISSING_UNIT":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"missing unit -> {missing_unit}")
    stale = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {
                "base_value": {
                    "value": "1",
                    "unit": "DIMENSIONLESS",
                    "lineage": "VALIDATOR_STALE",
                    "as_of": "2000-01-01T00:00:00Z",
                }
            },
            {
                **context,
                "request_time": "2000-01-01T00:00:10Z",
                "freshness_ttl_seconds": 1,
            },
            mode="TEST_VECTOR",
        )
    )
    if stale != "STALE_INPUT":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"stale input -> {stale}")
    nonfinite = _runtime_error_code(
        lambda: facade.compute(
            "QTT.COMP.VALIDATION.MEMO.ROOT",
            {"base_value": {"value": float("inf"), "unit": "DIMENSIONLESS", "lineage": "VALIDATOR_NONFINITE"}},
            context,
            mode="TEST_VECTOR",
        )
    )
    if nonfinite != "NONFINITE_VALUE":
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"nonfinite input -> {nonfinite}")

    ambiguous_records = copy.deepcopy(records)
    extra_binding = copy.deepcopy(ambiguous_records[-1]["bindings"][0])
    extra_binding["binding_id"] = "BINDING.VALIDATION.MEMO.UNRELATED.ALTERNATE"
    ambiguous_records[-1]["bindings"].append(extra_binding)
    ambiguous_code = _runtime_error_code(
        lambda: facade_class(
            records=ambiguous_records, implementation_allowlist=allowlist
        ).resolve("QTT.COMP.VALIDATION.MEMO.UNRELATED", context)
    )
    if ambiguous_code not in {
        "AMBIGUOUS_CONTEXT_BINDING",
        "OVERLAPPING_BINDING_SELECTORS",
        "AMBIGUOUS_BINDING_SELECTOR",
    }:
        raise InvariantError("RUNTIME_DEFECT_WRONG_REASON", f"ambiguous binding -> {ambiguous_code}")

    overlap_records = copy.deepcopy(records)
    overlap_binding = overlap_records[-1]["bindings"][0]
    overlap_binding["context_selector"] = {
        "context_family": "VALIDATOR_MEMOIZATION",
        "left_wildcard": "ANY",
    }
    alternate_overlap = copy.deepcopy(overlap_binding)
    alternate_overlap["binding_id"] = "BINDING.VALIDATION.MEMO.UNRELATED.OVERLAP"
    alternate_overlap["context_selector"] = {
        "context_family": "VALIDATOR_MEMOIZATION",
        "right_wildcard": "ANY",
    }
    overlap_records[-1]["bindings"].append(alternate_overlap)
    overlap_load_code = _runtime_error_code(
        lambda: facade_class(records=overlap_records, implementation_allowlist=allowlist)
    )
    if overlap_load_code not in {
        "OVERLAPPING_BINDING_SELECTORS",
        "AMBIGUOUS_BINDING_SELECTOR",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"overlapping selector load -> {overlap_load_code}",
        )

    missing_mode_records = copy.deepcopy(records)
    missing_mode_records[-1]["bindings"][0]["mode_state"] = {}
    missing_mode_code = _runtime_error_code(
        lambda: facade_class(
            records=missing_mode_records, implementation_allowlist=allowlist
        )
    )
    if missing_mode_code not in {
        "MODE_STATE_MISSING",
        "MODE_STATE_COVERAGE_MISSING",
        "SUPPORTED_MODE_STATE_MISSING",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"missing mode_state load -> {missing_mode_code}",
        )

    bulky_evidence_records = copy.deepcopy(records)
    bulky_evidence_records[-1]["bindings"][0]["evidence_summary"] = {
        "observations": {
            f"row_{index:05d}": {"value": index} for index in range(5_000)
        }
    }
    bulky_evidence_code = _runtime_error_code(
        lambda: facade_class(
            records=bulky_evidence_records, implementation_allowlist=allowlist
        )
    )
    if bulky_evidence_code not in {
        "EMBEDDED_BULK_EVIDENCE",
        "BULK_EVIDENCE_PAYLOAD",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"generic bulk evidence load -> {bulky_evidence_code}",
        )

    paper_record = copy.deepcopy(records[-1])
    paper_binding = paper_record["bindings"][0]
    paper_binding["supported_modes"] = ["PAPER"]
    paper_binding["mode_state"] = {
        "PAPER": {
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
            "activation_state": "INACTIVE_NONLIVE",
        }
    }
    paper_binding["readiness"]["evidence"] = "NONE"
    paper_binding["readiness"]["authorization"] = "NOT_ELIGIBLE"
    paper_binding["activation_state"] = "INACTIVE_NONLIVE"
    paper_binding["exact_resolution_action_or_null"] = (
        "MISSING_PAPER_AUTHORIZATION: validator synthetic binding"
    )
    paper_facade = facade_class(records=[paper_record], implementation_allowlist=allowlist)
    paper_context = _binding_context(paper_binding)
    paper_status = _plain(
        paper_facade.status(
            paper_record["canonical_component_id"],
            paper_context,
        )
    )
    paper_blockers = {str(value) for value in paper_status.get("blockers", ())}
    if (
        paper_status.get("authorization") != "NOT_ELIGIBLE"
        or paper_status.get("mode_state", {}).get("PAPER", {}).get("authorization")
        != "NOT_ELIGIBLE"
        or paper_status.get("derived_state") == "AUTHORIZED"
        or not any(value.startswith("MODE_NOT_AUTHORIZED: PAPER") for value in paper_blockers)
    ):
        raise InvariantError(
            "NOT_ELIGIBLE_STATUS_UNTRUTHFUL", repr(paper_status)
        )

    primary_id = "QTT.COMP.VALIDATION.MEMO.FALLBACK_PRIMARY"
    fallback_id = "QTT.COMP.VALIDATION.MEMO.FALLBACK_ALTERNATIVE"
    fallback_requirement = requirement(
        primary_id, "upstream_value", "upstream_value"
    )
    fallback_requirement["fallback_component_id_or_null"] = fallback_id
    fallback_requirement["failure_behavior"] = "USE_FALLBACK_FAIL_CLOSED"
    fallback_records = [
        record(
            "fallback_primary",
            ("base_value",),
            "upstream_value",
            (),
            memoizable=False,
        ),
        record(
            "fallback_alternative",
            ("base_value",),
            "upstream_value",
            (),
            memoizable=False,
        ),
        record(
            "fallback_root",
            ("base_value", "upstream_value"),
            "result",
            (fallback_requirement,),
            memoizable=False,
        ),
    ]
    counters.clear()
    fallback_facade = facade_class(
        records=fallback_records, implementation_allowlist=allowlist
    )
    fallback_receipt = _plain(
        fallback_facade.compute(
            "QTT.COMP.VALIDATION.MEMO.FALLBACK_ROOT",
            {
                "base_value": {
                    "value": "1",
                    "unit": "DIMENSIONLESS",
                    "lineage": "VALIDATOR_FALLBACK_INPUT",
                }
            },
            context,
            mode="TEST_VECTOR",
        )
    )
    if (
        fallback_receipt.get("fallback_used") is not True
        or fallback_receipt.get("outputs", {}).get("result") not in {"7", 7, Decimal("7")}
        or counters["fallback_primary"] != 1
        or counters["fallback_alternative"] != 1
        or counters["fallback_root"] != 1
    ):
        raise InvariantError(
            "RUNTIME_REQUIREMENT_FALLBACK",
            f"receipt={fallback_receipt}, counters={dict(counters)}",
        )
    receipt_generation = fallback_receipt.get("generation")
    fallback_generations = {
        entry.get("receipt_generation")
        for entry in fallback_receipt.get("requirement_receipts", ())
        if isinstance(entry, Mapping)
    }
    if not fallback_generations or fallback_generations != {receipt_generation}:
        raise InvariantError(
            "MIXED_FALLBACK_SNAPSHOT_GENERATION",
            f"root={receipt_generation!r}, requirements={sorted(fallback_generations, key=repr)!r}",
        )
    fallback_entries = [
        entry
        for entry in fallback_receipt.get("requirement_receipts", ())
        if isinstance(entry, Mapping)
        and entry.get("component_id") == fallback_id
    ]
    if len(fallback_entries) != 1:
        raise InvariantError(
            "FALLBACK_INPUT_PROJECTION_RECEIPT_MISSING", repr(fallback_receipt)
        )
    return {
        "memoizable_shared_calls": 1,
        "memoizable_reuse_count": 1,
        "different_request_shared_calls": 2,
        "nonmemoizable_shared_calls": 2,
        "unrelated_calls": 0,
        "runtime_defects": {
            "missing_unit": missing_unit,
            "stale": stale,
            "nonfinite": nonfinite,
            "ambiguous_binding": ambiguous_code,
            "overlapping_selector_load": overlap_load_code,
            "missing_mode_state_load": missing_mode_code,
            "bulk_evidence_load": bulky_evidence_code,
            "not_eligible_status": "TRUTHFUL",
            "runtime_requirement_fallback": "PASS",
            "fallback_input_projection": "PASS",
            "fallback_snapshot_generation": receipt_generation,
        },
    }


def _find_function(module: Any, names: Sequence[str]) -> Callable[..., Any] | None:
    for name in names:
        function = getattr(module, name, None)
        if callable(function):
            return function
    return None


def _invoke_records_function(function: Callable[..., Any], records: Sequence[Mapping[str, Any]]) -> Any:
    signature = inspect.signature(function)
    for key in ("records", "registry_records", "rows"):
        if key in signature.parameters:
            return function(**{key: records})
    return function(records)


def _derive_delta(control_module: Any, before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]) -> Any:
    function = _find_function(
        control_module,
        ("_derive_registry_update", "_derive_registry_update_v1", "_build_registry_update", "_diff_registry"),
    )
    if function is None:
        raise InvariantError("DELTA_HELPER_MISSING", "control.py must expose a private mechanism helper")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"before", "base", "old_records", "accepted_records", "base_records"}:
            kwargs[key] = before
        elif key in {"after", "candidate", "new_records", "candidate_records"}:
            kwargs[key] = after
    if len(kwargs) >= 2:
        return function(**kwargs)
    return function(before, after)


def _delta_field(delta: Any, name: str) -> set[str]:
    plain = _plain(delta)
    if not isinstance(plain, Mapping):
        return set()
    value = plain.get(name, [])
    return {str(item) for item in value} if isinstance(value, list) else set()


def _validate_delta(
    control_module: Any,
    records: Sequence[Mapping[str, Any]],
    reverse: Mapping[str, set[str]],
) -> tuple[Any, list[Mapping[str, Any]], str]:
    target_index = next(
        (
            index
            for index, record in enumerate(records)
            if record.get("bindings") and record.get("record_state") == "CANONICAL_ACCEPTED"
        ),
        None,
    )
    if target_index is None:
        raise InvariantError("DELTA_FIXTURE_MISSING", "no accepted bound record")
    candidate = list(records)
    target = copy.deepcopy(records[target_index])
    candidate[target_index] = target
    component_id = str(target["canonical_component_id"])
    binding = target["bindings"][0]
    policy = binding["selected_parameter_policy"]
    if isinstance(policy, Mapping):
        policy = dict(policy)
        policy["validation_probe_revision"] = int(policy.get("validation_probe_revision", 0)) + 1
        binding["selected_parameter_policy"] = policy
    else:
        binding["selected_parameter_policy"] = {"policy_ref": policy, "validation_probe_revision": 1}
    delta = _derive_delta(control_module, records, candidate)
    changed = _delta_field(delta, "changed_component_ids")
    added = _delta_field(delta, "added_component_ids")
    retired = _delta_field(delta, "retired_component_ids")
    changed_bindings = _delta_field(delta, "changed_binding_ids")
    dependents = _delta_field(delta, "affected_dependent_ids")
    expected_dependents: set[str] = set()
    queue = deque(reverse.get(component_id, ()))
    while queue:
        node = queue.popleft()
        if node in expected_dependents:
            continue
        expected_dependents.add(node)
        queue.extend(reverse.get(node, ()))
    if changed != {component_id} or added or retired:
        raise InvariantError("DELTA_EXACTNESS", f"changed={changed}, added={added}, retired={retired}")
    expected_binding_labels = {
        str(binding["binding_id"]),
        f"{component_id}::{binding['binding_id']}",
    }
    if not (changed_bindings & expected_binding_labels) or dependents != expected_dependents:
        raise InvariantError(
            "DELTA_EXACTNESS",
            f"changed_bindings={changed_bindings}, dependents={dependents}, expected={expected_dependents}",
        )
    return delta, candidate, component_id


def _build_indexes(control_module: Any, records: Sequence[Mapping[str, Any]]) -> Any:
    function = _find_function(
        control_module,
        ("_build_registry_snapshot", "_build_snapshot", "_build_index_set", "_build_indexes"),
    )
    if function is None:
        raise InvariantError("INDEX_HELPER_MISSING", "control.py must expose private snapshot/index construction")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "registry_records", "rows"}:
            kwargs[key] = records
        elif key == "generation":
            kwargs[key] = 1
        elif key == "layout":
            kwargs[key] = "IN_MEMORY_VALIDATION"
        elif key in {"shard_count", "registry_file_reads"}:
            kwargs[key] = 0
    return function(**kwargs) if kwargs else function(records)


def _refresh_indexes(
    control_module: Any,
    base: Any,
    records: Sequence[Mapping[str, Any]],
    delta: Any,
    *,
    verify_full_rebuild: bool = False,
) -> Any:
    function = _find_function(
        control_module,
        (
            "_refresh_index_set",
            "_refresh_indexes",
            "_incremental_snapshot",
            "_apply_registry_update_to_snapshot",
            "_apply_registry_update",
        ),
    )
    if function is None:
        raise InvariantError("INCREMENTAL_INDEX_HELPER_MISSING", "control.py must expose private incremental refresh")
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"base", "snapshot", "indexes", "old_snapshot"}:
            kwargs[key] = base
        elif key in {"records", "candidate_records", "new_records"}:
            kwargs[key] = records
        elif key in {"delta", "update", "registry_update"}:
            kwargs[key] = delta
        elif key == "verify_full_rebuild":
            kwargs[key] = verify_full_rebuild
    if len(kwargs) >= 2:
        result = function(**kwargs)
    else:
        result = function(base, records, delta)
    if isinstance(result, tuple) and result and hasattr(result[0], "indexes"):
        if verify_full_rebuild:
            stats = _plain(result[1]) if len(result) > 1 else None
            if not isinstance(stats, Mapping) or stats.get("full_rebuild_parity") is not True:
                raise InvariantError(
                    "INCREMENTAL_INDEX_FULL_REBUILD_PROOF_MISSING", repr(stats)
                )
        return result[0]
    if verify_full_rebuild and "verify_full_rebuild" not in signature.parameters:
        raise InvariantError(
            "INCREMENTAL_INDEX_FULL_REBUILD_PROOF_MISSING",
            f"{function.__name__} has no verify_full_rebuild mechanism",
        )
    return result


def _index_projection(value: Any) -> Any:
    plain = _plain(value)
    if isinstance(plain, Mapping):
        ignored = {
            "generation",
            "created_at",
            "built_at_monotonic",
            "diagnostics",
            "metrics",
            "counters",
        }
        return {
            key: _index_projection(child)
            for key, child in sorted(plain.items())
            if key.lower() not in ignored
        }
    if isinstance(plain, list):
        converted = [_index_projection(child) for child in plain]
        try:
            return sorted(converted, key=_canonical_json)
        except TypeError:
            return converted
    return plain


def _validate_index_parity(control_module: Any, records: Sequence[Mapping[str, Any]], candidate: Sequence[Mapping[str, Any]], delta: Any) -> None:
    if len(records) > 1_000:
        template = next(record for record in records if record.get("bindings"))
        records = _synthetic_records(256)
        candidate = list(records)
        changed = copy.deepcopy(records[127])
        changed["bindings"][0]["selected_parameter_policy"] = {
            **dict(changed["bindings"][0]["selected_parameter_policy"]),
            "validation_probe_revision": 1,
        }
        candidate[127] = changed
        delta = _derive_delta(control_module, records, candidate)
    base = _build_indexes(control_module, records)
    incremental = _refresh_indexes(
        control_module,
        base,
        candidate,
        delta,
        verify_full_rebuild=True,
    )
    full = _build_indexes(control_module, candidate)
    if _canonical_json(_index_projection(incremental)) != _canonical_json(_index_projection(full)):
        raise InvariantError("INCREMENTAL_INDEX_PARITY", "incremental refresh differs from full rebuild")
    repeated = _refresh_indexes(
        control_module,
        base,
        candidate,
        delta,
        verify_full_rebuild=True,
    )
    if _canonical_json(_index_projection(repeated)) != _canonical_json(_index_projection(incremental)):
        raise InvariantError("DELTA_IDEMPOTENCE", "reapplying RegistryUpdateV1 changes indexes")


def _write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in sorted(records, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"]))):
            handle.write(_canonical_json(record))
            handle.write("\n")


def _write_layout_fallback(directory: Path, records: Sequence[Mapping[str, Any]], sharded: bool) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    if not sharded:
        _write_jsonl(directory / "registry.jsonl", ordered)
        return
    partitions: list[dict[str, Any]] = []
    width = max(1, min(500, math.ceil(len(ordered) / 4)))
    for index, start in enumerate(range(0, len(ordered), width)):
        subset = ordered[start : start + width]
        name = f"registry.part-{index:04d}.jsonl"
        _write_jsonl(directory / name, subset)
        partitions.append(
            {
                "file_name": name,
                "canonical_id_start": subset[0]["canonical_component_id"],
                "canonical_id_end": subset[-1]["canonical_component_id"],
                "row_count": len(subset),
            }
        )
    manifest = {
        "registry_schema_version": "1.0",
        "layout": "DETERMINISTIC_SHARDED_JSONL",
        "partition_policy": {"kind": "STABLE_CANONICAL_ID_PREFIX_AND_RANGE"},
        "row_count": len(ordered),
        "partitions": [
            {
                "file": row["file_name"],
                "range_start": row["canonical_id_start"],
                "range_end": row["canonical_id_end"],
                "row_count": row["row_count"],
            }
            for row in partitions
        ],
    }
    (directory / "registry.manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8", newline="\n")


def _write_layout(control_module: Any, directory: Path, records: Sequence[Mapping[str, Any]], sharded: bool) -> None:
    function = _find_function(
        control_module,
        ("_write_logical_registry", "_write_registry_layout", "_write_registry_records"),
    )
    if function is None:
        _write_layout_fallback(directory, records, sharded)
        return
    signature = inspect.signature(function)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "rows", "registry_records"}:
            kwargs[key] = records
        elif key in {"artifact_dir", "registry_root", "directory", "out_dir", "path"}:
            kwargs[key] = directory
        elif key in {"force_sharded", "sharded"}:
            kwargs[key] = sharded
        elif key in {"force_layout", "layout"}:
            kwargs[key] = "sharded" if sharded else "single"
    try:
        function(**kwargs)
    except TypeError:
        _write_layout_fallback(directory, records, sharded)


_SCALE_PROBE_SEED = 169_10_000
_SCALE_ROOT_ID = "QTT.COMP.SCALE.SELECTED.RELATIVE_SPREAD"
_SCALE_STACK_IDENTITY_REF = "qtt.computation_control.native:stack_identity"


def _scale_requirement(
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


def _scale_record(
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
    requirements = tuple(copy.deepcopy(dict(value)) for value in requirements)
    requirements_by_input = {
        str(requirement["consumer_input_name"]): requirement
        for requirement in requirements
        if requirement.get("required_or_optional") != "OPTIONAL"
    }
    input_source_bindings: list[dict[str, Any]] = []
    for name, unit in inputs:
        requirement = requirements_by_input.get(name)
        if requirement is None:
            input_source_bindings.append(
                {
                    "input_name": name,
                    "source_ref": "CONTROL1_FIXED_SEED_SCALE_PROBE",
                    "declared_type": "DECIMAL",
                    "unit_or_basis": unit,
                    "binding_state": "EXACT_TYPED_FIXTURE_BINDING",
                }
            )
        else:
            input_source_bindings.append(
                {
                    "input_name": name,
                    "source_ref": requirement[
                        "required_component_id_or_source_selector"
                    ],
                    "producer_output_name": requirement["producer_output_name"],
                    "declared_type": "DECIMAL",
                    "unit_or_basis": unit,
                    "binding_state": "CANONICAL_REQUIREMENT_OUTPUT",
                }
            )
    return {
        "canonical_component_id": component_id,
        "semantic_version": "1.0",
        "record_state": "CANONICAL_ACCEPTED",
        "origin_cohorts": ["VALIDATOR_SYNTHETIC_SCALE"],
        "definition": {
            "display_name": suffix,
            "description": "Bounded temporary CONTROL1 structural scale computation.",
            "component_kind": "DETERMINISTIC_TRANSFORM",
            "family_template_ref_or_null": None,
            "complete_mathematical_or_procedural_definition": (
                f"allowlisted deterministic scale procedure {suffix}"
            ),
            "objective_sense_or_null": None,
            "assumptions": ["TEMPORARY_FIXED_SEED_VALIDATION_ONLY"],
            "hard_constraints": [],
            "soft_preferences": [],
            "domain_and_boundary_behavior": {"invalid": "FAIL_CLOSED"},
            "state_and_time_semantics": {
                "state": "STATELESS",
                "time": "SAME_REQUEST",
            },
            "input_schema": [
                {"name": name, "type": "DECIMAL", "unit": unit, "required": True}
                for name, unit in inputs
            ],
            "output_schema": [
                {"name": name, "type": "DECIMAL", "unit": unit, "required": True}
                for name, unit in outputs
            ],
            "units_and_bases": {
                name: unit for name, unit in [*inputs, *outputs]
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
            "requirements": list(requirements),
            "latency_class": "PRETRADE_BOUNDED",
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
            "quantum": {
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
                "fallback": "NOT_REQUIRED",
                "maturity_ceiling": "SPECIFIED",
            },
            "implementation_versions": [
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
            "oracle_and_test_refs": [
                "tests/pr169_qku_comp_control1/test_control1.py::test_fixed_seed_structural_scale_probe_real_layout_resolve_compute"
            ],
            "equivalence_proof_refs": [],
        },
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
            "consumer_class_tags": ["CONTROL1_INDEPENDENT_VALIDATOR"],
        },
        "bindings": [
            {
                "binding_id": binding_id or f"BINDING.SCALE.{suffix}",
                "market": "SYNTHETIC_SCALE",
                "venue": "LOCAL_FIXTURE",
                "context_selector": {
                    "market": "SYNTHETIC_SCALE",
                    "venue": "LOCAL_FIXTURE",
                },
                "qku_binding_selector_or_null": None,
                "supported_modes": ["FIXTURE_NONLIVE"],
                "mode_state": {
                    "FIXTURE_NONLIVE": {
                        "evidence": "FIXTURE",
                        "authorization": "NOT_ELIGIBLE",
                    }
                },
                "as_of_policy": "IMMUTABLE_FIXTURE",
                "selected_implementation_version": implementation_version,
                "binding_version": "1.0",
                "selected_parameter_policy": {
                    "policy_id": "PARAM.SCALE.FIXED",
                    "version": "1.0",
                    "defaults": {},
                    "default_provenance": "CONTROL1_FIXED_SEED_SCALE_PROBE",
                },
                "input_source_bindings": input_source_bindings,
                "venue_semantic_version": "LOCAL.FIXTURE.1",
                "portfolio_state_requirement": "NOT_REQUIRED",
                "cash_state_requirement": "NOT_REQUIRED",
                "freshness_and_TTL": {
                    "policy": "IMMUTABLE_FIXTURE",
                    "ttl_seconds": None,
                },
                "point_in_time_policy": "FIXTURE_LOCK_ONLY",
                "requirement_context_policy": "INHERIT_ROOT_CONTEXT",
                "selected_requirement_alternatives": [],
                "readiness": {
                    "specification": "PASS",
                    "implementation": "PASS",
                    "inputs": "PASS",
                    "requirements": "PASS",
                    "oracle": "PASS",
                    "context": "PASS",
                    "evidence": "FIXTURE",
                    "authorization": "NOT_ELIGIBLE",
                },
                "derived_state": "STACK_READY",
                "exact_resolution_action_or_null": None,
                "evidence_summary": {
                    "state": "FIXTURE",
                    "source_evidence_refs": [
                        "tests/pr169_qku_comp_control1/test_control1.py"
                    ],
                    "limitations": ["TEMPORARY_NONLIVE_STRUCTURAL_PROBE_ONLY"],
                },
                "agent_access_policy": {},
                "fallback_policy": {"state": "FAIL_CLOSED"},
                "runtime_snapshot_ref_or_null": None,
                "activation_state": "INACTIVE_NONLIVE",
                "rollback_target_or_null": None,
                "upstream_value_lineage": ["CONTROL1_FIXED_SEED_SCALE_PROBE"],
                "downstream_consumer_classes": [
                    "CONTROL1_INDEPENDENT_VALIDATOR"
                ],
                "producer_owner": "CONTROL1_INDEPENDENT_VALIDATOR",
                "validator_refs": ["tools/validate_pr169_qku_comp_control1.py"],
                "terminal_disposition_or_null": None,
            }
        ],
        "provenance": [
            {
                "source_artifact_ref": "CONTROL1_FIXED_SEED_SCALE_PROBE",
                "source_row_ref": component_id,
                "source_local_identity_or_name": suffix,
                "source_fields_consumed": ["fixed_seed_structural_probe"],
                "source_relation": "VALIDATION_ONLY",
                "canonical_target_ref": component_id,
                "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            }
        ],
        "relations": [],
        "governance": {
            "producer_owner": "CONTROL1_INDEPENDENT_VALIDATOR",
            "validator_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            "reviewer_or_challenger_owner": "CONTROL1_GROUPED_TEST_ORACLE",
            "change_authority": "TEMPORARY_VALIDATION_ONLY",
        },
    }


def _synthetic_records(count: int) -> list[dict[str, Any]]:
    mid_id = "QTT.COMP.SCALE.SELECTED.MID_PRICE"
    spread_id = "QTT.COMP.SCALE.SELECTED.SPREAD"
    selected = [
        _scale_record(
            mid_id,
            "qtt.computation_control.native:decimal_mid_price",
            (("best_bid", "PRICE"), ("best_ask", "PRICE")),
            (("mid_price", "PRICE"),),
        ),
        _scale_record(
            spread_id,
            "qtt.computation_control.native:decimal_spread",
            (("best_bid", "PRICE"), ("best_ask", "PRICE")),
            (("spread", "PRICE_DELTA"),),
        ),
        _scale_record(
            _SCALE_ROOT_ID,
            "qtt.computation_control.native:decimal_relative_spread",
            (("spread", "PRICE_DELTA"), ("mid_price", "PRICE")),
            (("relative_spread", "RATIO"),),
            requirements=(
                _scale_requirement(
                    mid_id, "mid_price", "mid_price", "MID_PRICE_DENOMINATOR"
                ),
                _scale_requirement(
                    spread_id, "spread", "spread", "ABSOLUTE_SPREAD_NUMERATOR"
                ),
            ),
        ),
    ]
    unrelated = [
        _scale_record(
            f"QTT.COMP.SCALE.UNRELATED.{index:08d}",
            _SCALE_STACK_IDENTITY_REF,
            (("result", "UNITLESS"),),
            (("result", "UNITLESS"),),
            binding_id=f"BINDING.SCALE.UNRELATED.{index:08d}",
        )
        for index in range(count - len(selected))
    ]
    records = [*selected, *unrelated]
    random.Random(_SCALE_PROBE_SEED).shuffle(records)
    return records


def _scale_probe(
    control_module: Any,
    facade_class: type[Any],
    count: int,
    deadline: Deadline,
) -> dict[str, Any]:
    if count <= 0:
        return {"records": 0, "skipped": True}
    started = time.perf_counter()
    records = _synthetic_records(count)
    build_ms = int((time.perf_counter() - started) * 1000)
    with tempfile.TemporaryDirectory(prefix="qtt-control1-scale-") as temporary:
        root = Path(temporary)
        single_dir = root / "single"
        shard_dir = root / "sharded"
        write_started = time.perf_counter()
        _write_layout(control_module, single_dir, records, False)
        _write_layout(control_module, shard_dir, records, True)
        logical_loader = getattr(control_module, "_load_logical_registry", None)
        if not callable(logical_loader):
            raise InvariantError(
                "LOGICAL_REGISTRY_LOADER_MISSING", "scale probe cannot load layouts"
            )
        single_rows, single_layout_info = logical_loader(single_dir)
        sharded_rows, sharded_layout_info = logical_loader(shard_dir)
        single_layout = str(single_layout_info.get("layout"))
        sharded_layout = str(sharded_layout_info.get("layout"))
        key = lambda row: (
            str(row["canonical_component_id"]),
            str(row["semantic_version"]),
        )
        if sorted(single_rows, key=key) != sorted(sharded_rows, key=key):
            raise InvariantError(
                "SINGLE_SHARD_LOGICAL_PARITY", "serialized logical rows differ"
            )
        single = _construct_facade(facade_class, single_dir)
        sharded = _construct_facade(facade_class, shard_dir)
        write_load_ms = int((time.perf_counter() - write_started) * 1000)
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
        typed_inputs = {
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
        planes = (single, sharded)
        original_open = Path.open

        def forbidden_open(*args: Any, **kwargs: Any) -> Any:
            raise InvariantError(
                "RUNTIME_REGISTRY_FILE_READ",
                "facade reopened a physical registry after initialization",
            )

        Path.open = forbidden_open
        resolve_started = time.perf_counter()
        try:
            deadline.check("scale_probe_resolve_compute")
            plans = [
                _operation(plane, "resolve", _SCALE_ROOT_ID, context=context)
                for plane in planes
            ]
            receipts = [
                _operation(
                    plane,
                    "compute",
                    _SCALE_ROOT_ID,
                    inputs=typed_inputs,
                    context=context,
                )
                for plane in planes
            ]
        finally:
            Path.open = original_open
        resolve_compute_ms = int((time.perf_counter() - resolve_started) * 1000)
        plan_rows = [_plain(plan) for plan in plans]
        node_sets = [
            {
                str(value.get("canonical_component_id"))
                for value in row.get("topological_nodes", ())
                if isinstance(value, Mapping)
            }
            for row in plan_rows
        ]
        expected_nodes = {
            "QTT.COMP.SCALE.SELECTED.MID_PRICE",
            "QTT.COMP.SCALE.SELECTED.SPREAD",
            _SCALE_ROOT_ID,
        }
        if any(nodes != expected_nodes for nodes in node_sets):
            raise InvariantError("SELECTED_SUBGRAPH_BREADTH", repr(node_sets))
        receipt_rows = [_plain(receipt) for receipt in receipts]
        stable_receipts = [
            {
                "component_id": row.get("component_id"),
                "outputs": row.get("outputs"),
                "output_units": row.get("output_units"),
                "nodes_executed": row.get("nodes_executed"),
                "components": sorted(
                    str(value.get("component_id"))
                    for value in row.get("requirement_receipts", ())
                    if isinstance(value, Mapping)
                ),
            }
            for row in receipt_rows
        ]
        if stable_receipts[0] != stable_receipts[1]:
            raise InvariantError(
                "SINGLE_SHARD_RECEIPT_PARITY", repr(stable_receipts)
            )
        if stable_receipts[0].get("outputs") != {"relative_spread": "0.4"}:
            raise InvariantError(
                "SCALE_COMPUTE_OUTPUT", repr(stable_receipts[0].get("outputs"))
            )
        diagnostics = [_diagnostic_mapping(plane) for plane in planes]
        for plane, counters in zip(planes, diagnostics, strict=True):
            _validate_runtime_counters(plane)
            if int(counters.get("registry_rows", -1)) != count:
                raise InvariantError("SCALE_REGISTRY_ROWS", repr(counters))
            if int(counters.get("records_examined_last_request", -1)) != 3:
                raise InvariantError("SCALE_FULL_REGISTRY_SCAN", repr(counters))
            if int(counters.get("nodes_executed_last_request", -1)) != 3:
                raise InvariantError("SCALE_EXECUTION_BREADTH", repr(counters))
            calls = counters.get("implementation_call_counts", {})
            if isinstance(calls, Mapping) and int(
                calls.get(_SCALE_STACK_IDENTITY_REF, 0)
            ):
                raise InvariantError(
                    "SCALE_UNRELATED_EXECUTION", repr(dict(calls))
                )
    return {
        "records": count,
        "fixed_seed": _SCALE_PROBE_SEED,
        "serialized_layouts": [single_layout, sharded_layout],
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
        "timing_threshold_authority": False,
        "local_non_authoritative_measurements_ms": {
            "record_materialization": build_ms,
            "both_layout_write_load_and_facade_initialization": write_load_ms,
            "resolve_and_compute": resolve_compute_ms,
        },
    }


def _validate_semantic_reuse(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    relation_counts: Counter[str] = Counter()
    accepted_ids = {
        str(record["canonical_component_id"])
        for record in records
        if record.get("record_state") == "CANONICAL_ACCEPTED"
    }
    for record in records:
        component_id = str(record["canonical_component_id"])
        proofs = record["definition"].get("equivalence_proof_refs", [])
        for relation in record.get("relations", []):
            kind = _relation_type(relation)
            relation_counts[kind] += 1
            target = str(
                relation.get("canonical_target_ref")
                or relation.get("target_component_id")
                or relation.get("target_ref")
                or ""
            )
            if kind in {"ALIAS_OF", "FAMILY_BINDING_OF"}:
                if not proofs and not relation.get("proof_refs"):
                    raise InvariantError("SEMANTIC_REUSE_WITHOUT_PROOF", f"{component_id}: {kind}")
                if target and target not in accepted_ids:
                    raise InvariantError("SEMANTIC_REUSE_TARGET", f"{component_id}: {target}")
            if kind == "ENCODES_OR_MAPS" and target == component_id:
                raise InvariantError("QUANTUM_ORIGINAL_ALIAS", component_id)
    provenance_relations = Counter(
        str(entry.get("source_relation", ""))
        for record in records
        for entry in record.get("provenance", [])
    )
    if not any(
        token in key
        for key in provenance_relations
        for token in ("DUPLICATE", "REUSE", "GROUPING_NOT_SEMANTIC_PROOF")
    ):
        raise InvariantError("SEMANTIC_REUSE_CASE_COVERAGE", "no dedupe/reuse source disposition")
    result = dict(relation_counts)
    result["SOURCE_DISPOSITION_KINDS"] = len(provenance_relations)
    return result


def _expect_defect(code: str, function: Callable[[], Any]) -> None:
    try:
        function()
    except InvariantError as exc:
        if exc.code != code:
            raise InvariantError("DEFECT_WRONG_REASON", f"expected={code}, observed={exc.code}: {exc.detail}") from exc
        return
    raise InvariantError("DEFECT_NOT_REJECTED", code)


def _defect_injection(template: Mapping[str, Any]) -> int:
    probes = 0

    bulk = copy.deepcopy(template)
    bulk["bindings"][0]["evidence_summary"] = {"replay_history": list(range(100))}
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(bulk))
    probes += 1

    neutral_bulk = copy.deepcopy(template)
    neutral_bulk["bindings"][0]["evidence_summary"] = {
        "observations": {f"row_{index:05d}": {"value": index} for index in range(5_000)}
    }
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(neutral_bulk))
    probes += 1

    deeply_nested = copy.deepcopy(template)
    nested: dict[str, Any] = {"terminal": "reference"}
    for index in range(12):
        nested = {f"level_{index:02d}": nested}
    deeply_nested["bindings"][0]["evidence_summary"] = nested
    _expect_defect("BULK_EVIDENCE_PAYLOAD", lambda: _validate_record(deeply_nested))
    probes += 1

    unit = copy.deepcopy(template)
    del unit["definition"]["units_and_bases"]
    _expect_defect("DEFINITION_SHAPE", lambda: _validate_record(unit))
    probes += 1

    empty_units = copy.deepcopy(template)
    empty_units["definition"]["input_schema"] = [
        {
            "name": "validator_input",
            "type": "DECIMAL",
            "unit_or_basis": "unitless",
        }
    ]
    empty_units["definition"]["units_and_bases"] = {}
    _expect_defect(
        "UNIT_SCHEMA_MISSING", lambda: _validate_record(empty_units)
    )
    probes += 1

    fixture_false_specification = copy.deepcopy(template)
    fixture_false_specification["definition"][
        "domain_and_boundary_behavior"
    ] = "CONTROL_PLANE_TYPED_VALIDATION_REQUIRED"
    fixture_false_specification["definition"]["implementation_versions"][0][
        "fixture_ref"
    ] = "tests/pr169_qku_comp_control1/fixtures/independent-proof.json"
    fixture_false_specification["bindings"][0]["readiness"][
        "specification"
    ] = "PASS"
    _expect_defect(
        "FALSE_SPECIFICATION_PASS",
        lambda: _validate_record(fixture_false_specification),
    )
    probes += 1

    fixture_false_compute = copy.deepcopy(fixture_false_specification)
    fixture_false_compute["record_state"] = "CANONICAL_ACCEPTED"
    fixture_false_compute["bindings"][0]["readiness"]["specification"] = "REQUIRED"
    fixture_false_compute["bindings"][0]["derived_state"] = "CONTEXT_READY"
    fixture_false_compute_issues = _independent_specification_issues(
        fixture_false_compute["definition"]
    )
    fixture_false_compute["bindings"][0]["exact_resolution_action_or_null"] = (
        "MISSING_SPECIFICATION_SEMANTICS: "
        f"{fixture_false_compute['canonical_component_id']}@"
        f"{fixture_false_compute['semantic_version']}: "
        + ",".join(fixture_false_compute_issues)
    )
    _expect_defect(
        "FALSE_SPECIFIED_STATE",
        lambda: _validate_record(fixture_false_compute),
    )
    probes += 1
    fixture_false_compute["bindings"][0]["derived_state"] = (
        "SPECIFICATION_REQUIRED"
    )
    fixture_false_compute["bindings"][0]["agent_access_policy"] = {
        "parameter_selector_agent": {
            "control_plane_operations": ["resolve", "compute", "status", "explain"]
        }
    }
    _expect_defect(
        "FALSE_AGENT_COMPUTE_ELIGIBILITY",
        lambda: _validate_record(fixture_false_compute),
    )
    probes += 1

    stale = copy.deepcopy(template)
    del stale["bindings"][0]["freshness_and_TTL"]
    _expect_defect("BINDING_SHAPE", lambda: _validate_record(stale))
    probes += 1

    nonfinite = copy.deepcopy(template)
    nonfinite["bindings"][0]["evidence_summary"] = {"metric": float("inf")}
    _expect_defect("NONFINITE_VALUE", lambda: _validate_record(nonfinite))
    probes += 1

    fixture = copy.deepcopy(template)
    fixture["definition"]["implementation_versions"][0]["fixture_inputs"] = {"value": "1"}
    _expect_defect("CANONICAL_FIXTURE_PAYLOAD", lambda: _validate_record(fixture))
    probes += 1

    ambiguous = copy.deepcopy(template)
    duplicate = copy.deepcopy(ambiguous["bindings"][0])
    duplicate["binding_id"] += "-other"
    ambiguous["bindings"].append(duplicate)
    _expect_defect("AMBIGUOUS_BINDING", lambda: _validate_record(ambiguous))
    probes += 1

    overlapping = copy.deepcopy(template)
    original = overlapping["bindings"][0]
    original["supported_modes"] = ["TEST_VECTOR"]
    original["mode_state"] = {
        "TEST_VECTOR": {"evidence": "FIXTURE", "authorization": "NOT_ELIGIBLE"}
    }
    original["context_selector"] = {
        "context_family": "VALIDATOR_OVERLAP",
        "left_wildcard": "ANY",
    }
    overlap = copy.deepcopy(original)
    overlap["binding_id"] += ".OVERLAP"
    overlap["context_selector"] = {
        "context_family": "VALIDATOR_OVERLAP",
        "right_wildcard": "ANY",
    }
    overlapping["bindings"].append(overlap)
    _expect_defect(
        "OVERLAPPING_BINDING_SELECTORS", lambda: _validate_record(overlapping)
    )
    probes += 1

    missing_mode = copy.deepcopy(template)
    missing_mode["bindings"][0]["supported_modes"] = ["TEST_VECTOR"]
    missing_mode["bindings"][0]["mode_state"] = {}
    _expect_defect("MODE_STATE_MISSING", lambda: _validate_record(missing_mode))
    probes += 1

    extra_mode = copy.deepcopy(template)
    extra_mode["bindings"][0]["supported_modes"] = ["TEST_VECTOR"]
    extra_mode["bindings"][0]["mode_state"] = {
        "TEST_VECTOR": {"evidence": "FIXTURE", "authorization": "NOT_ELIGIBLE"},
        "PAPER": {"evidence": "NONE", "authorization": "NOT_ELIGIBLE"},
    }
    _expect_defect(
        "MODE_STATE_WITHOUT_SUPPORTED_MODE", lambda: _validate_record(extra_mode)
    )
    probes += 1

    unsafe = copy.deepcopy(template)
    unsafe["definition"]["implementation_versions"] = [
        {
            "implementation_version": "1",
            "callable_or_solver_ref": "os.system",
            "determinism_or_seed_policy": "DETERMINISTIC",
            "memoizable_flag": False,
        }
    ]
    _expect_defect(
        "UNSAFE_CALLABLE_REF",
        lambda: _validate_callable_ref(_implementation_ref(unsafe["definition"]["implementation_versions"][0])),
    )
    probes += 1

    first_id = str(template["canonical_component_id"])
    cycle_a = copy.deepcopy(template)
    cycle_b = copy.deepcopy(template)
    cycle_b["canonical_component_id"] = first_id + ".CYCLE_B"
    req = {
        "required_component_id_or_source_selector": cycle_b["canonical_component_id"],
        "required_semantic_version_constraint": "1.0",
        "requirement_role": "DEFECT",
        "required_or_optional": "REQUIRED",
        "producer_output_name": "value",
        "consumer_input_name": "value",
        "unit_or_basis_conversion": "IDENTITY",
        "timing_and_freshness_constraint": "SAME_REQUEST",
        "activation_condition": "ALWAYS",
        "fallback_component_id_or_null": None,
        "failure_behavior": "FAIL_CLOSED",
    }
    cycle_a["definition"]["requirements"] = [req]
    reverse_req = dict(req)
    reverse_req["required_component_id_or_source_selector"] = first_id
    cycle_b["definition"]["requirements"] = [reverse_req]
    _expect_defect("DAG_CYCLE", lambda: _topological(_graph([cycle_a, cycle_b])[0]))
    probes += 1
    return probes


def _snapshot_replace_probe(control_module: Any, facade: Any, candidate: Sequence[Mapping[str, Any]], delta: Any, selector: str, context: Mapping[str, Any]) -> int:
    replace = None
    for name in ("_replace_snapshot", "_apply_validated_registry_update", "_swap_snapshot"):
        method = getattr(facade, name, None)
        if callable(method):
            replace = method
            break
    if replace is None:
        raise InvariantError("SNAPSHOT_SWAP_HELPER_MISSING", "facade needs a private validation-only snapshot swap mechanism")
    observed: list[str] = []
    failures: list[str] = []
    stop = threading.Event()
    first_observation = threading.Event()

    def reader() -> None:
        while not stop.is_set():
            try:
                observed.append(_canonical_json(_operation(facade, "status", selector, context=context), strip_volatile=True))
                first_observation.set()
                # Bound the observation rate while leaving the reader alive
                # until the replacement is visible.  A fixed call-count cap
                # can be exhausted before the writer thread is scheduled and
                # therefore does not exercise the post-swap snapshot at all.
                stop.wait(0.001)
            except Exception as exc:  # pragma: no cover - reported deterministically below
                failures.append(f"{type(exc).__name__}: {exc}")
                break

    thread = threading.Thread(target=reader, name="control1-snapshot-reader", daemon=True)
    thread.start()
    if not first_observation.wait(timeout=5):
        stop.set()
        thread.join(timeout=5)
        raise InvariantError("SNAPSHOT_SWAP_CONCURRENCY", "reader did not pin the old generation")
    signature = inspect.signature(replace)
    kwargs: dict[str, Any] = {}
    for key in signature.parameters:
        if key in {"records", "candidate_records", "new_records"}:
            kwargs[key] = candidate
        elif key in {"delta", "registry_update", "update"}:
            kwargs[key] = delta
    try:
        if kwargs:
            replace(**kwargs)
        else:
            replace(candidate, delta)
        wait_until = time.perf_counter() + 1.0
        while time.perf_counter() < wait_until and len(set(observed)) < 2 and not failures:
            time.sleep(0.001)
    finally:
        stop.set()
        thread.join(timeout=10)
    if thread.is_alive() or failures or not observed:
        raise InvariantError("SNAPSHOT_SWAP_CONCURRENCY", f"alive={thread.is_alive()}, failures={failures}, observations={len(observed)}")
    if len(set(observed)) != 2:
        raise InvariantError("MIXED_SNAPSHOT_GENERATION", f"expected old/new payloads, observed={len(set(observed))}")
    return len(observed)


def _bounded_snapshot_concurrency_probe(
    control_module: Any,
    facade_class: type[Any],
    template: Mapping[str, Any],
) -> int:
    base = _synthetic_records(128)
    candidate = list(base)
    changed = copy.deepcopy(base[63])
    changed["bindings"][0]["selected_parameter_policy"] = {
        **dict(changed["bindings"][0]["selected_parameter_policy"]),
        "validation_probe_revision": 1,
    }
    candidate[63] = changed
    delta = _derive_delta(control_module, base, candidate)
    facade = facade_class(records=base)
    selector = str(changed["canonical_component_id"])
    context = _binding_context(changed["bindings"][0])
    return _snapshot_replace_probe(control_module, facade, candidate, delta, selector, context)


def _compiler_mechanism_probe(control_module: Any, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    function = _find_function(
        control_module,
        ("_compile_expansion_batch_for_validation", "_compile_expansion_batch", "_compile_candidate_batch"),
    )
    if function is None:
        raise InvariantError("COMPILER_PROBE_HELPER_MISSING", "private compiler mechanism is required")
    source_template = next(
        (
            copy.deepcopy(record)
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED"
            and record.get("bindings")
            and record.get("definition", {}).get("implementation_versions")
            and not record.get("definition", {}).get("requirements")
        ),
        None,
    )
    if source_template is None:
        raise InvariantError("COMPILER_PROBE_FIXTURE_MISSING", "no accepted implementation record")
    if len(records) > 1_000:
        bounded = _synthetic_records(64)
        selected_version = str(
            source_template["definition"]["implementation_versions"][0]["implementation_version"]
        )
        bounded_template = next(
            record
            for record in bounded
            if not record.get("definition", {}).get("requirements")
        )
        bounded_template["definition"]["implementation_versions"] = copy.deepcopy(
            source_template["definition"]["implementation_versions"]
        )
        bounded_template["definition"]["implementation_inventory_class"] = "FORMULA"
        bounded_template["bindings"][0]["selected_implementation_version"] = selected_version
        bounded_template["bindings"][0]["readiness"]["implementation"] = "PASS"
        records = bounded
    base_projection = _canonical_json(records)
    template = next(
        copy.deepcopy(record)
        for record in records
        if record.get("definition", {}).get("implementation_versions")
        and not record.get("definition", {}).get("requirements")
    )
    base_id = str(template["canonical_component_id"])

    def provenance(case: str, target: str) -> dict[str, Any]:
        return {
            "source_artifact_ref": "VALIDATOR_SYNTHETIC_EXPANSION",
            "source_row_ref": case,
            "source_local_identity_or_name": f"VALIDATOR::{case}",
            "source_fields_consumed": ["case", "record"],
            "source_relation": case,
            "canonical_target_ref": target,
            "proof_refs": ["tools/validate_pr169_qku_comp_control1.py"],
        }

    def clone(case: str, *, same_semantics: bool = False) -> dict[str, Any]:
        value = copy.deepcopy(template)
        component_id = f"QTT.COMP.VALIDATION.{case}"
        value["canonical_component_id"] = component_id
        value["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        value["record_state"] = "PROVISIONAL"
        if not same_semantics:
            value["definition"]["display_name"] = f"Validation {case}"
            value["definition"]["description"] = f"Independent compiler probe for {case}."
            value["definition"]["complete_mathematical_or_procedural_definition"] = (
                f"VALIDATION_PROCEDURE::{case}"
            )
        if not same_semantics:
            value["definition"]["requirements"] = []
        value["provenance"] = [provenance(case, component_id)]
        value["relations"] = []
        for index, binding in enumerate(value["bindings"]):
            if case != "NAME_ALIAS":
                binding["binding_id"] = f"BINDING.VALIDATION.{case}.{index:02d}"
                binding["context_selector"] = {
                    "context_family": "VALIDATOR_SYNTHETIC",
                    "case": case,
                }
            binding["exact_resolution_action_or_null"] = f"MISSING_INDEPENDENT_PROMOTION: {component_id}"
            binding["readiness"] = {
                "specification": "PASS",
                "implementation": "REQUIRED",
                "inputs": "REQUIRED",
                "requirements": "REQUIRED",
                "oracle": "REQUIRED",
                "context": "REQUIRED",
                "evidence": "NONE",
                "authorization": "NOT_ELIGIBLE",
            }
            binding["derived_state"] = "SPECIFIED"
        value["uses"]["qku_role_bindings"] = []
        return value

    exact_duplicate = copy.deepcopy(template)
    exact_duplicate["origin_cohorts"] = sorted(set(exact_duplicate["origin_cohorts"]) | {"VALIDATOR_SYNTHETIC_EXPANSION"})
    exact_duplicate["provenance"] = [*exact_duplicate["provenance"], provenance("EXACT_DUPLICATE", base_id)]

    provenance_only = copy.deepcopy(template)
    provenance_only["provenance"] = [*provenance_only["provenance"], provenance("PROVENANCE_ONLY", base_id)]

    qku_addition = copy.deepcopy(template)
    qku_addition["provenance"] = [
        *qku_addition["provenance"],
        provenance("QKU_ROLE_ADDITION", base_id),
    ]
    qku_addition["uses"]["qku_role_bindings"] = [
        *qku_addition["uses"].get("qku_role_bindings", []),
        {
            "qku_id": "QKU-VALIDATOR-SEMANTIC-REUSE",
            "role_or_decision_stage": "INTERNAL_SUPPORT",
            "market_family": "VALIDATOR_SYNTHETIC",
            "stack_root_or_direct_component": base_id,
            "selection_rule_if_container": None,
            "agent_policy_tags": ["VALIDATOR_ONLY"],
            "source_refs": ["VALIDATOR_SYNTHETIC_EXPANSION"],
        },
    ]

    binding_addition = copy.deepcopy(template)
    binding_addition["provenance"] = [
        *binding_addition["provenance"],
        provenance("NEW_BINDING", base_id),
    ]
    new_binding = copy.deepcopy(binding_addition["bindings"][0])
    new_binding["binding_id"] = "BINDING.VALIDATION.NEW_BINDING.00"
    # A selector with only new keys still overlaps a broad existing selector:
    # requests that omit those keys can match both.  Give this proof binding a
    # genuinely disjoint market domain and repeat that domain in its selector.
    new_binding["market"] = "VALIDATOR_SYNTHETIC_NEW_BINDING"
    new_binding["context_selector"] = {
        "market": "VALIDATOR_SYNTHETIC_NEW_BINDING",
        "venue": copy.deepcopy(new_binding["venue"]),
        "case": "NEW_BINDING",
    }
    new_binding["readiness"] = {
        "specification": "PASS",
        "implementation": "REQUIRED",
        "inputs": "REQUIRED",
        "requirements": "REQUIRED",
        "oracle": "REQUIRED",
        "context": "REQUIRED",
        "evidence": "NONE",
        "authorization": "NOT_ELIGIBLE",
    }
    new_binding["derived_state"] = "SPECIFIED"
    new_binding["exact_resolution_action_or_null"] = (
        f"MISSING_INDEPENDENT_PROMOTION: {base_id}"
    )
    binding_addition["bindings"].append(new_binding)

    parameter_update = copy.deepcopy(template)
    parameter_update["provenance"] = [
        *parameter_update["provenance"],
        provenance("NEW_PARAMETER_POLICY", base_id),
    ]
    parameter_update["bindings"][0]["selected_parameter_policy"] = {
        **dict(parameter_update["bindings"][0]["selected_parameter_policy"]),
        "validation_probe_revision": 1,
    }

    implementation_update = copy.deepcopy(template)
    implementation_update["provenance"] = [
        *implementation_update["provenance"],
        provenance("NEW_IMPLEMENTATION", base_id),
    ]
    added_implementation = copy.deepcopy(implementation_update["definition"]["implementation_versions"][0])
    added_implementation["implementation_version"] = "validation-probe"
    implementation_update["definition"]["implementation_versions"].append(added_implementation)

    alias = clone("NAME_ALIAS", same_semantics=True)
    # A family binding preserves the complete generic definition.  Only its
    # contextual binding/use/provenance metadata may differ.
    family = clone("COMPATIBLE_FAMILY_MEMBER", same_semantics=True)
    for binding in family["bindings"]:
        binding["market"] = "VALIDATOR_SYNTHETIC_FAMILY"
        binding["context_selector"] = {
            "market": "VALIDATOR_SYNTHETIC_FAMILY",
            "venue": copy.deepcopy(binding["venue"]),
            "case": "COMPATIBLE_FAMILY_MEMBER",
        }
    family["relations"] = [
        {
            "relation_type": "FAMILY_BINDING_OF",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_FAMILY_COMPATIBILITY_PROOF"],
        }
    ]
    distinct = clone("SIMILAR_BUT_DISTINCT")
    distinct["relations"] = [
        {
            "relation_type": "DISTINCT_FROM",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_DISTINCTION_PROOF"],
        }
    ]
    true_new = clone("TRUE_NEW")
    encoding = clone("QUANTUM_ENCODING_RELATION")
    encoding["definition"]["component_kind"] = "QUANTUM_FORMULATION"
    encoding["definition"]["quantum"].update(
        {
            "applicability_state": "MAPPED_SYNTHETIC_VALIDATION_ONLY",
            "original_economic_problem_ref": base_id,
            "problem_family": "VALIDATOR_BINARY_SELECTION",
            "formulation_candidates": ["VALIDATOR_QUBO_ENCODING"],
            "selected_formulation_or_none": "VALIDATOR_QUBO_ENCODING",
            "variable_encoding": {"x": "BINARY"},
            "objective_map": "minimize negative validated utility over x",
            "constraint_map": ["x in {0,1}"],
            "penalty_policy": "BOUNDED_SYNTHETIC_PENALTY",
            "coefficient_scaling": "IDENTITY_SYNTHETIC_SCALE",
            "precision_and_quantization": "EXACT_SMALL_INSTANCE",
            "decomposition_or_embedding": "NOT_REQUIRED_SMALL_INSTANCE",
            "warm_start": "DETERMINISTIC_ZERO_STATE",
            "optimizer_and_version": "LOCAL_EXACT_ENUMERATION_V1",
            "shots_reads_or_sampling_policy": "NO_QPU_OR_SAMPLING",
            "inverse_map": "x maps directly to the selected binary decision",
            "original_model_feasibility_check": "EXACT_BINARY_DOMAIN_CHECK",
            "same_formulation_classical_comparator": base_id,
            "local_exact_or_small_instance_parity": "STRUCTURAL_FIXTURE_ONLY",
            "fallback": base_id,
            "maturity_ceiling": "SPECIFIED",
        }
    )
    encoding["relations"] = [
        {
            "relation_type": "ENCODES_OR_MAPS",
            "canonical_target_ref": base_id,
            "proof_refs": ["VALIDATOR_STRUCTURAL_MAPPING_ONLY"],
        }
    ]

    marker_items = [
        {"record": exact_duplicate, "case": "EXACT_DUPLICATE"},
        {
            "record": alias,
            "case": "NAME_ALIAS",
            "equivalence_decision": "YES",
            "candidate_alias": "VALIDATOR_NAME_ALIAS",
        },
        {"record": provenance_only, "case": "PROVENANCE_ONLY"},
        {"record": binding_addition, "case": "NEW_BINDING"},
        {"record": parameter_update, "case": "NEW_PARAMETER_POLICY"},
        {
            "record": family,
            "case": "COMPATIBLE_FAMILY_MEMBER",
            "equivalence_decision": "NO",
            "nonidentical_relation": "FAMILY_COMPATIBLE",
        },
        {
            "record": distinct,
            "case": "SIMILAR_BUT_DISTINCT",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {
            "record": true_new,
            "case": "TRUE_NEW",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        {
            "record": encoding,
            "case": "QUANTUM_ENCODING_RELATION",
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
    ]
    signature = inspect.signature(function)

    def invoke(base: Sequence[Mapping[str, Any]], items: Sequence[Mapping[str, Any]], source_order: str, inject_failure: bool) -> Any:
        intended_contexts: dict[str, dict[str, Any]] = {}
        for item in items:
            record = item.get("record", {})
            for binding in record.get("bindings", ()):
                for mode in binding.get("supported_modes", ()):
                    context = {
                        "market": copy.deepcopy(binding.get("market", "ANY")),
                        "venue": copy.deepcopy(binding.get("venue", "ANY")),
                        "mode": str(mode),
                    }
                    intended_contexts[_canonical_json(context)] = context
        batch = {
            "batch_id": f"VALIDATOR_SYNTHETIC_{source_order}",
            "batch_origin": "VALIDATOR_SYNTHETIC_EXPANSION",
            "submitted_by": "CONTROL1_CENTRAL_BUILDER",
            "submission_time": "2000-01-01T00:00:00Z",
            "source_refs": ["tools/validate_pr169_qku_comp_control1.py"],
            "source_classification": "OWNER_SUBMITTED",
            "intended_market_venue_modes": [
                intended_contexts[key] for key in sorted(intended_contexts)
            ],
            "items": list(items),
            "requested_evidence_modes": ["FIXTURE"],
            "requested_promotion_ceiling": "SPECIFIED",
        }
        if inject_failure:
            invalid = copy.deepcopy(template)
            invalid["definition"]["complete_mathematical_or_procedural_definition"] = (
                "MATERIAL_MUTATION_UNDER_EXISTING_ID"
            )
            batch["items"] = [{"record": invalid, "case": "INJECTED_FAILURE"}]
        kwargs: dict[str, Any] = {}
        for key in signature.parameters:
            if key in {"base", "base_records", "accepted_records", "records"}:
                kwargs[key] = base
            elif key in {"batch", "expansion_batch"}:
                kwargs[key] = batch
            elif key in {"items", "batch_items", "synthetic_items"}:
                kwargs[key] = batch["items"]
            elif key in {"source_order", "order_tag"}:
                kwargs[key] = source_order
            elif key in {"inject_failure", "fail_after_stage", "force_failure"}:
                kwargs[key] = inject_failure
        return function(**kwargs) if kwargs else function(base, batch)

    qku_role_rejection = _runtime_error_code(
        lambda: invoke(
            records,
            [{"record": qku_addition, "case": "QKU_ROLE_ADDITION"}],
            "QKU_ROLE_REJECTION",
            False,
        )
    )
    if qku_role_rejection != "NEW_REUSED_QKU_ROLE_REQUIRES_BUILD_OWNED_VERIFIER":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"unverified QKU role -> {qku_role_rejection}",
        )
    implementation_rejection = _runtime_error_code(
        lambda: invoke(
            records,
            [{"record": implementation_update, "case": "NEW_IMPLEMENTATION"}],
            "IMPLEMENTATION_REJECTION",
            False,
        )
    )
    if (
        implementation_rejection
        != "NEW_REUSED_IMPLEMENTATION_REQUIRES_BUILD_OWNED_VERIFIER"
    ):
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"unverified implementation -> {implementation_rejection}",
        )

    forward = _unwrap_records(invoke(records, marker_items, "FORWARD", False))
    reverse = _unwrap_records(invoke(records, list(reversed(marker_items)), "REVERSE", False))
    if forward is None or reverse is None:
        raise InvariantError("COMPILER_PROBE_RESULT", "compiler helper did not return records")
    forward_projection = sorted(forward, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    reverse_projection = sorted(reverse, key=lambda row: (str(row["canonical_component_id"]), str(row["semantic_version"])))
    if _canonical_json(forward_projection) != _canonical_json(reverse_projection):
        raise InvariantError("SOURCE_ORDER_ID_STABILITY", "forward and reverse batch allocation differ")
    failed = False
    try:
        invoke(records, marker_items, "FORWARD", True)
    except Exception:
        failed = True
    if not failed:
        raise InvariantError("FAILED_COMPILE_NOT_REJECTED", "failure injection returned normally")
    forged_alias = copy.deepcopy(marker_items[1])
    forged_alias["record"]["definition"][
        "complete_mathematical_or_procedural_definition"
    ] = "FORGED_CALLER_ASSERTED_SEMANTIC_EQUALITY"
    forged_alias["equivalence_proof_refs"] = [
        "CONTROL1_DIRECT_PROOF::FORGED_CALLER_PASS"
    ]
    forged_alias["trusted_proof_result_id"] = "FORGED.CALLER.PASS"
    forged_proof_code = _runtime_error_code(
        lambda: invoke(records, [forged_alias], "FORGED_CALLER_PROOF", False)
    )
    if forged_proof_code not in {
        "UNPROVEN_EQUIVALENCE",
        "BUILD_OWNED_EQUIVALENCE_PROOF_FAILED",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"forged caller equivalence proof -> {forged_proof_code}",
        )
    if _canonical_json(records) != base_projection:
        raise InvariantError("FAILED_COMPILE_ROLLBACK", "base records changed after injected failure")
    return {
        "synthetic_cases": len(marker_items) + 2,
        "forward_records": len(forward),
        "source_order_stable": True,
        "rollback": True,
        "forged_caller_proof_rejected": forged_proof_code,
        "unverified_qku_role_rejected": qku_role_rejection,
        "unverified_implementation_rejected": implementation_rejection,
        "build_owned_submitter": "CONTROL1_CENTRAL_BUILDER",
    }


def _hardened_contract_probe(
    control_module: Any, records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Independently exercise the hardened compiler/storage/runtime boundaries."""

    template = next(
        (
            copy.deepcopy(record)
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED"
            and record.get("bindings")
            and not record.get("definition", {}).get("requirements")
            and _schema_specs(record.get("definition", {}).get("input_schema"))
            and _schema_specs(record.get("definition", {}).get("output_schema"))
            and not _independent_specification_issues(record.get("definition", {}))
            and all(
                record["bindings"][0].get("readiness", {}).get(dimension) == "PASS"
                for dimension in ("specification", "implementation", "oracle")
            )
            and not _independent_input_source_binding_issues(
                record.get("definition", {}), record["bindings"][0]
            )
        ),
        None,
    )
    if template is None:
        raise InvariantError(
            "HARDENED_CONTRACT_TEMPLATE_MISSING",
            "accepted bound record with direct inputs/outputs is required",
        )

    base = copy.deepcopy(template)
    base["relations"] = []
    base["uses"]["qku_role_bindings"] = []
    base["definition"]["requirements"] = []
    base["record_state"] = "CANONICAL_ACCEPTED"
    binding = base["bindings"][0]
    binding["readiness"]["authorization"] = "NOT_ELIGIBLE"
    binding["activation_state"] = "INACTIVE_NONLIVE"
    binding["rollback_target_or_null"] = None
    binding["terminal_disposition_or_null"] = None
    binding["fallback_policy"] = {"state": "FAIL_CLOSED"}
    binding["selected_requirement_alternatives"] = []

    validate_shape = getattr(control_module, "_validate_record_shape")
    build_snapshot = getattr(control_module, "_build_snapshot")
    derive_delta = getattr(control_module, "_derive_registry_update")
    apply_update = getattr(control_module, "_apply_registry_update")
    compile_batch = getattr(control_module, "_compile_expansion_batch")
    derive_context = getattr(control_module, "_derive_requirement_context")
    write_layout = getattr(control_module, "_write_registry_layout")
    load_layout = getattr(control_module, "_load_logical_registry")
    registry_partitions = getattr(control_module, "_registry_partitions")
    choose_layout = getattr(control_module, "_choose_layout")

    validate_shape(base)
    snapshot = build_snapshot([base], generation=11)

    def update_error(candidate: Mapping[str, Any], batch_id: str) -> str:
        delta = derive_delta([base], [candidate], batch_id=batch_id)
        return _runtime_error_code(
            lambda: apply_update(snapshot, delta, [candidate])
        )

    demoted = copy.deepcopy(base)
    demoted["record_state"] = "PROVISIONAL"
    demotion_code = update_error(demoted, "VALIDATOR.ACCEPTED.DEMOTION")
    if demotion_code != "ACCEPTED_RECORD_STATE_DEMOTION_FORBIDDEN":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"accepted demotion -> {demotion_code}",
        )

    authority = copy.deepcopy(base)
    authority["bindings"][0]["readiness"]["authorization"] = "AUTHORIZED"
    authority["bindings"][0]["activation_state"] = "ACTIVE"
    authority_code = update_error(authority, "VALIDATOR.AUTHORITY.GRANT")
    if authority_code not in {
        "BINDING_AUTHORITY_CHANGE_FORBIDDEN",
        "BINDING_AUTHORITY_GRANT_FORBIDDEN",
    }:
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"accepted authority grant -> {authority_code}",
        )

    source_ref = "tools/validate_pr169_qku_comp_control1.py"

    def provenance(case: str, target: str) -> dict[str, Any]:
        return {
            "source_artifact_ref": source_ref,
            "source_row_ref": case,
            "source_local_identity_or_name": case,
            "source_fields_consumed": ["independent_hardened_contract_probe"],
            "source_relation": "VALIDATION_ONLY",
            "canonical_target_ref": target,
            "proof_refs": [source_ref],
        }

    def batch(
        items: Sequence[Mapping[str, Any]],
        case: str,
        *,
        ceiling: str = "SPECIFIED",
        evidence_modes: Sequence[str] = ("FIXTURE",),
    ) -> dict[str, Any]:
        return {
            "batch_id": f"VALIDATOR.HARDENED.{case}",
            "batch_origin": "VALIDATOR_SYNTHETIC_EXPANSION",
            "submitted_by": "CONTROL1_CENTRAL_BUILDER",
            "submission_time": "2000-01-01T00:00:00Z",
            "source_refs": [source_ref],
            "source_classification": "OWNER_SUBMITTED",
            "intended_market_venue_modes": [],
            "items": list(items),
            "requested_evidence_modes": list(evidence_modes),
            "requested_promotion_ceiling": ceiling,
        }

    apply_envelope = getattr(control_module, "_apply_expansion_envelope_to_candidate")
    validate_envelope = getattr(control_module, "_validate_expansion_envelope")
    batch_type = getattr(control_module, "ExpansionBatchV1")

    def promotion_candidate(state: str, case: str) -> dict[str, Any]:
        candidate = copy.deepcopy(base)
        candidate_id = f"QTT.COMP.VALIDATION.PROMOTION.{case}"
        candidate["canonical_component_id"] = candidate_id
        candidate["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        candidate["provenance"] = [provenance(case, candidate_id)]
        candidate["uses"]["qku_role_bindings"] = []
        candidate_binding = candidate["bindings"][0]
        candidate_binding["binding_id"] = f"BINDING.VALIDATION.PROMOTION.{case}"
        candidate_binding["readiness"] = {
            "specification": "PASS",
            "implementation": "PASS",
            "inputs": "REQUIRED",
            "requirements": "REQUIRED",
            "oracle": "PASS",
            "context": "REQUIRED",
            "evidence": "NONE",
            "authorization": "NOT_ELIGIBLE",
        }
        candidate_binding["activation_state"] = "INACTIVE_NONLIVE"
        if state in {"STACK_READY", "EVIDENCED", "AUTHORIZED"}:
            for dimension in ("inputs", "requirements", "context"):
                candidate_binding["readiness"][dimension] = "PASS"
        if state in {"EVIDENCED", "AUTHORIZED"}:
            candidate_binding["readiness"]["evidence"] = "PAPER"
        if state == "AUTHORIZED":
            candidate_binding["readiness"]["authorization"] = "AUTHORIZED"
            candidate_binding["activation_state"] = "ACTIVE"
        return candidate

    promotion_cases = {
        "NOT_ELIGIBLE": "VERIFIED",
        "SPECIFIED": "VERIFIED",
        "VERIFIED": "STACK_READY",
        "CONTEXT_READY": "STACK_READY",
        "STACK_READY": "EVIDENCED",
        "EVIDENCED": "AUTHORIZED",
    }
    promotion_codes: dict[str, str] = {}
    for ceiling, attempted_state in promotion_cases.items():
        candidate = promotion_candidate(attempted_state, ceiling)
        envelope = batch(
            [],
            f"PROMOTION.{ceiling}",
            ceiling=ceiling,
            evidence_modes=("FIXTURE", "PAPER"),
        )
        envelope_value = batch_type.from_mapping(envelope)
        validate_envelope(envelope_value)
        code = _runtime_error_code(
            lambda candidate=candidate, envelope_value=envelope_value: apply_envelope(
                candidate, batch=envelope_value, existing=None
            )
        )
        if code not in {
            "EXPANSION_STATE_EXCEEDS_CEILING",
            "EXPANSION_AUTHORIZATION_EXCEEDS_CEILING",
            "EXPANSION_MODE_AUTHORIZATION_EXCEEDS_CEILING",
        }:
            raise InvariantError(
                "RUNTIME_DEFECT_WRONG_REASON",
                f"promotion {attempted_state} under {ceiling} -> {code}",
            )
        promotion_codes[ceiling] = code
    authorized = promotion_candidate("AUTHORIZED", "AUTHORIZED")
    authorized_envelope = batch_type.from_mapping(
        batch(
            [],
            "PROMOTION.AUTHORIZED",
            ceiling="AUTHORIZED",
            evidence_modes=("FIXTURE", "PAPER"),
        )
    )
    validate_envelope(authorized_envelope)
    apply_envelope(authorized, batch=authorized_envelope, existing=None)
    promotion_codes["AUTHORIZED"] = "ALLOWED_AT_DECLARED_CEILING"

    raw_item = {
        "candidate_identity": "VALIDATOR_RAW_MATERIALIZATION",
        "component_kind": "DETERMINISTIC_TRANSFORM",
        "complete_mathematical_or_procedural_definition": "y = x + 1",
        "input_schema": [
            {"name": "x", "type": "DECIMAL", "unit": "UNITLESS", "required": True}
        ],
        "output_schema": [
            {"name": "y", "type": "DECIMAL", "unit": "UNITLESS", "required": True}
        ],
        "units_and_bases": {"x": "UNITLESS", "y": "UNITLESS"},
        "domain_and_boundary_behavior": {"domain": "finite decimal", "invalid": "FAIL_CLOSED"},
        "state_and_time_semantics": {"state": "STATELESS", "time": "SAME_REQUEST"},
        "decision_roles": ["INTERNAL_SUPPORT"],
        "decision_outputs": ["y"],
        "equivalence_decision": "NO",
        "nonidentical_relation": "DISTINCT",
    }
    raw_result = _unwrap_records(
        compile_batch([], batch([raw_item], "RAW.MATERIALIZATION", evidence_modes=()))
    )
    if raw_result is None or len(raw_result) != 1:
        raise InvariantError("RAW_MATERIALIZATION_RESULT", repr(raw_result))
    raw_record = raw_result[0]
    if (
        raw_record.get("canonical_component_id")
        != "QTT.COMP.EXPANSION.VALIDATOR_RAW_MATERIALIZATION"
        or raw_record.get("record_state") != "PROVISIONAL"
        or raw_record.get("definition", {}).get(
            "complete_mathematical_or_procedural_definition"
        )
        != "y = x + 1"
    ):
        raise InvariantError("RAW_MATERIALIZATION_RESULT", repr(raw_record))
    incomplete_raw = copy.deepcopy(raw_item)
    incomplete_raw.pop("domain_and_boundary_behavior")
    incomplete_raw_code = _runtime_error_code(
        lambda: compile_batch(
            [], batch([incomplete_raw], "RAW.INCOMPLETE", evidence_modes=())
        )
    )
    if incomplete_raw_code != "INCOMPLETE_RAW_EXPANSION_ITEM":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"incomplete raw materialization -> {incomplete_raw_code}",
        )

    def candidate_record(case: str) -> dict[str, Any]:
        candidate = copy.deepcopy(base)
        candidate_id = f"QTT.COMP.VALIDATION.SELECTOR.{case}"
        candidate["canonical_component_id"] = candidate_id
        candidate["record_state"] = "PROVISIONAL"
        candidate["origin_cohorts"] = ["VALIDATOR_SYNTHETIC_EXPANSION"]
        candidate["definition"]["display_name"] = f"Selector {case}"
        candidate["definition"]["description"] = f"Selector probe {case}"
        candidate["definition"][
            "complete_mathematical_or_procedural_definition"
        ] = f"VALIDATOR_SELECTOR_PROCEDURE::{case}"
        candidate["definition"]["requirements"] = []
        candidate["bindings"] = []
        candidate["exact_resolution_action"] = (
            f"MISSING_CONTEXTUAL_BINDING: {candidate_id}"
        )
        candidate["provenance"] = [provenance(case, candidate_id)]
        candidate["relations"] = []
        candidate["uses"]["qku_role_bindings"] = []
        return candidate

    base_local = copy.deepcopy(base)
    local_selector = "VALIDATOR::BASE_LOCAL_SELECTOR"
    base_local["provenance"] = [
        {
            **provenance("BASE_LOCAL", str(base_local["canonical_component_id"])),
            "source_local_identity_or_name": local_selector,
        }
    ]
    dependent = candidate_record("BASE_DEPENDENT")
    producer_output, producer_spec = next(
        iter(_schema_specs(base_local["definition"]["output_schema"]).items())
    )
    producer_unit = str(
        producer_spec.get("unit", producer_spec.get("units", "UNSPECIFIED"))
    )
    dependent["definition"]["input_schema"] = [
        {
            "name": "upstream_value",
            "type": producer_spec.get("type", "ANY"),
            "unit": producer_unit,
            "required": True,
        }
    ]
    dependent["definition"]["units_and_bases"] = {
        "upstream_value": producer_unit,
        **{
            name: spec.get("unit", spec.get("units", "UNSPECIFIED"))
            for name, spec in _schema_specs(
                dependent["definition"]["output_schema"]
            ).items()
        },
    }
    dependent["definition"]["requirements"] = [
        {
            "required_component_id_or_source_selector": local_selector,
            "required_semantic_version_constraint": f"=={base_local['semantic_version']}",
            "requirement_role": "VALIDATOR_BASE_SEEDED_SELECTOR",
            "required_or_optional": "REQUIRED",
            "producer_output_name": producer_output,
            "consumer_input_name": "upstream_value",
            "unit_or_basis_conversion": "IDENTITY",
            "timing_and_freshness_constraint": "SAME_REQUEST",
            "activation_condition": "ALWAYS",
            "fallback_component_id_or_null": None,
            "failure_behavior": "FAIL_CLOSED",
        }
    ]
    seeded_result = _unwrap_records(
        compile_batch(
            [base_local],
            batch(
                [
                    {
                        "record": dependent,
                        "equivalence_decision": "NO",
                        "nonidentical_relation": "DISTINCT",
                    }
                ],
                "SELECTOR.BASE_SEEDED",
                evidence_modes=(),
            ),
        )
    )
    seeded_dependent = next(
        record
        for record in seeded_result or ()
        if record["canonical_component_id"] == dependent["canonical_component_id"]
    )
    seeded_target = seeded_dependent["definition"]["requirements"][0][
        "required_component_id_or_source_selector"
    ]
    if seeded_target != base_local["canonical_component_id"]:
        raise InvariantError(
            "BASE_SEEDED_SOURCE_SELECTOR", f"resolved={seeded_target!r}"
        )

    selector_a = candidate_record("COLLISION_A")
    selector_b = candidate_record("COLLISION_B")
    selector_dep = candidate_record("COLLISION_DEP")
    selector_dep["definition"]["requirements"] = copy.deepcopy(
        dependent["definition"]["requirements"]
    )
    selector_dep["definition"]["requirements"][0][
        "required_component_id_or_source_selector"
    ] = "VALIDATOR::COLLIDING_SELECTOR"
    selector_dep["definition"]["input_schema"] = copy.deepcopy(
        dependent["definition"]["input_schema"]
    )
    selector_dep["definition"]["units_and_bases"] = copy.deepcopy(
        dependent["definition"]["units_and_bases"]
    )
    collision_items = {
        "A": {
            "record": selector_a,
            "source_selector_aliases": ["VALIDATOR::COLLIDING_SELECTOR"],
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
        "B": {
            "record": selector_b,
            "source_selector_aliases": ["VALIDATOR::COLLIDING_SELECTOR"],
            "equivalence_decision": "NO",
            "nonidentical_relation": "DISTINCT",
        },
    }
    collision_codes: list[str] = []
    for order in (("A", "B"), ("B", "A")):
        items = [collision_items[name] for name in order]
        items.append(
            {
                "record": selector_dep,
                "equivalence_decision": "NO",
                "nonidentical_relation": "DISTINCT",
            }
        )
        code = _runtime_error_code(
            lambda items=items, order=order: compile_batch(
                [],
                batch(
                    items,
                    f"SELECTOR.COLLISION.{''.join(order)}",
                    evidence_modes=(),
                ),
            )
        )
        if code != "AMBIGUOUS_SOURCE_SELECTOR":
            raise InvariantError(
                "RUNTIME_DEFECT_WRONG_REASON",
                f"selector collision {order} -> {code}",
            )
        collision_codes.append(code)

    nested_parameter = copy.deepcopy(base)
    nested_parameter["definition"][
        "parameter_schema_and_default_provenance"
    ] = {
        "parameters": [
            {
                "name": "validator_alpha",
                "type": "INTEGER",
                "unit": "UNITLESS",
                "minimum": 0,
                "maximum": 1,
                "default": 1,
                "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
            }
        ],
        "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
    }
    nested_parameter["bindings"][0]["selected_parameter_policy"] = {
        "policy_id": "PARAM.VALIDATOR.NESTED",
        "version": "1.0",
        "defaults": {"validator_alpha": 1},
        "default_provenance": "CONTROL1_INDEPENDENT_VALIDATOR",
    }
    validate_shape(nested_parameter)
    invalid_parameter = copy.deepcopy(nested_parameter)
    invalid_parameter["bindings"][0]["selected_parameter_policy"]["defaults"][
        "validator_alpha"
    ] = 2
    nested_parameter_code = _runtime_error_code(
        lambda: validate_shape(invalid_parameter)
    )
    if nested_parameter_code != "ABOVE_MAXIMUM":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"nested parameter default -> {nested_parameter_code}",
        )

    context_binding = copy.deepcopy(base["bindings"][0])
    context_binding["requirement_context_policy"] = {
        "inherit_root_context": True,
        "include_fields": ["market", "venue", "mode", "request_time"],
        "overrides": {"context_family": "VALIDATOR_PINNED_REQUIREMENT"},
    }
    context_requirement = copy.deepcopy(dependent["definition"]["requirements"][0])
    context_requirement["timing_and_freshness_constraint"] = (
        "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
    )
    pinned_context = derive_context(
        {
            "market": "VALIDATOR",
            "venue": "LOCAL",
            "mode": "TEST_VECTOR",
            "request_time": "2000-01-01T00:00:00Z",
            "binding_id": "CALLER_MUST_NOT_PIN",
        },
        consumer_binding=context_binding,
        requirement=context_requirement,
        target_component_id=str(base["canonical_component_id"]),
    )
    if (
        pinned_context.get("canonical_component_id") != base["canonical_component_id"]
        or pinned_context.get("request_scope") != "SAME_REQUEST"
        or pinned_context.get("requirement_timing_policy")
        != "SAME_REQUEST_IMMUTABLE_INPUT_LOCK"
        or pinned_context.get("input_lock_policy") != "IMMUTABLE"
        or pinned_context.get("binding_id") is not None
        or pinned_context.get("context_family")
        != "VALIDATOR_PINNED_REQUIREMENT"
    ):
        raise InvariantError("REQUIREMENT_CONTEXT_NOT_PINNED", repr(pinned_context))
    invalid_timing = copy.deepcopy(context_requirement)
    invalid_timing["timing_and_freshness_constraint"] = "CALLER_SELECTED_LATEST"
    invalid_timing_code = _runtime_error_code(
        lambda: derive_context(
            {},
            consumer_binding=context_binding,
            requirement=invalid_timing,
            target_component_id=str(base["canonical_component_id"]),
        )
    )
    if invalid_timing_code != "UNSUPPORTED_REQUIREMENT_TIMING_POLICY":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"requirement timing -> {invalid_timing_code}",
        )

    quantum = copy.deepcopy(base)
    quantum["canonical_component_id"] = "QTT.COMP.QUANTUM.VALIDATOR_SELF_ASSERTED"
    quantum["definition"]["component_kind"] = "QUANTUM_FORMULATION"
    quantum["definition"]["quantum"].update(
        {
            "applicability_state": "APPLICABLE",
            "original_economic_problem_ref": "SELF_ASSERTED_ORIGINAL",
            "problem_family": "QUBO",
            "formulation_candidates": ["QUBO"],
            "selected_formulation_or_none": "QUBO",
            "variable_encoding": {"x": "BINARY"},
            "objective_map": "SELF_ASSERTED_OBJECTIVE",
            "constraint_map": ["SELF_ASSERTED_CONSTRAINT"],
            "inverse_map": "SELF_ASSERTED_INVERSE",
            "same_formulation_classical_comparator": "SELF_ASSERTED_COMPARATOR",
            "local_exact_or_small_instance_parity": {
                "result": "PASS",
                "authority": "CALLER",
            },
            "fallback": "SELF_ASSERTED_FALLBACK",
            "maturity_ceiling": "LOCAL_EXACT_PARITY",
        }
    )
    quantum_code = _runtime_error_code(lambda: validate_shape(quantum))
    if quantum_code != "QUANTUM_MATURITY_REQUIRES_INDEPENDENT_PROMOTION_AUTHORITY":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"self-asserted quantum parity -> {quantum_code}",
        )

    with tempfile.TemporaryDirectory(prefix="qtt-control1-manifest-") as temporary:
        registry_root = Path(temporary) / "registry"
        write_layout([base], registry_root, force_layout="sharded")
        manifest_path = registry_root / "registry.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["partitions"][0]["range_start"] = "ZZZ.INVALID.START"
        manifest["partitions"][0]["range_end"] = "AAA.INVALID.END"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )
        manifest_code = _runtime_error_code(lambda: load_layout(registry_root))
    if manifest_code != "REGISTRY_MANIFEST_PARTITION_DERIVATION_MISMATCH":
        raise InvariantError(
            "RUNTIME_DEFECT_WRONG_REASON",
            f"manifest range tamper -> {manifest_code}",
        )

    original_policy = control_module.STORAGE_POLICY
    try:
        split_policy = dict(original_policy)
        split_policy["rp5c_rows_per_stable_partition"] = 2
        split_policy["diff_size_budget_bytes"] = 1_000_000_000
        control_module.STORAGE_POLICY = MappingProxyType(split_policy)
        compact_records = [
            {
                "canonical_component_id": f"QTT.COMP.FORMULA.{suffix}",
                "semantic_version": "1.0",
            }
            for suffix in ("ALPHA", "BETA", "GAMMA")
        ]
        partitions = registry_partitions(compact_records)
        reverse_partitions = registry_partitions(list(reversed(compact_records)))
        partition_projection = [partition.manifest_row() for partition in partitions]
        reverse_projection = [
            partition.manifest_row() for partition in reverse_partitions
        ]
        if len(partitions) <= 1 or partition_projection != reverse_projection:
            raise InvariantError(
                "STABLE_OVERFLOW_PARTITIONING",
                f"forward={partition_projection!r}, reverse={reverse_projection!r}",
            )
        with_unrelated = registry_partitions(
            [
                *compact_records,
                {
                    "canonical_component_id": "QTT.COMP.ALGORITHM.UNRELATED",
                    "semantic_version": "1.0",
                },
            ]
        )
        formula_before = [
            partition.manifest_row()
            for partition in partitions
            if partition.token.startswith("formula")
        ]
        formula_after = [
            partition.manifest_row()
            for partition in with_unrelated
            if partition.token.startswith("formula")
        ]
        if formula_before != formula_after:
            raise InvariantError(
                "UNRELATED_SHARD_CHURN",
                f"before={formula_before!r}, after={formula_after!r}",
            )
    finally:
        control_module.STORAGE_POLICY = original_policy

    measurement_to_policy = {
        "row_count": "single_file_max_rows",
        "serialized_bytes": "single_file_max_serialized_bytes",
        "maximum_record_serialized_bytes": "max_record_serialized_bytes",
        "load_ms": "single_file_max_load_ms",
        "index_build_ms": "single_file_max_index_build_ms",
        "validation_ms": "single_file_max_validation_ms",
        "diff_candidate_bytes": "diff_size_budget_bytes",
    }
    baseline_measurements = {name: 0 for name in measurement_to_policy}
    if choose_layout([], measurements=baseline_measurements) != "single":
        raise InvariantError(
            "CENTRAL_MEASURED_STORAGE_POLICY", "zero measurements did not select single"
        )
    measured_dimensions: list[str] = []
    for measurement_name, policy_name in measurement_to_policy.items():
        measurements = dict(baseline_measurements)
        measurements[measurement_name] = float(original_policy[policy_name]) + 1
        if choose_layout([], measurements=measurements) != "sharded":
            raise InvariantError(
                "CENTRAL_MEASURED_STORAGE_POLICY",
                f"ignored {measurement_name}/{policy_name}",
            )
        measured_dimensions.append(measurement_name)

    return {
        "accepted_state_demotion": demotion_code,
        "accepted_authority_grant": authority_code,
        "promotion_ceiling_cases": promotion_codes,
        "raw_materialization": raw_record["canonical_component_id"],
        "incomplete_raw_rejected": incomplete_raw_code,
        "base_seeded_selector_target": seeded_target,
        "collision_order_independent_rejection": collision_codes,
        "nested_parameter_schema": nested_parameter_code,
        "requirement_context_timing": invalid_timing_code,
        "quantum_self_assertion": quantum_code,
        "manifest_range_tamper": manifest_code,
        "stable_overflow_shards": len(partitions),
        "central_measured_storage_dimensions": measured_dimensions,
    }


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = _JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--timeout-ms", type=int, default=3_600_000)
    parser.add_argument("--scale-probe-records", type=int, default=10_000)
    args = parser.parse_args(argv)
    if args.timeout_ms <= 0:
        parser.error("--timeout-ms must be positive")
    if args.scale_probe_records < 0:
        parser.error("--scale-probe-records must be zero or positive")
    return args


def validate(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    artifact_dir = args.artifact_dir
    if not artifact_dir.is_absolute():
        artifact_dir = (repo_root / artifact_dir).resolve()
    deadline = Deadline(args.timeout_ms)
    audit = Audit(deadline)

    imported = audit.capture("public_facade_architecture", lambda: _import_control(repo_root))
    if imported is None:
        return _result(audit)
    _, control_module, facade_class = imported

    decimal_contract = audit.capture(
        "closed_decimal_context_rounding_and_boundary_contract",
        lambda: _validate_closed_decimal_native_contract(control_module),
    )
    if decimal_contract is not None:
        audit.metrics["closed_decimal_contract"] = decimal_contract

    loaded = audit.capture("logical_registry_layout_and_load", lambda: _load_logical_records(control_module, artifact_dir))
    if loaded is None:
        return _result(audit)
    records, layout, physical_count = loaded
    audit.metrics.update(
        {
            "logical_registry_rows": len(records),
            "active_physical_layout": layout,
            "active_registry_data_file_count": physical_count,
            "serialized_registry_bytes": sum(path.stat().st_size for path in artifact_dir.glob("registry*.json*")),
        }
    )

    def shape_validation() -> None:
        seen: set[tuple[str, str]] = set()
        binding_ids: set[str] = set()
        for index, record in enumerate(records):
            if index % 500 == 0:
                deadline.check("record_shape")
            _validate_record(record)
            key = (str(record["canonical_component_id"]), str(record["semantic_version"]))
            if key in seen:
                raise InvariantError("CANONICAL_ID_VERSION_DUPLICATE", repr(key))
            seen.add(key)
            for binding in record["bindings"]:
                binding_id = str(binding["binding_id"])
                if binding_id in binding_ids:
                    raise InvariantError("BINDING_ID_DUPLICATE", binding_id)
                binding_ids.add(binding_id)

    audit.capture("record_schema_and_uniqueness", shape_validation)
    source_universe = audit.capture(
        "independent_row_level_computation_universe_closure",
        lambda: _validate_source_universe_closure(repo_root, records, deadline),
    )
    if source_universe is not None:
        audit.metrics["computation_universe_row_level_closure"] = source_universe
        no_orphan = audit.capture(
            "active_agent_source_no_orphan_closure",
            lambda: _validate_no_orphan_closure(records, source_universe),
        )
        if no_orphan is not None:
            audit.metrics["no_orphan"] = no_orphan
        status_explain_probe = audit.capture(
            "operation_scoped_status_explain_qku_surface",
            lambda: _validate_status_explain_only_qku_surface(
                facade_class,
                records,
                source_universe,
                deadline,
            ),
        )
        if status_explain_probe is not None:
            audit.metrics["operation_scoped_status_explain_qku_surface"] = (
                status_explain_probe
            )

    accepted_group_map: Mapping[tuple[str, ...], str] | None = None
    accepted_base_records = audit.capture(
        "accepted_merge_base_registry",
        lambda: _load_accepted_base_records(control_module, repo_root, deadline),
    )
    if accepted_base_records:
        accepted_group_map = audit.capture(
            "accepted_merge_base_rp5c_stable_group_map",
            lambda: _registry_rp5c_group_map(accepted_base_records),
        )
    canonical_artifact_dir = (repo_root / DEFAULT_ARTIFACT_DIR).resolve()
    if (
        accepted_group_map is None
        and artifact_dir != canonical_artifact_dir
        and canonical_artifact_dir.is_dir()
    ):
        accepted_loaded = audit.capture(
            "canonical_candidate_registry_for_layout_parity",
            lambda: _load_logical_records(control_module, canonical_artifact_dir),
        )
        if accepted_loaded is not None:
            accepted_group_map = audit.capture(
                "canonical_candidate_rp5c_stable_group_map",
                lambda: _registry_rp5c_group_map(accepted_loaded[0]),
            )

    graph_pair = audit.capture("requirements_canonical_and_acyclic", lambda: _graph(records))
    graph: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = {}
    if graph_pair is not None:
        graph, reverse = graph_pair
        order = audit.capture("requirements_topological_order", lambda: _topological(graph))
        if order is not None:
            audit.metrics["canonical_dag_nodes"] = len(order)
            audit.metrics["canonical_requirement_edges"] = sum(map(len, graph.values()))
    qku_keys = audit.capture("qku_context_root_unambiguity", lambda: _validate_qku_unambiguity(records))
    if qku_keys is not None:
        audit.metrics["active_qku_context_keys"] = qku_keys
    qku_verification = audit.capture(
        "qku_verification_receipt_coverage",
        lambda: _validate_qku_verification_receipts(
            records,
            repo_root=repo_root,
            deadline=deadline,
            source_universe=source_universe,
        ),
    )
    if qku_verification is not None:
        audit.metrics["qku_verification"] = qku_verification
        qku_source_packs = audit.capture(
            "qku_claim_family_source_packs_and_crosswalk",
            lambda: _validate_qku_acceptance_source_packs(
                artifact_dir,
                records,
                qku_verification,
            ),
        )
        if qku_source_packs is not None:
            audit.metrics["qku_claim_family_source_packs"] = qku_source_packs

    rp5c = audit.capture("rp5c_source_reconstruction", lambda: _rp5c_source(repo_root, deadline))
    if rp5c is not None:
        groups, _ = rp5c
        coverage = audit.capture(
            "rp5c_exact_import_and_member_coverage",
            lambda: _validate_rp5c_import(
                records, groups, deadline, accepted_group_map
            ),
        )
        if coverage is not None:
            audit.metrics["rp5c_canonical_imports"] = coverage[0]
            audit.metrics["rp5c_duplicate_members_covered"] = coverage[1]
            audit.metrics["rp5c_inner_source_artifact_ref_sets"] = len(
                groups
            )
            audit.metrics["rp5c_inner_source_artifact_ref_total"] = sum(
                len(group["inner_source_artifact_refs"])
                for group in groups.values()
            )
            rp5c_ref_mutations = audit.capture(
                "rp5c_inner_source_ref_missing_extra_mutations",
                lambda: _validate_rp5c_inner_source_ref_mutations(
                    records, groups, deadline, accepted_group_map
                ),
            )
            if rp5c_ref_mutations is not None:
                audit.metrics["rp5c_inner_source_ref_mutation_rejections"] = (
                    rp5c_ref_mutations
                )
        compaction = audit.capture(
            "rp5c_deterministic_uncompacted_counterfactual",
            lambda: _validate_rp5c_compaction_counterfactual(
                records, groups, deadline
            ),
        )
        if compaction is not None:
            audit.metrics["rp5c_lineage_compaction"] = compaction
    owner_count = audit.capture("owner_requirement_213_coverage", lambda: _owner_requirement_coverage(records))
    if owner_count is not None:
        audit.metrics["owner_requirement_ids"] = owner_count

    implementation = audit.capture("implementation_inventory_and_safe_dispatch", lambda: _validate_implementation_inventory(records))
    implementation_records: list[Mapping[str, Any]] = []
    if implementation is not None:
        counts, implementation_records = implementation
        audit.metrics["implementation_records"] = counts
    closed_fixture_contracts = audit.capture(
        "closed_fixture_source_contracts",
        lambda: _validate_closed_fixture_source_contracts(repo_root, records),
    )
    if closed_fixture_contracts is not None:
        audit.metrics["closed_fixture_source_contracts"] = (
            closed_fixture_contracts
        )
    agent_count = audit.capture("pr165_d2_exact_agent_policies", lambda: _validate_agent_policies(records))
    if agent_count is not None:
        audit.metrics["pr165_d2_agent_ids"] = agent_count
    audit.capture("no_qpu_live_replay_paper_authority_claims", lambda: _validate_authority_absence(records))
    reuse = audit.capture("semantic_reuse_direct_proof_cases", lambda: _validate_semantic_reuse(records))
    if reuse is not None:
        audit.metrics["semantic_relation_counts"] = reuse

    template = next(
        (
            record
            for record in records
            if record.get("record_state") == "CANONICAL_ACCEPTED" and record.get("bindings")
        ),
        None,
    )
    if template is None:
        audit.fail("VALIDATION_TEMPLATE_MISSING", "no accepted bound record")
    else:
        defects = audit.capture("defect_injection_rejects_correct_reason", lambda: _defect_injection(template))
        if defects is not None:
            audit.metrics["defect_injections"] = defects
        memoization = audit.capture(
            "selected_subgraph_memoization_nonreuse_and_runtime_defects",
            lambda: _common_subgraph_probe(facade_class, template),
        )
        if memoization is not None:
            audit.metrics["common_subgraph_probe"] = memoization

    facade = audit.capture("public_facade_initialization", lambda: _construct_facade(facade_class, artifact_dir))
    invoked: list[tuple[Mapping[str, Any], Any, Any]] = []
    if facade is not None and implementation_records:
        fixture_result = audit.capture(
            "registered_implementation_dispositions_and_ready_fixture_compute",
            lambda: _invoke_implementation_fixtures(facade, control_module, implementation_records, deadline),
        )
        if fixture_result is not None:
            registered_count, facade_count, status_explain_count, invoked = fixture_result
            audit.metrics.update(
                {
                    "registered_implementation_inventory_dispositions": registered_count,
                    "registered_implementation_fixtures_invoked": facade_count,
                    "verified_facade_fixture_computations": facade_count,
                    "incomplete_implementation_status_explain_only": status_explain_count,
                }
            )
        if graph and invoked:
            subgraph = audit.capture(
                "closed_stack_selected_subgraph_compute",
                lambda: _validate_selected_subgraph(invoked, graph, len(records)),
            )
            if subgraph is not None:
                audit.metrics["representative_selected_subgraph_nodes"] = subgraph[0]
                audit.metrics["representative_selected_subgraph_requirements"] = subgraph[1]
        counters = audit.capture("zero_post_init_reads_scans_unrelated_execution", lambda: _validate_runtime_counters(facade))
        if counters is not None:
            audit.metrics.update(
                {
                    "runtime_registry_file_reads_after_initialization": counters[0],
                    "per_request_full_registry_iterations": counters[1],
                    "unrelated_component_executions": counters[2],
                }
            )

    delta = candidate = changed_id = None
    if reverse:
        delta_result = audit.capture("transient_delta_exactness", lambda: _validate_delta(control_module, records, reverse))
        if delta_result is not None:
            delta, candidate, changed_id = delta_result
            audit.metrics["delta_changed_component"] = changed_id
            audit.capture(
                "incremental_index_full_rebuild_parity_and_idempotence",
                lambda: _validate_index_parity(control_module, records, candidate, delta),
            )
    if template is not None:
        observations = audit.capture(
            "atomic_snapshot_replacement_concurrency",
            lambda: _bounded_snapshot_concurrency_probe(control_module, facade_class, template),
        )
        if observations is not None:
            audit.metrics["snapshot_concurrent_observations"] = observations

    compiler = audit.capture("compiler_source_order_and_failed_rollback", lambda: _compiler_mechanism_probe(control_module, records))
    if compiler is not None:
        audit.metrics["compiler_probe"] = compiler
    hardened = audit.capture(
        "hardened_compiler_storage_runtime_contract",
        lambda: _hardened_contract_probe(control_module, records),
    )
    if hardened is not None:
        audit.metrics["hardened_contract_probe"] = hardened

    if template is not None:
        mandatory_scale = audit.capture(
            "synthetic_2000_single_shard_scale_proof",
            lambda: _scale_probe(control_module, facade_class, 2_000, deadline),
        )
        if mandatory_scale is not None:
            audit.metrics["synthetic_2000_probe"] = mandatory_scale
        if args.scale_probe_records:
            larger = audit.capture(
                "larger_opt_in_scale_probe",
                lambda: _scale_probe(
                    control_module,
                    facade_class,
                    args.scale_probe_records,
                    deadline,
                ),
            )
            if larger is not None:
                audit.metrics["larger_scale_probe"] = larger
        else:
            audit.checks["larger_opt_in_scale_probe"] = True
            audit.metrics["larger_scale_probe"] = {"records": 0, "skipped": True}
    return _result(audit)


def _result(audit: Audit) -> dict[str, Any]:
    return {
        "validator": "PR169-QKU-COMP-CONTROL1",
        "validator_version": "5.1",
        "status": "PASS" if audit.error_count == 0 else "FAIL",
        "elapsed_ms": audit.deadline.elapsed_ms,
        "checks": audit.checks,
        "metrics": audit.metrics,
        "error_count": audit.error_count,
        "errors": audit.errors,
        "acceptance_report_trusted": False,
        "report_files_written": 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        result = validate(args)
    except Exception as exc:  # last-resort JSON-only failure boundary
        result = {
            "validator": "PR169-QKU-COMP-CONTROL1",
            "validator_version": "5.1",
            "status": "FAIL",
            "error_count": 1,
            "errors": [{"code": "VALIDATOR_UNHANDLED", "detail": f"{type(exc).__name__}: {exc}"}],
            "acceptance_report_trusted": False,
            "report_files_written": 0,
        }
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
    sys.stdout.write("\n")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
