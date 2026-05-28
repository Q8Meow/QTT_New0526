"""Lane F: private-doc attestation records."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .prior_artifact_reconciliation import basis_refs, target_id_from_request


def build(
    records_by_target: dict[str, Mapping[str, Any]],
    requests: list[Mapping[str, Any]],
    *,
    owner_decision_exists: bool,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for request in requests:
        target_id = target_id_from_request(request)
        source = records_by_target.get(target_id, {})
        output.append(
            {
                "lane": c.PR158Lane.LANE_F_PR154_PRIVATE_DOC_ATTESTATION.value,
                "request_id": request["request_id"],
                "PR154_target_id": target_id,
                "target_field_id": request.get("target_field_id_or_missing_field_id"),
                "private_doc_reason": "Owner access/use-rights attestation is required before private/internal use.",
                "requested_private_doc_locator": request.get("private_document_identifier_if_applicable"),
                "requested_doc_digest_if_available": None,
                "private_doc_access_rights_attestation_required_flag": True,
                "secret_redaction_required_flag": True,
                "raw_secret_capture_forbidden_flag": True,
                "external_fact_override_forbidden_flag": True,
                "connector_semantic_unlock_forbidden_flag": True,
                "runtime_cash_receipt_creation_forbidden_flag": True,
                "owner_attestation_text_template": (
                    "I attest that I have access and use rights for the named private document, "
                    "that no raw secret is being provided, and that the record is internal-only."
                ),
                "accept_option": "Provide docs/master_plan/owner_inputs/PR158_PrivateDocAttestationOwnerDecision.json with target_id, locator, and attestation text.",
                "decline_option": "Leave blocked and route to source-evidence/public fallback only if a public-source route exists.",
                "exact_acceptance_criteria": "Explicit owner access/use-rights attestation, non-secret locator, target-field match, and no connector/runtime/live authority.",
                "validator_that_will_unblock": "tools/validate_pr158_owner_response_selection_readiness_bridge.py",
                "future_route_if_declined": c.FutureRoute.PR159_PUBLIC_SOURCE_RETRY.value,
                "scoring_selection_downstream_impact": c.SelectionReadinessStatus.SELECTION_READY_AFTER_PRIVATE_DOC_ATTESTATION.value,
                "completion_decision_class": (
                    c.CompletionDecisionClass.PENDING_PRIVATE_DOC_ATTESTATION.value
                    if not owner_decision_exists
                    else c.CompletionDecisionClass.BLOCKED_PRIVATE_DOC_ATTESTATION_MISSING.value
                ),
                "response_value_or_null": None,
                "basis_artifact_refs": basis_refs(
                    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
                    "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
                    source.get("completion_evidence_ref"),
                ),
                "exact_next_action": "Owner must provide explicit private-doc attestation file; PR158 did not complete this record.",
            }
        )
    return sorted(output, key=lambda item: item["request_id"])


def aggregate(records: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "private_doc_owner_attested_count": 0,
        "private_doc_declined_count": 0,
        "missing_locator_or_digest_count": len(records),
        "routed_to_source_evidence_count": 0,
        "still_blocked_count": len(records),
    }

