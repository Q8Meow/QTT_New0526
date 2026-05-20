import json
from pathlib import Path
import shutil

from src.qtt.stage1_prediction_markets.credential_readiness.validator import (
    REPORT_PATHS,
    write_fixture_files,
    write_generated_reports,
)
from tests.source_evidence import pr131_credential_alias_readiness_support as support


def _reports_under(root):
    return {
        key: json.loads((root / path).read_text(encoding="utf-8"))
        for key, path in REPORT_PATHS.items()
    }


def test_pr131_generated_reports_are_deterministic():
    generated = support.generated_report_payloads()
    built = support.artifacts()

    for key, payload in generated.items():
        assert payload == built[key]

    base = Path(".tmp") / "pr131_deterministic_report_test"
    first = base / "first"
    second = base / "second"
    try:
        shutil.rmtree(base, ignore_errors=True)
        first.mkdir(parents=True)
        second.mkdir(parents=True)
        write_fixture_files(support.REPO_ROOT, first)
        write_generated_reports(support.REPO_ROOT, first)
        write_fixture_files(support.REPO_ROOT, second)
        write_generated_reports(support.REPO_ROOT, second)

        assert _reports_under(first) == _reports_under(second)
    finally:
        shutil.rmtree(base, ignore_errors=True)
