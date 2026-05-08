#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib
import re

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
CANONICAL_ID_RE = re.compile(
    r"^(?P<canonical_id>(?:0X|[0-9]+[A-Z0-9]*)(?:\.[0-9A-Z]+)*)(?=$|[\s:`\-\u2013\u2014])"
)

MASTER_PLAN_MARKERS = {
    "active_repository": "owner_declared_active_codex_repository_url = https://github.com/Q8Meow/QTT_New0526",
    "codex_handoff_readiness": (
        "codex_handoff_readiness_state = "
        "OWNER_START_READY_FOR_EXACT_FIRST_PR_SCHEMA_ONLY_SCOPE_AFTER_OWNER_COMMAND"
    ),
    "codex_ready_authority_class": (
        "document_authority_class = CODEX_READY_WORKING_DRAFT_CANDIDATE_NOT_REPO_AUTHORITATIVE"
    ),
    "final_no_edit_audit_passed": (
        "final_no_edit_owner_start_readiness_audit_result = "
        "PASSED_FOR_EXACT_FIRST_PR_SCHEMA_ONLY_SCOPE"
    ),
    "owner_start_ready_notice": "OWNER-START READY FOR EXACT FIRST-PR SCHEMA-ONLY SCOPE",
    "working_draft_edition": "working_draft_edition = v9.9.778",
}

SCOPE_BLOCKS = [
    "runtime",
    "live",
    "sha",
    "companion_package",
    "profit_claims",
    "source_retrieval",
    "source_acceptance",
    "connector_binding",
    "private_state_fetch",
    "order_execution",
    "neural_training",
    "neural_inference",
    "external_repo_clone",
    "package_install_scripts",
]


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def normalize_heading_title(raw_title: str) -> str:
    title = raw_title.strip()
    if title.endswith("#"):
        title = re.sub(r"\s+#+\s*$", "", title).strip()
    return title


def extract_canonical_id(title: str) -> str | None:
    canonical = CANONICAL_ID_RE.match(title)
    return canonical.group("canonical_id") if canonical else None


def extract_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    heading_stack: list[dict[str, object]] = []
    in_fence = False
    char_offset = 0

    for line_number, raw_line in enumerate(text.splitlines(keepends=True), start=1):
        line = raw_line.rstrip("\r\n")
        if FENCE_RE.match(line):
            in_fence = not in_fence
            char_offset += len(raw_line)
            continue

        match = None if in_fence else HEADING_RE.match(line)
        if not match:
            char_offset += len(raw_line)
            continue

        level = len(match.group(1))
        title = normalize_heading_title(match.group(2))
        canonical_id = extract_canonical_id(title)

        while heading_stack and int(heading_stack[-1]["level"]) >= level:
            heading_stack.pop()
        parent = heading_stack[-1] if heading_stack else None

        section = {
            "index": len(sections) + 1,
            "level": level,
            "title": title,
            "line": line_number,
            "char_offset": char_offset,
            "canonical_id": canonical_id,
            "parent_index": parent["index"] if parent else None,
            "parent_canonical_id": parent.get("canonical_id") if parent else None,
        }
        sections.append(
            {
                key: section[key]
                for key in [
                    "index",
                    "level",
                    "title",
                    "line",
                    "char_offset",
                    "canonical_id",
                    "parent_index",
                    "parent_canonical_id",
                ]
            }
        )
        heading_stack.append(section)
        char_offset += len(raw_line)
    return sections


def marker_report(text: str, markers: dict[str, str]) -> dict[str, bool]:
    return {name: marker in text for name, marker in sorted(markers.items())}


def duplicate_canonical_ids(sections: list[dict[str, object]]) -> list[str]:
    counts = Counter(
        section["canonical_id"]
        for section in sections
        if isinstance(section.get("canonical_id"), str)
    )
    return sorted(str(canonical_id) for canonical_id, count in counts.items() if count > 1)


def build_section_manifest(
    document: str, text: str, file_size_bytes: int | None = None
) -> dict[str, object]:
    sections = extract_sections(text)
    canonical_ids = [
        section["canonical_id"]
        for section in sections
        if isinstance(section.get("canonical_id"), str)
    ]
    return {
        "document": pathlib.Path(document).as_posix(),
        "source": "full_owner_master_plan",
        "schema_version": 2,
        "parser": "tools/master_plan_ingest.py",
        "deterministic_output": True,
        "sections": sections,
        "section_count": len(sections),
        "canonical_id_count": len(canonical_ids),
        "unique_canonical_id_count": len(set(canonical_ids)),
        "duplicate_canonical_ids": duplicate_canonical_ids(sections),
        "line_count": line_count(text),
        "char_count": len(text),
        "file_size_bytes": file_size_bytes
        if file_size_bytes is not None
        else len(text.encode("utf-8")),
        "required_markers": marker_report(text, MASTER_PLAN_MARKERS),
    }


def build_traceability_report(
    document: str, manifest: dict[str, object], text: str
) -> dict[str, object]:
    sections = manifest["sections"]
    assert isinstance(sections, list)
    canonical_id_count = int(manifest["canonical_id_count"])
    required_markers = marker_report(text, MASTER_PLAN_MARKERS)
    required_markers_present = all(required_markers.values())
    return {
        "document": pathlib.Path(document).as_posix(),
        "traceability_status": (
            "generated_from_full_owner_master_plan"
            if required_markers_present
            else "generated_with_missing_required_markers"
        ),
        "schema_version": 2,
        "section_manifest_schema_version": manifest["schema_version"],
        "sections_indexed": len(sections),
        "canonical_ids_indexed": canonical_id_count,
        "unique_canonical_ids_indexed": int(manifest["unique_canonical_id_count"]),
        "duplicate_canonical_ids": manifest["duplicate_canonical_ids"],
        "line_count": manifest["line_count"],
        "file_size_bytes": manifest["file_size_bytes"],
        "first_pr_scope": "schema_only_scaffold_no_runtime",
        "required_markers": required_markers,
        "consistency_checks": {
            "section_count_matches_manifest": len(sections) == manifest["section_count"],
            "canonical_id_count_matches_manifest": canonical_id_count
            == sum(1 for section in sections if section.get("canonical_id")),
            "line_count_matches_manifest": manifest["line_count"] == line_count(text),
            "required_master_plan_markers_present": required_markers_present,
        },
    }


def build_scope_report() -> dict[str, object]:
    return {
        "first_pr_scope": "schema_only_scaffold",
        "allowed_surface": [
            "schemas",
            "validators",
            "manifests",
            "scaffolds",
            "fail_closed_tests",
        ],
        "blocks": SCOPE_BLOCKS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--section-manifest-out", required=True)
    parser.add_argument("--traceability-out", required=True)
    parser.add_argument("--scope-report-out", required=True)
    args = parser.parse_args()

    master_path = pathlib.Path(args.input)
    text = master_path.read_text(encoding="utf-8")
    section_manifest = build_section_manifest(
        args.input, text, file_size_bytes=master_path.stat().st_size
    )
    if not section_manifest["sections"]:
        raise SystemExit("no master-plan headings found")
    if not all(section_manifest["required_markers"].values()):
        missing = [
            name
            for name, present in section_manifest["required_markers"].items()
            if not present
        ]
        raise SystemExit(f"master plan required markers missing: {', '.join(missing)}")

    traceability = build_traceability_report(args.input, section_manifest, text)
    scope_report = build_scope_report()
    for out, obj in [
        (args.section_manifest_out, section_manifest),
        (args.traceability_out, traceability),
        (args.scope_report_out, scope_report),
    ]:
        path = pathlib.Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print("MASTER_PLAN_INGEST_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
