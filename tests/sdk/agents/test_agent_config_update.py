"""
Agent Configuration Update Tests (SDK)

Tests for updating agent description, metadata, and enabled state.
"""

import uuid

import pytest

from vectara.types import (
    AgentRagConfig,
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
)


@pytest.mark.core
class TestAgentConfigUpdate:
    """Agent configuration update operations."""

    def _create_test_agent(self, sdk_client, unique_id):
        """Create a temporary agent for testing updates."""
        agent = sdk_client.agents.create(
            name=f"Config Test Agent {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[],
                ),
                generation=GenerationParameters(),
            ),
            description="Agent for config update tests",
        )
        return agent.key

    def test_update_agent_description(self, sdk_client, unique_id):
        """Test updating agent description and verifying persistence."""
        agent_key = self._create_test_agent(sdk_client, unique_id)
        try:
            new_desc = f"Updated description {unique_id}"
            sdk_client.agents.update(agent_key, description=new_desc)

            retrieved = sdk_client.agents.get(agent_key)
            assert retrieved.description == new_desc
        finally:
            try:
                sdk_client.agents.delete(agent_key)
            except Exception:
                pass

    def test_enable_disable_agent(self, sdk_client, unique_id):
        """Test disabling and re-enabling an agent."""
        agent_key = self._create_test_agent(sdk_client, unique_id)
        try:
            sdk_client.agents.update(agent_key, enabled=False)

            retrieved = sdk_client.agents.get(agent_key)
            assert retrieved.enabled is False, f"Expected disabled, got: {retrieved.enabled}"

            sdk_client.agents.update(agent_key, enabled=True)

            retrieved2 = sdk_client.agents.get(agent_key)
            assert retrieved2.enabled is True
        finally:
            try:
                sdk_client.agents.delete(agent_key)
            except Exception:
                pass
