"""
Agent Identity Tests (SDK)

Tests for agent identity configuration: get and update mode.
Note: Agent identity endpoints may not be available via the SDK --
these tests skip gracefully when not supported.
"""

import pytest
from vectara.core.api_error import ApiError
from vectara.errors import NotFoundError

from .conftest import create_agent


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
            assert retrieved.description == "Updated identity test", f"Expected updated description, got: {retrieved.description}"
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)

    def test_get_agent_identity(self, sdk_client, sdk_shared_agent):
        """Verify agent identity endpoint returns a response with expected fields."""
        try:
            identity = sdk_client.agents.get_identity(sdk_shared_agent)
            assert identity is not None, "Identity should not be None"
            assert hasattr(identity, "mode"), f"Identity should have 'mode' field: {identity}"
            assert identity.mode in ("auto", "manual"), f"Mode should be auto or manual, got: {identity.mode}"
        except (NotFoundError, ApiError) as e:
            # Identity endpoint may not be available in all environments
            if hasattr(e, "status_code") and e.status_code == 404:
                pytest.skip("Agent identity not available in this environment")
            raise

    def test_update_agent_identity_mode(self, sdk_client, sdk_shared_agent_corpus):
        """Update agent identity mode from auto to manual and back."""
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="SDK Identity Test",
            description="Agent for identity mode testing",
        )

        try:
            # Get current identity to determine initial mode
            try:
                identity = sdk_client.agents.get_identity(agent.key)
            except (NotFoundError, ApiError) as e:
                if hasattr(e, "status_code") and e.status_code == 404:
                    pytest.skip("Agent identity not available in this environment")
                raise

            original_mode = identity.mode

            # Update to manual mode
            updated = sdk_client.agents.update_identity(agent.key, mode="manual")
            # Verify the PATCH response contains updated mode (matches HTTP test behavior)
            assert updated.mode == "manual", f"Expected manual mode in PATCH response, got: {updated.mode}"

            # Restore original mode
            sdk_client.agents.update_identity(agent.key, mode=original_mode)
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass
