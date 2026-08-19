"""Guided Learning Engine & Learning Path Generator for EKIP Platform."""

import re
from typing import List, Dict, Any, Optional
from core.models.synthesis import LearningPath
from core.planner.execution_plan import ExecutionPlan
from core.logger import get_logger

logger = get_logger("core.synthesis.guided_learning")

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "you", "your", "he", "she", "it", "they", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "a", "an", "the",
    "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", "need", "needed", "needs", "want",
    "wants", "please", "tell", "show", "find", "give", "recommend", "recommendation", "recommendations", "recommending",
    "explain", "explains", "explaining", "describe", "describes", "concept", "concepts", "understanding", "learn",
    "learning", "tutorial", "tutorials", "video", "videos", "lecture", "lectures", "youtube", "book", "books", "what"
}

STOP_TOPICS = {
    "need", "video", "videos", "youtube", "recommend", "recommendation", "explain", "explains", "show", "find",
    "give", "tell", "what", "how", "why", "who", "where", "when", "this", "that", "topic", "core concept", "general topic"
}


def extract_canonical_topic(
    query: str,
    topic: str = "",
    plan: Optional[ExecutionPlan] = None
) -> str:
    """Extract a clean, canonical educational subject from the query, stripping request filler words."""
    if topic and topic.strip() and topic.strip().lower() not in STOP_TOPICS:
        return topic.strip().title()

    q_lower = query.lower().strip()

    # Step 1: Remove common request prefixes
    prefix_pattern = r'^(i need|need|please|can you|could you|tell me|show me|find me|give me|recommend|recommendation|recommendations|recommend videos for|recommend top learning video concepts for|explain|describe|what is|what are|how does|how do|definition of|overview of|summary of|intro to|introduction to|basics of)\s+'
    cleaned = re.sub(prefix_pattern, '', q_lower, flags=re.IGNORECASE).strip()

    # Step 2: Filter filler words inside remaining query text
    filler_words = {"youtube", "video", "videos", "lecture", "lectures", "tutorial", "tutorials", "concepts", "concept", "understanding", "learn", "learning", "guide", "resource", "resources", "top", "best", "good", "study", "notes", "paper", "papers", "that", "which", "explains", "explain", "about", "for", "with", "from", "a", "an", "the", "i", "need"}
    
    words = [w for w in re.split(r'\s+', cleaned) if w and w.lower() not in filler_words]
    candidate = " ".join(words).strip()
    candidate = re.sub(r'^[^\w]+|[^\w]+$', '', candidate)

    # Step 3: Fallback if candidate is empty or invalid
    if not candidate or candidate.lower() in STOP_TOPICS:
        all_words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query) if w.lower() not in STOP_WORDS]
        candidate = " ".join(all_words[:3]) if all_words else "General Educational Topic"

    return candidate.title()


class GuidedLearningEngine:
    """Generates context-aware follow-up questions and structured 4-tier learning paths."""

    def generate_guided_questions(
        self,
        query: str,
        topic: str = "",
        plan: Optional[ExecutionPlan] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Generate three topic-specific, non-generic follow-up questions."""
        curr_topic = extract_canonical_topic(query, topic, plan)
        t_lower = curr_topic.lower()

        # Topic-specific domain rules
        if "neural network" in t_lower or "deep learning" in t_lower or "neural network" in query.lower():
            return [
                "How does backpropagation calculate gradients across hidden layers?",
                "What role do non-linear activation functions (ReLU, Sigmoid) play?",
                "How do Convolutional Neural Networks (CNNs) differ from dense networks?",
            ]
        elif "quantum" in t_lower or "quantum" in query.lower():
            return [
                "How does quantum superposition enable parallel state evaluation?",
                "What is quantum entanglement and how does it affect qubit states?",
                "How does Shor's algorithm achieve exponential speedup over classical algorithms?",
            ]
        elif "database" in t_lower or "sql" in t_lower or "rag" in t_lower or "retrieval" in t_lower:
            return [
                "How does vector similarity search compare with BM25 keyword retrieval?",
                "What strategies prevent index degradation in high-dimensional vector databases?",
                "How does Reranking improve precision in hybrid search pipelines?",
            ]
        elif "python" in t_lower or "code" in t_lower or "programming" in t_lower:
            return [
                "How do Python memory management and garbage collection function?",
                "What are decorators and how do they modify function behavior?",
                "How do asyncio and concurrency models handle asynchronous IO?",
            ]
        elif "discipline" in t_lower or "discipline" in query.lower():
            return [
                "What are the core psychological principles behind building long-term discipline?",
                "How does self-discipline differ from temporary motivation in habit formation?",
                "What actionable strategies help maintain consistency during periods of low energy?",
            ]
        else:
            return [
                f"What are the core foundational principles underlying {curr_topic}?",
                f"How is {curr_topic} applied in real-world practical scenarios?",
                f"What are the key challenges and best practices when working with {curr_topic}?",
            ]

    def generate_learning_path(
        self,
        query: str,
        topic: str = "",
        plan: Optional[ExecutionPlan] = None
    ) -> LearningPath:
        """Generate a 4-tier structured learning path: Prerequisites -> Current -> Next -> Advanced."""
        curr_topic = extract_canonical_topic(query, topic, plan)
        t_lower = curr_topic.lower()

        if "neural network" in t_lower or "deep learning" in t_lower or "backpropagation" in t_lower or "neural network" in query.lower():
            return LearningPath(
                current_topic="Artificial Neural Networks & Deep Learning",
                prerequisites=["Linear Algebra & Matrix Operations", "Multivariable Calculus & Derivatives", "Python & NumPy Fundamentals"],
                next_topics=["Convolutional Neural Networks (CNNs)", "Recurrent Networks & LSTMs", "Transformer Architectures"],
                advanced_topics=["Attention Mechanisms & Self-Attention", "Large Language Model Fine-Tuning", "Reinforcement Learning from Human Feedback (RLHF)"],
            )
        elif "rag" in t_lower or "retrieval" in t_lower or "rag" in query.lower():
            return LearningPath(
                current_topic="Retrieval-Augmented Generation (RAG)",
                prerequisites=["Basic NLP Concepts", "Vector Embeddings", "LLM Prompt Engineering"],
                next_topics=["Hybrid Search (Dense + Sparse)", "Cross-Encoder Reranking", "Corrective RAG (CRAG)"],
                advanced_topics=["Multi-Agent Orchestration", "GraphRAG & Knowledge Graphs", "Autonomous Evidence Verification Engines"],
            )
        else:
            return LearningPath(
                current_topic=curr_topic,
                prerequisites=[f"Foundations of {curr_topic}", f"Core Principles of {curr_topic}", "Basic Terminology"],
                next_topics=[f"Practical Applications of {curr_topic}", f"Implementing {curr_topic}", "System Integration"],
                advanced_topics=[f"Advanced {curr_topic} Optimization", "Enterprise Scaling", "State-of-the-Art Research"],
            )


# Global singleton instance
guided_learning_engine = GuidedLearningEngine()

