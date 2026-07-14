"""Decision-centric QKU computation control plane.

Runtime consumers deliberately receive one operational object.  The typed
values returned by that object live in the private package implementation and
are not additional services or authorities.
"""

from .control import QKUComputationControlPlaneV1

__all__ = ["QKUComputationControlPlaneV1"]
