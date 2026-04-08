"""
Agent Context Preservation Tests

Verify multi-turn context is retained across 3+ turns and
that context is not shared between separate sessions.
"""

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestAgentContextPreservation:
    """Multi-turn context retention tests."""

    def test_three_turn_context_preservation(self, client, shared_agent):
        """Send 3 turns, verify the 3rd turn retains context from turn 1."""
        session_resp = client.create_agent_session(shared_agent)
        assert session_resp.success, f"Create session failed: {session_resp.status_code} - {session_resp.data}"

        session_key = session_resp.data.get("key")
        try:
            wait_for(
                lambda: client.get_agent_session(shared_agent, session_key).success,
                timeout=10, interval=0.5,
                description="session available",
            )

            turn1 = client.execute_agent(
                shared_agent,
                "My name is Alexander and I work at Acme Corp.",
                session_id=session_key,
            )
            assert turn1.success, f"Turn 1 failed: {turn1.status_code} - {turn1.data}"

            turn2 = client.execute_agent(
                shared_agent,
                "I'm interested in semantic search technology.",
                session_id=session_key,
            )
            assert turn2.success, f"Turn 2 failed: {turn2.status_code} - {turn2.data}"

            turn3 = client.execute_agent(
                shared_agent,
                "What company do I work at and what technology am I interested in?",
                session_id=session_key,
            )
            assert turn3.success, f"Turn 3 failed: {turn3.status_code} - {turn3.data}"

            events = turn3.data.get("events", [])
            output_events = [e for e in events if e.get("type") == "agent_output"]
            output_text = " ".join(e.get("content", "") for e in output_events).lower()

            assert "acme" in output_text, \
                f"Turn 3 should reference 'Acme' from turn 1, got: {output_text[:200]}"
            assert "semantic" in output_text or "search" in output_text, \
                f"Turn 3 should reference 'semantic search' from turn 2, got: {output_text[:200]}"
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_context_not_shared_across_sessions(self, client, shared_agent):
        """Verify context from session A does not leak into session B."""
        session_a = client.create_agent_session(shared_agent)
        session_b = client.create_agent_session(shared_agent)

        assert session_a.success, f"Create session A failed: {session_a.status_code} - {session_a.data}"
        assert session_b.success, f"Create session B failed: {session_b.status_code} - {session_b.data}"

        key_a = session_a.data.get("key")
        key_b = session_b.data.get("key")

        try:
            for key in [key_a, key_b]:
                wait_for(
                    lambda k=key: client.get_agent_session(shared_agent, k).success,
                    timeout=10, interval=0.5,
                    description=f"session {key} available",
                )

            resp_a = client.execute_agent(
                shared_agent,
                "Remember this secret code: XYLOPHONE-7749. My pet iguana is named Bartholomew.",
                session_id=key_a,
            )
            assert resp_a.success, f"Session A message failed: {resp_a.data}"

            resp_b = client.execute_agent(
                shared_agent,
                "What is my secret code? What is my pet's name?",
                session_id=key_b,
            )
            assert resp_b.success, f"Session B message failed: {resp_b.data}"

            events_b = resp_b.data.get("events", [])
            output_b = " ".join(
                e.get("content", "") for e in events_b if e.get("type") == "agent_output"
            ).lower()

            assert "xylophone" not in output_b and "7749" not in output_b, \
                f"Session B should NOT know session A's secret code, but got: {output_b[:200]}"
            assert "bartholomew" not in output_b, \
                f"Session B should NOT know session A's pet name, but got: {output_b[:200]}"
        finally:
            for key in [key_a, key_b]:
                if key:
                    try:
                        client.delete_agent_session(shared_agent, key)
                    except Exception:
                        pass
