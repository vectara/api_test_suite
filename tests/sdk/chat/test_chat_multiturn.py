"""
Chat Multi-Turn Tests (SDK)

Deep verification of chat turn counts, IDs, and content substantiveness
using the Vectara Python SDK.
"""

import pytest
from vectara.types import ChatParameters, KeyedSearchCorpus, SearchCorporaParameters


@pytest.mark.core
class TestChatMultiTurn:
    """Chat multi-turn deep verification."""

    def _create_chat(self, sdk_client, corpus_key):
        """Create a chat and return (chat_id, turn_id). Fail on error."""
        response = sdk_client.chat(
            query="What is artificial intelligence?",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=corpus_key)],
            ),
            chat=ChatParameters(store=True),
        )
        chat_id = response.chat_id
        turn_id = response.turn_id
        assert chat_id, f"No chat_id in response"
        return chat_id, turn_id

    def test_multiturn_turn_count_and_ids(self, sdk_client, sdk_seeded_shared_corpus):
        """Create chat + add turn, verify turn count and distinct IDs."""
        chat_id, turn_id_1 = self._create_chat(sdk_client, sdk_seeded_shared_corpus)

        try:
            add_resp = sdk_client.chats.create_turns(
                chat_id=chat_id,
                query="Tell me about vector databases",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
            )
            turn_id_2 = add_resp.turn_id

            turns_response = sdk_client.chats.list_turns(chat_id)
            turns = turns_response.turns or []
            assert len(turns) >= 2, f"Expected at least 2 turns, got {len(turns)}"

            turn_ids = [t.id for t in turns]
            assert len(set(turn_ids)) == len(turn_ids), f"Turn IDs should be distinct: {turn_ids}"
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_get_individual_turns_by_id(self, sdk_client, sdk_seeded_shared_corpus):
        """GET each turn by ID, verify chat_id and fields."""
        chat_id, _ = self._create_chat(sdk_client, sdk_seeded_shared_corpus)

        try:
            sdk_client.chats.create_turns(
                chat_id=chat_id,
                query="Tell me about machine learning",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
            )

            turns_response = sdk_client.chats.list_turns(chat_id)
            turns = turns_response.turns or []

            for turn in turns:
                turn_id = turn.id
                if not turn_id:
                    continue
                get_resp = sdk_client.chats.get_turn(chat_id, turn_id)
                assert get_resp.id == turn_id
                assert get_resp.chat_id == chat_id
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass

    def test_turn_answer_is_substantive(self, sdk_client, sdk_seeded_shared_corpus):
        """Verify each turn answer has real content, not empty."""
        chat_id, _ = self._create_chat(sdk_client, sdk_seeded_shared_corpus)

        try:
            sdk_client.chats.create_turns(
                chat_id=chat_id,
                query="How do vector databases work?",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                ),
            )

            turns_response = sdk_client.chats.list_turns(chat_id)
            turns = turns_response.turns or []

            turns_with_answers = [t for t in turns if t.answer]
            assert len(turns_with_answers) > 0, "Expected at least one turn with an answer"
            for turn in turns_with_answers:
                answer = turn.answer
                assert len(answer) > 20, f"Turn answer should be substantive (>20 chars), got {len(answer)} chars: {answer[:50]!r}"
        finally:
            try:
                sdk_client.chats.delete(chat_id)
            except Exception:
                pass
