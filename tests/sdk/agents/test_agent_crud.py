"""
Agent CRUD Tests (SDK)

Tests for agent create, read, update, delete, and listing operations.
"""

import time

import pytest

from vectara.errors import NotFoundError

from .conftest import create_agent


@pytest.mark.sanity
class TestAgentList:
    """Agent listing checks."""

    def test_list_agents(self, sdk_client):
        """Test listing all agents."""
        pager = sdk_client.agents.list(limit=10)
        agents = list(pager)

        assert isinstance(agents, list), f"Expected list, got {type(agents)}"


@pytest.mark.core
class TestAgentCrud:
    """Agent create, get, update, and delete checks."""

    def test_create_agent(self, sdk_client, sdk_shared_agent_corpus):
        """Test creating a new agent."""
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="Create Test Agent",
            description="Test agent created by SDK test suite",
        )

        try:
            assert agent.name is not None, "Agent should have a name"
            assert agent.key is not None, "Agent should have a key"
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass

    def test_create_agent_with_config(self, sdk_client, sdk_shared_agent_corpus):
        """Test creating an agent with custom configuration."""
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="Configured Agent",
            description="Agent with custom settings",
        )

        try:
            assert agent.description == "Agent with custom settings", (
                f"Expected description 'Agent with custom settings', got {agent.description!r}"
            )
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass

    def test_get_agent(self, sdk_client, sdk_shared_agent):
        """Test retrieving agent details."""
        retrieved = sdk_client.agents.get(sdk_shared_agent)

        assert retrieved.key == sdk_shared_agent, (
            f"Expected agent key {sdk_shared_agent!r}, got {retrieved.key!r}"
        )
        assert retrieved.name is not None, "Agent should have a name"

    def test_update_agent(self, sdk_client, sdk_shared_agent):
        """Test updating an agent."""
        # Save original description to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_description = original.description

        try:
            new_description = f"Updated description at {time.time()}"
            sdk_client.agents.update(
                sdk_shared_agent,
                description=new_description,
            )

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.description == new_description, (
                f"Description not persisted: expected {new_description!r}, got {retrieved.description!r}"
            )
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)

    def test_delete_agent(self, sdk_client, sdk_shared_agent_corpus):
        """Test deleting an agent."""
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="Delete Test Agent",
        )

        sdk_client.agents.delete(agent.key)

        with pytest.raises(NotFoundError):
            sdk_client.agents.get(agent.key)
