"""Load PR165-D selected batches and candidate context for PR166-S."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import group_by, index_by, load_report_records, row_contract


@dataclass(frozen=True)
class ExecutionContext:
    index: int
    retest: dict[str, Any]
    candidate: dict[str, Any]
    batch: dict[str, Any]
    repair: dict[str, Any] | None
    score: dict[str, Any]
    quantum: dict[str, Any]
    condition: dict[str, Any]
    expected: dict[str, Any]
    tca: dict[str, Any]
    latency: dict[str, Any]
    scenario: dict[str, Any]
    selection_fdc: dict[str, Any]
    selection_pit: dict[str, Any]

    @property
    def candidate_packet_id(self) -> str:
        return str(self.retest["candidate_packet_id"])

    @property
    def qku_id(self) -> str:
        return str(self.retest["qku_id"])

    @property
    def batch_id(self) -> str:
        return str(self.retest["batch_id"])

    @property
    def ready(self) -> bool:
        return self.retest.get("ready_execution_batch_flag") is True

    @property
    def repair_required(self) -> bool:
        return self.repair is not None or self.retest.get("batch_stream") == "REPAIR_BEFORE_RETEST"


@dataclass(frozen=True)
class LoadedSelection:
    contexts: list[ExecutionContext]
    batch_rows: list[dict[str, Any]]
    candidate_rows: list[dict[str, Any]]
    retest_rows: list[dict[str, Any]]
    repair_rows: list[dict[str, Any]]
    quantum_rows: list[dict[str, Any]]


def load_selected_contexts(repo_root: Path) -> LoadedSelection:
    retest_rows = load_report_records(repo_root, "PR165_D_RetestBatchSelectionQueue.report.json")
    repair_rows = load_report_records(repo_root, "PR165_D_RepairBeforeRetestSelectionQueue.report.json")
    candidate_rows = load_report_records(repo_root, "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json")
    batch_rows = load_report_records(repo_root, "PR165_D_BatchExposureCapacityLedger.report.json")
    score_rows = load_report_records(repo_root, "PR165_D_SelectionScoreRegistry.report.json")
    quantum_rows = load_report_records(repo_root, "PR165_D_QuantumSelectionRouter.report.json")
    selection_fdc_rows = load_report_records(repo_root, "PR165_D_SelectionFalseDiscoveryControl.report.json")
    selection_pit_rows = load_report_records(repo_root, "PR165_D_PointInTimeSelectionAudit.report.json")
    condition_rows = load_report_records(repo_root, "PR165_C_ConditionRegimeFeatureMatrix.report.json")
    expected_rows = load_report_records(repo_root, "PR165_ExpectedValueScoreRegistry.report.json")
    tca_rows = load_report_records(repo_root, "PR165_TCAAdjustedScoreRegistry.report.json")
    latency_rows = load_report_records(repo_root, "PR165_LatencyLaneAssignmentRegistry.report.json")
    scenario_rows = load_report_records(repo_root, "PR165_B_ScenarioOutcomeMatrix.report.json")

    by_candidate = index_by(candidate_rows, "candidate_packet_id")
    repair_by_candidate = index_by(repair_rows, "candidate_packet_id")
    score_by_candidate = index_by(score_rows, "candidate_packet_id")
    quantum_by_candidate = index_by(quantum_rows, "candidate_packet_id")
    condition_by_candidate = index_by(condition_rows, "candidate_packet_id")
    expected_by_candidate = index_by(expected_rows, "candidate_packet_id")
    tca_by_candidate = index_by(tca_rows, "candidate_packet_id")
    latency_by_candidate = index_by(latency_rows, "candidate_packet_id")
    scenario_by_candidate = index_by(scenario_rows, "candidate_packet_id")
    fdc_by_candidate = index_by(selection_fdc_rows, "candidate_packet_id")
    pit_by_candidate = index_by(selection_pit_rows, "candidate_packet_id")
    batch_by_id = index_by(batch_rows, "batch_id")

    contexts: list[ExecutionContext] = []
    for index, retest in enumerate(retest_rows, start=1):
        candidate_id = str(retest["candidate_packet_id"])
        contexts.append(
            ExecutionContext(
                index=index,
                retest=retest,
                candidate=by_candidate.get(candidate_id, {}),
                batch=batch_by_id.get(str(retest["batch_id"]), {}),
                repair=repair_by_candidate.get(candidate_id),
                score=score_by_candidate.get(candidate_id, {}),
                quantum=quantum_by_candidate.get(candidate_id, {}),
                condition=condition_by_candidate.get(candidate_id, {}),
                expected=expected_by_candidate.get(candidate_id, {}),
                tca=tca_by_candidate.get(candidate_id, {}),
                latency=latency_by_candidate.get(candidate_id, {}),
                scenario=scenario_by_candidate.get(candidate_id, {}),
                selection_fdc=fdc_by_candidate.get(candidate_id, {}),
                selection_pit=pit_by_candidate.get(candidate_id, {}),
            )
        )
    return LoadedSelection(contexts, batch_rows, candidate_rows, retest_rows, repair_rows, quantum_rows)


def ready_contexts(contexts: list[ExecutionContext]) -> list[ExecutionContext]:
    return [context for context in contexts if context.ready]


def repair_contexts(contexts: list[ExecutionContext]) -> list[ExecutionContext]:
    return [context for context in contexts if not context.ready]


def contexts_by_batch(contexts: list[ExecutionContext]) -> dict[str, list[ExecutionContext]]:
    return group_by_contexts(contexts, "batch_id")


def group_by_contexts(contexts: list[ExecutionContext], attr: str) -> dict[str, list[ExecutionContext]]:
    grouped: dict[str, list[ExecutionContext]] = {}
    for context in contexts:
        grouped.setdefault(str(getattr(context, attr)), []).append(context)
    return grouped


def build_selected_batch_consumption_rows(selection: LoadedSelection) -> list[dict[str, Any]]:
    contexts = selection.contexts
    by_batch = contexts_by_batch(contexts)
    stream_counts = Counter(context.retest.get("batch_stream") for context in contexts)
    rows: list[dict[str, Any]] = []
    for index, batch in enumerate(sorted(selection.batch_rows, key=lambda row: str(row["batch_id"])), start=1):
        batch_id = str(batch["batch_id"])
        members = by_batch.get(batch_id, [])
        ready_count = sum(1 for context in members if context.ready)
        repair_count = sum(1 for context in members if not context.ready)
        row_id = ordinal_ref("PR166_S_SELECTED_BATCH_CONSUMPTION", index)
        rows.append(
            {
                "selected_batch_consumption_id": row_id,
                "source_selected_batch_id": batch_id,
                "batch_id": batch_id,
                "source_pr165_d_batch_ref": batch.get("exposure_capacity_ledger_ref", batch_id),
                "scenario_group_id": batch.get("scenario_group_id", ""),
                "target_retest_mode": batch.get("target_retest_mode", "BOTH"),
                "selected_candidate_count": len(members),
                "ready_retest_candidate_count": ready_count,
                "repair_before_execution_candidate_count": repair_count,
                "batch_stream_distribution": dict(stream_counts),
                "consumption_status": "PR165_D_SELECTED_BATCH_CONSUMED",
                "execution_classification": (
                    "REPLAY_AND_PAPER_EXECUTED" if ready_count else "REPAIR_REQUIRED_BEFORE_EXECUTION"
                ),
                "no_raw_pr165_c_queue_bypass": True,
                "source_selected_batch_refs": [context.retest["retest_batch_selection_id"] for context in members[:50]],
                "downstream_replay_episode_ref": stable_ref("PR166_S_REPLAY_EPISODE", batch_id),
                "downstream_paper_episode_ref": stable_ref("PR166_S_PAPER_EPISODE", batch_id),
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_BatchExposureCapacityLedger.report.json",
                    source_row_ref=batch_id,
                    computed_by_module="selected_batch_loader",
                    owning_agent="selection_agent",
                    consuming_agent="replay_agent",
                    downstream_action_type="selected batch to replay/paper episode construction",
                    downstream_artifact_route="PR166_S_ReplayEpisodeRegistry.report.json",
                ),
            }
        )
    return rows


def numeric(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


def bucket_from_score(value: float, *, low: float = 0.33, high: float = 0.66) -> str:
    if value < low:
        return "LOW"
    if value > high:
        return "HIGH"
    return "MEDIUM"
