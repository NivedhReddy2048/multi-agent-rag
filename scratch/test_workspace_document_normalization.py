"""Targeted regression tests for Student Workspace document normalization and filename extraction."""

import pytest
from typing import Dict, Any

from ui.workspace import (
    normalize_workspace_docs,
    get_workspace_doc_name,
)


class DummyDoc:
    def __init__(self, filename=None, name=None, original_filename=None, title=None):
        if filename:
            self.filename = filename
        if name:
            self.name = name
        if original_filename:
            self.original_filename = original_filename
        if title:
            self.title = title


def test_normalize_none_input():
    """A. None input must return an empty list."""
    assert normalize_workspace_docs(None) == []


def test_normalize_list_input():
    """B. List input must remain a list."""
    doc1 = {"filename": "a.pdf"}
    doc2 = {"filename": "b.pdf"}
    raw = [doc1, doc2]
    normalized = normalize_workspace_docs(raw)
    assert isinstance(normalized, list)
    assert normalized == [doc1, doc2]


def test_normalize_wrapper_dict_documents():
    """C. Wrapper dictionary using 'documents' key."""
    doc1 = {"filename": "a.pdf"}
    doc2 = {"filename": "b.pdf"}
    raw = {"documents": [doc1, doc2]}
    normalized = normalize_workspace_docs(raw)
    assert normalized == [doc1, doc2]


def test_normalize_wrapper_dict_items():
    """D. Wrapper dictionary using 'items' key."""
    doc1 = {"filename": "a.pdf"}
    doc2 = {"filename": "b.pdf"}
    raw = {"items": [doc1, doc2]}
    normalized = normalize_workspace_docs(raw)
    assert normalized == [doc1, doc2]


def test_normalize_id_to_doc_dict():
    """E. ID-to-document dictionary must return document VALUES, not IDs."""
    doc1 = DummyDoc(filename="solar_system.pdf")
    doc2 = DummyDoc(filename="fastapi.pdf")
    raw = {"id1": doc1, "id2": doc2}
    normalized = normalize_workspace_docs(raw)
    assert isinstance(normalized, list)
    assert len(normalized) == 2
    assert normalized[0] == doc1
    assert normalized[1] == doc2
    # Ensure IDs ("id1", "id2") were not returned as elements
    assert "id1" not in normalized


def test_normalize_single_object():
    """F. Single object input must return [object]."""
    doc = DummyDoc(filename="single.pdf")
    normalized = normalize_workspace_docs(doc)
    assert normalized == [doc]


def test_get_doc_name_from_dict():
    """G. Filename extraction from dictionary with priority."""
    assert get_workspace_doc_name({"filename": "notes.pdf"}) == "notes.pdf"
    assert get_workspace_doc_name({"name": "lecture.docx"}) == "lecture.docx"
    assert get_workspace_doc_name({"original_filename": "data.csv"}) == "data.csv"
    assert get_workspace_doc_name({"title": "Research Paper"}) == "Research Paper"
    assert get_workspace_doc_name({}) == "Untitled document"


def test_get_doc_name_from_object():
    """H. Filename extraction from object with priority."""
    assert get_workspace_doc_name(DummyDoc(filename="notes.pdf")) == "notes.pdf"
    assert get_workspace_doc_name(DummyDoc(name="lecture.docx")) == "lecture.docx"
    assert get_workspace_doc_name(DummyDoc(original_filename="data.csv")) == "data.csv"
    assert get_workspace_doc_name(DummyDoc(title="Research Paper")) == "Research Paper"
    assert get_workspace_doc_name(DummyDoc()) == "Untitled document"


def test_rendering_regression_raw_dict():
    """I. Ensure engine.list_docs() dict shape is normalized without KeyError slice error."""
    class MockEngine:
        def list_docs(self) -> Dict[str, Any]:
            return {
                "solar_system.pdf": {"chunks": 12, "pages": 3},
                "fastapi_tutorial.pdf": {"chunks": 8, "pages": 2},
            }

    engine = MockEngine()
    raw_docs = engine.list_docs()
    normalized = normalize_workspace_docs(raw_docs)
    assert isinstance(normalized, list)
    assert len(normalized) == 2
    assert get_workspace_doc_name(normalized[0]) == "solar_system.pdf"
    assert get_workspace_doc_name(normalized[1]) == "fastapi_tutorial.pdf"
