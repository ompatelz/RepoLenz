"""End-to-end static analysis pipeline from a repository to a graph document."""

from __future__ import annotations

from pathlib import Path

from repolens.cache import AnalysisCache
from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType
from repolens.parsers import PythonAstParser
from repolens.scanner import RepositoryScanner


def analyze_repository(path: Path | str, *, use_cache: bool = True) -> GraphDocument:
    """Build a graph, reusing a fingerprint-validated local cache by default."""
    if use_cache:
        graph, _ = AnalysisCache().get_or_create(
            path, lambda: analyze_repository(path, use_cache=False)
        )
        return graph
    scan = RepositoryScanner().scan(path)
    root = Path(scan.root)
    parser = PythonAstParser()
    repo_id = f"repository:{scan.name}"
    nodes = [Node(id=repo_id, type=NodeType.REPOSITORY, name=scan.name, path=".")]
    edges = []
    modules = {}
    analyses = []
    for relative in scan.python_files:
        module = relative.removesuffix(".py").replace("/__init__", "").replace("/", ".")
        node_id = f"module:{module}"
        modules[module] = node_id
        nodes.append(
            Node(id=node_id, type=NodeType.MODULE, name=module.split(".")[-1], path=relative)
        )
        edges.append(Edge(source=repo_id, target=node_id, type=EdgeType.CONTAINS))
        analyses.append((node_id, parser.parse_file(root / relative, module)))
    for module_id, analysis in analyses:
        for symbol in analysis.symbols:
            kind = {
                "class": NodeType.CLASS,
                "function": NodeType.FUNCTION,
                "method": NodeType.METHOD,
            }[symbol.kind.value]
            nodes.append(
                Node(
                    id=f"symbol:{symbol.id}",
                    type=kind,
                    name=symbol.name,
                    path=analysis.path,
                    line_start=symbol.line_start,
                    line_end=symbol.line_end,
                    metadata={"decorators": symbol.decorators, "signature": symbol.signature},
                )
            )
            edges.append(
                Edge(source=module_id, target=f"symbol:{symbol.id}", type=EdgeType.CONTAINS)
            )
        for imported in analysis.imports:
            target = modules.get(imported.module)
            if target:
                edges.append(
                    Edge(
                        source=module_id,
                        target=target,
                        type=EdgeType.IMPORTS,
                        metadata={"line": imported.line},
                    )
                )
    return GraphDocument(
        metadata={"repository": scan.name},
        nodes=nodes,
        edges=edges,
        stats={"modules": len(modules), "symbols": sum(len(item.symbols) for _, item in analyses)},
    )
