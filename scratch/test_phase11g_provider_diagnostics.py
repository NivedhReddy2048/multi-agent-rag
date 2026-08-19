"""
EKIP Phase 11G — Provider Health & LLM Subsystem Diagnostic Script.
Inspects key presence, provider status, and direct API invocation results.
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from config.settings import Config
from core.llm.manager import LLMManager


def main():
    print("=" * 70)
    print("  EKIP PHASE 11G — PROVIDER DIAGNOSTICS")
    print("=" * 70)

    # 1. Inspect Config & Key presence
    print("\n--- 1. CONFIGURATION & ENVIRONMENT CHECK ---")
    print(f"GEMINI_API_KEY present : {bool(Config.GEMINI_API_KEY)} (len={len(Config.GEMINI_API_KEY)})")
    print(f"GROQ_API_KEY present   : {bool(Config.GROQ_API_KEY)} (len={len(Config.GROQ_API_KEY)})")
    print(f"COHERE_API_KEY present : {bool(Config.COHERE_API_KEY)} (len={len(Config.COHERE_API_KEY)})")
    print(f"MISTRAL_API_KEY present: {bool(Config.MISTRAL_API_KEY)} (len={len(Config.MISTRAL_API_KEY)})")
    print(f"PROVIDER_PRIORITY      : {Config.PROVIDER_PRIORITY}")

    print(f"GEMINI_MODEL           : {Config.GEMINI_MODEL}")
    print(f"GROQ_MODEL             : {Config.GROQ_MODEL}")
    print(f"COHERE_MODEL           : {Config.COHERE_MODEL}")
    print(f"MISTRAL_MODEL          : {Config.MISTRAL_MODEL}")

    # 2. Initialize LLMManager
    print("\n--- 2. INITIALIZING LLM MANAGER ---")
    manager = LLMManager()

    # 3. Test direct provider invocation
    print("\n--- 3. DIRECT PROVIDER INVOCATIONS ---")
    for name, provider in manager.registry.providers.items():
        print(f"\n[Provider: {name.upper()}]")
        print(f"  Primary Model : {provider.primary_model}")
        print(f"  Fallback Model: {provider.fallback_model}")
        print(f"  API Key Set   : {bool(provider.api_key)}")
        print(f"  Circuit State : {provider.current_status.value}")

        try:
            content, model_used, p_tok, c_tok = provider.generate(
                "Say hello in one word.",
                inputs={},
                temperature=0.1,
                max_tokens=20,
                timeout=10.0
            )
            print(f"  RESULT        : SUCCESS | Model: {model_used} | Output: '{content.strip()}'")
        except Exception as e:
            print(f"  RESULT        : FAILED | Error Type: {type(e).__name__} | Details: {e}")

    # 4. Execute manager.generate()
    print("\n--- 4. EXECUTING LLM MANAGER GENERATE ---")
    resp = manager.generate(
        prompt_or_chain_fn="Explain the core concepts of Transformer architectures in Machine Learning.",
        inputs={"query": "Explain the core concepts of Transformer architectures in Machine Learning."},
        timeout=15.0
    )

    print(f"Manager Response Success : {resp.success}")
    print(f"Provider                 : {resp.provider}")
    print(f"Model                    : {resp.model}")
    print(f"Error                    : {resp.error}")
    print(f"Failure Reason           : {getattr(resp, 'failure_reason', 'N/A')}")
    print(f"Attempts Detail          : {resp.attempts_detail}")


if __name__ == "__main__":
    main()
