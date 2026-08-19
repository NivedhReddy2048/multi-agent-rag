"""Unit tests for Document Management API (Task 15)."""

import pytest
from core.documents import (
    init_documents_table,
    save_user_document,
    get_user_documents,
    delete_user_document,
    get_document_chunks,
    reindex_document,
)


@pytest.fixture
def temp_doc_db(tmp_path):
    db_file = tmp_path / "test_ekip_docs.db"
    init_documents_table(str(db_file))
    return str(db_file)


def test_document_lifecycle(temp_doc_db):
    user_id = "testuser"
    filename = "venus.pdf"
    title = "Venus Overview"
    doc_type = "pdf"
    size_bytes = 102400
    chunks = [
        {"page_content": "Venus is the second planet from the Sun.", "metadata": {"page_number": 1}},
        {"page_content": "It has a dense atmosphere.", "metadata": {"page_number": 2}},
    ]

    # Save
    doc_id = save_user_document(user_id, filename, title, doc_type, size_bytes, chunks, db_path=temp_doc_db)
    assert doc_id is not None

    # Retrieve
    docs = get_user_documents(user_id, db_path=temp_doc_db)
    assert len(docs) == 1
    assert docs[0]["filename"] == "venus.pdf"
    assert docs[0]["chunk_count"] == 2

    # Chunks
    chk_list = get_document_chunks(doc_id, db_path=temp_doc_db)
    assert len(chk_list) == 2
    assert "second planet" in chk_list[0]["text"]

    # Reindex
    assert reindex_document(user_id, doc_id, db_path=temp_doc_db) is True

    # Delete
    assert delete_user_document(user_id, doc_id, db_path=temp_doc_db) is True
    assert len(get_user_documents(user_id, db_path=temp_doc_db)) == 0
