"""Small in-memory registry for deterministic plugin adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import PluginAdapterBase


@dataclass
class PluginRegistry:
    adapters: dict[str, PluginAdapterBase] = field(default_factory=dict)

    def register(self, plugin_id: str, adapter: PluginAdapterBase) -> None:
        if not plugin_id:
            raise ValueError("plugin_id is required")
        self.adapters[plugin_id] = adapter

    def get(self, plugin_id: str) -> PluginAdapterBase:
        return self.adapters[plugin_id]

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.adapters))
