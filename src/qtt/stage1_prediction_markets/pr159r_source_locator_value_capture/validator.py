"""Fail-closed validator for PR159R generated artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .io import as_list, as_mapping, json_dump, read_json
from .models import ValidationResult
from .report import build_artifacts


_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES = (
    ci_branch_context.PR159R_BRANCH_CONTEXT_REPAIR_BRANCH,
    ci_branch_context.PR159S_BRANCH_CONTEXT_REPAIR_BRANCH,
    ci_branch_context.PR159R_DETACHED_HEAD_REPAIR_BRANCH,
)


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _load(root: Path, rel_path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = root / rel_path
    if not full_path.exists():
        failures.append(f"PR159R_GENERATED_ARTIFACT_MISSING:{rel_path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, dict):
        failures.append(f"PR159R_GENERATED_ARTIFACT_NOT_OBJECT:{rel_path.as_posix()}")
        return {}
    return payload


def _records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [as_mapping(item) for item in as_list(payload.get("records"))]


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _branch_merged_ancestry_present(
    root: Path,
    branch: str,
    *,
    refresh_shallow: bool = False,
) -> bool:
    helper = (
        ci_branch_context.pr_branch_merged_ancestry_present_with_shallow_refresh
        if refresh_shallow
        else ci_branch_context.pr_branch_merged_ancestry_present
    )
    return helper(root, branch, git_stdout=_git_stdout)


def _pr159r_ancestry_present(root: Path, *, refresh_shallow: bool = False) -> bool:
    return _branch_merged_ancestry_present(
        root,
        c.EXPECTED_BRANCH,
        refresh_shallow=refresh_shallow,
    )


def _pr159r_or_repair_ancestry_present(
    root: Path,
    branch_context: str = "",
    *,
    refresh_shallow: bool = False,
) -> bool:
    if _pr159r_ancestry_present(root, refresh_shallow=refresh_shallow):
        return True
    ancestry_branches = list(_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES)
    normalized = ci_branch_context.normalize_branch_context(branch_context)
    if (
        normalized
        and normalized in _BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES
        and normalized not in ancestry_branches
    ):
        ancestry_branches.append(normalized)
    return any(
        _branch_merged_ancestry_present(
            root,
            branch,
            refresh_shallow=refresh_shallow,
        )
        for branch in ancestry_branches
    )


def _pr159r_detached_ci_context_allowed(root: Path) -> bool:
    branch_context = ci_branch_context.github_actions_branch_context()
    if ci_branch_context.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
        branch_context,
        "PR159R",
    ):
        return True
    if branch_context:
        return False
    return _pr159r_or_repair_ancestry_present(root)


def _validate_branch(root: Path, failures: list[str], receipts: list[str]) -> None:
    branch_rc, git_branch, _branch_err = _git_stdout(root, ["branch", "--show-current"])
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=git_branch,
    ):
        if _pr159r_detached_ci_context_allowed(root):
            receipts.append(c.PR159R_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY)
            return
        failures.append("PR159R_BLOCKED_WRONG_BRANCH:DETACHED_HEAD")
        return

    context = ci_branch_context.current_branch_context(root, git_stdout=_git_stdout)
    branch = context.branch
    if ci_branch_context.is_branch_allowed_for_upstream_pr_gate(branch, "PR159R"):
        return
    main_push_context = ci_branch_context.github_actions_main_push_context_active()
    ancestry_present = _pr159r_or_repair_ancestry_present(
        root,
        refresh_shallow=main_push_context,
    )
    if ci_branch_context.is_main_push_context_allowed_for_upstream_pr_gate(
        branch,
        "PR159R",
        ancestry_present=ancestry_present,
    ):
        receipts.append(c.PR159R_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY)
        return
    if main_push_context:
        failures.append(f"PR159R_BLOCKED_WRONG_BRANCH:{branch or 'main'}")
        return
    if ci_branch_context.is_branch_allowed_for_upstream_pr_gate(
        branch,
        "PR159R",
        ancestry_present=ancestry_present,
        include_main=True,
    ):
        return
    failures.append(f"PR159R_BLOCKED_WRONG_BRANCH:{branch or 'DETACHED_HEAD'}")


def _validate_receipts(master_report: Mapping[str, Any], failures: list[str]) -> None:
    receipts = [as_mapping(item) for item in as_list(master_report.get("input_consumption_receipt"))]
    by_path = {str(item.get("path")): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = by_path.get(path.as_posix(), {})
            fallback = by_path.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            _require(
                bool(requested.get("consumed") or fallback.get("consumed")),
                failures,
                "PR159R_MANDATORY_CROSSWALK_OR_FALLBACK_NOT_CONSUMED",
            )
            continue
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item.get("exists") and item.get("consumed")),
            failures,
            f"PR159R_MANDATORY_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    for path in (
        *c.MANDATORY_CONTEXT_INPUTS,
        *c.QUANTUM_SCORING_OPTIMIZER_INPUTS,
        *c.AGENT_CONTEXT_INPUTS,
    ):
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item.get("exists") and item.get("consumed")),
            failures,
            f"PR159R_CONTEXT_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    shard_receipts = [
        item
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("exists")
        and item.get("consumed")
    ]
    _require(len(shard_receipts) == 9, failures, "PR159R_PR157_SHARDS_NOT_CONSUMED")
    schema_receipts = [
        item
        for item in receipts
        if item.get("artifact_role") == "source_evidence_schema_input" and item.get("consumed")
    ]
    _require(bool(schema_receipts), failures, "PR159R_SOURCE_EVIDENCE_SCHEMAS_NOT_CONSUMED")


def _validate_counts(master_report: Mapping[str, Any], failures: list[str]) -> None:
    receipt = as_mapping(master_report.get("count_invariant_receipt"))
    _require(receipt.get("pr154_remaining_source_target_count") == 24, failures, "PR159R_PR154_REMAINING_COUNT_NOT_24")
    _require(receipt.get("atomicrows_remaining_source_target_count") == 845, failures, "PR159R_ATOMICROWS_REMAINING_COUNT_NOT_845")
    _require(receipt.get("atomicrows_public_external_source_required_count") == 315, failures, "PR159R_ATOMICROWS_PUBLIC_COUNT_NOT_315")
    _require(receipt.get("atomicrows_parameter_range_source_required_count") == 530, failures, "PR159R_ATOMICROWS_RANGE_COUNT_NOT_530")
    _require(receipt.get("total_remaining_source_target_count") == 869, failures, "PR159R_TOTAL_TARGET_COUNT_NOT_869")
    _require(receipt.get("pr160_pr159r_requeue_count") == 3, failures, "PR159R_PR160_REQUEUE_COUNT_NOT_3")
    _require(receipt.get("processed_target_count") == 869, failures, "PR159R_PROCESSED_TARGET_COUNT_NOT_869")
    _require(receipt.get("one_final_state_per_target_count") == 869, failures, "PR159R_ONE_FINAL_STATE_COUNT_NOT_869")
    _require(receipt.get("orphan_target_count") == 0, failures, "PR159R_ORPHAN_TARGET_COUNT_NONZERO")
    _require(receipt.get("placeholder_value_count") == 0, failures, "PR159R_PLACEHOLDER_VALUE_COUNT_NONZERO")
    _require(receipt.get("blocker_as_value_count") == 0, failures, "PR159R_BLOCKER_AS_VALUE_COUNT_NONZERO")
    _require(receipt.get("quantum_relevant_unclassified_count") == 0, failures, "PR159R_QUANTUM_RELEVANT_UNCLASSIFIED_NONZERO")
    _require(
        receipt.get("accepted_source_packet_count_after_PR159R")
        == receipt.get("accepted_source_packet_count_before_PR159R", 0)
        + receipt.get("new_accepted_source_packet_count", 0),
        failures,
        "PR159R_ACCEPTED_PACKET_COUNT_RECONCILIATION_FAILED",
    )
    _require(
        receipt.get("target_field_ledger_count_after_PR159R")
        == receipt.get("target_field_ledger_count_before_PR159R", 0)
        + receipt.get("new_ledger_record_count", 0),
        failures,
        "PR159R_LEDGER_COUNT_RECONCILIATION_FAILED",
    )
    _require(
        receipt.get("unresolved_after_PR159R_count")
        == receipt.get("total_remaining_source_target_count", 0)
        - receipt.get("new_accepted_source_packet_count", 0),
        failures,
        "PR159R_UNRESOLVED_COUNT_RECONCILIATION_FAILED",
    )
    _require(receipt.get("count_invariants_passed_flag") is True, failures, "PR159R_COUNT_INVARIANTS_FAILED")


def _validate_targets(target_registry: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(target_registry)
    _require(len(records) == 869, failures, "PR159R_TARGET_REGISTRY_COUNT_NOT_869")
    ids = [str(record.get("target_id_or_row_id")) for record in records]
    _require(len(ids) == len(set(ids)), failures, "PR159R_DUPLICATE_TARGET_ID")
    final_states = set(c.FINAL_TARGET_STATES)
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        _require(record.get("final_PR159R_target_state") in final_states, failures, f"PR159R_BAD_FINAL_STATE:{target_id}")
        _require(record.get("target_population") in c.CENTRAL_ENUM_VALUE_SETS["target_population"], failures, f"PR159R_BAD_POPULATION:{target_id}")
        _require(record.get("day1_priority_tier") in c.CENTRAL_ENUM_VALUE_SETS["day1_priority_tier"], failures, f"PR159R_BAD_PRIORITY:{target_id}")
        _require(bool(record.get("official_source_refs_checked")), failures, f"PR159R_TARGET_WITHOUT_OFFICIAL_SOURCE_REFS:{target_id}")
        accepted_state = str(record.get("final_PR159R_target_state")).startswith("ACCEPTED_SOURCE")
        if accepted_state:
            _require(record.get("accepted_value_or_range_or_enum_or_metadata") is not None, failures, f"PR159R_ACCEPTED_TARGET_VALUE_MISSING:{target_id}")
            _require(record.get("acceptance_blocker_class") == c.AcceptanceBlockerClass.NONE.value, failures, f"PR159R_ACCEPTED_TARGET_HAS_BLOCKER:{target_id}")
            _require(bool(record.get("PR159R_accepted_packet_ref_or_null")), failures, f"PR159R_ACCEPTED_TARGET_PACKET_REF_MISSING:{target_id}")
        else:
            _require(record.get("accepted_value_or_range_or_enum_or_metadata") is None, failures, f"PR159R_UNACCEPTED_TARGET_HAS_VALUE:{target_id}")


def _validate_requeue(requeue_report: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(requeue_report)
    _require(len(records) == 3, failures, "PR159R_REQUEUE_RECORD_COUNT_NOT_3")
    for record in records:
        _require(record.get("incremented_PR159R_869_target_universe_flag") is False, failures, "PR159R_REQUEUE_DOUBLE_COUNTED")
        _require(record.get("double_count_prevented_flag") is True, failures, "PR159R_REQUEUE_DOUBLE_COUNT_FLAG_FALSE")


def _validate_candidate_packets(
    candidate_registry: Mapping[str, Any],
    accepted_registry: Mapping[str, Any],
    failures: list[str],
) -> None:
    accepted_candidate_ids = {
        str(record.get("candidate_packet_id"))
        for record in _records(accepted_registry)
    }
    for record in _records(candidate_registry):
        packet_id = str(record.get("candidate_packet_id"))
        accepted_candidate = packet_id in accepted_candidate_ids
        _require(record.get("candidate_is_accepted_fact") is False, failures, f"PR159R_CANDIDATE_ACCEPTED_FACT:{packet_id}")
        _require(record.get("official_source_confidence") in c.CENTRAL_ENUM_VALUE_SETS["official_source_confidence"], failures, f"PR159R_BAD_CANDIDATE_CONFIDENCE:{packet_id}")
        _require(record.get("official_source_class") in c.CENTRAL_ENUM_VALUE_SETS["official_source_class"], failures, f"PR159R_BAD_CANDIDATE_SOURCE_CLASS:{packet_id}")
        locator = as_mapping(record.get("quote_span_or_machine_field_locator"))
        _require(bool(locator.get("locator") or locator.get("quote_span") or locator.get("machine_field_locator")), failures, f"PR159R_CANDIDATE_LOCATOR_MISSING:{packet_id}")
        if accepted_candidate:
            _require(record.get("extracted_value_or_range_or_enum_or_null") is not None, failures, f"PR159R_ACCEPTED_CANDIDATE_VALUE_MISSING:{packet_id}")
            _require(record.get("target_field_scope_match_flag") is True, failures, f"PR159R_ACCEPTED_CANDIDATE_SCOPE_MISMATCH:{packet_id}")
            _require(record.get("accepted_packet_ref_or_null") is not None, failures, f"PR159R_ACCEPTED_CANDIDATE_PACKET_REF_MISSING:{packet_id}")
        else:
            _require(record.get("extracted_value_or_range_or_enum_or_null") is None, failures, f"PR159R_CANDIDATE_INVENTED_VALUE:{packet_id}")
            _require(record.get("target_field_scope_match_flag") is False, failures, f"PR159R_CANDIDATE_SCOPE_MATCH_SHOULD_BE_FALSE:{packet_id}")


def _validate_accepted_packets(accepted_registry: Mapping[str, Any], ledger_registry: Mapping[str, Any], failures: list[str]) -> None:
    accepted = _records(accepted_registry)
    ledger = _records(ledger_registry)
    ledger_ids = {str(record.get("accepted_packet_id")) for record in ledger}
    _require(len(accepted) == len(ledger), failures, "PR159R_ACCEPTED_LEDGER_COUNT_MISMATCH")
    for record in accepted:
        packet_id = str(record.get("accepted_packet_id"))
        _require(record.get("official_source_confidence") == c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value, failures, f"PR159R_ACCEPTED_NOT_CONFIRMED:{packet_id}")
        _require(record.get("target_field_scope_match_flag") is True, failures, f"PR159R_ACCEPTED_SCOPE_MISMATCH:{packet_id}")
        _require(record.get("locator_valid_flag") is True, failures, f"PR159R_ACCEPTED_LOCATOR_INVALID:{packet_id}")
        _require(record.get("conflict_cleared_flag") is True, failures, f"PR159R_ACCEPTED_CONFLICT_NOT_CLEAR:{packet_id}")
        _require(record.get("freshness_valid_flag") is True, failures, f"PR159R_ACCEPTED_FRESHNESS_INVALID:{packet_id}")
        _require(record.get("accepted_value_or_range_or_enum_or_metadata") is not None, failures, f"PR159R_ACCEPTED_VALUE_MISSING:{packet_id}")
        _require(record.get("canonical_unit_or_basis") is not None, failures, f"PR159R_ACCEPTED_UNIT_MISSING:{packet_id}")
        _require(record.get("canonical_scale") is not None, failures, f"PR159R_ACCEPTED_SCALE_MISSING:{packet_id}")
        _require(record.get("unit_scale_canonicalized_flag") is True, failures, f"PR159R_ACCEPTED_UNIT_SCALE_NOT_CANONICAL:{packet_id}")
        _require(packet_id in ledger_ids, failures, f"PR159R_ACCEPTED_PACKET_WITHOUT_LEDGER:{packet_id}")
        for flag in (
            "no_connector_semantic_binding_confirmation",
            "no_runtime_receipt_confirmation",
            "no_live_order_authority_confirmation",
            "no_profit_evidence_confirmation",
            "no_quantum_backend_execution_confirmation",
        ):
            _require(record.get(flag) is True, failures, f"PR159R_ACCEPTED_AUTHORITY_FLAG_MISSING:{packet_id}:{flag}")


def _validate_fill_paths(master_report: Mapping[str, Any], fill_path_report: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(fill_path_report)
    unresolved_count = as_mapping(master_report.get("count_invariant_receipt")).get("unresolved_after_PR159R_count")
    _require(len(records) == unresolved_count, failures, "PR159R_FILL_PATH_COUNT_NOT_UNRESOLVED_COUNT")
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        for field in (
            "attempted_official_queries",
            "official_sources_checked",
            "exact_missing_evidence",
            "exact_next_official_source_needed",
            "exact_steps_to_fill",
            "validator_that_will_unblock",
            "future_PR_route",
            "responsible_actor_or_agent_role",
            "risk_if_unfilled",
        ):
            _require(bool(record.get(field)), failures, f"PR159R_FILL_PATH_MISSING_{field}:{target_id}")
        _require(record.get("unresolved_value_or_null") is None, failures, f"PR159R_UNRESOLVED_VALUE_NOT_NULL:{target_id}")
        for flag in ("can_qtt_use_in_replay_flag", "can_qtt_use_in_paper_flag", "can_qtt_use_in_live_flag"):
            _require(record.get(flag) is False, failures, f"PR159R_UNRESOLVED_FORBIDDEN_USE:{target_id}:{flag}")


def _validate_agent_matrix(agent_report: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(agent_report)
    _require(len(records) == 869, failures, "PR159R_AGENT_MATRIX_COUNT_NOT_869")
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        _require(record.get("no_orphan_status") in c.CENTRAL_ENUM_VALUE_SETS["no_orphan_status"], failures, f"PR159R_BAD_NO_ORPHAN_STATUS:{target_id}")
        _require(record.get("no_orphan_status") != c.NoOrphanStatus.ORPHAN_BLOCKED_NO_RESPONSIBLE_ROUTE.value, failures, f"PR159R_ORPHAN_TARGET:{target_id}")
        _require(bool(record.get("responsible_agent_role_ids")) or bool(record.get("consumer_class_ids")), failures, f"PR159R_TARGET_WITHOUT_AGENT_OR_CONSUMER:{target_id}")
        if record.get("exact_agent_id_or_null") is not None:
            _require(record.get("exact_agent_id_supported_by_existing_artifact_flag") is True, failures, f"PR159R_EXACT_AGENT_ID_UNSUPPORTED:{target_id}")


def _validate_quantum(quantum_report: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(quantum_report)
    _require(len(records) == 869, failures, "PR159R_QUANTUM_BRIDGE_COUNT_NOT_869")
    unclassified = [
        str(record.get("target_id_or_row_id"))
        for record in records
        if record.get("quantum_relevance_flag") is True
        and not record.get("quantum_optimizer_readiness_class")
    ]
    _require(not unclassified, failures, f"PR159R_QUANTUM_RELEVANT_UNCLASSIFIED:{','.join(unclassified[:5])}")
    for record in records:
        if record.get("quantum_relevance_flag") is True:
            target_id = str(record.get("target_id_or_row_id"))
            _require(record.get("classical_baseline_required_flag") is True, failures, f"PR159R_QUANTUM_WITHOUT_CLASSICAL_BASELINE:{target_id}")
            _require(record.get("replay_paper_quantum_comparison_required_flag") is True, failures, f"PR159R_QUANTUM_WITHOUT_REPLAY_PAPER_ROUTE:{target_id}")
            _require(record.get("future_PR169_quantum_backend_gated_sandbox_route") == c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value, failures, f"PR159R_QUANTUM_WITHOUT_PR169_ROUTE:{target_id}")


def _validate_second_pass_attempt_matrix(
    matrix_report: Mapping[str, Any],
    accepted_registry: Mapping[str, Any],
    failures: list[str],
) -> None:
    records = _records(matrix_report)
    accepted_by_target = {
        str(record.get("target_id_or_row_id")): str(record.get("accepted_packet_id"))
        for record in _records(accepted_registry)
    }
    _require(len(records) == 869, failures, "PR159R_SECOND_PASS_ATTEMPT_MATRIX_COUNT_NOT_869")
    ids = [str(record.get("target_id_or_row_id")) for record in records]
    _require(len(ids) == len(set(ids)), failures, "PR159R_SECOND_PASS_ATTEMPT_MATRIX_DUPLICATE_TARGET")
    for record in records:
        target_id = str(record.get("target_id_or_row_id"))
        accepted_ref = record.get("accepted_packet_ref_or_null")
        accepted = target_id in accepted_by_target
        _require(record.get("quantum_relevance_flag") in {True, False}, failures, f"PR159R_SECOND_PASS_BAD_QUANTUM_FLAG:{target_id}")
        _require(bool(record.get("official_sources_attempted")), failures, f"PR159R_SECOND_PASS_NO_SOURCES_ATTEMPTED:{target_id}")
        if accepted:
            _require(record.get("accepted_packet_possible_flag") is True, failures, f"PR159R_SECOND_PASS_ACCEPTED_NOT_POSSIBLE:{target_id}")
            _require(accepted_ref == accepted_by_target[target_id], failures, f"PR159R_SECOND_PASS_ACCEPTED_REF_MISMATCH:{target_id}")
            for field in (
                "exact_target_field_match_flag",
                "exact_value_or_metadata_available_flag",
                "exact_locator_available_flag",
                "unit_scale_available_flag",
                "freshness_available_flag",
                "conflict_clearance_available_flag",
            ):
                _require(record.get(field) is True, failures, f"PR159R_SECOND_PASS_ACCEPTED_FIELD_FALSE:{target_id}:{field}")
            _require(record.get("rejection_reason_if_not_accepted") is None, failures, f"PR159R_SECOND_PASS_ACCEPTED_HAS_REJECTION:{target_id}")
        else:
            _require(record.get("accepted_packet_possible_flag") is False, failures, f"PR159R_SECOND_PASS_UNACCEPTED_MARKED_POSSIBLE:{target_id}")
            _require(accepted_ref is None, failures, f"PR159R_SECOND_PASS_UNACCEPTED_HAS_PACKET:{target_id}")
            _require(record.get("rejection_reason_if_not_accepted") in c.CENTRAL_ENUM_VALUE_SETS["acceptance_blocker_class"], failures, f"PR159R_SECOND_PASS_BAD_REJECTION:{target_id}")
            _require(bool(record.get("exact_next_action")), failures, f"PR159R_SECOND_PASS_NEXT_ACTION_MISSING:{target_id}")


def _validate_source_family_reuse_matrix(matrix_report: Mapping[str, Any], failures: list[str]) -> None:
    records = _records(matrix_report)
    _require(bool(records), failures, "PR159R_SOURCE_FAMILY_REUSE_MATRIX_EMPTY")
    for record in records:
        family_id = str(record.get("source_family_id"))
        _require(bool(record.get("official_source_refs")), failures, f"PR159R_SOURCE_FAMILY_NO_SOURCE_REFS:{family_id}")
        _require(isinstance(record.get("target_ids_supported"), list), failures, f"PR159R_SOURCE_FAMILY_BAD_SUPPORTED_TARGETS:{family_id}")
        _require(record.get("conflict_check_status") in c.CENTRAL_ENUM_VALUE_SETS["conflict_status"], failures, f"PR159R_SOURCE_FAMILY_BAD_CONFLICT:{family_id}")
        _require(record.get("freshness_status") in c.CENTRAL_ENUM_VALUE_SETS["freshness_state"], failures, f"PR159R_SOURCE_FAMILY_BAD_FRESHNESS:{family_id}")
        if record.get("acceptance_possible_flag") is True:
            _require(bool(record.get("target_ids_supported")), failures, f"PR159R_SOURCE_FAMILY_ACCEPTANCE_WITHOUT_TARGET:{family_id}")
            _require(record.get("acceptance_blocker_if_not_possible") is None, failures, f"PR159R_SOURCE_FAMILY_ACCEPTED_HAS_BLOCKER:{family_id}")
        else:
            _require(record.get("acceptance_blocker_if_not_possible") in c.CENTRAL_ENUM_VALUE_SETS["acceptance_blocker_class"], failures, f"PR159R_SOURCE_FAMILY_BAD_BLOCKER:{family_id}")


def _validate_completion_alignment(
    master_report: Mapping[str, Any],
    pr154_completion: Mapping[str, Any],
    atomic_completion: Mapping[str, Any],
    pr161_handoff: Mapping[str, Any],
    accepted_registry: Mapping[str, Any],
    failures: list[str],
) -> None:
    counts = as_mapping(master_report.get("count_invariant_receipt"))
    accepted_ids = {str(record.get("accepted_packet_id")) for record in _records(accepted_registry)}
    pr154_ready = [record for record in _records(pr154_completion) if record.get("source_completed_flag") is True]
    atomic_ready = [record for record in _records(atomic_completion) if record.get("source_ready_flag") is True]
    _require(len(pr154_ready) == counts.get("pr154_source_completed_count"), failures, "PR159R_PR154_COMPLETION_COUNT_MISMATCH")
    _require(len(atomic_ready) == counts.get("atomicrows_source_ready_count"), failures, "PR159R_ATOMICROWS_READY_COUNT_MISMATCH")
    _require(_records(pr161_handoff) == [] or len(_records(pr161_handoff)) == counts.get("atomicrows_requires_PR161_materialization_count"), failures, "PR159R_PR161_HANDOFF_COUNT_MISMATCH")
    for record in pr154_ready + atomic_ready:
        packet_ref = str(record.get("accepted_source_packet_ref_or_null"))
        _require(packet_ref in accepted_ids, failures, f"PR159R_COMPLETION_WITHOUT_ACCEPTED_PACKET:{record.get('target_id_or_row_id')}")


def _placeholder_value_failures(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if "value" in key.lower() and isinstance(child, str) and child in c.FORBIDDEN_PLACEHOLDER_VALUES:
                failures.append(f"PR159R_PLACEHOLDER_AS_VALUE:{child_path}:{child}")
            failures.extend(_placeholder_value_failures(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_placeholder_value_failures(child, f"{path}[{index}]"))
    return failures


def _validate_no_authority(payloads: Iterable[Mapping[str, Any]], failures: list[str]) -> None:
    for payload in payloads:
        no_authority = as_mapping(payload.get("no_authority_confirmation"))
        if no_authority:
            _require(all(value is False for value in no_authority.values()), failures, "PR159R_NO_AUTHORITY_FLAG_TRUE")
        for record in _records(payload):
            item_auth = as_mapping(record.get("no_authority_confirmation"))
            if item_auth:
                _require(all(value is False for value in item_auth.values()), failures, "PR159R_RECORD_NO_AUTHORITY_FLAG_TRUE")
            text = " ".join(str(value) for value in record.values())
            for forbidden in (
                "profit_superiority",
                "latency_superiority_claim",
                "optimizer_execution_result",
                "quantum_backend_execution_result",
                "live_order_authority",
            ):
                _require(forbidden not in text, failures, f"PR159R_FORBIDDEN_AUTHORITY_TEXT:{forbidden}")


def _validate_currentness(root: Path, failures: list[str]) -> None:
    expected = build_artifacts(root)
    for rel_path, payload in expected.payloads.items():
        full_path = root / rel_path
        if full_path.exists() and full_path.read_text(encoding="utf-8") != json_dump(payload):
            failures.append(f"PR159R_GENERATED_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{rel_path}")
    for rel_path, payload in expected.markdown_payloads.items():
        full_path = root / rel_path
        if full_path.exists() and full_path.read_text(encoding="utf-8") != payload:
            failures.append(f"PR159R_MARKDOWN_ARTIFACT_NOT_DETERMINISTIC_CURRENT:{rel_path}")


def validate_existing_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    receipts: list[str] = []
    _validate_branch(root, failures, receipts)
    payloads = {path: _load(root, path, failures) for path in c.ALL_JSON_ARTIFACT_PATHS}
    if not (root / c.HUMAN_SUMMARY_PATH).exists():
        failures.append(f"PR159R_MARKDOWN_ARTIFACT_MISSING:{c.HUMAN_SUMMARY_PATH.as_posix()}")
    if failures:
        return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))

    master = payloads[c.MASTER_REPORT_PATH]
    target_registry = payloads[c.TARGET_RECONCILIATION_REGISTRY_PATH]
    requeue = payloads[c.PR160_REQUEUE_RECONCILIATION_PATH]
    candidate_registry = payloads[c.CANDIDATE_PACKET_REGISTRY_PATH]
    accepted_registry = payloads[c.ACCEPTED_PACKET_REGISTRY_PATH]
    ledger_registry = payloads[c.TARGET_FIELD_LEDGER_REGISTRY_PATH]
    fill_paths = payloads[c.UNRESOLVED_EXACT_FILL_PATH_PATH]
    agent_matrix = payloads[c.TARGET_AGENT_MATRIX_PATH]
    quantum_bridge = payloads[c.QUANTUM_UPSTREAM_DOWNSTREAM_BRIDGE_PATH]
    second_pass_attempt_matrix = payloads[c.SECOND_PASS_EXACT_ACCEPTANCE_ATTEMPT_MATRIX_PATH]
    source_family_reuse_matrix = payloads[c.SOURCE_FAMILY_REUSABLE_ACCEPTANCE_MATRIX_PATH]
    pr154_completion = payloads[c.PR154_SOURCE_COMPLETION_REGISTRY_PATH]
    atomic_completion = payloads[c.ATOMICROWS_SOURCE_READY_REGISTRY_PATH]
    pr161_handoff = payloads[c.PR161_MATERIALIZATION_HANDOFF_PATH]

    _validate_receipts(master, failures)
    _validate_counts(master, failures)
    _validate_targets(target_registry, failures)
    _validate_requeue(requeue, failures)
    _validate_candidate_packets(candidate_registry, accepted_registry, failures)
    _validate_accepted_packets(accepted_registry, ledger_registry, failures)
    _validate_fill_paths(master, fill_paths, failures)
    _validate_agent_matrix(agent_matrix, failures)
    _validate_quantum(quantum_bridge, failures)
    _validate_second_pass_attempt_matrix(second_pass_attempt_matrix, accepted_registry, failures)
    _validate_source_family_reuse_matrix(source_family_reuse_matrix, failures)
    _validate_completion_alignment(
        master,
        pr154_completion,
        atomic_completion,
        pr161_handoff,
        accepted_registry,
        failures,
    )
    for path, payload in payloads.items():
        failures.extend(_placeholder_value_failures(payload, path.as_posix()))
    _validate_no_authority(payloads.values(), failures)
    _validate_currentness(root, failures)
    return ValidationResult(tuple(sorted(set(failures))), tuple(receipts))
