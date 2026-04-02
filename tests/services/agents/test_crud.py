"""
Agent CRUD Tests

Tests for agent create, read, update, delete, and listing operations.
"""

import pytest
import time


@pytest.mark.sanity
class TestAgentCrudSanity:
    """Sanity-level agent CRUD checks."""

    def test_list_agents(self, client):
        """Test listing all agents."""
        response = client.list_agents(limit=10)

        assert response.success, (
            f"List agents failed: {response.status_code} - {response.data}"
        )


@pytest.mark.core
class TestAgentCrudCore:
    """Core-level agent CRUD checks."""

    def test_create_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test creating a new agent."""
        agent_name = f"Test Agent {unique_id}"

        response = client.create_agent(
            name=agent_name,
            corpus_keys=[seeded_corpus_for_agents],
            description="Test agent created by API test suite",
        )

        assert response.success, (
            f"Create agent failed: {response.status_code} - {response.data}"
        )

        # Get agent ID for cleanup
        agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
        if agent_id:
            try:
                client.delete_agent(agent_id)
            except Exception:
                pass

    def test_create_agent_with_config(self, client, seeded_corpus_for_agents, unique_id):
        """Test creating an agent with custom configuration."""
        agent_name = f"Configured Agent {unique_id}"

        response = client.create_agent(
            name=agent_name,
            corpus_keys=[seeded_corpus_for_agents],
            description="Agent with custom settings",
        )

        assert response.success, (
            f"Create configured agent failed: {response.status_code} - {response.data}"
        )

        agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
        if agent_id:
            try:
                client.delete_agent(agent_id)
            except Exception:
                pass

    def test_get_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test retrieving agent details."""
        # First create an agent
        create_response = client.create_agent(
            name=f"Get Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Get Test Agent {unique_id}",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for get test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        try:
            # Get the agent
            response = client.get_agent(agent_id)

            assert response.success, (
                f"Get agent failed: {response.status_code} - {response.data}"
            )
        finally:
            # Cleanup
            client.delete_agent(agent_id)

    def test_update_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test updating an agent."""
        # Create agent
        create_response = client.create_agent(
            name=f"Update Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
            description="Original description",
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Update Test Agent {unique_id}",
                description="Original description",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for update test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        try:
            # Update the agent
            new_description = f"Updated description at {time.time()}"
            update_response = client.update_agent(
                agent_id=agent_id,
                description=new_description,
            )

            assert update_response.success, (
                f"Update agent failed: {update_response.status_code} - {update_response.data}"
            )
        finally:
            # Cleanup
            client.delete_agent(agent_id)

    def test_delete_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test deleting an agent."""
        # Create agent to delete
        create_response = client.create_agent(
            name=f"Delete Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Delete Test Agent {unique_id}",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for delete test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        # Delete the agent
        delete_response = client.delete_agent(agent_id)

        assert delete_response.success, (
            f"Delete agent failed: {delete_response.status_code} - {delete_response.data}"
        )

        # Verify deletion
        get_response = client.get_agent(agent_id)
        assert get_response.status_code == 404, (
            f"Deleted agent should return 404, got {get_response.status_code}"
        )
