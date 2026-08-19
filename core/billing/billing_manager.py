"""Billing & SaaS Feature Gating Foundation."""

from typing import Dict, Any
from core.auth.user_models import UserProfile, SubscriptionPlan
from core.logger import get_logger

logger = get_logger("core.billing.manager")

# Plan limits catalog
PLAN_QUOTAS: Dict[SubscriptionPlan, Dict[str, Any]] = {
    SubscriptionPlan.FREE: {
        "max_queries_per_day": 50,
        "max_storage_mb": 100,
        "advanced_modules_enabled": False,
        "team_collaboration_enabled": False,
    },
    SubscriptionPlan.PRO: {
        "max_queries_per_day": 1000,
        "max_storage_mb": 5000,
        "advanced_modules_enabled": True,
        "team_collaboration_enabled": True,
    },
    SubscriptionPlan.ENTERPRISE: {
        "max_queries_per_day": 100000,
        "max_storage_mb": 500000,
        "advanced_modules_enabled": True,
        "team_collaboration_enabled": True,
    },
}


class BillingManager:
    """Manages subscription plans, usage quotas, feature gating, and SaaS monetization preparation."""

    @staticmethod
    def check_feature_access(user: UserProfile, feature: str) -> bool:
        """Check if user's subscription plan permits a specific feature."""
        quotas = PLAN_QUOTAS.get(user.subscription_plan, PLAN_QUOTAS[SubscriptionPlan.FREE])
        allowed = quotas.get(feature, True)
        logger.debug(f"Billing Check: User '{user.username}' ({user.subscription_plan.value}) Feature '{feature}': {allowed}")
        return allowed

    @staticmethod
    def get_user_quotas(user: UserProfile) -> Dict[str, Any]:
        return PLAN_QUOTAS.get(user.subscription_plan, PLAN_QUOTAS[SubscriptionPlan.FREE])


# Global singleton instance
billing_manager = BillingManager()
