"""Local HTTP API for a completed RepoLens analysis."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from repolens.graph import GraphEngine
from repolens.models import GraphDocument, Node


def create_app(document: GraphDocument) -> FastAPI:
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

    web_assets = Path(__file__).resolve().parents[1] / "web"
    if web_assets.is_dir():
        app.mount("/", StaticFiles(directory=web_assets, html=True), name="web")

    return app
