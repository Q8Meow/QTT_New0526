from __future__ import annotations

from .module_contract import stage_module_contract, write_artifacts

CONTRACT = stage_module_contract("fill_model_policy")

__all__ = ["CONTRACT", "write_artifacts"]
