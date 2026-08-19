"""Role-Based Access Control (RBAC) Framework."""

from typing import Dict, List, Set
from core.auth.user_models import UserProfile, UserRole
from core.logger import get_logger

logger = get_logger("core.rbac.manager")

# Permissions catalog
PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.ADMIN: {
        "user:manage",
        "course:create",
        "course:delete",
        "notebook:share",
        "quiz:assign",
        "analytics:view_all",
        "admin:console",
    },
    UserRole.TEACHER: {
        "course:create",
        "notebook:share",
        "quiz:assign",
        "student:monitor",
        "analytics:view_course",
    },
    UserRole.STUDENT: {
        "course:enroll",
        "quiz:submit",
        "note:save",
        "flashcard:view",
        "workspace:personal",
    },
    UserRole.RESEARCHER: {
        "notebook:share",
        "research:advanced",
        "workspace:personal",
    },
    UserRole.GUEST: {
        "workspace:read_only",
    },
}


class RBACManager:
    """Manages role permissions, access control checks, and resource authorization."""

    @staticmethod
    def has_permission(user: UserProfile, permission: str) -> bool:
        """Check if user role has a specific permission."""
        role_permissions = PERMISSIONS.get(user.role, set())
        allowed = permission in role_permissions or user.role == UserRole.ADMIN
        logger.debug(f"RBAC Check: User '{user.username}' (Role: {user.role.value}) Permission '{permission}': {allowed}")
        return allowed


# Global singleton instance
rbac_manager = RBACManager()
