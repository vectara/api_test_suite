"""
Chat Multi-Turn Tests

Deep verification of chat turn counts, IDs, and content substantiveness.
"""

import pytest


@pytest.mark.core
class TestChatMultiTurn:
    """Chat multi-turn deep verification."""

    def _create_chat(self, client, corpus_key):
        """Create a chat and return (chat_id, turn_id). Fail on error."""
        resp = client.create_chat(corpus_key, "What is artificial intelligence?")
        assert resp.success, f"Create chat failed: {resp.status_code} - {resp.data}"
        chat_id = resp.data.get("chat_id") or resp.data.get("id")
        turn_id = resp.data.get("turn_id")
        assert chat_id, f"No chat_id in response: {resp.data}"
        return chat_id, turn_id

    def test_multiturn_turn_count_and_ids(self, client, seeded_shared_corpus):
        """Create chat + add turn, verify turn count and distinct IDs."""
        chat_id, turn_id_1 = self._create_chat(client, seeded_shared_corpus)

        try:
            add_resp = client.add_chat_turn(chat_id, "Tell me about vector databases", seeded_shared_corpus)
            assert add_resp.success, f"Add turn failed: {add_resp.status_code} - {add_resp.data}"
            turn_id_2 = add_resp.data.get("turn_id")

            list_resp = client.list_chat_turns(chat_id)
            assert list_resp.success, f"List turns failed: {list_resp.status_code}"
            turns = list_resp.data.get("turns", [])
            assert len(turns) >= 2, f"Expected at least 2 turns, got {len(turns)}"

            turn_ids = [t.get("id") for t in turns]
            assert len(set(turn_ids)) == len(turn_ids), f"Turn IDs should be distinct: {turn_ids}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_get_individual_turns_by_id(self, client, seeded_shared_corpus):
        """GET each turn by ID, verify chat_id and fields."""
        chat_id, _ = self._create_chat(client, seeded_shared_corpus)

        try:
            client.add_chat_turn(chat_id, "Tell me about machine learning", seeded_shared_corpus)

            list_resp = client.list_chat_turns(chat_id)
            assert list_resp.success
            turns = list_resp.data.get("turns", [])

            for turn in turns:
                turn_id = turn.get("id")
                if not turn_id:
                    continue
                get_resp = client.get_chat_turn(chat_id, turn_id)
                assert get_resp.success, f"GET turn {turn_id} failed: {get_resp.status_code}"
                assert get_resp.data.get("id") == turn_id
                assert get_resp.data.get("chat_id") == chat_id
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass

    def test_turn_answer_is_substantive(self, client, seeded_shared_corpus):
        """Verify each turn answer has real content, not empty."""
        chat_id, _ = self._create_chat(client, seeded_shared_corpus)

        try:
            add_resp = client.add_chat_turn(chat_id, "How do vector databases work?", seeded_shared_corpus)
            assert add_resp.success

            list_resp = client.list_chat_turns(chat_id)
            turns = list_resp.data.get("turns", [])

            turns_with_answers = [t for t in turns if t.get("answer")]
            assert len(turns_with_answers) > 0, f"Expected at least one turn with an answer"
            for turn in turns_with_answers:
                answer = turn["answer"]
                assert len(answer) > 20, f"Turn answer should be substantive (>20 chars), got {len(answer)} chars: {answer[:50]!r}"
        finally:
            try:
                client.delete_chat(chat_id)
            except Exception:
                pass
