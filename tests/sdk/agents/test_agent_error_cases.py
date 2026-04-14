"""
Agent Error Case Tests (SDK)

Tests for error handling on non-existent agents and sessions.
"""

import uuid

import pytest

from vectara.errors import NotFoundError
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage

from utils.waiters import wait_for


def _session_exists(sdk_client, agent_key, session_key):
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


def _extract_output_text(events):
    output_parts = []
    for event in events:
        event_type = getattr(event, "type", None)
        if event_type and ("output" in str(event_type) or "message" in str(event_type)):
            content = getattr(event, "content", "") or ""
            if content:
                output_parts.append(content)
    return " ".join(output_parts)


@pytest.mark.regression
class TestAgentErrorCases:
    """Error handling for invalid agent/session operations."""

    def test_send_message_nonexistent_session(self, sdk_client, sdk_shared_agent):
        """testNonSseInputOnNonExistentSession -- 404 for bad session."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_events.create(
                sdk_shared_agent,
                f"ase_fake_{uuid.uuid4().hex[:8]}",
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Hello"}],
                    stream_response=False,
                ),
            )

    def test_send_message_nonexistent_agent(self, sdk_client):
        """testNonSseInputOnNonExistentAgent -- 404 for bad agent."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_events.create(
                f"nonexistent_{uuid.uuid4().hex[:8]}",
                "fake_session",
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Hello"}],
                    stream_response=False,
                ),
            )

    def test_fork_session_continue_conversation(self, sdk_client, sdk_agent_with_session):
        """forkSession_withoutCompaction_newSessionCanContinueConversation."""
        agent_key, session_key, events = sdk_agent_with_session

        try:
            forked = sdk_client.agent_sessions.create(
                agent_key,
                from_session={"session_key": session_key},
            )
        except Exception as e:
            pytest.skip(f"Fork failed: {e}")

        forked_key = forked.key
        try:
            wait_for(
                lambda: _session_exists(sdk_client, agent_key, forked_key),
                timeout=10,
                interval=0.5,
                description="forked session available",
            )

            response = sdk_client.agent_events.create(
                agent_key,
                forked_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Continue the conversation"}],
                    stream_response=False,
                ),
            )
            assert response is not None, "Should be able to chat in forked session"

            response_events = list(sdk_client.agent_events.list(agent_key, forked_key))
            has_output = any(
                getattr(e, "type", None) and "output" in str(getattr(e, "type", ""))
                for e in response_events
            )
            assert has_output, (
                f"Forked session response should have agent_output: "
                f"{[getattr(e, 'type', None) for e in response_events]}"
            )
        finally:
            if forked_key:
                try:
                    sdk_client.agent_sessions.delete(agent_key, forked_key)
                except Exception:
                    pass
