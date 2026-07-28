from pathlib import Path

from tools.independent_validate_qku_computation_control_plane_operations import (
    main,
)


def test_no_runtime_topology_is_implemented() -> None:
    root = Path(__file__).resolve().parents[4]
    package = (
        root
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
    )
    forbidden = {
        "runtime.py",
        "database.py",
        "backup.py",
        "supervision.py",
    }
    assert forbidden.isdisjoint(path.name for path in package.glob("*.py"))
    assert (package / "service.py").is_file()
    assert main() == 0
