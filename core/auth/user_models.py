"""User identity models and RBAC Role definitions."""

import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "administrator"
    TEACHER = "teacher"
    STUDENT = "student"
    RESEARCHER = "researcher"
    GUEST = "guest"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.STUDENT
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE
    organization_id: Optional[str] = None
    is_verified: bool = False
    created_at: float = Field(default_factory=time.time)
    preferences: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "subscription_plan": self.subscription_plan.value,
            "organization_id": self.organization_id,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "preferences": self.preferences,
        }
