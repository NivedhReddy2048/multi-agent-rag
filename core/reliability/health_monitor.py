"""Provider Health Monitor tracking provider metrics, latencies, success rates, and availability."""

import time
from typing import Dict, Any, List
from core.logger import get_logger

logger = get_logger("core.reliability.health_monitor")


class ProviderHealthStats:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency_ms = 0.0
        self.quota_used = 0
        self.quota_limit = 1000
        self.last_success_timestamp: float = 0.0

    def record_success(self, latency_ms: float):
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.quota_used += 1
        self.last_success_timestamp = time.time()

    def record_failure(self):
        self.total_requests += 1
        self.failed_requests += 1

    @property
    def success_rate(self) -> float:
        return round((self.successful_requests / self.total_requests) * 100, 2) if self.total_requests > 0 else 100.0

    @property
    def avg_latency_ms(self) -> float:
        return round(self.total_latency_ms / self.successful_requests, 2) if self.successful_requests > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "total_requests": self.total_requests,
            "success_rate": self.success_rate,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": self.avg_latency_ms,
            "quota_used": self.quota_used,
            "last_success_timestamp": self.last_success_timestamp,
        }


class ProviderHealthMonitor:
    """Aggregates real-time health metrics across all external APIs/Providers."""

    def __init__(self):
        self._providers: Dict[str, ProviderHealthStats] = {}

    def get_stats(self, provider_name: str) -> ProviderHealthStats:
        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderHealthStats(provider_name)
        return self._providers[provider_name]

    def record_call(self, provider_name: str, success: bool, latency_ms: float = 0.0):
        stats = self.get_stats(provider_name)
        if success:
            stats.record_success(latency_ms)
        else:
            stats.record_failure()

    def get_all_health(self) -> List[Dict[str, Any]]:
        return [stats.to_dict() for stats in self._providers.values()]


# Global singleton instance
health_monitor = ProviderHealthMonitor()
