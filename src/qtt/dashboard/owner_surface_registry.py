"""Central loader for the PR169-DASH1 owner dashboard surface registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .owner_surface_models import REGISTRY_FILENAME, read_jsonl


@dataclass(frozen=True)
class OwnerSurfaceFeature:
    row: dict[str, Any]

    @property
    def feature_id(self) -> str:
        return str(self.row["feature_id"])

    @property
    def panel_id(self) -> str:
        return str(self.row["panel_id"])

    @property
    def action_code_refs(self) -> tuple[str, ...]:
        return tuple(str(code) for code in self.row.get("action_code_refs", ()))


class OwnerDashboardSurfaceRegistry:
    """Indexed view over the single editable owner dashboard registry."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self._by_feature: dict[str, dict[str, Any]] = {}
        self._by_panel: dict[str, list[dict[str, Any]]] = {}
        self._by_alias: dict[str, dict[str, Any]] = {}
        for row in rows:
            feature_id = str(row["feature_id"])
            if feature_id in self._by_feature:
                raise ValueError(f"duplicate feature_id: {feature_id}")
            self._by_feature[feature_id] = row
            self._by_panel.setdefault(str(row["panel_id"]), []).append(row)
            for alias in row.get("legacy_aliases", []):
                alias_key = str(alias)
                if alias_key in self._by_alias:
                    raise ValueError(f"duplicate legacy alias: {alias_key}")
                self._by_alias[alias_key] = row

    @classmethod
    def load(cls, base_dir: Path | str) -> "OwnerDashboardSurfaceRegistry":
        base = Path(base_dir)
        return cls(read_jsonl(base / REGISTRY_FILENAME))

    def get(self, feature_id: str) -> dict[str, Any]:
        return self._by_feature[feature_id]

    def maybe_get(self, feature_id: str) -> dict[str, Any] | None:
        return self._by_feature.get(feature_id)

    def get_by_alias(self, alias: str) -> dict[str, Any]:
        return self._by_alias[alias]

    def panel_features(self, panel_id: str) -> list[dict[str, Any]]:
        return list(self._by_panel.get(panel_id, ()))

    def feature_refs_for_action(self, action_code: str) -> list[dict[str, Any]]:
        return [
            row
            for row in self.rows
            if action_code in {str(code) for code in row.get("action_code_refs", [])}
        ]
