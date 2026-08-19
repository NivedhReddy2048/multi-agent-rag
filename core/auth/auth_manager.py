"""Authentication & Identity Manager handling registration, JWT tokens, password hashing, and login/logout."""

import time
import hashlib
import secrets
import jwt
from typing import Dict, Any, Optional, Tuple
from core.auth.user_models import UserProfile, UserRole, SubscriptionPlan
from core.logger import get_logger

logger = get_logger("core.auth.manager")

SECRET_KEY = secrets.token_hex(32)


class AuthManager:
    """Handles authentication, password hashing, JWT tokens, and user registration."""

    def __init__(self, secret_key: str = SECRET_KEY):
        self.secret_key = secret_key
        self._users_by_email: Dict[str, UserProfile] = {}
        self._users_by_id: Dict[str, UserProfile] = {}
        self._tokens_black_list: set = set()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = "ekip_salt_2026_"
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.STUDENT,
        organization_id: Optional[str] = None,
    ) -> UserProfile:
        """Register a new user in the platform."""
        email_clean = email.strip().lower()
        if email_clean in self._users_by_email:
            raise ValueError(f"User with email '{email_clean}' already exists.")

        hashed = self.hash_password(password)
        user = UserProfile(
            username=username,
            email=email_clean,
            hashed_password=hashed,
            role=role,
            organization_id=organization_id,
            is_verified=True,  # Auto-verify in test/dev
        )
        self._users_by_email[email_clean] = user
        self._users_by_id[user.user_id] = user
        logger.info(f"Registered new user '{username}' ({email_clean}) with role '{role.value}'")
        return user

    def login(self, email: str, password: str) -> Tuple[str, UserProfile]:
        """Authenticate user and issue JWT access token."""
        email_clean = email.strip().lower()
        user = self._users_by_email.get(email_clean)
        if not user:
            raise ValueError("Invalid email or password.")

        if user.hashed_password != self.hash_password(password):
            raise ValueError("Invalid email or password.")

        payload = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "exp": time.time() + 86400,  # 24 hour expiration
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        logger.info(f"User '{user.email}' logged in successfully.")
        return token, user

    def verify_token(self, token: str) -> Optional[UserProfile]:
        """Verify JWT access token and return UserProfile."""
        if token in self._tokens_black_list:
            return None
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")
            return self._users_by_id.get(user_id)
        except Exception:
            return None

    def logout(self, token: str):
        """Logout user by blacklisting token."""
        self._tokens_black_list.add(token)

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        return self._users_by_id.get(user_id)


# Global singleton instance
auth_manager = AuthManager()
