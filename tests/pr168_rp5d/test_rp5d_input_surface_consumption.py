from __future__ import annotations

from ._helpers import rows


def test_every_input_surface_has_non_orphan_consumption_row() -> None:
    inventory = rows("rp5d_input_inventory.jsonl")
    consumption = rows("rp5d_input_consumption.jsonl")
    consumed_refs = {row["input_surface_ref"] for row in consumption}

    assert {row["input_surface_ref"] for row in inventory} == consumed_refs
    assert all(row["orphan_flag"] is False for row in consumption)
    assert all(row["consumer_output_refs"] for row in consumption)
