from __future__ import annotations

import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_pr169_val1 as val1


def test_val1_accepts_downloaded_timing_and_router_artifacts(tmp_path: Path):
    for phase in runner.ORDERED_PHASES:
        timing_dir = tmp_path / f"validation-timing-{phase}"
        router_dir = tmp_path / f"validation-router-{phase}"
        timing_dir.mkdir()
        router_dir.mkdir()
        (timing_dir / f"{phase}.json").write_text(
            json.dumps({"phase": phase, "total_elapsed_seconds": 1.0}),
            encoding="utf-8",
        )
        (router_dir / f"{phase}.json").write_text(
            json.dumps({"phase": phase, "full_validation_required": True}),
            encoding="utf-8",
        )

    assert val1.validate_artifacts(tmp_path, runner.ORDERED_PHASES) == []


def test_val1_rejects_missing_router_artifact(tmp_path: Path):
    phase = runner.ORDERED_PHASES[0]
    timing_dir = tmp_path / f"validation-timing-{phase}"
    timing_dir.mkdir()
    (timing_dir / f"{phase}.json").write_text("{}", encoding="utf-8")

    failures = val1.validate_artifacts(tmp_path, (phase,))

    assert failures == [f"VAL1_ROUTER_ARTIFACT_MISSING: {phase}"]
