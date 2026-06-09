"""Quantum consumer route projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_quantum_consumer_route_rows(repo_root):
    return build_core_tables(repo_root)["QuantumConsumerRouteCoreTable"]
