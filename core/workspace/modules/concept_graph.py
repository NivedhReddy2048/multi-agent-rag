"""Concept Relationship Graph Generator Plugin Module creating node/edge graphs."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class ConceptGraphModule(LearningModule):
    """Generates concept relationship graphs connecting prerequisites, applications, and connected topics."""

    name: str = "ConceptGraph"
    description: str = "Generates concept relationship graphs connecting central topic to prerequisites, applications, and related concepts."
    version: str = "1.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        central_node = response.query

        prereqs = response.learning_path.prerequisites if response.learning_path else ["Foundational Mathematics", "Basic Computer Science"]
        next_topics = response.learning_path.next_topics if response.learning_path else ["Advanced Applications", "System Integration"]
        adv_topics = response.learning_path.advanced_topics if response.learning_path else ["State of the Art Research"]

        nodes = [{"id": central_node, "label": central_node, "group": "central"}]
        edges = []

        for p in prereqs:
            nodes.append({"id": p, "label": p, "group": "prerequisite"})
            edges.append({"from": p, "to": central_node, "relation": "PREREQUISITE_FOR"})

        for nxt in next_topics:
            nodes.append({"id": nxt, "label": nxt, "group": "next_topic"})
            edges.append({"from": central_node, "to": nxt, "relation": "LEADS_TO"})

        for adv in adv_topics:
            nodes.append({"id": adv, "label": adv, "group": "advanced"})
            edges.append({"from": central_node, "to": adv, "relation": "EXTENDS_TO"})

        return {
            "module_name": self.name,
            "central_topic": central_node,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "graph": {"nodes": nodes, "edges": edges},
        }
