"""Deterministic official-source retrieval provenance for PR153R redo."""

from __future__ import annotations

import hashlib
import json
from urllib.parse import urlparse
from typing import Any, Mapping

from . import seed_map
from . import taxonomy as tx

STATIC_RETRIEVED_AT = "2026-05-26T00:00:00-04:00"
SOURCE_LAST_SEEN_AT = "2026-05-26"
DEFAULT_REVALIDATION_POLICY = (
    "LIVE_CRITICAL_FIELDS_P1D__LOW_RISK_FIELDS_P7D__EVENT_TRIGGERED_IMMEDIATE"
)

OFFICIAL_DOMAIN_CLASS_HINTS = {
    "docs.kalshi.com": "OFFICIAL_API_DOCS",
    "docs.polymarket.com": "OFFICIAL_API_DOCS",
    "www.interactivebrokers.com": "OFFICIAL_API_DOCS",
    "interactivebrokers.github.io": "OFFICIAL_API_DOCS",
    "ibkrcampus.com": "OFFICIAL_API_DOCS",
    "forecastex.com": "OFFICIAL_VENUE_DOCS",
    "data.forecastex.com": "OFFICIAL_RULEBOOKS",
}

ONLINE_RETRIEVED_OFFICIAL_URLS = frozenset(
    {
        "https://data.forecastex.com/regulatory/ForecastEx_LLC_Rulebook.pdf",
        "https://docs.kalshi.com/api-reference/account/get-account-api-limits",
        "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "https://docs.kalshi.com/api-reference/orders/create-order",
        "https://docs.kalshi.com/api-reference/orders/create-order-v2",
        "https://docs.kalshi.com/changelog",
        "https://docs.kalshi.com/fix/market-settlement",
        "https://docs.kalshi.com/getting_started/fixed_point_migration",
        "https://docs.kalshi.com/getting_started/market_settlement",
        "https://docs.kalshi.com/getting_started/quick_start_websockets",
        "https://docs.kalshi.com/getting_started/rate_limits",
        "https://docs.kalshi.com/python-sdk/models/Settlement",
        "https://docs.polymarket.com/api-reference/markets/get-clob-market-info",
        "https://docs.polymarket.com/api-reference/rate-limits",
        "https://docs.polymarket.com/concepts/order-lifecycle",
        "https://docs.polymarket.com/concepts/prices-orderbook",
        "https://docs.polymarket.com/market-data/websocket/overview",
        "https://docs.polymarket.com/resources/error-codes",
        "https://docs.polymarket.com/trading/clients/l1",
        "https://docs.polymarket.com/trading/clients/l2",
        "https://docs.polymarket.com/trading/clients/public",
        "https://docs.polymarket.com/trading/ctf/redeem",
        "https://docs.polymarket.com/trading/orderbook",
        "https://docs.polymarket.com/trading/orders/cancel",
        "https://docs.polymarket.com/trading/overview",
        "https://docs.polymarket.com/trading/quickstart",
        "https://forecastex.com/faq",
        "https://interactivebrokers.github.io/tws-api/minimum_increment.html",
        "https://interactivebrokers.github.io/tws-api/order_submission.html",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/order-types/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/trader-workstation-api/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/tws-api-error-codes/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-trading/",
        "https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/",
        "https://www.interactivebrokers.com/predictionmarkets/en/home.php",
    }
)


def _digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def requested_class_from_target(target: Mapping[str, Any]) -> str:
    value = str(target.get("official_source_class") or "")
    return value if value in tx.OFFICIAL_SOURCE_CLASSES else ""


def classify_source_url(url: str, requested_class: str = "") -> dict[str, Any]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    class_hint = OFFICIAL_DOMAIN_CLASS_HINTS.get(domain)
    source_class = requested_class or class_hint or "UNKNOWN_SOURCE_CLASS"
    official_candidate = class_hint is not None and source_class in tx.OFFICIAL_SOURCE_CLASSES
    if domain == "data.forecastex.com":
        source_class = "OFFICIAL_RULEBOOKS"
    elif "sdk" in parsed.path.lower() and domain == "docs.kalshi.com":
        source_class = "OFFICIAL_SDK_DOCS"
    elif "fee" in parsed.path.lower() or "settlement" in parsed.path.lower():
        if domain in {"docs.kalshi.com", "docs.polymarket.com", "forecastex.com"}:
            source_class = "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS"
    return {
        "source_url": url,
        "source_domain": domain,
        "official_source_candidate": official_candidate,
        "official_source_class": source_class,
        "source_candidate_authority_status": tx.CANDIDATE_SEED_ONLY_NOT_ACCEPTED_FACT,
        "online_retrieval_status": (
            tx.OFFICIAL_SOURCE_RETRIEVED_PENDING_ACCEPTANCE
            if url in ONLINE_RETRIEVED_OFFICIAL_URLS and official_candidate
            else "OFFICIAL_SOURCE_CANDIDATE_NOT_RETRIEVED_BY_REDO_TOOLING"
        ),
        "retrieved_at": STATIC_RETRIEVED_AT
        if url in ONLINE_RETRIEVED_OFFICIAL_URLS and official_candidate
        else None,
    }


def retrieval_records_for_target(
    target: Mapping[str, Any],
    seed_record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    requested_class = requested_class_from_target(target)
    records: list[dict[str, Any]] = []
    for url in seed_map.split_seed_urls(seed_record.get("source_seed_url")):
        record = classify_source_url(url, requested_class=requested_class)
        digest_payload = {
            "retrieval_target_id": target.get("retrieval_target_id"),
            "target_field_path": target.get("target_field_path"),
            "platform_scope": target.get("platform_scope"),
            "source_url": url,
            "online_retrieval_status": record["online_retrieval_status"],
            "scope": "TARGET_FIELD_SOURCE_PROVENANCE_ONLY",
        }
        record["retrieval_artifact_digest"] = _digest(digest_payload)
        records.append(record)
    return records


def target_digest_metadata(
    target: Mapping[str, Any],
    retrieval_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    digest_payload = {
        "retrieval_target_id": target.get("retrieval_target_id"),
        "target_field_path": target.get("target_field_path"),
        "platform_scope": target.get("platform_scope"),
        "source_urls": [record.get("source_url") for record in retrieval_records],
        "acceptance_status": tx.ACCEPTANCE_BLOCKED,
        "digest_scope": "TARGET_FIELD_SOURCE_PROVENANCE_ONLY",
    }
    return {
        "scope_type": "TARGET_FIELD_SOURCE_PROVENANCE",
        "digest_authority_class": "SOURCE_PROVENANCE_ONLY_NOT_QTT_NOT_GLOBAL_NOT_ATOMICROWS",
        "source_packet_integrity_digest": _digest(digest_payload),
        "source_locator": [record.get("source_url") for record in retrieval_records],
        "quote_span_locator": None,
        "machine_field_locator": None,
        "retrieved_at": STATIC_RETRIEVED_AT,
        "revalidation_policy": DEFAULT_REVALIDATION_POLICY,
        "source_last_seen_at": SOURCE_LAST_SEEN_AT,
        "source_materiality_class": "CONNECTOR_BLOCKING_UNTIL_ACCEPTED_PACKET",
        "source_conflict_check_status": "PENDING_ACCEPTANCE_CONFLICT_CHECK_NOT_ACCEPTED",
        "forbidden_digest_authority_classes_created": [],
    }


def block_codes_for_target(
    target: Mapping[str, Any],
    retrieval_records: list[Mapping[str, Any]],
    digest_metadata: Mapping[str, Any],
) -> list[str]:
    block_codes = {tx.BLOCK_OWNER_REVIEW_REQUIRED}
    if not retrieval_records:
        block_codes.add(tx.BLOCK_MISSING_OFFICIAL_SOURCE_LOCATOR)
    if not any(record.get("official_source_candidate") for record in retrieval_records):
        block_codes.add(tx.BLOCK_SOURCE_NOT_OFFICIAL)
    if not digest_metadata.get("source_packet_integrity_digest"):
        block_codes.add(tx.BLOCK_MISSING_SOURCE_DIGEST)
    if not (
        digest_metadata.get("quote_span_locator")
        or digest_metadata.get("machine_field_locator")
    ):
        block_codes.add(tx.BLOCK_MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR)
    seed_bucket = str(target.get("separation_bucket") or "")
    if "PARTIAL" in seed_bucket or "OWNER_LOCATOR" in seed_bucket:
        block_codes.add(tx.BLOCK_SCOPE_TOO_BROAD_FOR_ACCEPTANCE)
    if not digest_metadata.get("revalidation_policy"):
        block_codes.add(tx.BLOCK_REVALIDATION_POLICY_MISSING)
    return sorted(block_codes)
