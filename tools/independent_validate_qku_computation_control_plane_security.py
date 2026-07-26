#!/usr/bin/env python3
"""Independent static security validation without importing production."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import unicodedata


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    REPO_ROOT
    / "src"
    / "qtt"
    / "stage1_prediction_markets"
    / "qku_computation_control_plane"
)
FORBIDDEN_IMPORT_ROOTS = {
    "dill",
    "importlib",
    "marshal",
    "pickle",
    "shelve",
}
FORBIDDEN_CALLS = {"eval", "exec", "__import__", "compile"}
FORBIDDEN_ATTRIBUTE_CALLS = {
    ("importlib", "import_module"),
    ("pickle", "load"),
    ("pickle", "loads"),
}
SUCCESS_MARKER = "QKU_SECURITY_INDEPENDENTLY_VALIDATED"
SECRET_TERMS = frozenset(
    {
        "apikey",
        "apisecret",
        "authorization",
        "bearer",
        "password",
        "passphrase",
        "accesstoken",
        "refreshtoken",
        "sessiontoken",
        "cookie",
        "credential",
        "privatekey",
        "secret",
        "seedphrase",
        "walletsecret",
    }
)
ALLOWED_SECRET_LOOKALIKES = frozenset(
    {"tokencount", "tokenbudget", "credentialstate"}
)


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _independent_secret_match(value: str) -> bool:
    normalized = _normalize_key(value)
    if normalized in ALLOWED_SECRET_LOOKALIKES:
        return False
    return (
        normalized == "token"
        or normalized.endswith("token")
        or any(term in normalized for term in SECRET_TERMS)
    )


def _function_uses_name(
    tree: ast.Module,
    function_name: str,
    consumed_name: str,
) -> bool:
    function = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ),
        None,
    )
    return function is not None and any(
        isinstance(node, ast.Name) and node.id == consumed_name
        for node in ast.walk(function)
    )


def main() -> int:
    failures: list[str] = []
    authority_tree: ast.Module | None = None
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if path.name == "authority.py":
            authority_tree = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                if roots & FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: unsafe import {sorted(roots)}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    failures.append(f"{path.name}: unsafe import {root}")
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                if name in FORBIDDEN_CALLS:
                    failures.append(f"{path.name}: unsafe call {name}")
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and (
                        node.func.value.id,
                        node.func.attr,
                    )
                    in FORBIDDEN_ATTRIBUTE_CALLS
                ):
                    failures.append(
                        f"{path.name}: unsafe call "
                        f"{node.func.value.id}.{node.func.attr}"
                    )
    capability_defaults: list[bool] = []
    for node in authority_tree.body if authority_tree else ():
        if isinstance(node, ast.ClassDef) and node.name == "CapabilityEnvelopeV1":
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign):
                    capability_defaults.append(
                        isinstance(statement.value, ast.Constant)
                        and statement.value.value is False
                    )
    if len(capability_defaults) != 10 or not all(capability_defaults):
        failures.append("capability envelope is not exactly ten default-false fields")
    serialization_tree = ast.parse(
        (PACKAGE / "serialization.py").read_text(encoding="utf-8")
    )
    source_rights_tree = ast.parse(
        (PACKAGE / "source_rights.py").read_text(encoding="utf-8")
    )
    function = next(
        (
            node
            for node in serialization_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "validate_relative_path"
        ),
        None,
    )
    reserved_assignment = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "_WINDOWS_RESERVED_NAMES"
            for target in node.targets
        )
        for node in serialization_tree.body
    )
    call_attributes = {
        node.func.attr
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    constants = {
        node.value
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Constant)
    }
    attribute_names = {
        node.attr
        for node in (ast.walk(function) if function is not None else ())
        if isinstance(node, ast.Attribute)
    }
    if (
        function is None
        or not reserved_assignment
        or not {"replace", "split", "is_absolute"} <= call_attributes
        or not {"", ".", "..", ":"} <= constants
        or "drive" not in attribute_names
    ):
        failures.append(
            "relative-path safety lacks structural traversal, drive, "
            "segment, or reserved-name checks"
        )
    serialization_classes = {
        node.name
        for node in serialization_tree.body
        if isinstance(node, ast.ClassDef)
    }
    serialization_assignments = {
        target.id
        for node in serialization_tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    source_rights_imports = {
        alias.name
        for node in source_rights_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "serialization"
        for alias in node.names
    }
    if (
        "SecretKeyPolicyV1" not in serialization_classes
        or "SECRET_KEY_POLICY" not in serialization_assignments
        or "SECRET_KEY_POLICY" not in source_rights_imports
        or not _function_uses_name(
            serialization_tree,
            "_check_key",
            "SECRET_KEY_POLICY",
        )
        or not _function_uses_name(
            source_rights_tree,
            "reject_secret_material",
            "SECRET_KEY_POLICY",
        )
    ):
        failures.append(
            "serialization and source rights do not consume one secret policy"
        )
    secret_variants = (
        "API-KEY",
        "api.secret",
        "Authorization",
        "bearer_token",
        "password",
        "pass phrase",
        "access-token",
        "refresh_token",
        "SESSION.TOKEN",
        "cookie",
        "credential",
        "private/key",
        "seed_phrase",
        "wallet-secret",
    )
    allowed_variants = ("token_count", "token-budget", "credential.state")
    if not all(_independent_secret_match(value) for value in secret_variants):
        failures.append("independent secret-key normalization misses a class")
    if any(_independent_secret_match(value) for value in allowed_variants):
        failures.append("independent secret-key normalization has a false positive")
    serialization_text = (PACKAGE / "serialization.py").read_text(encoding="utf-8")
    for term in SECRET_TERMS | ALLOWED_SECRET_LOOKALIKES:
        if f'"{term}"' not in serialization_text:
            failures.append(f"central secret policy term is absent: {term}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
