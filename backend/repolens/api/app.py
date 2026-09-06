"""Local HTTP API for a completed RepoLens analysis."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles

from repolens.ai import NodeExplanation, build_node_context, get_provider
from repolens.exporters import get_exporter
from repolens.graph import GraphEngine
from repolens.models import GraphDocument, Node
from repolens.rules import ArchitectureRuleEngine, RuleCheckReport, load_rules


def create_app(document: GraphDocument, repo_root: Path | None = None) -> FastAPI:
    """Create a read-only local API over one analysis graph."""
    graph = GraphEngine(document)
    app = FastAPI(title="RepoLens", version="0.1.0")

    @app.get("/api/graph")
    def graph_document(level: str | None = None) -> GraphDocument:
        if level is not None:
            try:
                return graph.filter_level(level)
            except ValueError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
        return graph.serialize()

    @app.get("/api/nodes/{node_id}/subgraph")
    def node_subgraph(
        node_id: str,
        depth: int = Query(default=1, ge=1, le=5, description="Traversal depth bound (1-5)"),
    ) -> GraphDocument:
        if graph.node(node_id) is None:
            raise HTTPException(status_code=404, detail="Node not found")
        try:
            return graph.subgraph(node_id, depth=depth)
        except (ValueError, KeyError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/api/stats")
    def stats() -> dict[str, int]:
        return graph.stats()

    @app.get("/api/insights")
    def insights() -> dict[str, list[str] | list[list[str]]]:
        return graph.insights()

    @app.get("/api/nodes/{node_id}")
    def node(node_id: str) -> Node:
        item = graph.node(node_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Node not found")
        return item

    @app.get("/api/nodes/{node_id}/neighbors")
    def neighbors(node_id: str, direction: str = "both") -> list[Node]:
        return graph.neighbors(node_id, direction)

    @app.post("/api/nodes/{node_id}/explain")
    @app.get("/api/nodes/{node_id}/explain")
    def explain(
        node_id: str,
        provider: str | None = Query(
            default=None, description="Explanation provider: 'offline', 'openai', or 'mock'"
        ),
    ) -> NodeExplanation:
        if graph.node(node_id) is None:
            raise HTTPException(status_code=404, detail="Node not found")
        try:
            active_provider = get_provider(provider)
            context = build_node_context(graph, node_id, repo_root=repo_root)
            return active_provider.explain(context)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=500, detail=f"Explanation generation failed: {error}"
            ) from error

    @app.get("/api/rules/check")
    def check_rules() -> RuleCheckReport:
        config = load_rules(repo_root=repo_root)
        engine = ArchitectureRuleEngine(config)
        return engine.check(graph)

    @app.get("/api/export")
    def export_graph(
        format: str = Query(
            default="mermaid", description="Export format: mermaid, plantuml, dot, or html"
        ),
    ) -> Response:
        try:
            exporter = get_exporter(format)
            content = exporter.export(graph)
            media_type = "text/html" if format.lower() == "html" else "text/plain"
            return Response(content=content, media_type=media_type)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    web_assets = Path(__file__).resolve().parents[1] / "web"

    if web_assets.is_dir():
        app.mount("/", StaticFiles(directory=web_assets, html=True), name="web")

    return app
