"""
Agent Session Tests

Core-level tests for agent session management.
"""

import pytest


@pytest.mark.core
class TestAgentSessions:
    """Core checks for agent session operations."""

    def test_list_agent_sessions(self, client, shared_agent):
        """Test listing sessions for an agent."""
        # First execute a query to create a session
        client.execute_agent(
            agent_id=shared_agent,
            query_text="Create a session",
        )

        # List sessions
        response = client.list_agent_sessions(shared_agent, limit=10)

        assert response.success, f"List sessions failed: {response.status_code} - {response.data}"
