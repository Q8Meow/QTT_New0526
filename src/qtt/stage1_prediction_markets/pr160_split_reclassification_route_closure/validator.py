"""Fail-closed validator for PR160 generated artifacts."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from tools import ci_branch_context

from . import constants as c
from .io import as_list, as_mapping, json_dump, read_json
from .models import ValidationResult
from .report import build_artifacts


_PR159R_DETACHED_HEAD_REPAIR_BRANCH_CONTEXT = (
    "repair/pr159r-detached-head-branch-context"
)
_PR160_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES = (
    c.BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCH,
    c.PR159S_DOWNSTREAM_OPEN_INTAKE_REPAIR_BRANCH,
    "repair/pr160-main-ancestry-after-pr176",
)
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


def _require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def _load(root: Path, rel_path: Path, failures: list[str]) -> Mapping[str, Any]:
    full_path = root / rel_path
    if not full_path.exists():
        failures.append(f"PR160_GENERATED_ARTIFACT_MISSING:{rel_path.as_posix()}")
        return {}
    payload = read_json(full_path)
    if not isinstance(payload, dict):
        failures.append(f"PR160_GENERATED_ARTIFACT_NOT_OBJECT:{rel_path.as_posix()}")
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
    return helper(
        root,
        branch,
        git_stdout=_git_stdout,
    )


def _pr160_ancestry_present(root: Path, *, refresh_shallow: bool = False) -> bool:
    return _branch_merged_ancestry_present(
        root,
        c.EXPECTED_BRANCH,
        refresh_shallow=refresh_shallow,
    )


def _pr160_or_repair_ancestry_present(
    root: Path,
    branch_context: str = "",
    *,
    refresh_shallow: bool = False,
) -> bool:
    if _pr160_ancestry_present(root, refresh_shallow=refresh_shallow):
        return True
    ancestry_branches = list(_PR160_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES)
    normalized = ci_branch_context.normalize_branch_context(branch_context)
    if (
        normalized
        and normalized in _PR160_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES
        and normalized not in ancestry_branches
    ):
        ancestry_branches.append(normalized)
    return any(
        _branch_merged_ancestry_present(root, branch, refresh_shallow=refresh_shallow)
        for branch in ancestry_branches
    )


def _pr160_branch_context_allowed(branch_context: str) -> bool:
    normalized = ci_branch_context.normalize_branch_context(branch_context)
    return normalized in {
        c.EXPECTED_BRANCH,
        c.PR159R_DOWNSTREAM_SOURCE_CAPTURE_BRANCH,
        c.PR159S_DOWNSTREAM_OPEN_INTAKE_BRANCH,
        _PR161A_DOWNSTREAM_BRANCH,
        _PR161B_DOWNSTREAM_BRANCH,
        _PR161C_DOWNSTREAM_BRANCH,
        _PR161D_DOWNSTREAM_BRANCH,
        _PR161E_DOWNSTREAM_BRANCH,
        _PR161F_DOWNSTREAM_BRANCH,
        _PR162_DOWNSTREAM_BRANCH,
        _PR162A_DOWNSTREAM_BRANCH,
        _PR162B_DOWNSTREAM_BRANCH,
        _PR162C_DOWNSTREAM_BRANCH,
        _PR162D_DOWNSTREAM_BRANCH,
        *_PR160_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES,
    }


def _pr159r_detached_head_repair_head_ref_allowed() -> bool:
    return (
        ci_branch_context.github_actions_head_ref_branch_context()
        == _PR159R_DETACHED_HEAD_REPAIR_BRANCH_CONTEXT
    )


def _pr160_detached_ci_context_allowed(root: Path) -> bool:
    branch_context = ci_branch_context.github_actions_branch_context()
    if (
        _pr160_branch_context_allowed(branch_context)
        or _pr159r_detached_head_repair_head_ref_allowed()
    ):
        return True
    if branch_context:
        return False
    return _pr160_or_repair_ancestry_present(root)


def _pr160_repair_branch_allowed(root: Path, branch: str) -> bool:
    return (
        ci_branch_context.normalize_branch_context(branch)
        in _PR160_BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCHES
        and _pr160_or_repair_ancestry_present(root, branch)
    )


def _validate_branch(root: Path, failures: list[str], receipts: list[str]) -> None:
    branch_rc, git_branch, _branch_err = _git_stdout(root, ["branch", "--show-current"])
    if ci_branch_context.github_actions_pull_request_detached_context_active(
        branch_returncode=branch_rc,
        branch=git_branch,
    ):
        if _pr160_detached_ci_context_allowed(root):
            receipts.append(c.PR160_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY)
            return
        failures.append("PR160_BLOCKED_WRONG_BRANCH:DETACHED_HEAD")
        return

    context = ci_branch_context.current_branch_context(root, git_stdout=_git_stdout)
    branch = context.branch
    if branch in {
        c.EXPECTED_BRANCH,
        c.PR159R_DOWNSTREAM_SOURCE_CAPTURE_BRANCH,
        c.PR159S_DOWNSTREAM_OPEN_INTAKE_BRANCH,
        _PR161A_DOWNSTREAM_BRANCH,
        _PR161B_DOWNSTREAM_BRANCH,
        _PR161C_DOWNSTREAM_BRANCH,
        _PR161D_DOWNSTREAM_BRANCH,
        _PR161E_DOWNSTREAM_BRANCH,
        _PR161F_DOWNSTREAM_BRANCH,
        _PR162_DOWNSTREAM_BRANCH,
        _PR162A_DOWNSTREAM_BRANCH,
        _PR162B_DOWNSTREAM_BRANCH,
        _PR162C_DOWNSTREAM_BRANCH,
        _PR162D_DOWNSTREAM_BRANCH,
    }:
        return
    if ci_branch_context.github_actions_main_push_context_active():
        ancestry_present = _pr160_or_repair_ancestry_present(
            root,
            refresh_shallow=True,
        )
        if branch == "main" and ancestry_present:
            receipts.append(c.PR160_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY)
            return
        failures.append(f"PR160_BLOCKED_WRONG_BRANCH:{branch or 'main'}")
        return
    ancestry_present = _pr160_or_repair_ancestry_present(root)
    if branch == "main" and ancestry_present:
        return
    if _pr160_repair_branch_allowed(root, branch):
        return
    failures.append(f"PR160_BLOCKED_WRONG_BRANCH:{branch or 'DETACHED_HEAD'}")


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
                "PR160_MANDATORY_CROSSWALK_OR_FALLBACK_NOT_CONSUMED",
            )
            continue
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item.get("exists") and item.get("consumed")),
            failures,
            f"PR160_MANDATORY_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    for path in c.MANDATORY_PR160_INPUTS:
        item = by_path.get(path.as_posix(), {})
        _require(
            bool(item.get("exists") and item.get("consumed")),
            failures,
            f"PR160_MANDATORY_PR160_INPUT_NOT_CONSUMED:{path.as_posix()}",
        )
    shard_count = sum(
        1
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("exists")
        and item.get("consumed")
    )
    _require(shard_count == 9, failures, "PR160_PR157_SHARDS_NOT_CONSUMED")
    _require(master_report.get("master_plan_consumed_confirmation") is True, failures, "PR160_MASTER_PLAN_NOT_CONSUMED")
    _require(master_report.get("master_plan_not_edited_confirmation") is True, failures, "PR160_MASTER_PLAN_EDITED_FLAG")
    _require(
        master_report.get("source_evidence_packet_consumed_confirmation") is True,
        failures,
        "PR160_SOURCE_EVIDENCE_PACKET_NOT_CONSUMED",
    )


def _validate_counts(master_report: Mapping[str, Any], decisions: list[Mapping[str, Any]], failures: list[str]) -> None:
    receipt = as_mapping(master_report.get("count_invariant_receipt"))
    _require(receipt.get("pr154_split_reclassification_input_count") == 33, failures, "PR160_INPUT_COUNT_NOT_33")
    _require(receipt.get("split_records_processed_count") == 33, failures, "PR160_PROCESSED_COUNT_NOT_33")
    _require(receipt.get("final_route_decision_count") == 33, failures, "PR160_DECISION_COUNT_NOT_33")
    _require(receipt.get("one_final_route_per_record_count") == 33, failures, "PR160_ONE_ROUTE_COUNT_NOT_33")
    _require(receipt.get("generic_split_blocker_remaining_count") == 0, failures, "PR160_GENERIC_SPLIT_REMAINING")
    _require(receipt.get("total_pr154_universe_count") == 342, failures, "PR160_PR154_UNIVERSE_CHANGED")
    _require(receipt.get("total_atomicrows_universe_count") == 4183, failures, "PR160_ATOMICROWS_UNIVERSE_CHANGED")
    _require(receipt.get("count_invariants_passed_flag") is True, failures, "PR160_COUNT_INVARIANTS_FAILED")
    _require(len(decisions) == 33, failures, "PR160_DECISION_RECORDS_NOT_33")
    ids = [str(item.get("PR154_target_id")) for item in decisions]
    _require(len(ids) == len(set(ids)), failures, "PR160_DUPLICATE_TARGET_ID")


def _validate_decisions(decisions: list[Mapping[str, Any]], failures: list[str]) -> None:
    valid_routes = set(c.CENTRAL_ENUM_VALUE_SETS["final_route_class"])
    valid_blockers = set(c.CENTRAL_ENUM_VALUE_SETS["blocker_class"])
    valid_basis = set(c.CENTRAL_ENUM_VALUE_SETS["basis_class"])
    valid_authority = set(c.CENTRAL_ENUM_VALUE_SETS["authority_class"])
    valid_future = set(c.CENTRAL_ENUM_VALUE_SETS["future_route"])
    valid_compat = set(c.CENTRAL_ENUM_VALUE_SETS["quantum_classical_compatibility"])
    for item in decisions:
        target_id = str(item.get("PR154_target_id"))
        route = item.get("final_route_class")
        _require(route in valid_routes, failures, f"PR160_BAD_ROUTE:{target_id}")
        _require(item.get("one_final_route_flag") is True, failures, f"PR160_NOT_ONE_ROUTE:{target_id}")
        _require(
            item.get("generic_split_reclassification_state_remaining_flag") is False,
            failures,
            f"PR160_GENERIC_SPLIT_LEFT:{target_id}",
        )
        _require(item.get("blocker_class") in valid_blockers, failures, f"PR160_BAD_BLOCKER:{target_id}")
        _require(item.get("basis_class") in valid_basis, failures, f"PR160_BAD_BASIS:{target_id}")
        _require(item.get("authority_class") in valid_authority, failures, f"PR160_BAD_AUTHORITY:{target_id}")
        _require(item.get("future_pr_route") in valid_future, failures, f"PR160_BAD_FUTURE_ROUTE:{target_id}")
        _require(bool(item.get("basis_artifact_refs")), failures, f"PR160_NO_BASIS_REFS:{target_id}")
        for field in (
            "exact_next_action",
            "required_actor",
            "required_input_artifact",
            "validator_that_will_unblock",
            "risk_if_unresolved",
        ):
            _require(bool(item.get(field)), failures, f"PR160_DEPENDENCY_FIELD_MISSING:{target_id}:{field}")
        for value in as_list(item.get("quantum_classical_compatibility")):
            _require(value in valid_compat, failures, f"PR160_BAD_QUANTUM_COMPAT:{target_id}:{value}")
        for flag in (
            "can_qtt_use_in_replay_flag",
            "can_qtt_use_in_paper_flag",
            "can_qtt_use_in_live_flag",
            "source_acceptance_executed_flag",
            "source_value_materialized_flag",
            "owner_approval_created_flag",
            "private_doc_attestation_created_flag",
            "exact_agent_id_created_flag",
            "connector_semantic_binding_created_flag",
            "runtime_receipt_created_flag",
            "scoring_ranking_selection_execution_created_flag",
            "optimizer_execution_created_flag",
            "quantum_backend_execution_created_flag",
            "order_fill_profit_authority_created_flag",
        ):
            _require(item.get(flag) is False, failures, f"PR160_FORBIDDEN_FLAG_TRUE:{target_id}:{flag}")


def _validate_route_reports(
    root: Path,
    decisions: list[Mapping[str, Any]],
    failures: list[str],
) -> None:
    source_report = _load(root, c.PR159R_SOURCE_REQUEUE_PATH, failures)
    pr161_report = _load(root, c.PR161_MATERIALIZATION_ROUTE_PATH, failures)
    pr163_report = _load(root, c.PR163_AGENT_BINDING_ROUTE_PATH, failures)
    private_report = _load(root, c.PRIVATE_DOC_ROUTE_PATH, failures)
    owner_report = _load(root, c.OWNER_POLICY_ROUTE_PATH, failures)
    connector_report = _load(root, c.CONNECTOR_RUNTIME_ROUTE_PATH, failures)
    formula_report = _load(root, c.FORMULA_DERIVED_ROUTE_PATH, failures)
    source_records = _records(source_report)
    _require(len(source_records) == 3, failures, "PR160_PR159R_REQUEUE_COUNT_NOT_3")
    for record in source_records:
        target_id = str(record.get("PR154_target_id"))
        _require(record.get("accepted_source_packet_created_by_PR160_flag") is False, failures, f"PR160_SOURCE_PACKET_CREATED:{target_id}")
        _require(record.get("accepted_value_created_by_PR160_flag") is False, failures, f"PR160_SOURCE_VALUE_CREATED:{target_id}")
        _require(record.get("target_field_acceptance_ledger_created_by_PR160_flag") is False, failures, f"PR160_LEDGER_CREATED:{target_id}")
    _require(len(_records(pr161_report)) == 3, failures, "PR160_PR161_ROUTE_COUNT_NOT_3")
    _require(len(_records(pr163_report)) == 0, failures, "PR160_UNEXPECTED_PR163_ROUTE")
    _require(len(_records(private_report)) == 0, failures, "PR160_UNEXPECTED_PRIVATE_DOC_ROUTE")
    _require(len(_records(owner_report)) == 0, failures, "PR160_UNEXPECTED_OWNER_POLICY_ROUTE")
    _require(len(_records(connector_report)) == 3, failures, "PR160_CONNECTOR_RUNTIME_COUNT_NOT_3")
    _require(len(_records(formula_report)) == 15, failures, "PR160_FORMULA_DERIVED_METADATA_COUNT_NOT_15")
    _require(sum(1 for item in decisions if item.get("required_actor")) == 33, failures, "PR160_ORPHAN_ROUTE")


def _validate_metadata_updates(root: Path, failures: list[str]) -> None:
    for path, flag in (
        (c.SELECTION_UPDATE_PATH, "metadata_only_no_selection_execution"),
        (c.TRADE_CONTEXT_UPDATE_PATH, "metadata_only_no_trade_context_selection_execution"),
        (c.SCORING_RANKING_UPDATE_PATH, "metadata_only_no_scoring_execution"),
        (c.QUANTUM_COMPAT_UPDATE_PATH, "quantum_metadata_only_no_backend_execution"),
    ):
        records = _records(_load(root, path, failures))
        _require(len(records) == 33, failures, f"PR160_METADATA_UPDATE_COUNT_NOT_33:{path.as_posix()}")
        for record in records:
            _require(record.get(flag) is True, failures, f"PR160_METADATA_ONLY_FLAG_MISSING:{path.as_posix()}")
    _require(len(_records(_load(root, c.LOW_LATENCY_UPDATE_PATH, failures))) == 33, failures, "PR160_LOW_LATENCY_COUNT_NOT_33")
    _require(len(_records(_load(root, c.AGENT_RESPONSIBILITY_UPDATE_PATH, failures))) == 33, failures, "PR160_AGENT_COUNT_NOT_33")


def _validate_collision_and_owner_packet(root: Path, failures: list[str]) -> None:
    collision_records = _records(_load(root, c.ROUTE_COLLISION_AUDIT_PATH, failures))
    _require(len(collision_records) == 33, failures, "PR160_COLLISION_RECORD_COUNT_NOT_33")
    for record in collision_records:
        _require(record.get("unresolved_collision_blocked_flag") is False, failures, "PR160_UNRESOLVED_COLLISION")
    owner_packet = _load(root, c.OWNER_DECISION_PACKET_PATH, failures)
    _require(owner_packet.get("decision_required_count") == 0, failures, "PR160_UNEXPECTED_OWNER_DECISION_REQUIRED")
    _require(owner_packet.get("owner_response_file_created_by_PR160_flag") is False, failures, "PR160_FAKE_OWNER_RESPONSE")


def _placeholder_failures(value: Any, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, str):
        for token in ("PLACEHOLDER", "TODO", "TBD"):
            if token in value:
                failures.append(f"PR160_PLACEHOLDER_VALUE:{path}:{token}")
    elif isinstance(value, dict):
        for key, child in value.items():
            failures.extend(_placeholder_failures(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_placeholder_failures(child, f"{path}[{index}]"))
    return failures


def _validate_no_scattered_vocab(root: Path, failures: list[str]) -> None:
    src_dir = root / "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure"
    constants_text = (src_dir / "constants.py").read_text(encoding="utf-8")
    _require("class ReclassificationFinalRouteClass" in constants_text, failures, "PR160_ROUTE_ENUM_MISSING")
    _require("class BlockerClass" in constants_text, failures, "PR160_BLOCKER_ENUM_MISSING")
    for path in src_dir.glob("*.py"):
        if path.name == "constants.py":
            continue
        text = path.read_text(encoding="utf-8")
        _require(
            f'"{c.BlockerClass.MULTIPLE_PLAUSIBLE_ROUTES_OWNER_CHOICE_REQUIRED.value}"'
            not in text
            and f"'{c.BlockerClass.MULTIPLE_PLAUSIBLE_ROUTES_OWNER_CHOICE_REQUIRED.value}'"
            not in text
            and f'"{c.PR160TargetPopulation.PR154_SPLIT_RECLASSIFICATION_33.value}"'
            not in text
            and f"'{c.PR160TargetPopulation.PR154_SPLIT_RECLASSIFICATION_33.value}'"
            not in text,
            failures,
            f"PR160_SCATTERED_SPLIT_LITERAL:{path.name}",
        )
        _require(
            f'"{c.AuthorityProfile.PR160_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING.value}"'
            not in text
            and f"'{c.AuthorityProfile.PR160_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING.value}'"
            not in text,
            failures,
            f"PR160_SCATTERED_NO_AUTHORITY_LITERAL:{path.name}",
        )


def _validate_deterministic(root: Path, failures: list[str]) -> None:
    expected = build_artifacts(root)
    for rel_path, payload in expected.payloads.items():
        path = root / rel_path
        if not path.exists():
            continue
        actual_text = path.read_text(encoding="utf-8")
        expected_text = json_dump(payload)
        _require(actual_text == expected_text, failures, f"PR160_REPORT_NOT_DETERMINISTIC:{rel_path}")
    for rel_path, payload in expected.markdown_payloads.items():
        path = root / rel_path
        if not path.exists():
            continue
        _require(path.read_text(encoding="utf-8") == payload, failures, f"PR160_MARKDOWN_NOT_DETERMINISTIC:{rel_path}")


def _validate_master_plan_not_edited(root: Path, failures: list[str]) -> None:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", c.MASTER_PLAN_PATH.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        _require(not completed.stdout.strip(), failures, "PR160_MASTER_PLAN_EDITED")


def _validate_online_context(root: Path, failures: list[str]) -> None:
    path = root / c.ONLINE_CONTEXT_RECEIPTS_PATH
    if not path.exists():
        return
    records = _records(_load(root, c.ONLINE_CONTEXT_RECEIPTS_PATH, failures))
    for record in records:
        _require(record.get("accepted_source_authority_flag") is False, failures, "PR160_ONLINE_ACCEPTED_SOURCE_AUTHORITY")
        _require(record.get("accepted_value_authority_flag") is False, failures, "PR160_ONLINE_ACCEPTED_VALUE_AUTHORITY")
        _require(record.get("no_value_materialization_confirmation") is True, failures, "PR160_ONLINE_VALUE_MATERIALIZED")


def validate_existing_artifacts(repo_root: Path | str) -> ValidationResult:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    receipts: list[str] = []
    _validate_branch(root, failures, receipts)
    master_report = _load(root, c.MASTER_REPORT_PATH, failures)
    registry = _load(root, c.MASTER_REGISTRY_PATH, failures)
    ledger = _load(root, c.DECISION_LEDGER_REPORT_PATH, failures)
    _validate_receipts(master_report, failures)
    decisions = _records(registry)
    _validate_counts(master_report, decisions, failures)
    _require(len(_records(ledger)) == 33, failures, "PR160_LEDGER_COUNT_NOT_33")
    _validate_decisions(decisions, failures)
    _validate_route_reports(root, decisions, failures)
    _validate_metadata_updates(root, failures)
    _validate_collision_and_owner_packet(root, failures)
    _validate_online_context(root, failures)
    _validate_no_scattered_vocab(root, failures)
    _validate_master_plan_not_edited(root, failures)
    for rel_path in c.ALL_JSON_ARTIFACT_PATHS:
        payload = _load(root, rel_path, failures)
        failures.extend(_placeholder_failures(payload, rel_path.as_posix()))
    _require((root / c.HUMAN_SUMMARY_PATH).exists(), failures, "PR160_HUMAN_SUMMARY_MISSING")
    _validate_deterministic(root, failures)
    unique_failures = tuple(sorted(set(failures)))
    unique_receipts = tuple(dict.fromkeys(receipts)) if not unique_failures else ()
    return ValidationResult(unique_failures, unique_receipts)
