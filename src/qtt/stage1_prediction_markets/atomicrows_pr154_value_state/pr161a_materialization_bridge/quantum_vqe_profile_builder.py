"""VQE profile extraction facade."""

from __future__ import annotations


def build_vqe_profiles(profiles: list[dict[str, object]]) -> list[dict[str, object]]:
    return [profile for profile in profiles if str(profile["quantum_profile_type"]).startswith("VQE_")]

