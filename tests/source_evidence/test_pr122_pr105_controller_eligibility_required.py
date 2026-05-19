from __future__ import annotations

import json
from pathlib import Path


ROSTER = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
CONTROLLER = Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json")
ROADMAP_INDEX = Path("docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json")
BLUEPRINT_INDEX = Path("docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json")
ROADMAP_TEXT = Path(
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md"
)
BLUEPRINT_TEXT = Path(
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md"
)
PR122_REPORT = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR122_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATED_REPORT.json"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry(entries: list[dict], **expected: object) -> dict:
    for item in entries:
        if all(item.get(key) == value for key, value in expected.items()):
            return item
    raise AssertionError(f"missing entry: {expected}")


def test_pr105_identity_is_roadmap_blueprint_planned_not_github_105_or_repo_pr122():
    roster = _json(ROSTER)
    entries = roster["entries"]

    planned = _entry(entries, roster_entry_id="ROADMAP_PR_105_PLANNED")
    mismatch = _entry(entries, roster_entry_id="GITHUB_PR_105_IDENTITY_MISMATCH")

    assert planned["roadmap_pr_label"] == "PR #105"
    assert planned["blueprint_pr_label"] == "PR #105"
    assert planned["repo_canonical_pr_label"] is None
    assert planned["github_pr_number"] is None
    assert planned["current_status"] == "PLANNED"
    assert planned["identity_relation_class"] == "ROADMAP_ONLY_PLANNED"

    assert mismatch["github_pr_number"] == 105
    assert mismatch["same_number_mismatch_recorded"] is True
    assert mismatch["repo_canonical_pr_label"] != "PR122"
    assert mismatch["github_title"] != planned["roadmap_title"]


def test_pr105_controller_roadmap_and_blueprint_scope_match():
    controller = _json(CONTROLLER)
    mapping = _entry(
        controller["roadmap_range_currentization"],
        roadmap_pr_label="PR #105",
    )
    roadmap_entry = _entry(_json(ROADMAP_INDEX)["pr_entries"], number=105)
    blueprint_entry = _entry(_json(BLUEPRINT_INDEX)["entries"], number=105)

    assert mapping["controller_state"] == (
        "SOURCE_EVIDENCE_STATE_CONTROLLED_BY_ACCEPTED_SOURCE_WORKFLOW"
    )
    assert mapping["next_allowed_action_class"] == (
        "FUTURE_REPO_PR_REQUIRED_BEFORE_MATERIALIZATION"
    )
    assert roadmap_entry["title"] == "Source-evidence retrieval executor"
    assert roadmap_entry["marker"] == "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK"
    assert blueprint_entry["title"] == "Source-evidence retrieval executor"
    assert "candidate retrieval receipts only" in blueprint_entry["purpose"]
    assert "Accepted source facts" in blueprint_entry["must_not_create"]


def test_full_roadmap_and_blueprint_text_contain_pr105_scope():
    roadmap_text = ROADMAP_TEXT.read_text(encoding="utf-8")
    blueprint_text = BLUEPRINT_TEXT.read_text(encoding="utf-8")

    for text in (roadmap_text, blueprint_text):
        assert "PR #105" in text
        assert "Source-evidence retrieval executor" in text
        assert "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK" in text
        assert "Accepted source facts" in text


def test_pr122_report_records_controller_eligible_control_plane_with_target_block():
    report = _json(PR122_REPORT)

    assert report["controller_eligibility_state"] == (
        "ELIGIBLE_FOR_SCHEMA_CONTROL_PLANE_WITH_TARGET_DERIVATION_BLOCK"
    )
    assert report["implementation_performed"] is True
    assert report["source_retrieval_target_count"] == 0
    assert report["source_retrieval_target_derivation_source"][
        "canonical_target_like_rows"
    ] == 0
    assert report["target_derivation_block_receipt"].endswith(
        "CODEX_PR122_SOURCE_EVIDENCE_TARGET_DERIVATION_BLOCK_RECEIPT.json"
    )
