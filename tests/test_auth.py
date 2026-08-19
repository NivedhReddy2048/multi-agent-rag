"""Unit tests for EKIP backend authentication, database, validators, and session logic."""

import os
import pytest
import tempfile
from pathlib import Path

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
    verify_password,
    update_user_theme,
    get_user_theme,
    update_user_profile,
)
from core.auth.validators import (
    validate_username,
    validate_email,
    validate_phone,
    validate_password,
    validate_role,
    validate_registration_data,
)


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for isolated test runs."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name
    
    init_db(temp_path)
    yield temp_path
    
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def test_db_initialization(temp_db):
    """Test that data/ekip_users.db tables are initialized properly."""
    assert os.path.exists(temp_db)
    # Check default DB auto-creation function
    default_db = init_db()
    assert os.path.exists(default_db)


def test_user_creation_all_fields(temp_db):
    """Test user creation with all 8 specified fields."""
    user = create_user(
        first_name="Alex",
        last_name="Smith",
        username="alex_smith",
        email="alex@ekip.ai",
        phone="12345678901",
        role="Student",
        password="Password123",
        db_path=temp_db,
    )
    
    assert user is not None
    assert user["first_name"] == "Alex"
    assert user["last_name"] == "Smith"
    assert user["username"] == "alex_smith"
    assert user["email"] == "alex@ekip.ai"
    assert user["phone"] == "12345678901"
    assert user["role"] == "Student"
    assert user["password_hash"] != "Password123"
    assert verify_password("Password123", user["password_hash"]) is True


def test_duplicate_username_rejected(temp_db):
    """Test that creating a user with duplicate username raises ValueError."""
    create_user(
        first_name="John",
        last_name="Doe",
        username="johndoe",
        email="john1@ekip.ai",
        phone=None,
        role="Student",
        password="Password123",
        db_path=temp_db,
    )
    
    with pytest.raises(ValueError, match="already taken"):
        create_user(
            first_name="Jane",
            last_name="Doe",
            username="johndoe",
            email="john2@ekip.ai",
            phone=None,
            role="Researcher",
            password="Password123",
            db_path=temp_db,
        )


def test_duplicate_email_rejected(temp_db):
    """Test that creating a user with duplicate email raises ValueError."""
    create_user(
        first_name="Jane",
        last_name="Doe",
        username="janedoe",
        email="jane@ekip.ai",
        phone=None,
        role="Researcher",
        password="Password123",
        db_path=temp_db,
    )
    
    with pytest.raises(ValueError, match="already registered"):
        create_user(
            first_name="Janet",
            last_name="Doe",
            username="janetdoe",
            email="jane@ekip.ai",
            phone=None,
            role="Student",
            password="Password123",
            db_path=temp_db,
        )


def test_password_hashing(temp_db):
    """Test password bcrypt hashing security."""
    user = create_user(
        first_name="Sec",
        last_name="User",
        username="secuser",
        email="sec@ekip.ai",
        phone=None,
        role="Student",
        password="SuperSecretPassword1",
        db_path=temp_db,
    )
    
    stored_hash = user["password_hash"]
    assert stored_hash != "SuperSecretPassword1"
    assert stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$")
    assert verify_password("SuperSecretPassword1", stored_hash) is True
    assert verify_password("WrongPassword1", stored_hash) is False


def test_authentication_flow(temp_db):
    """Test user authentication by username and by email."""
    create_user(
        first_name="Auth",
        last_name="User",
        username="authuser",
        email="auth@ekip.ai",
        phone=None,
        role="Researcher",
        password="Password123",
        db_path=temp_db,
    )
    
    # Authenticate by username
    authed_by_user = authenticate_user("authuser", "Password123", db_path=temp_db)
    assert authed_by_user is not None
    assert authed_by_user["username"] == "authuser"
    assert authed_by_user["last_login"] is not None
    
    # Authenticate by email
    authed_by_email = authenticate_user("auth@ekip.ai", "Password123", db_path=temp_db)
    assert authed_by_email is not None
    assert authed_by_email["email"] == "auth@ekip.ai"
    
    # Invalid password
    bad_pw = authenticate_user("authuser", "WrongPassword", db_path=temp_db)
    assert bad_pw is None
    
    # Nonexistent user
    bad_user = authenticate_user("nonexistent", "Password123", db_path=temp_db)
    assert bad_user is None


def test_update_password(temp_db):
    """Test updating user password."""
    create_user(
        first_name="Pass",
        last_name="Update",
        username="passupdate",
        email="passupdate@ekip.ai",
        phone=None,
        role="Student",
        password="OldPassword123",
        db_path=temp_db,
    )
    
    # Update password
    success = update_password("passupdate", "NewPassword123", db_path=temp_db)
    assert success is True
    
    # Old password should fail
    old_auth = authenticate_user("passupdate", "OldPassword123", db_path=temp_db)
    assert old_auth is None
    
    # New password should succeed
    new_auth = authenticate_user("passupdate", "NewPassword123", db_path=temp_db)
    assert new_auth is not None


def test_remember_me_token_flow(temp_db):
    """Test remember token generation, validation, and invalidation."""
    create_user(
        first_name="Token",
        last_name="User",
        username="tokenuser",
        email="token@ekip.ai",
        phone=None,
        role="Student",
        password="Password123",
        db_path=temp_db,
    )
    
    # Generate remember token
    token = generate_remember_token("tokenuser", db_path=temp_db)
    assert token is not None
    assert len(token) > 10
    
    # Validate token
    validated_username = validate_remember_token(token, db_path=temp_db)
    assert validated_username == "tokenuser"
    
    # Invalid token returns None
    invalid = validate_remember_token("fake-token-uuid-1234", db_path=temp_db)
    assert invalid is None
    
    # Invalidate token
    inv_result = invalidate_remember_token("tokenuser", db_path=temp_db)
    assert inv_result is True
    assert validate_remember_token(token, db_path=temp_db) is None


def test_validators():
    """Test input field validation functions."""
    # Username tests
    assert validate_username("user_123") is True
    with pytest.raises(ValueError):
        validate_username("ab")  # Too short
    with pytest.raises(ValueError):
        validate_username("user@name!")  # Invalid chars
        
    # Email tests
    assert validate_email("test@domain.com") is True
    with pytest.raises(ValueError):
        validate_email("invalid-email")
        
    # Phone tests
    assert validate_phone(None) is True
    assert validate_phone("") is True
    assert validate_phone("12345678901") is True
    with pytest.raises(ValueError):
        validate_phone("123")  # Too short
        
    # Password tests
    assert validate_password("Valid1234") is True
    with pytest.raises(ValueError):
        validate_password("short")  # Less than 8 chars
    with pytest.raises(ValueError):
        validate_password("lowercase123")  # No uppercase
    with pytest.raises(ValueError):
        validate_password("UPPERCASE123")  # No lowercase
    with pytest.raises(ValueError):
        validate_password("NoDigitsHere")  # No digits
        
    # Role tests
    assert validate_role("Student") is True
    assert validate_role("Researcher") is True
    with pytest.raises(ValueError):
        validate_role("Admin")  # Invalid role


def test_theme_and_profile_updates(temp_db):
    """Test theme preference persistence and profile updates."""
    create_user(
        first_name="Theme",
        last_name="Tester",
        username="themetester",
        email="theme@ekip.ai",
        phone=None,
        role="Student",
        password="Password123",
        db_path=temp_db,
    )

    # Default theme check
    assert get_user_theme("themetester", db_path=temp_db) == "dark"

    # Update theme to light
    assert update_user_theme("themetester", "light", db_path=temp_db) is True
    assert get_user_theme("themetester", db_path=temp_db) == "light"

    # Invalid theme raises ValueError
    with pytest.raises(ValueError):
        update_user_theme("themetester", "blue", db_path=temp_db)

    # Profile update test
    updated_user = update_user_profile(
        username="themetester",
        first_name="UpdatedFirstName",
        last_name="UpdatedLastName",
        phone="98765432101",
        profile_image_b64="base64_sample_string",
        db_path=temp_db,
    )

    assert updated_user["first_name"] == "UpdatedFirstName"
    assert updated_user["last_name"] == "UpdatedLastName"
    assert updated_user["phone"] == "98765432101"
    assert updated_user["profile_image_b64"] == "base64_sample_string"

