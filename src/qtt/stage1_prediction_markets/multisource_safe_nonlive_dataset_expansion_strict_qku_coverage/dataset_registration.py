"""PR162C dataset registration helpers."""

from __future__ import annotations

from typing import Any


def registered_dataset_records(pr162a_datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dataset_id": record["dataset_id"],
            "source_dataset_created_by_pr": record.get("created_by_pr"),
            "registration_status": "REGISTERED_AS_PR162C_INPUT_CANDIDATE",
        }
        for record in pr162a_datasets
    ]
