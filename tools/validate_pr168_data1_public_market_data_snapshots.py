#!/usr/bin/env python3
"""Thin offline validator wrapper for PR168-DATA1 artifacts."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_data1_validator import run_validation


if __name__ == "__main__":
    run_validation("offline_cli")
