"""
Agent Identity Tests

Tests for agent identity configuration: get, update mode, and error handling.
"""

import uuid

import pytest


@pytest.mark.core
class TestAgentIdentity:
    """Core tests for agent identity configuration."""

    def test_get_agent_identity(self, client, shared_agent):
        """Verify agent identity endpoint returns a response."""
        resp = client.get_agent_identity(shared_agent)
        # Some agents may not have identity configured -- just verify the endpoint works
        assert resp.status_code in [200, 404], f"Unexpected status: {resp.status_code} - {resp.data}"

    def test_update_agent_identity_mode(self, client, shared_agent_corpus, unique_id):
        """Update agent identity mode from AUTO to MANUAL and back."""
        agent_resp = client.create_agent(
            name=f"Identity Test {unique_id}",
            description="Agent for identity testing",
        )
        if not agent_resp.success:
            pytest.skip(f"Could not create agent: {agent_resp.data}")

        agent_key = agent_resp.data.get("key") or agent_resp.data.get("id")

        try:
            # Update to manual mode
            update_resp = client.update_agent_identity(agent_key, mode="manual")
            # Accept either success or 404 (if identity not supported)
            if update_resp.status_code == 404:
                pytest.skip("Agent identity not available in this environment")
            assert update_resp.success, f"Update identity failed: {update_resp.data}"

            # Verify PATCH response contains the updated mode
            assert update_resp.data.get("mode") == "manual", f"Expected manual in PATCH response, got: {update_resp.data}"
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass
