from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import (
    OLD_LONG_ARTIFACT_NAMES,
    all_artifact_filenames,
)

from ._helpers import report


def test_artifact_name_registry_covers_every_generated_artifact() -> None:
    registry = report("rp5d_artifact_name_registry.json")
    by_name = {str(row["artifact_filename"]): row for row in registry["entries"]}

    assert set(all_artifact_filenames()) == set(by_name)
    assert not set(OLD_LONG_ARTIFACT_NAMES) & set(by_name)
    assert all(row["abbreviation_explanation"] for row in by_name.values())
