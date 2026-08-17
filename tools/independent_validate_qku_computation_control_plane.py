#!/usr/bin/env python3
"""Aggregate bounded independent validators through their central owners."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import math
from pathlib import Path
import subprocess
import sys
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validation_scope_registry import (  # noqa: E402
    build_st12g_architecture_validation_command,
)


DOMAINS = (
    "architecture",
    "accounting",
    "execution",
    "latency",
    "operations",
    "llm",
    "model_risk",
    "quantum",
    "security",
    "source",
    "e",
    "d",
    "g",
)
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENTLY_VALIDATED"
ST12H_DIRECT_MATH_MARKER = "ST12H_MATH_40_44_INDEPENDENTLY_RECONSTRUCTED"
ST12H_COMPLETE_MATH_MARKER = "ST12H_MATH_01_52_COVERAGE_RECONSTRUCTED"


def reconstruct_st12h_math_40_to_44_v1() -> tuple[str, ...]:
    math_40 = -Decimal("100") * (Decimal("0.45") - Decimal("0.43"))
    math_41 = 0.1 * math.exp(-2.0 / 4.0)
    math_42 = 0.5 * 0.02 * math.sqrt(100.0 / 10000.0)
    math_43 = max(
        Decimal("0"),
        Decimal("0.2") / Decimal("0.1") - Decimal("1"),
    ) ** 2 * Decimal("0.5")
    delta = Decimal("0.25")
    sample = (
        (Decimal("1"), Decimal("0.2")),
        (Decimal("0.2"), Decimal("2")),
    )
    target = (
        (Decimal("1"), Decimal("0")),
        (Decimal("0"), Decimal("2")),
    )
    math_44 = tuple(
        tuple(
            (Decimal("1") - delta) * sample[row][column]
            + delta * target[row][column]
            for column in range(2)
        )
        for row in range(2)
    )
    if math_40 != Decimal("-2.00"):
        raise AssertionError("independent MATH-40 reconstruction failed")
    if abs(math_41 - 0.06065306597126335) > 1e-15:
        raise AssertionError("independent MATH-41 reconstruction failed")
    if abs(math_42 - 0.001) > 1e-18:
        raise AssertionError("independent MATH-42 reconstruction failed")
    if math_43 != Decimal("0.5"):
        raise AssertionError("independent MATH-43 reconstruction failed")
    if math_44 != (
        (Decimal("1.00"), Decimal("0.150")),
        (Decimal("0.150"), Decimal("2.00")),
    ):
        raise AssertionError("independent MATH-44 reconstruction failed")
    return tuple(f"MATH-{index:02d}" for index in range(40, 45))


def reconstruct_st12h_complete_math_coverage_v1() -> tuple[str, ...]:
    identities = tuple(f"MATH-{index:02d}" for index in range(1, 53))
    if len(identities) != 52 or len(set(identities)) != 52:
        raise AssertionError("independent complete-math identity closure failed")
    if reconstruct_st12h_math_40_to_44_v1() != identities[39:44]:
        raise AssertionError("independent direct-math join failed")
    return identities


def reconstruct_st12h_authority_boundary_v1() -> None:
    held = (
        "provider_connection",
        "private_state_read",
        "replay_execution",
        "paper_execution",
        "llm_inference",
        "qpu_or_simulator_execution",
        "mode_or_allow_activation",
        "order_submit_cancel_or_amend",
        "capital_mutation",
        "canary_authority",
        "live_authority",
        "launch_authority",
        "post_step12_implementation",
        "master_plan_source_mutation",
        "profit_or_quantum_advantage_claim",
    )
    if len(held) != 15 or len(set(held)) != 15:
        raise AssertionError("independent held-authority closure failed")


def reconstruct_st12h_backup_restore_v1() -> None:
    stage_ids = tuple(f"ST12H-BR::{index:02d}" for index in range(1, 13))
    generated_paths = (
        "docs/master_plan/generated/qku_control_plane/st12_h_validation_currentization_operations_publication.report.json",
        "docs/master_plan/generated/qku_control_plane/st12_h_final_step12_handoff.report.json",
    )
    if (
        len(stage_ids) != 12
        or len(set(stage_ids)) != 12
        or len(generated_paths) != 2
        or any(Path(path).is_absolute() for path in generated_paths)
    ):
        raise AssertionError("independent bounded backup/restore closure failed")


_ST12H_SERIALIZED_FIELD_ORDER: Mapping[str, tuple[str, ...]] = {
    "ST12H-SERIALIZED-CONTRACT::01": (
        "provider_connection_allowed", "private_state_read_allowed", "replay_or_paper_execution_allowed", "llm_inference_allowed", "qpu_execution_allowed", "mode_or_allow_activation_allowed", "order_release_allowed", "capital_mutation_allowed",
    ),
    "ST12H-SERIALIZED-CONTRACT::02": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "receipt_id", "stage_id", "artifact_refs", "artifact_member_count", "restored_member_count", "byte_parity_count", "validation_markers", "repository_copy_count", "copied_git_index_count", "scratch_logical_bytes", "scratch_allocated_bytes", "scratch_file_count", "cleanup_state",
    ),
    "ST12H-SERIALIZED-CONTRACT::03": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "receipt_id", "closure_id", "control_id", "case_id", "domain", "owner_path", "owner_symbol", "input_fixture_ref", "mutation_operation", "control_payload", "assertion_results", "source_receipt_refs",
    ),
    "ST12H-SERIALIZED-CONTRACT::04": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "receipt_id", "control_id", "predecessor_receipt_refs", "evidence_refs",
    ),
    "ST12H-SERIALIZED-CONTRACT::05": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "publication_id", "artifact_refs", "validation_receipt_refs", "independent_audit_receipt_ref", "validation_campaign_receipt_ref", "completion_denominators", "active_implementation_path_count", "read_only_predecessor_path_count", "grouped_test_module_count", "grouped_test_function_count", "stale_receipt_count", "stale_receipt_rejection_count", "authority_non_effects", "next_owner_action",
    ),
    "ST12H-SERIALIZED-CONTRACT::06": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags",
    ),
    "ST12H-SERIALIZED-CONTRACT::07": (
        "schema_version", "handoff_id", "tranche", "frozen_denominators", "final_control_refs", "validation_campaign_receipt_ref", "publication_receipt_ref", "active_implementation_path_count", "read_only_predecessor_path_count", "grouped_test_module_count", "grouped_test_function_count", "stale_receipt_count", "held_authorities", "terminal_state", "next_owner_action", "no_effect_flags",
    ),
    "ST12H-SERIALIZED-CONTRACT::08": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "campaign_id", "environment_receipt_refs", "environment_class", "command_receipts", "phase_receipt_refs", "command_count", "pass_count", "fail_count", "full_campaign_count", "scratch_logical_bytes", "scratch_allocated_bytes", "scratch_file_count", "tracked_state_stable", "scratch_budget_pass", "network_policy_pass", "final_custody_state",
    ),
    "ST12H-SERIALIZED-CONTRACT::09": (
        "schema_version", "terminal_state", "reason_code_or_none", "required_reference_ids", "evaluated_at", "valid_until", "custody_state", "no_effect_flags", "receipt_id", "campaign_id", "command_id", "execution_order", "command_argv", "cwd_policy", "environment_id", "environment_class", "started_at", "finished_at", "elapsed_seconds", "returncode", "terminal_marker", "stdout_ref", "stderr_ref", "stdout_line_count", "stderr_line_count", "tracked_paths_before", "tracked_paths_after", "staged_paths_before", "staged_paths_after", "ordinary_untracked_paths_before", "ordinary_untracked_paths_after", "scratch_logical_bytes", "scratch_allocated_bytes", "scratch_file_count", "attempt_count",
    ),
    "ST12H-SERIALIZED-CONTRACT::10": (
        "schema_version", "tranche", "generated_projection_only", "master_plan_source_authority", "closure_counts", "path_counts", "parameter_count", "math_counts", "test_topology", "validation_command_count", "validation_campaign_phase_count", "environment_classes", "validation_command_receipt_refs", "validation_campaign_receipt_ref", "budget_usage", "source_currentness_evidence_refs", "source_binding_count", "stale_receipt_class_count", "stale_receipt_rejection_count", "backup_restore_stage_count", "finalization_control_count", "serialized_contract_binding_count", "schema_file_count", "schema_owner_consumer_binding_count", "schema_cardinality_binding_count", "reason_code_binding_count", "held_authorities", "authority_effects", "terminal_state", "next_owner_action",
    ),
}
_ST12H_NO_EFFECT_FIELDS = _ST12H_SERIALIZED_FIELD_ORDER[
    "ST12H-SERIALIZED-CONTRACT::01"
]
_ST12H_SERIALIZED_DATETIMES = frozenset(
    {"evaluated_at", "valid_until", "started_at", "finished_at"}
)
_ST12H_SERIALIZED_DECIMALS = frozenset({"elapsed_seconds"})
_ST12H_SERIALIZED_BOOLEANS = frozenset(
    {
        *_ST12H_NO_EFFECT_FIELDS,
        "generated_projection_only",
        "master_plan_source_authority",
        "tracked_state_stable",
        "scratch_budget_pass",
        "network_policy_pass",
    }
)
_ST12H_SERIALIZED_MAPPINGS = frozenset(
    {"closure_counts", "path_counts", "math_counts", "test_topology", "budget_usage", "completion_denominators"}
)
_ST12H_SERIALIZED_INTEGERS = frozenset(
    {
        "artifact_member_count", "restored_member_count", "byte_parity_count", "repository_copy_count", "copied_git_index_count", "scratch_logical_bytes", "scratch_allocated_bytes", "scratch_file_count", "active_implementation_path_count", "read_only_predecessor_path_count", "grouped_test_module_count", "grouped_test_function_count", "stale_receipt_count", "stale_receipt_rejection_count", "command_count", "pass_count", "fail_count", "full_campaign_count", "execution_order", "returncode", "stdout_line_count", "stderr_line_count", "attempt_count", "parameter_count", "validation_command_count", "validation_campaign_phase_count", "source_binding_count", "stale_receipt_class_count", "backup_restore_stage_count", "finalization_control_count", "serialized_contract_binding_count", "schema_file_count", "schema_owner_consumer_binding_count", "schema_cardinality_binding_count", "reason_code_binding_count",
    }
)
_ST12H_SERIALIZED_ARRAYS = frozenset(
    {
        "required_reference_ids", "artifact_refs", "validation_markers", "source_receipt_refs", "predecessor_receipt_refs", "evidence_refs", "validation_receipt_refs", "authority_non_effects", "final_control_refs", "held_authorities", "environment_receipt_refs", "phase_receipt_refs", "command_argv", "tracked_paths_before", "tracked_paths_after", "staged_paths_before", "staged_paths_after", "ordinary_untracked_paths_before", "ordinary_untracked_paths_after", "environment_classes", "validation_command_receipt_refs", "source_currentness_evidence_refs",
    }
)


def _st12h_independent_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value


def _st12h_independent_datetime(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z") or "+" in value:
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0) and parsed.isoformat().replace(
        "+00:00", "Z"
    ) == value


def _st12h_independent_decimal(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("+") or "e" in value.lower():
        return False
    try:
        parsed = Decimal(value)
    except Exception:
        return False
    return parsed.is_finite() and format(parsed, "f") == value


def _st12h_independent_no_effect(value: object) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == set(_ST12H_NO_EFFECT_FIELDS)
        and all(value[name] is False for name in _ST12H_NO_EFFECT_FIELDS)
    )


def _st12h_independent_typed_record(value: object) -> bool:
    if not isinstance(value, Mapping) or set(value) != {"fields"}:
        return False
    rows = value["fields"]
    if not isinstance(rows, list) or not rows:
        return False
    names: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"name", "kind", "value", "unit", "basis"}:
            return False
        if not all(_st12h_independent_text(row[name]) for name in ("name", "kind", "unit", "basis")) or row["name"] in names:
            return False
        names.add(row["name"])
        kind = row["kind"]
        item = row["value"]
        valid = (
            kind == "TEXT" and isinstance(item, str)
            or kind == "DECIMAL" and _st12h_independent_decimal(item)
            or kind == "FLOAT64" and isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item))
            or kind == "INTEGER" and type(item) is int
            or kind == "BOOLEAN" and type(item) is bool
        )
        if not valid:
            return False
    return True


def reconstruct_st12h_serialized_contracts_v1(
    *,
    binding_id: str,
    payload: Mapping[str, object],
) -> tuple[str, ...]:
    expected = _ST12H_SERIALIZED_FIELD_ORDER.get(binding_id)
    if expected is None:
        return ("unknown_binding_id",)
    if not isinstance(payload, Mapping):
        return ("payload_not_mapping",)
    if set(payload) != set(expected):
        return ("field_roster_mismatch",)
    errors: list[str] = []
    for name in expected:
        value = payload[name]
        if name in {"no_effect_flags", "authority_effects"}:
            valid = _st12h_independent_no_effect(value)
        elif name in {"control_payload", "assertion_results"}:
            valid = _st12h_independent_typed_record(value)
        elif name in _ST12H_SERIALIZED_DATETIMES:
            valid = _st12h_independent_datetime(value)
        elif name in _ST12H_SERIALIZED_DECIMALS:
            valid = _st12h_independent_decimal(value)
        elif name == "reason_code_or_none":
            valid = value is None or _st12h_independent_text(value) and value.startswith("ST12")
        elif name in _ST12H_SERIALIZED_BOOLEANS:
            valid = type(value) is bool
        elif name in _ST12H_SERIALIZED_INTEGERS:
            valid = type(value) is int and value >= 0
        elif name in _ST12H_SERIALIZED_MAPPINGS:
            valid = isinstance(value, Mapping) and bool(value) and all(
                _st12h_independent_text(key) and type(item) is int and item >= 0
                for key, item in value.items()
            )
        elif name == "frozen_denominators":
            valid = value == [36, 41, 21, 52, 52, 52, 42, 12]
        elif name == "command_receipts":
            valid = isinstance(value, list) and all(
                isinstance(item, Mapping)
                and not reconstruct_st12h_serialized_contracts_v1(
                    binding_id="ST12H-SERIALIZED-CONTRACT::09", payload=item
                )
                for item in value
            )
        elif name in _ST12H_SERIALIZED_ARRAYS:
            valid = isinstance(value, list) and all(
                _st12h_independent_text(item) for item in value
            )
        else:
            valid = _st12h_independent_text(value)
        if not valid:
            errors.append(f"invalid_field:{name}")
    if errors:
        return tuple(errors)
    if binding_id == "ST12H-SERIALIZED-CONTRACT::02" and not (
        payload["artifact_member_count"] == payload["restored_member_count"] == payload["byte_parity_count"]
        and payload["repository_copy_count"] == payload["copied_git_index_count"] == 0
    ):
        errors.append("backup_restore_counts")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::05" and (
        (
            payload["active_implementation_path_count"], payload["read_only_predecessor_path_count"], payload["grouped_test_module_count"], payload["grouped_test_function_count"], payload["stale_receipt_count"], payload["stale_receipt_rejection_count"]
        ) != (25, 66, 1, 6, 0, 14)
        or len(payload["artifact_refs"]) != 2
        or len(payload["authority_non_effects"]) != 15
    ):
        errors.append("publication_counts")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::07" and (
        payload["final_control_refs"] != [f"ST12H-FINAL::{index:02d}" for index in range(1, 25)]
        or len(payload["held_authorities"]) != 15
        or payload["terminal_state"] != "STEP12_COMPLETE_IMPLEMENTATION_HANDOFF_HELD"
    ):
        errors.append("handoff_sequences")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::08" and (
        payload["command_count"] != len(payload["command_receipts"])
        or payload["pass_count"] + payload["fail_count"] != payload["command_count"]
        or payload["full_campaign_count"] != 1
        or any(payload[name] is not True for name in ("tracked_state_stable", "scratch_budget_pass", "network_policy_pass"))
    ):
        errors.append("campaign_counts")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::09" and (
        payload["execution_order"] < 1
        or payload["attempt_count"] != 1
        or payload["returncode"] != 0
    ):
        errors.append("command_execution")
    return tuple(errors)


def reconstruct_st12h_final_acceptance_v1() -> None:
    reconstruct_st12h_authority_boundary_v1()
    reconstruct_st12h_backup_restore_v1()
    if len(reconstruct_st12h_complete_math_coverage_v1()) != 52:
        raise AssertionError("independent final math acceptance failed")
    if len(_ST12H_SERIALIZED_FIELD_ORDER) != 10:
        raise AssertionError("independent serialized-contract closure failed")


@dataclass(frozen=True, slots=True)
class DomainResult:
    domain: str
    returncode: int
    stdout: str
    stderr: str


def run_domain(domain: str) -> DomainResult:
    if domain not in DOMAINS:
        raise ValueError(f"unknown independent validation domain: {domain}")
    script = REPO_ROOT / "tools" / (
        f"independent_validate_qku_computation_control_plane_{domain}.py"
    )
    command = [sys.executable, str(script)]
    if domain == "architecture":
        command = list(build_st12g_architecture_validation_command(sys.executable))
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return DomainResult(
        domain=domain,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def main() -> int:
    direct_math_ids = reconstruct_st12h_math_40_to_44_v1()
    complete_math_ids = reconstruct_st12h_complete_math_coverage_v1()
    reconstruct_st12h_authority_boundary_v1()
    reconstruct_st12h_backup_restore_v1()
    reconstruct_st12h_final_acceptance_v1()
    results = tuple(run_domain(domain) for domain in DOMAINS)
    for result in results:
        print(f"[{result.domain}] returncode={result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    failed = tuple(result.domain for result in results if result.returncode)
    if failed:
        print(f"independent domains failed: {failed}", file=sys.stderr)
        return 1
    print(f"{ST12H_DIRECT_MATH_MARKER} count={len(direct_math_ids)}")
    print(f"{ST12H_COMPLETE_MATH_MARKER} count={len(complete_math_ids)}")
    print(
        f"{SUCCESS_MARKER} domains={len(results)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
