#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

try:
    from tools.master_plan_ingest import (
        MASTER_PLAN_MARKERS,
        build_section_manifest,
        duplicate_canonical_ids,
        line_count,
        marker_report,
    )
except ModuleNotFoundError:  # pragma: no cover - used when executed from tools/
    from master_plan_ingest import (  # type: ignore
        MASTER_PLAN_MARKERS,
        build_section_manifest,
        duplicate_canonical_ids,
        line_count,
        marker_report,
    )

MIN_MASTER_PLAN_BYTES = 10_000_000
MIN_MASTER_PLAN_LINES = 100_000

SOURCE_EVIDENCE_PACKET_NAME = "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
SOURCE_EVIDENCE_PACKET_MARKERS = {
    "packet_id": "packet_id = QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET",
    "packet_version": (
        "packet_version = "
        "v1.3A_OWNER_APPROVED_EXECUTION_MECHANICS_ABSTRACTION_AND_RETRIEVAL_READINESS_CURRENTIZATION_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "packet_authority_class": (
        "packet_authority_class = OWNER_POLICY_AND_RETRIEVAL_SCOPE_INPUT_NOT_EXTERNAL_FACT_AUTHORITY"
    ),
    "external_fact_authority_blocked": (
        "owner_source_evidence_definitions_packet_can_authorize_external_fact_value = false"
    ),
    "connector_semantic_population_blocked": (
        "owner_source_evidence_definitions_packet_can_populate_connector_semantic_value = false"
    ),
    "this_packet_retrieves_no_source_facts": "this_packet_retrieves_source_facts = false",
    "this_packet_accepts_no_source_facts": "this_packet_accepts_source_facts = false",
    "retrieval_queue_not_executed": "this_packet_does_not_execute_retrieval_target_queue = true",
    "source_target_paths_not_unlocked": "this_packet_does_not_unlock_source_target_field_paths = true",
}


def _as_posix(path: str | pathlib.Path) -> str:
    return pathlib.Path(path).as_posix()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _missing_markers(text: str, markers: dict[str, str]) -> list[str]:
    return [name for name, present in marker_report(text, markers).items() if not present]


def _default_source_packet_path(master_plan: pathlib.Path) -> pathlib.Path:
    return master_plan.parent / "source_evidence" / SOURCE_EVIDENCE_PACKET_NAME


def validate_traceability(
    *,
    master_plan: pathlib.Path,
    manifest: dict[str, Any],
    trace: dict[str, Any],
    expected_document: str,
    source_packet: pathlib.Path | None = None,
    min_master_plan_bytes: int = MIN_MASTER_PLAN_BYTES,
    min_master_plan_lines: int = MIN_MASTER_PLAN_LINES,
) -> list[str]:
    failures: list[str] = []
    text = master_plan.read_text(encoding="utf-8")
    expected_document = _as_posix(expected_document)
    actual_bytes = master_plan.stat().st_size
    recomputed_manifest = build_section_manifest(
        expected_document, text, file_size_bytes=actual_bytes
    )

    if _as_posix(str(manifest.get("document", ""))) != expected_document:
        failures.append("section manifest document does not match master-plan argument")
    if _as_posix(str(trace.get("document", ""))) != expected_document:
        failures.append("traceability report document does not match master-plan argument")

    actual_lines = line_count(text)
    if actual_lines < min_master_plan_lines:
        failures.append(
            f"master-plan line count is too small: {actual_lines} < {min_master_plan_lines}"
        )
    if actual_bytes < min_master_plan_bytes:
        failures.append(
            f"master-plan file size is too small: {actual_bytes} < {min_master_plan_bytes}"
        )

    missing_master_markers = _missing_markers(text, MASTER_PLAN_MARKERS)
    if missing_master_markers:
        failures.append(
            "master-plan currentization markers missing: "
            + ", ".join(missing_master_markers)
        )

    manifest_sections = manifest.get("sections")
    if not isinstance(manifest_sections, list):
        failures.append("section manifest sections field must be a list")
        manifest_sections = []

    if manifest.get("schema_version") != 2:
        failures.append("section manifest schema_version must be 2")
    if manifest.get("deterministic_output") is not True:
        failures.append("section manifest deterministic_output must be true")
    if manifest.get("source") != "full_owner_master_plan":
        failures.append("section manifest source must be full_owner_master_plan")
    if manifest.get("section_count") != len(manifest_sections):
        failures.append("section manifest section_count does not match sections length")
    if manifest.get("section_count") != recomputed_manifest["section_count"]:
        failures.append("section manifest section_count does not match recomputed headings")
    if manifest_sections != recomputed_manifest["sections"]:
        failures.append("section manifest sections do not match recomputed parser output")
    if manifest.get("line_count") != actual_lines:
        failures.append("section manifest line_count does not match master plan")
    if manifest.get("file_size_bytes") != actual_bytes:
        failures.append("section manifest file_size_bytes does not match master plan")
    if manifest.get("char_count") != len(text):
        failures.append("section manifest char_count does not match master plan")
    if manifest.get("canonical_id_count") != recomputed_manifest["canonical_id_count"]:
        failures.append("section manifest canonical_id_count does not match recomputed headings")
    if manifest.get("unique_canonical_id_count") != recomputed_manifest["unique_canonical_id_count"]:
        failures.append(
            "section manifest unique_canonical_id_count does not match recomputed headings"
        )
    if manifest.get("duplicate_canonical_ids") != duplicate_canonical_ids(manifest_sections):
        failures.append("section manifest duplicate_canonical_ids does not match sections")
    if manifest.get("required_markers") != marker_report(text, MASTER_PLAN_MARKERS):
        failures.append("section manifest required_markers do not match master plan")

    if trace.get("schema_version") != 2:
        failures.append("traceability report schema_version must be 2")
    if trace.get("traceability_status") != "generated_from_full_owner_master_plan":
        failures.append("traceability report status is not generated_from_full_owner_master_plan")
    if trace.get("section_manifest_schema_version") != manifest.get("schema_version"):
        failures.append("traceability report manifest schema version does not match manifest")
    if trace.get("sections_indexed") != manifest.get("section_count"):
        failures.append("traceability report sections_indexed does not match manifest")
    if trace.get("canonical_ids_indexed") != manifest.get("canonical_id_count"):
        failures.append("traceability report canonical_ids_indexed does not match manifest")
    if trace.get("unique_canonical_ids_indexed") != manifest.get("unique_canonical_id_count"):
        failures.append("traceability report unique canonical ID count does not match manifest")
    if trace.get("duplicate_canonical_ids") != manifest.get("duplicate_canonical_ids"):
        failures.append("traceability report duplicate_canonical_ids do not match manifest")
    if trace.get("line_count") != manifest.get("line_count"):
        failures.append("traceability report line_count does not match manifest")
    if trace.get("file_size_bytes") != manifest.get("file_size_bytes"):
        failures.append("traceability report file_size_bytes does not match manifest")
    if trace.get("required_markers") != marker_report(text, MASTER_PLAN_MARKERS):
        failures.append("traceability report required_markers do not match master plan")
    if trace.get("first_pr_scope") != "schema_only_scaffold_no_runtime":
        failures.append("traceability report first_pr_scope is not schema_only_scaffold_no_runtime")

    checks = trace.get("consistency_checks")
    if not isinstance(checks, dict) or not checks:
        failures.append("traceability report consistency_checks must be a non-empty object")
    elif not all(value is True for value in checks.values()):
        failures.append("traceability report consistency_checks must all be true")

    packet_path = source_packet or _default_source_packet_path(master_plan)
    if not packet_path.exists():
        failures.append(f"source-evidence definitions packet is missing: {packet_path}")
    else:
        packet_text = packet_path.read_text(encoding="utf-8")
        missing_packet_markers = _missing_markers(
            packet_text, SOURCE_EVIDENCE_PACKET_MARKERS
        )
        if missing_packet_markers:
            failures.append(
                "source-evidence definitions packet markers missing: "
                + ", ".join(missing_packet_markers)
            )

    return failures


def raise_for_failures(failures: list[str]) -> None:
    if failures:
        raise SystemExit("traceability check failed:\n- " + "\n- ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-plan", required=True)
    parser.add_argument("--section-manifest", required=True)
    parser.add_argument("--traceability-report", required=True)
    args = parser.parse_args()

    master = pathlib.Path(args.master_plan)
    manifest = _load_json(pathlib.Path(args.section_manifest))
    trace = _load_json(pathlib.Path(args.traceability_report))

    failures = validate_traceability(
        master_plan=master,
        manifest=manifest,
        trace=trace,
        expected_document=args.master_plan,
    )
    raise_for_failures(failures)
    print("TRACEABILITY_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
