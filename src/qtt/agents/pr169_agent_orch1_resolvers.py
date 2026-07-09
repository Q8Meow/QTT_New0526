from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_agent_orch1")

JSONL_FILES = frozenset(
    {
        "registry.jsonl",
        "dag.jsonl",
        "dag_nodes.jsonl",
        "dag_edges.jsonl",
        "task_registry.jsonl",
        "task_queue.jsonl",
        "task_env.jsonl",
        "directives.jsonl",
        "workflows.jsonl",
        "handoffs.jsonl",
        "role_map.jsonl",
        "duty_map.jsonl",
        "perm_scope.jsonl",
        "retry_policy.jsonl",
        "priority_policy.jsonl",
        "quarantine.jsonl",
        "agent_ops.jsonl",
        "team_queue.jsonl",
        "intel_lanes.jsonl",
        "tournament_tasks.jsonl",
        "task_receipts.jsonl",
        "decision_receipts.jsonl",
        "dispute_receipts.jsonl",
        "escalation_receipts.jsonl",
        "handoff_receipts.jsonl",
        "audit_trail.jsonl",
        "svc1_bindings.jsonl",
        "readiness_bindings.jsonl",
        "pretrade_bindings.jsonl",
        "mem1_bindings.jsonl",
        "owner_cmd_tasks.jsonl",
        "chat_tasks.jsonl",
        "qku_tasks.jsonl",
        "formula_tasks.jsonl",
        "access_proof.jsonl",
        "library_receipts.jsonl",
        "graph_routes.jsonl",
        "graph_tasks.jsonl",
        "graph_quality.jsonl",
        "tradeplan_tasks.jsonl",
        "pretrade_tasks.jsonl",
        "mode_tasks.jsonl",
        "order_policy_tasks.jsonl",
        "paper_prep.jsonl",
        "hotpath_prep.jsonl",
        "shadow_prep.jsonl",
        "live_prep.jsonl",
        "rank_tasks.jsonl",
        "tca_tasks.jsonl",
        "fdr_tasks.jsonl",
        "portfolio_tasks.jsonl",
        "capacity_tasks.jsonl",
        "champion_tasks.jsonl",
        "mem_prior_tasks.jsonl",
        "utility_tasks.jsonl",
        "scenario_tasks.jsonl",
        "calibration_tasks.jsonl",
        "notrade_tasks.jsonl",
        "var_tune_tasks.jsonl",
        "stack_tasks.jsonl",
        "venue_side_tasks.jsonl",
        "source_refresh_tasks.jsonl",
        "retest_tasks.jsonl",
        "reality_tasks.jsonl",
        "metric_tasks.jsonl",
        "plugin_prep.jsonl",
        "qmap_prep.jsonl",
        "allow_prep.jsonl",
        "formula_intake.jsonl",
        "latency_tiers.jsonl",
        "clean_room.jsonl",
        "quantum_tasks.jsonl",
        "fallback_tasks.jsonl",
        "downstream.jsonl",
        "value_routes.jsonl",
        "capability_routes.jsonl",
        "learning_routes.jsonl",
    }
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return tuple(rows)


def _first(rows: Iterable[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    for row in rows:
        if str(row.get(key)) == value:
            return dict(row)
    raise KeyError(value)


def _candidate_match(row: dict[str, Any], candidate_id: str) -> bool:
    return candidate_id in {
        str(row.get("candidate_id") or ""),
        str(row.get("candidate_id_or_gap") or ""),
        str(row.get("current_trade_candidate_id_or_gap") or ""),
        str(row.get("candidate_ref") or ""),
    }


@dataclass(frozen=True)
class AgentOrchRows:
    rows: tuple[dict[str, Any], ...]


class AgentOrchRegistry(AgentOrchRows):
    pass


class AgentDAGRegistryV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentDAGNodeV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDAGEdgeV1:
    row: dict[str, Any]


class AgentTaskRegistryV1(AgentOrchRows):
    pass


class AgentTaskQueueV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentTaskEnvelopeV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDirectiveEnvelopeV1:
    row: dict[str, Any]


class AgentWorkflowRunV1(AgentOrchRows):
    pass


@dataclass(frozen=True)
class AgentHandoffPacketV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class RuntimeTaskReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDecisionReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentDisagreementReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentEscalationReceiptV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentNoTradeTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentQKUFormulaTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentLLMTaskContractV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentPaperPrepTaskV1:
    row: dict[str, Any]


@dataclass(frozen=True)
class AgentHotpathPrepTaskV1:
    row: dict[str, Any]


class AgentOrchService:
    """Thin read API over AGENT-ORCH1 generated contract artifacts."""

    def __init__(self, artifact_dir: str | Path | None = None, repo_root: str | Path | None = None) -> None:
        root = Path(repo_root) if repo_root is not None else _repo_root()
        self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else root / GENERATED_PREFIX
        if not self.artifact_dir.is_absolute():
            self.artifact_dir = root / self.artifact_dir

    def _jsonl(self, file_name: str) -> tuple[dict[str, Any], ...]:
        if file_name not in JSONL_FILES:
            raise KeyError(file_name)
        return _read_jsonl(self.artifact_dir / file_name)

    def load_manifest(self) -> dict[str, Any]:
        return json.loads((self.artifact_dir / "manifest.json").read_text(encoding="utf-8"))

    def list_dags(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("dag.jsonl")

    def get_dag(self, dag_id: str) -> dict[str, Any]:
        return _first(self.list_dags(), "dag_id", dag_id)

    def list_nodes(self, dag_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("dag_nodes.jsonl")
        if dag_id is None:
            return rows
        return tuple(row for row in rows if row.get("dag_id") == dag_id)

    def list_edges(self, dag_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("dag_edges.jsonl")
        if dag_id is None:
            return rows
        return tuple(row for row in rows if row.get("dag_id") == dag_id)

    def list_tasks(self, queue_id: str | None = None, task_class: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._jsonl("task_queue.jsonl")
        if queue_id is not None:
            rows = tuple(row for row in rows if row.get("queue_id") == queue_id)
        if task_class is not None:
            rows = tuple(row for row in rows if row.get("task_class") == task_class)
        return rows

    def get_task(self, task_id: str) -> dict[str, Any]:
        for file_name in ("task_queue.jsonl", "task_registry.jsonl"):
            for row in self._jsonl(file_name):
                if row.get("task_id") == task_id or row.get("task_ref") == task_id:
                    return dict(row)
        raise KeyError(task_id)

    def list_task_envelopes(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("task_env.jsonl")

    def get_task_envelope(self, task_id: str) -> dict[str, Any]:
        for row in self.list_task_envelopes():
            if row.get("task_id") == task_id or row.get("task_ref") == task_id:
                return dict(row)
        raise KeyError(task_id)

    def list_workflows(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("workflows.jsonl")

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return _first(self.list_workflows(), "workflow_id", workflow_id)

    def list_task_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("task_receipts.jsonl")

    def get_task_receipt(self, receipt_id: str) -> dict[str, Any]:
        for row in self.list_task_receipts():
            if row.get("receipt_ref_or_gap") == receipt_id or row.get("task_id") == receipt_id:
                return dict(row)
        raise KeyError(receipt_id)

    def list_decision_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("decision_receipts.jsonl")

    def list_dispute_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("dispute_receipts.jsonl")

    def list_escalation_receipts(self) -> tuple[dict[str, Any], ...]:
        return self._jsonl("escalation_receipts.jsonl")

    def get_owner_request_tasks(self, owner_action_ref: str) -> tuple[dict[str, Any], ...]:
        return tuple(
            row
            for row in self._jsonl("owner_cmd_tasks.jsonl")
            if row.get("owner_action_ref_or_gap") == owner_action_ref
        )

    def get_qku_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("qku_tasks.jsonl", candidate_id)

    def get_formula_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("formula_tasks.jsonl", candidate_id)

    def get_no_trade_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for file_name in (
            "notrade_tasks.jsonl",
            "var_tune_tasks.jsonl",
            "stack_tasks.jsonl",
            "venue_side_tasks.jsonl",
            "source_refresh_tasks.jsonl",
            "retest_tasks.jsonl",
        ):
            rows.extend(self._candidate_rows(file_name, candidate_id))
        return tuple(rows)

    def get_paper_prep(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("paper_prep.jsonl", candidate_id)

    def get_hotpath_prep(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("hotpath_prep.jsonl", candidate_id)

    def get_llm_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        rows = [
            row
            for row in self._jsonl("chat_tasks.jsonl") + self._jsonl("task_registry.jsonl")
            if _candidate_match(row, candidate_id) and row.get("llm_task_ref_or_gap")
        ]
        return tuple(rows)

    def get_quantum_tasks(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return self._candidate_rows("quantum_tasks.jsonl", candidate_id)

    def get_downstream_routes(self, task_id: str) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for file_name in ("downstream.jsonl", "value_routes.jsonl", "capability_routes.jsonl", "learning_routes.jsonl"):
            rows.extend(
                row
                for row in self._jsonl(file_name)
                if row.get("task_id") == task_id or row.get("task_ref") == task_id
            )
        if rows:
            return tuple(rows)
        task = self.get_task(task_id)
        return (
            {
                "task_id": task_id,
                "downstream_route_refs": tuple(task.get("downstream_route_refs") or ()),
                "authority_state": task.get("authority_state"),
                "runtime_side_effect_allowed": task.get("runtime_side_effect_allowed"),
            },
        )

    def _candidate_rows(self, file_name: str, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(row for row in self._jsonl(file_name) if _candidate_match(row, candidate_id))


class AgentOrchAPI(AgentOrchService):
    pass
