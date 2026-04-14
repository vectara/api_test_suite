"""
Agent Identity Tests (SDK)

Tests for agent identity configuration: get and update mode.
Note: Agent identity endpoints may not be available via the SDK --
these tests skip gracefully when not supported.
"""

import pytest


@pytest.mark.core
class TestAgentIdentity:
    """Core tests for agent identity configuration."""

    def test_get_agent_has_expected_fields(self, sdk_client, sdk_shared_agent):
        """Verify agent get returns expected fields (identity via agent object)."""
        agent = sdk_client.agents.get(sdk_shared_agent)
        # Verify that the agent object has basic expected fields
        assert agent.key is not None, "Agent should have a key"
        assert agent.name is not None, "Agent should have a name"
        assert agent.model is not None, "Agent should have a model"

    def test_update_agent_description_persists(self, sdk_client, sdk_shared_agent):
        """Update agent description and verify it persists."""
        # Save original description to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_description = original.description

        try:
            sdk_client.agents.update(sdk_shared_agent, description="Updated identity test")
            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.description == "Updated identity test", (
                f"Expected updated description, got: {retrieved.description}"
            )
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)
