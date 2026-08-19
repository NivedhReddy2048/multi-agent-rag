"""EKIP Authentication & User Identity Package."""

from core.auth.user_models import UserProfile, UserRole, SubscriptionPlan
from core.auth.auth_manager import AuthManager, auth_manager
from core.auth.database import (
    init_db,
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
    update_password,
    update_last_login,
    user_exists,
    generate_remember_token,
    validate_remember_token,
    invalidate_remember_token,
)
from core.auth.validators import (
    validate_username,
    validate_email,
    validate_phone,
    validate_password,
    validate_role,
    validate_registration_data,
)
from core.auth.session import (
    initialize_auth_state,
    login_user,
    logout_user,
    check_remember_me,
)

__all__ = [
    "UserProfile",
    "UserRole",
    "SubscriptionPlan",
    "AuthManager",
    "auth_manager",
    "init_db",
    "create_user",
    "authenticate_user",
    "get_user_by_username",
    "get_user_by_email",
    "update_password",
    "update_last_login",
    "user_exists",
    "generate_remember_token",
    "validate_remember_token",
    "invalidate_remember_token",
    "validate_username",
    "validate_email",
    "validate_phone",
    "validate_password",
    "validate_role",
    "validate_registration_data",
    "initialize_auth_state",
    "login_user",
    "logout_user",
    "check_remember_me",
]
