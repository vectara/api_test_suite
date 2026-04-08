"""
Chat Tests

Core-level tests for chat/conversation operations including
creating, listing, adding turns, and deleting chats.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import pytest


@pytest.mark.core
class TestChat:
    """Core checks for chat/conversation operations."""

    def test_create_chat(self, client, seeded_shared_corpus):
        """Test starting a new chat conversation."""
        response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text="Tell me about AI",
        )

        # Skip if chat rephraser not configured on this instance
        if not response.success and "rephraser" in str(response.data).lower():
            pytest.skip("Chat rephraser not configured on this instance")

        assert response.success, f"Create chat failed: {response.status_code} - {response.data}"

        # Should return chat ID
        chat_id = response.data.get("chat_id")
        assert chat_id is not None, f"Response should contain chat_id, got: {response.data}"
        if chat_id:
            # Cleanup
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_list_chats(self, client):
        """Test listing chat conversations."""
        response = client.list_chats(limit=10)

        assert response.success, f"List chats failed: {response.status_code} - {response.data}"
        assert isinstance(response.data, (dict, list)), \
            f"Expected dict or list response, got: {type(response.data)}"
        if isinstance(response.data, dict) and "chats" in response.data:
            assert isinstance(response.data["chats"], list), \
                f"Expected chats to be a list, got: {type(response.data['chats'])}"

    def test_chat_turn(self, client, seeded_shared_corpus):
        """Test adding turns to a chat conversation."""
        # Create chat
        create_response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text="What is machine learning?",
        )

        if not create_response.success:
            pytest.skip("Could not create chat for turn test")

        chat_id = create_response.data.get("chat_id")
        if not chat_id:
            pytest.skip("No chat_id in response")

        try:
            # Add follow-up turn
            turn_response = client.add_chat_turn(
                chat_id=chat_id,
                query_text="Can you give me an example?",
                corpus_key=seeded_shared_corpus,
            )

            assert turn_response.success, f"Add chat turn failed: {turn_response.status_code} - {turn_response.data}"
            assert turn_response.data is not None, "Turn response should have data"
            turn_has_content = (
                turn_response.data.get("answer") is not None
                or turn_response.data.get("turn_id") is not None
            )
            assert turn_has_content, f"Turn response should have answer or turn_id, got: {turn_response.data}"
        finally:
            # Cleanup
            client.delete_chat(chat_id)

    def test_delete_chat(self, client, seeded_shared_corpus):
        """Test deleting a chat conversation."""
        # Create chat
        create_response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text="Test chat for deletion",
        )

        if not create_response.success:
            pytest.skip("Could not create chat for deletion test")

        chat_id = create_response.data.get("chat_id")
        if not chat_id:
            pytest.skip("No chat_id in response")

        # Delete chat
        delete_response = client.delete_chat(chat_id)

        assert delete_response.success, f"Delete chat failed: {delete_response.status_code} - {delete_response.data}"

        get_resp = client.get_chat(chat_id)
        assert get_resp.status_code == 404, \
            f"Deleted chat should return 404, got {get_resp.status_code}"
