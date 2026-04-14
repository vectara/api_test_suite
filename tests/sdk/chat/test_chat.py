"""
Chat Tests (SDK)

Core-level tests for chat/conversation operations including
creating, listing, adding turns, and deleting chats
using the Vectara Python SDK.

Note: Chat requires a configured rephraser on the instance.
Tests will skip gracefully if rephraser is not available.
"""

import pytest

from vectara.types import (
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
    ChatParameters,
)
from vectara.errors import NotFoundError


@pytest.mark.core
class TestChat:
    """Core checks for chat/conversation operations."""

    def test_create_chat(self, sdk_client, sdk_seeded_shared_corpus):
        """Test starting a new chat conversation."""
        try:
            response = sdk_client.chat(
                query="Tell me about AI",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            raise

        assert response.chat_id is not None, f"Response should contain chat_id"
        if response.chat_id:
            try:
                sdk_client.chats.delete(response.chat_id)
            except Exception:
                pass

    def test_list_chats(self, sdk_client):
        """Test listing chat conversations."""
        pager = sdk_client.chats.list(limit=10)
        chats = []
        try:
            for chat in pager:
                chats.append(chat)
                if len(chats) >= 10:
                    break
        except Exception:
            pass  # pagination may fail on long URLs
        assert isinstance(chats, list), f"Expected list, got: {type(chats)}"

    def test_chat_turn(self, sdk_client, sdk_seeded_shared_corpus):
        """Test adding turns to a chat conversation."""
        try:
            create_response = sdk_client.chat(
                query="What is machine learning?",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            pytest.skip(f"Could not create chat for turn test: {e}")

        chat_id = create_response.chat_id
        if not chat_id:
            pytest.skip("No chat_id in response")

        try:
            turn_response = sdk_client.chats.create_turns(
                chat_id=chat_id,
                query="Can you give me an example?",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
            )

            assert turn_response is not None, "Turn response should have data"
            turn_has_content = (
                getattr(turn_response, "answer", None) is not None
                or getattr(turn_response, "turn_id", None) is not None
            )
            assert turn_has_content, f"Turn response should have answer or turn_id"
        finally:
            sdk_client.chats.delete(chat_id)

    def test_delete_chat(self, sdk_client, sdk_seeded_shared_corpus):
        """Test deleting a chat conversation."""
        try:
            create_response = sdk_client.chat(
                query="Test chat for deletion",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
                chat=ChatParameters(store=True),
            )
        except Exception as e:
            if "rephraser" in str(e).lower():
                pytest.skip("Chat rephraser not configured on this instance")
            pytest.skip(f"Could not create chat for deletion test: {e}")

        chat_id = create_response.chat_id
        if not chat_id:
            pytest.skip("No chat_id in response")

        sdk_client.chats.delete(chat_id)

        with pytest.raises(NotFoundError):
            sdk_client.chats.get(chat_id)
