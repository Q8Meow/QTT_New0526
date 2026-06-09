"""Retest ingestion and pending-retest vocabulary."""

from __future__ import annotations

RETEST_MODES = ("REPLAY", "PAPER", "BOTH")
INGESTION_STATUSES = (
    "NO_VALIDATED_POST_MEMORY_RETEST_RESULT_DISCOVERED",
    "INGESTED_VALIDATED_REPLAY_RESULT",
    "INGESTED_VALIDATED_PAPER_RESULT",
    "INGESTED_VALIDATED_REPLAY_AND_PAPER_RESULT",
)
PENDING_EVIDENCE_REQUIREMENTS = (
    "matching_condition_fingerprint",
    "matching_combination_fingerprint",
    "asof_leakage_audit",
    "replay_or_paper_result_packet",
    "false_discovery_adjusted_confidence",
    "risk_adjusted_net_edge",
)
