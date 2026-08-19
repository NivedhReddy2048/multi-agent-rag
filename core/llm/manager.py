"""Singleton Enterprise Multi-LLM Manager with Circuit Breaker & Intelligent Router."""

import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from .base_provider import BaseLLMProvider, ProviderStatus, HealthCheckReport, LLMResponse
from .provider_registry import ProviderRegistry
from .health_monitor import HealthMonitor
from .router import IntelligentRouter
from core.logger import get_logger

logger = get_logger("core.llm.manager")


class LLMManager:
    """Singleton Enterprise Multi-LLM Orchestrator with Intelligent Router & Circuit Breaker."""

    _instance: Optional["LLMManager"] = None

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config=None):
        if self._initialized:
            if config:
                self.cfg = config
            return

        from config.settings import Config
        self.cfg = config or Config

        self.registry = ProviderRegistry(self.cfg)
        self.health_monitor = HealthMonitor(self.registry)
        self.router = IntelligentRouter(self.registry)

        # Do not issue blocking network calls while constructing a request path.
        # Explicit diagnostics and periodic open-circuit probes own health checks.
        logger.info("Initialized provider health cache without startup network probes.")

        self._initialized = True
        logger.info("Initialized Enterprise Multi-LLM Manager with Circuit Breaker & Intelligent Router.")

    def generate(
        self,
        prompt_or_chain_fn,
        inputs: Dict[str, Any] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 15.0,
        documents: Optional[List[Dict[str, Any]]] = None,
        query: str = "",
        intent: Optional[str] = None,
    ) -> LLMResponse:
        """
        Execute LLM generation with Intelligent Router, Deadline-Aware Failover,
        Request-Size Gating, and Circuit Breaker health cache.
        """
        import concurrent.futures

        inputs = inputs or {}
        request_id = str(uuid.uuid4())[:8]
        t0 = time.time()
        generation_start = time.monotonic()
        deadline = generation_start + max(1.0, float(timeout))
        
        fallback_chain: List[str] = []
        attempts_detail: List[Dict[str, Any]] = []

        # Determine prompt characteristics for telemetry and routing suitability
        prompt_str = str(inputs or prompt_or_chain_fn)
        prompt_length_chars = len(prompt_str)
        prompt_builder_used = any(kw in prompt_str for kw in ["EKIP", "Educational Knowledge", "Why before How", "Pedagogical"])

        # 1. Trigger background probe for open circuits if 5 min interval reached
        self.health_monitor.probe_open_circuits()

        # 2. Determine task intent and select router-ordered healthy providers
        task_intent = self.router.determine_intent(inputs or prompt_or_chain_fn, explicit_intent=intent)
        providers = self.router.select_ordered_providers(intent=task_intent)

        logger.info(
            f"[ReqId: {request_id}] Starting LLM Generation | Intent: {task_intent} | "
            f"Prompt Length: {prompt_length_chars} chars | Available Providers: {[p.name for p in providers]}"
        )

        attempt_count = 0

        for provider in providers:
            p_name = provider.name.capitalize()

            # Health Cache check — Skip if circuit is OPEN
            if provider.is_circuit_open():
                logger.info(f"[ReqId: {request_id}] Skipped Provider '{p_name}' -> Circuit Breaker OPEN.")
                fallback_chain.append(f"{p_name} (Circuit OPEN)")
                attempts_detail.append({
                    "provider": p_name,
                    "model": provider.primary_model,
                    "attempt_number": attempt_count + 1,
                    "duration_ms": 0,
                    "timeout_budget_seconds": 0,
                    "result": "SKIPPED",
                    "failure_reason": "Circuit OPEN",
                    "skipped_reason": "Circuit OPEN",
                })
                continue

            # Check if API key is missing
            if not provider.api_key:
                logger.warning(f"[ReqId: {request_id}] Skipped Provider '{p_name}' -> API Key missing.")
                provider.trip_circuit(ProviderStatus.INVALID_KEY)
                fallback_chain.append(f"{p_name} (No Key)")
                attempts_detail.append({
                    "provider": p_name,
                    "model": provider.primary_model,
                    "attempt_number": attempt_count + 1,
                    "duration_ms": 0,
                    "timeout_budget_seconds": 0,
                    "result": "SKIPPED",
                    "failure_reason": "API Key missing",
                    "skipped_reason": "API Key missing",
                })
                continue

            models_to_try = [provider.primary_model, provider.fallback_model]
            if provider.primary_model == provider.fallback_model:
                models_to_try = [provider.primary_model]

            for model_name in models_to_try:
                # Check global deadline before making another attempt
                remaining_budget = deadline - time.monotonic()
                if remaining_budget <= 0.1:
                    logger.warning(f"[ReqId: {request_id}] Global deadline reached before attempting {p_name} ({model_name}). Budget exhausted.")
                    attempts_detail.append({
                        "provider": p_name,
                        "model": model_name,
                        "attempt_number": attempt_count + 1,
                        "duration_ms": 0,
                        "timeout_budget_seconds": 0,
                        "result": "SKIPPED",
                        "failure_reason": "Global deadline exhausted",
                        "skipped_reason": "Global deadline exhausted",
                    })
                    break

                attempt_count += 1

                # Prompt Size Awareness Gating
                # groq/compound has a strict payload limit (~12,000 chars / ~3,000 tokens)
                if provider.name == "groq" and model_name == "groq/compound" and prompt_length_chars > 12000:
                    logger.info(f"[ReqId: {request_id}] Skipping model '{model_name}' -> Prompt length ({prompt_length_chars} chars) exceeds model payload limit.")
                    attempts_detail.append({
                        "provider": p_name,
                        "model": model_name,
                        "attempt_number": attempt_count,
                        "duration_ms": 0,
                        "timeout_budget_seconds": remaining_budget,
                        "result": "SKIPPED",
                        "failure_reason": "",
                        "skipped_reason": f"Prompt length ({prompt_length_chars} chars) exceeds model payload limit",
                    })
                    continue

                # Compute bounded attempt timeout (max 6s per model to allow failover)
                attempt_timeout = max(1.0, min(6.0, float(timeout), remaining_budget))
                attempt_t0 = time.time()

                try:
                    logger.info(f"[ReqId: {request_id}] Attempt {attempt_count}: Invoking {p_name} ({model_name}) with attempt_timeout={round(attempt_timeout, 2)}s (remaining_budget={round(remaining_budget, 2)}s)...")

                    content, model_used, p_tok, c_tok = provider.generate(
                        prompt_or_chain_fn,
                        inputs,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=attempt_timeout,
                        model_override=model_name,
                    )

                    attempt_duration_ms = round((time.time() - attempt_t0) * 1000, 2)
                    latency_ms = round((time.time() - t0) * 1000, 2)

                    provider.record_success(attempt_duration_ms)
                    fallback_chain.append(provider.name)

                    attempts_detail.append({
                        "provider": p_name,
                        "model": model_used,
                        "attempt_number": attempt_count,
                        "duration_ms": attempt_duration_ms,
                        "timeout_budget_seconds": round(attempt_timeout, 2),
                        "result": "SUCCESS",
                        "failure_reason": "",
                        "skipped_reason": "",
                    })

                    logger.info(
                        f"[ReqId: {request_id}] SUCCESS | Provider: {p_name} | Model: {model_used} | "
                        f"Latency: {latency_ms}ms | Fallback Chain: {fallback_chain}"
                    )

                    fallback_occurred = len(fallback_chain) > 1

                    return LLMResponse(
                        provider=provider.name,
                        model=model_used,
                        content=content,
                        latency=latency_ms,
                        tokens=p_tok + c_tok,
                        success=True,
                        error="",
                        fallback_occurred=fallback_occurred,
                        fallback_chain=fallback_chain,
                        prompt_tokens=p_tok,
                        completion_tokens=c_tok,
                        attempts_detail=attempts_detail,
                        prompt_builder_used=prompt_builder_used,
                        prompt_length_chars=prompt_length_chars,
                    )

                except Exception as e:
                    attempt_duration_ms = round((time.time() - attempt_t0) * 1000, 2)
                    if isinstance(e, (TypeError, AttributeError, KeyError, ValueError)):
                        logger.error(f"[ReqId: {request_id}] Programming error raised in provider '{p_name}': {type(e).__name__}: {e}")
                        raise e

                    err_str = str(e)
                    if isinstance(e, concurrent.futures.TimeoutError):
                        err_str = f"Execution timed out after {round(remaining_budget, 2)}s wall-clock limit"

                    sanitized_err = provider.sanitize_log_message(err_str[:120])
                    
                    status = ProviderStatus.OFFLINE
                    cooldown = 900.0  # 15 minutes default
                    
                    if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                        status = ProviderStatus.RATE_LIMITED
                    elif "401" in err_str or "403" in err_str or "INVALID" in err_str or "invalid_api_key" in err_str.lower():
                        status = ProviderStatus.INVALID_KEY
                    elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
                        status = ProviderStatus.TIMEOUT
                        cooldown = 300.0  # 5 minutes for timeouts

                    logger.warning(
                        f"[ReqId: {request_id}] FAILED | Provider: {p_name} | Model: {model_name} | "
                        f"Status: {status.value} | Reason: {sanitized_err}"
                    )
                    
                    provider.record_failure(err_str, status, cooldown_seconds=cooldown)

                    attempts_detail.append({
                        "provider": p_name,
                        "model": model_name,
                        "attempt_number": attempt_count,
                        "duration_ms": attempt_duration_ms,
                        "timeout_budget_seconds": round(attempt_timeout, 2),
                        "result": "FAILED",
                        "failure_reason": sanitized_err,
                        "skipped_reason": "",
                    })

            fallback_chain.append(provider.name)

            # Check global deadline before proceeding to next provider
            if deadline - time.monotonic() <= 0.1:
                logger.warning(f"[ReqId: {request_id}] Global deadline reached after provider {p_name}. Stopping failover chain.")
                break

        # 3. If EVERY provider failed, return structured failure only.
        latency_ms = round((time.time() - t0) * 1000, 2)
        logger.warning(f"[ReqId: {request_id}] ALL PROVIDERS FAILED in {latency_ms}ms. Returning structured failure.")

        return LLMResponse(
            provider="NONE",
            model="none",
            content="",
            latency=latency_ms,
            tokens=0,
            success=False,
            error="ALL_PROVIDERS_FAILED",
            fallback_occurred=False,
            fallback_chain=fallback_chain,
            prompt_tokens=0,
            completion_tokens=0,
            failure_reason="ALL_PROVIDERS_FAILED",
            attempts_detail=attempts_detail,
            prompt_builder_used=prompt_builder_used,
            prompt_length_chars=prompt_length_chars,
        )

    def invoke_with_fallback(
        self,
        prompt_or_chain_fn,
        inputs: Dict[str, Any] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 15.0,
        documents: Optional[List[Dict[str, Any]]] = None,
        query: str = "",
        intent: Optional[str] = None,
    ) -> LLMResponse:
        """Alias for generate() for backward compatibility."""
        return self.generate(
            prompt_or_chain_fn,
            inputs=inputs,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            documents=documents,
            query=query,
            intent=intent,
        )

    def build_graceful_degradation_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Deprecated compatibility shim; managers must not create user-facing text."""
        logger.warning("build_graceful_degradation_response is deprecated; returning no user-facing content.")
        return ""

    def run_all_health_checks(self) -> Dict[str, HealthCheckReport]:
        return self.health_monitor.run_all_checks()

    def get_provider_health(self) -> Dict[str, HealthCheckReport]:
        return self.health_monitor.get_summary_reports()
