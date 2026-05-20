from tests.source_evidence.pr128_cross_venue_execution_normalization_support import (
    REPO_ROOT,
    main_report,
)


def test_pr128_preserves_run_validation_gates_fresh_tempdir():
    text = (REPO_ROOT / "tools/run_validation_gates.py").read_text(encoding="utf-8")

    assert main_report()["run_validation_gates_uses_fresh_pytest_basetemp"] is True
    assert main_report()["fixed_tmp_run_validation_gates_pytest_reused"] is False
    assert 'prefix="run_validation_gates_pytest_"' in text
    assert ".tmp/run_validation_gates_pytest" not in text
