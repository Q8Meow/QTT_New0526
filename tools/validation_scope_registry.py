#!/usr/bin/env python3
"""Centralized narrow changed-path scope registry for validation guards."""

from __future__ import annotations

from fnmatch import fnmatchcase


PR168_GFP_BRANCH = "pr168-gfp-global-formula-discovery-real-computation"
PR168_RP_BRANCH = "pr168-rp-formula-based-replay-paper-recompute"
PR168_RANK_BRANCH = "pr168-rank-evidence-backed-ranking"
PR168_DATA1_BRANCH = "pr168-data1-public-market-data-snapshots"
PR168_DATA1A_BRANCH = "pr168-data1a-focused-audit-gfp2r-readiness"
PR168_GFP2R_BRANCH = "pr168-gfp2r-data1a-gated-candidate-recompute"
PR168_RP2_BRANCH = "pr168-rp2-map2-gfp2r-replay-paper-recompute"
PR168_MAP3_BRANCH = "pr168-map3-qku-formula-id-intake"
PR168_RP3_BRANCH = "pr168-rp3-map3-formula-replay-paper-evidence"
PR168_RANK3_BRANCH = "pr168-rank3-rp3-evidence-stack-ranking"
PR168_RP5A_BRANCH = "pr168-rp5a-legacy-semantic-audit"
PR168_RP5B_BRANCH = "pr168-rp5b-active-registry-safe-legacy-cleanup"
PR168_RP5C_BRANCH = "pr168-rp5c-immutable-qku-formula-library"
PR168_RP5C_POST_MERGE_REPAIR_BRANCH = "pr168-rp5c-postmerge-ci-repair"
PR168_VS1_BRANCH = "pr168-vs1-trading-intelligence-vertical-slice"
PR168_RP5D_BRANCH = "pr168-rp5d-replay-paper-executability-tiers"
PR168_RP5E_BRANCH = "pr168-rp5e-stack-gen"
PR168_RP5D_R1_BRANCH = "pr168-rp5d-r1-exec-now-unlock"
PR168_RP5F_BRANCH = "pr168-rp5f-dynamic-target-order-grid"
PR168_RP5G_BRANCH = "pr168-rp5g-trade-plan-sim-engine"
PR168_RANK4_BRANCH = "pr168-rank4-exec-advisory-ranking"
PR168_QOPT1_BRANCH = "pr168-qopt1-quantum-classical-batch-optimization"
PR168_VS2_BRANCH = "pr168-vs2-paper-intent-candidate-generator"
PR168_MEM1_BRANCH = "pr168-mem1-condition-scoped-outcome-memory"
PR169_DASH1_BRANCH = "pr169-dash1-owner-dashboard-interactive-research-v6"
PR169_DASH1_UI1_BRANCH = "pr169-dash1-ui1-theme-switch-safe-renderer-v9"
PR169_DASH1_UI1_R1_BRANCH = "pr169-dash1-ui1-r1-v3-owner12"
VALIDATION_FIXTURE_BRANCH = "pr-ci-fastfail-validation-context-preflight"

_PR168_BRANCHES = frozenset(
    {
        PR168_GFP_BRANCH,
        PR168_RP_BRANCH,
        PR168_RANK_BRANCH,
        PR168_DATA1_BRANCH,
        PR168_DATA1A_BRANCH,
        PR168_GFP2R_BRANCH,
        PR168_RP2_BRANCH,
        PR168_MAP3_BRANCH,
        PR168_RP3_BRANCH,
        PR168_RANK3_BRANCH,
        PR168_RP5A_BRANCH,
        PR168_RP5B_BRANCH,
        PR168_RP5C_BRANCH,
        PR168_RP5C_POST_MERGE_REPAIR_BRANCH,
        PR168_VS1_BRANCH,
        PR168_RP5D_BRANCH,
        PR168_RP5E_BRANCH,
        PR168_RP5D_R1_BRANCH,
        PR168_RP5F_BRANCH,
        PR168_RP5G_BRANCH,
        PR168_RANK4_BRANCH,
        PR168_QOPT1_BRANCH,
        PR168_VS2_BRANCH,
        PR168_MEM1_BRANCH,
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
        VALIDATION_FIXTURE_BRANCH,
    }
)
_VALIDATION_CONTEXT_BRANCHES = frozenset({VALIDATION_FIXTURE_BRANCH})

_PR168_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp_global_formula_discovery_real_computation.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/report.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/report.py",
        "src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/report.py",
        "src/qtt/stage1_prediction_markets/qtt_owner_global_override_directive_currentization_and_internal_gate_release/report.py",
        "tools/ci_branch_context.py",
        "tools/validate_idempotence_runtime_containment.py",
    }
)

_PR168_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP_*.report.json",
    "docs/master_plan/generated/pr168_gfp_shards/PR168_GFP_*.json",
    "src/qtt/stage1_prediction_markets/pr168_gfp_real_computation/**",
    "tests/pr168_gfp/**",
    "tools/validate_pr168_gfp_*.py",
)

_PR168_RP_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/build_pr168_rp_formula_based_replay_paper_recompute.py",
        "tools/run_validation_gates.py",
    }
)

_PR168_RP_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP_*.report.json",
    "docs/master_plan/generated/pr168_rp_shards/PR168_RP_*.report.json",
    "tools/pr168_rp_*.py",
    "tools/validate_pr168_rp_*.py",
    "tests/pr168_rp/**",
)

_PR168_RANK_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "tools/build_pr168_rank_evidence_backed_ranking.py",
    }
)

_PR168_RANK_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK_*.report.json",
    "docs/master_plan/generated/pr168_rank_shards/PR168_RANK_*.report.json",
    "tools/pr168_rank_*.py",
    "tools/validate_pr168_rank_*.py",
    "tests/pr168_rank/**",
)

_PR168_DATA1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1_public_market_data_snapshots.py",
        "tools/validate_pr168_data1_public_market_data_snapshots.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
    }
)

_PR168_DATA1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1_*.report.json",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_snapshots/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_forward_l2/**/*.manifest.json",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1_historical_replay_candidates/**/*.manifest.json",
    "tools/pr168_data1_*.py",
    "tests/pr168_data1/**",
)

_PR168_DATA1A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_data1a_focused_audit.py",
        "tools/validate_pr168_data1a_focused_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_DATA1A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_DATA1A_*.report.json",
    "docs/master_plan/generated/pr168_data1a_audit/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/*.manifest.json",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.jsonl",
    "docs/master_plan/generated/pr168_data1a_audit/**/*.manifest.json",
    "tools/pr168_data1a_*.py",
    "tests/pr168_data1a/**",
)

_PR168_GFP2R_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_GFP2R_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_GFP2R_*.report.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/*.manifest.json",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.jsonl",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute/**/*.manifest.json",
    "tools/pr168_gfp2r_*.py",
    "tests/pr168_gfp2r/**",
)

_PR168_RP2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp2_map2.py",
        "tools/validate_pr168_rp2_map2.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP2_*.report.json",
    "docs/master_plan/generated/rp2p/*.jsonl",
    "docs/master_plan/generated/rp2p/*.manifest.json",
    "docs/master_plan/generated/rp2p/**/*.jsonl",
    "docs/master_plan/generated/rp2p/**/*.manifest.json",
    "tools/pr168_rp2_*.py",
    "tests/pr168_rp2/**",
)

_PR168_MAP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_map3.py",
        "tools/validate_pr168_map3.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_MAP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_MAP3_*.report.json",
    "docs/master_plan/generated/map3/*.jsonl",
    "docs/master_plan/generated/map3/*.manifest.json",
    "docs/master_plan/generated/map3/**/*.jsonl",
    "docs/master_plan/generated/map3/**/*.manifest.json",
    "tools/pr168_map3_*.py",
    "tests/pr168_map3/**",
)

_PR168_RP3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp3.py",
        "tools/validate_pr168_rp3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP3_*.report.json",
    "docs/master_plan/generated/rp3/*.jsonl",
    "docs/master_plan/generated/rp3/*.manifest.json",
    "docs/master_plan/generated/rp3/**/*.jsonl",
    "docs/master_plan/generated/rp3/**/*.manifest.json",
    "tools/pr168_rp3_*.py",
    "tests/pr168_rp3/**",
)

_PR168_RANK3_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rank3.py",
        "tools/validate_pr168_rank3.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK3_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RANK3_*.report.json",
    "docs/master_plan/generated/rank3/*.jsonl",
    "docs/master_plan/generated/rank3/*.manifest.json",
    "docs/master_plan/generated/rank3/**/*.jsonl",
    "docs/master_plan/generated/rank3/**/*.manifest.json",
    "tools/pr168_rank3_*.py",
    "tests/pr168_rank3/**",
)

_PR168_RP5A_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5a_legacy_semantic_audit.py",
        "tools/validate_pr168_rp5a_legacy_semantic_audit.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5A_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5A_*.report.json",
    "docs/master_plan/generated/rp5a/*.jsonl",
    "docs/master_plan/generated/rp5a/*.manifest.json",
    "docs/master_plan/generated/rp5a/**/*.jsonl",
    "docs/master_plan/generated/rp5a/**/*.manifest.json",
    "tools/pr168_rp5a_*.py",
    "tests/pr168_rp5a/**",
)

_PR168_RP5B_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/validate_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5B_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5B_*.report.json",
    "docs/master_plan/generated/rp5b/*.jsonl",
    "docs/master_plan/generated/rp5b/*.manifest.json",
    "docs/master_plan/generated/rp5b/**/*.jsonl",
    "docs/master_plan/generated/rp5b/**/*.manifest.json",
    "tools/pr168_rp5b_*.py",
    "tests/pr168_rp5b/**",
)

_PR168_RP5C_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/validate_pr168_rp5c_immutable_qku_formula_library.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5C_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/PR168_RP5C_*.report.json",
    "docs/master_plan/generated/rp5c/*.jsonl",
    "docs/master_plan/generated/rp5c/*.manifest.json",
    "docs/master_plan/generated/rp5c/**/*.jsonl",
    "docs/master_plan/generated/rp5c/**/*.manifest.json",
    "tools/pr168_rp5c_*.py",
    "tests/pr168_rp5c/**",
)

_PR168_VS1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/run_pr168_vs1_trading_intelligence_slice.py",
        "tools/validate_pr168_vs1_trading_intelligence_slice.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_VS1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs1/*.jsonl",
    "docs/master_plan/generated/pr168_vs1/*.manifest.json",
    "docs/master_plan/generated/pr168_vs1/*.report.json",
    "src/qtt/stage1_prediction_markets/pr168_vs1_trading_intelligence/**",
    "tools/pr168_vs1_*.py",
    "tools/*pr168_vs1*.py",
    "tests/pr168_vs1/**",
)

_PR168_RP5D_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/validate_pr168_rp5d_replay_paper_executability_tiers.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d/*.report.json",
    "docs/master_plan/generated/pr168_rp5d/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/**",
    "tools/*pr168_rp5d*.py",
    "tests/pr168_rp5d/**",
)

_PR168_RP5E_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5e_stack_gen.py",
        "tools/validate_pr168_rp5e_stack_gen.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_consumption.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_input_inventory.jsonl",
        "docs/master_plan/generated/pr168_rp5d/rp5d_reading_receipts.jsonl",
    }
)

_PR168_RP5E_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5e/*.jsonl",
    "docs/master_plan/generated/pr168_rp5e/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5e/*.report.json",
    "docs/master_plan/generated/pr168_rp5e/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5e_stack_generator/**",
    "tools/*pr168_rp5e*.py",
    "tests/pr168_rp5e/**",
)

_PR168_RP5D_R1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "tools/build_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/validate_pr168_rp5d_r1_exec_now_unlock.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_validation_scope_registry.py",
        "src/qtt/stage1_prediction_markets/pr168_rp5d_executability/validator.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)

_PR168_RP5D_R1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5d_r1/*.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5d_r1_unlock/**",
    "tools/*pr168_rp5d_r1*.py",
    "tests/pr168_rp5d_r1/**",
)

_PR168_RP5F_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5f_dynamic_targets.py",
        "tools/validate_pr168_rp5f_dynamic_targets.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
        "tests/pr168_rp5c/test_rp5c_input_integrity.py",
    }
)

_PR168_RP5F_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5f/*.jsonl",
    "docs/master_plan/generated/pr168_rp5f/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5f/*.report.json",
    "docs/master_plan/generated/pr168_rp5f/*.json",
    "src/qtt/stage1_prediction_markets/pr168_rp5f_dynamic_targets/**",
    "tools/*pr168_rp5f*.py",
    "tests/pr168_rp5f/**",
)

_PR168_RP5G_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "tools/build_pr168_rp5g_trade_plan_sim.py",
        "tools/validate_pr168_rp5g_trade_plan_sim.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RP5G_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rp5g/*.jsonl",
    "docs/master_plan/generated/pr168_rp5g/*.manifest.json",
    "docs/master_plan/generated/pr168_rp5g/*.report.json",
    "docs/master_plan/generated/pr168_rp5g/*.json",
    "docs/master_plan/generated/pr168_rp5g/*.md",
    "src/qtt/stage1_prediction_markets/pr168_rp5g_trade_plan_sim/**",
    "tools/*pr168_rp5g*.py",
    "tests/pr168_rp5g/**",
)

_PR168_RANK4_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/ranking/__init__.py",
        "tools/build_pr168_rank4_advisory_ranking.py",
        "tools/validate_pr168_rank4_advisory_ranking.py",
        "tools/pr168_rp5c_config.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/tools/test_validate_idempotence_runtime_containment.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_RANK4_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_rank4/*.jsonl",
    "docs/master_plan/generated/pr168_rank4/*.manifest.json",
    "docs/master_plan/generated/pr168_rank4/*.report.json",
    "docs/master_plan/generated/pr168_rank4/*.json",
    "docs/master_plan/generated/pr168_rank4/*.md",
    "src/qtt/ranking/pr168_rank4/**",
    "tools/*pr168_rank4*.py",
    "tests/pr168_rank4/**",
)

_PR168_QOPT1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/optimization/__init__.py",
        "tools/build_pr168_qopt1_batch_optimization.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_qopt1_batch_optimization.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_QOPT1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_qopt1/*.jsonl",
    "docs/master_plan/generated/pr168_qopt1/*.manifest.json",
    "docs/master_plan/generated/pr168_qopt1/*.report.json",
    "docs/master_plan/generated/pr168_qopt1/*.json",
    "docs/master_plan/generated/pr168_qopt1/*.md",
    "src/qtt/optimization/pr168_qopt1/**",
    "tools/*pr168_qopt1*.py",
    "tests/pr168_qopt1/**",
)

_PR168_VS2_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/paper/__init__.py",
        "tools/build_pr168_vs2_paper_intent_candidates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr168_vs2_paper_intent_candidates.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_VS2_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_vs2/*.jsonl",
    "docs/master_plan/generated/pr168_vs2/*.manifest.json",
    "docs/master_plan/generated/pr168_vs2/*.report.json",
    "docs/master_plan/generated/pr168_vs2/*.json",
    "docs/master_plan/generated/pr168_vs2/*.md",
    "src/qtt/paper/pr168_vs2/**",
    "tools/*pr168_vs2*.py",
    "tests/pr168_vs2/**",
)

_PR168_MEM1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/memory/__init__.py",
        "tools/build_pr168_mem1_condition_scoped_memory.py",
        "tools/query_pr168_mem1_memory.py",
        "tools/validate_pr168_mem1_condition_scoped_memory.py",
        "tools/run_validation_gates.py",
        "tools/pr168_rp5c_config.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR168_MEM1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr168_mem1/*.jsonl",
    "docs/master_plan/generated/pr168_mem1/*.manifest.json",
    "docs/master_plan/generated/pr168_mem1/*.report.json",
    "docs/master_plan/generated/pr168_mem1/*.json",
    "docs/master_plan/generated/pr168_mem1/*.md",
    "src/qtt/memory/pr168_mem1/**",
    "tools/*pr168_mem1*.py",
    "tests/pr168_mem1/**",
)

_PR169_DASH1_ALLOWED_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
        "src/qtt/dashboard/__init__.py",
        "src/qtt/dashboard/owner_surface_models.py",
        "src/qtt/dashboard/owner_surface_registry.py",
        "src/qtt/dashboard/owner_surface_resolver.py",
        "src/qtt/dashboard/owner_action_registry.py",
        "src/qtt/dashboard/owner_dashboard_packet_builder.py",
        "src/qtt/dashboard/owner_dashboard_projection_builder.py",
        "src/qtt/dashboard/owner_dashboard_validator.py",
        "tools/build_pr168_rp5b_active_registry_safe_cleanup.py",
        "tools/build_pr169_dash1_owner_dashboard.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_pr169_dash1_owner_dashboard.py",
        "tools/validate_no_runtime_artifacts.py",
        "tools/pr168_rp5c_config.py",
        "tools/validate_source_fact_binding_connector_semantic_readiness_static.py",
        "tools/run_validation_gates.py",
        "tools/validation_inventory.py",
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/fail_closed/test_no_runtime_artifacts_strict.py",
        "tests/source_evidence/test_source_fact_binding_connector_semantic_readiness_static.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
        "tests/fail_closed/test_run_validation_gates.py",
    }
)

_PR169_DASH1_ALLOWED_PATTERNS = (
    "docs/master_plan/generated/pr169_dash1/**",
    "src/qtt/dashboard/**",
    "tools/*pr169_dash1*.py",
    "tests/pr169_dash1/**",
    "tests/pr169_dash1_ui1/**",
)

_FORBIDDEN_EXACT_PATHS = frozenset(
    {
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "AtomicRows.bundle.sha256",
        "docs/master_plan/generated/AtomicRows.bundle.sha256",
    }
)

_FORBIDDEN_PREFIXES = (
    ".tmp/",
    "src/qtt/live_connectors/",
    "src/qtt/connectors/live/",
    "src/qtt/private_state/",
    "src/qtt/live_order",
    "private-state/",
    "private_state/",
    "cash/",
    "secrets/",
)

_FORBIDDEN_NAME_TOKENS = (
    "live_order",
    "private_state",
    "private-state",
    "cash_account",
    "account_cash",
    "secret",
    "atomicrows.bundle.sha256",
    "qtt_sha",
    "qtt-sha",
    "qtt_freeze",
    "qtt-freeze",
    "qtt_checksum",
    "qtt-checksum",
    "qtt_global_digest",
    "qtt-global-digest",
)


def normalize_changed_path(path: str) -> str:
    """Normalize a changed path into repo-relative POSIX form."""
    normalized = str(path).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_validation_context_branch(branch: str) -> bool:
    return str(branch).strip() in _VALIDATION_CONTEXT_BRANCHES


def is_pr_scoped_changed_path_allowed(branch: str, path: str) -> bool:
    return bool(explain_pr_scope_decision(branch, path)["allowed"])


def _pr168_rp_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_data1a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_DATA1A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_DATA1A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-DATA1A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_gfp2r_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_GFP2R_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_GFP2R_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP2R",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_map3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MAP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MAP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MAP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank3_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK3_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK3_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK3",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5a_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5A_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5A_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5A",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5b_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5B_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5B_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5B",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5c_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5C_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5C_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5C",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5e_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5E_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5E_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5E",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5d_r1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5D_R1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5D_R1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5D-R1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5f_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5F_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5F_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5F",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rp5g_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RP5G_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RP5G_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RP5G",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_rank4_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_RANK4_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_RANK4_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-RANK4",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_qopt1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_QOPT1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_QOPT1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-QOPT1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_vs2_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_VS2_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_VS2_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-VS2",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr168_mem1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR168_MEM1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_MEM1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-MEM1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def _pr169_dash1_scope_decision(branch_name: str, normalized: str) -> dict[str, object] | None:
    if normalized in _PR169_DASH1_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR169_DASH1_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR169-DASH1",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return None


def explain_pr_scope_decision(branch: str, path: str) -> dict[str, object]:
    normalized = normalize_changed_path(path)
    branch_name = str(branch).strip()
    forbidden_reason = _forbidden_reason(normalized)
    if forbidden_reason:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": forbidden_reason,
            "reason": "forbidden_path",
        }
    if branch_name not in _PR168_BRANCHES:
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": None,
            "matched_rule": "branch_not_registered_for_pr_scope",
            "reason": "branch_not_registered",
        }
    if branch_name == PR168_RP_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP",
            "matched_rule": "no_pr168_rp_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK_BRANCH:
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK",
            "matched_rule": "no_pr168_rank_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1_BRANCH:
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1",
            "matched_rule": "no_pr168_data1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_DATA1A_BRANCH:
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-DATA1A",
            "matched_rule": "no_pr168_data1a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_GFP2R_BRANCH:
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP2R",
            "matched_rule": "no_pr168_gfp2r_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP2_BRANCH:
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP2",
            "matched_rule": "no_pr168_rp2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MAP3_BRANCH:
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MAP3",
            "matched_rule": "no_pr168_map3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP3_BRANCH:
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP3",
            "matched_rule": "no_pr168_rp3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK3_BRANCH:
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK3",
            "matched_rule": "no_pr168_rank3_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5A_BRANCH:
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5A",
            "matched_rule": "no_pr168_rp5a_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5B_BRANCH:
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5B",
            "matched_rule": "no_pr168_rp5b_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {PR168_RP5C_BRANCH, PR168_RP5C_POST_MERGE_REPAIR_BRANCH}:
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5C",
            "matched_rule": "no_pr168_rp5c_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS1_BRANCH:
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS1",
            "matched_rule": "no_pr168_vs1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_BRANCH:
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D",
            "matched_rule": "no_pr168_rp5d_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5E_BRANCH:
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5E",
            "matched_rule": "no_pr168_rp5e_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5D_R1_BRANCH:
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5D-R1",
            "matched_rule": "no_pr168_rp5d_r1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5F_BRANCH:
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5F",
            "matched_rule": "no_pr168_rp5f_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RP5G_BRANCH:
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RP5G",
            "matched_rule": "no_pr168_rp5g_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_RANK4_BRANCH:
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-RANK4",
            "matched_rule": "no_pr168_rank4_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_QOPT1_BRANCH:
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-QOPT1",
            "matched_rule": "no_pr168_qopt1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_VS2_BRANCH:
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-VS2",
            "matched_rule": "no_pr168_vs2_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == PR168_MEM1_BRANCH:
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-MEM1",
            "matched_rule": "no_pr168_mem1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name in {
        PR169_DASH1_BRANCH,
        PR169_DASH1_UI1_BRANCH,
        PR169_DASH1_UI1_R1_BRANCH,
    }:
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision
        return {
            "allowed": False,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR169-DASH1",
            "matched_rule": "no_pr169_dash1_scope_rule",
            "reason": "path_not_registered_for_pr_scope",
        }

    if branch_name == VALIDATION_FIXTURE_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision
        rank_decision = _pr168_rank_scope_decision(branch_name, normalized)
        if rank_decision:
            return rank_decision
        data1_decision = _pr168_data1_scope_decision(branch_name, normalized)
        if data1_decision:
            return data1_decision
        data1a_decision = _pr168_data1a_scope_decision(branch_name, normalized)
        if data1a_decision:
            return data1a_decision
        gfp2r_decision = _pr168_gfp2r_scope_decision(branch_name, normalized)
        if gfp2r_decision:
            return gfp2r_decision
        rp2_decision = _pr168_rp2_scope_decision(branch_name, normalized)
        if rp2_decision:
            return rp2_decision
        map3_decision = _pr168_map3_scope_decision(branch_name, normalized)
        if map3_decision:
            return map3_decision
        rp3_decision = _pr168_rp3_scope_decision(branch_name, normalized)
        if rp3_decision:
            return rp3_decision
        rank3_decision = _pr168_rank3_scope_decision(branch_name, normalized)
        if rank3_decision:
            return rank3_decision
        rank4_decision = _pr168_rank4_scope_decision(branch_name, normalized)
        if rank4_decision:
            return rank4_decision
        rp5a_decision = _pr168_rp5a_scope_decision(branch_name, normalized)
        if rp5a_decision:
            return rp5a_decision
        rp5b_decision = _pr168_rp5b_scope_decision(branch_name, normalized)
        if rp5b_decision:
            return rp5b_decision
        rp5c_decision = _pr168_rp5c_scope_decision(branch_name, normalized)
        if rp5c_decision:
            return rp5c_decision
        vs1_decision = _pr168_vs1_scope_decision(branch_name, normalized)
        if vs1_decision:
            return vs1_decision
        rp5d_decision = _pr168_rp5d_scope_decision(branch_name, normalized)
        if rp5d_decision:
            return rp5d_decision
        rp5e_decision = _pr168_rp5e_scope_decision(branch_name, normalized)
        if rp5e_decision:
            return rp5e_decision
        rp5d_r1_decision = _pr168_rp5d_r1_scope_decision(branch_name, normalized)
        if rp5d_r1_decision:
            return rp5d_r1_decision
        rp5f_decision = _pr168_rp5f_scope_decision(branch_name, normalized)
        if rp5f_decision:
            return rp5f_decision
        rp5g_decision = _pr168_rp5g_scope_decision(branch_name, normalized)
        if rp5g_decision:
            return rp5g_decision
        qopt1_decision = _pr168_qopt1_scope_decision(branch_name, normalized)
        if qopt1_decision:
            return qopt1_decision
        vs2_decision = _pr168_vs2_scope_decision(branch_name, normalized)
        if vs2_decision:
            return vs2_decision
        mem1_decision = _pr168_mem1_scope_decision(branch_name, normalized)
        if mem1_decision:
            return mem1_decision
        dash1_decision = _pr169_dash1_scope_decision(branch_name, normalized)
        if dash1_decision:
            return dash1_decision

    if normalized in _PR168_ALLOWED_EXACT_PATHS:
        return {
            "allowed": True,
            "branch": branch_name,
            "normalized_path": normalized,
            "pr_id": "PR168-GFP",
            "matched_rule": f"exact:{normalized}",
            "reason": "registered_exact_path",
        }
    for pattern in _PR168_ALLOWED_PATTERNS:
        if fnmatchcase(normalized, pattern):
            return {
                "allowed": True,
                "branch": branch_name,
                "normalized_path": normalized,
                "pr_id": "PR168-GFP",
                "matched_rule": f"pattern:{pattern}",
                "reason": "registered_pattern",
            }
    return {
        "allowed": False,
        "branch": branch_name,
        "normalized_path": normalized,
        "pr_id": "PR168-GFP",
        "matched_rule": "no_pr168_scope_rule",
        "reason": "path_not_registered_for_pr_scope",
    }


def _forbidden_reason(normalized: str) -> str | None:
    lowered = normalized.lower()
    if lowered.startswith("docs/master_plan/generated/pr168_vs2/no_private_state.") or lowered in {
        "docs/master_plan/generated/pr168_vs2/no_private_state.jsonl",
        "docs/master_plan/generated/pr168_vs2/no_private_state.manifest.json",
    }:
        return None
    if normalized in _FORBIDDEN_EXACT_PATHS:
        return f"forbidden_exact:{normalized}"
    if lowered.endswith("/atomicrows.bundle.sha256") or lowered == "atomicrows.bundle.sha256":
        return "forbidden_atomicrows_bundle_sha"
    for prefix in _FORBIDDEN_PREFIXES:
        if lowered.startswith(prefix):
            return f"forbidden_prefix:{prefix}"
    for token in _FORBIDDEN_NAME_TOKENS:
        if token in lowered:
            if (
                token == "live_order"
                and lowered.startswith("tests/")
                and "/test_no_live_order" in lowered
            ):
                continue
            if (
                token in {"qtt_sha", "qtt-sha"}
                and lowered.startswith("tests/pr169_dash1/")
                and "/test_dash1_no_qtt_sha" in lowered
            ):
                continue
            return f"forbidden_token:{token}"
    return None
