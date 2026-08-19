"""General AI Knowledge Agent wrapping existing Multi-LLM Manager failover mechanism."""

import time
from typing import List
from agents.sources.base_agent import BaseKnowledgeAgent
from core.models.domain import KnowledgeResult, SourceType
from core.llm import LLMManager
from config.settings import Config
from core.logger import get_logger

logger = get_logger("agents.sources.general_ai_agent")


class GeneralAIKnowledgeAgent(BaseKnowledgeAgent):
    """Generates baseline reasoning and knowledge via Multi-LLM provider failover (Gemini -> Groq -> Cohere -> Mistral)."""

    def __init__(self, llm_manager: LLMManager = None):
        super().__init__(
            agent_name="GeneralAIKnowledgeAgent",
            source_type=SourceType.GENERAL_AI,
            provider_key="multi_llm"
        )
        self.llm_mgr = llm_manager

    def initialize(self) -> bool:
        if self.llm_mgr is None:
            self.llm_mgr = LLMManager(Config)
        self.is_initialized = True
        logger.info("GeneralAIKnowledgeAgent initialized with LLMManager")
        return True

    def health(self) -> bool:
        return self.llm_mgr is not None

    def execute(self, query: str, max_results: int = 1) -> List[KnowledgeResult]:
        if not self.is_initialized:
            self.initialize()

        t0 = time.time()
        results: List[KnowledgeResult] = []

        try:
            prompt = f"Provide a clear, accurate educational background overview for: '{query}'."
            llm_res = self.llm_mgr.generate(prompt)
            response_text = llm_res.content
            provider_used = llm_res.provider
            model_used = llm_res.model
            lat = (time.time() - t0) * 1000

            results.append(KnowledgeResult(
                provider=provider_used or "general_ai",
                source_type=SourceType.GENERAL_AI,
                title=f"General AI Knowledge Synthesis ({provider_used})",
                content=response_text,
                summary=response_text[:300] + "..." if len(response_text) > 300 else response_text,
                confidence=0.90,
                latency_ms=lat,
                metadata={"model": model_used, "provider": provider_used},
            ))
            logger.info(f"GeneralAIKnowledgeAgent generated knowledge using provider '{provider_used}' in {int(lat)}ms")
        except Exception as e:
            logger.error(f"GeneralAIKnowledgeAgent execution error: {e}", exc_info=True)

        return results
