"""PR161F policy accessors derived from central constants."""

from __future__ import annotations

from . import constants as c


def authority_flags() -> dict[str, bool]:
    return {
        "no_live_connector_used_flag": True,
        "no_private_state_used_flag": True,
        "no_order_execution_flag": True,
        "no_profit_evidence_created_flag": True,
        "no_live_authority_created_flag": True,
        "no_optimizer_execution_created_flag": True,
        "no_quantum_backend_execution_created_flag": True,
        "no_quantum_simulator_execution_created_flag": True,
        "no_qtt_sha_authority_created_flag": True,
        "no_qtt_generated_sha_authority_created_flag": True,
        "no_qtt_freeze_checksum_global_digest_authority_created_flag": True,
        "no_atomicrows_bundle_sha_authority_created_flag": True,
        "no_atomicrows_bundle_hash_freeze_authority_created_flag": True,
    }


def owner_approval_flags() -> dict[str, bool]:
    return dict(c.OWNER_APPROVALS)


def no_authority_confirmation() -> dict[str, bool]:
    return dict(c.NO_AUTHORITY_CONFIRMATION)

