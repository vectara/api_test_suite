"""
Chat Turn CRUD Tests (SDK)

Core-level tests for chat turn operations including listing, retrieving,
updating, and deleting individual turns within a chat conversation
using the Vectara Python SDK.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import re

import pytest

from vectara.types import (
    SearchCorporaParameters,
    KeyedSearchCorpus,
    ChatParameters,
)
from vectara.errors import NotFoundError, BadRequestError


def _create_chat(sdk_client, corpus_key):
    """Create a chat and return (chat_id, turn_id, answer). Fail on error."""
    try:
        response = sdk_client.chat(
            query="Tell me about AI",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=corpus_key)],
            ),
            chat=ChatParameters(store=True),
        )
    except Exception as e:
        if "rephraser" in str(e).lower():
            pytest.skip("Chat rephraser not configured on this instance")
        raise

    chat_id = response.chat_id
    turn_id = response.turn_id
    answer = response.answer

    assert chat_id, f"No chat_id in create_chat response"

    return chat_id, turn_id, answer


@pytest.mark.core
class TestChatTurns:
    """Core checks for chat turn CRUD operations."""

    def test_get_single_chat(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat and GET it to verify chat_id is present."""
        chat_id, _, _ = _create_chat(sdk_client, sdk_seeded_shared_corpus)

        try:
            chat = sdk_client.chats.get(chat_id)

            assert chat.id is not None, f"Response should contain id"
            assert re.match(r"cht_.+", chat.id), f"id should match cht_.+ pattern, got: {chat.id}"
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_chat_not_found_returns_404(self, sdk_client):
        """GET a non-existent chat should raise NotFoundError."""
        with pytest.raises(NotFoundError):
            sdk_client.chats.get("cht_nonexistent_000000000000")

    def test_list_chat_turns(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat, list its turns, and verify at least 1 turn exists."""
        chat_id, _, _ = _create_chat(sdk_client, sdk_seeded_shared_corpus)

        try:
            turns = sdk_client.chats.list_turns(chat_id)

            assert len(turns) >= 1, f"Expected at least 1 turn, got {len(turns)}"

            first_turn = turns[0]
            assert first_turn.id is not None, f"Turn should have id"
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_get_chat_turn(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat, get the turn by ID, and verify fields."""
        chat_id, turn_id, _ = _create_chat(sdk_client, sdk_seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            turn = sdk_client.chats.get_turn(chat_id, turn_id)

            assert turn.id == turn_id, f"turn id mismatch: expected {turn_id}, got {turn.id}"
            assert re.match(r"trn_.+", turn.id), f"turn id should match trn_.+ pattern, got: {turn.id}"
            assert turn.chat_id == chat_id, f"chat_id mismatch in turn: expected {chat_id}, got {turn.chat_id}"
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_update_chat_turn(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat, PATCH the turn with enabled=false, then GET to verify."""
        chat_id, turn_id, _ = _create_chat(sdk_client, sdk_seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            sdk_client.chats.update_turn(
                chat_id=chat_id,
                turn_id=turn_id,
                enabled=False,
            )

            get_turn = sdk_client.chats.get_turn(chat_id, turn_id)
            assert get_turn.enabled is False, (
                f"Expected enabled=False after update, got: {get_turn.enabled}"
            )
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_delete_chat_turn(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat, delete the turn, and verify it returns error."""
        chat_id, turn_id, _ = _create_chat(sdk_client, sdk_seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            sdk_client.chats.delete_turn(chat_id, turn_id)

            with pytest.raises((NotFoundError, BadRequestError)):
                sdk_client.chats.get_turn(chat_id, turn_id)
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass
