"""Candidate-route construction for PR160 records."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


REPLAY_PAPER_REQUIRED = "REPLAY_PAPER_CALIBRATION_REQUIRED"
QUANTUM_METADATA_ONLY = "QUANTUM_METADATA_ONLY"
QUANTUM_EXECUTION_REQUIRED = "QUANTUM_EXECUTION_EVIDENCE_REQUIRED"
OFFICIAL_SOURCE_REQUIRED = "OFFICIAL_SOURCE_EVIDENCE_REQUIRED"
SCORING_FAMILY = "SCORING_FORMULA_INPUT"
OPTIMIZER_FAMILY = "OPTIMIZER_PARAMETER"
QUANTUM_FAMILY = "QUANTUM_PARAMETER"


def _basis_refs(record: Mapping[str, Any]) -> list[str]:
    refs = [
        "docs/master_plan/generated/PR136RouteTriage.report.json",
        "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
        "docs/master_plan/generated/PR150_SourceBackedClassicalQuantumParameterDefaultTargetMatrix.report.json",
        "docs/master_plan/generated/PR157_PR154BlockedRecordCompletionBridge.registry.json",
        "docs/master_plan/generated/PR158_PR154SplitReclassificationCandidateMap.registry.json",
    ]
    if record.get("PR159_accepted_packet_ref_or_null"):
        refs.append("docs/master_plan/generated/PR159_AcceptedSourceEvidencePacketRegistry.report.json")
    if record.get("PR159_unresolved_fill_path_ref_or_null"):
        refs.append("docs/master_plan/generated/PR159_UnresolvedOfficialSourceFillPath.report.json")
    return sorted(set(refs))


def _route_for_record(record: Mapping[str, Any]) -> tuple[str, str, str, str]:
    evidence = str(record.get("pr150_evidence_requirement_class_or_null") or "")
    family = str(record.get("pr150_target_family_id_or_null") or "")
    if record.get("PR159_accepted_packet_ref_or_null"):
        return (
            c.ReclassificationFinalRouteClass.ATOMICROWS_SOURCE_VALUE_MATERIALIZATION_ROUTE_PR161.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_PR159_ACCEPTED_SOURCE_PACKET.value,
            c.AuthorityClass.ACCEPTED_SOURCE_EVIDENCE_ALREADY_PRESENT.value,
            c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
        )
    if record.get("PR159_unresolved_fill_path_ref_or_null") or evidence == OFFICIAL_SOURCE_REQUIRED:
        return (
            c.ReclassificationFinalRouteClass.OFFICIAL_SOURCE_REQUIRED_ROUTE_PR159R.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_PR159_UNRESOLVED_FILL_PATH.value
            if record.get("PR159_unresolved_fill_path_ref_or_null")
            else c.ReclassificationBasisClass.DETERMINISTIC_FROM_PR154_MATERIALIZATION.value,
            c.AuthorityClass.ACCEPTED_SOURCE_EVIDENCE_REQUIRED.value,
            c.FutureRoute.PR159R_EXACT_SOURCE_LOCATOR_VALUE_UNIT_CAPTURE.value,
        )
    if evidence == QUANTUM_METADATA_ONLY or family == QUANTUM_FAMILY and evidence != QUANTUM_EXECUTION_REQUIRED:
        return (
            c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_SCORING_QUANTUM_ARTIFACTS.value,
            c.AuthorityClass.METADATA_ONLY_NOT_EXECUTION_AUTHORITY.value,
            c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
        )
    if evidence == QUANTUM_EXECUTION_REQUIRED:
        return (
            c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_SCORING_QUANTUM_ARTIFACTS.value,
            c.AuthorityClass.RUNTIME_RECEIPT_FUTURE_ONLY.value,
            c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
        )
    if family == SCORING_FAMILY:
        return (
            c.ReclassificationFinalRouteClass.SCORING_RANKING_METADATA_ROUTE.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_SCORING_QUANTUM_ARTIFACTS.value,
            c.AuthorityClass.METADATA_ONLY_NOT_EXECUTION_AUTHORITY.value,
            c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value,
        )
    if family == OPTIMIZER_FAMILY and evidence == REPLAY_PAPER_REQUIRED:
        return (
            c.ReclassificationFinalRouteClass.REPLAY_PAPER_EVALUATION_FUTURE_ROUTE.value,
            c.ReclassificationBasisClass.DETERMINISTIC_FROM_SCORING_QUANTUM_ARTIFACTS.value,
            c.AuthorityClass.METADATA_ONLY_NOT_EXECUTION_AUTHORITY.value,
            c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value,
        )
    return (
        c.ReclassificationFinalRouteClass.INVALID_OR_UNSUPPORTED_WITH_FILL_PATH.value,
        c.ReclassificationBasisClass.NO_DETERMINISTIC_BASIS_BLOCKED.value,
        c.AuthorityClass.OWNER_CHOICE_REQUIRED_NOT_EXTERNAL_FACT.value,
        c.FutureRoute.OWNER_REVIEW_AFTER_FUTURE_GATES.value,
    )


def candidate_routes_for_record(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    route, basis, authority, future_route = _route_for_record(record)
    target_id = str(record.get("PR154_target_id"))
    return [
        {
            "PR154_target_id": target_id,
            "candidate_route_class": route,
            "basis_artifact_refs": _basis_refs(record),
            "basis_class": basis,
            "route_confidence_class": (
                c.RouteConfidenceClass.INVALID_UNSUPPORTED.value
                if route == c.ReclassificationFinalRouteClass.INVALID_OR_UNSUPPORTED_WITH_FILL_PATH.value
                else c.RouteConfidenceClass.DETERMINISTIC.value
            ),
            "authority_class": authority,
            "downstream_dependency_ids": [future_route],
            "source_fact_risk_flag": authority == c.AuthorityClass.ACCEPTED_SOURCE_EVIDENCE_REQUIRED.value,
            "owner_policy_flag": False,
            "private_doc_flag": False,
            "runtime_receipt_flag": authority == c.AuthorityClass.RUNTIME_RECEIPT_FUTURE_ONLY.value,
            "connector_semantic_flag": route
            == c.ReclassificationFinalRouteClass.CONNECTOR_SEMANTIC_FUTURE_ROUTE.value,
            "quantum_metadata_flag": route
            in {
                c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value,
                c.ReclassificationFinalRouteClass.RUNTIME_RECEIPT_FUTURE_ROUTE.value,
            },
            "agent_binding_flag": False,
            "formula_derivative_flag": route
            in {
                c.ReclassificationFinalRouteClass.FORMULA_ONLY_DERIVED_ROUTE.value,
                c.ReclassificationFinalRouteClass.GENERATED_DERIVATIVE_FROM_ACCEPTED_INPUTS_ROUTE.value,
            },
            "scoring_selection_impact_flag": route
            in {
                c.ReclassificationFinalRouteClass.SCORING_RANKING_METADATA_ROUTE.value,
                c.ReclassificationFinalRouteClass.REPLAY_PAPER_EVALUATION_FUTURE_ROUTE.value,
            },
            "low_latency_impact_flag": route
            != c.ReclassificationFinalRouteClass.QUANTUM_CLASSICAL_METADATA_ONLY_ROUTE.value,
            "replay_paper_live_implication": (
                "Future replay/paper and owner review are required before any live use."
            ),
            "future_route": future_route,
            "selected_by_arbitration_flag": True,
        }
    ]


def build_candidate_route_matrix(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "PR154_target_id": str(record.get("PR154_target_id")),
            "request_id_or_record_id": str(record.get("request_id_or_record_id")),
            "candidate_routes": candidate_routes_for_record(record),
            "candidate_route_count": 1,
            "all_plausible_routes_recorded_flag": True,
            "generic_split_reclassification_state_remaining_flag": False,
        }
        for record in records
    ]
