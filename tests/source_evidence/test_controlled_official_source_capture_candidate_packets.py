from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import subprocess

from tools import validate_controlled_official_source_capture_candidate_packets as pr153_cli

from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets import (
    constants as c,
    report as pr153_report,
    reason_codes as rc,
)
from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets.models import (
    OWNER_DECISION_OPTIONS,
    OWNER_NON_SOURCE_BACKED_STATUSES,
    owner_decision_receipt,
    owner_provided_external_fact_candidate,
)
from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets.reason_codes import (
    ALL_REASON_CODES,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _report() -> dict:
    return pr153_report.build_report(REPO_ROOT)


def _candidates() -> list[dict]:
    return _report()["source_capture_candidate_packets"]


def _unresolved() -> list[dict]:
    return _report()["unresolved_capture_targets"]


def _sample_unresolved() -> dict:
    return next(
        item
        for item in _unresolved()
        if item["blocker_primary_category"] != "TARGET_NOT_CAPTURE_CANDIDATE"
    )


def _sample_internal_unresolved(kind: str) -> dict:
    wanted = {
        "policy": "candidate_count",
        "architecture": "candidate_inventory_links",
    }[kind]
    return next(item for item in _unresolved() if item["target_field_id"] == wanted)


def test_pr153_consumes_route_triage() -> None:
    assert _report()["pr136_alignment_summary"]["route_triage_consumed"] is True


def test_pr153_consumes_section_crosswalk_or_alias() -> None:
    summary = _report()["pr136_alignment_summary"]
    assert summary["section_crosswalk_or_alias_consumed"] is True
    assert summary["crosswalk_alias_used"] is True
    alias = _report()["upstream_artifact_inputs"]["crosswalk_alias_resolution"]
    assert alias["created_missing_alias"] is False


def test_pr153_consumes_market_specific_index() -> None:
    assert _report()["pr136_alignment_summary"]["market_specific_index_consumed"] is True


def test_pr153_consumes_command_action_matrix() -> None:
    assert _report()["pr136_alignment_summary"]["command_action_matrix_consumed"] is True


def test_pr153_consumes_pr137r_and_pr138_atomicrows_artifacts() -> None:
    assert _report()["pr137r_atomicrows_reconciliation_consumption_summary"]["consumed"] is True
    assert _report()["pr138_atomicrows_semantic_row_contract_consumption_summary"]["consumed"] is True


def test_pr153_consumes_pr149_pr150_pr151_pr152_reports() -> None:
    report = _report()
    assert report["pr149_bridge_consumption_summary"]["consumed"] is True
    assert report["pr150_target_matrix_consumption_summary"]["consumed"] is True
    assert report["pr151_retrieval_target_pack_consumption_summary"]["consumed"] is True
    assert report["pr152_global_audit_consumption_summary"]["consumed"] is True


def test_pr153_consumes_owner_source_evidence_packet() -> None:
    summary = _report()["owner_source_evidence_packet_summary"]
    assert summary["consumed"] is True
    assert summary["owner_packet_authorizes_external_fact_value"] is False


def test_candidate_packets_map_to_pr151_targets() -> None:
    targets = {
        item["retrieval_target_id"]
        for item in json.loads((REPO_ROOT / c.PR151_REPORT_PATH).read_text())[
            "official_source_retrieval_target_queue"
        ]
    }
    assert {packet["retrieval_target_id"] for packet in _candidates()}.issubset(targets)


def test_candidate_packets_map_to_pr150_targets() -> None:
    pr150 = json.loads((REPO_ROOT / c.PR150_REPORT_PATH).read_text())
    targets = {
        item["target_id"]
        for item in pr150["parameter_default_target_matrix"]["parameter_target_items"]
    }
    assert {packet["pr150_target_ref"] for packet in _candidates()}.issubset(targets)


def test_batch_plan_exists() -> None:
    plan = _report()["capture_batch_plan"]
    assert len(plan) == 14
    assert plan[0]["batch_size"] == c.BATCH_SIZE


def test_batch_receipts_exist() -> None:
    receipts = _report()["capture_batch_receipts"]
    assert len(receipts) == len(_report()["capture_batch_plan"])
    assert all(row["batch_status"] for row in receipts)


def test_capture_progress_ledger_exists() -> None:
    ledger = _report()["capture_progress_ledger"]
    assert len(ledger) == _report()["pr151_retrieval_target_pack_consumption_summary"]["retrieval_target_count"]


def test_resume_cursor_exists() -> None:
    cursor = _report()["capture_resume_cursor"]
    assert cursor["resume_status"] == "NO_NEXT_BATCH_ALL_TARGETS_ATTEMPTED"
    assert cursor["candidate_packet_count"] == len(_candidates())


def test_candidate_packet_count_equals_pr151_target_count_when_full_success() -> None:
    summary = _report()["validation_summary"]
    if summary["full_capture_success"]:
        assert summary["candidate_packet_count"] == summary["pr151_target_count"]
    else:
        assert summary["candidate_packet_count"] < summary["pr151_target_count"]


def test_candidate_packet_count_equals_342_when_pr151_count_is_342_and_full_success() -> None:
    summary = _report()["validation_summary"]
    assert summary["pr151_target_count"] == 342
    if summary["full_capture_success"]:
        assert summary["candidate_packet_count"] == 342
    else:
        assert summary["candidate_packet_count"] != 342


def test_unresolved_capture_targets_empty_when_full_success() -> None:
    summary = _report()["validation_summary"]
    assert (len(_unresolved()) == 0) is summary["full_capture_success"]


def test_incomplete_capture_requires_blocker_triage() -> None:
    summary = _report()["validation_summary"]
    assert summary["status"] == c.INCOMPLETE_MARKER
    assert summary["blocker_triage_success"] is True
    assert all(item["blocker_primary_category"] for item in _unresolved())


def test_pr153a_completion_status_and_corrected_denominator() -> None:
    report = _report()
    completion = report["pr153_completion_status"]
    denominator = report["corrected_denominator_summary"]
    summary = report["validation_summary"]

    assert completion["full_capture_success"] is False
    assert completion["blocker_triage_success"] is True
    assert completion["completion_label"] == c.COMPLETION_LABEL
    assert completion["owner_approved_commit_framing"] == c.OWNER_APPROVED_COMMIT_FRAMING
    assert completion["not_full_342_capture_success"] is True
    assert completion["all_PR151_targets_accounted"] is True
    assert completion["total_accounted_targets"] == 342

    assert summary["full_capture_success"] is False
    assert summary["blocker_triage_success"] is True
    assert summary["completion_label"] == c.COMPLETION_LABEL
    assert summary["owner_approved_commit_framing"] == c.OWNER_APPROVED_COMMIT_FRAMING
    assert summary["all_PR151_targets_accounted"] is True
    assert summary["total_accounted_targets"] == 342

    assert denominator["total_PR151_targets"] == 342
    assert denominator["true_external_public_source_value_capture_target_count"] == 126
    assert denominator["captured_candidate_packet_count"] == 92
    assert denominator["remaining_external_public_capture_retry_target_count"] == 34
    assert denominator["internal_control_plane_target_count"] == 138
    assert denominator["target_split_or_reclassification_required_count"] == 33
    assert denominator["private_doc_or_attestation_required_count"] == 6
    assert denominator["owner_provided_value_candidate_route_count"] == 39
    assert denominator["pr154_acceptance_review_only_count"] == 92
    assert denominator["corrected_public_capture_denominator"] == 126


def test_owner_lane_routing_summary_matches_pr153a_audit() -> None:
    lanes = _report()["owner_approved_lane_routing_summary"]
    expected = {
        "INTERNAL_QTT_POLICY_OR_CONTROL_PLANE_TARGET": (
            "INTERNAL_POLICY_CONTROL_PLANE_ROUTE_APPROVED",
            138,
        ),
        "TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED": (
            "TARGET_SPLIT_RECLASSIFICATION_REVIEW_APPROVED",
            33,
        ),
        "PRIVATE_DOC_OR_ATTESTATION_REQUIRED": (
            "PRIVATE_DOC_ACCESS_RIGHTS_ATTESTATION_ROUTE_APPROVED",
            6,
        ),
        "OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE": (
            "OWNER_PROVIDED_CANDIDATE_ROUTE_ONLY_NON_SOURCE_BACKED",
            39,
        ),
        "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET": ("PR153R_RETRY_CAPTURE", 34),
        "PR154_ACCEPTANCE_REVIEW_ONLY": (
            "PR154_INDEPENDENT_REVIEW_OR_OWNER_NON_SOURCE_BACKED_OVERRIDE_ROUTE",
            92,
        ),
        "OWNER_DISAPPROVAL_OR_DESCOPE_CANDIDATE": ("AVAILABLE_BUT_NOT_USED", 0),
    }
    for lane, (route, count) in expected.items():
        assert lanes[lane]["owner_route"] == route
        assert lanes[lane]["count"] == count
        assert lanes[lane]["can_owner_override_external_fact_truth_as_source_backed"] is False


def test_owner_global_authority_override_preserves_external_fact_boundary() -> None:
    override = _report()["owner_global_authority_override_clarification"]
    assert override["owner_may_override_pr154_workflow_gate"] is True
    assert override["owner_may_defer_pr154_workflow_gate"] is True
    assert override["owner_may_bypass_pr154_workflow_gate_with_receipt"] is True
    assert override["owner_override_does_not_create_source_backed_truth"] is True
    assert override["owner_override_does_not_create_accepted_source_evidence"] is True
    assert tuple(override["allowed_owner_non_source_backed_statuses"]) == OWNER_NON_SOURCE_BACKED_STATUSES
    assert "OWNER_OVERRIDE_RECORDED_PR154_WORKFLOW_GATE_BYPASSED" in override["owner_override_statuses_supported"]
    assert "OWNER_OVERRIDE_RECORDED_EXTERNAL_FACT_STILL_NON_SOURCE_BACKED" in override["owner_override_statuses_supported"]
    assert override["owner_override_receipt_required"] is True
    assert override["owner_assumes_external_fact_risk"] is True
    assert override["downstream_consumer_warning_required"] is True
    assert override["connector_use_allowed_without_later_owner_command"] is False
    assert override["runtime_use_allowed_without_later_owner_command"] is False
    assert override["order_use_allowed_without_later_owner_command"] is False
    assert override["replay_paper_truth_use_allowed_without_later_owner_command"] is False
    assert override["launch_readiness_use_allowed_without_later_owner_command"] is False
    assert override["atomicrows_materialization_allowed_without_later_owner_command"] is False
    assert override["source_backed_fact_created"] is False
    assert override["accepted_source_evidence_packet_created"] is False
    assert override["official_value_accepted"] is False


def test_pr153r_retry_contract_and_pr154_or_owner_override_handoff() -> None:
    retry = _report()["pr153r_retry_capture_contract"]
    handoff = _report()["pr154_or_owner_override_handoff_contract"]
    assert retry["retry_target_count"] == 34
    assert retry["retry_scope"] == "EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET only"
    assert len(retry["retry_target_ids"]) == 34
    assert retry["no_internal_control_plane_rows_in_retry"] is True
    assert retry["no_target_split_reclassification_rows_in_retry"] is True
    assert retry["no_private_doc_attestation_rows_in_retry_without_owner_doc_packet"] is True
    assert retry["no_owner_provided_external_value_as_source_truth"] is True
    assert retry["PR154_or_owner_non_source_backed_override_route_required_after_retry"] is True

    assert handoff["captured_candidate_count"] == 92
    assert handoff["candidates_are_not_accepted_source_evidence"] is True
    assert handoff["pr154_independent_revalidation_available"] is True
    assert handoff["owner_non_source_backed_override_available"] is True
    assert handoff["owner_non_source_backed_override_requires_receipt"] is True
    assert handoff["owner_non_source_backed_override_preserves_risk_flags"] is True
    assert handoff["source_backed_truth_requires_PR154_or_later_accepted_source_evidence"] is True
    assert handoff["non_source_backed_owner_use_requires_explicit_owner_override_receipt"] is True
    assert handoff["connector_use_allowed_without_later_owner_command"] is False
    assert handoff["runtime_use_allowed_without_later_owner_command"] is False
    assert handoff["order_use_allowed_without_later_owner_command"] is False
    assert handoff["replay_paper_truth_use_allowed_without_later_owner_command"] is False
    assert handoff["launch_readiness_use_allowed_without_later_owner_command"] is False
    assert handoff["atomicrows_materialization_allowed_without_later_owner_command"] is False


def test_owner_external_fact_boundary_blocks_source_truth_and_downstream_use() -> None:
    boundary = _report()["owner_external_fact_boundary"]
    assert boundary["can_owner_override_internal_workflow_blocker"] is True
    assert boundary["can_owner_approve_internal_policy_route"] is True
    assert boundary["can_owner_provide_external_fact_candidate"] is True
    assert boundary["can_owner_override_pr154_workflow_gate"] is True
    assert boundary["can_owner_override_external_fact_truth_as_source_backed"] is False
    assert boundary["owner_authorized_non_source_backed_candidate_allowed"] is True
    assert (
        boundary[
            "owner_authorized_non_source_backed_runtime_value_pending_later_owner_command_allowed"
        ]
        is True
    )
    assert (
        boundary[
            "connector_runtime_order_live_atomicrows_use_blocked_without_later_gates_or_explicit_owner_override_receipt"
        ]
        is True
    )
    assert boundary["source_backed_fact_created"] is False
    assert boundary["accepted_source_evidence_packet_created"] is False
    assert boundary["official_value_accepted"] is False


def test_incomplete_capture_requires_owner_decision_options() -> None:
    assert all(tuple(item["owner_decision_options"]) == OWNER_DECISION_OPTIONS for item in _unresolved())


def test_candidate_packets_have_officiality_evidence() -> None:
    for packet in _candidates():
        evidence = packet["officiality_evidence"]
        assert evidence["source_url"] == packet["source_url"]
        assert evidence["source_domain"] == packet["source_domain"]
        assert evidence["official_source_class"] in c.OFFICIAL_SOURCE_CLASS_VALUES


def test_candidate_packets_have_quote_span_or_machine_field_locator() -> None:
    for packet in _candidates():
        locator = packet["quote_span_or_machine_field_locator"]
        assert locator["locator_type"] in {"QUOTE_SPAN", "MACHINE_FIELD_LOCATOR"}
        assert locator["quote_text_or_machine_locator"]


def test_candidate_packets_are_not_accepted_source_evidence() -> None:
    assert all(packet["acceptance_status"] == "NOT_ACCEPTED_CANDIDATE_ONLY" for packet in _candidates())
    assert all(packet["no_claim_flags"]["accepted_source_evidence_packet_created"] is False for packet in _candidates())


def test_candidate_packets_are_not_connector_binding() -> None:
    assert all(packet["connector_binding_status"] == "NOT_BOUND" for packet in _candidates())
    assert all(packet["no_claim_flags"]["connector_binding_created"] is False for packet in _candidates())


def test_candidate_packets_are_not_runtime_receipts() -> None:
    assert all(packet["runtime_receipt_status"] == "NOT_CREATED" for packet in _candidates())
    assert all(packet["no_claim_flags"]["runtime_cash_receipt_created"] is False for packet in _candidates())


def test_candidate_packets_are_not_live_or_order_authority() -> None:
    assert all(packet["order_use_eligibility"] == "NOT_ORDER_USABLE_CANDIDATE_ONLY" for packet in _candidates())
    assert all(packet["no_claim_flags"]["order_execution_created"] is False for packet in _candidates())


def test_candidate_packets_are_not_replay_paper_truth_inputs() -> None:
    assert all(
        packet["replay_paper_truth_use_eligibility"]
        == "NOT_REPLAY_PAPER_TRUTH_USABLE_CANDIDATE_ONLY"
        for packet in _candidates()
    )


def test_candidate_packets_are_not_launch_readiness_inputs() -> None:
    assert all(
        packet["launch_readiness_use_eligibility"]
        == "NOT_LAUNCH_READINESS_USABLE_CANDIDATE_ONLY"
        for packet in _candidates()
    )


def test_candidate_packets_do_not_mutate_atomicrows_bundle() -> None:
    surface = _report()["atomicrows_compatibility_surface"]
    assert surface["bundle_mutation_attempted"] is False
    assert surface["bundle_file_created"] is False
    assert surface["bundle_integrity_artifact_created"] is False


def test_quantum_provider_capture_does_not_execute_quantum_logic() -> None:
    surface = _report()["quantum_forward_capture_surface"]
    assert surface["provider_documentation_candidate_capture_allowed"] is True
    for key, value in surface.items():
        if key.endswith("_created"):
            assert value is False


def test_pr154_handoff_contract_requires_independent_revalidation() -> None:
    handoff = _report()["acceptance_handoff_contract_for_PR154"]
    assert handoff["accepted_fact_creation_allowed_in_pr153"] is False
    assert "exact official source" in handoff["pr154_must_independently_verify"]
    assert handoff["pr153_outputs_not_consumable_as_values"] is True


def test_zero_candidate_report_is_blocked() -> None:
    mutated = json.loads(pr153_report.json_dump(_report()))
    mutated["source_capture_candidate_packets"] = []
    mutated["validation_summary"]["candidate_packet_count"] = 0
    mutated["validation_summary"]["full_capture_success"] = True
    failures = pr153_report.validate_report(mutated, REPO_ROOT)
    assert "PR153_BLOCK_TARGET_COUNT_MISMATCH" in failures


def test_unresolved_target_report_is_not_full_success() -> None:
    summary = _report()["validation_summary"]
    assert summary["unresolved_target_count"] == len(_unresolved())
    assert summary["full_capture_success"] is False


def test_p0_p1_capture_attempt_receipts_present() -> None:
    ledger = _report()["capture_progress_ledger"]
    assert any(row["priority_class"] == "P0" for row in ledger)
    assert any(row["priority_class"] == "P1" for row in ledger)
    assert all(row["batch_id"].startswith("PR153_BATCH_") for row in ledger)


def test_owner_decision_options_exist_for_every_blocked_target() -> None:
    queue = _report()["owner_blocker_decision_layer"]["owner_decision_required_queue"]
    assert len(queue) == len(_unresolved())
    assert all(tuple(row["owner_decision_options"]) == OWNER_DECISION_OPTIONS for row in queue)


def test_owner_override_records_receipt() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_OVERRIDE_BLOCKER")
    assert receipt["owner_decision_type"] == "OWNER_OVERRIDE_BLOCKER"
    assert receipt["owner_decision_status"].startswith("OWNER_OVERRIDE_RECORDED")


def test_owner_override_does_not_create_external_fact_authority() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_OVERRIDE_BLOCKER")
    assert receipt["source_backed_fact_created"] is False
    assert receipt["accepted_source_evidence_packet_created"] is False
    assert receipt["pr154_acceptance_required_for_external_fact"] is True


def test_owner_approval_routes_to_pr154_review_only() -> None:
    receipt = owner_decision_receipt(
        _sample_unresolved(),
        "OWNER_APPROVE_BLOCKER_OR_CANDIDATE_FOR_NEXT_REVIEW",
    )
    assert receipt["owner_decision_status"] == "OWNER_APPROVED_FOR_PR154_REVIEW"
    assert receipt["connector_semantic_value_created"] is False


def test_owner_provided_internal_policy_value_allowed_for_internal_policy_field() -> None:
    receipt = owner_decision_receipt(
        _sample_internal_unresolved("policy"),
        "OWNER_PROVIDE_VALUE",
        owner_provided_value="OWNER_POLICY_VALUE_PLACEHOLDER",
    )
    assert receipt["owner_decision_status"] == "OWNER_PROVIDED_INTERNAL_POLICY_VALUE"
    assert receipt["is_internal_qtt_policy_field"] is True


def test_owner_provided_internal_architecture_value_allowed_for_internal_architecture_field() -> None:
    receipt = owner_decision_receipt(
        _sample_internal_unresolved("architecture"),
        "OWNER_PROVIDE_VALUE",
        owner_provided_value="OWNER_ARCHITECTURE_VALUE_PLACEHOLDER",
    )
    assert receipt["owner_decision_status"] == "OWNER_PROVIDED_INTERNAL_ARCHITECTURE_VALUE"
    assert receipt["is_internal_qtt_architecture_field"] is True


def test_owner_provided_external_fact_value_is_candidate_only() -> None:
    receipt = owner_decision_receipt(
        _sample_unresolved(),
        "OWNER_PROVIDE_VALUE",
        owner_provided_value="OWNER_EXTERNAL_FACT_CANDIDATE",
    )
    candidate = owner_provided_external_fact_candidate(receipt)
    assert candidate["owner_value_authority_class"] == "OWNER_PROVIDED_CANDIDATE_ONLY_NOT_SOURCE_BACKED"
    assert candidate["source_backed_fact_created"] is False
    assert candidate["accepted_source_evidence_packet_created"] is False
    assert candidate["official_value_accepted"] is False
    assert candidate["source_truth_status"] == "OWNER_AUTHORIZED_NON_SOURCE_BACKED"
    assert candidate["owner_override_receipt_required"] is True
    assert candidate["owner_assumes_external_fact_risk"] is True
    assert candidate["downstream_consumer_warning_required"] is True


def test_owner_provided_external_fact_value_requires_pr154_acceptance() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_PROVIDE_VALUE")
    candidate = owner_provided_external_fact_candidate(receipt)
    assert candidate["pr154_acceptance_required"] is True
    assert candidate["official_source_evidence_required"] is True


def test_owner_provided_external_fact_value_not_connector_usable() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_PROVIDE_VALUE")
    assert owner_provided_external_fact_candidate(receipt)["connector_use_allowed"] is False


def test_owner_provided_external_fact_value_not_runtime_usable() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_PROVIDE_VALUE")
    assert owner_provided_external_fact_candidate(receipt)["runtime_use_allowed"] is False


def test_owner_provided_external_fact_value_not_order_usable() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_PROVIDE_VALUE")
    assert owner_provided_external_fact_candidate(receipt)["order_use_allowed"] is False


def test_owner_provided_external_fact_value_not_launch_readiness_usable() -> None:
    receipt = owner_decision_receipt(_sample_unresolved(), "OWNER_PROVIDE_VALUE")
    assert owner_provided_external_fact_candidate(receipt)["launch_readiness_use_allowed"] is False


def test_owner_disapproval_keeps_target_blocked_and_preserves_history() -> None:
    unresolved = _sample_unresolved()
    receipt = owner_decision_receipt(unresolved, "OWNER_DISAPPROVE")
    assert receipt["owner_decision_status"] == "OWNER_DISAPPROVED_TARGET_BLOCKED"
    assert receipt["retrieval_target_id"] == unresolved["retrieval_target_id"]
    assert receipt["blocker_primary_category"] == unresolved["blocker_primary_category"]


def test_owner_decision_reason_codes_are_centralized() -> None:
    for code in (
        "PR153_OWNER_DECISION_REQUIRED",
        "PR153_OWNER_OVERRIDE_BLOCKER_RECORDED",
        "PR153_OWNER_VALUE_REQUIRES_PR154_ACCEPTANCE",
        "PR153_BLOCK_OWNER_PROVIDED_EXTERNAL_FACT_AS_ACCEPTED_SOURCE_TRUTH",
        rc.PR153_OWNER_APPROVED_CORRECTED_DENOMINATOR,
        rc.PR153_OWNER_APPROVED_BLOCKER_TRIAGE_ARCHITECTURE,
        rc.PR153_OWNER_MAY_OVERRIDE_PR154_WORKFLOW_GATE,
        rc.PR153_OWNER_OVERRIDE_DOES_NOT_CREATE_SOURCE_BACKED_TRUTH,
        rc.PR153_OWNER_AUTHORIZED_NON_SOURCE_BACKED_CANDIDATE_ALLOWED,
        rc.PR153_OWNER_AUTHORIZED_NON_SOURCE_BACKED_RUNTIME_VALUE_PENDING_LATER_OWNER_COMMAND_ALLOWED,
        rc.PR153_OWNER_OVERRIDE_RECEIPT_REQUIRED,
        rc.PR153_PR153R_RETRY_CAPTURE_REQUIRED_FOR_34_EXTERNAL_TARGETS,
        rc.PR153_PR154_OR_OWNER_OVERRIDE_HANDOFF_READY,
        rc.PR153_BLOCKER_TRIAGE_SUCCESS_NOT_FULL_CAPTURE_SUCCESS,
    ):
        assert code in ALL_REASON_CODES


def test_owner_decision_does_not_mutate_master_plan_or_atomicrows_bundle() -> None:
    master_before = (REPO_ROOT / c.MASTER_PLAN_PATH).read_bytes()
    bundle_before = (REPO_ROOT / c.ATOMICROWS_BUNDLE_PATH).read_bytes()
    owner_decision_receipt(_sample_unresolved(), "OWNER_OVERRIDE_BLOCKER")
    assert (REPO_ROOT / c.MASTER_PLAN_PATH).read_bytes() == master_before
    assert (REPO_ROOT / c.ATOMICROWS_BUNDLE_PATH).read_bytes() == bundle_before


def test_report_is_deterministic_across_repeated_generation() -> None:
    first = pr153_report.build_report(REPO_ROOT)
    second = pr153_report.build_report(REPO_ROOT)
    assert first == second
    assert pr153_report.json_dump(first) == pr153_report.json_dump(second)


def test_default_validator_non_mutating() -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before = report_path.read_bytes()
    assert pr153_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert report_path.read_bytes() == before


def test_validator_emits_blocker_triage_ok_not_full_capture_success(capsys) -> None:
    assert pr153_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    output = capsys.readouterr().out.strip()
    assert output == c.BLOCKER_TRIAGE_OK_MARKER
    assert output != c.SUCCESS_MARKER
    assert _report()["validation_summary"]["full_capture_success"] is False
    assert _report()["validation_summary"]["blocker_triage_success"] is True


def test_output_writes_only_requested_output_path(tmp_path: Path) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before = report_path.read_bytes()
    output = tmp_path / "pr153.report.json"
    assert pr153_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--output", output.as_posix()]) == 0
    assert output.exists()
    assert report_path.read_bytes() == before


def test_write_report_updates_only_pr153_report_path() -> None:
    master_before = (REPO_ROOT / c.MASTER_PLAN_PATH).read_bytes()
    bundle_before = (REPO_ROOT / c.ATOMICROWS_BUNDLE_PATH).read_bytes()
    assert pr153_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--write-report"]) == 0
    assert (REPO_ROOT / c.MASTER_PLAN_PATH).read_bytes() == master_before
    assert (REPO_ROOT / c.ATOMICROWS_BUNDLE_PATH).read_bytes() == bundle_before


def test_no_master_plan_edit() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert c.MASTER_PLAN_PATH.as_posix() not in changed


def test_no_qtt_integrity_authority() -> None:
    serialized = pr153_report.json_dump(_report()).lower()
    assert ("qtt-generated " + "integrity authority") not in serialized
    assert "checksum authority" not in serialized


def test_no_forbidden_added_text_markers() -> None:
    serialized = pr153_report.json_dump(_report())
    forbidden_true_flags = [
        '"source_fact_acceptance_created": ' + "true",
        '"connector_binding_created": ' + "true",
        '"runtime_cash_receipt_created": ' + "true",
        '"order_execution_created": ' + "true",
        '"quantum_advantage_evidence_created": ' + "true",
    ]
    for marker in forbidden_true_flags:
        assert marker not in serialized


def test_no_test_bypass_markers() -> None:
    text = Path(__file__).read_text()
    forbidden = [
        "allow_" + "repair=True",
        "raise System" + "Exit(0)",
        "x" + "fail",
        "pytest.mark." + "sk" + "ip",
        "unittest." + "sk" + "ip",
    ]
    for marker in forbidden:
        assert marker not in text
