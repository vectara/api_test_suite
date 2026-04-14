"""
Agent Context Preservation Tests (SDK)

Verify multi-turn context is retained across 3+ turns and
that context is not shared between separate sessions.
"""

import pytest

from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage

from utils.waiters import wait_for


@pytest.mark.core
class TestAgentContextPreservation:
    """Multi-turn context retention tests."""

    def test_three_turn_context_preservation(self, sdk_client, sdk_shared_agent):
        """Send 3 turns, verify the 3rd turn retains context from turn 1."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            wait_for(
                lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
                timeout=10,
                interval=0.5,
                description="session available",
            )

            turn1 = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "My name is Alexander and I work at Acme Corp."}],
                    stream_response=False,
                ),
            )
            assert turn1 is not None, "Turn 1 failed"

            turn2 = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "I'm interested in semantic search technology."}],
                    stream_response=False,
                ),
            )
            assert turn2 is not None, "Turn 2 failed"

            turn3 = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "What company do I work at and what technology am I interested in?"}],
                    stream_response=False,
                ),
            )
            assert turn3 is not None, "Turn 3 failed"

            # Collect output from turn 3 events
            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            output_text = _extract_output_text(events).lower()

            assert "acme" in output_text, (
                f"Turn 3 should reference 'Acme' from turn 1, got: {output_text[:200]}"
            )
            assert "semantic" in output_text or "search" in output_text, (
                f"Turn 3 should reference 'semantic search' from turn 2, got: {output_text[:200]}"
            )
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass

    def test_context_not_shared_across_sessions(self, sdk_client, sdk_shared_agent):
        """Verify context from session A does not leak into session B."""
        session_a = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_b = sdk_client.agent_sessions.create(sdk_shared_agent)

        key_a = session_a.key
        key_b = session_b.key

        try:
            for key in [key_a, key_b]:
                wait_for(
                    lambda k=key: _session_exists(sdk_client, sdk_shared_agent, k),
                    timeout=10,
                    interval=0.5,
                    description=f"session {key} available",
                )

            sdk_client.agent_events.create(
                sdk_shared_agent,
                key_a,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Remember this secret code: XYLOPHONE-7749. My pet iguana is named Bartholomew."}],
                    stream_response=False,
                ),
            )

            sdk_client.agent_events.create(
                sdk_shared_agent,
                key_b,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "What is my secret code? What is my pet's name?"}],
                    stream_response=False,
                ),
            )

            events_b = list(sdk_client.agent_events.list(sdk_shared_agent, key_b))
            output_b = _extract_output_text(events_b).lower()

            assert "xylophone" not in output_b and "7749" not in output_b, (
                f"Session B should NOT know session A's secret code, but got: {output_b[:200]}"
            )
            assert "bartholomew" not in output_b, (
                f"Session B should NOT know session A's pet name, but got: {output_b[:200]}"
            )
        finally:
            for key in [key_a, key_b]:
                if key:
                    try:
                        sdk_client.agent_sessions.delete(sdk_shared_agent, key)
                    except Exception:
                        pass


def _session_exists(sdk_client, agent_key, session_key):
    """Return True if the session can be retrieved."""
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


def _extract_output_text(events):
    """Extract output text from agent events."""
    output_parts = []
    for event in events:
        event_type = getattr(event, "type", None)
        if event_type and ("output" in str(event_type) or "message" in str(event_type)):
            content = getattr(event, "content", "") or ""
            if content:
                output_parts.append(content)
    return " ".join(output_parts)
