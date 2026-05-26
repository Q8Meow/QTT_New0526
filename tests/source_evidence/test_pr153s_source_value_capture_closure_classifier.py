from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.controlled_official_source_capture_candidate_packets import (
    constants as pr153_c,
)
from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    accepted_packet as pr153r_accepted_packet,
)
from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    constants as pr153r_c,
)
from src.qtt.stage1_prediction_markets.pr153s_source_value_capture_closure_classifier import (
    classifier,
    report as report_builder,
    taxonomy as tx,
    validator,
)
from tools import validate_pr153s_source_value_capture_closure_classifier as pr153s_cli


REPO_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _report() -> dict:
    return report_builder.build_report(REPO_ROOT)


def _records() -> list[dict]:
    return _report()["per_target_closure_records"]


def _records_by_lane(lane: str) -> list[dict]:
    return [record for record in _records() if record["closure_lane"] == lane]


def _serialized_report() -> str:
    return report_builder.json_dump(_report())


def test_pr153s_report_generation_is_deterministic_across_repeated_builds():
    first = report_builder.json_dump(report_builder.build_report(REPO_ROOT))
    second = report_builder.json_dump(report_builder.build_report(REPO_ROOT))

    assert first == second
    payload = json.loads(first)
    assert payload["deterministic_generation_receipt"]["wall_clock_timestamps_used"] is False
    assert payload["deterministic_generation_receipt"]["runtime_git_branch_or_head_used"] is False


def test_all_pr151_targets_classify_into_exactly_one_lane_without_fabrication():
    pr151 = json.loads((REPO_ROOT / pr153_c.PR151_REPORT_PATH).read_text())
    pr151_ids = {
        row["retrieval_target_id"]
        for row in pr151["official_source_retrieval_target_queue"]
    }
    records = _records()

    assert len(pr151_ids) == pr153_c.PR153A_TOTAL_PR151_TARGETS
    assert len(records) == pr153_c.PR153A_TOTAL_PR151_TARGETS
    assert {record["target_id"] for record in records} == pr151_ids
    assert all(record["closure_lane"] in tx.CLOSURE_LANES for record in records)
    assert sum(_report()["closure_lane_summary"].values()) == len(records)


def test_no_duplicate_identity_or_index_only_identity():
    receipt = _report()["target_identity_resolution_receipt"]

    assert receipt["duplicate_identity_keys"] == []
    assert receipt["duplicate_target_ids"] == []
    assert receipt["index_only_identity_used"] is False
    assert receipt["identity_fields_available_for_all_records"] is True


def test_current_lane_counts_match_pr153_corrected_denominator():
    summary = _report()["closure_lane_summary"]

    assert summary[tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE] == (
        pr153_c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT
    )
    assert summary[tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE] == (
        pr153_c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
    )
    assert summary[tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE] == (
        pr153_c.PR153A_INTERNAL_CONTROL_PLANE_TARGET_COUNT
    )
    assert summary[tx.CLOSURE_SPLIT_OR_RECLASSIFICATION_REQUIRED] == (
        pr153_c.PR153A_TARGET_SPLIT_OR_RECLASSIFICATION_REQUIRED_COUNT
    )
    assert summary[tx.CLOSURE_PRIVATE_DOC_ATTESTATION_REQUIRED] == (
        pr153_c.PR153A_PRIVATE_DOC_OR_ATTESTATION_REQUIRED_COUNT
    )
    assert summary[tx.CLOSURE_OWNER_PROVIDED_ROUTE_REQUIRED] == (
        pr153_c.PR153A_OWNER_PROVIDED_VALUE_CANDIDATE_ROUTE_COUNT
    )
    assert summary[tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY] == 0
    assert summary[tx.CLOSURE_UNKNOWN_FAIL_CLOSED] == 0


def test_public_external_denominator_is_126_from_candidate_plus_pr153r_retry():
    receipt = _report()["public_external_source_denominator_receipt"]

    assert receipt["captured_public_external_candidate_count"] == (
        pr153_c.PR153A_CAPTURED_CANDIDATE_PACKET_COUNT
    )
    assert receipt["pr153r_retry_public_external_candidate_count"] == (
        pr153_c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
    )
    assert receipt["true_external_public_source_value_denominator"] == (
        pr153_c.PR153A_TRUE_EXTERNAL_PUBLIC_SOURCE_VALUE_CAPTURE_TARGET_COUNT
    )


def test_candidate_packets_are_not_accepted_source_packets_and_pr154_blocks_them():
    for record in _records_by_lane(
        tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE
    ):
        assert record["candidate_packet_present"] is True
        assert record["accepted_source_packet_present"] is False
        assert record["pr154_materialization_allowed"] is False
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_BLOCKED_PENDING_ACCEPTED_SOURCE_PACKET
        )
        assert record["pr154_consumer_must_not_use_candidate_value_as_accepted_fact"] is True


def test_pr153r_retry_candidates_remain_candidate_only_pending_acceptance():
    for record in _records_by_lane(
        tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE
    ):
        assert record["pr153r_retry_member"] is True
        assert record["accepted_source_packet_present"] is False
        assert record["pr154_materialization_allowed"] is False
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_BLOCKED_PENDING_PR153R_ACCEPTANCE_REVIEW
        )


def test_internal_control_plane_values_are_not_missing_public_external_sources():
    for record in _records_by_lane(tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE):
        assert record["internal_control_plane_member"] is True
        assert record["public_external_denominator_member"] is False
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_INTERNAL_OWNER_POLICY_REQUIRED
        )


def test_private_doc_targets_are_not_public_source_failures():
    for record in _records_by_lane(tx.CLOSURE_PRIVATE_DOC_ATTESTATION_REQUIRED):
        assert record["private_doc_attestation_member"] is True
        assert record["public_external_denominator_member"] is False
        assert record["pr154_consumer_must_not_use_private_doc_without_attestation"] is True
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_BLOCKED_PENDING_PRIVATE_DOC_ATTESTATION
        )


def test_owner_route_targets_are_not_accepted_facts():
    for record in _records_by_lane(tx.CLOSURE_OWNER_PROVIDED_ROUTE_REQUIRED):
        assert record["owner_route_member"] is True
        assert record["accepted_source_packet_present"] is False
        assert record["pr154_consumer_must_not_use_owner_route_as_fact"] is True
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_BLOCKED_PENDING_OWNER_ROUTE_PACKET
        )


def test_split_reclassification_targets_cannot_materialize_before_reclassification():
    for record in _records_by_lane(tx.CLOSURE_SPLIT_OR_RECLASSIFICATION_REQUIRED):
        assert record["split_or_reclassification_member"] is True
        assert record["pr154_materialization_allowed"] is False
        assert record["pr154_consumer_must_not_use_split_target_before_reclassification"] is True
        assert record["materialization_readiness_route"] == (
            tx.ROUTE_BLOCKED_PENDING_SPLIT_OR_RECLASSIFICATION
        )


def test_runtime_replay_quantum_closure_lanes_are_not_name_guessed():
    records_with_trigger_words = [
        record
        for record in _records()
        if any(
            token in record["target_field_path"]
            for token in ("runtime", "replay", "paper", "quantum")
        )
    ]

    assert records_with_trigger_words
    assert _report()["closure_lane_summary"][tx.CLOSURE_BLOCKED_UNTIL_RUNTIME_RECEIPT] == 0
    assert _report()["closure_lane_summary"][tx.CLOSURE_BLOCKED_UNTIL_REPLAY_PAPER_REVIEW] == 0
    assert (
        _report()["closure_lane_summary"][
            tx.CLOSURE_BLOCKED_UNTIL_QUANTUM_EXECUTION_EVIDENCE
        ]
        == 0
    )


def test_source_evidence_digest_metadata_remains_target_field_scoped_and_schema_backed():
    pr153r = json.loads((REPO_ROOT / pr153r_c.REPORT_PATH).read_text())
    assert pr153r["source_packet_digest_metadata_count"] == (
        pr153_c.PR153A_REMAINING_EXTERNAL_PUBLIC_CAPTURE_RETRY_TARGET_COUNT
    )
    for record in pr153r["per_target_records"]:
        assert pr153r_accepted_packet.digest_metadata_policy_failures(record) == []

    receipt = _report()["no_authority_creation_receipt"]
    assert receipt["source_evidence_digest_metadata_allowed_when_target_field_scoped"] is True
    assert receipt["source_evidence_digest_metadata_copied_into_pr153s_records"] is False


def test_no_qtt_global_atomicrows_runtime_profit_or_quantum_authority_created():
    receipt = _report()["no_authority_creation_receipt"]

    for key, expected in tx.zero_authority_counters().items():
        assert receipt[key] == expected
    assert receipt["source_retrieval_created"] is False
    assert receipt["source_acceptance_created"] is False
    assert receipt["connector_semantic_binding_created"] is False
    assert receipt["runtime_live_order_profit_authority_created"] is False
    assert receipt["quantum_backend_simulator_optimizer_execution_created"] is False


def test_no_atomicrows_bundle_or_hash_path_is_referenced_in_pr153s_report():
    serialized = _serialized_report()

    assert "AtomicRows.bundle." + "jsonl" not in serialized
    assert "AtomicRows.bundle." + "sha" + "256" not in serialized
    atomicrows = _report()["atomicrows_compatibility_receipt"]
    assert atomicrows["bundle_created_by_pr153s"] is False
    assert atomicrows["bundle_hash_or_sha_authority_created_by_pr153s"] is False
    assert atomicrows["row_values_created_by_pr153s"] == 0


def test_pr136_orchestration_artifacts_consumed_by_path_status_not_hashes():
    receipt = _report()["orchestration_alignment_receipt"]

    assert receipt["pr_identity_roster_consumed"] is True
    assert receipt["roadmap_execution_state_controller_consumed"] is True
    assert receipt["pr136_route_triage_consumed"] is True
    assert receipt["pr136_section_crosswalk_requested_alias_exists"] is False
    assert receipt["pr136_section_crosswalk_canonical_successor_consumed"] is True
    assert receipt["artifact_identification_uses_global_hashes"] is False
    assert receipt["artifact_identification_uses_paths_status_markers_only"] is True


def test_closure_routes_and_blockers_are_centralized_in_taxonomy():
    report = _report()

    assert report["taxonomy_module_path"] == tx.TAXONOMY_MODULE_PATH
    for record in _records():
        policy = tx.lane_policy(record["closure_lane"])
        assert record["materialization_readiness_route"] == policy["route"]
        assert record["source_authority_class"] == policy["authority"]
        assert set(record["blocker_codes"]).issubset(set(tx.BLOCKER_CODES))


def test_pr154_consumer_contract_fields_exist_and_block_unauthorized_materialization():
    contract = _report()["pr154_materialization_consumer_contract_receipt"]

    assert contract["contract_id"] == tx.PR154_CONSUMER_POLICY_ID
    assert contract["pr154_materialization_allowed_count"] == 0
    assert contract["candidate_values_materialized_as_accepted_facts"] is False
    for record in _records():
        for field in tx.PR154_CONSUMER_GUARD_FIELDS:
            assert field in record
            assert record[field] is True


def test_quantum_forward_metadata_is_metadata_only_no_execution_evidence():
    receipt = _report()["quantum_forward_compatibility_receipt"]

    assert receipt["metadata_only_for_future_pr159_pr160_readiness"] is True
    assert receipt["quantum_backend_execution_created"] is False
    assert receipt["quantum_simulator_execution_created"] is False
    assert receipt["optimizer_arbitration_created"] is False
    assert receipt["quantum_advantage_claim_created"] is False
    assert any(
        record["quantum_forward_compatibility_class"]
        in {
            tx.QUANTUM_FORWARD_METADATA_ONLY,
            tx.QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY,
            tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED,
        }
        for record in _records()
    )


def test_atomicrows_compatibility_receipt_is_ledger_only_no_materialization():
    receipt = _report()["atomicrows_compatibility_receipt"]

    assert receipt["future_pr154_readiness_ledger_only"] is True
    assert receipt["row_values_created_by_pr153s"] == 0
    assert receipt["bundle_created_by_pr153s"] is False
    assert receipt["row_family_mutated_by_pr153s"] is False


def test_validator_accepts_tracked_report_and_cli_emits_marker(capsys):
    failures = validator.validate_repository_artifacts(REPO_ROOT)
    assert failures == []

    assert pr153s_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert capsys.readouterr().out.strip() == tx.VALIDATOR_MARKER


def test_classifier_exposes_stable_sort_key_and_no_identity_duplicates():
    records, _upstream = classifier.classify_targets(REPO_ROOT)
    keys = [classifier.record_sort_key(record) for record in records]

    assert keys == sorted(keys)
    assert len({record["canonical_identity_key"] for record in records}) == len(records)
