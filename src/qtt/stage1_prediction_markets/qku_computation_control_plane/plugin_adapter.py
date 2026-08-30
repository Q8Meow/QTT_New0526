"""Read-only adapters over the centralized generic plugin authorities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import json
from pathlib import Path

from src.qtt.plugins.contracts import (
    CompatibilityAndDependencyReceiptV1,
    PackageAdmissionStateV1,
    PackageValidationTerminalStateV1,
    SelectedComponentPackageManifestV1,
)
from src.qtt.plugins.registry import selected_component_package_projection_v1

from .errors import OwnerAdapterError, ReasonCode
from .models import NO_EFFECTS_V1, NoEffectFlagsV1
from .serialization import deterministic_json


PLUGIN_REPORT_PATH = Path(
    "docs/master_plan/generated/PR162E_PluginFamilyRegistry.report.json"
)


def _view_text(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MALFORMED,
            f"selected package {field_name} must be canonical text",
        )
    return value


def _view_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_MALFORMED,
            f"selected package {field_name} must be an exact text tuple",
        )
    for item in value:
        _view_text(item, field_name)
    if len(value) != len(set(value)):
        raise OwnerAdapterError(
            ReasonCode.OWNER_DATA_CONTRADICTORY,
            f"selected package {field_name} must be duplicate-free",
        )
    return value


class _DeterministicEmptyPathTuple(tuple[()]):
    """Preserve an empty path tuple through the existing QKU path guard."""

    def __new__(cls) -> _DeterministicEmptyPathTuple:
        return super().__new__(cls)

    def __bool__(self) -> bool:
        return True


class _DeterministicNonPathKey(str):
    """Keep an exact JSON key while disambiguating a non-path field."""

    def casefold(self) -> str:
        return f"{super().casefold()}_field"


def _qku_projection_serialization_key(key: str, value: object) -> str:
    lowered = key.casefold()
    if lowered.endswith(("_path", "_paths")) and not (
        value is None or isinstance(value, (str, tuple, list))
    ):
        return _DeterministicNonPathKey(key)
    return key


def _qku_projection_serialization_value(
    value: object,
    *,
    field_name: str = "",
) -> object:
    if isinstance(value, Enum):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            _qku_projection_serialization_key(
                field_definition.name,
                getattr(value, field_definition.name),
            ): _qku_projection_serialization_value(
                getattr(value, field_definition.name),
                field_name=field_definition.name,
            )
            for field_definition in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            _qku_projection_serialization_key(
                key,
                item,
            ): _qku_projection_serialization_value(item, field_name=key)
            for key, item in value.items()
        }
    if type(value) is tuple:
        if not value and field_name.casefold().endswith("_paths"):
            return _DeterministicEmptyPathTuple()
        return tuple(
            _qku_projection_serialization_value(item) for item in value
        )
    return value


@dataclass(frozen=True, slots=True)
class SelectedComponentPackageEntryViewV1:
    package_component_id: str
    launch_role_id: str
    admission_state: str
    compatibility_state: str
    compatibility_reason_codes: tuple[str, ...]
    plugin_family_refs: tuple[str, ...]
    required_operation_classes: tuple[str, ...]
    optional_operation_classes: tuple[str, ...]
    default_failure_route: str
    latency_class: str
    rollback_target_kind: str
    fallback_component_id_or_none: str | None

    def __post_init__(self) -> None:
        for name in (
            "package_component_id",
            "launch_role_id",
            "admission_state",
            "compatibility_state",
            "default_failure_route",
            "latency_class",
            "rollback_target_kind",
        ):
            _view_text(getattr(self, name), name)
        for name in (
            "compatibility_reason_codes",
            "plugin_family_refs",
            "required_operation_classes",
            "optional_operation_classes",
        ):
            _view_text_tuple(getattr(self, name), name)
        if set(self.required_operation_classes).intersection(
            self.optional_operation_classes
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "selected package operation memberships must be disjoint",
            )
        if self.fallback_component_id_or_none is not None:
            _view_text(
                self.fallback_component_id_or_none,
                "fallback_component_id_or_none",
            )


@dataclass(frozen=True, slots=True)
class SelectedComponentOperationViewV1:
    operation_class: str
    required_component_ids: tuple[str, ...]
    optional_component_ids: tuple[str, ...]
    blocking_component_ids: tuple[str, ...]
    state: str
    terminal_failure_route: str

    def __post_init__(self) -> None:
        for name in ("operation_class", "state", "terminal_failure_route"):
            _view_text(getattr(self, name), name)
        for name in (
            "required_component_ids",
            "optional_component_ids",
            "blocking_component_ids",
        ):
            _view_text_tuple(getattr(self, name), name)
        if (
            set(self.required_component_ids).intersection(
                self.optional_component_ids
            )
            or not set(self.blocking_component_ids).issubset(
                self.required_component_ids
            )
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "selected package operation sets are contradictory",
            )


@dataclass(frozen=True, slots=True)
class SelectedComponentPackageViewV1:
    package_id: str
    package_version: str
    entry_count: int
    admitted_count: int
    evidence_held_count: int
    implementation_held_count: int
    edge_count: int
    operation_count: int
    selected_profile_ids: tuple[str, ...]
    excluded_profile_ids: tuple[str, ...]
    active_live_profile_ids: tuple[str, ...]
    entries: tuple[SelectedComponentPackageEntryViewV1, ...]
    operations: tuple[SelectedComponentOperationViewV1, ...]
    source_owner: str
    source_package_ref: str
    canonical_projection_json: str
    no_effects: NoEffectFlagsV1

    def __post_init__(self) -> None:
        for name in (
            "package_id",
            "package_version",
            "source_owner",
            "source_package_ref",
            "canonical_projection_json",
        ):
            _view_text(getattr(self, name), name)
        for name in (
            "entry_count",
            "admitted_count",
            "evidence_held_count",
            "implementation_held_count",
            "edge_count",
            "operation_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"selected package {name} must be a nonnegative integer",
                )
        for name in (
            "selected_profile_ids",
            "excluded_profile_ids",
            "active_live_profile_ids",
        ):
            _view_text_tuple(getattr(self, name), name)
        if type(self.entries) is not tuple or any(
            type(entry) is not SelectedComponentPackageEntryViewV1
            for entry in self.entries
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "selected package entries must use the exact view type",
            )
        if type(self.operations) is not tuple or any(
            type(operation) is not SelectedComponentOperationViewV1
            for operation in self.operations
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "selected package operations must use the exact view type",
            )
        if (
            self.entry_count != len(self.entries)
            or self.operation_count != len(self.operations)
            or self.admitted_count
            + self.evidence_held_count
            + self.implementation_held_count
            != self.entry_count
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "selected package view counts are inconsistent",
            )
        if self.active_live_profile_ids or self.no_effects is not NO_EFFECTS_V1:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "selected package view must preserve shared no-effect custody",
            )


class SelectedComponentPackageAdapterV1:
    @staticmethod
    def build_projection(
        launch_graph_projection: Mapping[str, object],
    ) -> Mapping[str, object]:
        return selected_component_package_projection_v1(
            launch_graph_projection
        )

    @staticmethod
    def build_view(
        launch_graph_projection: Mapping[str, object],
    ) -> SelectedComponentPackageViewV1:
        projection = SelectedComponentPackageAdapterV1.build_projection(
            launch_graph_projection
        )
        manifest = projection.get("manifest")
        compatibility = projection.get("compatibility_and_dependency")
        if (
            type(manifest) is not SelectedComponentPackageManifestV1
            or type(compatibility) is not CompatibilityAndDependencyReceiptV1
            or compatibility.terminal_state
            is PackageValidationTerminalStateV1.REJECTED_INVALID
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "generic selected package projection is not validated",
            )
        entries = tuple(
            SelectedComponentPackageEntryViewV1(
                package_component_id=entry.package_component_id,
                launch_role_id=entry.launch_role_id,
                admission_state=entry.admission_state.value,
                compatibility_state=entry.compatibility_state.value,
                compatibility_reason_codes=tuple(
                    reason.value for reason in entry.compatibility_reason_codes
                ),
                plugin_family_refs=(
                    *((entry.primary_plugin_family_or_none,)
                      if entry.primary_plugin_family_or_none is not None
                      else ()),
                    *entry.supporting_plugin_families,
                ),
                required_operation_classes=entry.required_operation_classes,
                optional_operation_classes=entry.optional_operation_classes,
                default_failure_route=entry.default_failure_route,
                latency_class=entry.latency_class,
                rollback_target_kind=entry.rollback_target_kind.value,
                fallback_component_id_or_none=(
                    entry.fallback_component_id_or_none
                ),
            )
            for entry in manifest.entries
        )
        operations = tuple(
            SelectedComponentOperationViewV1(
                operation_class=row.operation_class,
                required_component_ids=row.required_component_ids,
                optional_component_ids=row.optional_component_ids,
                blocking_component_ids=row.blocking_component_ids,
                state=row.state.value,
                terminal_failure_route=row.terminal_failure_route,
            )
            for row in manifest.operation_eligibility_rows
        )
        return SelectedComponentPackageViewV1(
            package_id=manifest.package_id,
            package_version=manifest.package_version.canonical,
            entry_count=len(entries),
            admitted_count=sum(
                entry.admission_state
                is PackageAdmissionStateV1.ADMITTED_CONTRACT_ONLY_NO_EFFECT
                for entry in manifest.entries
            ),
            evidence_held_count=sum(
                entry.admission_state
                is PackageAdmissionStateV1.HELD_EVIDENCE_INSUFFICIENT_NO_ADMISSION
                for entry in manifest.entries
            ),
            implementation_held_count=sum(
                entry.admission_state
                is PackageAdmissionStateV1.HELD_IMPLEMENTATION_MISSING_NO_ADMISSION
                for entry in manifest.entries
            ),
            edge_count=len(manifest.dependency_edges),
            operation_count=len(operations),
            selected_profile_ids=manifest.selected_profile_ids,
            excluded_profile_ids=manifest.excluded_profile_ids,
            active_live_profile_ids=manifest.active_live_profile_ids,
            entries=entries,
            operations=operations,
            source_owner="src/qtt/plugins/registry.py",
            source_package_ref=manifest.launch_graph_package_ref,
            canonical_projection_json=deterministic_json(
                _qku_projection_serialization_value(projection)
            ),
            no_effects=NO_EFFECTS_V1,
        )


@dataclass(frozen=True, slots=True)
class PluginFamilyViewV1:
    row_id: str
    plugin_family: str
    owning_agent: str
    plugin_count: int
    family_materialized: bool
    source_report: str
    source_owner: str = "PR162E_PLUGIN_FRAMEWORK"

    def __post_init__(self) -> None:
        for name in (
            "row_id",
            "plugin_family",
            "owning_agent",
            "source_report",
            "source_owner",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    f"PR162E {name} must be nonempty text",
                )
        if (
            isinstance(self.plugin_count, bool)
            or not isinstance(self.plugin_count, int)
            or self.plugin_count < 0
            or type(self.family_materialized) is not bool
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "PR162E plugin counts and flags must preserve their declared types",
            )
        if self.source_owner != "PR162E_PLUGIN_FRAMEWORK":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E canonical owner lineage changed",
            )
        from .serialization import validate_relative_path

        validate_relative_path(self.source_report)


class PR162EPluginAdapterV1:
    def __init__(self, repo_root: str | Path) -> None:
        self._repo_root = Path(repo_root).resolve()

    def load_families(self) -> tuple[PluginFamilyViewV1, ...]:
        path = self._repo_root / PLUGIN_REPORT_PATH
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MISSING, "PR162E plugin report is unavailable"
            ) from exc
        if not isinstance(payload, dict):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "PR162E plugin report must be an object",
            )
        if payload.get("validation_status") != "PASS":
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_STALE,
                "PR162E plugin report is not validated",
            )
        forbidden_counts = (
            "live_order_authority_count",
            "live_order_execution_count",
            "private_state_fetch_count",
            "quantum_backend_execution_count",
            "source_truth_acceptance_count",
        )
        if any(payload.get(key) != 0 for key in forbidden_counts):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E report contains forbidden exercised authority",
            )
        records = payload.get("records")
        if not isinstance(records, list) or payload.get("record_count") != len(records):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_MALFORMED,
                "PR162E record count is inconsistent",
            )
        views: list[PluginFamilyViewV1] = []
        for record in records:
            if not isinstance(record, dict):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    "PR162E plugin record is not an object",
                )
            values = {
                field_name: record.get(field_name)
                for field_name in ("row_id", "plugin_family", "owning_agent")
            }
            if any(
                not isinstance(value, str) or not value
                for value in values.values()
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    "PR162E plugin identity fields must be nonempty text",
                )
            plugin_count = record.get("plugin_count")
            materialized = record.get("family_materialized_flag")
            if (
                isinstance(plugin_count, bool)
                or not isinstance(plugin_count, int)
                or type(materialized) is not bool
            ):
                raise OwnerAdapterError(
                    ReasonCode.OWNER_DATA_MALFORMED,
                    "PR162E plugin count or materialization flag is malformed",
                )
            views.append(
                PluginFamilyViewV1(
                    row_id=values["row_id"],
                    plugin_family=values["plugin_family"],
                    owning_agent=values["owning_agent"],
                    plugin_count=plugin_count,
                    family_materialized=materialized,
                    source_report=PLUGIN_REPORT_PATH.as_posix(),
                )
            )
        if (
            not views
            or len({view.row_id for view in views}) != len(views)
            or len({view.plugin_family for view in views}) != len(views)
        ):
            raise OwnerAdapterError(
                ReasonCode.OWNER_DATA_CONTRADICTORY,
                "PR162E plugin identities must be nonempty and unique",
            )
        return tuple(sorted(views, key=lambda item: item.row_id))
