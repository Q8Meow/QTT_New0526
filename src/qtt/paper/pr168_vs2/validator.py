"""Validator for PR168-VS2 paper-intent candidate artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .models import (
    AUTHORITY_BOUNDARY_REF,
    AUTHORITY_FALSE_FIELDS,
    EXECUTION_AUTHORITY_REF,
    FORBIDDEN_VS2_FILENAMES,
    GENERATED_DIR,
    JSONL_OUTPUTS,
    JSON_OUTPUTS,
    READY_FORBIDDEN_TOKENS,
    REPORT_OUTPUTS,
    PR_ID,
    all_artifact_filenames,
    read_json,
    read_jsonl,
)


class Vs2ValidationError(AssertionError):
    """Raised when VS2 generated surfaces violate their contract."""


COMMON_FIELDS = (
    "schema_version",
    "row_id",
    "run_id",
    "producer_pr",
    "source_pr",
    "producer_tool",
    "created_at_utc",
    "source_artifact_refs",
    "upstream_refs",
    "downstream_refs",
    "owner_agent",
    "consumer_agents",
    "validation_refs",
    "authority_boundary_ref",
    "execution_authority_ref",
    "blocker_policy_ref",
    "orphan_flag",
)


def _walk_values(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        out: list[Any] = []
        for value in payload.values():
            out.extend(_walk_values(value))
        return out
    if isinstance(payload, list):
        out = []
        for value in payload:
            out.extend(_walk_values(value))
        return out
    return [payload]


def _rows(generated_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {name: read_jsonl(generated_dir / name) for name in JSONL_OUTPUTS}


def _reports(generated_dir: Path) -> dict[str, dict[str, Any]]:
    return {name: read_json(generated_dir / name) for name in (*JSON_OUTPUTS, *REPORT_OUTPUTS)}


def _check_common(filename: str, index: int, row: dict[str, Any], failures: list[str]) -> None:
    for field in COMMON_FIELDS:
        if row.get(field) in (None, "", []):
            failures.append(f"ROW_MISSING_COMMON_FIELD:{filename}:{index}:{field}")
    if row.get("producer_pr") != PR_ID or row.get("source_pr") != PR_ID:
        failures.append(f"ROW_BAD_PR:{filename}:{index}")
    if row.get("authority_boundary_ref") != AUTHORITY_BOUNDARY_REF:
        failures.append(f"ROW_BAD_AUTH_REF:{filename}:{index}")
    if row.get("execution_authority_ref") != EXECUTION_AUTHORITY_REF:
        failures.append(f"ROW_BAD_EXEC_REF:{filename}:{index}")
    if row.get("paper_intent_candidate_only_flag") is not True:
        failures.append(f"ROW_NOT_PAPER_INTENT_ONLY:{filename}:{index}")
    if row.get("advisory_only_flag") is not True:
        failures.append(f"ROW_NOT_ADVISORY_ONLY:{filename}:{index}")
    for field in AUTHORITY_FALSE_FIELDS:
        if row.get(field) is not False:
            failures.append(f"ROW_FORBIDDEN_AUTHORITY_TRUE:{filename}:{index}:{field}={row.get(field)!r}")


def _check_specific(rows: dict[str, list[dict[str, Any]]], reports: dict[str, dict[str, Any]], generated_dir: Path, failures: list[str]) -> None:
    if reports["missing_req.report.json"].get("fail_closed_flag") is not False:
        failures.append("MISSING_REQUIRED_INPUTS_PRESENT")
    if not rows["paper_intent_candidate.jsonl"]:
        failures.append("NO_PAPER_INTENT_CANDIDATES")
    if len(rows["vs2_packet_registry.jsonl"]) != len(rows["paper_intent_candidate.jsonl"]):
        failures.append("PACKET_REGISTRY_COUNT_MISMATCH")
    packet_ids = {row.get("paper_intent_candidate_id") for row in rows["paper_intent_candidate.jsonl"]}
    for filename in (
        "packet_access_contract.jsonl",
        "packet_evidence_bundle.jsonl",
        "packet_decision_trace.jsonl",
        "packet_idempotency_key.jsonl",
        "qku_formula_route_bundle.jsonl",
        "qstruct_carry.jsonl",
        "paper_readiness.jsonl",
        "no_live_submit.jsonl",
        "no_connector_write.jsonl",
        "no_private_state.jsonl",
        "no_cash_read.jsonl",
        "no_order_submit.jsonl",
        "paper_loop_packet.jsonl",
        "paper_loop_contract.jsonl",
        "mem1_handoff.jsonl",
        "downstream_handoff.jsonl",
    ):
        row_packet_ids = {row.get("paper_intent_candidate_id") for row in rows[filename]}
        missing = packet_ids - row_packet_ids
        if missing:
            failures.append(f"PACKET_ROWS_MISSING:{filename}:{sorted(missing)}")

    for packet in rows["paper_intent_candidate.jsonl"]:
        refs = packet.get("upstream_refs", []) + packet.get("source_artifact_refs", [])
        if not any("pr168_qopt1" in str(ref) for ref in refs):
            failures.append(f"PACKET_WITHOUT_QOPT1_REF:{packet.get('row_id')}")
        if not any("pr168_rank4" in str(ref) for ref in refs):
            failures.append(f"PACKET_WITHOUT_RANK4_REF:{packet.get('row_id')}")
        if not any("pr168_rp5g" in str(ref) for ref in refs):
            failures.append(f"PACKET_WITHOUT_RP5G_REF:{packet.get('row_id')}")
        for key in (
            "net_expected_pnl_cash",
            "lower_confidence_bound_pnl_cash",
            "candidate_minus_no_trade_cash",
            "TCA_total_cash",
            "fill_probability",
            "qopt_objective_value",
        ):
            if packet.get(key) in (None, ""):
                failures.append(f"PACKET_MISSING_NUMERIC:{packet.get('row_id')}:{key}")

    deferred_like = ("PAPER_INTENT_DEFERRED_", "READY_AFTER_", "MISSING_", "STALE_", "NOT_PAPER_INTENT_ELIGIBLE_")
    for row in rows["paper_readiness.jsonl"] + rows["packet_decision_trace.jsonl"] + rows["vs2_candidate_paper_elig.jsonl"]:
        state = str(row.get("paper_readiness_state") or row.get("paper_eligibility_state") or "")
        if state.startswith(deferred_like):
            if row.get("paper_loop_candidate_ready_now_flag") is True:
                failures.append(f"DEFERRED_READY_NOW_TRUE:{row.get('row_id')}")
            if row.get("paper_loop_ready_without_revalidation_flag") is True:
                failures.append(f"DEFERRED_READY_WITHOUT_REVALIDATION_TRUE:{row.get('row_id')}")
            if row.get("paper_submit_authority_created_flag") is True:
                failures.append(f"DEFERRED_PAPER_SUBMIT_TRUE:{row.get('row_id')}")
    for filename in JSONL_OUTPUTS:
        for row in rows[filename]:
            for value in _walk_values(row):
                if isinstance(value, str):
                    for token in READY_FORBIDDEN_TOKENS:
                        if token in value:
                            failures.append(f"FORBIDDEN_STATE_TOKEN:{filename}:{row.get('row_id')}:{token}")

    deferred_packets = {
        row.get("paper_intent_candidate_id")
        for row in rows["paper_readiness.jsonl"]
        if str(row.get("paper_readiness_state", "")).startswith("PAPER_INTENT_DEFERRED_")
    }
    completion_packets = {row.get("paper_intent_candidate_id") for row in rows["packet_completion_queue.jsonl"]}
    if not deferred_packets.issubset(completion_packets):
        failures.append(f"DEFERRED_WITHOUT_COMPLETION:{sorted(deferred_packets - completion_packets)}")
    for row in rows["packet_completion_queue.jsonl"]:
        for field in (
            "packet_completion_queue_id",
            "paper_intent_candidate_id",
            "readiness_gap_code",
            "exact_missing_requirement",
            "responsible_role_target",
            "canonical_agent_name_or_triage_route",
            "agent_alias_map_ref",
            "agent_resolution_source",
            "completion_owner_resolution_status",
            "upstream_pr_or_future_pr_route",
            "completion_action",
        ):
            if row.get(field) in (None, "", []):
                failures.append(f"COMPLETION_ROW_MISSING:{row.get('row_id')}:{field}")
        for field in ("formula_mutation_flag", "qku_mutation_flag", "profit_forcing_flag", "no_trade_bypass_flag", "paper_submit_authority_created_flag", "live_authority_created_flag", "orphan_flag"):
            if row.get(field) is not False:
                failures.append(f"COMPLETION_FORBIDDEN_TRUE:{row.get('row_id')}:{field}")

    for filename in FORBIDDEN_VS2_FILENAMES:
        if (generated_dir / filename).exists():
            failures.append(f"FORBIDDEN_VS2_ARTIFACT_PRESENT:{filename}")
    actual = {path.name for path in generated_dir.iterdir() if path.is_file()}
    expected = set(all_artifact_filenames())
    missing_files = sorted(expected - actual)
    extra_scope_files = sorted((actual - expected) & set(FORBIDDEN_VS2_FILENAMES))
    for name in missing_files:
        failures.append(f"MISSING_GENERATED_FILE:{name}")
    for name in extra_scope_files:
        failures.append(f"FORBIDDEN_EXTRA_FILE:{name}")

    artifact_paths = {Path(row.get("file_path", "")).name for row in rows["artifact_io.jsonl"]}
    value_paths = {Path(row.get("artifact_or_value_ref", "")).name for row in rows["value_route.jsonl"]}
    expected_without_manifests = set(all_artifact_filenames(include_manifests=False))
    if artifact_paths != expected_without_manifests:
        failures.append("ARTIFACT_IO_DOES_NOT_COVER_ALL_FILES")
    if value_paths != expected_without_manifests:
        failures.append("VALUE_ROUTE_DOES_NOT_COVER_ALL_FILES")
    if reports["no_orphan.report.json"].get("no_orphan_pass_flag") is not True:
        failures.append("NO_ORPHAN_REPORT_FAIL")
    if reports["authority_boundary.report.json"].get("authority_boundary_pass_flag") is not True:
        failures.append("AUTHORITY_REPORT_FAIL")

    for row in rows["research_rec.jsonl"] + rows["source_coverage.jsonl"] + rows["source_intake.jsonl"] + rows["source_value_cand.jsonl"] + rows["venue_order_semantic_cand.jsonl"] + rows["paper_default_cand.jsonl"]:
        if row.get("candidate_only_flag") is not True:
            failures.append(f"RESEARCH_NOT_CANDIDATE_ONLY:{row.get('row_id')}")
        if row.get("accepted_source_fact_flag") is not False or row.get("connector_semantic_binding_flag") is not False:
            failures.append(f"RESEARCH_CREATED_SOURCE_OR_CONNECTOR_AUTHORITY:{row.get('row_id')}")
        if row.get("replay_paper_verification_required") is not True:
            failures.append(f"RESEARCH_NO_REPLAY_PAPER_VERIFICATION:{row.get('row_id')}")

    if any("repair" in path.name.lower() for path in generated_dir.iterdir() if path.is_file()):
        failures.append("REPAIR_TERMINOLOGY_ARTIFACT_PRESENT")


def validate_vs2_artifacts(repo_root: str | Path, artifact_dir: str | Path | None = None) -> list[str]:
    root = Path(repo_root)
    generated_dir = Path(artifact_dir) if artifact_dir is not None else GENERATED_DIR
    if not generated_dir.is_absolute():
        generated_dir = root / generated_dir
    failures: list[str] = []
    if not generated_dir.is_dir():
        return [f"MISSING_VS2_GENERATED_DIR:{generated_dir}"]
    rows = _rows(generated_dir)
    reports = _reports(generated_dir)
    for filename in JSONL_OUTPUTS:
        if filename not in rows:
            failures.append(f"MISSING_JSONL_LOAD:{filename}")
        for index, row in enumerate(rows.get(filename, []), start=1):
            _check_common(filename, index, row, failures)
    _check_specific(rows, reports, generated_dir, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--artifact-dir", default=str(GENERATED_DIR))
    parser.add_argument("--timeout-ms", type=int, default=3600000)
    args = parser.parse_args(argv)
    failures = validate_vs2_artifacts(args.repo_root, args.artifact_dir)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("PR168-VS2 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
