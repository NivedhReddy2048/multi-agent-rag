"""Evidence-Grounded Synthesis Agent for EKIP Platform.

Enforces zero-prior-knowledge generation based strictly on supplied context.
"""

import time
from typing import Dict, Any, Generator
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent, AgentResult
from core.logger import get_logger
from core.llm_manager import LLMManager

logger = get_logger("agents.synthesis")


class SynthesisAgent(BaseAgent):
    """Synthesis Agent producing strictly evidence-grounded LLM answers with citation tagging."""

    name = "synthesis"
    description = "Generates grounded answers strictly using supplied context"

    def __init__(self, config):
        self.cfg = config
        self.llm_manager = LLMManager(config)

    def _prepare_prompt_and_context(self, context: Dict[str, Any]):
        query = context["query"]
        docs = context.get("documents", [])
        history = context.get("history", [])
        intent = context.get("intent", "QA")
        source_mode = context.get("source_mode", "documents")

        doc_parts = []
        web_parts = []

        for i, d in enumerate(docs):
            src = d.get("source_file", "Unknown")
            page = d.get("page", "?")
            is_web = "web_" in str(d.get("chunk_id", "")) or "url" in d or "Web Search" in src
            content = d.get("content", "").strip()

            if is_web:
                title = d.get("title") or src
                url = d.get("url", "")
                web_parts.append(f"[WEB SOURCE {len(web_parts)+1}: {title} ({url})]\n{content}")
            else:
                doc_parts.append(f"[DOCUMENT SOURCE {len(doc_parts)+1}: {src} | Page {page}]\n{content}")

        context_blocks = []
        if doc_parts:
            context_blocks.append("### INDEXED DOCUMENT SOURCES:\n" + "\n\n".join(doc_parts))
        if web_parts:
            context_blocks.append("### EXTERNAL WEB SEARCH RESULTS:\n" + "\n\n".join(web_parts))

        full_context = "\n\n---\n\n".join(context_blocks) if context_blocks else "No context sources available."

        mixed_instruction = ""
        if doc_parts and web_parts:
            mixed_instruction = (
                "\nCRITICAL INSTRUCTION FOR MIXED SOURCES:\n"
                "Both indexed documents and web search results are provided.\n"
                "You MUST structure your response into two clearly labeled sections:\n"
                "1. '### According to your indexed documents:' (cite [DOCUMENT SOURCE N])\n"
                "2. '### Additional information from web search:' (cite [WEB SOURCE N])\n"
                "Never merge document sources and web search results invisibly."
            )

        system_msg = (
            "You are a retrieval-grounded assistant.\n"
            "You will ONLY answer using the supplied context.\n"
            "Do not use any prior knowledge.\n"
            "Do not invent facts.\n"
            "State only information supported by the supplied context."
            f"{mixed_instruction}"
        )

        prompt = ChatPromptTemplate.from_template(f"""{system_msg}

Conversation History:
{{history}}

Supplied Context:
{{context}}

User Question: {{question}}

Answer:
""")

        history_str = "\n".join([f"{'User' if m.get('role')=='user' else 'Assistant'}: {str(m.get('content', ''))[:200]}" for m in history[-4:]])
        return prompt, {"history": history_str, "context": full_context, "question": query}, intent, docs, query, source_mode

    def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        prompt, inputs, intent, docs, query, source_mode = self._prepare_prompt_and_context(context)

        llm_res = self.llm_manager.generate(
            prompt,
            inputs,
            temperature=0.1,
            max_tokens=4096,
            timeout=getattr(self.cfg, "LLM_MAX_WAIT_SECONDS", 2.0),
            documents=docs,
            query=query,
            intent=intent,
        )

        latency = int((time.time() - t0) * 1000)
        self.last_metadata = {
            "latency_ms": latency,
            "intent": intent,
            "provider": llm_res.provider,
            "model": llm_res.model,
            "fallback_occurred": llm_res.fallback_occurred,
            "fallback_chain": llm_res.fallback_chain,
            "tokens": llm_res.tokens,
            "error": llm_res.error,
            "failure_reason": getattr(llm_res, "failure_reason", ""),
            "success": llm_res.success,
            "source_mode": source_mode,
        }
        return AgentResult(
            content=llm_res.content,
            confidence=85 if docs else 0,
            sources=docs,
            agent_trace=[f"Generated answer in {latency}ms (Provider: {llm_res.provider}, Mode: {source_mode})"],
            metadata=self.last_metadata,
            success=llm_res.success,
            error=llm_res.error,
        )

    def stream_synthesis(self, context: Dict[str, Any]) -> Generator[str, None, None]:
        """Streaming generator with multi-provider failover."""
        res = self.run(context)
        self.last_metadata = res.metadata
        yield res.content
