from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping


SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "bearer",
    "oauth",
    "cookie",
    "private_key",
    "privatekey",
    "wallet_secret",
    "walletsecret",
    "session_identifier",
    "sessionid",
    "auth_token",
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9_]{8,}", re.IGNORECASE),
    re.compile(r"\bpk_(?:live|test)_[A-Za-z0-9_]{8,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:api|oauth|auth|session|wallet)[_-]?token\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)

RAW_PRIVATE_KEY_PARTS = (
    "raw_payload",
    "raw_private",
    "raw_balance",
    "balance_value",
    "wallet_value",
    "account_value",
    "unredacted",
)

ALLOWED_REDACTION_MARKERS = {
    "REDACTED_FIXTURE_VALUE",
    "FIXTURE_PLACEHOLDER_ONLY",
    "DIGEST_ONLY",
    "FIELD_NAME_ONLY",
}

ALLOWED_FIELD_LABELS = {
    "verified_available_cash",
    "open_order_lock",
    "required_reserve",
    "margin_lock",
    "unsettled_funds",
    "locked_or_withdrawal_restricted_funds",
    "pending_use_funds",
    "field_names_only",
    "non_secret_digest_policy",
}


def canonicalize_redacted_payload(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def canonical_redacted_payload_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonicalize_redacted_payload(payload)).hexdigest()


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


def secret_like_findings(payload: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    for path, value in _walk(payload):
        if isinstance(value, Mapping):
            for key in value:
                key_lower = str(key).lower()
                if any(part in key_lower for part in SECRET_KEY_PARTS):
                    findings.append(f"secret-like key at {path}.{key}")
                if any(part in key_lower for part in RAW_PRIVATE_KEY_PARTS):
                    findings.append(f"unredacted private-state key at {path}.{key}")
        if isinstance(value, str):
            if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
                findings.append(f"secret-like value at {path}")
            if value.startswith(("RAW_", "UNREDACTED_")):
                findings.append(f"unredacted private-state value at {path}")
    return findings


def validate_redacted_payload_minimized(payload: Mapping[str, Any]) -> list[str]:
    failures = secret_like_findings(payload)
    for path, value in _walk(payload):
        if isinstance(value, str):
            if value in ALLOWED_REDACTION_MARKERS:
                continue
            if value in ALLOWED_FIELD_LABELS:
                continue
            if value.startswith(("PR130_", "PR129_", "TEST_FIXTURE_NOT_EXTERNAL_FACT")):
                continue
            if value in {
                "KALSHI",
                "POLYMARKET",
                "FORECASTEX_IBKR",
                "PREDICTION_MARKETS_GENERAL",
                "ACCOUNT_WALLET_BALANCE",
                "STRING",
                "DECIMAL_STRING_REDACTED",
                "OBJECT",
                "LIST",
                "BOOLEAN",
                "USD",
            }:
                continue
            if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
                continue
            if value.startswith("stage1."):
                continue
            failures.append(f"non-minimized fixture value at {path}")
    return failures
