"""Fail-closed validator for PR161B generated artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .io import read_json, records
from .models import ValidationResult


def validate_existing_artifacts(root: Path | str) -> ValidationResult:
    repo_root = Path(root).resolve()
    failures: list[str] = []
    receipts: list[str] = []
    _validate_branch(repo_root, failures, receipts)
    payloads = {key: _load(repo_root, path, failures) for key, path in c.REPORT_PATHS.items()}
    _validate_section_coverage(payloads.get("section_search_coverage", {}), failures)
    _validate_candidates(payloads.get("candidate_inventory", {}), failures)
    _validate_queues(payloads, failures)
    _validate_quantum(payloads, failures)
    _validate_orchestration(payloads, failures)
    _validate_summary(payloads.get("final_summary", {}), failures)
    _validate_forbidden(payloads.get("forbidden_authority_scan", {}), failures)
    _validate_schemas(repo_root, failures)
    if not failures:
        receipts.append(c.PREFLIGHT_RECEIPT_MARKER)
        receipts.append(c.SUCCESS_MARKER)
    return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))


def _load(root: Path, rel_path: Path, failures: list[str]) -> Mapping[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR161B_GENERATED_ARTIFACT_MISSING:{rel_path.as_posix()}")
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        failures.append(f"PR161B_GENERATED_ARTIFACT_NOT_OBJECT:{rel_path.as_posix()}")
        return {}
    return payload


def _validate_section_coverage(payload: Mapping[str, Any], failures: list[str]) -> None:
    section_records = records(payload)
    _require(len(section_records) == c.EXPECTED_MASTER_PLAN_SECTION_COUNT, failures, "PR161B_SECTION_COUNT_NOT_3006")
    _require(payload.get("master_plan_sections_searched_count") == len(section_records), failures, "PR161B_SECTION_SEARCHED_COUNT_MISMATCH")
    _require(payload.get("master_plan_sections_unsearched_count") == 0, failures, "PR161B_UNSEARCHED_SECTIONS_NONZERO")
    _require(payload.get("master_plan_section_search_error_count") == 0, failures, "PR161B_SECTION_SEARCH_ERROR_NONZERO")
    for record in section_records:
        section_id = str(record.get("section_id"))
        if record.get("searched_flag") is not True:
            failures.append(f"PR161B_SECTION_NOT_SEARCHED:{section_id}")
        if not record.get("extraction_pass_ids_applied"):
            failures.append(f"PR161B_SECTION_EXTRACTION_PASSES_MISSING:{section_id}")
        if not record.get("candidate_like_item_found_flag") and not record.get("no_candidate_reason_if_none"):
            failures.append(f"PR161B_SECTION_NO_CANDIDATE_REASON_MISSING:{section_id}")


def _validate_candidates(payload: Mapping[str, Any], failures: list[str]) -> None:
    required = {
        "residual_candidate_id",
        "extraction_source_path",
        "extraction_pass_ids",
        "master_plan_section_id",
        "master_plan_heading",
        "extracted_text",
        "normalized_candidate_name",
        "candidate_type",
        "candidate_family",
        "coverage_state",
        "coverage_match_tier",
        "residual_gap_flag",
        "downstream_agent_roles",
        "live_use_allowed_flag",
        "no_profit_evidence_created_flag",
        "no_runtime_authority_created_flag",
    }
    coverage_states = {item.value for item in c.CoverageState}
    gap_types = {item.value for item in c.ResidualGapType}
    for record in records(payload):
        candidate_id = str(record.get("residual_candidate_id"))
        missing = sorted(required - set(record))
        if missing:
            failures.append(f"PR161B_CANDIDATE_KEYS_MISSING:{candidate_id}:{','.join(missing)}")
        if record.get("coverage_state") not in coverage_states:
            failures.append(f"PR161B_BAD_COVERAGE_STATE:{candidate_id}")
        if record.get("residual_gap_flag") and record.get("residual_gap_type") not in gap_types:
            failures.append(f"PR161B_BAD_GAP_TYPE:{candidate_id}")
        if record.get("coverage_match_tier") == c.CoverageMatchTier.TIER_4_WEAK_TEXT_MATCH_POSSIBLE_ONLY.value and not record.get("residual_gap_flag"):
            failures.append(f"PR161B_WEAK_MATCH_COUNTED_AS_FULL:{candidate_id}")
        if record.get("live_use_allowed_flag") is not False:
            failures.append(f"PR161B_CANDIDATE_LIVE_ALLOWED:{candidate_id}")
        if not record.get("downstream_agent_roles"):
            failures.append(f"PR161B_CANDIDATE_AGENT_ROLES_MISSING:{candidate_id}")


def _validate_queues(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    candidates = records(payloads.get("candidate_inventory", {}))
    queue = records(payloads.get("assimilation_queue", {}))
    queue_ids = {str(item.get("residual_candidate_id")) for item in queue}
    for candidate in candidates:
        if candidate.get("pr161c_assimilation_required_flag") and candidate["residual_candidate_id"] not in queue_ids:
            failures.append(f"PR161B_ASSIMILATION_QUEUE_MISSING:{candidate['residual_candidate_id']}")


def _validate_quantum(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    quantum = records(payloads.get("quantum_optimizer", {}))
    quantum_queue = records(payloads.get("quantum_assimilation_queue", {}))
    families = {item.get("quantum_candidate_family") for item in quantum}
    for required_family in {"QUBO", "ISING", "QAOA", "VQE", "ANNEALING"}:
        _require(required_family in families, failures, f"PR161B_QUANTUM_FAMILY_MISSING:{required_family}")
    queue_ids = {str(item.get("quantum_residual_id")) for item in quantum_queue}
    for record in quantum:
        if record.get("pr161c_quantum_assimilation_required_flag") and record["quantum_residual_id"] not in queue_ids:
            failures.append(f"PR161B_QUANTUM_QUEUE_MISSING:{record['quantum_residual_id']}")
        for key in (
            "optimizer_execution_evidence_created_flag",
            "quantum_backend_execution_evidence_created_flag",
            "quantum_advantage_evidence_created_flag",
            "profit_evidence_created_flag",
            "live_use_allowed_flag",
        ):
            if record.get(key) is not False:
                failures.append(f"PR161B_QUANTUM_FORBIDDEN_FLAG:{record['quantum_residual_id']}:{key}")


def _validate_orchestration(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    candidates = records(payloads.get("candidate_inventory", {}))
    orchestration = records(payloads.get("orchestration_graph", {}))
    _require(len(candidates) == len(orchestration), failures, "PR161B_ORCHESTRATION_RECORD_COUNT_MISMATCH")
    for record in orchestration:
        if not record.get("upstream_pr_ids") or not record.get("downstream_agent_roles"):
            failures.append(f"PR161B_ORPHAN_ORCHESTRATION_RECORD:{record.get('orchestration_record_id')}")
        if record.get("live_use_allowed_flag") is not False:
            failures.append(f"PR161B_ORCHESTRATION_LIVE_ALLOWED:{record.get('orchestration_record_id')}")


def _validate_summary(payload: Mapping[str, Any], failures: list[str]) -> None:
    summary_records = records(payload)
    summary = summary_records[0] if summary_records else {}
    _require(summary.get("master_plan_section_count_expected") == c.EXPECTED_MASTER_PLAN_SECTION_COUNT, failures, "PR161B_SUMMARY_EXPECTED_SECTION_COUNT_BAD")
    _require(summary.get("master_plan_section_count_observed") == c.EXPECTED_MASTER_PLAN_SECTION_COUNT, failures, "PR161B_SUMMARY_OBSERVED_SECTION_COUNT_BAD")
    _require(summary.get("master_plan_sections_unsearched_count") == 0, failures, "PR161B_SUMMARY_UNSEARCHED_NONZERO")
    _require(summary.get("orphan_candidate_workflow_record_count") == 0, failures, "PR161B_SUMMARY_ORPHANS_NONZERO")
    _require(summary.get("master_plan_file_edited_flag") is False, failures, "PR161B_MASTER_PLAN_EDITED_FLAG_BAD")
    _require(summary.get("atomicrows_final_bundle_created_flag") is False, failures, "PR161B_ATOMICROWS_FINAL_BUNDLE_FLAG_BAD")
    _require(summary.get("official_facts_profit_replay_paper_live_execution_fabricated_flag") is False, failures, "PR161B_FAKE_EVIDENCE_FLAG_BAD")


def _validate_forbidden(payload: Mapping[str, Any], failures: list[str]) -> None:
    scan = records(payload)[0] if records(payload) else {}
    _require(scan.get("finding_count") == 0, failures, "PR161B_FORBIDDEN_AUTHORITY_FINDINGS_NONZERO")
    for key in (
        "profit_evidence_count",
        "replay_paper_execution_count",
        "optimizer_execution_count",
        "quantum_backend_execution_count",
        "quantum_simulator_execution_count",
        "quantum_advantage_claim_count",
        "runtime_live_order_profit_authority_count",
    ):
        if payload.get(key) != 0:
            failures.append(f"PR161B_FORBIDDEN_AUTHORITY_COUNT:{key}")


def _validate_schemas(root: Path, failures: list[str]) -> None:
    for rel_path in c.SCHEMA_PATHS:
        _require((root / rel_path).exists(), failures, f"PR161B_SCHEMA_MISSING:{rel_path.as_posix()}")


def _validate_branch(root: Path, failures: list[str], receipts: list[str]) -> None:
    branch_rc, branch, _ = _git_stdout(root, ["branch", "--show-current"])
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=branch,
    ):
        context = ci_branch_context.github_actions_branch_context()
        if _branch_context_allowed(root, context):
            receipts.append("PR161B_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY")
            return
        failures.append("PR161B_BLOCKED_WRONG_BRANCH:DETACHED_HEAD")
        return
    context = ci_branch_context.current_branch_context(root, git_stdout=_git_stdout).branch
    if _branch_context_allowed(root, context):
        return
    if ci_branch_context.github_actions_main_push_context_active() and context == "main" and _ancestry_present(root):
        receipts.append("PR161B_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY")
        return
    failures.append(f"PR161B_BLOCKED_WRONG_BRANCH:{context or 'DETACHED_HEAD'}")


def _branch_context_allowed(root: Path, branch: str) -> bool:
    normalized = ci_branch_context.normalize_branch_context(branch)
    if ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
        normalized,
        upstream_pr=161,
    ):
        return True
    return normalized in {
        c.EXPECTED_BRANCH,
        c.REPAIR_BRANCH,
        "pr161c-qku-residual-candidate-assimilation-fill-campaign",
        "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization",
        "pr161e-replay-paper-outcome-capture-scenario-learning-bridge",
        "pr161f-replay-paper-executor-input-run-artifact-generation",
        "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge",
        "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate",
        "pr162b-qku-formula-algorithm-solver-market-scope-materialization",
        "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage",
        "pr162d-aggressive-qku-candidate-materialization-agent-routing",
        "pr162d-r1-external-formula-data-quantum-acquisition-expansion",
        "pr162r-a-replay-paper-executability-classification-audit",
        "pr162d-r2a-real-computable-formulations-redo",
        "pr162r-generic-replay-paper-adapter-rerun",
        "pr162r-b-replay-paper-data-binding-completion",
        "pr163-generic-paper-adapter-capture-framework",
        "pr163-b-paired-replay-paper-concurrent-executor",
        "pr163-c-pretrade-infrastructure-rejection-remediation",
        "pr164-review-provenance-qku-canonical-coverage-audit",
    } or (
        normalized == "main" and _ancestry_present(root)
    )


def _ancestry_present(root: Path) -> bool:
    return any(
        ci_branch_context.pr_branch_merged_ancestry_present(root, branch, git_stdout=_git_stdout)
        for branch in (c.EXPECTED_BRANCH, c.REPAIR_BRANCH)
    )


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)
