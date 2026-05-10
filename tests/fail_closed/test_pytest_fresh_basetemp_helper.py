from datetime import UTC, datetime
from pathlib import Path
import re
import tempfile

from tools import run_pytest_fresh_basetemp as helper


def _fixed_basetemp() -> Path:
    return (
        Path(tempfile.gettempdir())
        / "qtt_pytest_basetemp"
        / "pytest_20260508_120000_000000_1234"
    )


def _custom_basetemp() -> Path:
    return Path(tempfile.gettempdir()) / "qtt_pytest_custom"


def test_helper_builds_pytest_command_using_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(helper.sys, "executable", python_executable)

    invocation = helper.build_pytest_invocation(
        ["tests/fail_closed", "-q"],
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.command[:3] == [python_executable, "-m", "pytest"]


def test_helper_adds_basetemp_when_absent():
    pytest_args = ["tests/fail_closed", "-q"]
    basetemp = _fixed_basetemp()

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=basetemp,
    )

    assert invocation.added_basetemp is True
    assert invocation.basetemp == str(basetemp)
    assert invocation.command[3:-2] == pytest_args
    assert invocation.command[-2:] == ["--basetemp", str(basetemp)]


def test_helper_preserves_user_pytest_args():
    pytest_args = ["tests/fail_closed", "-q", "-k", "scanner"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.command[3:-2] == pytest_args


def test_helper_does_not_duplicate_basetemp_when_separate_arg_supplied():
    custom_basetemp = str(_custom_basetemp())
    pytest_args = ["tests/fail_closed", "--basetemp", custom_basetemp, "-q"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.added_basetemp is False
    assert invocation.basetemp == custom_basetemp
    assert invocation.command[3:] == pytest_args
    assert invocation.command.count("--basetemp") == 1
    assert str(_fixed_basetemp()) not in invocation.command


def test_helper_does_not_duplicate_basetemp_when_equals_arg_supplied():
    custom_basetemp = str(_custom_basetemp())
    pytest_args = ["tests/fail_closed", f"--basetemp={custom_basetemp}", "-q"]

    invocation = helper.build_pytest_invocation(
        pytest_args,
        fresh_basetemp=_fixed_basetemp(),
    )

    assert invocation.added_basetemp is False
    assert invocation.basetemp == custom_basetemp
    assert invocation.command[3:] == pytest_args
    assert not any(arg == "--basetemp" for arg in invocation.command)


def test_selected_fresh_basetemp_is_under_system_temp():
    basetemp = helper.make_fresh_basetemp(
        now=datetime(2026, 5, 8, 12, 34, 56, 123456, tzinfo=UTC),
        pid=4321,
    )

    assert basetemp.parent == Path(tempfile.gettempdir()) / "qtt_pytest_basetemp"
    assert basetemp.name == "pytest_20260508_123456_123456_4321"


def test_selected_fresh_basetemp_is_short_and_windows_safe():
    basetemp = helper.make_fresh_basetemp(
        now=datetime(2026, 5, 8, 12, 34, 56, 123456, tzinfo=UTC),
        pid=4321,
    )

    assert len(str(basetemp)) <= helper.MAX_BASETEMP_TEXT_LENGTH
    assert re.fullmatch(r"pytest_\d{8}_\d{6}_\d{6}_4321", basetemp.name)
    assert not any(char in basetemp.name for char in '<>:"/\\|?*')


def test_main_prints_basetemp_and_returns_pytest_exit_code(monkeypatch, capsys):
    class Completed:
        returncode = 7

    seen: dict[str, list[str]] = {}

    def fake_run(command: list[str]) -> Completed:
        seen["command"] = command
        return Completed()

    monkeypatch.setattr(helper.subprocess, "run", fake_run)

    custom_basetemp = str(_custom_basetemp())
    exit_code = helper.main(["tests/fail_closed", "--basetemp", custom_basetemp, "-q"])

    assert exit_code == 7
    assert seen["command"][1:3] == ["-m", "pytest"]
    assert capsys.readouterr().out == f"pytest basetemp: {custom_basetemp}\n"


def test_helper_introduces_no_blocked_behavior_terms():
    helper_text = Path(helper.__file__).read_text(encoding="utf-8").lower()

    for blocked_term in ["runtime", "live", "source", "order", "sha", "freeze", "profit"]:
        assert blocked_term not in helper_text
