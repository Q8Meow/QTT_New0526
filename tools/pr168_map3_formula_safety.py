from __future__ import annotations

import ast


ALLOWED_AST_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.USub,
    ast.Load,
    ast.Name,
    ast.Constant,
    ast.Call,
}
ALLOWED_CALLS = {"abs", "min", "max"}


def validate_safe_expression(expression: str, allowed_names: set[str]) -> bool:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            return False
        if isinstance(node, ast.Name) and node.id not in allowed_names and node.id not in ALLOWED_CALLS:
            return False
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_CALLS:
                return False
    return True
