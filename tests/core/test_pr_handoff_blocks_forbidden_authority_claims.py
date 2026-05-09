from __future__ import annotations

from pathlib import Path

import pytest

from tools import pr_handoff_check


def _packet() -> dict:
    return pr_handoff_check.build_packet(repo_root=Path("."))


def _assert_failure_contains(failures: list[str], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


@pytest.mark.parametrize("claim", sorted(pr_handoff_check.FORBIDDEN_AUTHORITY_CLAIMS))
def test_pr_handoff_blocks_forbidden_authority_claims(claim):
    packet = _packet()
    packet["forbidden_authority_claims"][claim] = True

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, claim)


@pytest.mark.parametrize(
    "claim",
    [
        "freeze_or_sha_authority",
        "source_fact_acceptance",
        "connector_semantics",
        "runtime_resolver_snapshot",
        "replay_paper_execution_or_result_packets",
        "limited_live_canary_or_live_arbitrage",
        "live_reachability",
        "runtime_cash_or_usable_cash_receipt",
        "atomicrows_bundle_hash_or_4183_rows",
        "blocker_reduction",
        "profit_evidence",
    ],
)
def test_pr_handoff_blocks_named_forbidden_authority_groups(claim):
    packet = _packet()
    packet["forbidden_authority_claims"][claim] = True

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, claim)


@pytest.mark.parametrize("claim", sorted(pr_handoff_check.SUMMARY_NO_AUTHORITY))
def test_pr_handoff_summary_false_claims_fail_closed(claim):
    packet = _packet()
    packet["summary_no_authority"][claim] = True

    failures = pr_handoff_check.validate_packet(packet, repo_root=Path("."))

    _assert_failure_contains(failures, claim)
