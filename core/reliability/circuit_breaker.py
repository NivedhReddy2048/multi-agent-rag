"""Circuit Breaker & Retry Framework for Provider Reliability."""

import time
import random
from enum import Enum
from typing import Callable, Any, Dict, Optional
from core.events.event_bus import event_bus
from core.events.events import ProviderFailure
from core.logger import get_logger

logger = get_logger("core.reliability.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Circuit Breaker protecting against cascading external API failures."""

    def __init__(self, name: str, failure_threshold: int = 3, recovery_time_sec: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()

        if self.state == CircuitState.OPEN:
            if (now - self.last_state_change) >= self.recovery_time_sec:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                logger.info(f"Circuit Breaker '{self.name}' transition: OPEN -> HALF_OPEN")
            else:
                raise RuntimeError(f"Circuit Breaker '{self.name}' is OPEN. Request blocked.")

        try:
            res = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = now
                logger.info(f"Circuit Breaker '{self.name}' transition: HALF_OPEN -> CLOSED")
            return res
        except Exception as e:
            self.failure_count += 1
            event_bus.publish(ProviderFailure(payload={"provider": self.name, "error": str(e)}))
            logger.warning(f"Circuit Breaker '{self.name}' recorded failure ({self.failure_count}/{self.failure_threshold}): {e}")

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = now
                logger.error(f"Circuit Breaker '{self.name}' threshold exceeded! Transition: CLOSED -> OPEN")

            raise e


def retry_with_backoff(func: Callable, max_retries: int = 3, initial_delay: float = 0.5, backoff_factor: float = 2.0) -> Any:
    """Executes func with exponential backoff and jitter."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            jitter = random.uniform(0.8, 1.2)
            sleep_time = delay * jitter
            logger.info(f"Retry attempt {attempt}/{max_retries} failed ({e}). Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor
