from __future__ import annotations

from .module_contract import stage_module_contract, write_artifacts

CONTRACT = stage_module_contract("optional_input_resolution")

__all__ = ["CONTRACT", "write_artifacts"]
