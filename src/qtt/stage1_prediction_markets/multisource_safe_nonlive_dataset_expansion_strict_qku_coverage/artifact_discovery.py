"""Load upstream PR162C artifacts, including sharded reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import resolve_repo_relative


def load_report_payload(repo_root: Path, filename: str) -> dict[str, Any]:
    payload = read_json(repo_root / c.GENERATED_DIR / filename)
    if not isinstance(payload, dict):
        raise TypeError(f"report payload is not an object: {filename}")
    return payload


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = load_report_payload(repo_root, filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    manifest_filename = _manifest_filename(filename)
    manifest_payload = load_report_payload(repo_root, manifest_filename)
    manifest_by_report = {
        record["report_filename"]: record
        for record in records_from_payload(manifest_payload)
    }
    rows: list[dict[str, Any]] = []
    for shard_ref in manifest_by_report[filename]["shard_files"]:
        rows.extend(records_from_payload(read_json(resolve_repo_relative(repo_root, shard_ref))))
    return rows


def _manifest_filename(filename: str) -> str:
    if filename.startswith("PR162B_"):
        return "PR162B_ReportShardManifest.report.json"
    if filename.startswith("PR162A_"):
        return "PR162A_ReportShardManifest.report.json"
    if filename.startswith("PR162_"):
        return "PR162_ReportShardManifest.report.json"
    if filename.startswith("PR161F_"):
        return "PR161F_ReportShardManifest.report.json"
    if filename.startswith("PR161D_"):
        return "PR161D_ReportShardManifest.report.json"
    if filename.startswith("PR161E_"):
        return "PR161E_ReportShardManifest.report.json"
    return filename.split("_", 1)[0] + "_ReportShardManifest.report.json"


def load_upstream_context(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    filenames = [
        "PR162A_NormalizedDatasetInventory.report.json",
        "PR162A_DatasetMaterializationManifest.report.json",
        "PR162A_MarketScenarioQKUMappingMatrix.report.json",
        "PR162A_PR162AdapterRerunReadinessBridge.report.json",
        "PR162A_QuantumQKUDatasetFeatureBridge.report.json",
        "PR162B_QKUExecutionClassificationAudit.report.json",
        "PR162B_QKUMarketClassificationRegistry.report.json",
        "PR162B_QKUStage1PredictionMarketActivationGate.report.json",
        "PR162B_QKUDormancyRegistry.report.json",
        "PR162B_QKUFormulaRegistry.report.json",
        "PR162B_QKUAlgorithmRegistry.report.json",
        "PR162B_QKUObjectiveFunctionRegistry.report.json",
        "PR162B_QKUConstraintRegistry.report.json",
        "PR162B_QKUParameterValueRegistry.report.json",
        "PR162B_QKUParameterRangeScaleRegistry.report.json",
        "PR162B_QKUTradableValueCandidateRegistry.report.json",
        "PR162B_QKUSolverMappingRegistry.report.json",
        "PR162B_QKUExecutableComputeContractRegistry.report.json",
        "PR162B_QKUFormulaTestVectorRegistry.report.json",
        "PR162B_QKUAlgorithmTestVectorRegistry.report.json",
        "PR162B_QKUFormulaBindingProofMatrix.report.json",
        "PR162B_QKUMarketInputFieldRequirementMatrix.report.json",
        "PR162B_PR162CDataRequirementHandoff.report.json",
        "PR162B_QuantumQUBOIsingFormulaMaterialization.report.json",
        "PR162B_QuantumSolverSmokeExecutionReport.report.json",
    ]
    return {filename: load_report_records(repo_root, filename) for filename in filenames}
