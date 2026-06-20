from pathlib import Path

from tools import run_validation_gates as runner


def test_pr106_acceptance_gate_is_ordered_after_retrieval_and_preserves_fresh_tmp(monkeypatch):
    repo_root = Path(".tmp/test_pr123_pr106_run_validation_gates").resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    seen_basetemps: list[Path] = []

    def fake_run_commands(commands: list[list[str]]) -> int:
        command_names = [Path(command[1]).name for command in commands]
        retrieval_index = command_names.index("validate_source_evidence_retrieval_executor.py")
        acceptance_index = command_names.index("validate_source_evidence_acceptance.py")
        connector_index = command_names.index("validate_connector_capability_static.py")
        assert retrieval_index < acceptance_index < connector_index
        pytest_command = next(
            command
            for command in commands
            if Path(command[1]).name == "run_pytest_fresh_basetemp.py"
        )
        basetemp = Path(pytest_command[pytest_command.index("--basetemp") + 1])
        assert not basetemp.is_relative_to(repo_root)
        assert basetemp.name.startswith("run_validation_gates_pytest_")
        seen_basetemps.append(basetemp)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main([]) == 0
    finally:
        for child in sorted((repo_root / ".tmp").glob("*"), reverse=True):
            if child.is_dir():
                for path in sorted(child.rglob("*"), reverse=True):
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                child.rmdir()
        if (repo_root / ".tmp").exists():
            (repo_root / ".tmp").rmdir()
        if repo_root.exists():
            repo_root.rmdir()
    assert seen_basetemps
