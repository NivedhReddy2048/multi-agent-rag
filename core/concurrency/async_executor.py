"""Async & Concurrency Control Layer for handling 50+ concurrent provider calls."""

import asyncio
import inspect
from typing import List, Callable, Any
from core.logger import get_logger

logger = get_logger("core.concurrency.async_executor")


class AsyncConcurrencyLimiter:
    """Limits concurrent async provider/agent tasks using asyncio.Semaphore."""

    def __init__(self, max_concurrency: int = 50):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def run_task(self, func: Callable, *args, **kwargs) -> Any:
        async with self._semaphore:
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)

            res = func(*args, **kwargs)
            if inspect.isawaitable(res):
                return await res

            return res

    async def run_parallel(self, tasks: List[Callable[[], Any]]) -> List[Any]:
        """Execute multiple callables concurrently with semaphore rate limiting."""
        async_tasks = [self.run_task(task) for task in tasks]
        return await asyncio.gather(*async_tasks, return_exceptions=True)


# Global singleton instance
async_limiter = AsyncConcurrencyLimiter(max_concurrency=50)
