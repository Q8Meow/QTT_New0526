"""Backfill previous PR accepted official packet provenance without duplicating packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json


def _records(root: Path, rel_path: Path) -> list[Mapping[str, Any]]:
    path = root / rel_path
    if not path.exists():
        return []
    payload = as_mapping(read_json(path))
    return [as_mapping(record) for record in as_list(payload.get("records"))]


def build_backfill_records(root: Path) -> list[dict[str, Any]]:
    packet_sources = (
        ("PR159", c.PR159_ACCEPTED_PACKET_REGISTRY, c.PR159_TARGET_FIELD_LEDGER_REGISTRY),
        ("PR159R", c.PR159R_ACCEPTED_PACKET_REGISTRY, c.PR159R_TARGET_FIELD_LEDGER_REGISTRY),
    )
    records: list[dict[str, Any]] = []
    for prior_pr_label, packet_path, ledger_path in packet_sources:
        ledgers = _records(root, ledger_path)
        ledgers_by_packet = {
            str(item.get("accepted_packet_id")): item
            for item in ledgers
            if item.get("accepted_packet_id")
        }
        for packet in _records(root, packet_path):
            packet_id = str(packet.get("accepted_packet_id"))
            ledger = ledgers_by_packet.get(packet_id, {})
            target_id = str(packet.get("target_id_or_row_id") or ledger.get("target_id_or_row_id"))
            locator = packet.get("source_url_or_repo_relative_capture_path") or packet.get("locator_value")
            quote_locator = packet.get("quote_span_or_machine_field_locator")
            records.append(
                {
                    "backfill_record_id": f"PR159S_OFFICIAL_BACKFILL__{prior_pr_label}__{len(records)+1:04d}",
                    "source_provenance_tag": c.SourceProvenanceTag.OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR.value,
                    "official_confirmed_flag": True,
                    "official_source_packet_id": packet_id,
                    "official_source_class": packet.get("official_source_class"),
                    "official_source_locator": locator,
                    "accepted_ledger_record_id": ledger.get("ledger_record_id"),
                    "target_id_or_row_id": target_id,
                    "target_field_path": packet.get("target_field_id") or ledger.get("target_field_id"),
                    "target_field_scope": packet.get("source_population") or ledger.get("source_population"),
                    "platform": _platform_from_target(target_id),
                    "prior_pr_label": prior_pr_label,
                    "prior_artifact_path": packet_path.as_posix(),
                    "revalidation_class": packet.get("revalidation_class") or ledger.get("revalidation_due_class"),
                    "official_confirmation_basis": "accepted official source packet and target-field ledger from previous PR",
                    "source_capture_or_quote_locator": quote_locator,
                    "machine_field_locator": as_mapping(quote_locator).get("machine_field_locator"),
                    "authority_class": c.AuthorityClass.ACCEPTED_OFFICIAL_EXTERNAL_FACT.value,
                    "profit_validation_tag": c.ProfitValidationTag.PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR.value,
                    "not_duplicated_by_pr159s_flag": True,
                    "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
                }
            )
    return records


def _platform_from_target(target_id: str) -> str:
    for platform in ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR"):
        if platform in target_id:
            return platform
    return "PREDICTION_MARKETS_GENERAL"

