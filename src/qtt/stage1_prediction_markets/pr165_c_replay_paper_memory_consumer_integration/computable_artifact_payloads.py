"""Computable artifact payload projection."""

from __future__ import annotations

from .core_tables import build_core_tables


def build_computable_artifact_payload_rows(repo_root):
    return build_core_tables(repo_root)["ComputableArtifactPayloadCoreTable"]
