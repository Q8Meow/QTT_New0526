from tools import run_validation_gates as runner
from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_preserves_run_validation_gates_fresh_tempdir():
    command_names = [command[1] for command in runner.build_validation_commands()]

    assert any(
        "venue_market_data_ingest_adapters_validate.py" in name
        for name in command_names
    )
    assert support.main_report()["PR132_VALIDATION_EVIDENCE"][
        "run_validation_gates_uses_fresh_pytest_basetemp"
    ] is True
