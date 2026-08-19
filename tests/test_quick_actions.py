"""Unit tests for Quick Start Actions & Intent Mapping (Task 17)."""

import pytest
from ui.workspace import QUICK_ACTIONS, handle_quick_action
from core.planner.enums import EducationalIntent
from core.chat.database import init_chat_db


@pytest.fixture
def temp_chat_db(tmp_path):
    db_file = tmp_path / "test_ekip_chats.db"
    init_chat_db(str(db_file))
    return str(db_file)


def test_quick_actions_mapping():
    assert len(QUICK_ACTIONS) == 8

    intents = {act["intent"] for act in QUICK_ACTIONS}
    assert "CONCEPT_EXPLANATION" in intents
    assert "WEB_SEARCH" in intents
    assert "DOCUMENT_SUMMARIZATION" in intents
    assert "QUIZ_GENERATION" in intents
    assert "COMPARISON" in intents
    assert "GENERAL_KNOWLEDGE" in intents


def test_quick_action_cards_structure():
    for card in QUICK_ACTIONS:
        assert "icon" in card
        assert "label" in card
        assert "subtitle" in card
        assert "intent" in card
        assert "auto_submit" in card
