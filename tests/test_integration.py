"""End-to-End Integration Test Suite for EKIP Platform (Task 18)."""

import pytest
import tempfile
from pathlib import Path

from core.auth.database import (
    init_db,
    init_user_preferences,
    create_user,
    authenticate_user,
    update_user_theme,
    get_user_theme,
    generate_remember_token,
    validate_remember_token,
    invalidate_remember_token,
)
from core.chat.database import (
    init_chat_db,
    create_chat_session,
    save_message,
    get_chat_messages,
    get_chat_sessions,
    delete_chat_session,
)
from core.documents import (
    init_documents_table,
    save_user_document,
    get_user_documents,
    delete_user_document,
    get_document_chunks,
)


@pytest.fixture
def temp_dbs(tmp_path):
    users_db = str(tmp_path / "ekip_users.db")
    chats_db = str(tmp_path / "ekip_chats.db")

    init_db(users_db)
    init_user_preferences(users_db)
    init_chat_db(chats_db)
    init_documents_table(users_db)

    return {"users_db": users_db, "chats_db": chats_db}


def test_full_user_journey(temp_dbs):
    u_db = temp_dbs["users_db"]
    c_db = temp_dbs["chats_db"]
    username = "e2e_student"
    password = "SecurePassword123!"

    # 1. Create user
    res = create_user(
        username=username,
        email="student@ekip.edu",
        password=password,
        first_name="E2E",
        last_name="Tester",
        role="Student",
        phone="+1234567890",
        db_path=u_db,
    )
    assert res is not None
    assert res["username"] == username

    # 2. Authenticate
    authenticated_user = authenticate_user(username, password, db_path=u_db)
    assert authenticated_user is not None
    assert authenticated_user["username"] == username

    # 3. Create Chat Session
    session_id = create_chat_session(username, "E2E Quantum Chat", db_path=c_db)
    assert session_id is not None

    # 4. Save Messages
    save_message(session_id, "user", "What is quantum entanglement?", db_path=c_db)
    save_message(session_id, "assistant", "Quantum entanglement is a phenomenon...", db_path=c_db)

    # 5. Verify Retrieval
    messages = get_chat_messages(session_id, db_path=c_db)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # 6. Delete Chat
    deleted = delete_chat_session(session_id, db_path=c_db)
    assert deleted is True

    # 7. Verify Cleanup
    sessions = get_chat_sessions(username, db_path=c_db)
    assert len(sessions) == 0


def test_theme_persistence(temp_dbs):
    u_db = temp_dbs["users_db"]
    username = "theme_user"
    create_user(
        first_name="Theme",
        last_name="User",
        username=username,
        email="theme@ekip.edu",
        phone=None,
        role="Student",
        password="Pass123!",
        db_path=u_db,
    )

    # Default Theme
    assert get_user_theme(username, db_path=u_db) == "dark"

    # Update Theme
    assert update_user_theme(username, "light", db_path=u_db) is True
    assert get_user_theme(username, db_path=u_db) == "light"

    # Switch Back
    assert update_user_theme(username, "dark", db_path=u_db) is True
    assert get_user_theme(username, db_path=u_db) == "dark"


def test_remember_me_token(temp_dbs):
    u_db = temp_dbs["users_db"]
    username = "remember_user"
    create_user(
        first_name="Remember",
        last_name="User",
        username=username,
        email="remember@ekip.edu",
        phone=None,
        role="Student",
        password="Pass123!",
        db_path=u_db,
    )

    # Generate token
    token = generate_remember_token(username, db_path=u_db)
    assert token is not None

    # Validate token
    validated = validate_remember_token(token, db_path=u_db)
    assert validated == username

    # Invalidate token
    assert invalidate_remember_token(username, db_path=u_db) is True
    assert validate_remember_token(token, db_path=u_db) is None


def test_document_upload_and_delete(temp_dbs):
    u_db = temp_dbs["users_db"]
    user_id = "doc_user"

    chunks = [
        {"page_content": "Deep solar system research paper details.", "metadata": {"page_number": 1}},
        {"page_content": "Mars exploration missions review.", "metadata": {"page_number": 2}},
    ]

    doc_id = save_user_document(user_id, "solar_system.pdf", "Solar System Report", "pdf", 204800, chunks, db_path=u_db)
    assert doc_id is not None

    # Verify in DB
    docs = get_user_documents(user_id, db_path=u_db)
    assert len(docs) == 1
    assert docs[0]["filename"] == "solar_system.pdf"

    # Retrieve Chunks
    chk_list = get_document_chunks(doc_id, db_path=u_db)
    assert len(chk_list) == 2

    # Delete Document
    deleted = delete_user_document(user_id, doc_id, db_path=u_db)
    assert deleted is True

    # Verify Removed
    assert len(get_user_documents(user_id, db_path=u_db)) == 0
