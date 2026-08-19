import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

print("--- TESTING ALL VALID GROQ MODELS FOR RAG PAYLOADS ---", flush=True)

prompt = "Explain computer architecture. " + ("Here is document context chunk. " * 300)
print(f"Prompt length: {len(prompt)} chars", flush=True)

for m in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "groq/compound-mini"]:
    try:
        llm = ChatGroq(
            model=m,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_retries=1,
            request_timeout=15.0
        )
        res = llm.invoke(prompt)
        print(f"  {m}: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  {m}: FAILED ({e})", flush=True)
