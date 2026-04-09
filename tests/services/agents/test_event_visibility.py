"""
Agent Event Visibility Tests

Tests for hiding and unhiding agent session events, including error handling.
"""

import pytest


@pytest.mark.core
class TestEventVisibility:
    """Core tests for hiding and unhiding agent events."""

    def test_hide_and_unhide_event(self, client, shared_agent):
        """Hide an event, verify excluded from listing, unhide, verify reappears."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        # Send message to generate events
        client.execute_agent(agent_id=shared_agent, query_text="Hello for visibility test", session_id=session_key)

        # List events
        events_resp = client.list_session_events(shared_agent, session_key)
        assert events_resp.success
        events = events_resp.data.get("events", [])
        assert len(events) > 0, "Expected at least one event"

        event_id = events[0].get("id")
        initial_count = len(events)

        # Hide
        hide_resp = client.hide_event(shared_agent, session_key, event_id)
        assert hide_resp.success, f"Hide failed: {hide_resp.data}"

        # Verify hidden from default listing
        visible_resp = client.list_session_events(shared_agent, session_key)
        visible_events = visible_resp.data.get("events", [])
        assert len(visible_events) == initial_count - 1
        assert all(e.get("id") != event_id for e in visible_events)

        # Unhide
        unhide_resp = client.unhide_event(shared_agent, session_key, event_id)
        assert unhide_resp.success, f"Unhide failed: {unhide_resp.data}"

        # Verify reappears
        after_resp = client.list_session_events(shared_agent, session_key)
        after_events = after_resp.data.get("events", [])
        assert len(after_events) == initial_count

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass


@pytest.mark.regression
class TestEventVisibilityErrors:
    """Regression tests for event visibility error handling."""

    def test_hide_nonexistent_event_returns_404(self, client, shared_agent):
        """Hiding a nonexistent event should return 404."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip("Could not create session")
        session_key = session_resp.data.get("key")

        resp = client.hide_event(shared_agent, session_key, "aev_nonexistent")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass
