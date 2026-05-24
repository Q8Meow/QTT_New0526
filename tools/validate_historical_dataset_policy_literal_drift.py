from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.replay_paper import historical_dataset_policy as policy


REPORT_PATH = Path("docs/master_plan/generated/PR135PolicyLiteralDrift.report.json")
APPROVED_DEFINITION_PATHS = {
    Path(policy.POLICY_MODULE_PATH).as_posix(),
    Path(policy.POLICY_SCHEMA_DEFS_PATH).as_posix(),
    Path(policy.POLICY_MANIFEST_PATH).as_posix(),
}
INSTANCE_DATA_PREFIXES = (
    "docs/master_plan/generated/",
    "docs/roadmap/generated/",
    "tests/fixtures/replay_paper/",
)


def _write_report(repo_root: Path, failures: Sequence[str]) -> None:
    payload = {
        "receipt_type": "PR135_POLICY_LITERAL_DRIFT_REPORT",
        "repo_pr_number": policy.PRODUCER_REPO_PR,
        "roadmap_pr_number": policy.PRODUCER_ROADMAP_PR,
        "approved_definition_locations": sorted(APPROVED_DEFINITION_PATHS),
        "instance_data_prefixes": list(INSTANCE_DATA_PREFIXES),
        "policy_literal_drift_detected": bool(failures),
        "failures": list(failures),
    }
    path = repo_root / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _policy_terms() -> set[str]:
    terms: set[str] = set()
    terms.add(policy.VALIDATOR_MARKER)
    terms.update(policy.CANONICAL_VENUE_IDS)
    terms.update(policy.FORBIDDEN_VENUE_IDENTITIES)
    terms.update(policy.INPUT_LOCK_STATES)
    terms.update(policy.REQUIRED_FIXTURE_CASE_BLOCKS.values())
    terms.update(policy.NO_AUTHORITY_FLAGS)
    terms.update(policy.RECORD_NO_AUTHORITY_FLAGS)
    terms.update(policy.SOURCE_BOUNDARY_CONSTANTS)
    terms.update(policy.CANDIDATE_SET_CONSTANTS)
    return terms


def _repo_owned_scan_paths(repo_root: Path, extra_paths: Iterable[Path]) -> list[Path]:
    candidates = [
        Path("src/qtt/stage1_prediction_markets/replay_paper/historical_dataset_digest_and_loader.py"),
        Path("tools/build_historical_dataset_digest_and_loader_fixture.py"),
        Path("tools/validate_historical_dataset_digest_and_loader.py"),
        Path("tools/validate_historical_dataset_policy_literal_drift.py"),
        Path("tests/replay_paper/test_historical_dataset_digest_and_loader.py"),
        Path("tools/run_validation_gates.py"),
        Path("schemas/replay_paper/historical_dataset_digest_and_loader.schema.json"),
        Path("schemas/replay_paper/historical_dataset_digest_and_loader_receipt.schema.json"),
        Path(policy.POLICY_SCHEMA_DEFS_PATH),
        Path(policy.POLICY_MANIFEST_PATH),
    ]
    candidates.extend(extra_paths)
    return [repo_root / path for path in candidates if (repo_root / path).exists()]


def _is_approved_definition(rel_path: str) -> bool:
    return rel_path in APPROVED_DEFINITION_PATHS


def _is_instance_data(rel_path: str) -> bool:
    return rel_path.startswith(INSTANCE_DATA_PREFIXES)


def _literal_string_values(path: Path) -> list[str]:
    if path.suffix != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def _python_literal_collection_duplicates(path: Path, terms: set[str]) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            continue
        values = [
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        ]
        if len({value for value in values if value in terms}) >= 2:
            return True
    return False


def _looks_like_definition_list(path: Path, terms: set[str]) -> bool:
    if path.suffix == ".py":
        return _python_literal_collection_duplicates(path, terms)
    if path.suffix == ".json":
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        text = json.dumps(payload, sort_keys=True)
        hits = [term for term in terms if term in text]
        return len(hits) >= 2
    return False


def validate_policy_literal_drift(
    *,
    repo_root: Path = _REPO_ROOT,
    extra_paths: Sequence[Path] = (),
    write_report: bool = False,
) -> list[str]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    terms = _policy_terms()
    schema_defs = repo_root / policy.POLICY_SCHEMA_DEFS_PATH
    manifest = repo_root / policy.POLICY_MANIFEST_PATH
    if not schema_defs.exists():
        failures.append(f"missing policy schema defs: {policy.POLICY_SCHEMA_DEFS_PATH}")
    if not manifest.exists():
        failures.append(f"missing policy manifest: {policy.POLICY_MANIFEST_PATH}")

    if schema_defs.exists() and manifest.exists():
        defs = json.loads(schema_defs.read_text(encoding="utf-8")).get("$defs", {})
        manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
        if defs.get("validator_marker", {}).get("const") != policy.VALIDATOR_MARKER:
            failures.append("policy schema defs validator marker drift")
        if defs.get("canonical_venue_id", {}).get("enum") != list(policy.CANONICAL_VENUE_IDS):
            failures.append("policy schema defs canonical venue drift")
        if manifest_payload.get("input_lock_states") != list(policy.INPUT_LOCK_STATES):
            failures.append("policy manifest input lock state drift")
        if manifest_payload.get("no_authority_flags") != policy.NO_AUTHORITY_FLAGS:
            failures.append("policy manifest no-authority flag drift")

    for path in _repo_owned_scan_paths(repo_root, extra_paths):
        try:
            rel_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        if _is_approved_definition(rel_path) or _is_instance_data(rel_path):
            continue
        if _looks_like_definition_list(path, terms):
            failures.append(f"policy literals duplicated outside approved locations: {rel_path}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        if policy.VALIDATOR_MARKER in text and not _is_approved_definition(rel_path):
            failures.append(f"validator marker literal outside approved policy locations: {rel_path}")
    if write_report:
        _write_report(repo_root, failures)
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--extra-file", action="append", default=[], type=Path)
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Opt-in regeneration of the tracked PR135 policy literal drift report.",
    )
    args = parser.parse_args(argv)
    failures = validate_policy_literal_drift(
        repo_root=args.repo_root,
        extra_paths=tuple(args.extra_file),
        write_report=args.write_report,
    )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
