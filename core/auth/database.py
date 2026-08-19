"""Database management layer for EKIP user authentication."""

import os
import sqlite3
import uuid
import bcrypt
from pathlib import Path
from typing import Optional, Dict, Any
from core.auth.validators import validate_registration_data, validate_password

# Default database location inside project data/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "ekip_users.db"


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Resolve database path, creating parent directory if necessary."""
    if custom_path:
        path = Path(custom_path)
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite database connection with row factory configured."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Convert SQLite Row to dictionary."""
    if row is None:
        return None
    return dict(row)


def init_db(db_path: Optional[str] = None) -> str:
    """Initialize SQLite database and create users table if it does not exist."""
    path = get_db_path(db_path)
    conn = get_db_connection(str(path))
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NULLABLE,
                    role TEXT NOT NULL CHECK(role IN ('Student', 'Researcher')),
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULLABLE,
                    remember_token TEXT NULLABLE,
                    profile_image TEXT NULLABLE
                );
                """
            )
            # Schema Migration: Add theme and profile_image_b64 if missing
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cur.fetchall()]
            if "theme" not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'dark'")
            if "profile_image_b64" not in columns:
                cur.execute("ALTER TABLE users ADD COLUMN profile_image_b64 TEXT")
        init_user_preferences(str(path))
    finally:
        conn.close()
    return str(path)


def init_user_preferences(db_path: Optional[str] = None):
    """Initialize user_preferences table."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    default_view TEXT DEFAULT 'dashboard',
                    show_welcome_card INTEGER DEFAULT 1,
                    last_active_chat_id TEXT,
                    sidebar_collapsed INTEGER DEFAULT 0,
                    quick_actions_collapsed INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
    finally:
        conn.close()


def get_user_preferences(user_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve user preferences dictionary, creating default row if missing."""
    if not user_id:
        return {
            "user_id": "guest",
            "default_view": "dashboard",
            "show_welcome_card": 1,
            "last_active_chat_id": None,
            "sidebar_collapsed": 0,
            "quick_actions_collapsed": 0,
        }
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_preferences WHERE LOWER(user_id) = LOWER(?)", (user_id.strip(),))
        row = cur.fetchone()
        if row:
            return dict(row)
        else:
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)",
                    (user_id.strip(),),
                )
            return {
                "user_id": user_id.strip(),
                "default_view": "dashboard",
                "show_welcome_card": 1,
                "last_active_chat_id": None,
                "sidebar_collapsed": 0,
                "quick_actions_collapsed": 0,
            }
    finally:
        conn.close()


def update_user_preferences(user_id: str, db_path: Optional[str] = None, **kwargs) -> bool:
    """Update user preference key-values."""
    if not user_id or not kwargs:
        return False
    # Ensure preference row exists
    get_user_preferences(user_id, db_path)
    fields = []
    values = []
    for k, v in kwargs.items():
        if k in (
            "default_view",
            "show_welcome_card",
            "last_active_chat_id",
            "sidebar_collapsed",
            "quick_actions_collapsed",
        ):
            fields.append(f"{k} = ?")
            values.append(v)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(user_id.strip())

    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            query = f"UPDATE user_preferences SET {', '.join(fields)} WHERE LOWER(user_id) = LOWER(?)"
            cur.execute(query, values)
            return cur.rowcount > 0
    finally:
        conn.close()


def update_user_theme(username: str, theme: str, db_path: Optional[str] = None) -> bool:
    """Update user's preferred UI theme ('dark' or 'light')."""
    if theme not in ("dark", "light"):
        raise ValueError("Theme must be 'dark' or 'light'.")
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET theme = ? WHERE LOWER(username) = LOWER(?)",
                (theme, username.strip()),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def get_user_theme(username: str, db_path: Optional[str] = None) -> str:
    """Retrieve user's preferred UI theme, defaulting to 'dark'."""
    user = get_user_by_username(username, db_path)
    if user and user.get("theme"):
        return user["theme"]
    return "dark"


def update_user_profile(
    username: str,
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    profile_image_b64: Optional[str] = None,
    role: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Update user profile fields (first_name, last_name, phone, profile_image_b64, role)."""
    if not first_name or not first_name.strip():
        raise ValueError("First name is required.")
    if not last_name or not last_name.strip():
        raise ValueError("Last name is required.")
    if role is not None:
        from core.auth.validators import validate_role
        validate_role(role)

    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            if role is not None:
                cur.execute(
                    """
                    UPDATE users
                    SET first_name = ?, last_name = ?, phone = ?, profile_image_b64 = ?, role = ?
                    WHERE LOWER(username) = LOWER(?)
                    """,
                    (
                        first_name.strip(),
                        last_name.strip(),
                        phone.strip() if (phone and phone.strip()) else None,
                        profile_image_b64,
                        role.strip(),
                        username.strip(),
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET first_name = ?, last_name = ?, phone = ?, profile_image_b64 = ?
                    WHERE LOWER(username) = LOWER(?)
                    """,
                    (
                        first_name.strip(),
                        last_name.strip(),
                        phone.strip() if (phone and phone.strip()) else None,
                        profile_image_b64,
                        username.strip(),
                    ),
                )
        updated_user = get_user_by_username(username, db_path)
        if not updated_user:
            raise RuntimeError("Failed to retrieve updated user profile.")
        return updated_user
    finally:
        conn.close()


def user_exists(username: str, email: str, db_path: Optional[str] = None) -> bool:
    """Check if username or email already exists in users table."""
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?) LIMIT 1",
            (username.strip(), email.strip()),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def get_user_by_username(username: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by username."""
    if not username:
        return None
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)
        )
        row = cur.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_user_by_email(email: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by email."""
    if not email:
        return None
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),)
        )
        row = cur.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def create_user(
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    phone: Optional[str],
    role: str,
    password: str,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new user in the database after validating fields."""
    validate_registration_data(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        phone=phone,
        role=role,
        password=password,
    )

    clean_username = username.strip()
    clean_email = email.strip().lower()
    clean_phone = phone.strip() if (phone and isinstance(phone, str) and phone.strip()) else None

    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, email FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
            (clean_username, clean_email),
        )
        existing = cur.fetchone()
        if existing:
            if existing["username"].lower() == clean_username.lower():
                raise ValueError(f"Username '{clean_username}' is already taken.")
            if existing["email"].lower() == clean_email.lower():
                raise ValueError(f"Email '{clean_email}' is already registered.")

        pw_hash = hash_password(password)

        with conn:
            cur.execute(
                """
                INSERT INTO users (
                    first_name, last_name, username, email, phone, role, password_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    first_name.strip(),
                    last_name.strip(),
                    clean_username,
                    clean_email,
                    clean_phone,
                    role,
                    pw_hash,
                ),
            )
        user = get_user_by_username(clean_username, db_path)
        if not user:
            raise RuntimeError("Failed to retrieve created user record.")
        return user
    finally:
        conn.close()


def authenticate_user(
    username: str, password: str, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Authenticate user by username or email and password."""
    if not username or not password:
        return None

    user = get_user_by_username(username, db_path) or get_user_by_email(username, db_path)
    if not user:
        return None

    if verify_password(password, user["password_hash"]):
        update_last_login(user["username"], db_path)
        user_dict = dict(user)
        # Refresh user dict to get updated last_login
        updated_user = get_user_by_username(user["username"], db_path)
        return updated_user or user_dict

    return None


def update_password(
    username: str, new_password: str, db_path: Optional[str] = None
) -> bool:
    """Update user's password in the database."""
    validate_password(new_password)
    user = get_user_by_username(username, db_path) or get_user_by_email(username, db_path)
    if not user:
        return False

    pw_hash = hash_password(new_password)
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (pw_hash, user["username"]),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def update_last_login(username: str, db_path: Optional[str] = None) -> bool:
    """Update last_login timestamp for user."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE LOWER(username) = LOWER(?)",
                (username.strip(),),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def generate_remember_token(
    username: str, db_path: Optional[str] = None
) -> str:
    """Generate a UUID remember token, store it in database, and return it."""
    user = get_user_by_username(username, db_path)
    if not user:
        raise ValueError(f"User '{username}' does not exist.")

    token = str(uuid.uuid4())
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET remember_token = ? WHERE username = ?",
                (token, user["username"]),
            )
        return token
    finally:
        conn.close()


def validate_remember_token(
    token: str, db_path: Optional[str] = None
) -> Optional[str]:
    """Validate remember token and return matching username or None."""
    if not token or not isinstance(token, str):
        return None
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username FROM users WHERE remember_token = ? AND remember_token IS NOT NULL LIMIT 1",
            (token.strip(),),
        )
        row = cur.fetchone()
        if row:
            return row["username"]
        return None
    finally:
        conn.close()


def invalidate_remember_token(
    identifier: str, db_path: Optional[str] = None
) -> bool:
    """Invalidate remember token for user by username or token string."""
    if not identifier:
        return False
    conn = get_db_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET remember_token = NULL WHERE LOWER(username) = LOWER(?) OR remember_token = ?",
                (identifier.strip(), identifier.strip()),
            )
            return cur.rowcount > 0
    finally:
        conn.close()
