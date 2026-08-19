"""Multi-Level Intelligent Caching Layer supporting TTL, LRU eviction, and namespace separation."""

import time
from collections import OrderedDict
from typing import Dict, Any, Optional
from core.events.event_bus import event_bus
from core.events.events import CacheHit, CacheMiss
from core.logger import get_logger

logger = get_logger("core.cache.manager")


class CacheEntry:
    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl


class NamespaceLRUCache:
    """In-memory LRU Cache with TTL support for a single namespace."""

    def __init__(self, namespace: str, max_size: int = 1000, default_ttl: float = 3600.0):
        self.namespace = namespace
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            self.misses += 1
            event_bus.publish(CacheMiss(payload={"namespace": self.namespace, "key": key}))
            return None

        entry = self._cache[key]
        if entry.is_expired:
            del self._cache[key]
            self.misses += 1
            event_bus.publish(CacheMiss(payload={"namespace": self.namespace, "key": key, "reason": "expired"}))
            return None

        # Move to end for LRU order
        self._cache.move_to_end(key)
        self.hits += 1
        event_bus.publish(CacheHit(payload={"namespace": self.namespace, "key": key}))
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self.max_size:
            # Evict LRU item (first item)
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug(f"[{self.namespace}] Evicted LRU item: '{evicted_key}'")

        entry_ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(key, value, entry_ttl)

    def invalidate(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return round((self.hits / total) * 100, 2) if total > 0 else 0.0


class MultiLevelCacheManager:
    """Manages multi-tier cached namespaces: semantic, planner, retrieval, provider, document."""

    def __init__(self):
        self._namespaces: Dict[str, NamespaceLRUCache] = {
            "semantic": NamespaceLRUCache("semantic", max_size=500, default_ttl=7200),
            "planner": NamespaceLRUCache("planner", max_size=500, default_ttl=3600),
            "retrieval": NamespaceLRUCache("retrieval", max_size=1000, default_ttl=1800),
            "provider": NamespaceLRUCache("provider", max_size=2000, default_ttl=600),
            "document": NamespaceLRUCache("document", max_size=200, default_ttl=86400),
        }

    def get_namespace(self, name: str) -> NamespaceLRUCache:
        if name not in self._namespaces:
            self._namespaces[name] = NamespaceLRUCache(name)
        return self._namespaces[name]

    def get(self, namespace: str, key: str) -> Optional[Any]:
        return self.get_namespace(namespace).get(key)

    def set(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None):
        self.get_namespace(namespace).set(key, value, ttl)

    def invalidate(self, namespace: str, key: str):
        self.get_namespace(namespace).invalidate(key)

    def clear_namespace(self, namespace: str):
        self.get_namespace(namespace).clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        return {
            ns_name: {
                "size": len(ns._cache),
                "max_size": ns.max_size,
                "hits": ns.hits,
                "misses": ns.misses,
                "hit_ratio": ns.hit_ratio,
            }
            for ns_name, ns in self._namespaces.items()
        }


# Global singleton instance
cache_manager = MultiLevelCacheManager()
