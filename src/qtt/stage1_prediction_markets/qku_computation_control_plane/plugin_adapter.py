"""Read-only adapter over the merged PR162E plugin-framework report."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .errors import OwnerAdapterError, ReasonCode


PLUGIN_REPORT_PATH = Path(
    "docs/master_plan/generated/PR162E_PluginFamilyRegistry.report.json"
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
