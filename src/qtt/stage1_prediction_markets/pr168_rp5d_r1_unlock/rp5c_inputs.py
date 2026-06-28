"""RP5C input references for RP5D-R1."""

from .models import REQUIRED_INPUT_REFS

RP5C_INPUT_REFS = tuple(ref for ref in REQUIRED_INPUT_REFS if "/rp5c/" in ref or "RP5C" in ref)

__all__ = ["RP5C_INPUT_REFS"]
