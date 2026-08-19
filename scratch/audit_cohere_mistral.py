import os
import sys
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_mistralai import ChatMistralAI

load_dotenv()

print("--- TESTING COHERE LIVE MODELS ---", flush=True)
for m in ["command-r-plus", "command-r", "command-r-08-2024"]:
    try:
        llm = ChatCohere(model=m, cohere_api_key=os.getenv("COHERE_API_KEY"), max_retries=1, request_timeout=5.0)
        res = llm.invoke("Hi")
        print(f"  Cohere {m}: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  Cohere {m}: FAILED ({e})", flush=True)

print("\n--- TESTING MISTRAL LIVE MODELS ---", flush=True)
for m in ["mistral-large-latest", "mistral-small-latest", "open-mixtral-8x7b"]:
    try:
        llm = ChatMistralAI(model=m, mistral_api_key=os.getenv("MISTRAL_API_KEY"), max_retries=1, request_timeout=5.0)
        res = llm.invoke("Hi")
        print(f"  Mistral {m}: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  Mistral {m}: FAILED ({e})", flush=True)
