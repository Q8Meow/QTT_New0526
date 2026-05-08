#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import os
import pathlib
import subprocess
import sys
from typing import Sequence

MAX_BASETEMP_TEXT_LENGTH = 64


@dataclass(frozen=True)
class PytestInvocation:
    command: list[str]
    basetemp: str
    added_basetemp: bool


def make_fresh_basetemp(
    *, now: datetime | None = None, pid: int | None = None
) -> pathlib.Path:
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    else:
        moment = moment.astimezone(UTC)
    timestamp = moment.strftime("%Y%m%d_%H%M%S_%f")
    process_id = os.getpid() if pid is None else pid
    return pathlib.Path(".tmp") / f"pytest_{timestamp}_{process_id}"


def find_explicit_basetemp(pytest_args: Sequence[str]) -> str | None:
    for index, arg in enumerate(pytest_args):
        if arg == "--basetemp":
            if index + 1 < len(pytest_args):
                return pytest_args[index + 1]
            return "<missing --basetemp value>"
        if arg.startswith("--basetemp="):
            return arg.split("=", 1)[1]
    return None


def build_pytest_invocation(
    pytest_args: Sequence[str], *, fresh_basetemp: pathlib.Path | None = None
) -> PytestInvocation:
    forwarded_args = list(pytest_args)
    explicit_basetemp = find_explicit_basetemp(forwarded_args)
    if explicit_basetemp is None:
        selected_basetemp = fresh_basetemp or make_fresh_basetemp()
        forwarded_args.extend(["--basetemp", str(selected_basetemp)])
        return PytestInvocation(
            command=[sys.executable, "-m", "pytest", *forwarded_args],
            basetemp=str(selected_basetemp),
            added_basetemp=True,
        )

    return PytestInvocation(
        command=[sys.executable, "-m", "pytest", *forwarded_args],
        basetemp=explicit_basetemp,
        added_basetemp=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    invocation = build_pytest_invocation(sys.argv[1:] if argv is None else argv)
    if invocation.added_basetemp:
        pathlib.Path(invocation.basetemp).parent.mkdir(parents=True, exist_ok=True)
    print(f"pytest basetemp: {invocation.basetemp}", flush=True)
    completed = subprocess.run(invocation.command)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
