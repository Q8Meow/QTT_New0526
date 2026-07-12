from __future__ import annotations

from typing import Any

from tests.pr168_rp5b._helpers import assert_rp5b_valid, final_summary, load_rows
from tools import pr168_rp5b_validator as validator
from tools.pr168_rp5b_config import DELETE_ACTIONS, PROTECTED_CLASSIFICATIONS


GOVERNED_PATH = "docs/master_plan/generated/rp5a/governed_candidate.report.json"
UNRELATED_PR169_ROLLBACK_PATH = (
    "src/qtt/stage1_prediction_markets/pr169_qku_formula_exp1/runtime.py"
)
DELETE_ACTION = next(iter(DELETE_ACTIONS))
PROTECTED_CLASSIFICATION = next(iter(PROTECTED_CLASSIFICATIONS))
SECOND_GOVERNED_PATH = "docs/master_plan/generated/rp5a/second_candidate.report.json"


def _candidate(path: str = GOVERNED_PATH) -> dict[str, Any]:
    return {
        "file_path": path,
        "rp5b_reverification_required_flag": True,
    }


def _verification(
    path: str = GOVERNED_PATH,
    *,
    classification: str = "DELETE_FROM_ACTIVE_TREE_SAFE",
    final_action: str = "KEEP_SOURCE_CODE",
    safe_to_delete: bool = False,
    contains_unique_identity: bool = False,
) -> dict[str, Any]:
    return {
        "file_path": path,
        "rp5a_classification": classification,
        "final_action": final_action,
        "safe_to_delete_now_flag": safe_to_delete,
        "contains_unique_qku_formula_identity_now_flag": contains_unique_identity,
    }


def _manifest_delete(path: str = GOVERNED_PATH) -> dict[str, str]:
    return {"file_path": path, "git_action": "DELETE"}


def _deletion_failures(
    *,
    candidate_rows: list[dict[str, Any]] | None = None,
    verification_rows: list[dict[str, Any]] | None = None,
    preservation_rows: list[dict[str, Any]] | None = None,
    deleted_rows: list[dict[str, Any]] | None = None,
    actual_deleted: set[str] | None = None,
) -> list[str]:
    return validator._deletion_failures(
        candidate_rows if candidate_rows is not None else [_candidate()],
        verification_rows if verification_rows is not None else [_verification()],
        preservation_rows if preservation_rows is not None else [],
        deleted_rows if deleted_rows is not None else [],
        actual_deleted if actual_deleted is not None else set(),
    )


def test_unrelated_pr169_rollback_deletions_do_not_create_manifest_mismatch() -> None:
    assert _deletion_failures(actual_deleted={UNRELATED_PR169_ROLLBACK_PATH}) == []


def test_unstaged_git_status_deletion_preserves_full_repo_path() -> None:
    args = ["git", "status", "--short", "--untracked-files=all"]
    assert validator._deleted_files_from_git_output(
        args,
        f" D {GOVERNED_PATH}\n",
    ) == {GOVERNED_PATH}


def test_undeclared_deletion_inside_governed_universe_fails() -> None:
    failures = _deletion_failures(actual_deleted={GOVERNED_PATH})
    assert any(
        failure.startswith("DELETED_MANIFEST_GIT_MISMATCH:")
        and GOVERNED_PATH in failure
        for failure in failures
    )


def test_manifest_deletion_without_verification_still_fails() -> None:
    failures = _deletion_failures(
        verification_rows=[],
        deleted_rows=[_manifest_delete()],
        actual_deleted={GOVERNED_PATH},
    )
    assert f"DELETED_WITHOUT_VERIFICATION:{GOVERNED_PATH}" in failures


def test_manifest_deletion_requires_safe_delete_verification_action() -> None:
    failures = _deletion_failures(
        verification_rows=[_verification()],
        deleted_rows=[_manifest_delete()],
        actual_deleted={GOVERNED_PATH},
    )
    assert f"DELETE_ACTION_WITHOUT_SAFE_FLAG:{GOVERNED_PATH}" in failures
    assert (
        f"DELETED_WITHOUT_DELETE_ACTION:{GOVERNED_PATH}:KEEP_SOURCE_CODE"
        in failures
    )


def test_protected_rp5b_deletion_still_fails() -> None:
    failures = _deletion_failures(
        verification_rows=[
            _verification(
                classification=PROTECTED_CLASSIFICATION,
                final_action=DELETE_ACTION,
                safe_to_delete=True,
            )
        ],
        deleted_rows=[_manifest_delete()],
        actual_deleted={GOVERNED_PATH},
    )
    assert f"PROTECTED_FILE_SELECTED_FOR_DELETE:{GOVERNED_PATH}" in failures


def test_unsafe_rp5b_deletion_still_fails() -> None:
    failures = _deletion_failures(
        verification_rows=[_verification(final_action=DELETE_ACTION)],
        deleted_rows=[_manifest_delete()],
        actual_deleted={GOVERNED_PATH},
    )
    assert f"DELETE_ACTION_WITHOUT_SAFE_FLAG:{GOVERNED_PATH}" in failures


def test_unique_identity_deletion_without_preservation_still_fails() -> None:
    failures = _deletion_failures(
        verification_rows=[
            _verification(
                final_action=DELETE_ACTION,
                safe_to_delete=True,
                contains_unique_identity=True,
            )
        ],
        deleted_rows=[_manifest_delete()],
        actual_deleted={GOVERNED_PATH},
    )
    assert f"DELETED_IDENTITY_WITHOUT_PRESERVATION:{GOVERNED_PATH}" in failures


def test_candidate_verification_path_drift_fails() -> None:
    failures = _deletion_failures(
        verification_rows=[_verification(SECOND_GOVERNED_PATH)],
    )
    assert any(
        failure.startswith("CANDIDATE_VERIFICATION_PATH_MISMATCH:")
        for failure in failures
    )


def test_candidate_verification_duplicate_multiplicity_drift_fails() -> None:
    failures = _deletion_failures(
        candidate_rows=[
            _candidate(),
            _candidate(),
            _candidate(SECOND_GOVERNED_PATH),
        ],
        verification_rows=[
            _verification(),
            _verification(SECOND_GOVERNED_PATH),
            _verification(SECOND_GOVERNED_PATH),
        ],
    )
    assert any(failure.startswith("CANDIDATE_DUPLICATE_PATHS:") for failure in failures)
    assert any(
        failure.startswith("VERIFICATION_DUPLICATE_PATHS:") for failure in failures
    )
    assert any(
        failure.startswith("CANDIDATE_VERIFICATION_PATH_MULTIPLICITY_MISMATCH:")
        for failure in failures
    )


def test_deleted_manifest_matches_git_deletions() -> None:
    assert_rp5b_valid()
    assert load_rows("deleted_from_active_tree_rows") == []
    assert final_summary()["files_deleted_count"] == 0
