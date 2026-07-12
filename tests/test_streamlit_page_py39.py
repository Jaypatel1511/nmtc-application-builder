"""M1: Streamlit pages must import on Python 3.9.

PEP 604 unions (``X | Y``) in function signatures and variable annotations
are evaluated at def-time unless ``from __future__ import annotations`` is
active. Page 1 used ``dict | None`` in a module-level function signature,
crashing the page at import time on 3.9 (the floor of this project's
supported range). AST check: any module using PEP 604 syntax in annotations
must carry the future import.
"""
import ast
import os

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STREAMLIT_APP = os.path.join(_REPO_ROOT, "streamlit_app")


def _streamlit_modules() -> list:
    paths = []
    for root, _dirs, files in os.walk(_STREAMLIT_APP):
        for name in files:
            if name.endswith(".py"):
                paths.append(os.path.join(root, name))
    return sorted(paths)


def _has_future_annotations(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )


def _annotation_nodes(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            for arg in (
                args.args + args.posonlyargs + args.kwonlyargs
                + ([args.vararg] if args.vararg else [])
                + ([args.kwarg] if args.kwarg else [])
            ):
                if arg.annotation is not None:
                    yield arg.annotation
            if node.returns is not None:
                yield node.returns
        elif isinstance(node, ast.AnnAssign):
            yield node.annotation


def _uses_pep604_union(annotation: ast.AST) -> bool:
    return any(
        isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr)
        for sub in ast.walk(annotation)
    )


@pytest.mark.parametrize("path", _streamlit_modules(),
                         ids=lambda p: os.path.relpath(p, _REPO_ROOT))
def test_pep604_annotations_require_future_import(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    uses_604 = any(_uses_pep604_union(a) for a in _annotation_nodes(tree))
    if uses_604:
        assert _has_future_annotations(tree), (
            f"{os.path.relpath(path, _REPO_ROOT)} uses PEP 604 unions in "
            "annotations without 'from __future__ import annotations' — "
            "this crashes at import time on Python 3.9"
        )
