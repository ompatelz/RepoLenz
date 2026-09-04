"""Local HTTP API for a completed RepoLens analysis."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from repolens.graph import GraphEngine
from repolens.models import GraphDocument, Node


def create_app(document: GraphDocument) -> FastAPI:
    """Create a read-only local API over one analysis graph."""
    graph = GraphEngine(document)
    app = FastAPI(title="RepoLens", version="0.1.0")

    @app.get("/api/graph")
    def graph_document() -> GraphDocument:
        return graph.serialize()

    @app.get("/api/stats")
    def stats() -> dict[str, int]:
        return graph.stats()

    @app.get("/api/nodes/{node_id}")
    def node(node_id: str) -> Node:
        item = graph.node(node_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Node not found")
        return item

    @app.get("/api/nodes/{node_id}/neighbors")
    def neighbors(node_id: str, direction: str = "both") -> list[Node]:
        return graph.neighbors(node_id, direction)

    return app
