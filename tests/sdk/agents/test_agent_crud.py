"""
Agent CRUD Tests (SDK)

Tests for agent create, read, update, delete, and listing operations.
"""

import time

import pytest

from vectara.types import (
    AgentRagConfig,
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
)
from vectara.errors import NotFoundError


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

    def test_create_agent(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Test creating a new agent."""
        agent_name = f"Test Agent {unique_id}"

        agent = sdk_client.agents.create(
            name=agent_name,
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
            description="Test agent created by SDK test suite",
        )

        try:
            assert agent.name == agent_name, f"Expected name {agent_name!r}, got {agent.name!r}"
            assert agent.key is not None, "Agent should have a key"
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass

    def test_create_agent_with_config(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Test creating an agent with custom configuration."""
        agent_name = f"Configured Agent {unique_id}"

        agent = sdk_client.agents.create(
            name=agent_name,
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
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

    def test_get_agent(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Test retrieving agent details."""
        agent = sdk_client.agents.create(
            name=f"Get Test Agent {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
        )

        try:
            retrieved = sdk_client.agents.get(agent.key)

            assert retrieved.key == agent.key, (
                f"Expected agent key {agent.key!r}, got {retrieved.key!r}"
            )
            assert retrieved.name is not None, "Agent should have a name"
        finally:
            sdk_client.agents.delete(agent.key)

    def test_update_agent(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Test updating an agent."""
        agent = sdk_client.agents.create(
            name=f"Update Test Agent {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
            description="Original description",
        )

        try:
            new_description = f"Updated description at {time.time()}"
            updated = sdk_client.agents.update(
                agent.key,
                description=new_description,
            )

            retrieved = sdk_client.agents.get(agent.key)
            assert retrieved.description == new_description, (
                f"Description not persisted: expected {new_description!r}, got {retrieved.description!r}"
            )
        finally:
            sdk_client.agents.delete(agent.key)

    def test_delete_agent(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Test deleting an agent."""
        agent = sdk_client.agents.create(
            name=f"Delete Test Agent {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
        )

        sdk_client.agents.delete(agent.key)

        with pytest.raises(NotFoundError):
            sdk_client.agents.get(agent.key)
