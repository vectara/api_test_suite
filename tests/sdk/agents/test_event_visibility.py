"""
Agent Event Visibility Tests (SDK)

Tests for hiding and unhiding agent session events, including error handling.
"""

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage
from vectara.core.api_error import ApiError
from vectara.errors import NotFoundError


@pytest.mark.core
class TestEventVisibility:
    """Core tests for hiding and unhiding agent events."""

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

    def test_hide_and_unhide_event(self, sdk_client, sdk_shared_agent):
        """Hide an event, verify excluded from listing, unhide, verify reappears."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            # Send message to generate events
            sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "Hello for hide/unhide test"}],
                    stream_response=False,
                ),
            )

            # List events
            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, "Expected at least one event"

            event_id = getattr(events[0], "id", None)
            assert event_id is not None, "Event should have an id"
            initial_count = len(events)

            # Hide the event
            hidden_event = sdk_client.agent_events.hide(sdk_shared_agent, session_key, event_id)
            assert hidden_event is not None, "Hide should return the event"

            # Verify hidden from default listing
            visible_events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(visible_events) == initial_count - 1, f"Expected {initial_count - 1} visible events after hide, got {len(visible_events)}"
            visible_ids = {getattr(e, "id", None) for e in visible_events}
            assert event_id not in visible_ids, "Hidden event should not appear in default listing"

            # Unhide the event
            unhidden_event = sdk_client.agent_events.unhide(sdk_shared_agent, session_key, event_id)
            assert unhidden_event is not None, "Unhide should return the event"

            # Verify reappears
            after_events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(after_events) == initial_count, f"Expected {initial_count} events after unhide, got {len(after_events)}"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass


@pytest.mark.regression
class TestEventVisibilityErrors:
    """Regression tests for event visibility error handling."""

    def test_list_events_nonexistent_session(self, sdk_client, sdk_shared_agent):
        """Listing events for a nonexistent session should raise an error."""
        with pytest.raises(NotFoundError):
            list(sdk_client.agent_events.list(sdk_shared_agent, "ase_nonexistent"))

    def test_hide_nonexistent_event_returns_404(self, sdk_client, sdk_shared_agent):
        """Hiding a nonexistent event should return NotFoundError."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            with pytest.raises((NotFoundError, ApiError)):
                sdk_client.agent_events.hide(sdk_shared_agent, session_key, "aev_nonexistent")
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
