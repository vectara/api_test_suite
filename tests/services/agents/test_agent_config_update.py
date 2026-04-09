"""
Agent Configuration Update Tests

Tests for updating agent model, tools, instructions, metadata, and enabled state.
"""

import uuid

import pytest


@pytest.mark.core
class TestAgentConfigUpdate:
    """Agent configuration update operations."""

    def _create_test_agent(self, client, unique_id):
        """Create a temporary agent for testing updates."""
        name = f"Config Test Agent {unique_id}"
        resp = client.create_agent(name=name, description="Agent for config update tests")
        assert resp.success, f"Create agent failed: {resp.status_code} - {resp.data}"
        agent_id = resp.data.get("id") or resp.data.get("key")
        assert agent_id, f"No agent id in create response: {resp.data}"
        return agent_id

    def test_update_agent_description(self, client, unique_id):
        """Test updating agent description and verifying persistence."""
        agent_id = self._create_test_agent(client, unique_id)
        try:
            new_desc = f"Updated description {unique_id}"
            update_resp = client.update_agent(agent_id, description=new_desc)
            assert update_resp.success, f"Update failed: {update_resp.status_code}"

            get_resp = client.get_agent(agent_id)
            assert get_resp.success
            assert get_resp.data.get("description") == new_desc
        finally:
            try:
                client.delete_agent(agent_id)
            except Exception:
                pass

    def test_update_agent_metadata(self, client, unique_id):
        """Test updating agent metadata."""
        agent_id = self._create_test_agent(client, unique_id)
        try:
            metadata = {"environment": "test", "version": "1.0"}
            update_resp = client.update_agent(agent_id, metadata=metadata)
            assert update_resp.success, f"Update metadata failed: {update_resp.status_code}"

            get_resp = client.get_agent(agent_id)
            assert get_resp.success
            agent_metadata = get_resp.data.get("metadata", {})
            assert agent_metadata.get("environment") == "test", \
                f"Metadata not persisted: {agent_metadata}"
        finally:
            try:
                client.delete_agent(agent_id)
            except Exception:
                pass

    def test_enable_disable_agent(self, client, unique_id):
        """Test disabling and re-enabling an agent."""
        agent_id = self._create_test_agent(client, unique_id)
        try:
            disable_resp = client.update_agent(agent_id, enabled=False)
            assert disable_resp.success, f"Disable failed: {disable_resp.status_code}"

            get_resp = client.get_agent(agent_id)
            assert get_resp.success
            assert get_resp.data.get("enabled") is False, \
                f"Expected disabled, got: {get_resp.data.get('enabled')}"

            enable_resp = client.update_agent(agent_id, enabled=True)
            assert enable_resp.success

            get_resp2 = client.get_agent(agent_id)
            assert get_resp2.data.get("enabled") is True
        finally:
            try:
                client.delete_agent(agent_id)
            except Exception:
                pass
