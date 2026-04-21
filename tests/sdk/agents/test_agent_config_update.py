"""
Agent Configuration Update Tests (SDK)

Tests for updating agent description, metadata, and enabled state.
"""

import uuid

import pytest


@pytest.mark.core
@pytest.mark.serial
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

    def test_update_agent_metadata(self, sdk_client, sdk_shared_agent):
        """Test updating agent metadata dict, verify persistence, restore original."""
        original = sdk_client.agents.get(sdk_shared_agent)
        original_metadata = getattr(original, "metadata", None)

        try:
            metadata = {"environment": "test", "version": "1.0"}
            sdk_client.agents.update(sdk_shared_agent, metadata=metadata)

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            agent_metadata = getattr(retrieved, "metadata", {}) or {}
            assert agent_metadata.get("environment") == "test", f"Metadata not persisted: {agent_metadata}"
            assert agent_metadata.get("version") == "1.0", f"Metadata version not persisted: {agent_metadata}"
        finally:
            # Restore original metadata
            if original_metadata is not None:
                sdk_client.agents.update(sdk_shared_agent, metadata=original_metadata)
            else:
                try:
                    sdk_client.agents.update(sdk_shared_agent, metadata={})
                except Exception:
                    pass

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
