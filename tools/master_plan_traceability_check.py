#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--master-plan', required=True)
    parser.add_argument('--section-manifest', required=True)
    parser.add_argument('--traceability-report', required=True)
    args = parser.parse_args()

    master = pathlib.Path(args.master_plan)
    manifest = json.loads(pathlib.Path(args.section_manifest).read_text(encoding='utf-8'))
    trace = json.loads(pathlib.Path(args.traceability_report).read_text(encoding='utf-8'))
    text = master.read_text(encoding='utf-8')

    if manifest.get('document') != args.master_plan or trace.get('document') != args.master_plan:
        raise SystemExit('traceability mismatch')
    if manifest.get('line_count', 0) < 100000:
        raise SystemExit('master-plan line count is too small; expected full owner file')
    if 'v9.9.778' not in text or 'OWNER-START READY FOR EXACT FIRST-PR SCHEMA-ONLY SCOPE' not in text:
        raise SystemExit('master-plan currentization markers missing')
    print('TRACEABILITY_GATE_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
