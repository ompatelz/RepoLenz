"""Query and serialize evidence-backed architecture graphs."""

from __future__ import annotations

from typing import cast

import networkx as nx

from repolens.models import GraphDocument, Node, NodeType


class GraphEngine:
    def __init__(self, document: GraphDocument) -> None:
        self.document = document
        self.graph: nx.MultiDiGraph[str, dict[str, object]] = nx.MultiDiGraph()
        for node in document.nodes:
            self.graph.add_node(node.id, node=node)
        for edge in document.edges:
            self.graph.add_edge(edge.source, edge.target, edge=edge)

    def node(self, node_id: str) -> Node | None:
        value = self.graph.nodes.get(node_id, {}).get("node")
        return value if isinstance(value, Node) else None

    def neighbors(self, node_id: str, direction: str = "both") -> list[Node]:
        ids = (
            set(self.graph.successors(node_id))
            if direction == "outgoing"
            else set(self.graph.predecessors(node_id))
            if direction == "incoming"
            else set(self.graph.successors(node_id)) | set(self.graph.predecessors(node_id))
        )
        return [cast(Node, self.graph.nodes[item]["node"]) for item in sorted(ids)]

    def subgraph(self, node_id: str, depth: int = 1) -> GraphDocument:
        reached = {node_id}
        frontier = {node_id}
        for _ in range(depth):
            frontier = {
                item for current in frontier for item in self.graph.predecessors(current)
            } | {item for current in frontier for item in self.graph.successors(current)}
            reached |= frontier
        nodes = [
            cast(Node, self.graph.nodes[item]["node"])
            for item in sorted(reached)
            if item in self.graph
        ]
        edges = [
            data["edge"]
            for source, target, data in self.graph.edges(data=True)
            if source in reached and target in reached
        ]
        return GraphDocument(nodes=nodes, edges=edges)

    def shortest_path(self, source: str, target: str) -> list[Node]:
        return [
            cast(Node, self.graph.nodes[item]["node"])
            for item in nx.shortest_path(self.graph, source, target)
        ]

    def cycles(self) -> list[list[str]]:
        return [sorted(cycle) for cycle in nx.simple_cycles(self.graph)]

    def stats(self) -> dict[str, int]:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "cycles": len(self.cycles()),
            "routes": sum(
                1
                for _, data in self.graph.nodes(data=True)
                if getattr(data.get("node"), "type", None) == NodeType.ROUTE
            ),
            "models": sum(
                1
                for _, data in self.graph.nodes(data=True)
                if getattr(data.get("node"), "type", None) == NodeType.MODEL
            ),
        }

    def insights(self) -> dict[str, list[str] | list[list[str]]]:
        """Compute deterministic, evidence-backed architecture signals."""
        incoming = sorted(
            self.graph.nodes,
            key=lambda item: (-self.graph.in_degree(item), item),
        )
        outgoing = sorted(
            self.graph.nodes,
            key=lambda item: (-self.graph.out_degree(item), item),
        )
        return {
            "cycles": self.cycles(),
            "dependency_hubs": [item for item in incoming if self.graph.in_degree(item) > 1][:10],
            "fan_out": [item for item in outgoing if self.graph.out_degree(item) > 1][:10],
            "orphans": sorted(
                item
                for item in self.graph.nodes
                if self.graph.in_degree(item) == 0 and self.graph.out_degree(item) == 0
            ),
        }

    def serialize(self) -> GraphDocument:
        return self.document
