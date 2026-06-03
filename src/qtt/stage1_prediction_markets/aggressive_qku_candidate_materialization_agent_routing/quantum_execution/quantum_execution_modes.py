"""PR162D quantum execution mode registry."""

from __future__ import annotations

from .. import constants as c


def quantum_execution_mode_records() -> list[dict[str, object]]:
    allowed = [
        {
            "quantum_execution_mode": mode,
            "allowed_in_pr162d_flag": True,
            "ci_allowed_flag": mode
            in {
                "QUANTUM_DESCRIPTOR_ONLY",
                "QUANTUM_LOCAL_EXACT_SMOKE",
                "QUANTUM_LOCAL_SIMULATOR_IF_AVAILABLE",
                "QUANTUM_PROVIDER_DRY_RUN",
            },
            "remote_execution_required_for_ci_flag": False,
            "live_order_authority": False,
        }
        for mode in c.QUANTUM_EXECUTION_MODES
    ]
    forbidden = [
        {
            "quantum_execution_mode": mode,
            "allowed_in_pr162d_flag": False,
            "ci_allowed_flag": False,
            "remote_execution_required_for_ci_flag": False,
            "live_order_authority": False,
        }
        for mode in c.FORBIDDEN_QUANTUM_MODES
    ]
    return allowed + forbidden
