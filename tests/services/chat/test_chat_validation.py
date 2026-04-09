"""
Chat Validation Tests

Validation and edge case tests for chat/conversation operations including
bad requests, response field completeness, and query length limits.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import pytest


@pytest.mark.core
class TestChatValidation:
    """Core validation checks for chat operations."""

    def test_chat_bad_request_missing_corpus(self, client):
        """POST /v2/chats without search.corpora should return 400."""
        response = client.post(
            "/v2/chats",
            data={
                "query": "Tell me about AI",
                "search": {},
                "chat": {"store": True},
            },
        )

        assert response.status_code == 400, f"Expected 400 for missing corpora, got {response.status_code} - {response.data}"

    def test_chat_response_field_completeness(self, client, seeded_shared_corpus):
        """Create a chat and verify chat_id, turn_id, answer, and search_results are present."""
        response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text="What is artificial intelligence?",
        )

        if not response.success and "rephraser" in str(response.data).lower():
            pytest.skip("Chat rephraser not configured on this instance")

        assert response.success, f"Create chat failed: {response.status_code} - {response.data}"

        chat_id = response.data.get("chat_id")
        assert chat_id is not None, f"Response missing chat_id: {response.data}"
        assert response.data.get("turn_id") is not None, f"Response missing turn_id: {response.data}"
        assert response.data.get("answer") is not None, f"Response missing answer: {response.data}"
        assert response.data.get("search_results") is not None, f"Response missing search_results: {response.data}"

        if chat_id:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass


@pytest.mark.regression
class TestChatEdgeCases:
    """Regression tests for chat query length limits."""

    def test_chat_query_max_length_accepted(self, client, seeded_shared_corpus):
        """A 5000 character query should be accepted."""
        long_query = "a" * 5000

        response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text=long_query,
        )

        if not response.success and "rephraser" in str(response.data).lower():
            pytest.skip("Chat rephraser not configured on this instance")

        assert response.success, f"5000 char query should succeed, got: {response.status_code} - {response.data}"

        chat_id = response.data.get("chat_id")
        if chat_id:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_chat_query_exceeds_max_length(self, client, seeded_shared_corpus):
        """A 5001 character query should return an error."""
        long_query = "a" * 5001

        response = client.create_chat(
            corpus_key=seeded_shared_corpus,
            query_text=long_query,
        )

        if not response.success and "rephraser" in str(response.data).lower():
            pytest.skip("Chat rephraser not configured on this instance")

        assert not response.success, f"5001 char query should fail, got: {response.status_code} - {response.data}"
        assert response.status_code in (400, 413, 422), f"Expected 400/413/422 for oversized query, got {response.status_code}"

        chat_id = response.data.get("chat_id") if isinstance(response.data, dict) else None
        if chat_id:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass
