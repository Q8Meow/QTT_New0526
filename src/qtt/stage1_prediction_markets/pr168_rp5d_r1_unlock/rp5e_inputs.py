"""RP5E unlock input references for RP5D-R1."""

from .models import REQUIRED_INPUT_REFS

RP5E_INPUT_REFS = tuple(ref for ref in REQUIRED_INPUT_REFS if "pr168_rp5e" in ref)

__all__ = ["RP5E_INPUT_REFS"]
