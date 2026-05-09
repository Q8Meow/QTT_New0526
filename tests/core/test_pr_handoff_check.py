from __future__ import annotations

from pathlib import Path

from tools import pr_handoff_check


def _packet() -> dict:
    return pr_handoff_check.build_packet(repo_root=Path("."))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_pr_handoff_packet_valid_static_packet_passes():
    packet = _packet()

    assert pr_handoff_check.validate_packet(packet, repo_root=Path(".")) == []


def test_pr_handoff_packet_requires_not_created_claims():
    packet = _packet()
    packet["not_created_claims"]["source_fact_acceptance"] = "CREATED"

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, "not_created_claims.source_fact_acceptance")


def test_pr_handoff_packet_requires_remaining_blockers():
    packet = _packet()
    packet["remaining_blockers"] = packet["remaining_blockers"][:-1]

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, "remaining_blockers")


def test_pr_handoff_packet_represents_generated_derivative_and_atomicrows_absent_bootstrap():
    packet = _packet()
    status = packet["generated_derivative_and_atomicrows_status"]

    assert status["generated_derivative_status"] == (
        "STATIC_BOOTSTRAP_ABSENT_NO_COMPLETION_AUTHORITY"
    )
    assert status["atomicrows_bundle_present"] is False
    assert status["atomicrows_bundle_sha_present"] is False
    assert status["atomicrows_row_count_status"] == "NOT_CREATED_UNBOUND"
    assert status["bootstrap_status_explicit"] is True


def test_pr_handoff_summary_cannot_claim_authority_not_created_by_receipts():
    packet = _packet()
    packet["summary_no_authority"]["creates_live_reachability"] = True

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, "creates_live_reachability")


def test_pr_handoff_schema_is_closed_at_root():
    import json

    schema = json.loads(
        Path("src/qtt/core/schemas/pr_handoff_packet.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "not_created_claims" in schema["required"]

