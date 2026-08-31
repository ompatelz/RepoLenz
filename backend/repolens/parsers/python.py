"""Python AST parser that never imports or executes target modules."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import cast

from repolens.parsers.models import (
    Import,
    ImportKind,
    ModuleAnalysis,
    Relationship,
    Symbol,
    SymbolKind,
)


class PythonAstParser:
    def parse_file(self, path: Path | str, module_path: str | None = None) -> ModuleAnalysis:
        source_path = Path(path)
        module = module_path or source_path.with_suffix("").as_posix().replace("/", ".")
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        except (OSError, SyntaxError) as error:
            return ModuleAnalysis(path=str(source_path), module=module, errors=[str(error)])
        visitor = _Visitor(module, source_path.as_posix())
        visitor.visit(tree)
        return ModuleAnalysis(
            path=str(source_path),
            module=module,
            symbols=visitor.symbols,
            imports=visitor.imports,
            relationships=visitor.relationships,
        )


class _Visitor(ast.NodeVisitor):
    def __init__(self, module: str, path: str) -> None:
        self.module = module
        self.path = path
        self.symbols: list[Symbol] = []
        self.imports: list[Import] = []
        self.relationships: list[Relationship] = []
        self.stack: list[tuple[str, SymbolKind]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                Import(
                    module=alias.name,
                    alias=alias.asname,
                    kind=self._kind(alias.name),
                    line=node.lineno,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imports.append(
                Import(
                    module=node.module or "",
                    name=alias.name,
                    alias=alias.asname,
                    level=node.level,
                    kind=ImportKind.UNRESOLVED if node.level else self._kind(node.module or ""),
                    line=node.lineno,
                )
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._relations(node, "inherits", node.bases)
        self._symbol(node, SymbolKind.CLASS)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._symbol(
            node,
            SymbolKind.METHOD
            if self.stack and self.stack[-1][1] is SymbolKind.CLASS
            else SymbolKind.FUNCTION,
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._symbol(
            node,
            SymbolKind.METHOD
            if self.stack and self.stack[-1][1] is SymbolKind.CLASS
            else SymbolKind.FUNCTION,
        )

    def _symbol(
        self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, kind: SymbolKind
    ) -> None:
        parent = ".".join(item[0] for item in self.stack)
        ident = f"{self.module}:{parent + '.' if parent else ''}{node.name}"
        function = cast(ast.FunctionDef | ast.AsyncFunctionDef, node)
        sig = None if kind is SymbolKind.CLASS else f"{node.name}({ast.unparse(function.args)})"
        self.symbols.append(
            Symbol(
                id=ident,
                kind=kind,
                name=node.name,
                module=self.module,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring=ast.get_docstring(node),
                decorators=[ast.unparse(item) for item in node.decorator_list],
                bases=[ast.unparse(item) for item in node.bases]
                if isinstance(node, ast.ClassDef)
                else [],
            )
        )
        self.stack.append((node.name, kind))
        self.generic_visit(node)
        self.stack.pop()

    def _relations(self, node: ast.ClassDef, relation: str, items: list[ast.expr]) -> None:
        names = self.stack + [(node.name, SymbolKind.CLASS)]
        source = f"{self.module}:{'.'.join(item[0] for item in names)}"
        for item in items:
            self.relationships.append(
                Relationship(
                    source=source, target=ast.unparse(item), type=relation, line=node.lineno
                )
            )

    @staticmethod
    def _kind(name: str) -> ImportKind:
        root = name.split(".")[0]
        return (
            ImportKind.STANDARD_LIBRARY
            if root in sys.stdlib_module_names
            else ImportKind.THIRD_PARTY
        )
