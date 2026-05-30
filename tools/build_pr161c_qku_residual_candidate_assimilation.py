#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_residual_candidate_assimilation.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    print("PR161C_QKU_RESIDUAL_ASSIMILATION_PREFLIGHT_RECEIPT")
    print(f"primary_qku_source_membership_record_count={artifacts.summary['primary_qku_source_membership_record_count']}")
    print(f"pr161a_field_value_facet_count={artifacts.summary['pr161a_field_value_facet_count']}")
    print(f"expanded_qku_and_field_facet_record_count_if_emitted={artifacts.summary['expanded_qku_and_field_facet_record_count_if_emitted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
