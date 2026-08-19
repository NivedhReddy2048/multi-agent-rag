import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("--- AUDITING SDK VERSIONS ---", flush=True)
import langchain_google_genai
import langchain_groq
import google.generativeai as genai
import groq

print(f"langchain_google_genai version: {getattr(langchain_google_genai, '__version__', 'unknown')}", flush=True)
print(f"langchain_groq version: {getattr(langchain_groq, '__version__', 'unknown')}", flush=True)
print(f"google.generativeai version: {getattr(genai, '__version__', 'unknown')}", flush=True)
print(f"groq version: {getattr(groq, '__version__', 'unknown')}", flush=True)

print("\n--- AUDITING CHATGOOGLEGENERATIVEAI SIGNATURE ---", flush=True)
import inspect
from langchain_google_genai import ChatGoogleGenerativeAI
sig = inspect.signature(ChatGoogleGenerativeAI.__init__)
print("ChatGoogleGenerativeAI params:", list(sig.parameters.keys()), flush=True)

print("\n--- AUDITING CHATGROQ SIGNATURE ---", flush=True)
from langchain_groq import ChatGroq
sig_groq = inspect.signature(ChatGroq.__init__)
print("ChatGroq params:", list(sig_groq.parameters.keys()), flush=True)

print("\n--- TESTING GEMINI LIVE MODELS ---", flush=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
try:
    models = genai.list_models()
    g_list = [m.name.replace("models/", "") for m in models if "generateContent" in m.supported_generation_methods]
    print("Available Gemini models:", g_list, flush=True)
except Exception as e:
    print("Gemini model list error:", e, flush=True)

print("\n--- TESTING GROQ LIVE MODELS ---", flush=True)
try:
    g_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    g_models = g_client.models.list()
    print("Available Groq models:", [m.id for m in g_models.data], flush=True)
except Exception as e:
    print("Groq model list error:", e, flush=True)

print("\n--- TESTING GEMINI INDIVIDUAL MODEL INVOCATIONS ---", flush=True)
for m in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
    try:
        llm = ChatGoogleGenerativeAI(model=m, google_api_key=os.getenv("GEMINI_API_KEY"), max_retries=1, request_timeout=5.0)
        res = llm.invoke("Hi")
        print(f"  {m}: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  {m}: FAILED ({e})", flush=True)

print("\n--- TESTING GROQ INDIVIDUAL MODEL INVOCATIONS ---", flush=True)
for m in ["groq/compound", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]:
    try:
        llm = ChatGroq(model=m, groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=1, request_timeout=5.0)
        res = llm.invoke("Hi")
        print(f"  {m}: SUCCESS (len={len(res.content)})", flush=True)
    except Exception as e:
        print(f"  {m}: FAILED ({e})", flush=True)
