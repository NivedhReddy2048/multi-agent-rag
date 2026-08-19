import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

print("--- TESTING CHATGOOGLEGENERATIVEAI WITH MAX_RETRIES & TIMEOUT ---", flush=True)
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        max_retries=1,
        request_timeout=10.0
    )
    res = llm.invoke("Hi")
    print("Gemini 2.5 flash invoke with max_retries=1, request_timeout=10.0: SUCCESS", flush=True)
    print("  Content preview:", res.content[:50], flush=True)
except Exception as e:
    print("Gemini invoke failed:", e, flush=True)

print("\n--- TESTING CHATGROQ WITH MAX_RETRIES & TIMEOUT ---", flush=True)
try:
    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        max_retries=1,
        request_timeout=10.0
    )
    res = llm.invoke("Hi")
    print("Groq openai/gpt-oss-20b invoke with max_retries=1, request_timeout=10.0: SUCCESS", flush=True)
    print("  Content preview:", res.content[:50], flush=True)
except Exception as e:
    print("Groq invoke failed:", e, flush=True)

print("\n--- TESTING GROQ/COMPOUND VS OPENAI/GPT-OSS-20B WITH LARGE PROMPT (10,000 CHARS) ---", flush=True)
large_prompt = "Explain quantum physics in detail. " + ("Here is extra context. " * 300)
print(f"Prompt length: {len(large_prompt)} chars", flush=True)

for model_name in ["groq/compound", "openai/gpt-oss-20b"]:
    try:
        llm = ChatGroq(
            model=model_name,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            max_retries=1,
            request_timeout=15.0
        )
        res = llm.invoke(large_prompt)
        print(f"  {model_name} with large prompt: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  {model_name} with large prompt: FAILED ({e})", flush=True)
