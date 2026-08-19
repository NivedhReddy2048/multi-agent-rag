"""EKIP KnowledgePlanner Concrete Implementation.

Implements the KnowledgePlanner abstract interface using zero-network RuleBasedPlannerEngine.
"""

from typing import List, Dict, Any, Optional
from core.interfaces.planner import KnowledgePlanner
from core.planner.rules import RuleBasedPlannerEngine
from core.planner.execution_plan import ExecutionPlan
from core.logger import get_logger

logger = get_logger("core.planner.knowledge_planner")


class ConcreteKnowledgePlanner(KnowledgePlanner):
    """Concrete implementation of KnowledgePlanner decision engine."""

    def __init__(self):
        self.engine = RuleBasedPlannerEngine()

    def plan(self, question: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Evaluate question semantics and return list of target provider/source names."""
        history = context.get("conversation_history", []) if context else []
        plan_obj = self.engine.generate_plan(question, history)
        return [s.value for s in plan_obj.selected_sources]

    def create_execution_plan(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> ExecutionPlan:
        """Generate structured, explainable ExecutionPlan contract."""
        logger.info(f"Generating ExecutionPlan for question: '{question[:40]}...'")
        return self.engine.generate_plan(question, history or [])


# Global singleton instance
knowledge_planner = ConcreteKnowledgePlanner()

__all__ = ["ConcreteKnowledgePlanner", "knowledge_planner"]
