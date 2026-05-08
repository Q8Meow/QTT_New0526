from pathlib import Path

from tools.master_plan_ingest import (
    MASTER_PLAN_MARKERS,
    build_section_manifest,
    extract_sections,
)
from tools.master_plan_traceability_check import SOURCE_EVIDENCE_PACKET_MARKERS


def _marker_block() -> str:
    return "\n".join(MASTER_PLAN_MARKERS.values())


def test_section_parser_ignores_fenced_headings_and_preserves_alphanumeric_ids():
    text = "\n".join(
        [
            "# Root",
            "```markdown",
            "## 0X.9 Hidden fenced heading",
            "```",
            "## 0X.0A Visible heading ##",
            "### 21.6AE1 Mixed alphanumeric suffix",
            "#### 20B.1A2A Venue suffix",
            "~~~text",
            "### 3.3AB0A Hidden fenced heading",
            "~~~",
            "### 2.24A1A.3 Dotted mixed suffix",
        ]
    )

    sections = extract_sections(text)

    assert [section["canonical_id"] for section in sections] == [
        None,
        "0X.0A",
        "21.6AE1",
        "20B.1A2A",
        "2.24A1A.3",
    ]
    assert sections[1]["title"] == "0X.0A Visible heading"
    assert sections[2]["parent_canonical_id"] == "0X.0A"
    assert sections[3]["parent_canonical_id"] == "21.6AE1"
    assert sections[4]["parent_canonical_id"] == "0X.0A"
    assert [section["index"] for section in sections] == [1, 2, 3, 4, 5]


def test_section_manifest_fields_are_static_and_recomputable():
    text = _marker_block() + "\n# Master\n## 0X.1 One\n### 0X.1A Child\n"
    manifest = build_section_manifest("docs/master_plan/QTT_MasterPlan_Current.md", text)

    assert manifest["schema_version"] == 2
    assert manifest["deterministic_output"] is True
    assert manifest["line_count"] == text.count("\n") + 1
    assert manifest["char_count"] == len(text)
    assert manifest["file_size_bytes"] == len(text.encode("utf-8"))
    assert manifest["section_count"] == 3
    assert manifest["canonical_id_count"] == 2
    assert manifest["duplicate_canonical_ids"] == []
    assert all(manifest["required_markers"].values())


def test_master_plan_and_source_packet_guardrail_markers_present():
    master = Path("docs/master_plan/QTT_MasterPlan_Current.md").read_text(encoding="utf-8")
    packet = Path(
        "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
    ).read_text(encoding="utf-8")

    assert all(marker in master for marker in MASTER_PLAN_MARKERS.values())
    assert all(marker in packet for marker in SOURCE_EVIDENCE_PACKET_MARKERS.values())
