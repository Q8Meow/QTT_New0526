"""Provider dry-run adapter."""

from __future__ import annotations

from typing import Any

from .backend_adapter_base import BackendAdapter


def provider_dry_run_payload(provider: str, problem: dict[str, Any]) -> dict[str, Any]:
    adapter = BackendAdapter(
        f"PR162D-{provider.upper()}-DRY-RUN-ADAPTER",
        "PROVIDER_DRY_RUN_PAYLOAD_ONLY",
    )
    payload = adapter.build_payload(problem)
    payload["provider"] = provider
    payload["provider_submission_status"] = "DRY_RUN_PAYLOAD_BUILT_NO_REMOTE_SUBMISSION"
    return payload
