"""In-Memory Provider Health Cache & Circuit Breaker Recovery Monitor for Multi-LLM Layer."""

import time
from typing import Dict, List, Optional
from .base_provider import BaseLLMProvider, HealthCheckReport, ProviderStatus
from .provider_registry import ProviderRegistry
from core.logger import get_logger

logger = get_logger("core.llm.health_monitor")


class ProviderHealthCache:
    """Fast, zero-latency health cache checking circuit breaker status prior to API invocation."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def is_available(self, provider_name: str) -> bool:
        """Check if provider circuit is healthy and closed."""
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return False
        if provider.is_circuit_open():
            logger.info(f"Health Cache: Provider '{provider_name}' skipped immediately (Circuit OPEN until {time.strftime('%H:%M:%S', time.localtime(provider.retry_after))}).")
            return False
        return True


class HealthMonitor:
    """Monitors real-time status, latencies, and failure diagnostics for all providers."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.health_cache = ProviderHealthCache(registry)
        self.last_probe_time: float = time.time()
        self.probe_interval_seconds: float = 300.0  # 5 minutes

    def check_provider(self, provider_name: str) -> HealthCheckReport:
        provider = self.registry.get_provider(provider_name)
        if not provider:
            return HealthCheckReport(
                provider=provider_name,
                model="unknown",
                status=ProviderStatus.OFFLINE,
                latency_ms=0.0,
                details=f"Provider '{provider_name}' not found in registry.",
            )
        return provider.health_check()

    def run_all_checks(self) -> Dict[str, HealthCheckReport]:
        reports = {}
        for provider in self.registry.get_ordered_providers():
            logger.info(f"Pinging provider health: {provider.name}...")
            report = provider.health_check()
            reports[provider.name] = report
            logger.info(f"Provider '{provider.name}' status: {report.status} | Latency: {report.latency_ms}ms")
        return reports

    def probe_open_circuits(self, force: bool = False) -> List[str]:
        """
        Background Recovery (Task 5): Probe open circuits every 5 minutes.
        Only probes providers whose circuit is currently OPEN.
        If healthy -> resets circuit to ONLINE and resumes routing.
        """
        now = time.time()
        if not force and (now - self.last_probe_time) < self.probe_interval_seconds:
            return []

        self.last_probe_time = now
        recovered_providers = []

        for provider in self.registry.get_ordered_providers():
            if provider.is_circuit_open() or provider.current_status in (ProviderStatus.OFFLINE, ProviderStatus.OPEN_CIRCUIT, ProviderStatus.RATE_LIMITED):
                logger.info(f"Background Probe: Testing recovery for open circuit provider '{provider.name}'...")
                report = provider.health_check()
                if report.status == ProviderStatus.ONLINE:
                    logger.info(f"Background Probe: Provider '{provider.name}' successfully RECOVERED! Circuit closed.")
                    recovered_providers.append(provider.name)
                else:
                    logger.info(f"Background Probe: Provider '{provider.name}' still unhealthy ({report.status}). Keeping circuit open.")

        return recovered_providers

    def get_summary_reports(self) -> Dict[str, HealthCheckReport]:
        reports = {}
        for provider in self.registry.get_ordered_providers():
            reports[provider.name] = HealthCheckReport(
                provider=provider.name,
                model=provider.primary_model,
                status=provider.current_status,
                latency_ms=provider.avg_latency_ms,
                details=provider.last_error_msg or ("Circuit OPEN (cooling down)" if provider.is_circuit_open() else "Operating normally"),
                last_success=provider.last_success_time,
                failures=provider.failures_count,
                total_requests=provider.total_requests,
                successful_requests=provider.successful_requests,
                avg_latency_ms=provider.avg_latency_ms,
            )
        return reports
