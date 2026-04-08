"""
Chat Turn CRUD Tests

Core-level tests for chat turn operations including listing, retrieving,
updating, and deleting individual turns within a chat conversation.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import re

import pytest


def _create_chat(client, corpus_key):
    """Create a chat and return (chat_id, turn_id, answer). Fail on error."""
    response = client.create_chat(
        corpus_key=corpus_key,
        query_text="Tell me about AI",
    )

    if not response.success and "rephraser" in str(response.data).lower():
        pytest.skip("Chat rephraser not configured on this instance")

    assert response.success, f"Create chat failed: {response.status_code} - {response.data}"

    chat_id = response.data.get("chat_id")
    turn_id = response.data.get("turn_id")
    answer = response.data.get("answer")

    assert chat_id, f"No chat_id in create_chat response: {response.data}"

    return chat_id, turn_id, answer


@pytest.mark.core
class TestChatTurns:
    """Core checks for chat turn CRUD operations."""

    def test_get_single_chat(self, client, seeded_shared_corpus):
        """Create a chat and GET /v2/chats/{id} to verify chat_id is present."""
        chat_id, _, _ = _create_chat(client, seeded_shared_corpus)

        try:
            response = client.get_chat(chat_id)

            assert response.success, f"Get chat failed: {response.status_code} - {response.data}"
            assert response.data.get("id") is not None, \
                f"Response should contain id, got: {response.data}"
            assert re.match(r"cht_.+", response.data["id"]), \
                f"id should match cht_.+ pattern, got: {response.data['id']}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_chat_not_found_returns_404(self, client):
        """GET a non-existent chat should return 404."""
        response = client.get_chat("cht_nonexistent_000000000000")

        assert response.status_code == 404, \
            f"Expected 404 for non-existent chat, got {response.status_code}"

    def test_list_chat_turns(self, client, seeded_shared_corpus):
        """Create a chat, list its turns, and verify at least 1 turn exists."""
        chat_id, _, _ = _create_chat(client, seeded_shared_corpus)

        try:
            response = client.list_chat_turns(chat_id)

            assert response.success, f"List turns failed: {response.status_code} - {response.data}"
            turns = response.data.get("turns", response.data if isinstance(response.data, list) else [])
            assert len(turns) >= 1, f"Expected at least 1 turn, got {len(turns)}"

            first_turn = turns[0]
            assert first_turn.get("id") is not None, \
                f"Turn should have id, got: {first_turn}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_get_chat_turn(self, client, seeded_shared_corpus):
        """Create a chat, get the turn by ID, and verify fields."""
        chat_id, turn_id, _ = _create_chat(client, seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            response = client.get_chat_turn(chat_id, turn_id)

            assert response.success, f"Get turn failed: {response.status_code} - {response.data}"
            assert response.data.get("id") == turn_id, \
                f"turn id mismatch: expected {turn_id}, got {response.data.get('id')}"
            assert re.match(r"trn_.+", response.data["id"]), \
                f"turn id should match trn_.+ pattern, got: {response.data['id']}"
            assert response.data.get("chat_id") == chat_id, \
                f"chat_id mismatch in turn: expected {chat_id}, got {response.data.get('chat_id')}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_update_chat_turn(self, client, seeded_shared_corpus):
        """Create a chat, PATCH the turn with enabled=false, then GET to verify."""
        chat_id, turn_id, _ = _create_chat(client, seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            update_response = client.update_chat_turn(
                chat_id=chat_id,
                turn_id=turn_id,
                enabled=False,
            )

            assert update_response.success, \
                f"Update turn failed: {update_response.status_code} - {update_response.data}"

            get_response = client.get_chat_turn(chat_id, turn_id)
            assert get_response.success, f"Get turn after update failed: {get_response.status_code}"
            assert get_response.data.get("enabled") is False, \
                f"Expected enabled=False after update, got: {get_response.data.get('enabled')}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_delete_chat_turn(self, client, seeded_shared_corpus):
        """Create a chat, delete the turn, and verify it returns 404 or error."""
        chat_id, turn_id, _ = _create_chat(client, seeded_shared_corpus)

        if not turn_id:
            pytest.skip("No turn_id in create_chat response")

        try:
            delete_response = client.delete_chat_turn(chat_id, turn_id)

            assert delete_response.success, \
                f"Delete turn failed: {delete_response.status_code} - {delete_response.data}"

            get_response = client.get_chat_turn(chat_id, turn_id)
            assert get_response.status_code in (404, 400), \
                f"Deleted turn should return 404 or 400, got {get_response.status_code}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass
