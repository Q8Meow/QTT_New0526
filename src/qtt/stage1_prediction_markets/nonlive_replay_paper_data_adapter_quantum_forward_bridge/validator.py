"""PR162 artifact validator."""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload
from .loaders import load_pr161f_records
from .paths import normalize_shard_ref, resolve_repo_relative
from .pr152_currentization import pr152_currentization_evidence


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    failures: tuple[str, ...]


def validate_artifacts(repo_root: Path) -> ValidationResult:
    failures: list[str] = []
    reports: dict[str, dict[str, Any]] = {}
    for filename in c.REPORT_FILENAMES:
        path = repo_root / c.GENERATED_DIR / filename
        if not path.exists():
            failures.append(f"missing PR162 report: {path}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"PR162 report is not an object: {path}")
            continue
        reports[filename] = payload
    for schema_filename in c.SCHEMA_FILENAMES:
        if not (repo_root / c.SCHEMA_DIR / schema_filename).exists():
            failures.append(f"missing PR162 schema: {schema_filename}")
    if failures:
        return ValidationResult(False, tuple(failures))

    _validate_common_report_contracts(reports, failures)
    manifest_by_report = _manifest_by_report(
        reports[c.SHARD_MANIFEST_REPORT_FILENAME],
        failures,
    )
    _validate_manifest_paths(repo_root, reports, manifest_by_report, failures)
    loaded = {
        filename: _load_records(repo_root, filename, reports[filename], manifest_by_report, failures)
        for filename in c.REPORT_FILENAMES
        if filename != c.SHARD_MANIFEST_REPORT_FILENAME
    }
    if failures:
        return ValidationResult(False, tuple(failures))

    _validate_pr161f_inputs(repo_root, loaded, failures)
    _validate_dataset_discovery(loaded, failures)
    _validate_adapter_and_artifacts(loaded, failures)
    _validate_handoff_and_coverage(loaded, failures)
    _validate_quantum_bridge(loaded, failures)
    _validate_agent_bridge(loaded, failures)
    _validate_pr152_currentization(repo_root, reports, loaded, failures)
    _validate_forbidden_scan(repo_root, reports, loaded, failures)
    _validate_no_absolute_paths(reports, loaded, failures)
    _validate_git_guardrails(repo_root, failures)
    return ValidationResult(not failures, tuple(failures))


def _validate_common_report_contracts(
    reports: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for filename, payload in reports.items():
        _expect(payload.get("report_id"), failures, f"{filename} missing report_id")
        _expect(payload.get("created_by_pr") == c.PR_ID, failures, f"{filename} created_by_pr mismatch")
        _expect(payload.get("authority_class") == c.AUTHORITY_CLASS, failures, f"{filename} authority class mismatch")
        _expect(payload.get("schema_ref") == c.REPORT_SCHEMA_REFS[filename], failures, f"{filename} schema_ref mismatch")
        _expect(isinstance(payload.get("source_inputs"), list), failures, f"{filename} source_inputs missing")
        _expect(tuple(payload.get("upstream_pr_refs") or ()) == c.UPSTREAM_PR_REFS, failures, f"{filename} upstream refs mismatch")
        for route in c.DOWNSTREAM_PR_ROUTES:
            _expect(route in payload.get("downstream_pr_routes", []), failures, f"{filename} missing downstream route {route}")
        for flag, expected in c.NO_AUTHORITY_FLAGS.items():
            _expect(payload.get(flag) is expected, failures, f"{filename} no-authority flag drift: {flag}")


def _validate_pr161f_inputs(
    repo_root: Path,
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    pr161f = load_pr161f_records(repo_root)
    _expect(
        len(pr161f["PR161F_ExecutorInputRegistry.report.json"]) == 9360,
        failures,
        "PR162 must consume 9360 PR161F executor inputs",
    )
    _expect(
        len(pr161f["PR161F_ReplayRunRequestRegistry.report.json"]) == 9360,
        failures,
        "PR162 must consume 9360 PR161F replay requests",
    )
    _expect(
        len(pr161f["PR161F_PaperRunRequestRegistry.report.json"]) == 9360,
        failures,
        "PR162 must consume 9360 PR161F paper requests",
    )
    _expect(
        len(pr161f["PR161F_PairedReplayPaperRunPlan.report.json"]) == 9360,
        failures,
        "PR162 must consume 9360 PR161F paired plans",
    )
    _expect(
        len(pr161f["PR161F_ResultPacketEmissionEligibilityGate.report.json"]) == 9360,
        failures,
        "PR162 must consume 9360 PR161F eligibility gates",
    )
    _expect(
        len(pr161f["PR161F_QuantumClassicalHybridRunPlan.report.json"]) == 4525,
        failures,
        "PR162 must consume 4525 PR161F quantum/classical/hybrid plans",
    )
    qku_coverage = loaded["PR162_QKUArtifactCoverageBridge.report.json"]
    _expect(len(qku_coverage) == 9360, failures, "PR162 QKU coverage must cover every PR161F QKU")


def _validate_dataset_discovery(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162_NonLiveDatasetDiscovery.report.json"]
    _expect(records, failures, "dataset discovery must emit allowlist records")
    for record in records:
        rel = record.get("relative_posix_path", "")
        _expect("\\" not in rel, failures, f"dataset path must be POSIX relative: {record['record_id']}")
        _expect(not re.match(r"^[A-Za-z]:/", rel), failures, f"dataset path must not be absolute: {record['record_id']}")
        _expect(
            record.get("dataset_authority_class") in c.DATASET_AUTHORITY_CLASSES,
            failures,
            f"dataset authority class invalid: {record['record_id']}",
        )
        if record.get("dataset_authority_class") in {
            "REPO_LOCAL_SYNTHETIC_FIXTURE",
            "REPO_LOCAL_SMOKE_FIXTURE",
        }:
            _expect(
                record.get("allowed_for_real_nonlive_artifact_candidate") is False,
                failures,
                f"synthetic/smoke fixture labeled run-capable: {record['record_id']}",
            )
    _expect(
        all(record.get("allowed_for_real_nonlive_artifact_candidate") is False for record in records),
        failures,
        "current repo state must not produce run-capable real non-live datasets",
    )


def _validate_adapter_and_artifacts(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    replay_contract = loaded["PR162_ReplayDataAdapterContract.report.json"]
    paper_contract = loaded["PR162_PaperDataAdapterContract.report.json"]
    artifact_records = loaded["PR162_RealNonLiveRunArtifactCandidateRegistry.report.json"]
    _expect(len(replay_contract) == 1, failures, "replay adapter contract count mismatch")
    _expect(len(paper_contract) == 1, failures, "paper adapter contract count mismatch")
    _expect(replay_contract[0]["artifact_status"] == "REPLAY_BLOCKED_NO_SAFE_DATA", failures, "replay contract must fail closed")
    _expect(paper_contract[0]["artifact_status"] == "PAPER_BLOCKED_NO_SAFE_DATA", failures, "paper contract must fail closed")
    _expect(artifact_records == [], failures, "no real non-live artifact candidates should be produced without safe data")


def _validate_handoff_and_coverage(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    result_handoff = loaded["PR162_ResultPacketReadinessHandoffCandidate.report.json"]
    pr161e_handoff = loaded["PR162_PR161EIngestionHandoffCandidate.report.json"]
    qku_coverage = loaded["PR162_QKUArtifactCoverageBridge.report.json"]
    _expect(len(result_handoff) == 9360, failures, "result handoff must cover every QKU")
    _expect(len(pr161e_handoff) == 9360, failures, "PR161E handoff must cover every QKU")
    _expect(
        all(record["result_packet_ready_flag"] is False for record in result_handoff),
        failures,
        "result packet readiness must remain blocked",
    )
    _expect(
        all(record["pr161e_handoff_candidate_flag"] is False for record in pr161e_handoff),
        failures,
        "PR161E ingestion handoff must remain blocked without validated real artifacts",
    )
    _expect(
        all(record["replay_lane_state"] == "REPLAY_BLOCKED_NO_SAFE_DATA" for record in qku_coverage),
        failures,
        "replay lane separation drift",
    )
    _expect(
        all(record["paper_lane_state"] == "PAPER_BLOCKED_NO_SAFE_DATA" for record in qku_coverage),
        failures,
        "paper lane separation drift",
    )
    _expect(
        sum(1 for record in qku_coverage if record["orphan_status"].startswith("NOT_ORPHANED")) == 9360,
        failures,
        "QKU coverage contains orphaned non-rejected artifact state",
    )


def _validate_quantum_bridge(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    readiness = loaded["PR162_QKUQuantumExecutionReadinessBridge.report.json"]
    encoding = loaded["PR162_QKUQuantumProblemEncodingBlueprint.report.json"]
    params = loaded["PR162_QuantumParameterRangeCandidateRegistry.report.json"]
    backend = loaded["PR162_QuantumBackendFitCandidateMatrix.report.json"]
    comparator = loaded["PR162_QuantumClassicalHybridComparatorBlueprint.report.json"]
    work_orders = loaded["PR162_QuantumReplayPaperWorkOrderQueue.report.json"]
    live_bridge = loaded["PR162_QuantumLiveModeControlPlaneBridge.report.json"]
    latency = loaded["PR162_QuantumLatencyLivePathReadinessBridge.report.json"]
    downstream = loaded["PR162_QKUQuantumDownstreamAgentRouteMatrix.report.json"]
    qch_bridge = loaded["PR162_QuantumClassicalHybridArtifactInputBridge.report.json"]

    for report_name, records in {
        "readiness": readiness,
        "encoding": encoding,
        "backend": backend,
        "comparator": comparator,
        "work_orders": work_orders,
        "live_bridge": live_bridge,
        "latency": latency,
        "downstream": downstream,
        "qch_bridge": qch_bridge,
    }.items():
        _expect(len(records) == 4525, failures, f"quantum {report_name} must cover 4525 QKUs")
    _expect(len(params) == len(c.PARAMETER_CANDIDATE_NAMES), failures, "parameter candidate registry count mismatch")
    _expect(
        all("QUANTUM_ENCODING_BLUEPRINT_READY" in record["readiness_states"] for record in readiness),
        failures,
        "quantum readiness missing encoding blueprint state",
    )
    _expect(
        all(record["live_hot_path_allowed_flag"] is False for record in encoding),
        failures,
        "encoding blueprint allowed live hot path",
    )
    _expect(
        all(record["candidate_authority_class"] in c.PARAMETER_CANDIDATE_AUTHORITY_CLASSES for record in params),
        failures,
        "parameter candidate authority class invalid",
    )
    _expect(
        all(record["live_use_allowed_flag"] is False for record in params),
        failures,
        "parameter candidates must not allow live use",
    )
    _expect(
        all(record["live_mode_forbidden_in_pr162_flag"] is True for record in backend),
        failures,
        "backend matrix allowed PR162 live mode",
    )
    _expect(
        all(record["candidate_backend_family"] == "BACKEND_BLOCKED_NO_DATA" for record in backend),
        failures,
        "backend matrix must be blocked no data in current repo state",
    )
    _expect(
        all(record["quantum_advantage_claim_allowed_flag"] is False for record in comparator),
        failures,
        "comparator blueprint allowed quantum advantage claim",
    )
    _expect(
        all(record["live_mode_ready_flag"] is False for record in work_orders),
        failures,
        "work order created live readiness",
    )
    _expect(
        all(record["pr162_live_authority_created_flag"] is False for record in live_bridge),
        failures,
        "live control bridge created live authority",
    )
    _expect(
        all(record["live_hot_path_admissibility"] == "PRECOMPUTED_SNAPSHOT_ONLY" for record in latency),
        failures,
        "latency bridge must require precomputed snapshots",
    )
    _expect(
        all(record["no_agent_self_authorizes_live_trading_flag"] is True for record in downstream),
        failures,
        "quantum downstream route allowed agent self-authorization",
    )


def _validate_agent_bridge(
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    records = loaded["PR162_QTTAgentExecutorHandoffBridge.report.json"]
    _expect({record["agent_id"] for record in records} == set(c.AGENT_ROLES), failures, "agent bridge role coverage mismatch")
    _expect(
        all(record["runtime_agent_execution_created_flag"] is False for record in records),
        failures,
        "agent bridge created runtime agent execution",
    )
    _expect(
        all(record["self_authorizing_trading_allowed_flag"] is False for record in records),
        failures,
        "agent bridge allowed self-authorized trading",
    )
    _expect(
        all(record["live_authority_allowed_flag"] is False for record in records),
        failures,
        "agent bridge allowed live authority",
    )


def _validate_pr152_currentization(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    evidence = pr152_currentization_evidence(repo_root)
    expected_result = evidence["pr152_currentization_result"]
    summary = reports["PR162_FinalSummary.report.json"]
    records = loaded["PR162_FinalSummary.report.json"]
    _expect(len(records) == 1, failures, "PR162 final summary must contain one record")
    containers = [summary, *records[:1]]
    for container in containers:
        _expect(
            container.get("pr152_currentization_result") == expected_result,
            failures,
            "PR162 final summary PR152 currentization result is stale",
        )
        _expect(
            container.get("pr152_currentization_failure_count")
            == evidence["pr152_currentization_failure_count"],
            failures,
            "PR162 final summary PR152 currentization failure count is stale",
        )
    _expect(
        expected_result == c.PR152_CURRENTIZATION_RESULT_PASS,
        failures,
        f"PR152 currentization validation is not confirmed pass: {expected_result}",
    )


def _validate_forbidden_scan(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    scan = loaded["PR162_ForbiddenAuthorityScan.report.json"][0]
    _expect(scan["scan_status"] == "PASS", failures, "forbidden authority scan report must pass")
    _expect(
        scan["no_scattered_hardcoded_policy_scan_status"] == "PASS",
        failures,
        "no-scattered-policy scan report must pass",
    )
    _scan_source_policy_literals(repo_root, failures)
    _scan_hidden_network_calls(repo_root, failures)
    all_text = "\n".join(_stringify(list(reports.values())))
    forbidden_fragments = (
        "profit guarantee",
        "quantum advantage evidence",
        "live order receipt",
        "private account state fetched",
        "qpu call executed",
    )
    for fragment in forbidden_fragments:
        _expect(fragment not in all_text.lower(), failures, f"forbidden authority wording found: {fragment}")


def _validate_no_absolute_paths(
    reports: dict[str, dict[str, Any]],
    loaded: dict[str, list[dict[str, Any]]],
    failures: list[str],
) -> None:
    text = "\n".join(_stringify(list(reports.values()))) + "\n" + "\n".join(
        _stringify(list(loaded.values()))
    )
    _expect(not re.search(r"[A-Za-z]:[\\/]", text), failures, "generated reports contain Windows absolute path")
    _expect("\\Users\\" not in text and "/Users/" not in text, failures, "generated reports contain local user path")


def _validate_git_guardrails(repo_root: Path, failures: list[str]) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    changed = {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}
    _expect(
        "docs/master_plan/QTT_MasterPlan_Current.md" not in changed,
        failures,
        "PR162 must not mutate QTT_MasterPlan_Current.md",
    )
    _expect(
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl" not in changed,
        failures,
        "PR162 must not mutate AtomicRows.bundle.jsonl",
    )


def _manifest_by_report(manifest: dict[str, Any], failures: list[str]) -> dict[str, dict[str, Any]]:
    by_report: dict[str, dict[str, Any]] = {}
    for record in records_from_payload(manifest):
        report_filename = record.get("report_filename")
        if not isinstance(report_filename, str):
            failures.append("PR162 shard manifest record missing report_filename")
            continue
        if report_filename in by_report:
            failures.append(f"duplicate PR162 shard manifest record: {report_filename}")
            continue
        by_report[report_filename] = record
    return by_report


def _validate_manifest_paths(
    repo_root: Path,
    reports: dict[str, dict[str, Any]],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    expected = {filename for filename, payload in reports.items() if payload.get("sharded_flag")}
    _expect(set(manifest_by_report) == expected, failures, "PR162 shard manifest must list exactly sharded reports")
    for report_filename, record in manifest_by_report.items():
        payload = reports[report_filename]
        shard_files = record.get("shard_files") or []
        _expect(payload.get("records") == [], failures, f"sharded top-level report duplicated records: {report_filename}")
        _expect(int(record.get("shard_count", -1)) == len(shard_files), failures, f"PR162 shard count mismatch: {report_filename}")
        for index, shard_ref in enumerate(shard_files, start=1):
            normalized = normalize_shard_ref(repo_root, shard_ref)
            _expect(normalized == shard_ref, failures, f"PR162 shard ref must already be normalized: {shard_ref}")
            _expect("\\" not in shard_ref, failures, f"PR162 shard ref must be POSIX: {shard_ref}")
            shard_path = resolve_repo_relative(repo_root, shard_ref)
            _expect(shard_path.exists(), failures, f"missing PR162 shard file: {shard_ref}")
            shard_payload = read_json(shard_path)
            _expect(shard_payload.get("parent_report_filename") == report_filename, failures, f"PR162 shard parent mismatch: {shard_ref}")
            _expect(shard_payload.get("shard_index") == index, failures, f"PR162 shard index mismatch: {shard_ref}")


def _load_records(
    repo_root: Path,
    filename: str,
    payload: dict[str, Any],
    manifest_by_report: dict[str, dict[str, Any]],
    failures: list[str],
) -> list[dict[str, Any]]:
    if not payload.get("sharded_flag"):
        records = records_from_payload(payload)
        _expect(int(payload.get("record_count", len(records))) == len(records), failures, f"record_count mismatch: {filename}")
        return records
    manifest_record = manifest_by_report.get(filename)
    if manifest_record is None:
        failures.append(f"missing PR162 shard manifest record for {filename}")
        return []
    merged: list[dict[str, Any]] = []
    for shard_ref in manifest_record.get("shard_files") or []:
        shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
        merged.extend(records_from_payload(shard_payload))
    _expect(int(manifest_record.get("total_record_count", -1)) == len(merged), failures, f"manifest total mismatch: {filename}")
    _expect(int(payload.get("total_record_count", -1)) == len(merged), failures, f"payload total mismatch: {filename}")
    return merged


def _scan_source_policy_literals(repo_root: Path, failures: list[str]) -> None:
    allowed = set(c.BLOCKER_CODES) | set(c.SOURCE_CLASSES)
    source_roots = [
        repo_root / "src/qtt/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge",
        repo_root / "tools/build_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        repo_root / "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        repo_root / "tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge",
    ]
    patterns = (
        re.compile(r'"(PR162_BLOCKED_[A-Z0-9_]+)"'),
        re.compile(r'"(QUANTUM_(?:BLOCKED|ENCODING|PARAMETER|BACKEND|CLASSICAL|REPLAY|REAL|RESULT|FUTURE)[A-Z0-9_]+)"'),
        re.compile(r'"(BACKEND_(?:BLOCKED|UNVERIFIED)[A-Z0-9_]+)"'),
        re.compile(r'"(COMPARATOR_(?:BLOCKED|BLUEPRINT)[A-Z0-9_]+)"'),
        re.compile(r'"(PR161E_HANDOFF_[A-Z0-9_]+)"'),
        re.compile(r'"((?:REPLAY|PAPER)_BLOCKED_[A-Z0-9_]+)"'),
    )
    for root in source_roots:
        if root.is_file():
            candidates = [root]
        elif root.exists():
            candidates = sorted(root.rglob("*.py"))
        else:
            candidates = []
        for path in candidates:
            if path.name in c.NO_SCATTERED_POLICY_ALLOWLIST:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                for match in pattern.findall(text):
                    _expect(
                        match in allowed,
                        failures,
                        f"policy literal outside central registry: {path.relative_to(repo_root).as_posix()}:{match}",
                    )


def _scan_hidden_network_calls(repo_root: Path, failures: list[str]) -> None:
    roots = [
        repo_root / "src/qtt/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge",
        repo_root / "tools/build_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
        repo_root / "tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
    ]
    forbidden = ("requests.", "httpx.", "urllib.request", "socket.", "websocket", "pip install")
    for root in roots:
        if root.is_file():
            candidates = [root]
        else:
            candidates = sorted(root.rglob("*.py"))
        for path in candidates:
            if path.name == "validator.py":
                continue
            text = path.read_text(encoding="utf-8").lower()
            for fragment in forbidden:
                _expect(fragment not in text, failures, f"hidden network call pattern in {path.relative_to(repo_root).as_posix()}: {fragment}")


def _stringify(values: Any) -> list[str]:
    if isinstance(values, dict):
        result: list[str] = []
        for key, value in values.items():
            result.append(str(key))
            result.extend(_stringify(value))
        return result
    if isinstance(values, list | tuple | set):
        result = []
        for value in values:
            result.extend(_stringify(value))
        return result
    return [str(values)]


def _expect(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)
