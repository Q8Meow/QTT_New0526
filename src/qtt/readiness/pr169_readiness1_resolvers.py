"""Thin READINESS1 resolver views.

The resolver reads only the PR169-READINESS1 canonical registry and derived
projections. It deliberately does not scan upstream generated JSONL at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


GENERATED_PREFIX = Path("docs/master_plan/generated/pr169_readiness1")
REGISTRY_NAME = "agent_readiness_registry.jsonl"


@dataclass(frozen=True)
class ReadinessView:
    rows: tuple[dict[str, Any], ...]

    def by_candidate(self, candidate_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(row for row in self.rows if row.get("candidate_id") == candidate_id)

    def ids(self) -> tuple[str, ...]:
        return tuple(str(row.get("candidate_id")) for row in self.rows)


class AgentAccessContractV1(ReadinessView):
    pass


class Stage1AgentComputationUniverseV1(ReadinessView):
    pass


class QKUAccessResolverV1(ReadinessView):
    def qku_refs(self, candidate_id: str) -> tuple[str, ...]:
        refs: list[str] = []
        for row in self.by_candidate(candidate_id):
            refs.extend(str(ref) for ref in row.get("qku_refs", []))
        return tuple(dict.fromkeys(refs))


class FormulaAccessResolverV1(ReadinessView):
    def formula_refs(self, candidate_id: str) -> tuple[str, ...]:
        refs: list[str] = []
        for row in self.by_candidate(candidate_id):
            refs.extend(str(ref) for ref in row.get("formula_refs", []))
        return tuple(dict.fromkeys(refs))


class CandidateReadinessResolverV1(ReadinessView):
    def executable_now_candidates(self) -> tuple[str, ...]:
        return tuple(
            str(row["candidate_id"])
            for row in self.rows
            if row.get("executable_now_state") == "EXECUTABLE_NOW_NONLIVE_SAFE"
        )


class ExecutableNowCurrentStateV1(ReadinessView):
    pass


class PaperLoopUsableCandidateSetV1(ReadinessView):
    pass


class AdapterBlockedCandidateSetV1(ReadinessView):
    pass


class AdapterUnlockQueueV1(ReadinessView):
    pass


class AgentConsumerRouteMapV1(ReadinessView):
    pass


class LLMConsumerViewContractV1(ReadinessView):
    pass


class LLMGroundingViewV1(ReadinessView):
    pass


class OwnerCommandRouteViewV1(ReadinessView):
    pass


class OwnerPlainEnglishIntentRouteViewV1(ReadinessView):
    pass


class OwnerChatActionCatalogRouteViewV1(ReadinessView):
    pass


class SurfaceParityHandoffViewV1(ReadinessView):
    pass


class OwnerUXSemanticBundleHandoffViewV1(ReadinessView):
    pass


class PluginIntakeHandoffViewV1(ReadinessView):
    pass


class MetricsRouteAliasViewV1(ReadinessView):
    pass


class AgentKPITrustQuarantineHandoffViewV1(ReadinessView):
    pass


class QKUFormulaAgentComputeMapViewV1(ReadinessView):
    pass


class TradeVariableSearchHandoffViewV1(ReadinessView):
    pass


class EdgeAlphaDecisionReadinessViewV1(ReadinessView):
    pass


class OrderScenarioTournamentHandoffViewV1(ReadinessView):
    pass


class ShadowComparisonHandoffViewV1(ReadinessView):
    pass


class ExecutionRouterActionHandoffViewV1(ReadinessView):
    pass


class ConnectorRouteHandoffViewV1(ReadinessView):
    pass


class AgentLearningHandoffViewV1(ReadinessView):
    pass


class SourceCoverageHandoffViewV1(ReadinessView):
    pass


class ParameterOperabilityHandoffViewV1(ReadinessView):
    pass


class OwnerEnablementHandoffViewV1(ReadinessView):
    pass


@dataclass(frozen=True)
class OwnerThreeQuestionCoverageReportV1:
    payload: dict[str, Any]

    @property
    def acceptance_state(self) -> str:
        return str(self.payload.get("acceptance_state", "FAIL"))


@dataclass(frozen=True)
class NoRawJsonlRuntimeScanReportV1:
    payload: dict[str, Any]

    @property
    def blocked_paths(self) -> tuple[str, ...]:
        return tuple(str(path) for path in self.payload.get("blocked_paths", []))


def _repo_root(repo_root: Path | str | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    return Path(__file__).resolve().parents[3]


def _artifact_path(name: str, repo_root: Path | str | None = None) -> Path:
    path = _repo_root(repo_root) / GENERATED_PREFIX / name
    resolved_prefix = (_repo_root(repo_root) / GENERATED_PREFIX).resolve()
    resolved_path = path.resolve()
    if resolved_prefix not in (resolved_path, *resolved_path.parents):
        raise ValueError(f"artifact path escapes READINESS1 prefix: {name}")
    return path


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return tuple(rows)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def load_projection(
    name: str,
    *,
    repo_root: Path | str | None = None,
) -> tuple[dict[str, Any], ...]:
    path = _artifact_path(name, repo_root)
    return _read_jsonl(path)


def load_registry(*, repo_root: Path | str | None = None) -> CandidateReadinessResolverV1:
    return CandidateReadinessResolverV1(load_projection(REGISTRY_NAME, repo_root=repo_root))


def load_agent_universe(*, repo_root: Path | str | None = None) -> Stage1AgentComputationUniverseV1:
    return Stage1AgentComputationUniverseV1(
        load_projection("agent_universe.generated.jsonl", repo_root=repo_root)
    )


def load_qku_resolver(*, repo_root: Path | str | None = None) -> QKUAccessResolverV1:
    return QKUAccessResolverV1(load_projection(REGISTRY_NAME, repo_root=repo_root))


def load_formula_resolver(*, repo_root: Path | str | None = None) -> FormulaAccessResolverV1:
    return FormulaAccessResolverV1(load_projection(REGISTRY_NAME, repo_root=repo_root))


def load_owner_three_question_report(
    *,
    repo_root: Path | str | None = None,
) -> OwnerThreeQuestionCoverageReportV1:
    return OwnerThreeQuestionCoverageReportV1(
        _read_json(_artifact_path("owner_three_question_coverage.report.json", repo_root))
    )


def load_no_raw_jsonl_scan_report(
    *,
    repo_root: Path | str | None = None,
) -> NoRawJsonlRuntimeScanReportV1:
    return NoRawJsonlRuntimeScanReportV1(
        _read_json(_artifact_path("no_raw_jsonl_scan.report.json", repo_root))
    )


def candidate_route_refs(
    candidate_id: str,
    *,
    repo_root: Path | str | None = None,
) -> tuple[str, ...]:
    registry = load_registry(repo_root=repo_root)
    refs: list[str] = []
    for row in registry.by_candidate(candidate_id):
        refs.extend(str(ref) for ref in row.get("downstream_consumer_refs", []))
    return tuple(dict.fromkeys(refs))


def iter_candidate_rows(
    *,
    repo_root: Path | str | None = None,
) -> Iterable[dict[str, Any]]:
    return iter(load_registry(repo_root=repo_root).rows)

