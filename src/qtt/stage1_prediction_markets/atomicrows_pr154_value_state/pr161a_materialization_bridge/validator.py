"""Fail-closed validator for PR161A generated artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .io import as_list, as_mapping, read_json, records
from .models import ValidationResult
from .quantum_candidate_validator import validate_quantum_candidate_records


def validate_existing_artifacts(root: Path | str) -> ValidationResult:
    repo_root = Path(root).resolve()
    failures: list[str] = []
    receipts: list[str] = []
    _validate_branch(repo_root, failures, receipts)

    payloads = {
        key: _load(repo_root, path, failures)
        for key, path in c.REPORT_PATHS.items()
    }
    _validate_counts(payloads, failures)
    _validate_field_records(payloads.get("field_inventory", {}), failures)
    _validate_source_registry(payloads.get("source_intake", {}), failures)
    _validate_quantum(payloads, failures)
    _validate_no_forbidden_authority(payloads, failures)
    _validate_schema_files(repo_root, failures)

    if not failures:
        receipts.append(c.PREFLIGHT_RECEIPT_MARKER)
        receipts.append(c.SUCCESS_MARKER)
    return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))


def _load(root: Path, rel_path: Path, failures: list[str]) -> Mapping[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR161A_GENERATED_ARTIFACT_MISSING:{rel_path.as_posix()}")
        return {}
    payload = read_json(path)
    if not isinstance(payload, dict):
        failures.append(f"PR161A_GENERATED_ARTIFACT_NOT_OBJECT:{rel_path.as_posix()}")
        return {}
    return payload


def _validate_counts(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    summary = as_mapping(as_list(payloads.get("final_summary", {}).get("records"))[0])
    _require(
        summary.get("atomicrows_universe_observed_count") == c.EXPECTED_ATOMICROWS_COUNT,
        failures,
        "PR161A_ATOMICROWS_COUNT_NOT_4183",
    )
    _require(
        summary.get("pr154_universe_observed_count") == c.EXPECTED_PR154_COUNT,
        failures,
        "PR161A_PR154_COUNT_NOT_342",
    )
    _require(
        summary.get("combined_entity_processed_count") == c.EXPECTED_COMBINED_ENTITY_COUNT,
        failures,
        "PR161A_COMBINED_COUNT_NOT_4525",
    )
    _require(
        summary.get("entity_value_state_classified_count") == c.EXPECTED_COMBINED_ENTITY_COUNT,
        failures,
        "PR161A_ENTITY_CLASSIFIED_COUNT_NOT_4525",
    )
    _require(summary.get("field_value_record_count", 0) >= c.EXPECTED_COMBINED_ENTITY_COUNT, failures, "PR161A_FIELD_RECORD_COUNT_TOO_LOW")
    _require(summary.get("generic_blocker_count") == 0, failures, "PR161A_GENERIC_BLOCKER_COUNT_NONZERO")
    _require(summary.get("orphan_count") == 0, failures, "PR161A_ORPHAN_COUNT_NONZERO")
    _require(summary.get("still_missing_after_all_lanes_count") == 0, failures, "PR161A_STILL_MISSING_NONZERO")


def _validate_field_records(payload: Mapping[str, Any], failures: list[str]) -> None:
    required = {
        "record_id",
        "universe",
        "field_path",
        "source_intake_state",
        "value_materialization_state",
        "value_authority_class",
        "attempted_fill_lanes",
        "agent_consumable_state",
        "profit_validation_tag",
        "live_use_allowed_flag",
    }
    materialization_states = {item.value for item in c.ValueMaterializationState}
    source_states = {item.value for item in c.SourceIntakeState}
    authority_states = {item.value for item in c.ValueAuthorityClass}
    entity_ids: set[str] = set()
    for record in records(payload):
        record_id = str(record.get("record_id"))
        missing = sorted(required - set(record))
        if missing:
            failures.append(f"PR161A_FIELD_REQUIRED_KEYS_MISSING:{record_id}:{','.join(missing)}")
        if record.get("source_intake_state") not in source_states:
            failures.append(f"PR161A_BAD_SOURCE_STATE:{record_id}")
        if record.get("value_materialization_state") not in materialization_states:
            failures.append(f"PR161A_BAD_VALUE_STATE:{record_id}")
        if record.get("value_authority_class") not in authority_states:
            failures.append(f"PR161A_BAD_AUTHORITY_STATE:{record_id}")
        if record.get("profit_validation_tag") != c.PROFIT_NOT_TESTED:
            failures.append(f"PR161A_BAD_PROFIT_TAG:{record_id}")
        if record.get("live_use_allowed_flag") is not False:
            failures.append(f"PR161A_LIVE_USE_ALLOWED:{record_id}")
        if not record.get("attempted_fill_lanes"):
            failures.append(f"PR161A_ATTEMPTED_LANES_MISSING:{record_id}")
        entity_ids.add(str(record.get("row_id") or record.get("target_id")))
    _require(len(entity_ids) == c.EXPECTED_COMBINED_ENTITY_COUNT, failures, "PR161A_NOT_EVERY_ENTITY_HAS_FIELD_RECORD")


def _validate_source_registry(payload: Mapping[str, Any], failures: list[str]) -> None:
    _require(payload.get("official_source_candidate_count") == 338, failures, "PR161A_OFFICIAL_CANDIDATE_COUNT_NOT_338")
    _require(payload.get("open_research_candidate_count", 0) >= 530, failures, "PR161A_OPEN_RESEARCH_COUNT_TOO_LOW")
    _require(payload.get("github_research_pattern_candidate_count", 0) >= 59, failures, "PR161A_GITHUB_PATTERN_COUNT_TOO_LOW")
    for record in records(payload):
        source_id = str(record.get("source_intake_id"))
        _require(bool(record.get("source_url_or_locator")), failures, f"PR161A_SOURCE_LOCATOR_MISSING:{source_id}")
        _require(record.get("live_use_allowed_flag") is False, failures, f"PR161A_SOURCE_LIVE_ALLOWED:{source_id}")


def _validate_quantum(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    profiles = records(payloads.get("quantum_profiles", {}))
    profile_types = {str(record.get("quantum_profile_type")) for record in profiles}
    _require(set(c.QUANTUM_PROFILE_TYPES) == profile_types, failures, "PR161A_QUANTUM_PROFILE_TYPE_SET_MISMATCH")
    failures.extend(validate_quantum_candidate_records(profiles))
    _require(len(records(payloads.get("quantum_formulas", {}))) == len(c.QUANTUM_FORMULA_TEMPLATE_FAMILIES), failures, "PR161A_QUANTUM_FORMULA_COUNT_BAD")
    _require(len(records(payloads.get("quantum_replay_queue", {}))) == len(profiles), failures, "PR161A_QUANTUM_DESCRIPTOR_COUNT_BAD")
    _require(len(records(payloads.get("quantum_agent_bridge", {}))) == len(profiles), failures, "PR161A_QUANTUM_AGENT_BRIDGE_COUNT_BAD")
    _require(len(records(payloads.get("quantum_traceability", {}))) == len(profiles), failures, "PR161A_QUANTUM_TRACEABILITY_COUNT_BAD")


def _validate_no_forbidden_authority(payloads: Mapping[str, Mapping[str, Any]], failures: list[str]) -> None:
    scan_records = records(payloads.get("forbidden_scan", {}))
    scan = as_mapping(scan_records[0]) if scan_records else {}
    _require(scan.get("finding_count") == 0, failures, "PR161A_FORBIDDEN_SCAN_FINDINGS_NONZERO")
    for payload in payloads.values():
        no_auth = as_mapping(payload.get("no_authority_confirmation"))
        for key, value in no_auth.items():
            if value is not False:
                failures.append(f"PR161A_FORBIDDEN_AUTHORITY_FLAG:{key}")
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
                failures.append(f"PR161A_FORBIDDEN_AUTHORITY_COUNT:{key}")


def _validate_schema_files(root: Path, failures: list[str]) -> None:
    for rel_path in c.SCHEMA_PATHS:
        _require((root / rel_path).exists(), failures, f"PR161A_SCHEMA_MISSING:{rel_path.as_posix()}")


def _validate_branch(root: Path, failures: list[str], receipts: list[str]) -> None:
    branch_rc, branch, _ = _git_stdout(root, ["branch", "--show-current"])
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=branch,
    ):
        context = ci_branch_context.github_actions_branch_context()
        if _branch_context_allowed(root, context):
            receipts.append("PR161A_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY")
            return
        failures.append("PR161A_BLOCKED_WRONG_BRANCH:DETACHED_HEAD")
        return
    context = ci_branch_context.current_branch_context(root, git_stdout=_git_stdout).branch
    if _branch_context_allowed(root, context):
        return
    if ci_branch_context.github_actions_main_push_context_active() and context == "main" and _ancestry_present(root):
        receipts.append("PR161A_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY")
        return
    failures.append(f"PR161A_BLOCKED_WRONG_BRANCH:{context or 'DETACHED_HEAD'}")


def _branch_context_allowed(root: Path, branch: str) -> bool:
    normalized = ci_branch_context.normalize_branch_context(branch)
    return normalized in {
        c.EXPECTED_BRANCH,
        c.REPAIR_BRANCH,
        "pr161b-master-plan-residual-candidate-coverage-assimilation-bridge",
        "pr161c-qku-residual-candidate-assimilation-fill-campaign",
        "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization",
        "pr161e-replay-paper-outcome-capture-scenario-learning-bridge",
        "pr161f-replay-paper-executor-input-run-artifact-generation",
        "pr162-safe-nonlive-replay-paper-executor-data-adapter-quantum-forward-bridge",
        "pr162a-safe-repo-local-nonlive-dataset-materialization-authority-gate",
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

