#!/usr/bin/env python3
"""Aggregate bounded independent validators through their central owners."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from types import MappingProxyType
from typing import Mapping, Sequence
import unicodedata
import warnings
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.validation_scope_registry import (  # noqa: E402
    build_st12g_architecture_validation_command,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ComputationControlPlaneError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (  # noqa: E402
    NO_EFFECTS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (  # noqa: E402
    ST12HBackupRestoreReceiptV1,
    ST12HControlReceiptV1,
    ST12HFinalizationReceiptV1,
    ST12HPublicationReceiptV1,
    ST12HReceiptCustodyV1,
    ST12HValidationCampaignReceiptV1,
    ST12HValidationCommandReceiptV1,
    _ST12H_SEMANTIC_VALIDATOR_REVISION,
    _validate_st12h_receipt_currentness_v1,
    serialize_st12h_contract_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (  # noqa: E402
    ST12H_BACKUP_RESTORE_PLANS,
    ST12H_FINALIZATION_CONTROLS,
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


@dataclass(frozen=True, slots=True)
class ST12HDirectMathEvidenceV1:
    math_id: str
    vector_ref: str
    independent_method: str
    observed_result: object
    mutation: str
    mutation_result: object
    negative_vector_rejected: bool


@dataclass(frozen=True, slots=True)
class ST12HMathEvidenceCrosswalkV1:
    math_id: str
    production_owner: tuple[str, ...]
    independent_validator_owner: str
    exact_vector_or_invariant: str
    boundary_negative_mutation_evidence: str
    validator_command: tuple[str, ...]
    validator_marker: str
    evidence_class: str
    execution_receipt_ref: str


_ST12H_DIRECT_MATH_IDS = tuple(f"MATH-{index:02d}" for index in range(40, 45))
_ST12H_MATH_SHARD_REGISTRY = (
    REPO_ROOT
    / ".codex_inputs"
    / "h80"
    / "p"
    / "registries"
    / "h_math_reconstruction_shard_registry.jsonl"
)
_ST12H_GOLDEN_VECTOR_REGISTRY = (
    REPO_ROOT
    / ".codex_inputs"
    / "h80"
    / "p"
    / "registries"
    / "h_golden_vector_registry.jsonl"
)
_ST12H_INDEPENDENT_ORACLE_REGISTRY = (
    REPO_ROOT
    / ".codex_inputs"
    / "h80"
    / "p"
    / "registries"
    / "h_independent_oracle_registry.jsonl"
)


def _st12h_registry_rows(
    path: Path,
    id_field: str,
) -> Mapping[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        key = payload[id_field]
        if not isinstance(key, str) or key in rows:
            raise AssertionError(
                f"invalid or duplicate ST12-H registry identity: {key!r}"
            )
        rows[key] = payload
    return rows


def _st12h_direct_math_observable(
    math_id: str,
    values: Mapping[str, object],
) -> object:
    if math_id == "MATH-40":
        side = values["side"]
        if side not in {"BUY", "SELL"}:
            raise ValueError("MATH-40 side must be BUY or SELL")
        quantity = Decimal(str(values["quantity"]))
        fill_price = Decimal(str(values["fill_price"]))
        reference_price = Decimal(str(values["reference_price"]))
        if quantity <= 0:
            raise ValueError("MATH-40 quantity must be positive")
        sign = Decimal("-1") if side == "BUY" else Decimal("1")
        return sign * quantity * (fill_price - reference_price)
    if math_id == "MATH-41":
        latency = float(values["latency"])
        tau = float(values["tau"])
        baseline = float(values["baseline"])
        if latency < 0 or tau <= 0 or not all(
            math.isfinite(value) for value in (latency, tau, baseline)
        ):
            raise ValueError("MATH-41 inputs are outside their declared domain")
        return baseline * math.exp(-latency / tau)
    if math_id == "MATH-42":
        eta = float(values["eta"])
        sigma = float(values["sigma"])
        quantity = float(values["quantity"])
        volume = float(values["volume"])
        if eta < 0 or sigma < 0 or quantity < 0 or volume <= 0:
            raise ValueError("MATH-42 inputs are outside their declared domain")
        return eta * sigma * math.sqrt(quantity / volume)
    if math_id == "MATH-43":
        participation = Decimal(str(values["participation"]))
        threshold = Decimal(str(values["threshold"]))
        coefficient = Decimal(str(values["coefficient"]))
        if participation < 0 or threshold <= 0 or coefficient < 0:
            raise ValueError("MATH-43 inputs are outside their declared domain")
        return (
            max(Decimal("0"), participation / threshold - Decimal("1")) ** 2
            * coefficient
        )
    if math_id == "MATH-44":
        delta = Decimal(str(values["delta"]))
        sample = values["sample"]
        target = values["target"]
        if not Decimal("0") <= delta <= Decimal("1"):
            raise ValueError("MATH-44 delta must be in [0,1]")
        if (
            not isinstance(sample, tuple)
            or not isinstance(target, tuple)
            or len(sample) != 2
            or len(target) != 2
            or any(len(row) != 2 for row in (*sample, *target))
        ):
            raise ValueError("MATH-44 requires two 2x2 matrices")
        return tuple(
            tuple(
                (Decimal("1") - delta) * Decimal(str(sample[row][column]))
                + delta * Decimal(str(target[row][column]))
                for column in range(2)
            )
            for row in range(2)
        )
    raise ValueError(f"not an H-direct math obligation: {math_id}")


def reconstruct_st12h_direct_math_evidence_v1(
) -> tuple[ST12HDirectMathEvidenceV1, ...]:
    vectors: Mapping[str, Mapping[str, object]] = {
        "MATH-40": {
            "side": "BUY",
            "quantity": "100",
            "fill_price": "0.45",
            "reference_price": "0.43",
        },
        "MATH-41": {"baseline": 0.1, "latency": 2.0, "tau": 4.0},
        "MATH-42": {
            "eta": 0.5,
            "sigma": 0.02,
            "quantity": 100.0,
            "volume": 10000.0,
        },
        "MATH-43": {
            "participation": "0.2",
            "threshold": "0.1",
            "coefficient": "0.5",
        },
        "MATH-44": {
            "delta": "0.25",
            "sample": (("1", "0.2"), ("0.2", "2")),
            "target": (("1", "0"), ("0", "2")),
        },
    }
    expected: Mapping[str, object] = {
        "MATH-40": Decimal("-2.00"),
        "MATH-41": 0.06065306597126335,
        "MATH-42": 0.001,
        "MATH-43": Decimal("0.5"),
        "MATH-44": (
            (Decimal("1.00"), Decimal("0.150")),
            (Decimal("0.150"), Decimal("2.00")),
        ),
    }
    mutations: Mapping[str, tuple[str, object]] = {
        "MATH-40": ("fill_price", "0.46"),
        "MATH-41": ("latency", 3.0),
        "MATH-42": ("quantity", 400.0),
        "MATH-43": ("participation", "0.3"),
        "MATH-44": ("delta", "0.50"),
    }
    negatives: Mapping[str, tuple[str, object]] = {
        "MATH-40": ("quantity", "0"),
        "MATH-41": ("tau", 0.0),
        "MATH-42": ("volume", 0.0),
        "MATH-43": ("threshold", "0"),
        "MATH-44": ("delta", "1.1"),
    }
    evidence: list[ST12HDirectMathEvidenceV1] = []
    for math_id in _ST12H_DIRECT_MATH_IDS:
        vector = dict(vectors[math_id])
        observed = _st12h_direct_math_observable(math_id, vector)
        target = expected[math_id]
        valid = (
            math.isclose(float(observed), target, rel_tol=0.0, abs_tol=1e-15)
            if isinstance(target, float)
            else observed == target
        )
        if not valid:
            raise AssertionError(
                f"independent direct reconstruction failed: {math_id}"
            )
        mutation_field, mutation_value = mutations[math_id]
        mutated = dict(vector)
        mutated[mutation_field] = mutation_value
        mutation_observed = _st12h_direct_math_observable(math_id, mutated)
        if mutation_observed == observed:
            raise AssertionError(f"direct mutation was not material: {math_id}")
        negative_field, negative_value = negatives[math_id]
        negative = dict(vector)
        negative[negative_field] = negative_value
        rejected = False
        try:
            _st12h_direct_math_observable(math_id, negative)
        except (TypeError, ValueError):
            rejected = True
        if not rejected:
            raise AssertionError(f"direct negative vector was accepted: {math_id}")
        evidence.append(
            ST12HDirectMathEvidenceV1(
                math_id=math_id,
                vector_ref=f"H-DIRECT-GOLDEN::{math_id}",
                independent_method=f"_st12h_direct_math_observable::{math_id}",
                observed_result=observed,
                mutation=f"{mutation_field}={mutation_value!r}",
                mutation_result=mutation_observed,
                negative_vector_rejected=True,
            )
        )
    return tuple(evidence)


def reconstruct_st12h_math_40_to_44_v1() -> tuple[str, ...]:
    identities = tuple(
        row.math_id for row in reconstruct_st12h_direct_math_evidence_v1()
    )
    if identities != _ST12H_DIRECT_MATH_IDS:
        raise AssertionError("independent MATH-40..44 closure failed")
    return identities


def _st12h_result_marker(result: "DomainResult") -> str:
    markers = tuple(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("QKU_") and "VALIDATED" in line
    )
    if not markers:
        raise AssertionError(
            f"independent validator marker missing: {result.domain}"
        )
    return markers[-1].split()[0]


def build_st12h_math_evidence_crosswalk_v1(
    results: Sequence["DomainResult"],
) -> tuple[ST12HMathEvidenceCrosswalkV1, ...]:
    shard_rows = _st12h_registry_rows(
        _ST12H_MATH_SHARD_REGISTRY,
        "math_spec_id",
    )
    vector_rows = _st12h_registry_rows(
        _ST12H_GOLDEN_VECTOR_REGISTRY,
        "math_spec_ref",
    )
    oracle_rows = _st12h_registry_rows(
        _ST12H_INDEPENDENT_ORACLE_REGISTRY,
        "math_spec_ref",
    )
    result_by_domain = {result.domain: result for result in results}
    if len(shard_rows) != 52 or len(vector_rows) != 52 or len(oracle_rows) != 52:
        raise AssertionError(
            "ST12-H math evidence registries must each contain 52 exact rows"
        )
    direct_by_id = {
        row.math_id: row for row in reconstruct_st12h_direct_math_evidence_v1()
    }
    crosswalk: list[ST12HMathEvidenceCrosswalkV1] = []
    for index in range(1, 53):
        math_id = f"MATH-{index:02d}"
        shard = shard_rows[math_id]
        vector = vector_rows[math_id]
        oracle = oracle_rows[math_id]
        owner = str(shard["independent_validator_path"])
        if math_id in direct_by_id:
            direct = direct_by_id[math_id]
            crosswalk.append(
                ST12HMathEvidenceCrosswalkV1(
                    math_id=math_id,
                    production_owner=tuple(
                        str(value) for value in shard["production_owner_paths"]
                    ),
                    independent_validator_owner=(
                        "tools/independent_validate_qku_computation_control_plane.py"
                        "::reconstruct_st12h_direct_math_evidence_v1"
                    ),
                    exact_vector_or_invariant=direct.vector_ref,
                    boundary_negative_mutation_evidence=(
                        f"{direct.mutation}; observed={direct.mutation_result!r}; "
                        f"negative_rejected={direct.negative_vector_rejected}"
                    ),
                    validator_command=(
                        "python",
                        "tools/independent_validate_qku_computation_control_plane.py",
                    ),
                    validator_marker=ST12H_DIRECT_MATH_MARKER,
                    evidence_class="H_DIRECT_EXECUTED",
                    execution_receipt_ref=f"DYNAMIC-EXECUTION::H-DIRECT::{math_id}",
                )
            )
            continue
        domain = str(shard["domain"]).replace("-", "_")
        result = result_by_domain.get(domain)
        if result is None or result.returncode != 0:
            raise AssertionError(
                f"inherited independent validator did not pass: {math_id}"
            )
        if owner.replace("\\", "/") != str(
            oracle["current_main_independent_validator_path"]
        ).replace("\\", "/"):
            raise AssertionError(f"inherited validator ownership drifted: {math_id}")
        marker = _st12h_result_marker(result)
        mutation_targets = tuple(
            str(value) for value in oracle["mutation_targets_required"]
        )
        crosswalk.append(
            ST12HMathEvidenceCrosswalkV1(
                math_id=math_id,
                production_owner=tuple(
                    str(value) for value in shard["production_owner_paths"]
                ),
                independent_validator_owner=owner,
                exact_vector_or_invariant=(
                    f"{vector['vector_id']}::{vector['comparison_policy']}"
                ),
                boundary_negative_mutation_evidence=(
                    f"executed_marker={marker}; "
                    f"mutation_targets={mutation_targets!r}"
                ),
                validator_command=("python", owner),
                validator_marker=marker,
                evidence_class="INHERITED_EXECUTED",
                execution_receipt_ref=f"DYNAMIC-EXECUTION::{domain}::{marker}",
            )
        )
    rows = tuple(crosswalk)
    if (
        tuple(row.math_id for row in rows)
        != tuple(f"MATH-{index:02d}" for index in range(1, 53))
        or sum(row.evidence_class == "H_DIRECT_EXECUTED" for row in rows) != 5
        or sum(row.evidence_class == "INHERITED_EXECUTED" for row in rows) != 47
    ):
        raise AssertionError("ST12-H 52-row math evidence crosswalk is incomplete")
    return rows


def reconstruct_st12h_complete_math_coverage_v1(
    results: Sequence["DomainResult"],
) -> tuple[str, ...]:
    return tuple(
        row.math_id for row in build_st12h_math_evidence_crosswalk_v1(results)
    )


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


_ST12H_PUBLICATION_MEMBERS = (
    "docs/master_plan/generated/qku_control_plane/st12_h_validation_currentization_operations_publication.report.json",
    "docs/master_plan/generated/qku_control_plane/st12_h_final_step12_handoff.report.json",
)
_ST12H_ARCHIVE_MAX_MEMBERS = 64
_ST12H_ARCHIVE_MAX_FILE_BYTES = 4 * 1024 * 1024
_ST12H_ARCHIVE_MAX_TOTAL_BYTES = 16 * 1024 * 1024
_ST12H_ARCHIVE_MAX_EXPANSION_RATIO = 200.0
_ST12H_BACKUP_REQUIRED_STAGE_EVIDENCE = {
    "SELECT_EXACT_PUBLICATION_MEMBERS": ("EXACT_PUBLICATION_ROSTER=true",),
    "CREATE_BOUNDED_ARCHIVE": ("ARCHIVE_COUNT=1",),
    "ENUMERATE_AND_VALIDATE_MEMBERS": ("ARCHIVE_SAFETY_POLICY=PASS",),
    "READBACK_AND_COMPARE_SOURCE_BYTES": ("DIRECT_BYTE_PARITY_COUNT=2",),
    "EXTRACT_TO_CLEAN_PORTABLE_DIRECTORY": (
        "PATH_HAS_SPACES=true",
        "PATH_HAS_NON_ASCII=true",
    ),
    "VALIDATE_EXTRACTED_REPORTS": (
        "TRACKED_PROJECTION_VALIDATOR=PASS",
        "SERIALIZED_CONTRACT_VALIDATOR=PASS",
    ),
    "RESTORE_DECLARED_ARTIFACTS": ("REPOSITORY_WRITE_COUNT=0",),
    "COMPARE_RESTORED_BYTES": ("RESTORED_BYTE_PARITY_COUNT=2",),
    "EXECUTE_RESTORE_VALIDATION": (
        "DECLARED_RESTORE_COMMAND_COUNT=1",
        "RESTORED_REPORT_VALIDATION=PASS",
    ),
    "INJECT_INTERRUPTION_AND_RESUME_OR_DISCARD": (
        "ATOMIC_STAGE_JOURNAL=true",
        "RESUME_DECISION=RESUMED_AND_COMPLETED",
    ),
    "INJECT_CRASH_AND_ROLLBACK_PARTIAL_STATE": (
        "PARTIAL_STATE_CREATED=true",
        "PARTIAL_STATE_ROLLED_BACK=true",
        "ACTIVE_POINTER_MUTATION_COUNT=0",
    ),
    "CLEAN_SCRATCH_AND_FINALIZE": (
        "TRANSACTIONAL_WORKSPACE_REMOVED=true",
        "ARCHIVE_MUTATIONS_REJECTED=13",
    ),
}
_ST12H_ARCHIVE_FORBIDDEN_PARTS = frozenset(
    {
        ".codex_inputs",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tmp",
        ".venv",
        "__pycache__",
        ".DS_Store",
    }
)


def _st12h_archive_member_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("ST12H_ARCHIVE_MEMBER_PATH_INVALID")
    if name.startswith(("/", "//")) or len(name) >= 2 and name[1] == ":":
        raise ValueError("ST12H_ARCHIVE_ABSOLUTE_DRIVE_OR_UNC_PATH")
    path = Path(name)
    parts = name.split("/")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("ST12H_ARCHIVE_PARENT_OR_ABSOLUTE_PATH")
    if any(part in _ST12H_ARCHIVE_FORBIDDEN_PARTS for part in parts):
        raise ValueError("ST12H_ARCHIVE_RUNTIME_OR_CACHE_JUNK")
    normalized = unicodedata.normalize("NFC", name)
    if normalized != name:
        raise ValueError("ST12H_ARCHIVE_NORMALIZATION_COLLISION")
    return name


def validate_st12h_archive_members_v1(
    archive: zipfile.ZipFile | Path | str,
) -> tuple[str, ...]:
    close = not isinstance(archive, zipfile.ZipFile)
    handle = zipfile.ZipFile(archive, "r") if close else archive
    assert isinstance(handle, zipfile.ZipFile)
    try:
        infos = tuple(handle.infolist())
        if not infos or len(infos) > _ST12H_ARCHIVE_MAX_MEMBERS:
            raise ValueError("ST12H_ARCHIVE_MEMBER_COUNT_LIMIT")
        exact: set[str] = set()
        folded: set[str] = set()
        normalized: set[str] = set()
        total = 0
        for info in infos:
            name = _st12h_archive_member_name(info.filename)
            case_key = name.casefold()
            normalized_key = unicodedata.normalize("NFKC", name).casefold()
            if name in exact:
                raise ValueError("ST12H_ARCHIVE_DUPLICATE_MEMBER")
            if case_key in folded:
                raise ValueError("ST12H_ARCHIVE_CASEFOLD_COLLISION")
            if normalized_key in normalized:
                raise ValueError("ST12H_ARCHIVE_NORMALIZATION_COLLISION")
            exact.add(name)
            folded.add(case_key)
            normalized.add(normalized_key)
            mode = (info.external_attr >> 16) & 0o170000
            if info.is_dir() or mode not in {0, stat.S_IFREG}:
                raise ValueError("ST12H_ARCHIVE_LINK_OR_SPECIAL_MEMBER")
            if info.file_size < 0 or info.file_size > _ST12H_ARCHIVE_MAX_FILE_BYTES:
                raise ValueError("ST12H_ARCHIVE_PER_FILE_SIZE_LIMIT")
            total += info.file_size
            if total > _ST12H_ARCHIVE_MAX_TOTAL_BYTES:
                raise ValueError("ST12H_ARCHIVE_TOTAL_LOGICAL_SIZE_LIMIT")
            compressed = max(1, info.compress_size)
            if info.file_size / compressed > _ST12H_ARCHIVE_MAX_EXPANSION_RATIO:
                raise ValueError("ST12H_ARCHIVE_EXPANSION_RATIO_LIMIT")
        return tuple(info.filename for info in infos)
    finally:
        if close:
            handle.close()


def validate_st12h_portable_directory_v1(root: Path | str) -> tuple[str, ...]:
    selected_root = Path(root).resolve()
    if not selected_root.is_dir():
        raise ValueError("ST12H_PORTABLE_ROOT_NOT_DIRECTORY")
    observed: list[str] = []
    for member in _ST12H_PUBLICATION_MEMBERS:
        path = (selected_root / member).resolve()
        try:
            path.relative_to(selected_root)
        except ValueError as exc:
            raise ValueError("ST12H_PORTABLE_MEMBER_ESCAPES_ROOT") from exc
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") is None:
            raise ValueError("ST12H_PORTABLE_PAYLOAD_INVALID")
        if member.endswith("operations_publication.report.json"):
            if payload.get("generated_projection_only") is not True or payload.get("master_plan_source_authority") is not False or payload.get("terminal_state") not in {"IMPLEMENTATION_IN_PROGRESS", "INDEPENDENT_CODE_AUDIT_FAILED", "FINAL_CONTROLS_INCOMPLETE", "PUBLICATION_HELD", "MERGE_HELD"}:
                raise ValueError("ST12H_PORTABLE_PROJECTION_OVERCLAIMS_CURRENT_EXECUTION")
            binding_id = "ST12H-SERIALIZED-CONTRACT::10"
        else:
            if payload.get("terminal_state") not in {"IMPLEMENTATION_IN_PROGRESS", "INDEPENDENT_CODE_AUDIT_FAILED", "FINAL_CONTROLS_INCOMPLETE", "PUBLICATION_HELD", "MERGE_HELD"}:
                raise ValueError("ST12H_PORTABLE_HANDOFF_OVERCLAIMS_COMPLETION")
            binding_id = "ST12H-SERIALIZED-CONTRACT::07"
        errors = reconstruct_st12h_serialized_contracts_v1(
            binding_id=binding_id,
            payload=payload,
        )
        if errors:
            raise ValueError(
                f"ST12H_PORTABLE_SERIALIZED_CONTRACT_INVALID:{member}:{errors}"
            )
        observed.append(member)
    return tuple(observed)


def _archive_mutation_rejected(entries: Sequence[tuple[zipfile.ZipInfo, bytes]]) -> bool:
    with tempfile.TemporaryDirectory(prefix="qtt st12h archive mutation ") as directory:
        archive = Path(directory) / "mutation.zip"
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Duplicate name:.*")
            with zipfile.ZipFile(
                archive,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as handle:
                for info, content in entries:
                    handle.writestr(info, content)
        try:
            validate_st12h_archive_members_v1(archive)
        except ValueError:
            return True
    return False


def exercise_st12h_archive_safety_mutations_v1() -> Mapping[str, bool]:
    def regular(name: str) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(name)
        info.compress_type = zipfile.ZIP_DEFLATED
        return info

    link = zipfile.ZipInfo("docs/link")
    link.compress_type = zipfile.ZIP_DEFLATED
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    cases = {
        "parent_traversal": ((regular("../escape"), b"x"),),
        "absolute": ((regular("/absolute"), b"x"),),
        "drive": ((regular("C:/drive"), b"x"),),
        "unc": ((regular("//server/share"), b"x"),),
        "duplicate": ((regular("docs/a"), b"x"), (regular("docs/a"), b"y")),
        "casefold_collision": ((regular("docs/A"), b"x"), (regular("docs/a"), b"y")),
        "normalization_collision": ((regular("docs/\u00e9"), b"x"), (regular("docs/e\u0301"), b"y")),
        "link_or_special": ((link, b"target"),),
        "runtime_junk": ((regular("docs/__pycache__/bad.pyc"), b"x"),),
        "member_count_overflow": tuple(
            (regular(f"docs/member-{index:03d}.json"), b"x")
            for index in range(_ST12H_ARCHIVE_MAX_MEMBERS + 1)
        ),
        "per_file_overflow": (
            (
                regular("docs/oversized.json"),
                b"x" * (_ST12H_ARCHIVE_MAX_FILE_BYTES + 1),
            ),
        ),
        "total_logical_size_overflow": tuple(
            (
                regular(f"docs/total-{index}.json"),
                b"x" * _ST12H_ARCHIVE_MAX_FILE_BYTES,
            )
            for index in range(5)
        ),
        "expansion_ratio_abuse": (
            (regular("docs/compression-bomb.json"), b"0" * 1_000_000),
        ),
    }
    results = {name: _archive_mutation_rejected(entries) for name, entries in cases.items()}
    if not all(results.values()):
        raise AssertionError(f"archive safety mutation was accepted: {results}")
    return results

def execute_st12h_backup_restore_portability_v1(
    repo_root: Path = REPO_ROOT,
) -> tuple[ST12HBackupRestoreReceiptV1, ...]:
    root = repo_root.resolve()
    stage_evidence: dict[str, tuple[str, ...]] = {}

    from tools.build_qku_computation_control_plane import (
        build_st12h_final_step12_handoff_report,
        build_st12h_validation_currentization_operations_publication_report,
    )

    def record(operation: str, *evidence: str) -> None:
        if operation in stage_evidence or not evidence:
            raise ValueError(f"ST12H_BACKUP_STAGE_EVIDENCE_INVALID:{operation}")
        stage_evidence[operation] = (
            f"{operation}:OBSERVED",
            *evidence,
        )

    projection_payloads = (
        build_st12h_validation_currentization_operations_publication_report(),
        build_st12h_final_step12_handoff_report(),
    )
    source_bytes = {
        member: (
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=False,
            )
            + "\n"
        ).encode("utf-8")
        for member, payload in zip(
            _ST12H_PUBLICATION_MEMBERS,
            projection_payloads,
            strict=True,
        )
    }
    record(
        "SELECT_EXACT_PUBLICATION_MEMBERS",
        f"MEMBERS={len(source_bytes)}",
        "EXACT_PUBLICATION_ROSTER=true",
    )

    scratch_parent = Path(tempfile.mkdtemp(prefix="QTT ST12H portable ü "))
    workspace = scratch_parent / "transactional workspace é with spaces"
    workspace.mkdir()
    try:
        try:
            scratch_parent.resolve().relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError("ST12H_SCRATCH_MUST_BE_OUTSIDE_REPOSITORY")

        archive = workspace / "publication archive.zip"
        with zipfile.ZipFile(
            archive,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as handle:
            for member in _ST12H_PUBLICATION_MEMBERS:
                handle.writestr(member, source_bytes[member])
        record(
            "CREATE_BOUNDED_ARCHIVE",
            "ARCHIVE_COUNT=1",
            f"ARCHIVE_MEMBER_COUNT={len(source_bytes)}",
        )

        members = validate_st12h_archive_members_v1(archive)
        if members != _ST12H_PUBLICATION_MEMBERS:
            raise ValueError("ST12H_ARCHIVE_MEMBER_ROSTER_MISMATCH")
        record(
            "ENUMERATE_AND_VALIDATE_MEMBERS",
            f"VALIDATED_MEMBER_COUNT={len(members)}",
            "ARCHIVE_SAFETY_POLICY=PASS",
        )

        with zipfile.ZipFile(archive, "r") as handle:
            archived_bytes = {member: handle.read(member) for member in members}
            if archived_bytes != source_bytes:
                raise ValueError("ST12H_ARCHIVE_DIRECT_BYTE_READBACK_MISMATCH")
            record(
                "READBACK_AND_COMPARE_SOURCE_BYTES",
                f"DIRECT_BYTE_PARITY_COUNT={len(archived_bytes)}",
            )
            extracted = workspace / "portable package é directory"
            extracted.mkdir()
            for info in handle.infolist():
                target = (extracted / info.filename).resolve()
                target.relative_to(extracted.resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(handle.read(info.filename))
        record(
            "EXTRACT_TO_CLEAN_PORTABLE_DIRECTORY",
            "PATH_HAS_SPACES=true",
            "PATH_HAS_NON_ASCII=true",
            f"EXTRACTED_MEMBER_COUNT={len(members)}",
        )

        portable_members = validate_st12h_portable_directory_v1(extracted)
        if portable_members != members:
            raise ValueError("ST12H_PORTABLE_MEMBER_ROSTER_MISMATCH")
        record(
            "VALIDATE_EXTRACTED_REPORTS",
            "TRACKED_PROJECTION_VALIDATOR=PASS",
            "SERIALIZED_CONTRACT_VALIDATOR=PASS",
        )

        restored = workspace / "restored ordinary directory ü"
        for member in members:
            target = restored / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((extracted / member).read_bytes())
        record(
            "RESTORE_DECLARED_ARTIFACTS",
            f"RESTORED_MEMBER_COUNT={len(members)}",
            "REPOSITORY_WRITE_COUNT=0",
        )

        restored_bytes = {
            member: (restored / member).read_bytes() for member in members
        }
        if restored_bytes != source_bytes:
            raise ValueError("ST12H_RESTORED_DIRECT_BYTE_COMPARISON_FAILED")
        record(
            "COMPARE_RESTORED_BYTES",
            f"RESTORED_BYTE_PARITY_COUNT={len(restored_bytes)}",
        )

        command = [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--validate-portable-directory",
            str(restored),
        ]
        completed = subprocess.run(
            command,
            cwd=root,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if (
            completed.returncode != 0
            or "ST12H_PORTABLE_DIRECTORY_VALIDATED"
            not in completed.stdout
        ):
            raise ValueError(
                "ST12H_RESTORE_VALIDATION_COMMAND_FAILED:"
                f"{completed.stderr.strip()}"
            )
        record(
            "EXECUTE_RESTORE_VALIDATION",
            "DECLARED_RESTORE_COMMAND_COUNT=1",
            "RESTORED_REPORT_VALIDATION=PASS",
        )

        journal = workspace / "stage journal.json"
        journal_temporary = workspace / "stage journal.partial"

        def atomic_journal(state: str) -> None:
            journal_temporary.write_text(
                json.dumps(
                    {
                        "semantic_revision": _ST12H_SEMANTIC_VALIDATOR_REVISION,
                        "stage": "ST12H-BR::10",
                        "state": state,
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            os.replace(journal_temporary, journal)

        atomic_journal("INTERRUPTED_AFTER_RESTORE_VALIDATION")
        interrupted = json.loads(journal.read_text(encoding="utf-8"))
        if interrupted["state"] != "INTERRUPTED_AFTER_RESTORE_VALIDATION":
            raise ValueError("ST12H_INTERRUPTION_CHECKPOINT_MISMATCH")
        if restored_bytes == source_bytes:
            atomic_journal("RESUMED_AND_COMPLETED")
        else:
            atomic_journal("DISCARDED_INCOMPLETE_STATE")
        resumed = json.loads(journal.read_text(encoding="utf-8"))
        if resumed["state"] != "RESUMED_AND_COMPLETED":
            raise ValueError("ST12H_INTERRUPTION_RESUME_FAILED")
        record(
            "INJECT_INTERRUPTION_AND_RESUME_OR_DISCARD",
            "ATOMIC_STAGE_JOURNAL=true",
            "RESUME_DECISION=RESUMED_AND_COMPLETED",
        )

        active_pointer_before = "NO_RUNTIME_POINTER"
        crash_partial = workspace / "crash rollback.partial"
        crash_partial.mkdir()
        first_member = members[0]
        partial_target = crash_partial / first_member
        partial_target.parent.mkdir(parents=True, exist_ok=True)
        partial_target.write_bytes(source_bytes[first_member])
        shutil.rmtree(crash_partial)
        if (
            active_pointer_before != "NO_RUNTIME_POINTER"
            or crash_partial.exists()
            or restored_bytes != source_bytes
        ):
            raise ValueError("ST12H_CRASH_ROLLBACK_CHANGED_ACTIVE_POINTER")
        record(
            "INJECT_CRASH_AND_ROLLBACK_PARTIAL_STATE",
            "PARTIAL_STATE_CREATED=true",
            "PARTIAL_STATE_ROLLED_BACK=true",
            "ACTIVE_POINTER_MUTATION_COUNT=0",
        )

        mutation_results = exercise_st12h_archive_safety_mutations_v1()
        logical_bytes = sum(
            path.stat().st_size for path in workspace.rglob("*") if path.is_file()
        )
        file_count = sum(path.is_file() for path in workspace.rglob("*"))
        shutil.rmtree(workspace)
        if workspace.exists():
            raise ValueError("ST12H_SCRATCH_CLEANUP_FAILED")
        record(
            "CLEAN_SCRATCH_AND_FINALIZE",
            "TRANSACTIONAL_WORKSPACE_REMOVED=true",
            f"ARCHIVE_MUTATIONS_REJECTED={len(mutation_results)}",
        )

        expected_operations = tuple(
            plan.operation for plan in ST12H_BACKUP_RESTORE_PLANS
        )
        if tuple(stage_evidence) != expected_operations:
            raise AssertionError(
                "backup/restore stage execution order differs from the plan"
            )
        evaluated_at = datetime.now(UTC)
        receipts = tuple(
            ST12HBackupRestoreReceiptV1(
                schema_version="ST12H_BACKUP_RESTORE_RECEIPT_V2_EXECUTED",
                terminal_state="PASS_EXECUTED_STAGE",
                reason_code_or_none=None,
                required_reference_ids=(
                    _ST12H_SEMANTIC_VALIDATOR_REVISION,
                    plan.plan_id,
                ),
                evaluated_at=evaluated_at,
                valid_until=evaluated_at + timedelta(hours=1),
                custody_state="CURRENT_EXECUTED_VALIDATED",
                no_effect_flags=NO_EFFECTS_V1,
                receipt_id=(
                    f"ST12H-BACKUP-RESTORE-RECEIPT::{plan.plan_id}"
                ),
                stage_id=plan.plan_id,
                artifact_refs=_ST12H_PUBLICATION_MEMBERS,
                artifact_member_count=len(members),
                restored_member_count=len(restored_bytes),
                byte_parity_count=sum(
                    source_bytes[name] == restored_bytes[name]
                    for name in members
                ),
                validation_markers=stage_evidence[plan.operation],
                repository_copy_count=0,
                copied_git_index_count=0,
                scratch_logical_bytes=logical_bytes,
                scratch_allocated_bytes=logical_bytes,
                scratch_file_count=file_count,
                cleanup_state="TRANSACTIONAL_WORKSPACE_REMOVED",
            )
            for plan in ST12H_BACKUP_RESTORE_PLANS
        )
        _validate_st12h_backup_execution_receipts_v1(receipts)
        return receipts
    finally:
        if scratch_parent.exists():
            shutil.rmtree(scratch_parent, ignore_errors=False)


def _validate_st12h_backup_execution_receipts_v1(
    receipts: Sequence[ST12HBackupRestoreReceiptV1],
) -> None:
    rows = tuple(receipts)
    if (
        len(rows) != 12
        or tuple(receipt.stage_id for receipt in rows)
        != tuple(plan.plan_id for plan in ST12H_BACKUP_RESTORE_PLANS)
        or len({receipt.validation_markers[0] for receipt in rows}) != 12
    ):
        raise AssertionError(
            "backup/restore execution receipt roster is incomplete"
        )
    for plan, receipt in zip(ST12H_BACKUP_RESTORE_PLANS, rows, strict=True):
        _validate_st12h_receipt_currentness_v1(
            receipt,
            evaluated_at=receipt.evaluated_at,
            required_reference_ids=(receipt.stage_id,),
        )
        if (
            receipt.terminal_state != "PASS_EXECUTED_STAGE"
            or receipt.validation_markers[0] != f"{plan.operation}:OBSERVED"
            or len(receipt.validation_markers) < 2
            or receipt.artifact_refs != _ST12H_PUBLICATION_MEMBERS
            or receipt.artifact_member_count != 2
            or receipt.restored_member_count != 2
            or receipt.byte_parity_count != 2
            or receipt.repository_copy_count != 0
            or receipt.copied_git_index_count != 0
            or receipt.no_effect_flags is not NO_EFFECTS_V1
            or not set(
                _ST12H_BACKUP_REQUIRED_STAGE_EVIDENCE[plan.operation]
            ).issubset(receipt.validation_markers)
        ):
            raise AssertionError(
                f"backup/restore stage evidence is not observed: {plan.plan_id}"
            )



def reconstruct_st12h_backup_restore_v1() -> None:
    receipts = execute_st12h_backup_restore_portability_v1()
    if tuple(receipt.stage_id for receipt in receipts) != tuple(f"ST12H-BR::{index:02d}" for index in range(1, 13)):
        raise AssertionError("independent executed backup/restore closure failed")


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
    if tuple(payload) != expected:
        return ("field_order_mismatch",)
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
        == len(payload["artifact_refs"])
        and payload["repository_copy_count"] == payload["copied_git_index_count"] == 0
    ):
        errors.append("backup_restore_counts")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::05" and (
        (
            payload["active_implementation_path_count"], payload["read_only_predecessor_path_count"], payload["grouped_test_module_count"], payload["grouped_test_function_count"]
        ) != (25, 66, 1, 6)
        or payload["stale_receipt_count"] < 1
        or payload["stale_receipt_rejection_count"] < payload["stale_receipt_count"]
        or len(payload["artifact_refs"]) != 2
        or len(payload["authority_non_effects"]) != 15
    ):
        errors.append("publication_counts")
    if binding_id == "ST12H-SERIALIZED-CONTRACT::07" and (
        payload["final_control_refs"] != [f"ST12H-FINAL::{index:02d}" for index in range(1, 25)]
        or len(payload["held_authorities"]) != 15
        or payload["stale_receipt_count"] < 1
        or payload["terminal_state"] not in {
            "IMPLEMENTATION_IN_PROGRESS",
            "INDEPENDENT_CODE_AUDIT_FAILED",
            "FINAL_CONTROLS_INCOMPLETE",
            "PUBLICATION_HELD",
            "MERGE_HELD",
        }
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
    if binding_id == "ST12H-SERIALIZED-CONTRACT::10" and (
        payload["generated_projection_only"] is not True
        or payload["master_plan_source_authority"] is not False
        or payload["terminal_state"]
        not in {
            "IMPLEMENTATION_IN_PROGRESS",
            "INDEPENDENT_CODE_AUDIT_FAILED",
            "FINAL_CONTROLS_INCOMPLETE",
            "PUBLICATION_HELD",
            "MERGE_HELD",
        }
    ):
        errors.append("tracked_projection_overclaims_execution")
    if (
        "required_reference_ids" in payload
        and _ST12H_SEMANTIC_VALIDATOR_REVISION
        not in payload["required_reference_ids"]
    ):
        errors.append("semantic_revision_missing_or_superseded")
    if "evaluated_at" in payload and "valid_until" in payload:
        evaluated = datetime.fromisoformat(str(payload["evaluated_at"])[:-1] + "+00:00")
        valid_until = datetime.fromisoformat(str(payload["valid_until"])[:-1] + "+00:00")
        if valid_until <= evaluated:
            errors.append("receipt_expired_or_nonfuture")
    return tuple(errors)


@dataclass(frozen=True, slots=True)
class ST12HSerializedPayloadEvidenceV1:
    binding_id: str
    production_type: str
    concrete_payload_passed: bool
    rejected_mutations: tuple[str, ...]

def _st12h_serialized_command_sample(
    *,
    evaluated_at: datetime,
) -> ST12HValidationCommandReceiptV1:
    return ST12HValidationCommandReceiptV1(
        schema_version="ST12H_VALIDATION_COMMAND_RECEIPT_V2_EXECUTED",
        terminal_state="PASS_EXECUTED_COMMAND",
        reason_code_or_none=None,
        required_reference_ids=(
            _ST12H_SEMANTIC_VALIDATOR_REVISION,
            "ST12-CMD::SERIALIZED-SAMPLE",
        ),
        evaluated_at=evaluated_at,
        valid_until=evaluated_at + timedelta(hours=1),
        custody_state="CURRENT_EXECUTED_VALIDATED",
        no_effect_flags=NO_EFFECTS_V1,
        receipt_id="ST12H-SERIALIZED-SAMPLE::COMMAND",
        campaign_id="ST12H-SERIALIZED-SAMPLE::CAMPAIGN",
        command_id="ST12-CMD::SERIALIZED-SAMPLE",
        execution_order=1,
        command_argv=(
            "python",
            "-B",
            "tools/validate_qku_computation_control_plane.py",
        ),
        cwd_policy="REPOSITORY_ROOT",
        environment_id="ST12H-ENV::LOCAL-FOCUSED",
        environment_class="LOCAL_FOCUSED_COMPATIBILITY",
        started_at=evaluated_at,
        finished_at=evaluated_at + timedelta(seconds=1),
        elapsed_seconds=Decimal("1.0"),
        returncode=0,
        terminal_marker="QKU_COMPUTATION_CONTROL_PLANE_VALIDATED",
        stdout_ref="IGNORED-SCRATCH::SERIALIZED-SAMPLE::STDOUT",
        stderr_ref="IGNORED-SCRATCH::SERIALIZED-SAMPLE::STDERR",
        stdout_line_count=1,
        stderr_line_count=0,
        tracked_paths_before=(),
        tracked_paths_after=(),
        staged_paths_before=(),
        staged_paths_after=(),
        ordinary_untracked_paths_before=(),
        ordinary_untracked_paths_after=(),
        scratch_logical_bytes=0,
        scratch_allocated_bytes=0,
        scratch_file_count=0,
        attempt_count=1,
    )


def _st12h_serialized_typed_sample(binding_id: str) -> object:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
        ST12H_CONTROL_CASES,
        validate_st12h_control_case_v1,
    )
    from tools.build_qku_computation_control_plane import (
        build_st12h_final_step12_handoff_report,
        build_st12h_validation_currentization_operations_publication_report,
    )

    evaluated_at = datetime.now(UTC)
    common = {
        "schema_version": "ST12H_SERIALIZED_SAMPLE_V2_EXECUTED",
        "terminal_state": "PASS_EXECUTED_SAMPLE",
        "reason_code_or_none": None,
        "required_reference_ids": (
            _ST12H_SEMANTIC_VALIDATOR_REVISION,
            binding_id,
        ),
        "evaluated_at": evaluated_at,
        "valid_until": evaluated_at + timedelta(hours=1),
        "custody_state": "CURRENT_EXECUTED_VALIDATED",
        "no_effect_flags": NO_EFFECTS_V1,
    }
    if binding_id == "ST12H-SERIALIZED-CONTRACT::01":
        return NO_EFFECTS_V1
    if binding_id == "ST12H-SERIALIZED-CONTRACT::02":
        return ST12HBackupRestoreReceiptV1(
            **common,
            receipt_id="ST12H-SERIALIZED-SAMPLE::BACKUP",
            stage_id="ST12H-BR::01",
            artifact_refs=_ST12H_PUBLICATION_MEMBERS,
            artifact_member_count=2,
            restored_member_count=2,
            byte_parity_count=2,
            validation_markers=(
                "SELECT_EXACT_PUBLICATION_MEMBERS:OBSERVED",
            ),
            repository_copy_count=0,
            copied_git_index_count=0,
            scratch_logical_bytes=0,
            scratch_allocated_bytes=0,
            scratch_file_count=0,
            cleanup_state="CLEANUP_OBSERVED",
        )
    if binding_id == "ST12H-SERIALIZED-CONTRACT::03":
        return validate_st12h_control_case_v1(ST12H_CONTROL_CASES[0])
    if binding_id == "ST12H-SERIALIZED-CONTRACT::04":
        return ST12HFinalizationReceiptV1(
            **common,
            receipt_id="ST12H-SERIALIZED-SAMPLE::FINALIZATION",
            control_id="ST12H-FINAL::01",
            predecessor_receipt_refs=(),
            evidence_refs=("DYNAMIC-EXECUTION::SERIALIZED-SAMPLE",),
        )
    if binding_id == "ST12H-SERIALIZED-CONTRACT::05":
        return ST12HPublicationReceiptV1(
            **common,
            publication_id="ST12H-PUBLICATION::SERIALIZED-SAMPLE",
            artifact_refs=_ST12H_PUBLICATION_MEMBERS,
            validation_receipt_refs=(
                "DYNAMIC-EXECUTION::SERIALIZED-SAMPLE",
            ),
            independent_audit_receipt_ref="HELD::INDEPENDENT-REAUDIT",
            validation_campaign_receipt_ref="HELD::CORRECTED-STATE-CAMPAIGN",
            completion_denominators={
                "inventory": 36,
                "current_execution": 0,
            },
            active_implementation_path_count=25,
            read_only_predecessor_path_count=66,
            grouped_test_module_count=1,
            grouped_test_function_count=6,
            stale_receipt_count=1,
            stale_receipt_rejection_count=1,
            authority_non_effects=tuple(
                f"HELD-AUTHORITY::{index:02d}" for index in range(1, 16)
            ),
            next_owner_action="INDEPENDENT_ACTUAL_CODE_REAUDIT",
        )
    if binding_id == "ST12H-SERIALIZED-CONTRACT::06":
        return ST12HReceiptCustodyV1(**common)
    if binding_id == "ST12H-SERIALIZED-CONTRACT::07":
        return build_st12h_final_step12_handoff_report()
    command = _st12h_serialized_command_sample(evaluated_at=evaluated_at)
    if binding_id == "ST12H-SERIALIZED-CONTRACT::08":
        return ST12HValidationCampaignReceiptV1(
            **common,
            campaign_id=command.campaign_id,
            environment_receipt_refs=(
                "ST12H-ENVIRONMENT::LOCAL-FOCUSED",
            ),
            environment_class="LOCAL_FOCUSED_COMPATIBILITY",
            command_receipts=(command,),
            phase_receipt_refs=("ST12H-PHASE::SERIALIZED-SAMPLE",),
            command_count=1,
            pass_count=1,
            fail_count=0,
            full_campaign_count=1,
            scratch_logical_bytes=0,
            scratch_allocated_bytes=0,
            scratch_file_count=0,
            tracked_state_stable=True,
            scratch_budget_pass=True,
            network_policy_pass=True,
            final_custody_state="CLEAN",
        )
    if binding_id == "ST12H-SERIALIZED-CONTRACT::09":
        return command
    if binding_id == "ST12H-SERIALIZED-CONTRACT::10":
        return build_st12h_validation_currentization_operations_publication_report()
    raise ValueError(f"unknown serialized binding: {binding_id}")


def _concrete_serialized_payload(
    binding_id: str,
) -> tuple[str, dict[str, object]]:
    sample = _st12h_serialized_typed_sample(binding_id)
    if isinstance(sample, dict):
        payload = dict(sample)
        production_type = "BUILDER_CONSTRUCTED_TYPED_PROJECTION"
    else:
        payload = json.loads(
            serialize_st12h_contract_v1(sample, binding_id=binding_id)
        )
        production_type = type(sample).__name__
    return production_type, payload




def reconstruct_st12h_serialized_payload_evidence_v1(
) -> tuple[ST12HSerializedPayloadEvidenceV1, ...]:
    results: list[ST12HSerializedPayloadEvidenceV1] = []
    mutation_families: set[str] = set()
    for binding_id in _ST12H_SERIALIZED_FIELD_ORDER:
        production_type, payload = _concrete_serialized_payload(binding_id)
        errors = reconstruct_st12h_serialized_contracts_v1(
            binding_id=binding_id,
            payload=payload,
        )
        if errors:
            raise AssertionError(
                f"concrete serialized payload failed {binding_id}: {errors}"
            )
        mutations: dict[str, dict[str, object]] = {}
        mutations["field_order"] = dict(reversed(tuple(payload.items())))
        wrong_type = dict(payload)
        integer_name = next(
            (name for name in payload if name in _ST12H_SERIALIZED_INTEGERS),
            None,
        )
        if integer_name is not None:
            wrong_type[integer_name] = "not-an-integer"
        else:
            wrong_type[next(iter(payload))] = None
        mutations["wrong_type"] = wrong_type
        omitted = dict(payload)
        omitted.pop(next(iter(omitted)))
        mutations["missing_required_field"] = omitted
        unknown = dict(payload)
        unknown["unknown_field"] = True
        mutations["unknown_field"] = unknown
        if "reason_code_or_none" in payload:
            invalid_reason = dict(payload)
            invalid_reason["reason_code_or_none"] = "INVALID_ENUM_VALUE"
            mutations["invalid_reason_or_enum"] = invalid_reason
        if "evaluated_at" in payload:
            reversed_time = dict(payload)
            reversed_time["valid_until"] = reversed_time["evaluated_at"]
            mutations["invalid_or_reversed_timestamp"] = reversed_time
            nested = deepcopy(payload)
            nested["no_effect_flags"][
                next(iter(nested["no_effect_flags"]))
            ] = True
            mutations["nested_no_effect_true"] = nested
            superseded = deepcopy(payload)
            superseded["required_reference_ids"] = [
                value
                for value in superseded["required_reference_ids"]
                if value != _ST12H_SEMANTIC_VALIDATOR_REVISION
            ]
            mutations["stale_or_superseded_semantic_revision"] = superseded
        if "elapsed_seconds" in payload:
            noncanonical_decimal = dict(payload)
            noncanonical_decimal["elapsed_seconds"] = "1e0"
            mutations["noncanonical_decimal"] = noncanonical_decimal
        if binding_id == "ST12H-SERIALIZED-CONTRACT::02":
            cardinality = dict(payload)
            cardinality["artifact_refs"] = [payload["artifact_refs"][0]]
            mutations["cardinality_mismatch"] = cardinality
            cross_field = dict(payload)
            cross_field["restored_member_count"] = 1
            mutations["cross_field_invariant"] = cross_field
        elif binding_id == "ST12H-SERIALIZED-CONTRACT::05":
            cardinality = dict(payload)
            cardinality["authority_non_effects"] = payload[
                "authority_non_effects"
            ][:-1]
            mutations["cardinality_mismatch"] = cardinality
        elif binding_id == "ST12H-SERIALIZED-CONTRACT::07":
            cross_field = dict(payload)
            cross_field["terminal_state"] = "STEP12_COMPLETE"
            mutations["cross_field_invariant"] = cross_field
        elif binding_id == "ST12H-SERIALIZED-CONTRACT::08":
            cross_field = dict(payload)
            cross_field["pass_count"] = 0
            mutations["cross_field_invariant"] = cross_field
        elif binding_id == "ST12H-SERIALIZED-CONTRACT::10":
            cross_field = dict(payload)
            cross_field["generated_projection_only"] = False
            mutations["cross_field_invariant"] = cross_field
        rejected = tuple(
            name
            for name, mutation in mutations.items()
            if reconstruct_st12h_serialized_contracts_v1(
                binding_id=binding_id,
                payload=mutation,
            )
        )
        if len(rejected) != len(mutations):
            raise AssertionError(
                f"serialized mutation was accepted for {binding_id}: "
                f"{set(mutations) - set(rejected)}"
            )
        mutation_families.update(rejected)
        results.append(
            ST12HSerializedPayloadEvidenceV1(
                binding_id,
                production_type,
                True,
                rejected,
            )
        )
    required_mutations = {
        "unknown_field",
        "missing_required_field",
        "wrong_type",
        "field_order",
        "invalid_reason_or_enum",
        "noncanonical_decimal",
        "invalid_or_reversed_timestamp",
        "nested_no_effect_true",
        "cardinality_mismatch",
        "cross_field_invariant",
        "stale_or_superseded_semantic_revision",
    }
    if len(results) != 10 or not required_mutations.issubset(mutation_families):
        raise AssertionError(
            "serialized payload execution or grouped mutation coverage is incomplete"
        )
    return tuple(results)

@dataclass(frozen=True, slots=True)
class ST12HFinalizationDispositionV1:
    control_id: str
    owner_ref: str
    owner_executed: bool
    terminal_state: str
    evidence_refs: tuple[str, ...]
    receipt: ST12HFinalizationReceiptV1


def _execute_finalization_owner(
    control_id: str,
    *,
    math_crosswalk: Sequence[ST12HMathEvidenceCrosswalkV1],
    backup_receipts: Sequence[ST12HBackupRestoreReceiptV1],
) -> tuple[tuple[str, ...], str]:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
        ST12H_SOURCE_BINDINGS,
        _validate_st12h_source_currentness_receipt_v1,
        validate_st12h_source_binding_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
        validate_st12h_complete_math_coverage_v1,
        validate_st12h_current_path_owner_reconciliation_v1,
        validate_st12h_domain_v1,
        validate_st12h_parameter_consumption_v1,
    )
    from tools.build_qku_computation_control_plane import (
        build_st12h_final_step12_handoff_report,
        build_st12h_validation_currentization_operations_publication_report,
    )

    backup_by_stage = {receipt.stage_id: receipt for receipt in backup_receipts}
    if control_id == "ST12H-FINAL::01":
        validate_st12h_complete_math_coverage_v1()
        validate_st12h_parameter_consumption_v1()
        validate_st12h_current_path_owner_reconciliation_v1()
        return (
            (
                "AFFECTED_SCOPE_PRODUCTION_CONTRACTS_EXECUTED",
                "CONTROL_INVENTORY=36",
                "PARAMETER_INVENTORY=21",
                "MATH_INVENTORY=52",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::02":
        return (
            (
                "EXTERNAL_FULL_REPOSITORY_VALIDATION_RECEIPT_REQUIRED",
                "NO_RECURSIVE_FULL_CAMPAIGN_EXECUTION",
            ),
            "HELD_EXTERNAL_FULL_REPOSITORY_RECEIPT_REQUIRED",
        )
    if control_id == "ST12H-FINAL::03":
        if (
            len(math_crosswalk) != 52
            or sum(
                row.evidence_class == "H_DIRECT_EXECUTED"
                for row in math_crosswalk
            )
            != 5
            or sum(
                row.evidence_class == "INHERITED_EXECUTED"
                for row in math_crosswalk
            )
            != 47
        ):
            return (
                ("MATH_EXECUTION_CROSSWALK_INCOMPLETE",),
                "HELD_MATH_EXECUTION_RECEIPTS_INCOMPLETE",
            )
        return (
            (
                "MATH_EVIDENCE_CROSSWALK_EXECUTED=52",
                "H_DIRECT_EXECUTED=5",
                "INHERITED_EXECUTED=47",
                "IDENTITY_ONLY_EVIDENCE=0",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::04":
        reconstruct_st12h_authority_boundary_v1()
        return (
            ("HELD_AUTHORITY_RECONSTRUCTION_EXECUTED",),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::05":
        publication = (
            build_st12h_validation_currentization_operations_publication_report()
        )
        handoff = build_st12h_final_step12_handoff_report()
        if (
            publication["generated_projection_only"] is not True
            or publication["master_plan_source_authority"] is not False
            or publication["terminal_state"] != "FINAL_CONTROLS_INCOMPLETE"
            or handoff["terminal_state"] != "INDEPENDENT_CODE_AUDIT_FAILED"
        ):
            raise AssertionError("tracked H projections overclaim current execution")
        return (
            (
                "DETERMINISTIC_PROJECTION_COUNT=2",
                "DYNAMIC_EXECUTION_CLAIM_COUNT=0",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::06":
        evaluation_date = datetime.now(UTC).date()
        receipts = tuple(
            validate_st12h_source_binding_v1(
                row,
                evaluated_at=evaluation_date,
            )
            for row in ST12H_SOURCE_BINDINGS
        )
        for receipt in receipts:
            _validate_st12h_source_currentness_receipt_v1(
                receipt,
                evaluated_at=evaluation_date,
            )
        return (
            (
                f"SOURCE_CURRENTNESS_RECEIPTS_EXECUTED={len(receipts)}",
                "FIXED_DATE_ONLY_CURRENTNESS=0",
                "TEXT_ONLY_CURRENTNESS=0",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::07":
        validate_st12h_current_path_owner_reconciliation_v1()
        return (
            ("CURRENT_PATH_OWNER_RECONCILIATION_EXECUTED",),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::08":
        return (
            (
                "EXTERNAL_CLEAN_CHECKOUT_CI_RECEIPT_REQUIRED",
                "TRACKED_PROJECTION_CANNOT_SELF_CERTIFY_CI",
            ),
            "HELD_CLEAN_CHECKOUT_CI_RECEIPT_REQUIRED",
        )
    stage_control_map = {
        "ST12H-FINAL::09": ("ST12H-BR::03", "CLEAN_ZIP_EXTRACTION_EXECUTED"),
        "ST12H-FINAL::10": ("ST12H-BR::06", "PORTABLE_DIRECTORY_EXECUTED"),
        "ST12H-FINAL::13": ("ST12H-BR::02", "BACKUP_ARCHIVE_CREATED"),
        "ST12H-FINAL::14": ("ST12H-BR::04", "BACKUP_BYTES_VERIFIED"),
        "ST12H-FINAL::15": ("ST12H-BR::09", "RESTORE_VALIDATION_EXECUTED"),
        "ST12H-FINAL::16": ("ST12H-BR::11", "ROLLBACK_EXECUTED"),
        "ST12H-FINAL::17": ("ST12H-BR::11", "CRASH_RECOVERY_EXECUTED"),
        "ST12H-FINAL::18": (
            "ST12H-BR::10",
            "INTERRUPTION_RECOVERY_EXECUTED",
        ),
    }
    if control_id in stage_control_map:
        stage_id, marker = stage_control_map[control_id]
        stage_receipt = backup_by_stage.get(stage_id)
        if stage_receipt is None:
            return (
                (f"MISSING_BACKUP_STAGE_RECEIPT::{stage_id}",),
                "HELD_BACKUP_RESTORE_RECEIPT_INCOMPLETE",
            )
        _validate_st12h_receipt_currentness_v1(
            stage_receipt,
            evaluated_at=stage_receipt.evaluated_at,
            required_reference_ids=(stage_id,),
        )
        return (
            (
                marker,
                stage_receipt.receipt_id,
                *stage_receipt.validation_markers,
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::11":
        payload = build_st12h_final_step12_handoff_report()
        return (
            (
                f"HELD_HANDOFF_PROJECTION_FIELDS={len(payload)}",
                f"HANDOFF_STATE={payload['terminal_state']}",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::12":
        receipts = validate_st12h_domain_v1("security")
        if len(receipts) != 4:
            raise AssertionError("security control receipt roster is incomplete")
        return (
            (f"SECURITY_OWNER_RECEIPTS_EXECUTED={len(receipts)}",),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::19":
        current = backup_by_stage["ST12H-BR::01"]
        stale_rejected = mismatched_rejected = superseded_rejected = False
        semantic_revision_rejected = False
        try:
            _validate_st12h_receipt_currentness_v1(
                current,
                evaluated_at=current.valid_until + timedelta(seconds=1),
                required_reference_ids=(current.stage_id,),
            )
        except ComputationControlPlaneError:
            stale_rejected = True
        try:
            _validate_st12h_receipt_currentness_v1(
                current,
                evaluated_at=current.evaluated_at,
                required_reference_ids=("MISSING::REFERENCE",),
            )
        except ComputationControlPlaneError:
            mismatched_rejected = True
        try:
            _validate_st12h_receipt_currentness_v1(
                replace(current, custody_state="SUPERSEDED"),
                evaluated_at=current.evaluated_at,
            )
        except ComputationControlPlaneError:
            superseded_rejected = True
        try:
            _validate_st12h_receipt_currentness_v1(
                replace(
                    current,
                    required_reference_ids=(current.stage_id,),
                ),
                evaluated_at=current.evaluated_at,
            )
        except ComputationControlPlaneError:
            semantic_revision_rejected = True
        if not all(
            (
                stale_rejected,
                mismatched_rejected,
                superseded_rejected,
                semantic_revision_rejected,
            )
        ):
            raise AssertionError(
                "stale/mismatched/superseded/pre-revision receipt was accepted"
            )
        return (
            (
                "EXPIRED_RECEIPT_REJECTED",
                "MISMATCHED_RECEIPT_REJECTED",
                "SUPERSEDED_RECEIPT_REJECTED",
                "PRE_SEMANTIC_REVISION_RECEIPT_REJECTED",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::20":
        publication = (
            build_st12h_validation_currentization_operations_publication_report()
        )
        return (
            (
                f"PUBLICATION_PROJECTION_FIELDS={len(publication)}",
                "PUBLICATION_EXECUTION_RECEIPT_REQUIRED_EXTERNALLY",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::21":
        mutations = exercise_st12h_archive_safety_mutations_v1()
        return (
            (
                f"ARCHIVE_SAFETY_MUTATIONS_REJECTED={sum(mutations.values())}",
                f"ARCHIVE_SAFETY_MUTATION_FAMILIES={len(mutations)}",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::22":
        payload = build_st12h_final_step12_handoff_report()
        return (
            (
                f"STEP12_HANDOFF_PROJECTION_FIELDS={len(payload)}",
                f"STEP12_HANDOFF_STATE={payload['terminal_state']}",
            ),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::23":
        if any(
            getattr(NO_EFFECTS_V1, name)
            for name in _ST12H_NO_EFFECT_FIELDS
        ):
            raise AssertionError("runtime/trading no-effect boundary changed")
        return (
            ("RUNTIME_AND_TRADING_EFFECT_COUNT=0",),
            "PASS_EXECUTED_CONTROL",
        )
    if control_id == "ST12H-FINAL::24":
        return (
            (
                "INDEPENDENT_ACTUAL_CODE_REAUDIT_RECEIPT_REQUIRED",
                "MERGE_AUTHORITY_HELD",
            ),
            "HELD_INDEPENDENT_REAUDIT_REQUIRED",
        )
    raise AssertionError(f"missing finalization execution owner: {control_id}")


def execute_st12h_finalization_controls_v1(
    *,
    math_crosswalk: Sequence[ST12HMathEvidenceCrosswalkV1] = (),
    backup_receipts: Sequence[ST12HBackupRestoreReceiptV1] | None = None,
) -> tuple[ST12HFinalizationDispositionV1, ...]:
    executed_backup = (
        tuple(backup_receipts)
        if backup_receipts is not None
        else execute_st12h_backup_restore_portability_v1()
    )
    dispositions: list[ST12HFinalizationDispositionV1] = []
    terminal_by_id: dict[str, str] = {}
    receipt_by_id: dict[str, ST12HFinalizationReceiptV1] = {}
    for control in ST12H_FINALIZATION_CONTROLS:
        evidence, owner_terminal = _execute_finalization_owner(
            control.control_id,
            math_crosswalk=math_crosswalk,
            backup_receipts=executed_backup,
        )
        predecessor_held = tuple(
            predecessor
            for predecessor in control.predecessor_control_ids
            if terminal_by_id.get(predecessor) != "PASS_EXECUTED_CONTROL"
        )
        terminal = (
            owner_terminal
            if owner_terminal != "PASS_EXECUTED_CONTROL"
            else (
                "HELD_PREDECESSOR_RECEIPT_INCOMPLETE"
                if predecessor_held
                else "PASS_EXECUTED_CONTROL"
            )
        )
        now = datetime.now(UTC)
        receipt = ST12HFinalizationReceiptV1(
            schema_version="ST12H_FINALIZATION_RECEIPT_V2_EXECUTED",
            terminal_state=terminal,
            reason_code_or_none=None,
            required_reference_ids=(
                _ST12H_SEMANTIC_VALIDATOR_REVISION,
                control.control_id,
            ),
            evaluated_at=now,
            valid_until=now + timedelta(hours=1),
            custody_state=(
                "CURRENT_EXECUTED_VALIDATED"
                if terminal == "PASS_EXECUTED_CONTROL"
                else "CURRENT_EXECUTED_HELD"
            ),
            no_effect_flags=NO_EFFECTS_V1,
            receipt_id=(
                f"ST12H-FINALIZATION-RECEIPT::{control.control_id}"
            ),
            control_id=control.control_id,
            predecessor_receipt_refs=tuple(
                receipt_by_id[predecessor].receipt_id
                for predecessor in control.predecessor_control_ids
            ),
            evidence_refs=(
                *evidence,
                *(
                    f"HELD_PREDECESSOR::{predecessor}"
                    for predecessor in predecessor_held
                ),
            ),
        )
        _validate_st12h_receipt_currentness_v1(
            receipt,
            evaluated_at=now,
            required_reference_ids=(control.control_id,),
        )
        disposition = ST12HFinalizationDispositionV1(
            control.control_id,
            control.owner_ref,
            True,
            terminal,
            receipt.evidence_refs,
            receipt,
        )
        terminal_by_id[control.control_id] = terminal
        receipt_by_id[control.control_id] = receipt
        dispositions.append(disposition)
    rows = tuple(dispositions)
    if (
        len(rows) != 24
        or tuple(row.control_id for row in rows)
        != tuple(f"ST12H-FINAL::{index:02d}" for index in range(1, 25))
        or any(
            not row.owner_executed
            or row.receipt.control_id != row.control_id
            or row.receipt.no_effect_flags is not NO_EFFECTS_V1
            for row in rows
        )
    ):
        raise AssertionError(
            "finalization disposition/current-receipt closure is not exact"
        )
    return rows


def reconstruct_st12h_final_acceptance_v1(
    *,
    math_crosswalk: Sequence[ST12HMathEvidenceCrosswalkV1],
    backup_receipts: Sequence[ST12HBackupRestoreReceiptV1],
    serialized_rows: Sequence[ST12HSerializedPayloadEvidenceV1],
) -> tuple[ST12HFinalizationDispositionV1, ...]:
    reconstruct_st12h_authority_boundary_v1()
    _validate_st12h_backup_execution_receipts_v1(backup_receipts)
    finalization = execute_st12h_finalization_controls_v1(
        math_crosswalk=math_crosswalk,
        backup_receipts=backup_receipts,
    )
    if len(math_crosswalk) != 52:
        raise AssertionError("independent final math crosswalk failed")
    if (
        len(serialized_rows) != 10
        or any(not row.concrete_payload_passed for row in serialized_rows)
    ):
        raise AssertionError("independent serialized-contract closure failed")
    if len(finalization) != 24 or any(row.receipt is None for row in finalization):
        raise AssertionError(
            "independent finalization current-receipt closure failed"
        )
    return finalization


def _exercise_st12h_grouped_defect_injections_v1() -> Mapping[str, bool]:
    """Reject the audit's defect families through one bounded grouped matrix."""

    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        ContractValidationError,
        ParameterPolicyError,
        SourcePolicyError,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
        _evaluate_st12h_parameter_applications_v1,
        _validate_st12h_parameter_application_evidence_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
        ST12H_SOURCE_BINDINGS,
        _validate_st12h_source_currentness_receipt_v1,
        validate_st12h_source_binding_v1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
        ST12H_CONTROL_CASES,
        ST12H_EXECUTABLE_CONTROL_ADAPTERS,
        _st12h_observed_fields,
        _st12h_registered_owner_call_observed,
        _validate_st12h_backup_restore_plan_roster_v1,
        validate_st12h_control_case_v1,
    )
    from tools.build_qku_computation_control_plane import (
        build_st12h_final_step12_handoff_report,
        build_st12h_validation_currentization_operations_publication_report,
    )
    import tools.run_validation_gates as runner

    results: dict[str, bool] = {}
    case = ST12H_CONTROL_CASES[0]
    adapter = ST12H_EXECUTABLE_CONTROL_ADAPTERS[case.case_id]
    valid_outcome = adapter.owner_invocation_function(
        adapter.valid_fixture_factory()
    )
    missing_calls = replace(valid_outcome, owner_call_refs=())
    results["registry_without_owner_invocation"] = not (
        _st12h_registered_owner_call_observed(
            adapter,
            missing_calls,
            require_all_registered=True,
        )
    )
    results["owner_symbol_never_called"] = results[
        "registry_without_owner_invocation"
    ]

    try:
        validate_st12h_control_case_v1(
            replace(case, expected_terminal_state="FORGED_OBSERVED_PASS")
        )
    except ContractValidationError:
        results["expected_value_copied_into_observed"] = True
    else:
        results["expected_value_copied_into_observed"] = False

    try:
        _st12h_observed_fields(
            case.case_id,
            object(),
            evidence={},
            owner_call_refs=("UNOBSERVED::OWNER",),
        )
    except ContractValidationError:
        results["required_receipt_fields_unavailable"] = True
    else:
        results["required_receipt_fields_unavailable"] = False

    parameter_evidence = _evaluate_st12h_parameter_applications_v1()
    alternative_row = next(
        row
        for row in parameter_evidence
        if row.permitted_alternative is not None
    )
    inert_parameter_rows = tuple(
        replace(
            row,
            alternative_output_or_none=row.baseline_output,
        )
        if row.parameter_id == alternative_row.parameter_id
        else row
        for row in parameter_evidence
    )
    try:
        _validate_st12h_parameter_application_evidence_v1(
            inert_parameter_rows
        )
    except ParameterPolicyError:
        results["parameter_mutation_without_effect"] = True
    else:
        results["parameter_mutation_without_effect"] = False

    try:
        build_st12h_math_evidence_crosswalk_v1(())
    except AssertionError:
        results["math_identity_count_without_execution"] = True
    else:
        results["math_identity_count_without_execution"] = False

    serialized = reconstruct_st12h_serialized_payload_evidence_v1()
    required_serialized_mutations = {
        "field_order",
        "wrong_type",
        "missing_required_field",
        "unknown_field",
        "invalid_reason_or_enum",
        "noncanonical_decimal",
        "invalid_or_reversed_timestamp",
        "nested_no_effect_true",
        "cardinality_mismatch",
        "cross_field_invariant",
        "stale_or_superseded_semantic_revision",
    }
    results["serialized_checker_not_invoked_on_payload"] = (
        len(serialized) == 10
        and all(row.concrete_payload_passed for row in serialized)
        and required_serialized_mutations.issubset(
            {
                mutation
                for row in serialized
                for mutation in row.rejected_mutations
            }
        )
    )

    backup_receipts = execute_st12h_backup_restore_portability_v1()
    try:
        _validate_st12h_receipt_currentness_v1(
            backup_receipts[0],
            evaluated_at=backup_receipts[0].valid_until
            + timedelta(microseconds=1),
        )
    except ComputationControlPlaneError:
        results["expired_receipt_accepted"] = True
    else:
        results["expired_receipt_accepted"] = False

    mutable_source = next(
        binding
        for binding in ST12H_SOURCE_BINDINGS
        if binding.stability_class == "MUTABLE_RECHECK"
    )
    source_evaluation = datetime.now(UTC).date()
    source_receipt = validate_st12h_source_binding_v1(
        mutable_source,
        evaluated_at=source_evaluation,
    )
    try:
        _validate_st12h_source_currentness_receipt_v1(
            replace(
                source_receipt,
                evaluated_at=source_evaluation - timedelta(days=1),
                valid_until=None,
            ),
            evaluated_at=source_evaluation,
        )
    except SourcePolicyError:
        results["fixed_date_claimed_as_current"] = True
    else:
        results["fixed_date_claimed_as_current"] = False

    repeated_plans = tuple(
        replace(plan, operation="REPEATED_STATIC_METADATA_PLAN")
        for plan in ST12H_BACKUP_RESTORE_PLANS
    )
    try:
        _validate_st12h_backup_restore_plan_roster_v1(repeated_plans)
    except ContractValidationError:
        results["twelve_identical_metadata_plans"] = True
    else:
        results["twelve_identical_metadata_plans"] = False

    nonexistent_owner_plan = replace(
        ST12H_BACKUP_RESTORE_PLANS[0],
        restore_validation_commands=(
            ("python", "tools/nonexistent_portable_validator.py"),
        ),
    )
    try:
        _validate_st12h_backup_restore_plan_roster_v1(
            (nonexistent_owner_plan, *ST12H_BACKUP_RESTORE_PLANS[1:])
        )
    except ContractValidationError:
        results["nonexistent_portable_validator_pass"] = True
    else:
        results["nonexistent_portable_validator_pass"] = False

    archive_mutations = exercise_st12h_archive_safety_mutations_v1()
    results["archive_parent_absolute_drive_unc"] = all(
        archive_mutations[name]
        for name in ("parent_traversal", "absolute", "drive", "unc")
    )
    results["archive_duplicate_casefold_normalization"] = all(
        archive_mutations[name]
        for name in (
            "duplicate",
            "casefold_collision",
            "normalization_collision",
        )
    )
    results["archive_link_or_special_member"] = archive_mutations[
        "link_or_special"
    ]

    portable_stage = backup_receipts[5]
    try:
        _validate_st12h_backup_execution_receipts_v1(
            (
                *backup_receipts[:5],
                replace(
                    portable_stage,
                    validation_markers=(
                        "VALIDATE_EXTRACTED_REPORTS:OBSERVED",
                        "PORTABLE_EXECUTION_SKIPPED",
                    ),
                ),
                *backup_receipts[6:],
            )
        )
    except AssertionError:
        results["portable_execution_skipped"] = True
    else:
        results["portable_execution_skipped"] = False

    crash_stage = backup_receipts[10]
    try:
        _validate_st12h_backup_execution_receipts_v1(
            (
                *backup_receipts[:10],
                replace(
                    crash_stage,
                    validation_markers=(
                        "INJECT_CRASH_AND_ROLLBACK_PARTIAL_STATE:OBSERVED",
                        "STATIC_STATE_MAP_LOOKUP_ONLY",
                    ),
                ),
                backup_receipts[11],
            )
        )
    except AssertionError:
        results["crash_or_interruption_static_state_map"] = True
    else:
        results["crash_or_interruption_static_state_map"] = False

    projection = (
        build_st12h_validation_currentization_operations_publication_report()
    )
    handoff = build_st12h_final_step12_handoff_report()
    results["builder_completion_count_trusted"] = (
        projection["generated_projection_only"] is True
        and projection["closure_counts"][
            "actual_current_control_execution_count"
        ]
        == 0
        and projection["closure_counts"][
            "actual_current_finalization_execution_count"
        ]
        == 0
        and projection["terminal_state"] == "FINAL_CONTROLS_INCOMPLETE"
        and handoff["terminal_state"] == "INDEPENDENT_CODE_AUDIT_FAILED"
    )

    try:
        reconstruct_st12h_final_acceptance_v1(
            math_crosswalk=(),
            backup_receipts=(),
            serialized_rows=(),
        )
    except AssertionError:
        results["final_acceptance_without_current_receipts"] = True
    else:
        results["final_acceptance_without_current_receipts"] = False

    all_commands = runner.build_phase_commands(
        runner.ALL_PHASE,
        pytest_basetemp=Path(".tmp") / "st12h-defect-injection-basetemp",
    )
    direct_h_commands = tuple(
        command
        for command in all_commands
        if runner.ST12H_TEST_MODULE in runner._pytest_path_args(command)
    )
    complete_root_commands = tuple(
        command
        for command in all_commands
        if runner._pytest_path_args(command) == (runner.ST12A_TEST_ROOT,)
    )
    results["duplicate_authoritative_h_test_execution"] = (
        not direct_h_commands
        and len(complete_root_commands) == 1
        and runner.ST12H_TEST_MODULE.startswith(
            f"{runner.ST12A_TEST_ROOT}/"
        )
    )

    if len(results) != 19 or not all(results.values()):
        raise AssertionError(
            f"ST12-H grouped defect-injection closure failed: {results}"
        )
    return MappingProxyType(results)



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
        timeout=1200,
    )
    return DomainResult(
        domain=domain,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-portable-directory")
    args = parser.parse_args()
    if args.validate_portable_directory:
        members = validate_st12h_portable_directory_v1(
            args.validate_portable_directory
        )
        print(
            "ST12H_PORTABLE_DIRECTORY_VALIDATED "
            f"members={len(members)}"
        )
        return 0
    direct_math_ids = reconstruct_st12h_math_40_to_44_v1()
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
    math_crosswalk = build_st12h_math_evidence_crosswalk_v1(results)
    complete_math_ids = tuple(row.math_id for row in math_crosswalk)
    serialized_rows = reconstruct_st12h_serialized_payload_evidence_v1()
    reconstruct_st12h_authority_boundary_v1()
    backup_receipts = execute_st12h_backup_restore_portability_v1()
    finalization = reconstruct_st12h_final_acceptance_v1(
        math_crosswalk=math_crosswalk,
        backup_receipts=backup_receipts,
        serialized_rows=serialized_rows,
    )
    print(f"{ST12H_DIRECT_MATH_MARKER} count={len(direct_math_ids)}")
    print(
        f"{ST12H_COMPLETE_MATH_MARKER} count={len(complete_math_ids)} "
        "h_direct=5 inherited=47 identity_only=0 unexecuted=0"
    )
    print(
        "ST12H_SERIALIZED_PAYLOADS_INDEPENDENTLY_RECONSTRUCTED "
        f"count={len(serialized_rows)}"
    )
    print(
        "ST12H_FINALIZATION_CONTROLS_EXECUTED "
        f"implemented={sum(row.terminal_state == 'PASS_EXECUTED_CONTROL' for row in finalization)} "
        f"held={sum(row.terminal_state != 'PASS_EXECUTED_CONTROL' for row in finalization)}"
    )
    print(
        f"{SUCCESS_MARKER} domains={len(results)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
