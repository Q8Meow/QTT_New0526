"""VS1 input references for RP5D-R1."""

from .models import REQUIRED_INPUT_REFS

VS1_INPUT_REFS = tuple(ref for ref in REQUIRED_INPUT_REFS if "vs1" in ref.lower())

__all__ = ["VS1_INPUT_REFS"]
