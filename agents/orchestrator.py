import time
import json
import re
import uuid
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseAgent, AgentResult, SOURCE_MODES
from .retrieval import RetrievalAgent
from .synthesis import SynthesisAgent
from .validation import ValidationAgent
from .crag import CRAGAgent
from core.logger import get_logger
from core.llm_manager import LLMManager
from analytics.telemetry import TelemetryTracker
from core.web_search import search_web

logger = get_logger("agents.orchestrator")


class OrchestratorAgent(BaseAgent):
    """Evidence-Driven Central Orchestrator routing queries, evaluating evidence, and controlling web fallback."""

    name = "orchestrator"
    description = "Evidence-driven central orchestrator controlling RAG execution pipeline"

    def __init__(self, config, engine, memory):
        self.cfg = config
        self.engine = engine
        self.memory = memory
        self.llm_manager = LLMManager(config)

        self.retrieval = RetrievalAgent(engine)
        self.synthesis = SynthesisAgent(config)
        self.validation = ValidationAgent()
        self.crag = CRAGAgent(config)

    @staticmethod
    def _is_web_source(source: Dict[str, Any]) -> bool:
        return "web_" in str(source.get("chunk_id", "")) or bool(source.get("url"))

    def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Execute web retrieval only after this orchestrator selected the branch."""
        logger.info("Orchestrator selected web-search branch for query '{}'.", query[:80])
        return search_web(query, getattr(self.cfg, "TAVILY_API_KEY", ""))

    @staticmethod
    def _evidence_bullets(sources: List[Dict[str, Any]], label: str) -> str:
        lines = []
        for index, source in enumerate(sources, start=1):
            snippet = str(source.get("content", source.get("snippet", ""))).strip().replace("\n", " ")
            if len(snippet) > 360:
                snippet = snippet[:357] + "..."
            lines.append(f"- {snippet} [{label} {index}]")
        return "\n".join(lines) or "- No evidence text was returned."

    def _enforce_mixed_sections(
        self, content: str, doc_sources: List[Dict[str, Any]], web_sources: List[Dict[str, Any]]
    ) -> str:
        """Guarantee visible source separation without asking validation to route or rewrite."""
        doc_heading = "## Information from Indexed Documents"
        web_heading = "## Information from External Web Sources"
        if doc_heading in content and web_heading in content:
            return content

        doc_sentences, web_sentences = [], []
        for sentence in re.split(r"(?<=[.!?])\s+", content.strip()):
            if "[WEB SOURCE" in sentence:
                web_sentences.append(sentence)
            else:
                doc_sentences.append(sentence)
        doc_text = " ".join(doc_sentences).strip() or self._evidence_bullets(doc_sources, "DOCUMENT SOURCE")
        web_text = " ".join(web_sentences).strip() or self._evidence_bullets(web_sources, "WEB SOURCE")
        logger.info("Orchestrator structurally separated mixed document and web evidence.")
        return f"{doc_heading}\n\n{doc_text}\n\n{web_heading}\n\n{web_text}"

    def _orchestrator_fallback(
        self, sources: List[Dict[str, Any]], source_mode: str, reason: str
    ) -> AgentResult:
        """Create the sole user-facing graceful fallback after an explicit evidence decision."""
        if not sources:
            logger.info("Orchestrator selected no-evidence response: {}.", reason)
            return AgentResult(
                content="The indexed documents do not contain enough information to answer this question.",
                confidence=0,
                sources=[],
                metadata={"source_mode": "none", "failure_reason": reason, "success": False},
                success=False,
                error=reason,
            )

        doc_sources = [s for s in sources if not self._is_web_source(s)]
        web_sources = [s for s in sources if self._is_web_source(s)]
        document_text = self._evidence_bullets(doc_sources, "DOCUMENT SOURCE")
        web_text = self._evidence_bullets(web_sources, "WEB SOURCE")
        if source_mode == "documents+web":
            content = (
                "The AI generation service is temporarily unavailable. Retrieved evidence is shown below.\n\n"
                f"## Information from Indexed Documents\n\n{document_text}\n\n"
                f"## Information from External Web Sources\n\n{web_text}"
            )
        elif source_mode == "web":
            content = "The AI generation service is temporarily unavailable. Retrieved web evidence is shown below.\n\n" + web_text
        else:
            content = "The AI generation service is temporarily unavailable. Retrieved document evidence is shown below.\n\n" + document_text
        logger.warning("Orchestrator selected graceful evidence fallback: {}.", reason)
        return AgentResult(
            content=content,
            confidence=0,
            sources=sources,
            metadata={"source_mode": source_mode, "failure_reason": reason, "success": False},
            success=False,
            error=reason,
        )

    @staticmethod
    def _calculate_confidence(
        retrieval_confidence: float, crag_score: float, synthesis_success: bool, fallback_occurred: bool
    ) -> int:
        """Compute answer confidence independently from faithfulness."""
        if not synthesis_success:
            return 0
        retrieval_quality = max(0.0, min(1.0, float(retrieval_confidence) / 100.0))
        crag_quality = max(0.0, min(1.0, float(crag_score)))
        provider_reliability = 0.85 if fallback_occurred else 1.0
        return round((0.45 * retrieval_quality + 0.35 * crag_quality + 0.20 * provider_reliability) * 100)

    def _synthesize(self, synth_ctx: Dict[str, Any], stream_writer=None) -> AgentResult:
        if stream_writer and callable(stream_writer):
            content = stream_writer(self.synthesis.stream_synthesis(synth_ctx))
            metadata = getattr(self.synthesis, "last_metadata", {})
            return AgentResult(
                content=content,
                sources=synth_ctx["documents"],
                metadata=metadata,
                success=bool(metadata.get("success", True)),
                error=metadata.get("error", ""),
            )
        return self.synthesis.run(synth_ctx)

    def classify_intent(self, query: str, history: List[Dict], request_id: str = "") -> Dict[str, Any]:
        q_lower = query.lower().strip()
        if re.search(r'^(hi|hello|hey|greetings|good morning|good afternoon)\b', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: GREETING")
            return {"intent": "GREETING", "doc_filter": None, "urgency": "low"}
        if re.search(r'^(list|show|get|display)\s+(docs|documents|files|index)', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: LIST")
            return {"intent": "LIST", "doc_filter": None, "urgency": "low"}
        if re.search(r'^(delete|remove)\s+(doc|document|file)', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: DELETE")
            return {"intent": "DELETE", "doc_filter": None, "urgency": "high"}
        if re.search(r'\b(report|comprehensive analysis|deep dive|study guide)\b', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: REPORT")
            return {"intent": "REPORT", "doc_filter": None, "urgency": "high"}
        if re.search(r'\b(compare|contrast|difference between)\b', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: COMPARE")
            return {"intent": "COMPARE", "doc_filter": None, "urgency": "medium"}
        if re.search(r'\b(summarize|summary|overview|key points|tldr)\b', q_lower):
            logger.info(f"[{request_id}] Fast-path regex intent matched: SUMMARY")
            return {"intent": "SUMMARY", "doc_filter": None, "urgency": "medium"}
        if len(q_lower.split()) < 15 or q_lower.startswith(("what", "how", "why", "who", "where", "when", "is", "are", "can")):
            logger.info(f"[{request_id}] Fast-path regex intent matched: QA")
            return {"intent": "QA", "doc_filter": None, "urgency": "medium"}

        prompt = ChatPromptTemplate.from_template("""
You are an intent classifier for an enterprise document RAG system.
Classify the user query into exactly one of these categories:
- QA: Specific factual question
- SUMMARY: Request for summary/overview
- REPORT: Request for comprehensive report, analysis, or study guide
- COMPARE: Compare multiple documents or topics
- LIST: List documents or metadata
- DELETE: Request to remove a document
- GREETING: Casual greeting

Return ONLY a JSON object with keys: intent, doc_filter (document name mentioned or null), urgency (low/medium/high).

Query: {query}
History: {history}
JSON:
""")
        history_summary = str(history[-3:]) if history else "[]"

        try:
            llm_res = self.llm_manager.generate(
                prompt,
                {"query": query, "history": history_summary},
                temperature=0.0,
                max_tokens=256,
                timeout=2.0,
            )
            raw = llm_res.content
            provider = llm_res.provider
            m = re.search(r'\{.*\}', str(raw), re.DOTALL)
            if m:
                res = json.loads(m.group())
                logger.info(f"[{request_id}] Classified intent: {res.get('intent')} via provider '{provider}' for query: '{query[:30]}...'")
                return res
        except Exception as e:
            logger.warning(f"[{request_id}] Intent classification fallback triggered: {e}")

        return {"intent": "QA", "doc_filter": None, "urgency": "medium"}

    def run(self, context: Dict[str, Any]) -> AgentResult:
        t0 = time.time()
        request_id = context.get("request_id") or f"req_{uuid.uuid4().hex[:8]}"
        query, history = context["query"], context.get("history", [])
        filters = context.get("filters", {})
        stage_times: Dict[str, float] = {}

        t_intent = time.time()
        classification = self.classify_intent(query, history, request_id=request_id)
        intent, doc_filter = classification.get("intent", "QA"), classification.get("doc_filter")
        stage_times["intent_classification_ms"] = round((time.time() - t_intent) * 1000, 2)
        trace = [f"🎯 Intent: {intent} (req: {request_id})"]

        if intent == "DELETE":
            from .admin import AdminAgent
            return AdminAgent(self.engine).run({"action": "delete", "doc_name": doc_filter or query, "query": query})
        if intent == "LIST":
            docs = self.engine.list_docs()
            content = "\n".join(f"- **{k}**: {v['chunks']} chunks, {v['pages']} pages" for k, v in docs.items()) or "No documents currently indexed."
            return AgentResult(content=content, confidence=100, agent_trace=trace + ["📂 Listed documents"], metadata={"source_mode": "none"})
        if intent == "GREETING":
            return AgentResult(content="Hello! I'm your Enterprise Knowledge Intelligence assistant. Upload documents and ask me anything about them.", confidence=100, agent_trace=trace + ["👋 Greeting handler"], metadata={"source_mode": "none"})

        # REPORT intentionally shares this same retrieval → CRAG → decision → synthesis
        # → validation → telemetry path; ReportAgent is no longer a bypass.
        trace.append("🔍 RetrievalAgent")
        retrieved = self.retrieval.run({
            "query": query, "doc_filter": [doc_filter] if doc_filter else None, "filters": filters,
            "top_k": 50 if intent in ("SUMMARY", "REPORT") else 8, "request_id": request_id,
        })
        stage_times.update(retrieved.metadata.get("stage_latency_ms", {}))
        doc_sources = retrieved.sources or []

        t_crag = time.time()
        trace.append("🔄 CRAGAgent")
        crag_result = self.crag.run({"query": query, "documents": doc_sources})
        stage_times["crag_evaluation_ms"] = round((time.time() - t_crag) * 1000, 2)
        trace.extend(crag_result.agent_trace)
        crag_score = float(crag_result.metadata.get("retrieval_score", 0.0))

        web_sources: List[Dict[str, Any]] = []
        if crag_result.metadata.get("sufficient", False) and doc_sources:
            source_mode, final_sources = "documents", doc_sources
            logger.info("[{}] Orchestrator selected document synthesis.", request_id)
        elif getattr(self.cfg, "ENABLE_WEB_SEARCH", True):
            trace.append("🌐 Orchestrator Web Search")
            web_sources = self._search_web(query)
            final_sources = doc_sources + web_sources
            source_mode = "documents+web" if doc_sources and web_sources else ("web" if web_sources else "none")
            logger.info("[{}] Orchestrator selected source mode '{}'.", request_id, source_mode)
        else:
            final_sources, source_mode = [], "none"
            logger.info("[{}] Orchestrator selected no-evidence branch because web search is disabled.", request_id)

        t_synthesis = time.time()
        synthesized: AgentResult
        if source_mode == "none":
            synthesized = self._orchestrator_fallback([], "none", "INSUFFICIENT_EVIDENCE")
        else:
            synth_ctx = {"query": query, "documents": final_sources, "history": history, "intent": intent, "source_mode": source_mode, "request_id": request_id}
            synthesized = self._synthesize(synth_ctx, context.get("stream_writer"))
            synthesis_failed = not synthesized.success or not synthesized.content.strip() or synthesized.content.strip() == "INSUFFICIENT_CONTEXT"
            if synthesis_failed and source_mode == "documents" and getattr(self.cfg, "ENABLE_WEB_SEARCH", True):
                trace.append("🌐 Orchestrator Retry With Web Evidence")
                web_sources = self._search_web(query)
                if web_sources:
                    final_sources, source_mode = doc_sources + web_sources, "documents+web"
                    synth_ctx.update({"documents": final_sources, "source_mode": source_mode})
                    synthesized = self._synthesize(synth_ctx, context.get("stream_writer"))
                    synthesis_failed = not synthesized.success or not synthesized.content.strip() or synthesized.content.strip() == "INSUFFICIENT_CONTEXT"
            if synthesis_failed:
                synthesized = self._orchestrator_fallback(final_sources, source_mode, synthesized.metadata.get("failure_reason") or "SYNTHESIS_FAILED")

        if source_mode not in SOURCE_MODES or (source_mode != "none" and not final_sources):
            logger.error("[{}] Invalid evidence state mode='{}', source count={}; selecting no-evidence fallback.", request_id, source_mode, len(final_sources))
            final_sources, source_mode = [], "none"
            synthesized = self._orchestrator_fallback([], source_mode, "INVALID_EVIDENCE_STATE")
        if source_mode == "documents+web" and synthesized.content:
            synthesized.content = self._enforce_mixed_sections(synthesized.content, doc_sources, web_sources)
        stage_times["llm_synthesis_ms"] = round((time.time() - t_synthesis) * 1000, 2)

        t_validation = time.time()
        trace.append("🛡️ ValidationAgent")
        validated = self.validation.run({"answer": synthesized.content, "sources": final_sources, "query": query, "source_mode": source_mode, "request_id": request_id})
        stage_times["validation_ms"] = round((time.time() - t_validation) * 1000, 2)
        if not validated.success and source_mode != "none":
            synthesized = self._orchestrator_fallback(final_sources, source_mode, "VALIDATION_EMPTY_OUTPUT")
            validated = self.validation.run({"answer": synthesized.content, "sources": final_sources, "query": query, "source_mode": source_mode, "request_id": request_id})

        synth_meta = synthesized.metadata if isinstance(synthesized.metadata, dict) else {}
        synthesis_success = bool(synth_meta.get("success", synthesized.success))
        final_confidence = self._calculate_confidence(
            retrieved.confidence, crag_score, synthesis_success, bool(synth_meta.get("fallback_occurred", False))
        )
        faithfulness = float(validated.metadata.get("faithfulness", 0.0))
        total_time = int((time.time() - t0) * 1000)
        decision = "Grounded Synthesis" if source_mode == "documents" else ("Web Augmented Synthesis" if "web" in source_mode else "Insufficient Context")

        t_memory = time.time()
        TelemetryTracker.record_query_metrics(
            memory_instance=self.memory, query=query, intent=intent, confidence=final_confidence,
            faithfulness=faithfulness, blocked=not synthesis_success, latency_ms=total_time,
            agent_trace=trace + validated.agent_trace, source_mode=source_mode,
            crag_used=bool(web_sources), web_results_count=len(web_sources),
        )
        stage_times["memory_persistence_ms"] = round((time.time() - t_memory) * 1000, 2)
        final_trace = trace + validated.agent_trace + [f"⏱️ Stage breakdown (ms): {stage_times}"]

        return AgentResult(
            content=validated.content, confidence=final_confidence, sources=final_sources, agent_trace=final_trace,
            metadata={
                "request_id": request_id, "intent": intent, "total_latency_ms": total_time,
                "stage_latency_ms": stage_times, "faithfulness": faithfulness, "source_mode": source_mode,
                "crag_used": bool(web_sources), "crag_confidence": crag_result.confidence, "crag_score": crag_score,
                "web_results_count": len(web_sources), "retrieved_chunks_count": len(doc_sources),
                "provider": synth_meta.get("provider", "NONE" if not synthesis_success else "Unknown"),
                "model": synth_meta.get("model", "none" if not synthesis_success else "Unknown"),
                "latency_ms": synth_meta.get("latency_ms", total_time), "tokens": synth_meta.get("tokens", 0),
                "fallback_occurred": bool(synth_meta.get("fallback_occurred", False)),
                "fallback_chain": synth_meta.get("fallback_chain", []), "error": synth_meta.get("error", ""),
                "failure_reason": synth_meta.get("failure_reason", ""), "synthesis_success": synthesis_success,
                "validation_warnings": validated.metadata.get("warnings", []), "decision": decision,
            },
            success=synthesis_success,
            error=synth_meta.get("error", ""),
        )
