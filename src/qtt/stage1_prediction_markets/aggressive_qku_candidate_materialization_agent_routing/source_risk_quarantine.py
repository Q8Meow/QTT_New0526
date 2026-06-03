"""Quarantine ledger helpers for unsafe or unmappable sources."""

from __future__ import annotations


def source_risk_quarantine_records() -> list[dict[str, object]]:
    return [
        {
            "record_id": "PR162D-SOURCE-RISK-QUARANTINE-SUMMARY",
            "unsafe_private_secret_count": 0,
            "illegal_or_rights_blocked_count": 0,
            "private_account_or_order_endpoint_only_count": 0,
            "unmappable_to_qku_count": 0,
            "duplicate_low_value_count": 0,
            "corrupt_unreadable_count": 0,
            "malware_or_suspicious_code_count": 0,
            "quarantine_count": 0,
        }
    ]
