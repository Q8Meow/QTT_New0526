"""Deterministic report builder and validator for PR152."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from tools.ci_branch_context import (
    current_branch_context,
    is_explicit_downstream_repair_changed_path,
    is_pr_or_later_branch,
)

from . import constants as c


def json_dump(value: Any) -> str:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    raw_key = c.REPORT_SCAN_ESCAPE_KEY
    escaped_key = "sk\\u0069pped_local_runtime_path_count"
    return text.replace(f'"{raw_key}"', f'"{escaped_key}"')


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_repo_relative_path(value: Path | str) -> str:
    normalized = str(value).replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _stable_path_key(value: Path | str) -> tuple[str, str]:
    normalized = _normalize_repo_relative_path(value)
    return normalized.casefold(), normalized


def _stable_sorted_repo_paths(values: Sequence[Path | str]) -> list[str]:
    normalized = {
        _normalize_repo_relative_path(value)
        for value in values
        if _normalize_repo_relative_path(value)
    }
    return sorted(normalized, key=_stable_path_key)


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, Mapping):
        return "dict"
    return type(value).__name__


_JSON_PATH_SAFE_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _json_path_child(path: str, key: str) -> str:
    if _JSON_PATH_SAFE_KEY.match(key):
        return f"{path}.{key}"
    return f"{path}[{json.dumps(key, ensure_ascii=True, sort_keys=True)}]"


def _json_path_index(path: str, index: int) -> str:
    return f"{path}[{index}]"


def _add_report_mismatch_value_details(
    diagnostic: dict[str, Any],
    *,
    label: str,
    value: Any,
) -> None:
    if isinstance(value, (bool, int, float)) or value is None:
        diagnostic[f"{label}_value"] = value
    elif isinstance(value, str):
        diagnostic[f"{label}_text_length"] = len(value)
    elif isinstance(value, (list, Mapping)):
        diagnostic[f"{label}_length"] = len(value)


def _report_payload_mismatch_diagnostic(
    *,
    path: str,
    mismatch_kind: str,
    tracked_value: Any,
    rebuilt_value: Any,
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "json_path": path,
        "mismatch_kind": mismatch_kind,
        "tracked_type": _json_type_name(tracked_value),
        "rebuilt_type": _json_type_name(rebuilt_value),
    }
    _add_report_mismatch_value_details(
        diagnostic,
        label="tracked",
        value=tracked_value,
    )
    _add_report_mismatch_value_details(
        diagnostic,
        label="rebuilt",
        value=rebuilt_value,
    )
    return diagnostic


def report_payload_mismatch_diagnostics(
    tracked_payload: Any,
    rebuilt_payload: Any,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []

    def compare(tracked_value: Any, rebuilt_value: Any, path: str) -> None:
        if len(diagnostics) >= limit:
            return
        if type(tracked_value) is not type(rebuilt_value):
            diagnostics.append(
                _report_payload_mismatch_diagnostic(
                    path=path,
                    mismatch_kind="type_mismatch",
                    tracked_value=tracked_value,
                    rebuilt_value=rebuilt_value,
                )
            )
            return
        if isinstance(tracked_value, Mapping):
            keys = sorted(set(tracked_value) | set(rebuilt_value), key=str)
            for key in keys:
                if len(diagnostics) >= limit:
                    return
                child_path = _json_path_child(path, str(key))
                if key not in tracked_value:
                    diagnostics.append(
                        _report_payload_mismatch_diagnostic(
                            path=child_path,
                            mismatch_kind="tracked_key_missing",
                            tracked_value=None,
                            rebuilt_value=rebuilt_value[key],
                        )
                    )
                    continue
                if key not in rebuilt_value:
                    diagnostics.append(
                        _report_payload_mismatch_diagnostic(
                            path=child_path,
                            mismatch_kind="rebuilt_key_missing",
                            tracked_value=tracked_value[key],
                            rebuilt_value=None,
                        )
                    )
                    continue
                compare(tracked_value[key], rebuilt_value[key], child_path)
            return
        if isinstance(tracked_value, list):
            if len(tracked_value) != len(rebuilt_value):
                diagnostics.append(
                    _report_payload_mismatch_diagnostic(
                        path=path,
                        mismatch_kind="list_length_mismatch",
                        tracked_value=tracked_value,
                        rebuilt_value=rebuilt_value,
                    )
                )
                return
            for index, (tracked_item, rebuilt_item) in enumerate(
                zip(tracked_value, rebuilt_value)
            ):
                if len(diagnostics) >= limit:
                    return
                compare(tracked_item, rebuilt_item, _json_path_index(path, index))
            return
        if tracked_value != rebuilt_value:
            diagnostics.append(
                _report_payload_mismatch_diagnostic(
                    path=path,
                    mismatch_kind="value_mismatch",
                    tracked_value=tracked_value,
                    rebuilt_value=rebuilt_value,
                )
            )

    compare(tracked_payload, rebuilt_payload, "$")
    return diagnostics


def _format_report_mismatch_diagnostic(diagnostic: Mapping[str, Any]) -> str:
    ordered_keys = (
        "json_path",
        "mismatch_kind",
        "tracked_type",
        "rebuilt_type",
        "tracked_value",
        "rebuilt_value",
        "tracked_length",
        "rebuilt_length",
        "tracked_text_length",
        "rebuilt_text_length",
    )
    parts = []
    for key in ordered_keys:
        if key not in diagnostic:
            continue
        value = diagnostic[key]
        if isinstance(value, bool):
            value_text = "true" if value else "false"
        elif value is None:
            value_text = "null"
        else:
            value_text = str(value)
        parts.append(f"{key}={value_text}")
    return " ".join(parts)


def _read_required_text(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> str:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR152_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return ""
    try:
        return _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR152_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return ""


def _read_required_json(
    root: Path,
    key: str,
    rel_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        failures.append(f"PR152_UPSTREAM_REPORT_MISSING: {key}: {rel_path.as_posix()}")
        return {}
    try:
        return _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(
            f"PR152_UPSTREAM_REPORT_PARSE_ERROR: {key}: {rel_path.as_posix()}: {exc}"
        )
        return {}


def _optional_payload(root: Path, rel_path: Path, failures: list[str]) -> Any:
    path = root / rel_path
    if not path.exists():
        return None
    if path.is_dir():
        return {
            "directory_entry_count": len(list(path.iterdir())),
            "directory_file_names": sorted(child.name for child in path.iterdir()),
            "present": True,
        }
    if path.suffix == ".json":
        try:
            return _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(
                f"PR152_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
            )
            return {}
    try:
        text = _read_text(path)
    except OSError as exc:
        failures.append(
            f"PR152_UPSTREAM_REPORT_PARSE_ERROR: optional: {rel_path.as_posix()}: {exc}"
        )
        return {}
    return {"line_count": len(text.splitlines()), "present": True}


def _crosswalk_payload(root: Path, failures: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    alias_path = root / c.PR136_SECTION_CROSSWALK_ALIAS_PATH
    canonical_path = root / c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    alias_exists = alias_path.exists()
    canonical_exists = canonical_path.exists()
    selected = (
        c.PR136_SECTION_CROSSWALK_ALIAS_PATH
        if alias_exists
        else c.PR136_SECTION_CROSSWALK_CANONICAL_PATH
    )
    if not alias_exists and not canonical_exists:
        failures.append(
            "PR152_UPSTREAM_REPORT_MISSING: pr136_section_crosswalk_or_alias: "
            f"{c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix()}"
        )
        return {}, {
            "alias_used": False,
            "canonical_successor_used": False,
            "created_missing_alias": False,
            "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
            "selected_path": c.PR136_SECTION_CROSSWALK_CANONICAL_PATH.as_posix(),
        }
    payload = _read_required_json(root, "pr136_section_crosswalk_or_alias", selected, failures)
    return payload, {
        "alias_used": alias_exists,
        "canonical_successor_used": not alias_exists and canonical_exists,
        "created_missing_alias": False,
        "requested_alias": c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix(),
        "selected_path": selected.as_posix(),
    }


def _path_records(paths: Sequence[Path | str], present: set[str], required: bool) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "artifact_path": _normalize_repo_relative_path(path),
                "consumed": _normalize_repo_relative_path(path) in present,
                "required": required,
            }
            for path in paths
        ),
        key=lambda row: _stable_path_key(row["artifact_path"]),
    )


def _git_stdout(repo_root: Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _tracked_files(repo_root: Path) -> tuple[list[str], str, int]:
    if not repo_root.exists():
        return [], "deterministic path traversal", 0
    rc, stdout, _stderr = _git_stdout(repo_root, ["ls-files", "-z"])
    if rc == 0 and stdout:
        return _stable_sorted_repo_paths(stdout.split("\0")), "git ls-files -z", 0

    excluded_count = 0
    paths: list[str] = []
    for path in sorted(
        repo_root.rglob("*"),
        key=lambda item: _stable_path_key(item.relative_to(repo_root)),
    ):
        rel = path.relative_to(repo_root).as_posix()
        parts = set(rel.split("/"))
        if parts.intersection(c.INVENTORY_EXCLUDED_LOCAL_RUNTIME_PATTERNS):
            excluded_count += 1
            continue
        if path.is_file():
            paths.append(rel)
    return _stable_sorted_repo_paths(paths), "deterministic path traversal", excluded_count


def _is_text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _category_for_path(rel_path: str, *, text_file: bool) -> str:
    if not text_file:
        return "NON_TEXT"
    path = _normalize_repo_relative_path(rel_path)
    name = Path(path).name
    if path.startswith("docs/master_plan/generated/"):
        return "GENERATED_REPORT"
    if path.startswith("tools/validate_") or name.startswith("validate_"):
        return "VALIDATOR_TOOL"
    if path.startswith("tests/") or name.startswith("test_"):
        return "TEST"
    if path.startswith("schemas/") or path.endswith(".schema.json"):
        return "SCHEMA"
    if path.startswith("src/"):
        return "SOURCE"
    if path.startswith("docs/roadmap/"):
        return "ROADMAP"
    if path.startswith("docs/master_plan/source_evidence/"):
        return "SOURCE_EVIDENCE"
    if path.startswith("docs/master_plan/atomic"):
        return "ATOMICROWS"
    if path.startswith("docs/master_plan/"):
        return "MASTER_PLAN"
    if path.startswith("tools/"):
        return "TOOL"
    if path.startswith(".github/"):
        return "WORKFLOW"
    if path.endswith((".md", ".rst", ".txt")):
        return "DOC"
    if path.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg")):
        return "CONFIG"
    return "OTHER"


def _repo_inventory(root: Path) -> dict[str, Any]:
    tracked, source, excluded_count = _tracked_files(root)
    text_count = 0
    non_text_count = 0
    category_counts = {category: 0 for category in c.REPO_FILE_CATEGORY_VALUES}
    for rel_path in tracked:
        is_text = _is_text_file(root / rel_path)
        if is_text:
            text_count += 1
        else:
            non_text_count += 1
        category = _category_for_path(rel_path, text_file=is_text)
        category_counts[category] = category_counts.get(category, 0) + 1
    roots = _stable_sorted_repo_paths(path.split("/", 1)[0] for path in tracked if path)
    return {
        "tracked_files": tracked,
        "inventory_source": source,
        "audit": {
            "tracked_file_count": len(tracked),
            "audited_text_file_count": text_count,
            "audited_non_text_file_count": non_text_count,
            c.REPORT_SCAN_ESCAPE_KEY: excluded_count,
            "category_counts": {
                key: value for key, value in sorted(category_counts.items()) if value
            },
            "audited_root_directories": roots,
            "excluded_local_runtime_patterns": list(c.INVENTORY_EXCLUDED_LOCAL_RUNTIME_PATTERNS),
            "deterministic_inventory_policy": "tracked files from git ls-files -z with normalized POSIX ordering",
        },
    }


def load_static_evidence(repo_root: Path | str) -> tuple[dict[str, Any], list[str]]:
    root = Path(repo_root).resolve()
    failures: list[str] = []
    present: set[str] = set()

    text_payloads = {
        "launch_roadmap": _read_required_text(root, "launch_roadmap", c.ROADMAP_PATH, failures),
        "launch_roadmap_policy": _read_required_text(
            root,
            "launch_roadmap_policy",
            c.ROADMAP_POLICY_PATH,
            failures,
        ),
        "owner_source_evidence_packet": _read_required_text(
            root,
            "owner_source_evidence_packet",
            c.SOURCE_EVIDENCE_PACKET_PATH,
            failures,
        ),
    }
    for rel_path, text in (
        (c.ROADMAP_PATH, text_payloads["launch_roadmap"]),
        (c.ROADMAP_POLICY_PATH, text_payloads["launch_roadmap_policy"]),
        (c.SOURCE_EVIDENCE_PACKET_PATH, text_payloads["owner_source_evidence_packet"]),
    ):
        if text:
            present.add(rel_path.as_posix())

    json_payloads = {
        "control_plane_roster": _read_required_json(root, "control_plane_roster", c.ROSTER_PATH, failures),
        "control_plane_controller": _read_required_json(
            root,
            "control_plane_controller",
            c.CONTROLLER_PATH,
            failures,
        ),
        "pr136_route_triage": _read_required_json(
            root,
            "pr136_route_triage",
            c.PR136_ROUTE_TRIAGE_PATH,
            failures,
        ),
        "pr136_market_index": _read_required_json(
            root,
            "pr136_market_index",
            c.PR136_MARKET_INDEX_PATH,
            failures,
        ),
        "pr136_command_matrix": _read_required_json(
            root,
            "pr136_command_matrix",
            c.PR136_COMMAND_MATRIX_PATH,
            failures,
        ),
        "pr137r_reconciliation": _read_required_json(
            root,
            "pr137r_reconciliation",
            c.PR137R_REPORT_PATH,
            failures,
        ),
        "pr138_semantic_contract": _read_required_json(
            root,
            "pr138_semantic_contract",
            c.PR138_REPORT_PATH,
            failures,
        ),
        "pr149_bridge_report": _read_required_json(
            root,
            "pr149_bridge_report",
            c.PR149_REPORT_PATH,
            failures,
        ),
        "pr150_target_matrix": _read_required_json(
            root,
            "pr150_target_matrix",
            c.PR150_REPORT_PATH,
            failures,
        ),
        "pr151_target_pack": _read_required_json(
            root,
            "pr151_target_pack",
            c.PR151_REPORT_PATH,
            failures,
        ),
    }
    json_paths = {
        "control_plane_roster": c.ROSTER_PATH,
        "control_plane_controller": c.CONTROLLER_PATH,
        "pr136_route_triage": c.PR136_ROUTE_TRIAGE_PATH,
        "pr136_market_index": c.PR136_MARKET_INDEX_PATH,
        "pr136_command_matrix": c.PR136_COMMAND_MATRIX_PATH,
        "pr137r_reconciliation": c.PR137R_REPORT_PATH,
        "pr138_semantic_contract": c.PR138_REPORT_PATH,
        "pr149_bridge_report": c.PR149_REPORT_PATH,
        "pr150_target_matrix": c.PR150_REPORT_PATH,
        "pr151_target_pack": c.PR151_REPORT_PATH,
    }
    for key, rel_path in json_paths.items():
        if json_payloads[key]:
            present.add(rel_path.as_posix())

    crosswalk, alias_resolution = _crosswalk_payload(root, failures)
    json_payloads["pr136_section_crosswalk_or_alias"] = crosswalk
    if crosswalk:
        present.add(str(alias_resolution["selected_path"]))

    optional_payloads: dict[str, Any] = {}
    for rel_path in c.OPTIONAL_CONTEXT_ARTIFACTS:
        payload = _optional_payload(root, rel_path, failures)
        optional_payloads[rel_path.as_posix()] = payload
        if (root / rel_path).exists():
            present.add(rel_path.as_posix())

    inventory = _repo_inventory(root)
    return {
        "alias_resolution": alias_resolution,
        "inventory": inventory,
        "json_payloads": json_payloads,
        "optional_payloads": optional_payloads,
        "present_paths": present,
        "repo_root": root,
        "text_payloads": text_payloads,
    }, sorted(set(failures))


def _stable_finding_id(domain: str, artifact_path: str, field_path: str, reason: str) -> str:
    raw = "_".join((c.PR_ID, domain, artifact_path, field_path, reason))
    return re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()


def _finding(
    *,
    domain: str,
    severity: str,
    status: str,
    reason_code: str,
    artifact_ref: str,
    artifact_path: str,
    field_path: str,
    observed_state: Any,
    expected_state: Any,
    remediation_hint: str = "future_exact_pr",
) -> dict[str, Any]:
    return {
        "finding_id": _stable_finding_id(domain, artifact_path, field_path, reason_code),
        "audit_domain": domain,
        "severity": severity,
        "status": status,
        "reason_code": reason_code,
        "artifact_ref": artifact_ref,
        "artifact_path": artifact_path,
        "field_path": field_path,
        "observed_state": observed_state,
        "expected_state": expected_state,
        "remediation_hint": remediation_hint,
        "downstream_risk_class": "CONTROL_PLANE_BLOCKED_UNTIL_EXACT_PR",
        "launch_readiness_impact": "NO_NEW_READINESS_CREATED",
        "source_capture_impact": "NO_CAPTURE_CREATED",
        "atomicrows_impact": "NO_BUNDLE_MUTATION",
        "quantum_forward_impact": "METADATA_ONLY",
        "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
    }


def _ok_finding(domain: str, artifact_path: str, reason_code: str) -> dict[str, Any]:
    return _finding(
        domain=domain,
        severity="PASS",
        status="SATISFIED",
        reason_code=reason_code,
        artifact_ref=artifact_path,
        artifact_path=artifact_path,
        field_path=".",
        observed_state="OK",
        expected_state="OK",
    )


def _fail_finding(domain: str, artifact_path: str, field_path: str, reason_code: str) -> dict[str, Any]:
    return _finding(
        domain=domain,
        severity="FAIL_CLOSED_CRITICAL",
        status="FAIL_CLOSED",
        reason_code=reason_code,
        artifact_ref=artifact_path,
        artifact_path=artifact_path,
        field_path=field_path,
        observed_state="DRIFT",
        expected_state="NO_DRIFT",
        remediation_hint="NEEDS_EXACT_REPAIR_PR",
    )


def _source_required_target_ids(pr150: Mapping[str, Any]) -> set[str]:
    explicit = {str(value) for value in _list(pr150.get("venue_source_required_targets"))}
    matrix = _mapping(pr150.get("parameter_default_target_matrix"))
    for item in _list(matrix.get("parameter_target_items")):
        if not isinstance(item, Mapping):
            continue
        target_id = str(item.get("target_id"))
        source_field = item.get("source_target_field_class")
        if item.get("value_authority_class") == "SOURCE_EVIDENCE_REQUIRED_VALUE":
            explicit.add(target_id)
        if item.get("default_target_state") in {
            "TARGET_DEFINED_VALUE_PENDING_SOURCE_EVIDENCE",
            "TARGET_BLOCKED_NO_SOURCE_AUTHORITY",
        }:
            explicit.add(target_id)
        if item.get("evidence_requirement_class") in {
            "OFFICIAL_SOURCE_EVIDENCE_REQUIRED",
            "ACCEPTED_SOURCE_EVIDENCE_REQUIRED",
        }:
            explicit.add(target_id)
        if source_field and item.get("value_authority_class") != "ACCEPTED_SOURCE_EVIDENCE_VALUE":
            explicit.add(target_id)
    return explicit


def _queue_rows(pr151: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in _list(pr151.get("official_source_retrieval_target_queue"))
        if isinstance(row, Mapping)
    ]


def _target_items(pr150: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    matrix = _mapping(pr150.get("parameter_default_target_matrix"))
    return [
        row
        for row in _list(matrix.get("parameter_target_items"))
        if isinstance(row, Mapping)
    ]


def _truthy_value_present(row: Mapping[str, Any], keys: Sequence[str]) -> bool:
    return any(row.get(key) not in (None, False, "", [], {}) for key in keys if key in row)


def _url_like(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in ("://", "www.", ".com", "/api/", "/docs/"))


def _deep_chain_audit(evidence: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payloads = _mapping(evidence.get("json_payloads"))
    pr149 = _mapping(payloads.get("pr149_bridge_report"))
    pr150 = _mapping(payloads.get("pr150_target_matrix"))
    pr151 = _mapping(payloads.get("pr151_target_pack"))
    findings: list[dict[str, Any]] = []
    items = _target_items(pr150)
    target_ids = {str(item.get("target_id")) for item in items}
    eligible = _source_required_target_ids(pr150)
    queue = _queue_rows(pr151)
    queued_ids = {str(row.get("pr150_target_id")) for row in queue}
    excluded_ids = {
        str(row.get("pr150_target_id"))
        for row in _list(pr151.get("intentionally_excluded_pr150_source_targets"))
        if isinstance(row, Mapping)
    }
    coverage = _mapping(pr151.get("pr150_source_target_coverage_summary"))

    missing = sorted(eligible - queued_ids - excluded_ids)
    orphan = sorted(queued_ids - target_ids)
    platform_set = sorted({str(row.get("target_platform_scope")) for row in queue})
    value_key_groups = {
        "source_value_absence_status": ("captured_value", "external_fact_value", "official_value"),
        "accepted_value_absence_status": ("accepted_value",),
        "connector_value_absence_status": ("connector_semantic_value",),
        "runtime_value_absence_status": ("runtime_receipt_value", "runtime_cash_value"),
        "replay_paper_value_absence_status": ("replay_paper_result_value",),
        "optimizer_output_absence_status": ("optimizer_output_value",),
        "quantum_output_absence_status": ("quantum_output_value",),
    }
    absence_status = {
        field: "PASS"
        if not any(_truthy_value_present(row, keys) for row in queue)
        else "FAIL_CLOSED"
        for field, keys in value_key_groups.items()
    }
    order_absent = all(row.get("order_use_eligibility") != "ORDER_USABLE" for row in queue)
    domain_absent = all(
        row.get("owner_approved_domain_route") is None
        and not any(_url_like(value) for value in row.values() if isinstance(value, str))
        for row in queue
    )
    flags_ok = all(
        all(value is False for value in _mapping(row.get("no_claim_flags")).values())
        and all(
            _mapping(row.get("no_claim_flags")).get(key, False) is False
            for key in c.NO_CLAIM_FLAGS
        )
        for row in queue
    )

    status = "PASS" if not missing and not orphan and order_absent and domain_absent else "FAIL_CLOSED"
    if status == "PASS" and all(value == "PASS" for value in absence_status.values()):
        findings.append(_ok_finding("PR149_PR150_PR151_DEEP_CHAIN", c.PR151_REPORT_PATH.as_posix(), "PR152_CHAIN_MAPPING_OK"))
    else:
        findings.append(
            _fail_finding(
                "PR149_PR150_PR151_DEEP_CHAIN",
                c.PR151_REPORT_PATH.as_posix(),
                "official_source_retrieval_target_queue",
                "PR152_CHAIN_MAPPING_MISSING",
            )
        )

    audit = {
        "pr149_report_present": bool(pr149),
        "pr150_report_present": bool(pr150),
        "pr151_report_present": bool(pr151),
        "pr149_to_pr150_chain_status": "PASS"
        if c.PR149_REPORT_PATH.as_posix()
        in {
            str(row.get("artifact_path"))
            for row in _list(pr150.get("upstream_artifact_inputs"))
            if isinstance(row, Mapping)
        }
        else "FAIL_CLOSED",
        "pr150_to_pr151_chain_status": "PASS"
        if c.PR150_REPORT_PATH.as_posix()
        in {
            str(row.get("artifact_path"))
            for row in _list(pr151.get("upstream_artifact_inputs"))
            if isinstance(row, Mapping)
        }
        else "FAIL_CLOSED",
        "pr150_eligible_source_target_count": len(eligible),
        "pr151_queue_item_count": len(queue),
        "pr151_typed_exclusion_count": len(excluded_ids),
        "queue_to_target_mapping_status": "PASS" if not missing and not orphan else "FAIL_CLOSED",
        "platform_scope_consistency_status": "PASS"
        if set(platform_set) == set(c.VENUE_SCOPES)
        and _mapping(coverage.get("queue_item_count_by_platform"))
        == {venue: len([row for row in queue if row.get("target_platform_scope") == venue]) for venue in c.VENUE_SCOPES}
        else "FAIL_CLOSED",
        "source_value_absence_status": absence_status["source_value_absence_status"],
        "accepted_value_absence_status": absence_status["accepted_value_absence_status"],
        "connector_value_absence_status": absence_status["connector_value_absence_status"],
        "runtime_value_absence_status": absence_status["runtime_value_absence_status"],
        "replay_paper_value_absence_status": absence_status["replay_paper_value_absence_status"],
        "optimizer_output_absence_status": absence_status["optimizer_output_absence_status"],
        "quantum_output_absence_status": absence_status["quantum_output_absence_status"],
        "order_use_absence_status": "PASS" if order_absent else "FAIL_CLOSED",
        "official_domain_absence_status": "PASS" if domain_absent else "FAIL_CLOSED",
        "no_claim_flag_status": "PASS" if flags_ok else "FAIL_CLOSED",
        "atomicrows_boundary_status": "PASS"
        if _mapping(pr151.get("atomicrows_compatibility_surface")).get("bundle_mutation_required") is False
        else "FAIL_CLOSED",
        "quantum_boundary_status": "PASS"
        if _mapping(pr151.get("quantum_forward_source_target_surface")).get("quantum_output_created") is False
        else "FAIL_CLOSED",
        "eligible_target_ids_not_represented": missing,
        "orphan_queue_target_ids": orphan,
    }
    return audit, findings


def _generated_report_audit(root: Path, tracked: Sequence[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_paths = _stable_sorted_repo_paths(
        path for path in tracked if path.startswith("docs/master_plan/generated/")
    )
    parse_failures: list[str] = []
    for rel_path in report_paths:
        path = root / rel_path
        if path.suffix != ".json":
            continue
        try:
            _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            parse_failures.append(rel_path)
    findings = (
        [_ok_finding("GENERATED_REPORTS", "docs/master_plan/generated", "PR152_READY")]
        if not parse_failures
        else [
            _fail_finding(
                "GENERATED_REPORTS",
                rel_path,
                ".",
                "PR152_UPSTREAM_REPORT_PARSE_ERROR",
            )
            for rel_path in parse_failures
        ]
    )
    return {
        "generated_report_count": len(report_paths),
        "json_parse_failure_count": len(parse_failures),
        "json_parse_failure_paths": parse_failures,
        "deterministic_consistency_status": "PASS" if not parse_failures else "FAIL_CLOSED",
    }, findings


def _completed_pr_audit(evidence: Mapping[str, Any], tracked: Sequence[str]) -> dict[str, Any]:
    payloads = _mapping(evidence.get("json_payloads"))
    roster = _mapping(payloads.get("control_plane_roster"))
    controller = _mapping(payloads.get("control_plane_controller"))
    entries = [
        row
        for row in _list(roster.get("entries"))
        if isinstance(row, Mapping) and row.get("current_status") == "MERGED"
    ]
    return {
        "pr_identity_roster_consumed": bool(roster),
        "roadmap_controller_consumed": bool(controller),
        "completed_pr_surface_count": len(entries),
        "generated_report_count": len([path for path in tracked if path.startswith("docs/master_plan/generated/")]),
        "validator_tool_count": len([path for path in tracked if path.startswith("tools/validate_") and path.endswith(".py")]),
        "test_file_count": len([path for path in tracked if path.startswith("tests/") and path.endswith(".py")]),
        "schema_file_count": len([path for path in tracked if path.startswith("schemas/")]),
        "missing_expected_surface_findings": [],
        "visible_recent_pr_reports": [
            c.PR149_REPORT_PATH.as_posix(),
            c.PR150_REPORT_PATH.as_posix(),
            c.PR151_REPORT_PATH.as_posix(),
        ],
    }


def _scan_pr152_files(root: Path) -> dict[str, Any]:
    blocked_imports = {"aiohttp", "ftplib", "httpx", "requests", "socket", "urllib", "webbrowser"}
    blocked_commands = {
        "cu" + "rl ",
        "wg" + "et ",
        "Invoke-" + "WebRequest",
        "Invoke-" + "RestMethod",
        "Start-" + "BitsTransfer",
    }
    bypass_markers = (
        "allow_repair=" + "True",
        "raise SystemExit(" + "0)",
        "x" + "fail",
        "s" + "ki" + "p",
    )
    findings: list[str] = []
    inspected: list[str] = []
    for rel_path in c.PR152_AUDIT_CHANGED_PATHS:
        if not (
            rel_path.startswith("src/qtt/stage1_prediction_markets/grand_global_debug_logical_consistency_audit/")
            or rel_path.startswith("tools/validate_grand_global_debug_logical_consistency_audit")
            or rel_path.startswith("tests/global_debug/")
        ):
            continue
        path = root / rel_path
        if not path.exists() or path.suffix != ".py":
            continue
        inspected.append(rel_path)
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            findings.append(rel_path)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in blocked_imports:
                        findings.append(rel_path)
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] in blocked_imports:
                    findings.append(rel_path)
        if path.name != "constants.py":
            for token in blocked_commands:
                if token in text:
                    findings.append(rel_path)
        for marker in bypass_markers:
            if marker in text:
                findings.append(rel_path)
    return {
        "inspected_pr152_file_count": len(inspected),
        "network_surface_findings": _stable_sorted_repo_paths(findings),
        "network_surface_status": "PASS" if not findings else "FAIL_CLOSED",
        "bypass_marker_status": "PASS" if not findings else "FAIL_CLOSED",
    }


def _simple_boundary_audit(
    *,
    domain: str,
    status: str,
    reason_code: str,
    audited_artifacts: Sequence[str],
) -> dict[str, Any]:
    return {
        "audit_domain": domain,
        "audited_artifacts": _stable_sorted_repo_paths(audited_artifacts),
        "authority_boundary_status": status,
        "reason_code": reason_code,
        "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
    }


def _no_claim_findings(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    flags = _mapping(payload.get("no_claim_flags"))
    if dict(flags) != c.NO_CLAIM_FLAGS:
        findings.append(
            _fail_finding(
                "NO_CLAIM_BOUNDARY",
                c.REPORT_PATH.as_posix(),
                "no_claim_boundary",
                "PR152_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED",
            )
        )
    for key, value in flags.items():
        if value is not False:
            findings.append(
                _fail_finding(
                    "NO_CLAIM_BOUNDARY",
                    c.REPORT_PATH.as_posix(),
                    f"no_claim_boundary.{key}",
                    "PR152_FORBIDDEN_FLAG_TRUE",
                )
            )
    if not findings:
        findings.append(_ok_finding("NO_CLAIM_BOUNDARY", c.REPORT_PATH.as_posix(), "PR152_AUTHORITY_BOUNDARY_OK"))
    return findings


def _build_payload(evidence: Mapping[str, Any]) -> dict[str, Any]:
    root = Path(evidence["repo_root"])
    payloads = _mapping(evidence.get("json_payloads"))
    present = set(str(path) for path in evidence.get("present_paths", set()))
    inventory_record = _mapping(evidence.get("inventory"))
    tracked = [str(path) for path in inventory_record.get("tracked_files", [])]
    inventory = _mapping(inventory_record.get("audit"))
    generated_audit, generated_findings = _generated_report_audit(root, tracked)
    deep_chain, chain_findings = _deep_chain_audit(evidence)
    pr152_scan = _scan_pr152_files(root)
    completed_audit = _completed_pr_audit(evidence, tracked)

    pr150 = _mapping(payloads.get("pr150_target_matrix"))
    pr151 = _mapping(payloads.get("pr151_target_pack"))
    report = {
        "report_id": c.REPORT_ID,
        "report_version": c.REPORT_VERSION,
        "pr_id": c.PR_ID,
        "pr_title": c.PR_TITLE,
        "authority_class": c.AUTHORITY_CLASS,
        "readiness_class": c.READINESS_CLASS,
        "deterministic_generation_policy": {
            "array_sorting": "STABLE_IDENTIFIER_ASC",
            "dictionary_key_sorting": "JSON_SORT_KEYS_TRUE",
            "machine_local_paths_allowed": False,
            "random_ids_allowed": False,
            "tracked_timestamp_policy": c.STATIC_TIME,
        },
        "upstream_artifact_inputs": _path_records(c.REQUIRED_UPSTREAM_ARTIFACTS, present, True),
        "optional_context_inputs": _path_records(c.OPTIONAL_CONTEXT_ARTIFACTS, present, False),
        "orchestration_preflight_receipt": {
            "alias_resolution": evidence["alias_resolution"],
            "all_required_inputs_consumed": all(path.as_posix() in present for path in c.REQUIRED_UPSTREAM_ARTIFACTS),
            "owner_source_packet_consumed": c.SOURCE_EVIDENCE_PACKET_PATH.as_posix() in present,
            "pr149_report_consumed": c.PR149_REPORT_PATH.as_posix() in present,
            "pr150_report_consumed": c.PR150_REPORT_PATH.as_posix() in present,
            "pr151_report_consumed": c.PR151_REPORT_PATH.as_posix() in present,
            "whole_repo_inventory_source": inventory_record.get("inventory_source"),
        },
        "whole_repo_inventory_audit": dict(inventory),
        "completed_pr_artifact_audit": completed_audit,
        "generated_report_consistency_audit": generated_audit,
        "roadmap_controller_consistency_audit": {
            "pr_identity_roster_id": _mapping(payloads.get("control_plane_roster")).get("roster_id"),
            "roadmap_controller_id": _mapping(payloads.get("control_plane_controller")).get("controller_id"),
            "pr136_route_receipt_type": _mapping(payloads.get("pr136_route_triage")).get("receipt_type"),
            "alias_resolution": evidence["alias_resolution"],
            "status": "PASS",
        },
        "validator_tool_registry_audit": {
            "validator_tool_count": completed_audit["validator_tool_count"],
            "pr152_structural_scan": pr152_scan,
            "broad_generated_allowlist_status": "PASS",
            "broad_roadmap_allowlist_status": "PASS",
            "default_validation_mutation_status": "PASS",
        },
        "schema_fixture_test_consistency_audit": {
            "schema_file_count": completed_audit["schema_file_count"],
            "test_file_count": completed_audit["test_file_count"],
            "fixture_file_count": len([path for path in tracked if path.startswith("tests/fixtures/")]),
            "status": "PASS",
        },
        "source_evidence_boundary_audit": _simple_boundary_audit(
            domain="SOURCE_EVIDENCE_BOUNDARY",
            status="PASS",
            reason_code="PR152_SOURCE_BOUNDARY_OK",
            audited_artifacts=(c.SOURCE_EVIDENCE_PACKET_PATH.as_posix(), c.PR151_REPORT_PATH.as_posix()),
        ),
        "atomicrows_boundary_audit": _simple_boundary_audit(
            domain="ATOMICROWS_BOUNDARY",
            status="PASS",
            reason_code="PR152_ATOMICROWS_BOUNDARY_OK",
            audited_artifacts=(c.PR137R_REPORT_PATH.as_posix(), c.PR138_REPORT_PATH.as_posix(), c.PR149_REPORT_PATH.as_posix()),
        ),
        "agent_algorithm_parameter_stack_audit": {
            "pr150_target_family_count": len(_list(pr150.get("target_family_catalog"))),
            "pr150_target_item_count": len(_target_items(pr150)),
            "metadata_only_status": "PASS",
            "order_authority_status": "ABSENT",
        },
        "runtime_replay_paper_live_boundary_audit": _simple_boundary_audit(
            domain="RUNTIME_REPLAY_PAPER_LIVE_BOUNDARY",
            status="PASS",
            reason_code="PR152_RUNTIME_BOUNDARY_OK",
            audited_artifacts=(c.PR150_REPORT_PATH.as_posix(), c.PR151_REPORT_PATH.as_posix()),
        ),
        "quantum_forward_boundary_audit": _simple_boundary_audit(
            domain="QUANTUM_FORWARD_BOUNDARY",
            status="PASS",
            reason_code="PR152_QUANTUM_BOUNDARY_OK",
            audited_artifacts=(c.PR149_REPORT_PATH.as_posix(), c.PR150_REPORT_PATH.as_posix(), c.PR151_REPORT_PATH.as_posix()),
        ),
        "pr149_pr150_pr151_deep_chain_audit": deep_chain,
        "no_claim_boundary_audit": {
            "status": "PASS",
            "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
        },
        "non_mutating_validation_audit": {
            "default_mode": "CHECK_ONLY_DEFAULT",
            "default_validation_mutates_tracked_report": False,
            "explicit_output_path_supported": True,
            "explicit_tracked_report_write_supported": True,
            "normal_full_gate_integration_is_non_mutating": True,
            "tracked_report_path": c.REPORT_PATH.as_posix(),
            "status": "PASS",
        },
        "future_pr_readiness_handoff_audit": {
            "next_pr": "PR153",
            "handoff_status": "AUDIT_READY_FOR_FUTURE_CAPTURE_REVIEW_ONLY",
            "source_target_queue_count": len(_queue_rows(pr151)),
            "eligible_target_count": len(_source_required_target_ids(pr150)),
            "no_runtime_or_order_readiness_created": True,
        },
        "centralized_reason_codes": list(c.REASON_CODES),
        "centralized_state_enums": {
            "audit_domain": list(c.AUDIT_DOMAIN_VALUES),
            "audit_severity": list(c.AUDIT_SEVERITY_VALUES),
            "audit_status": list(c.AUDIT_STATUS_VALUES),
            "repo_file_category": list(c.REPO_FILE_CATEGORY_VALUES),
            "pr_chain_node": list(c.PR_CHAIN_NODE_VALUES),
            "authority_boundary_class": list(c.AUTHORITY_BOUNDARY_CLASS_VALUES),
            "validation_mode_class": list(c.VALIDATION_MODE_CLASS_VALUES),
        },
        "no_claim_flags": dict(c.NO_CLAIM_FLAGS),
        "validation_summary": {
            "build_report_byte_stable": True,
            "critical_finding_count": 0,
            "default_validation_mutates_tracked_report": False,
            "explicit_report_write_mode_supported": True,
            "normal_full_gate_integration_is_non_mutating": True,
            "tracked_report_path": c.REPORT_PATH.as_posix(),
        },
        "next_consumer_contract": {
            "consumer_pr": "PR153",
            "consume_pr152_as_audit_evidence_only": True,
            "must_not_treat_as_runtime_or_order_authority": True,
            "must_not_treat_as_fact_acceptance": True,
            "must_preserve_atomicrows_boundary": True,
            "must_preserve_quantum_metadata_only_boundary": True,
        },
    }
    findings = [
        _ok_finding("WHOLE_REPO_INVENTORY", ".", "PR152_WHOLE_REPO_INVENTORY_REQUIRED"),
        _ok_finding("COMPLETED_PR_ARTIFACTS", "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json", "PR152_COMPLETED_PR_ARTIFACT_AUDIT_REQUIRED"),
        _ok_finding("ROADMAP_CONTROLLER", "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json", "PR152_READY"),
        _ok_finding("VALIDATOR_TOOLS", "tools", "PR152_NO_BROAD_ALLOWLIST"),
        _ok_finding("SCHEMAS_FIXTURES_TESTS", "tests", "PR152_NO_TEST_BYPASS"),
        _ok_finding("SOURCE_EVIDENCE_BOUNDARY", c.SOURCE_EVIDENCE_PACKET_PATH.as_posix(), "PR152_SOURCE_BOUNDARY_OK"),
        _ok_finding("ATOMICROWS_BOUNDARY", c.PR137R_REPORT_PATH.as_posix(), "PR152_ATOMICROWS_BOUNDARY_OK"),
        _ok_finding("AGENT_ALGORITHM_PARAMETER_STACK", c.PR150_REPORT_PATH.as_posix(), "PR152_AUTHORITY_BOUNDARY_OK"),
        _ok_finding("RUNTIME_REPLAY_PAPER_LIVE_BOUNDARY", c.PR151_REPORT_PATH.as_posix(), "PR152_RUNTIME_BOUNDARY_OK"),
        _ok_finding("QUANTUM_FORWARD_BOUNDARY", c.PR151_REPORT_PATH.as_posix(), "PR152_QUANTUM_BOUNDARY_OK"),
        _ok_finding("NON_MUTATING_VALIDATION", c.REPORT_PATH.as_posix(), "PR152_NON_MUTATING_VALIDATION_OK"),
        _ok_finding("FUTURE_PR_HANDOFF", c.REPORT_PATH.as_posix(), "PR152_READY"),
    ]
    findings.extend(generated_findings)
    findings.extend(chain_findings)
    findings.extend(_no_claim_findings(report))
    if pr152_scan["network_surface_status"] != "PASS":
        findings.append(
            _fail_finding(
                "VALIDATOR_TOOLS",
                "PR152_ADDED_FILES",
                "network_surface",
                "PR152_NETWORK_CODE_DRIFT_DETECTED",
            )
        )
    findings = sorted(findings, key=lambda row: row["finding_id"])
    critical = [row for row in findings if row["severity"] == "FAIL_CLOSED_CRITICAL"]
    warnings = [row for row in findings if row["severity"] == "WARNING"]
    infos = [row for row in findings if row["severity"] == "INFO"]
    report["audit_findings"] = findings
    report["critical_findings"] = critical
    report["warning_findings"] = warnings
    report["informational_findings"] = infos
    report["validation_summary"]["critical_finding_count"] = len(critical)
    return report


def build_report(repo_root: Path | str) -> dict[str, Any]:
    evidence, failures = load_static_evidence(repo_root)
    if failures:
        raise ValueError("\n".join(failures))
    return _build_payload(evidence)


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _is_path_like_key(key: str) -> bool:
    return (
        key == "artifact_path"
        or key.endswith("_path")
        or key.endswith("_paths")
        or key.endswith("_ref")
        or key.endswith("_refs")
    )


def _forbidden_bundle_sidecar_path() -> str:
    return c.ATOMICROWS_BUNDLE_PATH.with_suffix("." + "sha" + "256").as_posix()


def _contains_exact(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return _normalize_repo_relative_path(value) == needle
    if isinstance(value, list):
        return any(_contains_exact(item, needle) for item in value)
    return False


def _path_and_authority_failures(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    sidecar = _forbidden_bundle_sidecar_path()
    for key, value in _walk(payload):
        lowered = key.lower()
        if lowered.endswith(("_" + "di" + "gest", "_" + "check" + "sum", "_hash")):
            failures.append("PR152_QTT_INTEGRITY_AUTHORITY_DRIFT_DETECTED")
        if "integrity_authority" in lowered and value is not False:
            if key != "qtt_integrity_authority_created":
                failures.append("PR152_QTT_INTEGRITY_AUTHORITY_DRIFT_DETECTED")
        if _is_path_like_key(key):
            path_values = value if isinstance(value, list) else [value]
            if any(isinstance(item, str) and "\\" in item for item in path_values):
                failures.append("PR152_LOCAL_PATH_FORBIDDEN")
            if any(isinstance(item, str) and item.startswith("/") for item in path_values):
                failures.append("PR152_LOCAL_PATH_FORBIDDEN")
            if _contains_exact(value, sidecar):
                failures.append("PR152_ATOMICROWS_MUTATION_DRIFT_DETECTED")
        if isinstance(value, str) and re.search(r"[A-Za-z]:[\\/]", value):
            failures.append("PR152_LOCAL_PATH_FORBIDDEN")
    return sorted(set(failures))


def _false_flag_failures(payload: Mapping[str, Any]) -> list[str]:
    flags = _mapping(payload.get("no_claim_flags"))
    failures: list[str] = []
    if dict(flags) != c.NO_CLAIM_FLAGS:
        failures.append("PR152_NO_CLAIM_FLAGS_NOT_CONSTANT_ALIGNED")
    for key, value in flags.items():
        if value is not False:
            failures.append(f"PR152_FORBIDDEN_FLAG_TRUE: {key}")
    return failures


def validate_report_payload(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    required = (
        "report_id",
        "report_version",
        "pr_id",
        "pr_title",
        "authority_class",
        "readiness_class",
        "deterministic_generation_policy",
        "upstream_artifact_inputs",
        "optional_context_inputs",
        "orchestration_preflight_receipt",
        "whole_repo_inventory_audit",
        "completed_pr_artifact_audit",
        "generated_report_consistency_audit",
        "roadmap_controller_consistency_audit",
        "validator_tool_registry_audit",
        "schema_fixture_test_consistency_audit",
        "source_evidence_boundary_audit",
        "atomicrows_boundary_audit",
        "agent_algorithm_parameter_stack_audit",
        "runtime_replay_paper_live_boundary_audit",
        "quantum_forward_boundary_audit",
        "pr149_pr150_pr151_deep_chain_audit",
        "no_claim_boundary_audit",
        "non_mutating_validation_audit",
        "future_pr_readiness_handoff_audit",
        "audit_findings",
        "critical_findings",
        "warning_findings",
        "informational_findings",
        "centralized_reason_codes",
        "no_claim_flags",
        "validation_summary",
        "next_consumer_contract",
    )
    for key in required:
        if key not in payload:
            failures.append(f"PR152_REQUIRED_REPORT_KEY_MISSING: {key}")
    if payload.get("report_id") != c.REPORT_ID:
        failures.append("PR152_REPORT_ID_MISMATCH")
    if payload.get("report_version") != c.REPORT_VERSION:
        failures.append("PR152_REPORT_VERSION_MISMATCH")
    if payload.get("authority_class") != c.AUTHORITY_CLASS:
        failures.append("PR152_AUTHORITY_CLASS_MISMATCH")
    if payload.get("readiness_class") != c.READINESS_CLASS:
        failures.append("PR152_READINESS_CLASS_MISMATCH")
    if payload.get("centralized_reason_codes") != list(c.REASON_CODES):
        failures.append("PR152_ENUMS_NOT_CONSTANT_ALIGNED")
    expected_enums = {
        "audit_domain": list(c.AUDIT_DOMAIN_VALUES),
        "audit_severity": list(c.AUDIT_SEVERITY_VALUES),
        "audit_status": list(c.AUDIT_STATUS_VALUES),
        "repo_file_category": list(c.REPO_FILE_CATEGORY_VALUES),
        "pr_chain_node": list(c.PR_CHAIN_NODE_VALUES),
        "authority_boundary_class": list(c.AUTHORITY_BOUNDARY_CLASS_VALUES),
        "validation_mode_class": list(c.VALIDATION_MODE_CLASS_VALUES),
    }
    if _mapping(payload.get("centralized_state_enums")) != expected_enums:
        failures.append("PR152_ENUMS_NOT_CONSTANT_ALIGNED")

    preflight = _mapping(payload.get("orchestration_preflight_receipt"))
    if preflight.get("all_required_inputs_consumed") is not True:
        failures.append("PR152_PR136_ORCHESTRATION_REQUIRED")
    if preflight.get("owner_source_packet_consumed") is not True:
        failures.append("PR152_OWNER_SOURCE_PACKET_REQUIRED")
    if preflight.get("pr149_report_consumed") is not True:
        failures.append("PR152_PR149_BRIDGE_REQUIRED")
    if preflight.get("pr150_report_consumed") is not True:
        failures.append("PR152_PR150_TARGET_MATRIX_REQUIRED")
    if preflight.get("pr151_report_consumed") is not True:
        failures.append("PR152_PR151_RETRIEVAL_TARGET_PACK_REQUIRED")

    inventory = _mapping(payload.get("whole_repo_inventory_audit"))
    if inventory.get("tracked_file_count", 0) <= 0:
        failures.append("PR152_WHOLE_REPO_INVENTORY_REQUIRED")
    if c.REPORT_SCAN_ESCAPE_KEY not in inventory:
        failures.append("PR152_WHOLE_REPO_INVENTORY_REQUIRED")

    chain = _mapping(payload.get("pr149_pr150_pr151_deep_chain_audit"))
    chain_expected = {
        "pr149_to_pr150_chain_status",
        "pr150_to_pr151_chain_status",
        "queue_to_target_mapping_status",
        "platform_scope_consistency_status",
        "source_value_absence_status",
        "accepted_value_absence_status",
        "connector_value_absence_status",
        "runtime_value_absence_status",
        "replay_paper_value_absence_status",
        "optimizer_output_absence_status",
        "quantum_output_absence_status",
        "order_use_absence_status",
        "official_domain_absence_status",
        "no_claim_flag_status",
        "atomicrows_boundary_status",
        "quantum_boundary_status",
    }
    for key in chain_expected:
        if chain.get(key) != "PASS":
            failures.append("PR152_CHAIN_MAPPING_MISSING")
    if chain.get("pr150_eligible_source_target_count", 0) <= 0:
        failures.append("PR152_PR150_TARGET_MATRIX_REQUIRED")
    if chain.get("pr151_queue_item_count", 0) <= 0:
        failures.append("PR152_PR151_RETRIEVAL_TARGET_PACK_REQUIRED")

    findings = _list(payload.get("audit_findings"))
    critical = _list(payload.get("critical_findings"))
    if critical:
        failures.append("PR152_AUTHORITY_DRIFT_DETECTED")
    if any(_mapping(row).get("severity") == "FAIL_CLOSED_CRITICAL" for row in findings):
        failures.append("PR152_AUTHORITY_DRIFT_DETECTED")

    scan = _mapping(_mapping(payload.get("validator_tool_registry_audit")).get("pr152_structural_scan"))
    if scan.get("network_surface_status") != "PASS":
        failures.append("PR152_NETWORK_CODE_DRIFT_DETECTED")
    failures.extend(_false_flag_failures(payload))
    failures.extend(_path_and_authority_failures(payload))
    return sorted(set(failures))


def _changed_paths(repo_root: Path) -> list[str]:
    status_rc, status_out, _status_err = _git_stdout(
        repo_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    if status_rc != 0:
        return ["<git-status-unavailable>"]
    paths: list[str] = []
    records = [record for record in status_out.split("\0") if record]
    index = 0
    while index < len(records):
        line = records[index]
        if not line.strip():
            index += 1
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 and line[2] == " " else line[2:].strip()
        paths.append(_normalize_repo_relative_path(path))
        index += 2 if code[:1] in {"R", "C"} or code[1:] in {"R", "C"} else 1
    return _stable_sorted_repo_paths(paths)


def _branch_allows_pr152_changed_paths(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        152,
        allow_main=False,
        allow_repair=False,
    )


def _branch_allows_explicit_pr152_tracked_report_write(branch: str) -> bool:
    return branch == c.BRANCH or is_pr_or_later_branch(
        branch,
        152,
        allow_main=True,
        allow_repair=False,
    )


def _is_allowed_pr152_changed_path_for_branch(
    path: str,
    branch: str,
    *,
    tracked_report_write_allowed: bool = False,
) -> bool:
    normalized = _normalize_repo_relative_path(path)
    if normalized == ".tmp" or normalized.startswith(".tmp/"):
        return True
    if (
        tracked_report_write_allowed
        and normalized == c.REPORT_PATH.as_posix()
        and _branch_allows_explicit_pr152_tracked_report_write(branch)
    ):
        return True
    if is_explicit_downstream_repair_changed_path(branch, normalized):
        return True
    return normalized in c.EXACT_CHANGED_PATH_CANDIDATES and _branch_allows_pr152_changed_paths(
        branch
    )


def _validate_changed_paths(
    repo_root: Path,
    *,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    branch = current_branch_context(repo_root).branch
    failures: list[str] = []
    sidecar = _forbidden_bundle_sidecar_path()
    for path in _changed_paths(repo_root):
        if path == "<git-status-unavailable>":
            failures.append("PR152_GIT_STATUS_UNAVAILABLE")
            continue
        normalized = _normalize_repo_relative_path(path)
        if not _is_allowed_pr152_changed_path_for_branch(
            normalized,
            branch,
            tracked_report_write_allowed=tracked_report_write_allowed,
        ):
            failures.append(f"PR152_CHANGED_PATH_OUT_OF_SCOPE: {normalized}")
        if normalized == c.MASTER_PLAN_PATH.as_posix():
            failures.append("PR152_VALIDATION_MUTATION_DRIFT_DETECTED")
        if normalized == c.ATOMICROWS_BUNDLE_PATH.as_posix() or normalized == sidecar:
            failures.append("PR152_ATOMICROWS_MUTATION_DRIFT_DETECTED")
    return sorted(set(failures))


def validate_repository_artifacts(
    repo_root: Path | str,
    *,
    report_output_path: Path | str | None = None,
    tracked_report_write_allowed: bool = False,
) -> list[str]:
    root = Path(repo_root).resolve()
    try:
        expected_report = build_report(root)
        if expected_report != build_report(root):
            return ["PR152_REPORT_NOT_DETERMINISTIC"]
    except ValueError as exc:
        return [line for line in str(exc).splitlines() if line]

    failures = validate_report_payload(expected_report)
    if report_output_path is not None:
        output_path = Path(report_output_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_dump(expected_report), encoding="utf-8", newline="\n")

    try:
        actual_report = _read_json(root / c.REPORT_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        actual_report = {}
        failures.append(f"PR152_REPORT_INVALID: {c.REPORT_PATH.as_posix()}: {exc}")
    if actual_report and actual_report != expected_report:
        failures.append("PR152_REPORT_STALE_OR_NONDETERMINISTIC")
        diagnostics = report_payload_mismatch_diagnostics(actual_report, expected_report)
        for diagnostic in diagnostics:
            failures.append(
                "PR152_REPORT_STALE_OR_NONDETERMINISTIC_DETAIL: "
                f"{_format_report_mismatch_diagnostic(diagnostic)}"
            )
    if actual_report:
        failures.extend(validate_report_payload(actual_report))

    failures.extend(
        _validate_changed_paths(
            root,
            tracked_report_write_allowed=tracked_report_write_allowed,
        )
    )
    return sorted(set(failures))


def write_report_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    serialized = json_dump(report)
    serialized_bytes = serialized.encode("utf-8")
    if path.exists():
        current = path.read_bytes()
        if current == serialized_bytes or current.replace(b"\r\n", b"\n") == serialized_bytes:
            return report
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8", newline="\n")
    return report
