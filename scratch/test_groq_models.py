"""
Test available Groq models.
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.llm.groq_provider import GroqProvider

candidate_models = [
    "openai/gpt-oss-20b",
    "qwen-2.5-32b",
    "deepseek-r1-distill-qwen-32b",
    "llama-3.3-70b-specdec",
    "groq/compound",
]

provider = GroqProvider("test", "test", Config.GROQ_API_KEY)

for model in candidate_models:
    try:
        content, model_used, p_tok, c_tok = provider.generate(
            "Hello", inputs={}, temperature=0.1, max_tokens=10, timeout=10.0, model_override=model
        )
        print(f"[SUCCESS] Groq model '{model}' works! Output: '{content.strip()}'")
    except Exception as e:
        err_msg = str(e).split("\n")[0]
        print(f"[FAILED ] Groq model '{model}': {err_msg[:100]}")
