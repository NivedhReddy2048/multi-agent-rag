"""EKIP Modular Knowledge Source Agents Package."""

from agents.sources.base_agent import BaseKnowledgeAgent
from agents.sources.document_agent import DocumentKnowledgeAgent
from agents.sources.general_ai_agent import GeneralAIKnowledgeAgent
from agents.sources.trusted_web_agent import TrustedWebKnowledgeAgent
from agents.sources.wikipedia_agent import WikipediaKnowledgeAgent
from agents.sources.semantic_scholar_agent import SemanticScholarKnowledgeAgent
from agents.sources.arxiv_agent import ArxivKnowledgeAgent
from agents.sources.google_books_agent import GoogleBooksKnowledgeAgent
from agents.sources.youtube_agent import YoutubeKnowledgeAgent
from agents.sources.github_agent import GithubKnowledgeAgent

__all__ = [
    "BaseKnowledgeAgent",
    "DocumentKnowledgeAgent",
    "GeneralAIKnowledgeAgent",
    "TrustedWebKnowledgeAgent",
    "WikipediaKnowledgeAgent",
    "SemanticScholarKnowledgeAgent",
    "ArxivKnowledgeAgent",
    "GoogleBooksKnowledgeAgent",
    "YoutubeKnowledgeAgent",
    "GithubKnowledgeAgent",
]
