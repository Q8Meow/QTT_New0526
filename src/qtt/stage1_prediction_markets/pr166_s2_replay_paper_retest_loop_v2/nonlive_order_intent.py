from __future__ import annotations

from .module_contract import stage_module_contract, write_artifacts

CONTRACT = stage_module_contract("nonlive_order_intent")

__all__ = ["CONTRACT", "write_artifacts"]
