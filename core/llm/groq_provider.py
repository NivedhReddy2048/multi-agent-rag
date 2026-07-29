"""Groq LLM Provider Implementation."""

from typing import Dict, Any, Optional, Tuple
from langchain_groq import ChatGroq
from .base_provider import BaseLLMProvider, ProviderStatus
from core.logger import get_logger

logger = get_logger("core.llm.groq_provider")


class GroqProvider(BaseLLMProvider):
    """Groq Provider Implementation."""

    def __init__(self, primary_model: str, fallback_model: str, api_key: str):
        super().__init__("groq", primary_model, fallback_model, api_key)

    def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 10.0):
        cache_key = (model_name, temperature, max_tokens, timeout)
        if cache_key in self.client_cache:
            return self.client_cache[cache_key]

        client = ChatGroq(
            model=model_name,
            groq_api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=timeout,
        )
        self.client_cache[cache_key] = client
        return client

    def generate(
        self,
        prompt_or_chain_fn,
        inputs: Dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 10.0,
        model_override: Optional[str] = None,
    ) -> Tuple[str, str, int, int]:
        model_name = model_override or self.primary_model
        logger.info(f"ENTER GROQ provider generation | Model: {model_name}")
        try:
            client = self.get_client(model_name, temperature, max_tokens, timeout)

            if callable(prompt_or_chain_fn):
                response = prompt_or_chain_fn(client)
            elif isinstance(prompt_or_chain_fn, str):
                response = client.invoke(prompt_or_chain_fn)
            else:
                chain = prompt_or_chain_fn | client
                response = chain.invoke(inputs)

            content = response.content if hasattr(response, "content") else str(response)

            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, "response_metadata") and "token_usage" in response.response_metadata:
                usage = response.response_metadata["token_usage"]
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)

            if prompt_tokens == 0:
                completion_tokens = len(content.split())
                prompt_tokens = len(str(inputs).split())

            logger.info(f"EXIT GROQ provider generation | Model: {model_name} | Success")
            return content, model_name, prompt_tokens, completion_tokens
        except Exception as e:
            logger.warning(f"EXIT GROQ provider generation | Model: {model_name} | FAILED: {e}")
            raise e
