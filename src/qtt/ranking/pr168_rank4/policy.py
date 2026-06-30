"""Policy parameter helpers for PR168-RANK4."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import PARAM_DEFAULTS, dec


def policy_value(name: str) -> Decimal:
    return dec(PARAM_DEFAULTS[name])


def policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "parameter_name": key,
            "parameter_value": str(value),
            "policy_source": "RANK4_BOOTSTRAP_DEFAULT_IF_NO_STRONGER_REPO_POLICY_PRESENT",
            "candidate_only_flag": True,
            "live_default_flag": False,
            "profit_proof_flag": False,
            "replay_paper_verification_required": True,
        }
        for key, value in sorted(PARAM_DEFAULTS.items())
    ]

