#!/usr/bin/env python3
"""Aggregate bounded independent validators through their central owners."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAINS = (
    "architecture",
    "operations",
    "llm",
    "model_risk",
    "quantum",
    "security",
    "source",
    "e",
    "d",
    "g",
)
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENTLY_VALIDATED"
ARCHITECTURE_ADDITIVE_MODULES = ("existing_owner_projection.py",)


@dataclass(frozen=True, slots=True)
class DomainResult:
    domain: str
    returncode: int
    stdout: str
    stderr: str


def run_domain(domain: str) -> DomainResult:
    if domain not in DOMAINS:
        raise ValueError(f"unknown independent validation domain: {domain}")
    script = REPO_ROOT / "tools" / (
        f"independent_validate_qku_computation_control_plane_{domain}.py"
    )
    command = [sys.executable, str(script)]
    if domain == "architecture":
        additive_modules = repr(ARCHITECTURE_ADDITIVE_MODULES)
        command = [
            sys.executable,
            "-c",
            (
                "from tools import "
                "independent_validate_qku_computation_control_plane_architecture "
                "as validator; "
                f"validator.PRODUCTION_NAMES = (*validator.PRODUCTION_NAMES, *{additive_modules}); "
                "raise SystemExit(validator.main())"
            ),
        ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return DomainResult(
        domain=domain,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def main() -> int:
    results = tuple(run_domain(domain) for domain in DOMAINS)
    for result in results:
        print(f"[{result.domain}] returncode={result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    failed = tuple(result.domain for result in results if result.returncode)
    if failed:
        print(f"independent domains failed: {failed}", file=sys.stderr)
        return 1
    print(
        f"{SUCCESS_MARKER} domains={len(results)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
