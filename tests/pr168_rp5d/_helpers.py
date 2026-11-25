from __future__ import annotations

import os
import shutil
import stat
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from unittest.mock import patch

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability import models, runner, validator
from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import (
    GENERATED_DIR,
    REPO_ROOT,
    RP5C_REQUIRED_FILES,
    VS1_REQUIRED_FILES,
    read_json,
    read_jsonl,
)


def _copy_input(source: Path, workspace: Path) -> None:
    info = source.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        or info.st_nlink != 1
        or source.resolve(strict=True) != source
    ):
        raise ValueError(f"RP5D fixture requires an ordinary, unaliased input: {source}")
    target = workspace / source.relative_to(REPO_ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as original, target.open("xb") as copy:
        shutil.copyfileobj(original, copy)


def _seed_workspace(workspace: Path) -> None:
    if os.path.lexists(GENERATED_DIR):
        info = GENERATED_DIR.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            or GENERATED_DIR.resolve(strict=True) != GENERATED_DIR
        ):
            raise ValueError(f"RP5D fixture requires an ordinary directory: {GENERATED_DIR}")
        for source in sorted(GENERATED_DIR.iterdir()):
            _copy_input(source, workspace)
    for ref in sorted(set(RP5C_REQUIRED_FILES) | set(VS1_REQUIRED_FILES)):
        source = REPO_ROOT / ref
        if os.path.lexists(source):
            _copy_input(source, workspace)


@lru_cache(maxsize=1)
def _validated_workspace() -> tuple[TemporaryDirectory[str], Path, dict[str, object]]:
    parent = Path(gettempdir()).resolve(strict=True)
    if parent.is_relative_to(REPO_ROOT):
        raise ValueError(f"RP5D fixture temporary directory must be outside the checkout: {parent}")
    temporary = TemporaryDirectory(prefix="rp5d-", dir=parent)
    try:
        workspace = Path(temporary.name)
        _seed_workspace(workspace)
        generated = workspace / GENERATED_DIR.relative_to(REPO_ROOT)
        original_rel_ref = models.rel_ref

        def artifact_ref(path: str | Path) -> str:
            physical = Path(path)
            if physical.is_relative_to(generated):
                physical = GENERATED_DIR / physical.relative_to(generated)
            return original_rel_ref(physical)

        # Keep the runner's input discovery in the checkout. Give the validator
        # exact inputs and keep generated references checkout-relative.
        with (
            patch.object(models, "rel_ref", artifact_ref),
            patch.object(runner, "GENERATED_DIR", generated),
            patch.multiple(
                validator,
                GENERATED_DIR=generated,
                REPO_ROOT=workspace,
                _validation_result=validator._validation_result.__wrapped__,
            ),
        ):
            if not (generated / "rp5d_run_receipt.report.json").is_file():
                runner.run_layer(offline=True)
            result = validator.run_validation("pytest")
    except BaseException:
        temporary.cleanup()
        raise
    return temporary, generated, result


def assert_rp5d_valid() -> dict[str, object]:
    _, _, result = _validated_workspace()
    return result


def rows(name: str) -> list[dict[str, object]]:
    _, generated, _ = _validated_workspace()
    return read_jsonl(generated / name)


def report(name: str) -> dict[str, object]:
    _, generated, _ = _validated_workspace()
    return read_json(generated / name)
