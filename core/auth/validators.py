"""Validation layer for EKIP authentication data."""

import re
from typing import Optional


def validate_username(username: str) -> bool:
    """Validate username format (3-20 chars, alphanumeric + underscore only)."""
    if not username or not isinstance(username, str):
        raise ValueError("Username is required.")
    
    username = username.strip()
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        raise ValueError(
            "Username must be 3-20 characters long and contain only letters, numbers, and underscores."
        )
    return True


def validate_email(email: str) -> bool:
    """Validate email address format using regex."""
    if not email or not isinstance(email, str):
        raise ValueError("Email address is required.")
    
    email = email.strip()
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise ValueError("Invalid email address format.")
    return True


def validate_phone(phone: Optional[str]) -> bool:
    """Validate phone number format (optional; if provided, 10-15 digits only)."""
    if phone is None or (isinstance(phone, str) and not phone.strip()):
        return True
    
    cleaned = re.sub(r"[\s\-\+\(\)]", "", str(phone).strip())
    if not re.match(r"^\d{10,15}$", cleaned):
        raise ValueError("Phone number must contain between 10 and 15 digits.")
    return True


def validate_password(password: str) -> bool:
    """Validate password strength (Min 8 chars, 1 uppercase, 1 lowercase, 1 digit)."""
    if not password or not isinstance(password, str):
        raise ValueError("Password is required.")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return True


def validate_role(role: str) -> bool:
    """Validate role string (Must be 'Student' or 'Researcher')."""
    if not role or role not in ("Student", "Researcher"):
        raise ValueError("Role must be exactly 'Student' or 'Researcher'.")
    return True


def validate_registration_data(
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    phone: Optional[str],
    role: str,
    password: str,
) -> bool:
    """Validate all user registration fields prior to database operations."""
    if not first_name or not isinstance(first_name, str) or not first_name.strip():
        raise ValueError("First name is required.")
    if not last_name or not isinstance(last_name, str) or not last_name.strip():
        raise ValueError("Last name is required.")
    
    validate_username(username)
    validate_email(email)
    validate_phone(phone)
    validate_role(role)
    validate_password(password)
    return True
