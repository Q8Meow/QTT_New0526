"""PR153S deterministic per-target closure classification."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    taxonomy as pr153r_tx,
)

from . import inputs
from . import taxonomy as tx


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def identity_tuple(pr151_target: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _text(pr151_target.get("target_platform_scope")),
        _text(pr151_target.get("target_field_path")),
        _text(pr151_target.get("pr150_target_id")),
        _text(pr151_target.get("retrieval_target_id")),
    )


def identity_key(pr151_target: Mapping[str, Any]) -> str:
    return "|".join(identity_tuple(pr151_target))


def record_sort_key(record: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _text(record.get("platform_scope")),
        _text(record.get("target_field_path")),
        _text(record.get("upstream_target_id")),
        _text(record.get("target_id")),
    )


def _closure_lane(
    target_id: str,
    candidate: Mapping[str, Any] | None,
    owner_queue: Mapping[str, Any] | None,
    pr153r_record: Mapping[str, Any] | None,
) -> tuple[str, str]:
    if pr153r_record and pr153r_record.get("acceptance_decision") == (
        pr153r_tx.ACCEPTED_TARGET_FIELD_SOURCE_PACKET
    ):
        return (
            tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY,
            "PR153R upstream record already reports accepted source packet status.",
        )
    if candidate is not None:
        return (
            tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE,
            "PR153 captured candidate packet exists and acceptance_status is not accepted.",
        )
    if pr153r_record is not None:
        return (
            tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE,
            "PR153R retry record exists and remains blocked pending acceptance review.",
        )
    if owner_queue is not None:
        upstream_lane = _text(owner_queue.get("recommended_primary_eligibility_lane"))
        lane = tx.PR153_ELIGIBILITY_TO_PR153S_CLOSURE.get(upstream_lane)
        if lane is not None:
            return (
                lane,
                f"PR153 owner blocker queue assigned eligibility lane {upstream_lane}.",
            )
        return (
            tx.CLOSURE_UNKNOWN_FAIL_CLOSED,
            f"PR153 owner blocker queue lane is not mapped for PR153S: {upstream_lane}",
        )
    return (
        tx.CLOSURE_UNKNOWN_FAIL_CLOSED,
        f"No PR153 candidate, PR153 owner queue, or PR153R retry record for {target_id}.",
    )


def _quantum_class(
    pr151_target: Mapping[str, Any],
    pr150_target: Mapping[str, Any],
) -> str:
    if pr150_target.get("quantum_execution_evidence_requirement"):
        return tx.QUANTUM_FORWARD_EXECUTION_EVIDENCE_REQUIRED
    joined = " ".join(
        _text(value)
        for value in (
            pr151_target.get("quantum_forward_dependency"),
            pr151_target.get("source_target_class"),
            pr151_target.get("target_field_path"),
            pr151_target.get("pr150_target_domain"),
            pr150_target.get("target_family_id"),
            pr150_target.get("target_domain"),
        )
    ).upper()
    if "QUANTUM" in joined or "QAOA" in joined or "QUBO" in joined or "ISING" in joined:
        return tx.QUANTUM_FORWARD_METADATA_ONLY
    if "OPTIMIZER" in joined or "ANNEAL" in joined or "VQE" in joined:
        return tx.QUANTUM_FORWARD_OPTIMIZER_METADATA_ONLY
    return tx.QUANTUM_FORWARD_NOT_APPLICABLE


def _upstream_refs(
    pr151_target: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any] | None,
    owner_queue: Mapping[str, Any] | None,
    pr153r_record: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    refs = [
        {
            "artifact_path": "docs/master_plan/generated/PR151_OfficialSourceRetrievalTargetPackForParameterDefaults.report.json",
            "record_id": pr151_target.get("retrieval_target_id"),
            "role": "canonical_target_record",
        },
        {
            "artifact_path": "docs/master_plan/generated/PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json",
            "record_id": pr151_target.get("pr150_target_id"),
            "role": "upstream_parameter_target_record",
        },
    ]
    if candidate is not None:
        refs.append(
            {
                "artifact_path": "docs/master_plan/generated/PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json",
                "record_id": candidate.get("candidate_packet_id"),
                "role": "captured_candidate_packet_only_not_accepted",
            }
        )
    if owner_queue is not None:
        refs.append(
            {
                "artifact_path": "docs/master_plan/generated/PR153_ControlledOfficialSourceCaptureCandidatePackets.report.json",
                "record_id": owner_queue.get("retrieval_target_id"),
                "role": "owner_blocker_closure_lane",
            }
        )
    if pr153r_record is not None:
        refs.append(
            {
                "artifact_path": "docs/master_plan/generated/PR153R_RedoExternalSourceValueCaptureTargets.report.json",
                "record_id": pr153r_record.get("retrieval_target_id"),
                "role": "retry_candidate_pending_acceptance",
            }
        )
    return refs


def _target_family(pr151_target: Mapping[str, Any], pr150_target: Mapping[str, Any]) -> str:
    return (
        _text(pr151_target.get("pr150_target_domain"))
        or _text(pr150_target.get("target_domain"))
        or _text(pr150_target.get("target_family_id"))
    )


def classify_targets(
    repo_root: str | Path,
) -> tuple[list[dict[str, Any]], inputs.UpstreamInputs]:
    upstream = inputs.load_inputs(repo_root)
    records: list[dict[str, Any]] = []
    for pr151_target in upstream.pr151_targets:
        target_id = _text(pr151_target.get("retrieval_target_id"))
        pr150_id = _text(pr151_target.get("pr150_target_id"))
        pr150_target = _mapping(upstream.pr150_targets_by_id.get(pr150_id))
        candidate = upstream.pr153_candidates_by_id.get(target_id)
        owner_queue = upstream.pr153_owner_queue_by_id.get(target_id)
        pr153r_record = upstream.pr153r_records_by_id.get(target_id)
        lane, lane_basis = _closure_lane(target_id, candidate, owner_queue, pr153r_record)
        policy = tx.lane_policy(lane)
        quantum_class = _quantum_class(pr151_target, pr150_target)
        runtime_required = bool(pr150_target.get("runtime_receipt_requirement"))
        replay_required = bool(pr150_target.get("replay_paper_calibration_requirement"))
        quantum_required = bool(pr150_target.get("quantum_execution_evidence_requirement"))
        accepted = lane == tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY
        pr153r_member = pr153r_record is not None
        pr153_candidate_member = candidate is not None
        public_external = lane in {
            tx.CLOSURE_PUBLIC_EXTERNAL_CANDIDATE_CAPTURED_PENDING_ACCEPTANCE,
            tx.CLOSURE_PUBLIC_EXTERNAL_PR153R_RETRY_CANDIDATE_PENDING_ACCEPTANCE,
            tx.CLOSURE_ACCEPTED_SOURCE_READY_EXISTING_PACKET_ONLY,
        }
        record = {
            "target_id": target_id,
            "upstream_target_id": pr150_id,
            "canonical_identity_key": identity_key(pr151_target),
            "platform_scope": pr151_target.get("target_platform_scope"),
            "market_scope_if_available": pr151_target.get("target_market_scope"),
            "target_field_path": pr151_target.get("target_field_path"),
            "parameter_family_or_target_family": _target_family(pr151_target, pr150_target),
            "source_authority_class": policy["authority"],
            "closure_lane": lane,
            "closure_lane_basis": lane_basis,
            "materialization_readiness_route": policy["route"],
            "materialization_route_basis": (
                "PR153S maps the closure lane to the centralized PR154 route policy."
            ),
            "required_next_action": policy["next_action"],
            "blocker_codes": list(policy["blockers"]),
            "upstream_artifact_refs": _upstream_refs(
                pr151_target,
                candidate=candidate,
                owner_queue=owner_queue,
                pr153r_record=pr153r_record,
            ),
            "public_external_denominator_member": public_external,
            "candidate_packet_present": bool(
                candidate is not None
                or (
                    pr153r_record is not None
                    and (
                        _list(pr153r_record.get("classified_seed_url_candidates"))
                        or _list(pr153r_record.get("retrieved_official_locators"))
                    )
                )
            ),
            "pr153_candidate_member": pr153_candidate_member,
            "pr153r_retry_member": pr153r_member,
            "accepted_source_packet_present": accepted,
            "internal_control_plane_member": (
                lane == tx.CLOSURE_INTERNAL_CONTROL_PLANE_NON_EXTERNAL_VALUE
            ),
            "split_or_reclassification_member": (
                lane == tx.CLOSURE_SPLIT_OR_RECLASSIFICATION_REQUIRED
            ),
            "private_doc_attestation_member": (
                lane == tx.CLOSURE_PRIVATE_DOC_ATTESTATION_REQUIRED
            ),
            "owner_route_member": lane == tx.CLOSURE_OWNER_PROVIDED_ROUTE_REQUIRED,
            "runtime_receipt_route_member": (
                lane == tx.CLOSURE_BLOCKED_UNTIL_RUNTIME_RECEIPT
            ),
            "replay_paper_route_member": (
                lane == tx.CLOSURE_BLOCKED_UNTIL_REPLAY_PAPER_REVIEW
            ),
            "quantum_evidence_route_member": (
                lane == tx.CLOSURE_BLOCKED_UNTIL_QUANTUM_EXECUTION_EVIDENCE
            ),
            "pr154_materialization_allowed": bool(policy["allowed"]),
            "pr154_materialization_block_reason": policy["pr154_block_reason"],
            "pr154_required_authority_before_value": policy["authority"],
            "pr154_allowed_value_source_class": (
                tx.PR154_ALLOWED_VALUE_SOURCE_CLASS_ACCEPTED_SOURCE_PACKET
                if accepted
                else tx.PR154_ALLOWED_VALUE_SOURCE_CLASS_BLOCKED
            ),
            "pr154_consumer_must_not_use_candidate_value_as_accepted_fact": True,
            "pr154_consumer_must_not_use_owner_route_as_fact": True,
            "pr154_consumer_must_not_use_private_doc_without_attestation": True,
            "pr154_consumer_must_not_use_split_target_before_reclassification": True,
            "pr154_consumer_must_not_use_runtime_value_without_receipt": True,
            "pr154_consumer_must_not_use_quantum_value_without_execution_evidence": True,
            "pr154_consumer_must_not_touch_atomicrows_bundle_hash": True,
            "pr154_consumer_must_not_create_qtt_sha_authority": True,
            "atomicrows_compatibility_class": policy["atomicrows_class"],
            "atomicrows_materialization_boundary": (
                tx.ATOMICROWS_BOUNDARY_LEDGER_ONLY_NO_ROW_VALUE
            ),
            "quantum_forward_compatibility_class": quantum_class,
            "quantum_execution_required_before_value": quantum_required,
            "runtime_receipt_required_before_value": runtime_required,
            "replay_paper_required_before_value": replay_required,
            "live_order_authority_created": False,
        }
        records.append(record)
    return sorted(records, key=record_sort_key), upstream


def count_by(records: list[Mapping[str, Any]], field: str, universe: tuple[str, ...]) -> dict[str, int]:
    counter = Counter(_text(record.get(field)) for record in records)
    return {key: counter.get(key, 0) for key in universe}
