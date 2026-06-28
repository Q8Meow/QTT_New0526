"""PR165-D2 routing input references for RP5D-R1."""

from .models import REQUIRED_INPUT_REFS

PR165_D2_INPUT_REFS = tuple(ref for ref in REQUIRED_INPUT_REFS if "PR165_D2" in ref)

__all__ = ["PR165_D2_INPUT_REFS"]
