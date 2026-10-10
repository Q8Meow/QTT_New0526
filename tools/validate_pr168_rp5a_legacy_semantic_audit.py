#!/usr/bin/env python3
"""CLI wrapper for PR168-RP5A validation."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5a_validator import run_validation


def main(*, builder_read_context=None) -> int:
    from tools.build_pr168_rp5a_legacy_semantic_audit import _builder_reads_or_current_v1

    with _builder_reads_or_current_v1(builder_read_context) as original:
        print(json.dumps(run_validation(builder_read_context=original), sort_keys=True))
    return 0


def _standalone_main_v1():
    import os
    from tools.validation_reliability import _read_rp5a_bound_launch_fd_v1
    from tools.build_pr168_rp5a_legacy_semantic_audit import (
        _rp5a_reconstruct_reader_v1, _rp5a_bound_reader_v1,
    )
    _, scanner, reader, basis, fence, parent = _read_rp5a_bound_launch_fd_v1(
        sys.stdin.fileno(), repo_root=REPO_ROOT, environment=os.environ.copy(),
        explicit_basetemp=None, original_argv=tuple(sys.orig_argv), expected_role="VALIDATE")
    if scanner is not None or parent is not None:
        raise ValueError("standalone validator requires direct reader-only authority")
    original = _rp5a_reconstruct_reader_v1(reader, basis, fence)
    with _rp5a_bound_reader_v1(original):
        return main(builder_read_context=original)


if __name__ == "__main__":
    raise SystemExit(_standalone_main_v1())
