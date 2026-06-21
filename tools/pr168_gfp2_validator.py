#!/usr/bin/env python3
"""Shared validators for PR168-GFP2 artifacts."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_gfp2_constants import BASELINE_COUNTS, GENERATED_DIR, REQUIRED_REPORTS
from tools.pr168_gfp2_report_writer import read_records, read_report


class ValidationError(AssertionError):
    pass


FORBIDDEN_TRUE_FLAGS = (
    "live_authority_created_flag",
    "order_authority_created_flag",
    "source_truth_acceptance_created_flag",
    "connector_semantic_binding_created_flag",
    "private_state_accessed_flag",
    "cash_accessed_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "qku_sha_or_atomicrows_hash_authority_flag",
    "qtt_sha_or_atomicrows_hash_authority_flag",
    "profit_guarantee_created_flag",
)


def load(filename: str) -> list[dict[str, Any]]:
    return read_records(REPO_ROOT, filename)


def root(filename: str) -> dict[str, Any]:
    return read_report(REPO_ROOT, filename)


def expect(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{code}: {message}")


def validate_reports_exist() -> None:
    missing = [name for name in REQUIRED_REPORTS if not (REPO_ROOT / GENERATED_DIR / name).exists()]
    expect(not missing, "PR168_GFP2_MISSING_REPORTS", str(missing[:20]))
    for name in REQUIRED_REPORTS:
        report = root(name)
        for field in (
            "report_id",
            "report_version",
            "created_by_tool",
            "upstream_input_refs",
            "numeric_evidence_refs",
            "data_provenance_refs",
            "owning_agent",
            "downstream_consumers",
            "downstream_pr_refs",
            "validator_refs",
            "test_refs",
            "no_orphan_status",
            "terminal_by_nature_flag",
            "authority_class",
            "manual_edit_allowed_flag",
            "qku_sha_or_atomicrows_hash_authority_flag",
            "live_authority_created_flag",
            "profit_evidence_created_flag",
            "source_truth_acceptance_created_flag",
        ):
            expect(field in report, "PR168_GFP2_REPORT_METADATA_MISSING", f"{name} missing {field}")
        for flag in FORBIDDEN_TRUE_FLAGS:
            expect(report.get(flag) is False, "PR168_GFP2_FORBIDDEN_AUTHORITY", f"{name} {flag}")


def validate_counts() -> None:
    summary = load("PR168_GFP2_FinalSummary.report.json")[0]
    for key, expected in BASELINE_COUNTS.items():
        expect(summary.get(key) == expected, "PR168_GFP2_BASELINE_COUNT", f"{key} {summary.get(key)} != {expected}")
    expect(
        root("PR168_GFP2_AllQKUComputabilityClassificationLedger.report.json")["record_count"]
        == BASELINE_COUNTS["formula_assignment_count"],
        "PR168_GFP2_FULL_UNIVERSE_NOT_20387",
        "full universe ledger must cover formula assignment universe",
    )
    expect(
        root("PR168_GFP2_Selected35FormulaProvenance.report.json")["record_count"]
        == BASELINE_COUNTS["selected_formula_count"],
        "PR168_GFP2_SELECTED_FORMULA_COUNT",
        "selected formula count mismatch",
    )


def validate_no_real_positive_negative_without_accepted_data() -> None:
    proof = load("PR168_GFP2_RealPositiveNegativeProofLedger.report.json")
    expect(proof, "PR168_GFP2_PROOF_LEDGER_EMPTY", "proof ledger rows required")
    for row in proof[:1000]:
        expect(row["accepted_real_data_available_flag"] is False, "PR168_GFP2_ACCEPTED_DATA_UNEXPECTED", str(row.get("canonical_row_key")))
        expect(row["real_positive_claim_allowed_flag"] is False, "PR168_GFP2_FAKE_REAL_POSITIVE", str(row.get("canonical_row_key")))
        expect(row["real_negative_claim_allowed_flag"] is False, "PR168_GFP2_FAKE_REAL_NEGATIVE", str(row.get("canonical_row_key")))
        expect(row["proof_eligible_flag"] is False, "PR168_GFP2_FAKE_PROOF_ELIGIBLE", str(row.get("canonical_row_key")))


def validate_prior_supersession() -> None:
    rows = load("PR168_GFP2_PriorResultSupersessionLedger.report.json")
    expect(rows, "PR168_GFP2_PRIOR_SUPERSESSION_EMPTY", "prior correction rows required")
    for row in rows[:2000]:
        expect(row["historical_record_preserved_flag"] is True, "PR168_GFP2_PRIOR_NOT_PRESERVED", str(row))
        expect(row["supersedes_previous_authority_flag"] is True, "PR168_GFP2_PRIOR_NOT_SUPERSEDED", str(row))
        expect(row["requires_real_market_recompute_flag"] is True, "PR168_GFP2_PRIOR_NO_RECOMPUTE", str(row))
        expect(row["real_positive_claim_allowed_flag"] is False, "PR168_GFP2_PRIOR_POSITIVE_ALLOWED", str(row))
        expect(row["real_negative_claim_allowed_flag"] is False, "PR168_GFP2_PRIOR_NEGATIVE_ALLOWED", str(row))
        expect(row["champion_eligible"] is False, "PR168_GFP2_PRIOR_CHAMPION_ALLOWED", str(row))
        expect(row["live_candidate_worthy"] is False, "PR168_GFP2_PRIOR_LIVE_ALLOWED", str(row))
        expect(row["no_orphan_status"], "PR168_GFP2_PRIOR_ORPHAN", str(row))
    expect(load("PR168_GFP2_FakeNegativeReopenQueue.report.json"), "PR168_GFP2_FAKE_NEGATIVE_QUEUE_EMPTY", "fake negative reopen queue required")
    expect(load("PR168_GFP2_FakeNeutralZeroNoTradeReopenQueue.report.json"), "PR168_GFP2_FAKE_NEUTRAL_QUEUE_EMPTY", "fake neutral/no-trade queue required")


def validate_zero_positive_not_final() -> None:
    row = load("PR168_GFP2_ZeroPositiveNotFinalTruthAudit.report.json")[0]
    expect(row["zero_positive_final_truth_allowed_flag"] is False, "PR168_GFP2_ZERO_POSITIVE_FINAL", str(row))
    expect(row["zero_positive_result_label"] == "0_REAL_POSITIVES_PROVEN_WITH_ACCEPTED_DATA", "PR168_GFP2_ZERO_LABEL", str(row))


def validate_gap_repair_recovery() -> None:
    gaps = load("PR168_GFP2_GapRoutedUniverseRepairQueue.report.json")
    recovery = load("PR168_GFP2_NegativeToPositiveRecoveryOpportunityLedger.report.json")
    ladder = load("PR168_GFP2_NegativeCandidateRepairLadderQueue.report.json")
    expect(len(gaps) == BASELINE_COUNTS["formula_assignment_count"], "PR168_GFP2_GAP_COUNT", str(len(gaps)))
    expect(len(recovery) == BASELINE_COUNTS["formula_assignment_count"], "PR168_GFP2_RECOVERY_COUNT", str(len(recovery)))
    expect(len(ladder) == BASELINE_COUNTS["formula_assignment_count"], "PR168_GFP2_LADDER_COUNT", str(len(ladder)))
    for row in recovery[:1000]:
        expect(row["forced_positive_flag"] is False, "PR168_GFP2_FORCED_POSITIVE", str(row))
        expect(row["recovery_eligibility_state"].startswith("RECOVERY_ELIGIBLE"), "PR168_GFP2_RECOVERY_STATE", str(row))


def validate_quantum() -> None:
    rows = load("PR168_GFP2_QuantumStructuralReadinessFullUniverse.report.json")
    expect(len(rows) == BASELINE_COUNTS["formula_assignment_count"], "PR168_GFP2_QUANTUM_FULL_UNIVERSE", str(len(rows)))
    quantum = [row for row in rows if row["structural_readiness_state"] == "QUANTUM_STRUCTURAL_GAP_ROUTED"]
    expect(quantum, "PR168_GFP2_NO_QUANTUM_ROWS", "expected quantum-forward rows")
    for row in quantum[:1000]:
        expect(row["objective_exists"] is True, "PR168_GFP2_QUANTUM_OBJECTIVE_MISSING", str(row.get("qku_id")))
        expect(row["classical_fallback_exists"] is True, "PR168_GFP2_QUANTUM_FALLBACK_MISSING", str(row.get("qku_id")))
        expect(row["classical_comparator_exists"] is True, "PR168_GFP2_QUANTUM_COMPARATOR_MISSING", str(row.get("qku_id")))
        expect(row["backend_execution_flag"] is False, "PR168_GFP2_QUANTUM_BACKEND", str(row.get("qku_id")))
        expect(row["quantum_advantage_claim_flag"] is False, "PR168_GFP2_QUANTUM_ADVANTAGE", str(row.get("qku_id")))


def validate_agent_and_dag() -> None:
    roster = load("PR168_GFP2_AgentRosterDiscoveryAuditConsumption.report.json")
    duty = load("PR168_GFP2_AgentDutySourceCrosswalkConsumption.report.json")
    expect(roster and roster[0]["agent_ids"], "PR168_GFP2_AGENT_ROSTER_MISSING", str(roster))
    expect(duty and duty[0]["agent_ids"], "PR168_GFP2_AGENT_DUTY_MISSING", str(duty))
    no_orphan = load("PR168_GFP2_NoOrphanProof.report.json")
    expect(no_orphan, "PR168_GFP2_NO_ORPHAN_EMPTY", "no-orphan proof required")
    for row in no_orphan:
        expect(row["has_upstream_refs"] is True, "PR168_GFP2_NO_UPSTREAM", str(row))
        expect(row["has_downstream_consumers"] is True, "PR168_GFP2_NO_DOWNSTREAM", str(row))
        expect(row["has_agent_owner"] is True, "PR168_GFP2_NO_AGENT", str(row))
        expect(row["has_validator_refs"] is True, "PR168_GFP2_NO_VALIDATOR", str(row))
        expect(row["has_test_refs"] is True, "PR168_GFP2_NO_TEST", str(row))
    terminal = load("PR168_GFP2_TerminalArtifactExceptionLedger.report.json")
    expect(terminal and terminal[0]["terminal_reason_code"], "PR168_GFP2_TERMINAL_REASON", str(terminal))


def validate_optimizer_and_seeds() -> None:
    rows = load("PR168_GFP2_OptimizerDefaultAndParameterRangeSeed.report.json")
    expect(rows, "PR168_GFP2_OPTIMIZER_EMPTY", "optimizer defaults required")
    for row in rows:
        expect(row["source_tier"] == "GAP_ROUTED", "PR168_GFP2_OPTIMIZER_UNSOURCED_NOT_GAP", str(row))
        expect(row["accepted_truth_flag"] is False, "PR168_GFP2_OPTIMIZER_ACCEPTED", str(row))
        expect(row["repair_route_if_missing"], "PR168_GFP2_OPTIMIZER_NO_REPAIR", str(row))
    alpha = load("PR168_GFP2_AlphaCaptureMechanismRegistry.report.json")
    expect(alpha, "PR168_GFP2_ALPHA_EMPTY", "alpha seed rows required")
    for row in alpha:
        expect(row["creates_champion_or_live_authority_flag"] is False, "PR168_GFP2_ALPHA_LIVE", str(row))


def validate_nonofficial_sources() -> None:
    rows = load("PR168_GFP2_NonOfficialCandidateSourceLane.report.json")
    expect(rows, "PR168_GFP2_NONOFFICIAL_EMPTY", "non-official/institutional candidate lane required")
    for row in rows:
        expect(row["accepted_truth_flag"] is False, "PR168_GFP2_NONOFFICIAL_TRUTH", str(row))
        expect(row["candidate_only_flag"] is True, "PR168_GFP2_NONOFFICIAL_NOT_CANDIDATE", str(row))


def validate_handoffs() -> None:
    for filename in (
        "PR168_GFP2_To_PR168_RP2_RealMarketReplayRecompute.report.json",
        "PR168_GFP2_To_PR168_RANK2_ProvenanceAwareRankingSeed.report.json",
        "PR168_GFP2_To_PR162E_PluginIntakeCandidateQueue.report.json",
        "PR168_GFP2_To_PR162D_R3_ExternalAcquisitionRepairQueue.report.json",
        "PR168_GFP2_To_PR165_B_NegativeMemorySeed.report.json",
        "PR168_GFP2_To_PR167_OpenTradeCombinationReadiness.report.json",
        "PR168_GFP2_To_RuntimeFormulaAllowlistHotPathCacheSeed.report.json",
        "PR168_GFP2_To_DashboardFormulaTradeControlSeed.report.json",
    ):
        expect(load(filename), "PR168_GFP2_HANDOFF_EMPTY", filename)


def validate_windows_linux() -> None:
    paths = list((REPO_ROOT / GENERATED_DIR).glob("PR168_GFP2_*.report.json"))
    paths += list((REPO_ROOT / GENERATED_DIR / "pr168_gfp2_shards").glob("PR168_GFP2_*.report.json"))
    lowered: dict[str, Path] = {}
    for path in paths:
        key = path.relative_to(REPO_ROOT).as_posix().lower()
        expect(key not in lowered, "PR168_GFP2_PATH_CASE_COLLISION", str(path))
        lowered[key] = path
        payload = json.loads(path.read_text(encoding="utf-8"))
        for value in _walk(payload):
            if isinstance(value, float):
                expect(math.isfinite(value), "PR168_GFP2_NONFINITE_FLOAT", str(path))


def validate_generic() -> None:
    validate_reports_exist()
    validate_counts()
    validate_no_real_positive_negative_without_accepted_data()
    validate_prior_supersession()
    validate_zero_positive_not_final()
    validate_gap_repair_recovery()
    validate_quantum()
    validate_agent_and_dag()
    validate_optimizer_and_seeds()
    validate_nonofficial_sources()
    validate_handoffs()
    validate_windows_linux()


VALIDATORS: dict[str, Callable[[], None]] = {
    "full_universe": validate_generic,
    "real_data_proof": validate_no_real_positive_negative_without_accepted_data,
    "prior_supersession": validate_prior_supersession,
    "zero_positive": validate_zero_positive_not_final,
    "recovery": validate_gap_repair_recovery,
    "quantum": validate_quantum,
    "agent_dag": validate_agent_and_dag,
    "optimizer": validate_optimizer_and_seeds,
    "sources": validate_nonofficial_sources,
    "handoffs": validate_handoffs,
    "windows_linux": validate_windows_linux,
}


def run_validation(mode: str = "generic") -> None:
    key = mode
    if key.startswith("validate_pr168_gfp2_"):
        key = key.removeprefix("validate_pr168_gfp2_")
    if key.endswith(".py"):
        key = key[:-3]
    validator = VALIDATORS.get(key, validate_generic)
    validator()
    print(f"PR168_GFP2_VALIDATION_OK {key}")


def _walk(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)
    else:
        yield value


def main(script_name: str | None = None) -> int:
    mode = script_name or Path(sys.argv[0]).stem
    run_validation(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
