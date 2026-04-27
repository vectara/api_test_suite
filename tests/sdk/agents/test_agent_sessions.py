"""
Agent Session Tests (SDK)

Core-level tests for agent session management.
"""

import pytest


@pytest.mark.core
class TestAgentSessions:
    """Core checks for agent session operations."""

    def test_list_agent_sessions(self, sdk_client, sdk_shared_agent):
        """Test listing sessions for an agent."""
        # First create a session to ensure there is at least one
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            # List sessions
            pager = sdk_client.agent_sessions.list(sdk_shared_agent, limit=10)
            sessions = list(pager)

            assert isinstance(sessions, list), f"Expected list, got {type(sessions)}"
            assert len(sessions) > 0, "Expected at least one session after creating one"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass
