from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c


def counts(artifacts):
    return artifacts["master"]["count_invariant_receipt"]


def no_authority_records(payload):
    return all(
        all(value is False for value in record.get("no_authority_confirmation", {}).values())
        for record in payload["records"]
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def quantum_relevant(records):
    return [record for record in records if record.get("quantum_relevance_flag") is True]


def forbidden_value_strings():
    return c.FORBIDDEN_PLACEHOLDER_VALUES

