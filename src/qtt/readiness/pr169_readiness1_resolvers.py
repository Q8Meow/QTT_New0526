"""Thin READINESS1 resolver views.

The resolver reads only the PR169-READINESS1 canonical registry and derived
projections. It deliberately does not scan upstream generated JSONL at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

try:
    from qtt.computation_control import QKUComputationControlPlaneV1
except ModuleNotFoundError:  # repository-root ``src.qtt`` test/import mode
    from src.qtt.computation_control import QKUComputationControlPlaneV1


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


_REGISTRY_UPDATE_FIELDS = frozenset(
    {
        "batch_id",
        "registry_schema_version",
        "added_component_ids",
        "changed_component_ids",
        "retired_component_ids",
        "added_binding_ids",
        "changed_binding_ids",
        "removed_binding_ids",
        "affected_dependent_ids",
        "affected_consumer_classes",
    }
)
_REGISTRY_UPDATE_ID_FIELDS = (
    "added_component_ids",
    "changed_component_ids",
    "retired_component_ids",
    "added_binding_ids",
    "changed_binding_ids",
    "removed_binding_ids",
    "affected_dependent_ids",
)
_REGISTRY_UPDATE_ALIASES = {
    "added": "added_component_ids",
    "changed": "changed_component_ids",
    "retired": "retired_component_ids",
    "binding": "changed_binding_ids",
    "affected_consumers": "affected_consumer_classes",
}


def _registry_update(update: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(update, Mapping):
        raise TypeError("registry_update must be a transient Mapping")
    unknown = set(update) - _REGISTRY_UPDATE_FIELDS - set(_REGISTRY_UPDATE_ALIASES)
    if unknown:
        raise ValueError(f"unsupported registry_update fields: {sorted(unknown)}")

    normalized: dict[str, Any] = {
        "batch_id": update.get("batch_id"),
        "registry_schema_version": update.get("registry_schema_version"),
    }
    for field in (*_REGISTRY_UPDATE_ID_FIELDS, "affected_consumer_classes"):
        source = update.get(field, ())
        if not source:
            for alias, canonical in _REGISTRY_UPDATE_ALIASES.items():
                if canonical == field and alias in update:
                    source = update[alias]
                    break
        if isinstance(source, (str, bytes)) or not isinstance(source, Iterable):
            raise TypeError(f"registry_update field {field} must be an iterable of IDs")
        normalized[field] = tuple(dict.fromkeys(str(value) for value in source))
    return normalized


def _selector_values(selector: str | Mapping[str, Any]) -> frozenset[str]:
    if isinstance(selector, str):
        return frozenset({selector})
    if not isinstance(selector, Mapping):
        raise TypeError("selector must be a string or Mapping")

    values: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, str):
            values.add(value)
        elif isinstance(value, Mapping):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            for nested in value:
                collect(nested)

    collect(selector)
    return frozenset(values)


def project_computation_status(
    control_plane: QKUComputationControlPlaneV1,
    selectors: str | Mapping[str, Any] | Iterable[str | Mapping[str, Any]],
    context: Mapping[str, Any] | None = None,
    *,
    agent_id: str | None = None,
    registry_update: Mapping[str, Any] | None = None,
    consumer_class: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Project public status only for IDs/classes affected by a transient delta."""

    update = _registry_update(registry_update) if registry_update is not None else None
    affected_ids = (
        frozenset(
            value
            for field in _REGISTRY_UPDATE_ID_FIELDS
            for value in update[field]
        )
        if update is not None
        else frozenset()
    )
    affected_consumers = (
        frozenset(update["affected_consumer_classes"])
        if update is not None
        else frozenset()
    )

    selector_rows = (
        (selectors,)
        if isinstance(selectors, (str, Mapping))
        else selectors
    )
    seen_selectors: set[str] = set()
    projected: list[dict[str, Any]] = []
    for selector in selector_rows:
        selector_key = (
            selector
            if isinstance(selector, str)
            else json.dumps(dict(selector), sort_keys=True, separators=(",", ":"), default=str)
        )
        if selector_key in seen_selectors:
            continue
        seen_selectors.add(selector_key)
        if update is not None and not (_selector_values(selector) & affected_ids):
            continue
        if consumer_class is not None and affected_consumers and consumer_class not in affected_consumers:
            continue
        public_selector: str | dict[str, Any]
        public_selector = dict(selector) if isinstance(selector, Mapping) else selector
        projected.append(
            {
                "selector": public_selector,
                "status": dict(control_plane.status(selector, context, agent_id=agent_id)),
            }
        )
    return tuple(projected)


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

