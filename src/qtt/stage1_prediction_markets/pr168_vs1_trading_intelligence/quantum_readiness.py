"""Quantum structural readiness metadata for PR168-VS1."""

from __future__ import annotations

CLASSICAL_FALLBACK_OPTIMIZERS = (
    "TPE",
    "Hyperband",
    "differential_evolution",
    "dual_annealing",
    "SHGO",
    "greedy_top_k",
    "beam_search",
    "successive_halving",
)

__all__ = ["CLASSICAL_FALLBACK_OPTIMIZERS"]
