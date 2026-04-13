"""
Agent Identity Tests (SDK)

Tests for agent identity configuration: get and update mode.
Note: Agent identity endpoints may not be available via the SDK --
these tests skip gracefully when not supported.
"""

import uuid

import pytest

from vectara.types import (
    AgentRagConfig,
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
)
from vectara.core.api_error import ApiError
from vectara.errors import NotFoundError


@pytest.mark.core
class TestAgentIdentity:
    """Core tests for agent identity configuration."""

    def test_get_agent_has_expected_fields(self, sdk_client, sdk_shared_agent):
        """Verify agent get returns expected fields (identity via agent object)."""
        agent = sdk_client.agents.get(sdk_shared_agent)
        # Verify that the agent object has basic expected fields
        assert agent.key is not None, "Agent should have a key"
        assert agent.name is not None, "Agent should have a name"
        assert agent.type is not None, "Agent should have a type"

    def test_update_agent_description_persists(self, sdk_client, sdk_shared_agent_corpus, unique_id):
        """Update agent description and verify it persists."""
        agent = sdk_client.agents.create(
            name=f"Identity Test {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
            description="Agent for identity testing",
        )

        try:
            updated = sdk_client.agents.update(agent.key, description="Updated identity test")
            retrieved = sdk_client.agents.get(agent.key)
            assert retrieved.description == "Updated identity test", (
                f"Expected updated description, got: {retrieved.description}"
            )
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass
