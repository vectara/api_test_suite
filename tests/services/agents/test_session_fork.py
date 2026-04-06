"""
Agent Session Fork Tests

Tests for forking agent sessions, including event copying and error handling.
"""

import pytest


@pytest.mark.core
class TestSessionFork:
    """Core tests for forking agent sessions."""

    def test_fork_session_copies_events(self, client, shared_agent, unique_id):
        """Fork a session and verify events are copied with new IDs."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        # Send message to generate events
        client.execute_agent(agent_id=shared_agent, query_text="Hello", session_id=session_key)

        # List events from source session
        events_resp = client.list_session_events(shared_agent, session_key)
        assert events_resp.success
        source_events = events_resp.data.get("events", [])

        # Fork session
        fork_resp = client.create_agent_session(
            shared_agent,
            metadata={"forked": True},
            from_session={"session_key": session_key},
        )
        assert fork_resp.success, f"Fork failed: {fork_resp.status_code} - {fork_resp.data}"
        forked_key = fork_resp.data.get("key")

        # Verify forked session has events
        forked_events_resp = client.list_session_events(shared_agent, forked_key)
        assert forked_events_resp.success
        forked_events = forked_events_resp.data.get("events", [])
        assert len(forked_events) == len(source_events), f"Expected {len(source_events)} events, got {len(forked_events)}"

        # Event IDs should be different
        source_ids = {e.get("id") for e in source_events}
        forked_ids = {e.get("id") for e in forked_events}
        assert source_ids.isdisjoint(forked_ids), "Forked events should have new IDs"

        try:
            client.delete_agent_session(shared_agent, forked_key)
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass

    def test_fork_empty_session(self, client, shared_agent):
        """Fork a session with no events."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        fork_resp = client.create_agent_session(
            shared_agent,
            from_session={"session_key": session_key},
        )
        assert fork_resp.success, f"Fork empty session failed: {fork_resp.data}"
        forked_key = fork_resp.data.get("key")

        forked_events = client.list_session_events(shared_agent, forked_key)
        assert forked_events.success
        assert len(forked_events.data.get("events", [])) == 0

        try:
            client.delete_agent_session(shared_agent, forked_key)
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass


@pytest.mark.regression
class TestSessionForkErrors:
    """Regression tests for session fork error handling."""

    def test_fork_nonexistent_session_fails(self, client, shared_agent):
        """Fork with invalid source session should fail."""
        resp = client.create_agent_session(
            shared_agent,
            from_session={"session_key": "ses_nonexistent_xyz"},
        )
        assert resp.status_code >= 400, f"Expected error, got {resp.status_code}"

    def test_fork_mutually_exclusive_fields_fails(self, client, shared_agent):
        """Both include_up_to_event_id and compact_up_to_event_id should fail."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip("Could not create session")
        session_key = session_resp.data.get("key")

        resp = client.create_agent_session(
            shared_agent,
            from_session={
                "session_key": session_key,
                "include_up_to_event_id": "aev_fake",
                "compact_up_to_event_id": "aev_fake",
            },
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass
