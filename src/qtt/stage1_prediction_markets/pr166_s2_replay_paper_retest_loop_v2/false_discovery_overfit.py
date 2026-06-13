from __future__ import annotations

from .module_contract import stage_module_contract, write_artifacts

CONTRACT = stage_module_contract("false_discovery_overfit")

__all__ = ["CONTRACT", "write_artifacts"]
