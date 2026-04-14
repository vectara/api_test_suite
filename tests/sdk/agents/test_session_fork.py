"""
Agent Session Fork Tests (SDK)

Tests for forking agent sessions, including event copying and error handling.
"""

import pytest

from vectara.errors import NotFoundError, BadRequestError
from vectara.core.api_error import ApiError
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage


@pytest.mark.core
class TestSessionFork:
    """Core tests for forking agent sessions."""

    def test_fork_session_copies_events(self, sdk_client, sdk_shared_agent, unique_id):
        """Fork a session and verify events are copied."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        # Send message to generate events
        sdk_client.agent_events.create(
            sdk_shared_agent,
            session_key,
            request=CreateAgentEventsRequestBody_InputMessage(
                messages=[{"type": "text", "content": "Hello"}],
                stream_response=False,
            ),
        )

        # List events from source session
        source_events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))

        # Fork session
        forked = sdk_client.agent_sessions.create(
            sdk_shared_agent,
            metadata={"forked": True},
            from_session={"session_key": session_key},
        )
        forked_key = forked.key

        # Verify forked session has events
        forked_events = list(sdk_client.agent_events.list(sdk_shared_agent, forked_key))
        assert len(forked_events) == len(source_events), (
            f"Expected {len(source_events)} events, got {len(forked_events)}"
        )

        # Event IDs should be different
        source_ids = {getattr(e, "id", None) for e in source_events}
        forked_ids = {getattr(e, "id", None) for e in forked_events}
        assert source_ids.isdisjoint(forked_ids), "Forked events should have new IDs"

        # Event types should match between source and fork
        source_types = [getattr(e, "type", None) for e in source_events]
        forked_types = [getattr(e, "type", None) for e in forked_events]
        assert source_types == forked_types, (
            f"Event types mismatch: source={source_types}, forked={forked_types}"
        )

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, forked_key)
            sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
        except Exception:
            pass

    def test_fork_empty_session(self, sdk_client, sdk_shared_agent):
        """Fork a session with no events."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        forked = sdk_client.agent_sessions.create(
            sdk_shared_agent,
            from_session={"session_key": session_key},
        )
        forked_key = forked.key

        forked_events = list(sdk_client.agent_events.list(sdk_shared_agent, forked_key))
        assert len(forked_events) == 0

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, forked_key)
            sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
        except Exception:
            pass


@pytest.mark.regression
class TestSessionForkErrors:
    """Regression tests for session fork error handling."""

    def test_fork_nonexistent_session_fails(self, sdk_client, sdk_shared_agent):
        """Fork with invalid source session should fail."""
        with pytest.raises((NotFoundError, BadRequestError, ApiError)):
            sdk_client.agent_sessions.create(
                sdk_shared_agent,
                from_session={"session_key": "ses_nonexistent_xyz"},
            )

    def test_fork_mutually_exclusive_fields_fails(self, sdk_client, sdk_shared_agent):
        """Both include_up_to_event_id and compact_up_to_event_id should fail."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            with pytest.raises((BadRequestError, ApiError)):
                sdk_client.agent_sessions.create(
                    sdk_shared_agent,
                    from_session={
                        "session_key": session_key,
                        "include_up_to_event_id": "aev_fake",
                        "compact_up_to_event_id": "aev_fake",
                    },
                )
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
