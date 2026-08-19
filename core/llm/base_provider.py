"""Base Provider Interface and Dataclasses for Multi-LLM Layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Dict, Any, List, Optional, Tuple
from core.logger import get_logger

logger = get_logger("core.llm.base_provider")


class ProviderStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    RATE_LIMITED = "RATE LIMITED"
    INVALID_KEY = "INVALID KEY"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    OPEN_CIRCUIT = "OPEN CIRCUIT"
    UNKNOWN = "UNKNOWN"


@dataclass
class HealthCheckReport:
    provider: str
    model: str
    status: ProviderStatus
    latency_ms: float
    details: str
    last_success: str = ""
    failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    avg_latency_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 100.0 if self.status == ProviderStatus.ONLINE else 0.0
        return round((self.successful_requests / self.total_requests) * 100.0, 1)


@dataclass
class LLMResponse:
    provider: str
    model: str
    content: str
    latency: float
    tokens: int
    success: bool
    error: str
    fallback_occurred: bool = False
    fallback_chain: List[str] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    failure_reason: str = ""
    attempts_detail: List[Dict[str, Any]] = field(default_factory=list)
    prompt_builder_used: bool = False
    prompt_length_chars: int = 0

    def __post_init__(self):
        if not self.fallback_chain:
            self.fallback_chain = [self.provider] if self.provider != "NONE" else []

    def __iter__(self):
        """Enable tuple unpacking (content, provider, metadata) for backward compatibility."""
        yield self.content
        yield self.provider
        yield {
            "latency_ms": self.latency,
            "model": self.model,
            "tokens": self.tokens,
            "success": self.success,
            "error": self.error,
            "fallback_occurred": self.fallback_occurred,
            "fallback_chain": self.fallback_chain,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "attempts_detail": self.attempts_detail,
            "prompt_builder_used": self.prompt_builder_used,
            "prompt_length_chars": self.prompt_length_chars,
        }


class BaseLLMProvider(ABC):
    """Abstract Base Class for all LLM Providers."""

    def __init__(self, name: str, primary_model: str, fallback_model: str, api_key: str):
        self.name = name
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.api_key = api_key
        self.client_cache: Dict[Tuple, Any] = {}
        
        # Telemetry & Circuit Breaker metrics
        self.failures_count = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.total_latency_ms = 0.0
        self.last_success_time = "Never"
        self.current_status = ProviderStatus.UNKNOWN
        self.last_error_msg = ""
        self.last_failure_time = 0.0
        self.retry_after = 0.0
        self.cooldown_seconds = 900.0  # 15 minutes default

    def sanitize_log_message(self, message: str) -> str:
        """Strip sensitive API keys from log messages."""
        if not self.api_key:
            return message
        return message.replace(self.api_key, "[REDACTED_API_KEY]")

    def is_circuit_open(self) -> bool:
        """Return True if circuit breaker is OPEN and retry_after timestamp has not expired."""
        if not self.api_key:
            return True
        if self.current_status in (ProviderStatus.OPEN_CIRCUIT, ProviderStatus.RATE_LIMITED, ProviderStatus.INVALID_KEY):
            if time.time() < self.retry_after:
                return True
        return False

    def trip_circuit(self, status: ProviderStatus = ProviderStatus.OPEN_CIRCUIT, cooldown_seconds: float = 900.0):
        """Trip circuit breaker into OPEN state with cooldown timer."""
        self.current_status = status
        self.last_failure_time = time.time()
        self.retry_after = time.time() + cooldown_seconds
        logger.warning(
            f"Circuit breaker TRIPPED for provider '{self.name}'. Status: {status.value}. "
            f"Retry allowed at {time.strftime('%H:%M:%S', time.localtime(self.retry_after))}"
        )

    def reset_circuit(self):
        """Close circuit breaker and return provider to ONLINE state."""
        self.current_status = ProviderStatus.ONLINE
        self.retry_after = 0.0
        logger.info(f"Circuit breaker CLOSED (recovered) for provider '{self.name}'. Status: ONLINE.")

    @abstractmethod
    def get_client(self, model_name: str, temperature: float = 0.1, max_tokens: int = 4096, timeout: float = 2.0):
        """Instantiate and cache provider-specific LangChain client."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt_or_chain_fn,
        inputs: Dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        timeout: float = 2.0,
        model_override: Optional[str] = None,
    ) -> Tuple[str, str, int, int]:
        """
        Execute generation for prompt or callable chain.
        Returns: Tuple[content_text, model_used, prompt_tokens, completion_tokens]
        """
        pass

    def record_success(self, latency_ms: float):
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.last_success_time = time.strftime("%H:%M:%S")
        self.reset_circuit()

    def record_failure(self, error_str: str, status: ProviderStatus, cooldown_seconds: float = 900.0):
        self.total_requests += 1
        self.failures_count += 1
        self.last_error_msg = self.sanitize_log_message(error_str[:120])
        self.trip_circuit(status, cooldown_seconds)

    def health_check(self) -> HealthCheckReport:
        """Run ping diagnostic to update provider health."""
        t0 = time.time()
        if not self.api_key:
            self.current_status = ProviderStatus.INVALID_KEY
            return HealthCheckReport(
                provider=self.name,
                model=self.primary_model,
                status=ProviderStatus.INVALID_KEY,
                latency_ms=0.0,
                details=f"{self.name.upper()}_API_KEY is empty in configuration.",
                last_success=self.last_success_time,
                failures=self.failures_count,
                total_requests=self.total_requests,
                successful_requests=self.successful_requests,
                avg_latency_ms=self.avg_latency_ms,
            )

        try:
            client = self.get_client(self.primary_model, max_tokens=10, timeout=10.0)
            _ = client.invoke("Ping")
            latency = round((time.time() - t0) * 1000, 2)
            self.record_success(latency)
            return HealthCheckReport(
                provider=self.name,
                model=self.primary_model,
                status=ProviderStatus.ONLINE,
                latency_ms=latency,
                details="Connection verified successfully.",
                last_success=self.last_success_time,
                failures=self.failures_count,
                total_requests=self.total_requests,
                successful_requests=self.successful_requests,
                avg_latency_ms=self.avg_latency_ms,
            )
        except Exception as e:
            latency = round((time.time() - t0) * 1000, 2)
            err_str = str(e)
            status = ProviderStatus.OFFLINE
            if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                status = ProviderStatus.RATE_LIMITED
            elif "401" in err_str or "403" in err_str or "INVALID" in err_str or "invalid_api_key" in err_str.lower():
                status = ProviderStatus.INVALID_KEY

            self.record_failure(err_str, status)
            return HealthCheckReport(
                provider=self.name,
                model=self.primary_model,
                status=status,
                latency_ms=latency,
                details=self.sanitize_log_message(f"Health check error: {err_str[:120]}"),
                last_success=self.last_success_time,
                failures=self.failures_count,
                total_requests=self.total_requests,
                successful_requests=self.successful_requests,
                avg_latency_ms=self.avg_latency_ms,
            )

    @property
    def avg_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return round(self.total_latency_ms / self.successful_requests, 2)
