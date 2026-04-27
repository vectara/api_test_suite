"""
Agent Session Advanced Tests (SDK)

Core tests for agent session creation with metadata and message sending.
"""

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage


@pytest.mark.core
class TestAgentSessionAdvanced:

    def test_create_session_with_metadata(self, sdk_client, sdk_shared_agent):
        session = sdk_client.agent_sessions.create(
            sdk_shared_agent,
            metadata={"topic": "astronomy", "test": True},
        )
        session_key = session.key

        # Verify session exists and metadata returned
        retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session_key)
        session_metadata = getattr(retrieved, "metadata", {}) or {}
        assert session_metadata.get("topic") == "astronomy", f"Expected metadata topic=astronomy, got: {session_metadata}"

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
        except Exception:
            pass

    def test_send_message_to_session(self, sdk_client, sdk_shared_agent):
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            # Send message via agent_events with explicit session
            response = sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Tell me about vector search"}],
                    stream_response=False,
                ),
            )
            assert response is not None, "Send message failed"

            # Verify response has events with content
            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, "Expected events in response"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
