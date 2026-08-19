"""Plugin Manager registering, discovering, enabling/disabling, and executing EKIP Learning Modules."""

import time
from typing import Dict, Any, List, Optional, Type
from core.workspace.modules.base_module import LearningModule
from core.models.synthesis import EducationalResponse
from core.models.workspace import LearningSession
from core.logger import get_logger

logger = get_logger("core.workspace.modules.manager")


class LearningModuleManager:
    """Discovers, registers, enables/disables, and executes plugin learning modules dynamically."""

    def __init__(self):
        self._registry: Dict[str, LearningModule] = {}

    def register_module(self, module: LearningModule):
        """Register a LearningModule plugin instance."""
        self._registry[module.name.lower()] = module
        logger.info(f"Registered Learning Module: '{module.name}' (v{module.version})")

    def unregister_module(self, module_name: str):
        """Unregister a module by name."""
        key = module_name.lower()
        if key in self._registry:
            del self._registry[key]
            logger.info(f"Unregistered Learning Module: '{module_name}'")

    def enable_module(self, module_name: str):
        """Enable a registered module."""
        key = module_name.lower()
        if key in self._registry:
            self._registry[key].is_enabled = True

    def disable_module(self, module_name: str):
        """Disable a registered module."""
        key = module_name.lower()
        if key in self._registry:
            self._registry[key].is_enabled = False

    def get_module(self, module_name: str) -> Optional[LearningModule]:
        """Get registered module instance."""
        return self._registry.get(module_name.lower())

    def list_modules(self) -> List[Dict[str, Any]]:
        """List metadata of all registered modules."""
        return [
            {
                "name": mod.name,
                "description": mod.description,
                "version": mod.version,
                "is_enabled": mod.is_enabled,
            }
            for mod in self._registry.values()
        ]

    def execute_all(self, response: EducationalResponse, session: Optional[LearningSession] = None) -> Dict[str, Any]:
        """Execute all enabled modules sequentially against an EducationalResponse."""
        results: Dict[str, Any] = {}
        for name, mod in self._registry.items():
            if mod.is_enabled:
                start_t = time.time()
                try:
                    out = mod.process(response, session)
                    latency = round((time.time() - start_t) * 1000, 2)
                    out["execution_latency_ms"] = latency
                    results[name] = out
                    logger.info(f"Executed module '{mod.name}' successfully in {latency}ms")
                except Exception as e:
                    logger.error(f"Error executing module '{mod.name}': {e}", exc_info=True)
                    results[name] = {"error": str(e), "execution_latency_ms": round((time.time() - start_t) * 1000, 2)}
        return results


# Global singleton instance
module_manager = LearningModuleManager()
