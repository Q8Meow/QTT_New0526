"""Internal immutable value models for the computation control plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Iterable, Mapping


JSONScalar = str | int | float | bool | None


def _freeze(value: Any) -> Any:
    """Recursively freeze caller-owned containers without changing scalars."""

    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ComputationRecordV1:
    """The sole persistent logical-registry row type.

    It is an immutable value wrapper, not a registry/service authority.  JSONL
    serialization remains the canonical physical representation.
    """

    canonical_component_id: str
    semantic_version: str
    record_state: str
    origin_cohorts: tuple[str, ...]
    definition: Mapping[str, Any]
    uses: Mapping[str, Any]
    bindings: tuple[Mapping[str, Any], ...]
    provenance: tuple[Mapping[str, Any], ...]
    relations: tuple[Mapping[str, Any], ...]
    governance: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "origin_cohorts", tuple(str(value) for value in self.origin_cohorts)
        )
        object.__setattr__(self, "definition", _freeze(self.definition))
        object.__setattr__(self, "uses", _freeze(self.uses))
        object.__setattr__(self, "bindings", tuple(_freeze(value) for value in self.bindings))
        object.__setattr__(
            self, "provenance", tuple(_freeze(value) for value in self.provenance)
        )
        object.__setattr__(self, "relations", tuple(_freeze(value) for value in self.relations))
        object.__setattr__(self, "governance", _freeze(self.governance))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ComputationRecordV1":
        return cls(
            canonical_component_id=str(value["canonical_component_id"]),
            semantic_version=str(value["semantic_version"]),
            record_state=str(value["record_state"]),
            origin_cohorts=tuple(value["origin_cohorts"]),
            definition=value["definition"],
            uses=value["uses"],
            bindings=tuple(value["bindings"]),
            provenance=tuple(value["provenance"]),
            relations=tuple(value["relations"]),
            governance=value["governance"],
        )

    def as_dict(self) -> dict[str, Any]:
        return _thaw(self.__dict__)


@dataclass(frozen=True)
class ExpansionBatchV1:
    """The sole typed build-time intake for computation expansion."""

    batch_id: str
    batch_origin: str
    submitted_by: str
    submission_time: str
    source_refs: tuple[str, ...]
    source_classification: str
    intended_market_venue_modes: tuple[Mapping[str, Any], ...]
    items: tuple[Mapping[str, Any], ...]
    requested_evidence_modes: tuple[str, ...] = ()
    requested_promotion_ceiling: str = "SPECIFIED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_refs", tuple(str(item) for item in self.source_refs))
        object.__setattr__(
            self,
            "intended_market_venue_modes",
            tuple(_freeze(item) for item in self.intended_market_venue_modes),
        )
        object.__setattr__(self, "items", tuple(_freeze(item) for item in self.items))
        object.__setattr__(
            self,
            "requested_evidence_modes",
            tuple(str(item) for item in self.requested_evidence_modes),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExpansionBatchV1":
        return cls(
            batch_id=str(value["batch_id"]),
            batch_origin=str(value["batch_origin"]),
            submitted_by=str(value["submitted_by"]),
            submission_time=str(value["submission_time"]),
            source_refs=tuple(str(item) for item in value.get("source_refs", ())),
            source_classification=str(value.get("source_classification", "OWNER_SUBMITTED")),
            intended_market_venue_modes=tuple(value.get("intended_market_venue_modes", ())),
            items=tuple(value.get("items", ())),
            requested_evidence_modes=tuple(value.get("requested_evidence_modes", ())),
            requested_promotion_ceiling=str(value.get("requested_promotion_ceiling", "SPECIFIED")),
        )

    def as_dict(self) -> dict[str, Any]:
        return _thaw(
            {
                "batch_id": self.batch_id,
                "batch_origin": self.batch_origin,
                "submitted_by": self.submitted_by,
                "submission_time": self.submission_time,
                "source_refs": self.source_refs,
                "source_classification": self.source_classification,
                "intended_market_venue_modes": self.intended_market_venue_modes,
                "items": self.items,
                "requested_evidence_modes": self.requested_evidence_modes,
                "requested_promotion_ceiling": self.requested_promotion_ceiling,
            }
        )


@dataclass(frozen=True)
class RegistryUpdateV1:
    """Transient changed-component delta; never a persistent event record."""

    batch_id: str
    registry_schema_version: str
    added_component_ids: tuple[str, ...] = ()
    changed_component_ids: tuple[str, ...] = ()
    retired_component_ids: tuple[str, ...] = ()
    added_binding_ids: tuple[str, ...] = ()
    changed_binding_ids: tuple[str, ...] = ()
    removed_binding_ids: tuple[str, ...] = ()
    affected_dependent_ids: tuple[str, ...] = ()
    affected_consumer_classes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "added_component_ids",
            "changed_component_ids",
            "retired_component_ids",
            "added_binding_ids",
            "changed_binding_ids",
            "removed_binding_ids",
            "affected_dependent_ids",
            "affected_consumer_classes",
        ):
            values = tuple(sorted({str(item) for item in getattr(self, field_name)}))
            object.__setattr__(self, field_name, values)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RegistryUpdateV1":
        return cls(
            batch_id=str(value.get("batch_id", "IN_PROCESS_UPDATE")),
            registry_schema_version=str(value.get("registry_schema_version", "1.0")),
            added_component_ids=tuple(value.get("added_component_ids", ())),
            changed_component_ids=tuple(value.get("changed_component_ids", ())),
            retired_component_ids=tuple(value.get("retired_component_ids", ())),
            added_binding_ids=tuple(value.get("added_binding_ids", ())),
            changed_binding_ids=tuple(value.get("changed_binding_ids", ())),
            removed_binding_ids=tuple(value.get("removed_binding_ids", ())),
            affected_dependent_ids=tuple(value.get("affected_dependent_ids", ())),
            affected_consumer_classes=tuple(value.get("affected_consumer_classes", ())),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "registry_schema_version": self.registry_schema_version,
            "added_component_ids": list(self.added_component_ids),
            "changed_component_ids": list(self.changed_component_ids),
            "retired_component_ids": list(self.retired_component_ids),
            "added_binding_ids": list(self.added_binding_ids),
            "changed_binding_ids": list(self.changed_binding_ids),
            "removed_binding_ids": list(self.removed_binding_ids),
            "affected_dependent_ids": list(self.affected_dependent_ids),
            "affected_consumer_classes": list(self.affected_consumer_classes),
        }

    @property
    def affected_component_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                set(self.added_component_ids)
                | set(self.changed_component_ids)
                | set(self.retired_component_ids)
                | set(self.affected_dependent_ids)
            )
        )


@dataclass(frozen=True)
class ResolvedNodeV1:
    node_id: str
    canonical_component_id: str
    semantic_version: str
    binding_id: str
    implementation_version: str
    callable_or_solver_ref: str
    parameter_policy: Mapping[str, Any]
    context: Mapping[str, Any]
    requirement_inputs: tuple[Mapping[str, Any], ...]
    definition: Mapping[str, Any]
    binding: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameter_policy", _freeze(self.parameter_policy))
        object.__setattr__(self, "context", _freeze(self.context))
        object.__setattr__(self, "requirement_inputs", tuple(_freeze(item) for item in self.requirement_inputs))
        object.__setattr__(self, "definition", _freeze(self.definition))
        object.__setattr__(self, "binding", _freeze(self.binding))

    def as_dict(self) -> dict[str, Any]:
        return _thaw(self.__dict__)


@dataclass(frozen=True)
class ResolvedDecisionPlanV1:
    """One request-pinned, in-memory requirements plan."""

    plan_id: str
    generation: int
    root_component_id: str
    root_semantic_version: str
    root_binding_id: str
    decision_roles: tuple[str, ...]
    context: Mapping[str, Any]
    topological_nodes: tuple[ResolvedNodeV1, ...]
    blockers: tuple[str, ...] = ()
    fallback_paths: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_roles", tuple(str(item) for item in self.decision_roles))
        object.__setattr__(self, "context", _freeze(self.context))
        object.__setattr__(self, "topological_nodes", tuple(self.topological_nodes))
        object.__setattr__(self, "blockers", tuple(str(item) for item in self.blockers))
        object.__setattr__(self, "fallback_paths", tuple(_freeze(item) for item in self.fallback_paths))

    @property
    def ready(self) -> bool:
        return not self.blockers

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "generation": self.generation,
            "root_component_id": self.root_component_id,
            "root_semantic_version": self.root_semantic_version,
            "root_binding_id": self.root_binding_id,
            "decision_roles": list(self.decision_roles),
            "context": _thaw(self.context),
            "topological_execution_order": [node.node_id for node in self.topological_nodes],
            "nodes": [node.as_dict() for node in self.topological_nodes],
            "blockers": list(self.blockers),
            "fallback_paths": _thaw(self.fallback_paths),
            "persistent": False,
        }


@dataclass(frozen=True)
class ComputationReceiptV1:
    """Typed non-authoritative execution receipt graph."""

    receipt_id: str
    plan_id: str
    generation: int
    component_id: str
    decision_roles: tuple[str, ...]
    context_lock: Mapping[str, Any]
    input_values: Mapping[str, Any]
    input_lineage: Mapping[str, Any]
    requirement_receipts: tuple[Mapping[str, Any], ...]
    selected_versions: Mapping[str, Any]
    started_at: str
    ended_at: str
    latency_ms: float
    outputs: Mapping[str, Any]
    output_units: Mapping[str, Any]
    output_accounting_class: str
    fallback_used: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    consumer: str
    mode: str
    nodes_executed: int
    shared_invocations_reused: int
    no_order_authority: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "context_lock",
            "input_values",
            "input_lineage",
            "selected_versions",
            "outputs",
            "output_units",
        ):
            object.__setattr__(self, field_name, _freeze(getattr(self, field_name)))
        object.__setattr__(self, "requirement_receipts", tuple(_freeze(item) for item in self.requirement_receipts))
        object.__setattr__(self, "decision_roles", tuple(str(item) for item in self.decision_roles))
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(self, "errors", tuple(str(item) for item in self.errors))

    def as_dict(self) -> dict[str, Any]:
        return _thaw(self.__dict__)


class ComputationControlError(RuntimeError):
    """Typed fail-closed error raised by the public facade."""

    def __init__(self, code: str, detail: str, *, component_id: str | None = None) -> None:
        self.code = str(code)
        self.detail = str(detail)
        self.component_id = component_id
        super().__init__(f"{self.code}: {self.detail}")

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "component_id": self.component_id}


def json_compatible(value: Any) -> Any:
    """Convert immutable/Decimal DTO content for stable JSON output."""

    value = _thaw(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_compatible(item) for item in value]
    return value


def immutable_records(records: Iterable[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    return tuple(_freeze(record) for record in records)
