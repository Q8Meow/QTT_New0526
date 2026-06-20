#!/usr/bin/env python3
"""Centralized narrow changed-path scope registry for validation guards."""

from __future__ import annotations

from fnmatch import fnmatchcase


PR168_GFP_BRANCH = "pr168-gfp-global-formula-discovery-real-computation"
PR168_RP_BRANCH = "pr168-rp-formula-based-replay-paper-recompute"
VALIDATION_FIXTURE_BRANCH = "pr-ci-fastfail-validation-context-preflight"

_PR168_BRANCHES = frozenset({PR168_GFP_BRANCH, PR168_RP_BRANCH, VALIDATION_FIXTURE_BRANCH})
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
        "tools/validation_scope_registry.py",
        "tools/validate_validation_scope_registry.py",
        "tests/tools/test_validation_scope_registry.py",
        "tools/qtt_authority_reason_code_registry.py",
        "tools/validate_qtt_authority_reason_code_registry.py",
        "tests/tools/test_qtt_authority_reason_code_registry.py",
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

    if branch_name == VALIDATION_FIXTURE_BRANCH:
        rp_decision = _pr168_rp_scope_decision(branch_name, normalized)
        if rp_decision:
            return rp_decision

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
    if normalized in _FORBIDDEN_EXACT_PATHS:
        return f"forbidden_exact:{normalized}"
    if lowered.endswith("/atomicrows.bundle.sha256") or lowered == "atomicrows.bundle.sha256":
        return "forbidden_atomicrows_bundle_sha"
    for prefix in _FORBIDDEN_PREFIXES:
        if lowered.startswith(prefix):
            return f"forbidden_prefix:{prefix}"
    for token in _FORBIDDEN_NAME_TOKENS:
        if token in lowered:
            return f"forbidden_token:{token}"
    return None
