"""Admin Console Backend providing management APIs for multi-tenant SaaS platforms."""

from typing import Dict, Any, List
from core.auth.auth_manager import auth_manager
from core.courses.course_manager import course_manager
from core.logger import get_logger

logger = get_logger("core.admin.manager")


class AdminManager:
    """Provides administrative APIs for managing users, organizations, system metrics, and SaaS health."""

    @staticmethod
    def get_system_summary() -> Dict[str, Any]:
        """Aggregate high-level system usage statistics."""
        return {
            "total_registered_users": len(auth_manager._users_by_id),
            "total_active_courses": len(course_manager._courses),
            "auth_tokens_blacklisted": len(auth_manager._tokens_black_list),
            "system_status": "healthy",
        }

    @staticmethod
    def list_all_users() -> List[Dict[str, Any]]:
        """Return list of all user profiles for admin inspection."""
        return [u.to_dict() for u in auth_manager._users_by_id.values()]


# Global singleton instance
admin_manager = AdminManager()
