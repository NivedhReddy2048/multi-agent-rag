import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

print("--- TESTING GROQ MODEL SIZE CAPACITY (15k, 30k, 50k CHARS) ---", flush=True)

for size in [15000, 30000, 50000]:
    prompt = "Explain machine learning in detail. " + ("Sample context line for RAG. " * (size // 30))
    print(f"\nTesting prompt length: {len(prompt)} chars ({len(prompt)//4} tokens approx)", flush=True)
    for model_name in ["groq/compound", "openai/gpt-oss-20b"]:
        try:
            llm = ChatGroq(
                model=model_name,
                groq_api_key=os.getenv("GROQ_API_KEY"),
                max_retries=1,
                request_timeout=15.0
            )
            res = llm.invoke(prompt)
            print(f"  {model_name}: SUCCESS (len={len(res.content)})", flush=True)
        except Exception as e:
            print(f"  {model_name}: FAILED ({e})", flush=True)
