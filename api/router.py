"""Backend REST API Router defining endpoint handlers for Multi-User SaaS."""

from typing import Dict, Any, Optional
from core.auth import auth_manager, UserRole
from core.courses import course_manager
from core.collaboration import collaboration_manager
from core.admin import admin_manager
from core.billing import billing_manager
from core.logger import get_logger

logger = get_logger("api.router")


class APIRouter:
    """Lightweight REST API Router serving /api/auth, /api/users, /api/courses, /api/admin endpoints."""

    def handle_request(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
        payload = payload or {}
        user = auth_manager.verify_token(token) if token else None

        # /api/auth Endpoints
        if endpoint == "/api/auth/register" and method == "POST":
            user = auth_manager.register_user(
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                password=payload.get("password", ""),
                role=UserRole(payload.get("role", "student")),
            )
            return {"status": "success", "user": user.to_dict()}

        elif endpoint == "/api/auth/login" and method == "POST":
            tok, u = auth_manager.login(payload.get("email", ""), payload.get("password", ""))
            return {"status": "success", "token": tok, "user": u.to_dict()}

        # /api/users Endpoints
        elif endpoint == "/api/users/me" and method == "GET":
            if not user:
                return {"status": "error", "message": "Unauthorized"}, 401
            return {"status": "success", "user": user.to_dict()}

        # /api/courses Endpoints
        elif endpoint == "/api/courses/create" and method == "POST":
            if not user or user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
                return {"status": "error", "message": "Forbidden: Requires Teacher or Admin role"}, 403
            course = course_manager.create_course(
                title=payload.get("title", ""),
                description=payload.get("description", ""),
                teacher_id=user.user_id,
            )
            return {"status": "success", "course": course.model_dump()}

        elif endpoint == "/api/courses/list" and method == "GET":
            if not user:
                return {"status": "error", "message": "Unauthorized"}, 401
            courses = course_manager.list_courses_for_student(user.user_id) if user.role == UserRole.STUDENT else course_manager.list_courses_for_teacher(user.user_id)
            return {"status": "success", "courses": [c.model_dump() for c in courses]}

        # /api/admin Endpoints
        elif endpoint == "/api/admin/metrics" and method == "GET":
            if not user or user.role != UserRole.ADMIN:
                return {"status": "error", "message": "Forbidden: Admin access required"}, 403
            return {"status": "success", "metrics": admin_manager.get_system_summary()}

        return {"status": "error", "message": f"Endpoint '{endpoint}' not found"}, 404


# Global singleton instance
api_router = APIRouter()
