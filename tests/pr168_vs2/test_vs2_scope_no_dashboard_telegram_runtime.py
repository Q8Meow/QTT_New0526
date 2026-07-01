from src.qtt.paper.pr168_vs2.models import FORBIDDEN_VS2_FILENAMES

from .test_support import ARTIFACT_DIR


def test_forbidden_owner_dashboard_telegram_llm_artifacts_absent() -> None:
    present = {path.name for path in ARTIFACT_DIR.iterdir() if path.is_file()}
    assert present.isdisjoint(FORBIDDEN_VS2_FILENAMES)


def test_no_runtime_modules_created() -> None:
    package_dir = ARTIFACT_DIR.parents[3] / "src" / "qtt" / "paper" / "pr168_vs2"
    forbidden = {"dashboard.py", "telegram.py", "owner_actions.py", "owner_surface_registry.py", "llm_runtime.py"}
    assert {path.name for path in package_dir.glob("*.py")}.isdisjoint(forbidden)
