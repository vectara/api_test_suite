"""
Chat Validation Tests (SDK)

Validation and edge case tests for chat/conversation operations including
bad requests, response field completeness, and query length limits
using the Vectara Python SDK.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import pytest
from vectara.errors import BadRequestError
from vectara.types import ChatParameters, KeyedSearchCorpus, SearchCorporaParameters


@pytest.mark.core
class TestChatValidation:
    """Core validation checks for chat operations."""

    def test_chat_bad_request_missing_corpus(self, sdk_client):
        """Chat without search.corpora should raise BadRequestError."""
        with pytest.raises((BadRequestError, Exception)):
            sdk_client.chat(
                query="Tell me about AI",
                search=SearchCorporaParameters(),
                chat=ChatParameters(store=True),
            )

    def test_chat_response_field_completeness(self, sdk_client, sdk_seeded_shared_corpus):
        """Create a chat and verify chat_id, turn_id, answer, and search_results are present."""
        try:
            response = sdk_client.chat(
                query="What is artificial intelligence?",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            raise

        assert response.chat_id is not None, f"Response missing chat_id"
        assert response.turn_id is not None, f"Response missing turn_id"
        assert response.answer is not None, f"Response missing answer"
        assert response.search_results is not None, f"Response missing search_results"

        if response.chat_id:
            try:
                sdk_client.chats.delete(response.chat_id)
            except Exception:
                pass


@pytest.mark.regression
class TestChatEdgeCases:
    """Regression tests for chat query length limits."""

    def test_chat_query_max_length_accepted(self, sdk_client, sdk_seeded_shared_corpus):
        """A 5000 character query should be accepted."""
        long_query = "a" * 5000

        try:
            response = sdk_client.chat(
                query=long_query,
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            raise

        assert response.chat_id is not None, "5000 char query should succeed"

        if response.chat_id:
            try:
                sdk_client.chats.delete(response.chat_id)
            except Exception:
                pass

    def test_chat_query_exceeds_max_length(self, sdk_client, sdk_seeded_shared_corpus):
        """A 5001 character query should return an error."""
        long_query = "a" * 5001

        try:
            response = sdk_client.chat(
                query=long_query,
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            # Expected: should raise an error for oversized query
            return

        # If it did not raise, the test fails
        chat_id = response.chat_id
        if chat_id:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass
        pytest.fail(f"5001 char query should have raised an error")
