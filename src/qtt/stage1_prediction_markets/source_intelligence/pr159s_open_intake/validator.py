"""Fail-closed validator for PR159S generated artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .io import as_list, as_mapping, read_json
from .models import ValidationResult


_REPAIR_BRANCHES = (c.BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCH,)
_PR161A_DOWNSTREAM_BRANCH = "pr161a-atomicrows-pr154-value-state-materialization-bridge"
_PR161B_DOWNSTREAM_BRANCH = "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge"
_PR161C_DOWNSTREAM_BRANCH = "pr161c-qku-residual-candidate-assimilation-fill-campaign"
_PR161D_DOWNSTREAM_BRANCH = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"
_PR161E_DOWNSTREAM_BRANCH = "pr161e-replay-paper-outcome-capture-scenario-learning-bridge"
_PR161F_DOWNSTREAM_BRANCH = "pr161f-replay-paper-executor-input-run-artifact-generation"
_PR162_DOWNSTREAM_BRANCH = (
    "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge"
)
_PR162A_DOWNSTREAM_BRANCH = (
    "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate"
)
_PR162B_DOWNSTREAM_BRANCH = (
    "pr162b-qku-formula-algorithm-solver-market-scope-materialization"
)
_PR162C_DOWNSTREAM_BRANCH = (
    "pr162c-multisource-safe-nonlive-dataset-executable-qku-strict-coverage"
)
_PR162D_DOWNSTREAM_BRANCH = (
    "pr162d-aggressive-qku-candidate-materialization-agent-routing"
)
_PR162D_R1_DOWNSTREAM_BRANCH = (
    "pr162d-r1-external-formula-data-quantum-acquisition-expansion"
)
_PR162R_A_DOWNSTREAM_BRANCH = (
    "pr162r-a-replay-paper-executability-classification-audit"
)
_PR162D_R2A_DOWNSTREAM_BRANCH = (
    "pr162d-r2a-real-computable-formulations-redo"
)


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _branch_merged_ancestry_present(root: Path, branch: str) -> bool:
    return ci_branch_context.pr_branch_merged_ancestry_present(root, branch, git_stdout=_git_stdout)


def _ancestry_present(root: Path, branch_context: str = "") -> bool:
    if _branch_merged_ancestry_present(root, c.EXPECTED_BRANCH):
        return True
    normalized = ci_branch_context.normalize_branch_context(branch_context)
    branches = list(_REPAIR_BRANCHES)
    if normalized and normalized in _REPAIR_BRANCHES and normalized not in branches:
        branches.append(normalized)
    return any(_branch_merged_ancestry_present(root, branch) for branch in branches)


def _branch_context_allowed(branch_context: str) -> bool:
    normalized = ci_branch_context.normalize_branch_context(branch_context)
    return (
        normalized == c.EXPECTED_BRANCH
        or normalized == _PR161A_DOWNSTREAM_BRANCH
        or normalized == _PR161B_DOWNSTREAM_BRANCH
        or normalized == _PR161C_DOWNSTREAM_BRANCH
        or normalized == _PR161D_DOWNSTREAM_BRANCH
        or normalized == _PR161E_DOWNSTREAM_BRANCH
        or normalized == _PR161F_DOWNSTREAM_BRANCH
        or normalized == _PR162_DOWNSTREAM_BRANCH
        or normalized == _PR162A_DOWNSTREAM_BRANCH
        or normalized == _PR162B_DOWNSTREAM_BRANCH
        or normalized == _PR162C_DOWNSTREAM_BRANCH
        or normalized == _PR162D_DOWNSTREAM_BRANCH
        or normalized == _PR162D_R1_DOWNSTREAM_BRANCH
        or normalized == _PR162R_A_DOWNSTREAM_BRANCH
        or normalized == _PR162D_R2A_DOWNSTREAM_BRANCH
        or normalized in _REPAIR_BRANCHES
    )


def _detached_ci_context_allowed(root: Path) -> bool:
    branch_context = ci_branch_context.github_actions_branch_context()
    if _branch_context_allowed(branch_context):
        return True
    if branch_context:
        return False
    return _ancestry_present(root)


def _validate_branch(root: Path, failures: list[str], receipts: list[str]) -> None:
    branch_rc, git_branch, _branch_err = _git_stdout(root, ["branch", "--show-current"])
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=git_branch,
    ):
        if _detached_ci_context_allowed(root):
            receipts.append(c.PR159S_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY)
            return
        failures.append("PR159S_BLOCKED_WRONG_BRANCH:DETACHED_HEAD")
        return

    context = ci_branch_context.current_branch_context(root, git_stdout=_git_stdout)
    branch = context.branch
    if branch in {c.EXPECTED_BRANCH, _PR161A_DOWNSTREAM_BRANCH, _PR161B_DOWNSTREAM_BRANCH, _PR161C_DOWNSTREAM_BRANCH, _PR161D_DOWNSTREAM_BRANCH, _PR161E_DOWNSTREAM_BRANCH, _PR161F_DOWNSTREAM_BRANCH, _PR162_DOWNSTREAM_BRANCH, _PR162A_DOWNSTREAM_BRANCH, _PR162B_DOWNSTREAM_BRANCH, _PR162C_DOWNSTREAM_BRANCH, _PR162D_DOWNSTREAM_BRANCH, _PR162D_R1_DOWNSTREAM_BRANCH, _PR162R_A_DOWNSTREAM_BRANCH, _PR162D_R2A_DOWNSTREAM_BRANCH}:
        return
    if ci_branch_context.github_actions_main_push_context_active():
        if branch == "main" and _ancestry_present(root):
            receipts.append(c.PR159S_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY)
            return
        failures.append(f"PR159S_BLOCKED_WRONG_BRANCH:{branch or 'main'}")
        return
    if branch == "main" and _ancestry_present(root):
        return
    if ci_branch_context.normalize_branch_context(branch) in _REPAIR_BRANCHES and _ancestry_present(root, branch):
        return
    failures.append(f"PR159S_BLOCKED_WRONG_BRANCH:{branch or 'DETACHED_HEAD'}")


def _load(root: Path, rel_path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = root / rel_path
    if not full_path.exists():
        failures.append(f"PR159S_GENERATED_ARTIFACT_MISSING:{rel_path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, dict):
        failures.append(f"PR159S_GENERATED_ARTIFACT_NOT_OBJECT:{rel_path.as_posix()}")
        return {}
    return payload


def _records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [as_mapping(record) for record in as_list(payload.get("records"))]


def _validate_counts(summary: Mapping[str, Any], failures: list[str]) -> None:
    receipt = as_mapping(summary.get("count_invariant_receipt"))
    _require(receipt.get("processed_total") == c.EXPECTED_INPUT_TOTAL, failures, "PR159S_PROCESSED_TOTAL_NOT_868")
    _require(receipt.get("processed_atomicrows") == c.EXPECTED_ATOMICROWS_INPUT, failures, "PR159S_ATOMICROWS_TOTAL_NOT_845")
    _require(receipt.get("processed_pr154") == c.EXPECTED_PR154_INPUT, failures, "PR159S_PR154_TOTAL_NOT_23")
    _require(receipt.get("terminal_completion_total") == c.EXPECTED_INPUT_TOTAL, failures, "PR159S_TERMINAL_TOTAL_NOT_868")
    _require(receipt.get("source_profit_classified_total") == c.EXPECTED_INPUT_TOTAL, failures, "PR159S_SOURCE_PROFIT_TOTAL_NOT_868")
    _require(receipt.get("profit_validation_classified_total") == c.EXPECTED_INPUT_TOTAL, failures, "PR159S_PROFIT_TOTAL_NOT_868")
    _require(receipt.get("orphan_target_count") == 0, failures, "PR159S_ORPHAN_TARGET_COUNT_NONZERO")
    _require(receipt.get("generic_blocker_count") == 0, failures, "PR159S_GENERIC_BLOCKER_COUNT_NONZERO")
    _require(
        sum(as_mapping(receipt.get("terminal_completion_partition")).values()) == c.EXPECTED_INPUT_TOTAL,
        failures,
        "PR159S_TERMINAL_PARTITION_NOT_868",
    )
    _require(
        sum(as_mapping(receipt.get("source_provenance_partition")).values()) == c.EXPECTED_INPUT_TOTAL,
        failures,
        "PR159S_PROVENANCE_PARTITION_NOT_868",
    )
    _require(
        sum(as_mapping(receipt.get("profit_validation_partition")).values()) == c.EXPECTED_INPUT_TOTAL,
        failures,
        "PR159S_PROFIT_PARTITION_NOT_868",
    )
    _require(receipt.get("count_invariants_passed_flag") is True, failures, "PR159S_COUNT_INVARIANTS_FAILED")


def _validate_target_records(summary: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(summary)
    _require(len(records) == c.EXPECTED_INPUT_TOTAL, failures, "PR159S_SUMMARY_RECORD_COUNT_NOT_868")
    ids = [str(record.get("target_id_or_row_id")) for record in records]
    _require(len(ids) == len(set(ids)), failures, "PR159S_DUPLICATE_TARGET_IDS")
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        _require(record.get("terminal_completion_state") in c.TERMINAL_COMPLETION_STATES, failures, f"PR159S_BAD_TERMINAL_STATE:{target_id}")
        _require(record.get("source_provenance_tag") in c.SOURCE_PROVENANCE_TAGS, failures, f"PR159S_BAD_SOURCE_TAG:{target_id}")
        _require(record.get("profit_validation_tag") in c.PROFIT_VALIDATION_TAGS, failures, f"PR159S_BAD_PROFIT_TAG:{target_id}")
        _require(record.get("authority_class") in c.AUTHORITY_CLASSES, failures, f"PR159S_BAD_AUTHORITY:{target_id}")
        _require(record.get("source_class") in c.SOURCE_CLASSES, failures, f"PR159S_BAD_SOURCE_CLASS:{target_id}")
        _require(record.get("field_id") is not None, failures, f"PR159S_FIELD_ID_MISSING:{target_id}")
        _require(record.get("field_name") is not None, failures, f"PR159S_FIELD_NAME_MISSING:{target_id}")
        _require(record.get("field_value") is not None, failures, f"PR159S_FIELD_VALUE_MISSING:{target_id}")
        _require(record.get("source_locator") or record.get("source_artifact_path"), failures, f"PR159S_SOURCE_LOCATOR_MISSING:{target_id}")
        _require(record.get("live_use_pending_flag") is True, failures, f"PR159S_LIVE_PENDING_FLAG_MISSING:{target_id}")
        if record.get("source_provenance_tag") == c.SourceProvenanceTag.OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD.value:
            _require(record.get("official_confirmed_flag") is False, failures, f"PR159S_PENDING_OFFICIAL_MARKED_CONFIRMED:{target_id}")
            _require(record.get("official_source_packet_id") is None, failures, f"PR159S_PENDING_OFFICIAL_HAS_PACKET:{target_id}")
        if record.get("official_confirmed_flag") is True:
            _require(record.get("official_source_packet_id"), failures, f"PR159S_OFFICIAL_CONFIRMED_WITHOUT_PACKET:{target_id}")


def _validate_backfill(backfill: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(backfill)
    _require(len(records) == c.EXPECTED_PRIOR_ACCEPTED_OFFICIAL_TOTAL, failures, "PR159S_BACKFILL_COUNT_NOT_11")
    for record in records:
        record_id = str(record.get("backfill_record_id"))
        _require(record.get("source_provenance_tag") == c.SourceProvenanceTag.OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR.value, failures, f"PR159S_BACKFILL_BAD_TAG:{record_id}")
        _require(record.get("official_confirmed_flag") is True, failures, f"PR159S_BACKFILL_NOT_CONFIRMED:{record_id}")
        _require(bool(record.get("official_source_packet_id")), failures, f"PR159S_BACKFILL_PACKET_MISSING:{record_id}")
        _require(bool(record.get("official_source_locator")), failures, f"PR159S_BACKFILL_LOCATOR_MISSING:{record_id}")
        _require(record.get("authority_class") == c.AuthorityClass.ACCEPTED_OFFICIAL_EXTERNAL_FACT.value, failures, f"PR159S_BACKFILL_AUTHORITY_BAD:{record_id}")


def _validate_no_fake_official_facts(official_delta: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(official_delta)
    for record in records:
        record_id = str(record.get("official_delta_record_id"))
        _require(record.get("accepted_official_external_fact_created_flag") is False, failures, f"PR159S_FAKE_OFFICIAL_FACT_CREATED:{record_id}")
        _require(record.get("official_confirmed_flag") is False, failures, f"PR159S_OFFICIAL_DELTA_CONFIRMED_WITHOUT_PACKET:{record_id}")
        _require(record.get("official_source_packet_id") is None, failures, f"PR159S_OFFICIAL_DELTA_PACKET_CREATED:{record_id}")


def _validate_no_fake_profit(profit_registry: Mapping[str, Any], failures: list[str]) -> None:
    for record in _records(profit_registry):
        record_id = str(record.get("profit_validation_state_id"))
        _require(record.get("profit_proven_status_assigned_by_pr159s_flag") is False, failures, f"PR159S_FAKE_PROFIT_PROVEN:{record_id}")
        _require(record.get("non_profitable_status_assigned_by_pr159s_flag") is False, failures, f"PR159S_FAKE_NON_PROFITABLE:{record_id}")
        if record.get("profit_validation_tag") in {
            c.ProfitValidationTag.REPLAY_AND_PAPER_PROFITABLE.value,
            c.ProfitValidationTag.REPLAY_AND_PAPER_NON_PROFITABLE.value,
        }:
            _require(record.get("replay_paper_result_link"), failures, f"PR159S_PROFIT_TAG_WITHOUT_RESULT:{record_id}")


def _validate_no_forbidden_authority(payloads: list[Mapping[str, Any]], failures: list[str]) -> None:
    for payload in payloads:
        report_type = str(payload.get("report_type"))
        no_auth = as_mapping(payload.get("no_authority_confirmation"))
        for key, value in no_auth.items():
            _require(value is False, failures, f"PR159S_FORBIDDEN_AUTHORITY_FLAG:{report_type}:{key}")
        for key in c.ZERO_AUTHORITY_COUNTS:
            _require(payload.get(key) == 0, failures, f"PR159S_FORBIDDEN_AUTHORITY_COUNT:{report_type}:{key}")
        for record in _records(payload):
            record_auth = as_mapping(record.get("no_authority_confirmation"))
            for key, value in record_auth.items():
                _require(value is False, failures, f"PR159S_RECORD_FORBIDDEN_AUTHORITY:{report_type}:{key}")


def _validate_atomicrows(atomicrows: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(atomicrows)
    _require(len(records) == c.EXPECTED_ATOMICROWS_INPUT, failures, "PR159S_ATOMICROWS_READINESS_COUNT_NOT_845")
    for record in records:
        record_id = str(record.get("atomicrows_candidate_record_id"))
        _require(record.get("atomicrows_official_source_ready") is False, failures, f"PR159S_ATOMICROWS_FAKE_OFFICIAL_READY:{record_id}")
        _require(record.get("final_bundle_created_flag") is False, failures, f"PR159S_FINAL_BUNDLE_CREATED:{record_id}")
        _require(record.get("bundle_checksum_hash_authority_created_flag") is False, failures, f"PR159S_BUNDLE_HASH_AUTHORITY:{record_id}")


def _validate_taxonomy(taxonomy: Mapping[str, Any], failures: list[str]) -> None:
    values = as_mapping(taxonomy.get("central_enum_value_sets"))
    for key in (
        "source_provenance_tag",
        "profit_validation_tag",
        "terminal_completion_state",
        "authority_class",
        "source_quality_tier",
    ):
        _require(bool(values.get(key)), failures, f"PR159S_CENTRAL_ENUM_SET_MISSING:{key}")
    _require(
        len(_records(taxonomy))
        == len(c.OfficialSourceClass) + len(c.OpenResearchSourceClass) + len(c.ProhibitedExecutableTrustInput),
        failures,
        "PR159S_TAXONOMY_RECORD_COUNT_BAD",
    )


def _validate_schema_files(root: Path, failures: list[str]) -> None:
    for rel_path in c.SCHEMA_PATHS:
        _require((root / rel_path).exists(), failures, f"PR159S_SCHEMA_MISSING:{rel_path.as_posix()}")


def validate_existing_artifacts(root: Path) -> ValidationResult:
    failures: list[str] = []
    receipts: list[str] = []
    _validate_branch(root, failures, receipts)
    payloads = [_load(root, path, failures) for path in c.ALL_JSON_ARTIFACT_PATHS]
    if failures:
        return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))
    by_path = dict(zip((path.as_posix() for path in c.ALL_JSON_ARTIFACT_PATHS), payloads, strict=True))
    summary = by_path[c.TERMINAL_COMPLETION_SUMMARY_PATH.as_posix()]
    _validate_counts(summary, failures)
    _validate_target_records(summary, failures)
    _validate_backfill(by_path[c.OFFICIAL_CONFIRMED_BACKFILL_PATH.as_posix()], failures)
    _validate_no_fake_official_facts(by_path[c.OFFICIAL_EXTERNAL_FACT_DELTA_PATH.as_posix()], failures)
    _validate_no_fake_profit(by_path[c.PROFIT_VALIDATION_STATE_REGISTRY_PATH.as_posix()], failures)
    _validate_no_forbidden_authority(payloads, failures)
    _validate_atomicrows(by_path[c.ATOMICROWS_CANDIDATE_READINESS_DELTA_PATH.as_posix()], failures)
    _validate_taxonomy(by_path[c.SOURCE_TAXONOMY_PATH.as_posix()], failures)
    _validate_schema_files(root, failures)
    return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))
