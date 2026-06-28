"""RP5D input references for RP5D-R1."""

from .models import REQUIRED_INPUT_REFS, RP5D_QUEUE_FILES

RP5D_INPUT_REFS = tuple(ref for ref in REQUIRED_INPUT_REFS if "pr168_rp5d" in ref)

__all__ = ["RP5D_INPUT_REFS", "RP5D_QUEUE_FILES"]
