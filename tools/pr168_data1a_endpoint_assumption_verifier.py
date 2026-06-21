#!/usr/bin/env python3
"""Endpoint assumption drift verifier for PR168-DATA1A."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from tools.pr168_data1a_config import OFFICIAL_DOC_URLS, route_defaults


def _verify_url(url: str, timeout: int = 12) -> dict[str, Any]:
    curl = shutil.which("curl")
    if curl is None:
        return {"http_status": None, "reachable_flag": False, "content_sample_bytes": 0, "error": "CURL_NOT_AVAILABLE"}
    try:
        result = subprocess.run(
            [
                curl,
                "--location",
                "--max-time",
                str(timeout),
                "--user-agent",
                "QTT-PR168-DATA1A-doc-assumption-verifier",
                "--silent",
                "--show-error",
                "--output",
                "-",
                "--write-out",
                "\nPR168_DATA1A_HTTP_STATUS:%{http_code}",
                url,
            ],
            check=False,
            capture_output=True,
            timeout=timeout + 5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"http_status": None, "reachable_flag": False, "content_sample_bytes": 0, "error": type(exc).__name__}
    marker = b"\nPR168_DATA1A_HTTP_STATUS:"
    body, marker_found, status_text = result.stdout.rpartition(marker)
    status = None
    if marker_found:
        try:
            status = int(status_text.strip()[:3])
        except ValueError:
            status = None
    error = None
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        error = stderr[:160] or f"CURL_EXIT_{result.returncode}"
    return {
        "http_status": status,
        "reachable_flag": status is not None and 200 <= status < 400,
        "content_sample_bytes": min(len(body), 2048),
        "error": error,
    }


def verify_endpoint_assumptions(created_at_utc: str, *, online: bool) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    rows: list[dict[str, Any]] = []
    for index, url in enumerate(OFFICIAL_DOC_URLS, start=1):
        if online:
            result = _verify_url(url)
            verification_state = "ONLINE_DOC_REACHABLE" if result["reachable_flag"] else "ONLINE_DOC_UNREACHABLE"
            drift_state = "NO_DATA1_SNAPSHOT_MUTATION_DOC_RECHECK_ONLY" if result["reachable_flag"] else "NETWORK_OR_DOC_REACHABILITY_GAP"
        else:
            result = {"http_status": None, "reachable_flag": False, "content_sample_bytes": 0, "error": "OFFLINE_MODE"}
            verification_state = "OFFLINE_NOT_VERIFIED"
            drift_state = "NOT_EVALUATED_OFFLINE"
        rows.append(
            {
                "endpoint_assumption_row_id": f"endpoint_assumption_{index:05d}",
                "source_url": url,
                "verification_mode": "online" if online else "offline",
                "verification_state": verification_state,
                "drift_state": drift_state,
                "http_status": result["http_status"],
                "reachable_flag": result["reachable_flag"],
                "content_sample_bytes": result["content_sample_bytes"],
                "error": result["error"],
                "snapshot_mutation_allowed_flag": False,
                "follow_up_route_if_drift": "DATA1B_ENDPOINT_REVIEW" if drift_state != "NO_DATA1_SNAPSHOT_MUTATION_DOC_RECHECK_ONLY" else None,
                "created_at_utc": created_at_utc,
                **route_defaults("source_evidence", provenance_refs=[url]),
            }
        )
    unreachable = [row for row in rows if not row["reachable_flag"]]
    summary = {
        "online_verification_requested_flag": online,
        "endpoint_assumption_row_count": len(rows),
        "endpoint_assumption_reachable_count": len(rows) - len(unreachable),
        "endpoint_assumption_unreachable_count": len(unreachable),
        "endpoint_assumption_drift_count": len([row for row in rows if row["drift_state"] == "NETWORK_OR_DOC_REACHABILITY_GAP"]),
        "DATA1_snapshot_mutation_count": 0,
        "DATA1B_follow_up_required_count": len([row for row in rows if row["follow_up_route_if_drift"]]),
        **route_defaults("source_evidence", provenance_refs=OFFICIAL_DOC_URLS),
    }
    network_receipt = None
    if online and len(unreachable) == len(rows):
        network_receipt = {
            "receipt_id": "pr168_data1a_online_verification_network_unavailable",
            "unreachable_count": len(unreachable),
            "reason": "all official doc checks failed; offline DATA1 audit remains valid",
            **route_defaults(
                "source_evidence",
                provenance_refs=OFFICIAL_DOC_URLS,
                terminal_by_nature_flag=True,
                terminal_reason_code="ONLINE_VERIFICATION_NETWORK_UNAVAILABLE",
            ),
        }
    return summary, rows, network_receipt
