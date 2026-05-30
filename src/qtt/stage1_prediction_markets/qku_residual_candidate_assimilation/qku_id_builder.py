"""Deterministic non-hash QKU and graph edge ID builders."""

from __future__ import annotations

import re


_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.:-]+")
_SAFE_NAME_RE = re.compile(r"[^a-z0-9]+")


def safe_id(value: object) -> str:
    text = str(value or "UNSPECIFIED").strip()
    text = _SAFE_ID_RE.sub("_", text)
    return text.strip("_") or "UNSPECIFIED"


def normalize_name(value: object) -> str:
    text = str(value or "unspecified").strip().lower()
    text = _SAFE_NAME_RE.sub("_", text)
    return text.strip("_") or "unspecified"


def atomicrow_qku_id(row_id: str) -> str:
    return f"QKU-ATOMICROW-{safe_id(row_id)}"


def pr154_qku_id(target_id: str) -> str:
    return f"QKU-PR154-{safe_id(target_id)}"


def residual_qku_id(assimilation_queue_id: str) -> str:
    return f"QKU-RESIDUAL-PR161B-{safe_id(assimilation_queue_id)}"


def field_facet_qku_id(parent_qku_id: str, serial: int) -> str:
    return f"QKU-FIELD-FACET-{safe_id(parent_qku_id)}-{serial:05d}"


def graph_node_id(qku_id: str) -> str:
    return f"QKUNODE-{safe_id(qku_id)}"


def graph_edge_id(source_qku_id: str, edge_direction: str, edge_type: str, serial: int) -> str:
    direction = "UP" if edge_direction.upper().startswith("UP") else "DOWN"
    return f"QKUEDGE-{direction}-{safe_id(source_qku_id)}-{safe_id(edge_type)}-{serial:04d}"
