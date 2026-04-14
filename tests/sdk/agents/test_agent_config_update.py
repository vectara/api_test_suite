"""
Agent Configuration Update Tests (SDK)

Tests for updating agent description, metadata, and enabled state.
"""

import uuid

import pytest


@pytest.mark.core
class TestAgentConfigUpdate:
    """Agent configuration update operations."""

    def test_update_agent_description(self, sdk_client, sdk_shared_agent):
        """Test updating agent description and verifying persistence."""
        # Save original description to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_description = original.description

        try:
            new_desc = f"Updated description {uuid.uuid4().hex[:8]}"
            sdk_client.agents.update(sdk_shared_agent, description=new_desc)

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.description == new_desc
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)

    def test_enable_disable_agent(self, sdk_client, sdk_shared_agent):
        """Test disabling and re-enabling an agent."""
        # Save original enabled state to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_enabled = original.enabled

        try:
            sdk_client.agents.update(sdk_shared_agent, enabled=False)

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.enabled is False, f"Expected disabled, got: {retrieved.enabled}"

            sdk_client.agents.update(sdk_shared_agent, enabled=True)

            retrieved2 = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved2.enabled is True
        finally:
            sdk_client.agents.update(sdk_shared_agent, enabled=original_enabled)
