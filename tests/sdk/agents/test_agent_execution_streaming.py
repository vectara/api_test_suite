"""
Agent Execution Streaming Tests (SDK)

Tests for agent execution event responses, verifying events arrive correctly.
"""

import pytest

from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage

from utils.waiters import wait_for


def _session_exists(sdk_client, agent_key, session_key):
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


@pytest.mark.core
class TestAgentExecutionStreaming:
    """Core tests for agent execution event responses."""

    def test_execute_agent_sse(self, sdk_client, sdk_shared_agent):
        """Send message to agent and verify events arrive in response."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        wait_for(
            lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
            timeout=10,
            interval=0.5,
            description="session to be available",
        )

        response = sdk_client.agent_events.create(
            sdk_shared_agent,
            session_key,
            request=CreateAgentEventsRequestBody_InputMessage(
                messages=[{"type": "text", "content": "What is Vectara?"}],
                stream_response=False,
            ),
        )
        assert response is not None, "Agent execution should return a response"

        events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
        assert len(events) > 0, "Expected at least one event"

        event_types = [getattr(e, "type", None) for e in events]
        has_output = any(
            et and ("output" in str(et) or "message" in str(et))
            for et in event_types
        )
        assert has_output, f"No output event found. Event types: {event_types}"

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
        except Exception:
            pass
