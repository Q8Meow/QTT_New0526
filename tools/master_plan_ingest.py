#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import pathlib
import re

HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$', re.MULTILINE)
CANONICAL_ID_RE = re.compile(r'^(?:0X(?:\.[0-9A-Z]+)*|\d+(?:\.\d+[A-Z]*)*)\b')

def extract_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    for match in HEADING_RE.finditer(text):
        level = len(match.group(1))
        title = match.group(2).strip()
        canonical = CANONICAL_ID_RE.match(title)
        sections.append({
            "level": level,
            "title": title,
            "line": text.count("\n", 0, match.start()) + 1,
            "canonical_id": canonical.group(0) if canonical else None,
        })
    return sections

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--section-manifest-out', required=True)
    parser.add_argument('--traceability-out', required=True)
    parser.add_argument('--scope-report-out', required=True)
    args = parser.parse_args()

    master_path = pathlib.Path(args.input)
    text = master_path.read_text(encoding='utf-8')
    sections = extract_sections(text)
    if not sections:
        raise SystemExit('no master-plan headings found')
    if 'v9.9.778' not in text:
        raise SystemExit('master plan is not v9.9.778 currentized content')

    section_manifest = {
        "document": args.input,
        "source": "full_owner_master_plan",
        "sections": sections,
        "section_count": len(sections),
        "line_count": text.count('\n') + 1,
    }
    traceability = {
        "document": args.input,
        "traceability_status": "generated_from_full_owner_master_plan",
        "sections_indexed": len(sections),
        "canonical_ids_indexed": sum(1 for section in sections if section.get('canonical_id')),
        "first_pr_scope": "schema_only_scaffold_no_runtime",
    }
    scope_report = {
        "first_pr_scope": "schema_only_scaffold",
        "allowed_surface": [
            "schemas", "validators", "manifests", "scaffolds", "fail_closed_tests"
        ],
        "blocks": [
            "runtime", "live", "sha", "companion_package", "profit_claims",
            "source_retrieval", "source_acceptance", "connector_binding",
            "private_state_fetch", "order_execution", "neural_training",
            "neural_inference", "external_repo_clone", "package_install_scripts"
        ],
    }
    for out, obj in [
        (args.section_manifest_out, section_manifest),
        (args.traceability_out, traceability),
        (args.scope_report_out, scope_report),
    ]:
        path = pathlib.Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
    print('MASTER_PLAN_INGEST_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
