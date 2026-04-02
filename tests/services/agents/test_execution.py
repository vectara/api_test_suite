"""
Agent Execution Tests

Tests for executing queries against agents, multi-turn conversations,
response time, and edge cases.
"""

import pytest


@pytest.mark.core
class TestAgentExecutionCore:
    """Core-level agent execution checks."""

    def test_execute_agent_query(self, client, shared_agent):
        """Test executing a query against an agent."""
        response = client.execute_agent(
            agent_id=shared_agent,
            query_text="What is Vectara?",
        )

        assert response.success, (
            f"Agent execution failed: {response.status_code} - {response.data}"
        )

    def test_execute_agent_with_context(self, client, shared_agent):
        """Test multi-turn conversation with an agent."""
        # First turn
        response1 = client.execute_agent(
            agent_id=shared_agent,
            query_text="Tell me about Vectara agents.",
        )

        assert response1.success, (
            f"First turn failed: {response1.status_code} - {response1.data}"
        )

        # Get session ID if available for follow-up
        session_id = response1.data.get("session_id")

        # Second turn (follow-up)
        response2 = client.execute_agent(
            agent_id=shared_agent,
            query_text="How do I configure them?",
            session_id=session_id,
        )

        assert response2.success, (
            f"Follow-up turn failed: {response2.status_code} - {response2.data}"
        )

    def test_execute_agent_response_time(self, client, shared_agent):
        """Test that agent execution completes in acceptable time."""
        response = client.execute_agent(
            agent_id=shared_agent,
            query_text="What is semantic search?",
        )

        assert response.success, f"Agent execution failed: {response.status_code}"

        # Agent responses involve LLM generation, allow more time
        assert response.elapsed_ms < 60000, (
            f"Agent execution took too long: {response.elapsed_ms:.1f}ms"
        )


@pytest.mark.regression
class TestAgentExecutionRegression:
    """Regression-level agent execution edge cases."""

    def test_execute_nonexistent_agent(self, client):
        """Test executing against a non-existent agent."""
        response = client.execute_agent(
            agent_id="nonexistent_agent_xyz123",
            query_text="test query",
        )

        assert not response.success, "Execution against non-existent agent should fail"
        assert response.status_code in [400, 404], (
            f"Expected 400 or 404, got {response.status_code}"
        )

    def test_agent_handles_special_characters(self, client, shared_agent):
        """Test agent handles queries with special characters."""
        response = client.execute_agent(
            agent_id=shared_agent,
            query_text="What's Vectara's approach to AI & machine-learning?",
        )

        assert response.success, (
            f"Special character query failed: {response.status_code}"
        )

    def test_agent_handles_long_query(self, client, shared_agent):
        """Test agent handles longer queries."""
        long_query = (
            "I'm trying to understand how Vectara's conversational AI agents work. "
            "Can you explain the process of creating an agent, configuring it with "
            "multiple corpora, and then using it for multi-turn conversations? "
            "I'm particularly interested in how context is maintained across turns."
        )

        response = client.execute_agent(
            agent_id=shared_agent,
            query_text=long_query,
        )

        assert response.success, (
            f"Long query failed: {response.status_code}"
        )
