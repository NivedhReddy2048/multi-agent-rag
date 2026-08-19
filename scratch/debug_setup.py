import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("Starting setup...", flush=True)
from config.settings import Config
from core.verification.knowledge_verifier import KnowledgeVerifier
from core.models.domain import KnowledgeResult, SourceType
from agents.crag import CRAGAgent
from agents.synthesis import SynthesisAgent
from core.planner.execution_plan import ExecutionPlan
from core.planner.enums import EducationalIntent, DifficultyLevel, ExpectedOutputFormat, SourceStrategy
from core.models.verification import VerifiedKnowledgeCollection, VerifiedKnowledgeResult
from core.synthesis.prompt_builder import EducationalPromptBuilder

print("Imports completed!", flush=True)

cfg = Config()
print("Config loaded!", flush=True)

verifier = KnowledgeVerifier()
print("Verifier loaded!", flush=True)

crag = CRAGAgent(cfg)
print("CRAG loaded!", flush=True)

synthesis = SynthesisAgent(cfg)
print("Synthesis loaded!", flush=True)

print("ALL SETUP STEPS SUCCEEDED!", flush=True)
