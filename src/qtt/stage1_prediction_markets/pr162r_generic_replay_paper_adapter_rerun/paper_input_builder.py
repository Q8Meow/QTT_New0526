"""Paper adapter input packet builder."""

from __future__ import annotations

from typing import Any

from .adapter_input_common import build_adapter_input_rows


def build_paper_adapter_inputs(
    packets: list[dict[str, Any]],
    computability_by_packet: dict[str, dict[str, Any]],
    binding_by_packet: dict[str, dict[str, Any]],
    smoke_by_formulation: dict[str, dict[str, Any]],
    latency_by_packet: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return build_adapter_input_rows(
        lane="PAPER",
        packets=packets,
        computability_by_packet=computability_by_packet,
        binding_by_packet=binding_by_packet,
        smoke_by_formulation=smoke_by_formulation,
        latency_by_packet=latency_by_packet,
    )
