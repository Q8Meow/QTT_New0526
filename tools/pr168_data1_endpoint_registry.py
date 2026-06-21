#!/usr/bin/env python3
"""Endpoint registry facade for PR168-DATA1."""

from __future__ import annotations

from tools.pr168_data1_online_doc_discovery import endpoint_contract_rows


def build_endpoint_registry(now_utc: str) -> list[dict[str, object]]:
    return endpoint_contract_rows(now_utc)
