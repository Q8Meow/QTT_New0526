from src.qtt.memory.pr168_mem1.validator import validate_mem1_artifacts

from .test_support import ARTIFACT_DIR, REPO_ROOT


def test_mem1_validator_passes_generated_artifacts() -> None:
    assert validate_mem1_artifacts(REPO_ROOT, ARTIFACT_DIR) == []
