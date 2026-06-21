#!/usr/bin/env python3
"""Deterministic small backoff helpers for PR168-DATA1 public probes."""

from __future__ import annotations

import time

from tools.pr168_data1_config import BACKOFF_SECONDS_DEFAULT


def deterministic_sleep(attempt: int = 0) -> None:
    """Sleep for a bounded deterministic interval between public read-only calls."""

    delay = min(BACKOFF_SECONDS_DEFAULT * (attempt + 1), 1.0)
    time.sleep(delay)
