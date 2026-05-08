from pathlib import Path

from tools.master_plan_ingest import (
    MASTER_PLAN_MARKERS,
    build_section_manifest,
    build_traceability_report,
)
from tools.master_plan_traceability_check import (
    SOURCE_EVIDENCE_PACKET_MARKERS,
    SOURCE_EVIDENCE_PACKET_NAME,
    validate_traceability,
)


def _write_packet(root: Path, omitted_marker_name: str | None = None) -> Path:
    packet_dir = root / "source_evidence"
    packet_dir.mkdir(parents=True)
    packet_path = packet_dir / SOURCE_EVIDENCE_PACKET_NAME
    markers = [
        marker
        for name, marker in SOURCE_EVIDENCE_PACKET_MARKERS.items()
        if name != omitted_marker_name
    ]
    packet_path.write_text("\n".join(markers) + "\n", encoding="utf-8")
    return packet_path


def _write_master_plan(root: Path) -> Path:
    text = "\n".join(
        [
            *MASTER_PLAN_MARKERS.values(),
            "# Master Plan",
            "## 0X.1 One",
            "### 0X.1A Child",
            "```text",
            "## 21.6AE1 Ignored fenced heading",
            "```",
            "## 21.6AE1 Accurate alphanumeric ID",
        ]
    )
    path = root / "QTT_MasterPlan_Current.md"
    path.write_text(text + "\n", encoding="utf-8")
    return path


def test_traceability_validation_accepts_recomputed_static_reports(tmp_path):
    master = _write_master_plan(tmp_path)
    packet = _write_packet(tmp_path)
    text = master.read_text(encoding="utf-8")
    manifest = build_section_manifest(
        master.as_posix(), text, file_size_bytes=master.stat().st_size
    )
    trace = build_traceability_report(master.as_posix(), manifest, text)

    failures = validate_traceability(
        master_plan=master,
        manifest=manifest,
        trace=trace,
        expected_document=master.as_posix(),
        source_packet=packet,
        min_master_plan_bytes=1,
        min_master_plan_lines=1,
    )

    assert failures == []


def test_traceability_validation_catches_report_count_drift(tmp_path):
    master = _write_master_plan(tmp_path)
    packet = _write_packet(tmp_path)
    text = master.read_text(encoding="utf-8")
    manifest = build_section_manifest(
        master.as_posix(), text, file_size_bytes=master.stat().st_size
    )
    trace = build_traceability_report(master.as_posix(), manifest, text)
    trace["sections_indexed"] += 1

    failures = validate_traceability(
        master_plan=master,
        manifest=manifest,
        trace=trace,
        expected_document=master.as_posix(),
        source_packet=packet,
        min_master_plan_bytes=1,
        min_master_plan_lines=1,
    )

    assert any("sections_indexed" in failure for failure in failures)


def test_traceability_validation_catches_source_packet_marker_drift(tmp_path):
    master = _write_master_plan(tmp_path)
    packet = _write_packet(tmp_path, omitted_marker_name="external_fact_authority_blocked")
    text = master.read_text(encoding="utf-8")
    manifest = build_section_manifest(
        master.as_posix(), text, file_size_bytes=master.stat().st_size
    )
    trace = build_traceability_report(master.as_posix(), manifest, text)

    failures = validate_traceability(
        master_plan=master,
        manifest=manifest,
        trace=trace,
        expected_document=master.as_posix(),
        source_packet=packet,
        min_master_plan_bytes=1,
        min_master_plan_lines=1,
    )

    assert any("source-evidence definitions packet markers missing" in failure for failure in failures)
