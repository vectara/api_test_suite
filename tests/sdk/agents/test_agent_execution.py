"""
Agent Execution Tests (SDK)

Tests for executing queries against agents, multi-turn conversations,
and edge cases.
"""

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage
from vectara.core.api_error import ApiError
from vectara.errors import NotFoundError


def _extract_output_text(events):
    output_parts = []
    for event in events:
        event_type = getattr(event, "type", None)
        if event_type and ("output" in str(event_type) or "message" in str(event_type)):
            content = getattr(event, "content", "") or ""
            if content:
                output_parts.append(content)
    return " ".join(output_parts)


@pytest.mark.core
class TestAgentExecution:
    """Agent execution checks."""

    def test_execute_agent_query(self, sdk_client, sdk_shared_agent):
        """Test executing a query against an agent."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
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
            assert len(events) > 0, "Expected events in agent response"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass

    def test_execute_agent_with_context(self, sdk_client, sdk_shared_agent):
        """Test multi-turn conversation with an agent."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            # First turn
            response1 = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Tell me about Vectara agents."}],
                    stream_response=False,
                ),
            )
            assert response1 is not None, "First turn failed"

            # Second turn (follow-up)
            response2 = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "How do I configure them?"}],
                    stream_response=False,
                ),
            )
            assert response2 is not None, "Follow-up turn failed"

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, "Expected events in multi-turn response"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass


@pytest.mark.regression
class TestAgentExecutionEdgeCases:
    """Agent execution edge cases."""

    def test_execute_nonexistent_agent(self, sdk_client):
        """Test executing against a non-existent agent."""
        with pytest.raises((NotFoundError, ApiError)):
            sdk_client.agent_events.create(
                "nonexistent_agent_xyz123",
                "fake_session",
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "test query"}],
                    stream_response=False,
                ),
            )

    def test_agent_handles_special_characters(self, sdk_client, sdk_shared_agent):
        """Test agent handles queries with special characters."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            response = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "What's Vectara's approach to AI & machine-learning?"}],
                    stream_response=False,
                ),
            )
            assert response is not None, "Special character query failed"

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, "Expected events for special character query"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass

    def test_agent_handles_long_query(self, sdk_client, sdk_shared_agent):
        """Test agent handles longer queries."""
        long_query = (
            "I'm trying to understand how Vectara's conversational AI agents work. "
            "Can you explain the process of creating an agent, configuring it with "
            "multiple corpora, and then using it for multi-turn conversations? "
            "I'm particularly interested in how context is maintained across turns."
        )

        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            response = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": long_query}],
                    stream_response=False,
                ),
            )
            assert response is not None, "Long query failed"

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, "Expected events for long query"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
