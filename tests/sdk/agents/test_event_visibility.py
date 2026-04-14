"""
Agent Event Visibility Tests (SDK)

Tests for listing agent session events and verifying event presence.
Note: Hide/unhide event operations may not be directly exposed via the SDK.
These tests focus on event listing and presence verification.
"""

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage


@pytest.mark.core
class TestEventVisibility:
    """Core tests for agent event listing."""

    def test_events_present_after_message(self, sdk_client, sdk_shared_agent):
        """Send a message and verify events are listed."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        # Send message to generate events
        sdk_client.agent_events.create(
            sdk_shared_agent,
            session_key,
            request=CreateAgentEventsRequestBody_InputMessage(
                messages=[{"type": "text", "content": "Hello for visibility test"}],
                stream_response=False,
            ),
        )

        # List events
        events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
        assert len(events) > 0, "Expected at least one event"

        # Verify events have type attributes
        for event in events:
            assert getattr(event, "type", None) is not None, f"Event should have a type: {event}"

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
        except Exception:
            pass


@pytest.mark.regression
class TestEventVisibilityErrors:
    """Regression tests for event visibility error handling."""

    def test_list_events_nonexistent_session(self, sdk_client, sdk_shared_agent):
        """Listing events for a nonexistent session should raise an error."""
        from vectara.errors import NotFoundError

        with pytest.raises(NotFoundError):
            list(sdk_client.agent_events.list(sdk_shared_agent, "ase_nonexistent"))
