"""Mind Map Generator Plugin Module creating structured hierarchical JSON trees for visualization."""

from typing import Dict, Any, Optional, List
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession


class MindMapModule(LearningModule):
    """Generates structured hierarchical JSON mind maps from EducationalResponse."""

    name: str = "MindMap"
    description: str = "Generates structured JSON tree hierarchies for mind map visualization."
    version: str = "1.0.0"

    def process(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        root_topic = response.query

        # Key Takeaways as Sub-branches
        takeaway_children = [{"name": kt} for kt in response.key_takeaways]

        # Glossary terms as Sub-branches
        term_children = [{"name": f"{t}: {d[:40]}..."} for t, d in response.important_terms.items()]

        mind_map = {
            "name": root_topic,
            "children": [
                {
                    "name": "🧠 Core Principles & Takeaways",
                    "children": takeaway_children,
                },
                {
                    "name": "📖 Key Terms & Definitions",
                    "children": term_children,
                },
                {
                    "name": "🌐 Evidence Sources",
                    "children": [{"name": p} for p in response.providers_used],
                },
            ],
        }

        return {
            "module_name": self.name,
            "topic": root_topic,
            "mind_map_tree": mind_map,
        }
