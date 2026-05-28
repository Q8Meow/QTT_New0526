"""Human-readable PR158 owner review summary."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_summary(report: Mapping[str, Any]) -> str:
    counts = report["count_invariant_receipt"]
    lane = report["lane_summary_counts"]
    overlay = report["atomicrows_selection_readiness_aggregate_counts"]
    lines = [
        "# PR158 Owner Decision Summary",
        "",
        "PR158 is a non-live owner-response and AtomicRows selection-readiness bridge. It creates no runtime, live, connector, source-retrieval, source-acceptance, replay, paper, scoring, ranking, selection, optimizer, quantum-backend, order, fill, or profit authority.",
        "",
        "## Counts",
        f"- PR157 owner request packet: {counts['owner_request_packet_count']}",
        f"- AtomicRows owner-response lanes A-C: {counts['atomicrows_owner_response_count']}",
        f"- PR154 owner-dependent lanes D-F: {counts['pr154_owner_dependent_count']}",
        f"- AtomicRows selection-readiness overlay: {overlay['atomicrows_selection_readiness_total_count']}",
        "",
        "## Lane A - Agent Assignment",
        f"- Role/family/consumer responsibility filled: {lane['lane_a']['role_family_consumer_only_count']}",
        f"- Exact agent IDs invented: 0",
        f"- Exact IDs deferred to PR163: {lane['lane_a']['exact_agent_id_deferred_to_PR163_count']}",
        "",
        "## Lane B - Owner Policy Defaults",
        f"- Conservative internal policy classes filled: {lane['lane_b']['filled_from_conservative_owner_policy_class_count']}",
        "- These values require policy snapshots, replay, paper, dual review, and owner promotion review before live use.",
        "",
        "## Lane C - Parameter Range Owner Policy",
        f"- Conservative family policy classes filled: {lane['lane_c']['filled_from_conservative_family_policy_class_count']}",
        "- No numeric ranges were invented.",
        "",
        "## Lane D - PR154 Owner Routes",
        f"- Internal route metadata packets filled: {lane['lane_d']['filled_from_owner_route_policy_count']}",
        "- Route metadata is control-plane only and does not create connector or live authority.",
        "",
        "## Lane E - Split/Reclassification",
        f"- Routed to PR160: {lane['lane_e']['routed_to_PR160_count']}",
        "- PR158 found no deterministic split basis that can be safely completed without PR160.",
        "",
        "## Lane F - Private Docs",
        f"- Awaiting explicit owner attestation: {lane['lane_f']['still_blocked_count']}",
        f"- Review file: `{c.PRIVATE_DOC_REVIEW_PATH.as_posix()}`",
        "",
        "## Cross-Lane S - Selection Readiness",
        f"- Static overlay records: {overlay['atomicrows_selection_readiness_total_count']}",
        f"- Low-latency precomputed metadata eligible: {overlay['low_latency_precomputed_index_eligible_count']}",
        "- Scoring/ranking/selection execution remains blocked for later PR164+ gates.",
        "",
        "## Owner Next Actions",
        "- For exact agent IDs: wait for PR163 exact binding artifacts.",
        "- For split/reclassification records: complete PR160.",
        "- For private-doc records: provide the optional PR158 private-doc decision file with explicit access/use-rights attestation.",
        "- For source-required records: complete PR159 source retry/source completion.",
        "",
    ]
    return "\n".join(lines)


def build_private_doc_review(records: list[Mapping[str, Any]]) -> str:
    lines = [
        "# PR158 Private Doc Attestation Owner Review",
        "",
        "No private-doc record was completed by PR158 because no explicit owner attestation input file exists.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## {record['PR154_target_id']}",
                f"- request_id: `{record['request_id']}`",
                f"- locator currently available: `{record['requested_private_doc_locator']}`",
                f"- required attestation: {record['owner_attestation_text_template']}",
                f"- next action: {record['exact_next_action']}",
                "",
            ]
        )
    return "\n".join(lines)

