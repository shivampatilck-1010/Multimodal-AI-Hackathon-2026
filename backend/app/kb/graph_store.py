"""Storage and graph analysis engine for Course Knowledge Graphs and Prerequisites."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

import networkx as nx

from app.kb.models import (
    ConceptNode,
    PrerequisiteEdge,
    CourseKnowledgeGraph,
)

logger = logging.getLogger(__name__)


class GraphStore:
    """Manages concept taxonomy and prerequisite DAGs for courses."""

    def __init__(self, persist_dir: Path | None = None) -> None:
        self.persist_dir = persist_dir
        self._graphs: dict[str, CourseKnowledgeGraph] = {}
        self._lock = threading.RLock()
        if self.persist_dir is not None:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._load_all()

    def get_graph(self, course_id: str) -> CourseKnowledgeGraph | None:
        with self._lock:
            return self._graphs.get(course_id)

    def save_graph(self, graph: CourseKnowledgeGraph) -> None:
        """Validate DAG acyclicity and persist course graph."""
        with self._lock:
            # Validate and resolve cycles if any
            clean_graph = self._ensure_acyclic(graph)
            self._graphs[graph.course_id] = clean_graph
            if self.persist_dir is not None:
                self._persist_one(clean_graph)

    def _ensure_acyclic(self, graph: CourseKnowledgeGraph) -> CourseKnowledgeGraph:
        """Verify graph is a DAG; if cycles exist, break them using lowest confidence edges."""
        g = nx.DiGraph()
        for node_id in graph.nodes:
            g.add_node(node_id)
        for edge in graph.edges:
            if edge.relation_type == "prerequisite_of":
                g.add_edge(
                    edge.source_concept_id,
                    edge.target_concept_id,
                    strength=edge.strength,
                    rationale=edge.rationale,
                )

        if not nx.is_directed_acyclic_graph(g):
            logger.warning(
                "cycle_detected_in_prerequisites",
                extra={"course_id": graph.course_id},
            )
            # Find and break simple cycles
            while not nx.is_directed_acyclic_graph(g):
                try:
                    cycle = nx.find_cycle(g, orientation="original")
                    # Remove edge with lowest strength in cycle
                    weakest_edge = min(
                        cycle,
                        key=lambda e: g[e[0]][e[1]].get("strength", 1.0),
                    )
                    g.remove_edge(weakest_edge[0], weakest_edge[1])
                    logger.info(
                        "prerequisite_cycle_edge_removed",
                        extra={"edge": f"{weakest_edge[0]} -> {weakest_edge[1]}"},
                    )
                except nx.NetworkXNoCycle:
                    break

            # Reconstruct clean edge list
            clean_edges = []
            for u, v, data in g.edges(data=True):
                clean_edges.append(
                    PrerequisiteEdge(
                        source_concept_id=u,
                        target_concept_id=v,
                        relation_type="prerequisite_of",
                        rationale=data.get("rationale", ""),
                        strength=data.get("strength", 1.0),
                    )
                )
            # Add non-prerequisite edges back
            clean_edges.extend(
                [e for e in graph.edges if e.relation_type != "prerequisite_of"]
            )
            graph = CourseKnowledgeGraph(
                course_id=graph.course_id,
                nodes=graph.nodes,
                edges=clean_edges,
                topics_hierarchy=graph.topics_hierarchy,
            )
        return graph

    def get_topological_order(self, course_id: str) -> list[str]:
        """Return concept IDs in pedagogical learning order (prerequisites first)."""
        with self._lock:
            graph = self._graphs.get(course_id)
            if not graph:
                return []
            g = nx.DiGraph()
            for node_id in graph.nodes:
                g.add_node(node_id)
            for edge in graph.edges:
                if edge.relation_type == "prerequisite_of":
                    g.add_edge(edge.source_concept_id, edge.target_concept_id)
            try:
                return list(nx.topological_sort(g))
            except nx.NetworkXUnfeasible:
                return list(graph.nodes.keys())

    def get_all_ancestor_prerequisites(
        self, course_id: str, concept_id: str
    ) -> list[str]:
        """Return all transitive prerequisites needed to understand a concept."""
        with self._lock:
            graph = self._graphs.get(course_id)
            if not graph or concept_id not in graph.nodes:
                return []
            g = nx.DiGraph()
            for edge in graph.edges:
                if edge.relation_type == "prerequisite_of":
                    g.add_edge(edge.source_concept_id, edge.target_concept_id)
            if concept_id not in g:
                return []
            return list(nx.ancestors(g, concept_id))

    def _persist_one(self, graph: CourseKnowledgeGraph) -> None:
        assert self.persist_dir is not None
        target = self.persist_dir / f"{graph.course_id}_graph.json"
        tmp = target.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(target)

    def _load_all(self) -> None:
        assert self.persist_dir is not None
        for path in self.persist_dir.glob("*_graph.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                graph = CourseKnowledgeGraph.model_validate(data)
                self._graphs[graph.course_id] = graph
                logger.info("loaded_knowledge_graph", extra={"course_id": graph.course_id})
            except Exception as e:
                logger.error(f"failed_loading_graph_{path.name}: {e}")
