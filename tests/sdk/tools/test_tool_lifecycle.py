"""
Tool Lifecycle Tests (SDK)

Tests for tool enable/disable operations.
"""

import pytest

from vectara.types import CreateToolRequest_Lambda, UpdateToolRequest_Lambda


@pytest.mark.core
class TestToolLifecycle:
    """Tool lifecycle operations."""

    def test_enable_disable_tool(self, sdk_client, unique_id):
        """Test disabling and re-enabling a tool."""
        tool = sdk_client.tools.create(
            request=CreateToolRequest_Lambda(
                name=f"test_tool_{unique_id}",
                title=f"Test Tool {unique_id}",
                description="A test tool for lifecycle testing",
                code="def process(request): return {'result': 'ok'}",
            ),
        )

        tool_id = getattr(tool, "id", None)
        assert tool_id, "No tool id in response"

        try:
            disabled = sdk_client.tools.update(
                tool_id,
                request=UpdateToolRequest_Lambda(enabled=False),
            )
            assert getattr(disabled, "enabled", None) is False, (
                f"Expected enabled=False, got: {getattr(disabled, 'enabled', None)}"
            )

            enabled = sdk_client.tools.update(
                tool_id,
                request=UpdateToolRequest_Lambda(enabled=True),
            )
            assert getattr(enabled, "enabled", None) is True, (
                f"Expected enabled=True, got: {getattr(enabled, 'enabled', None)}"
            )
        finally:
            try:
                sdk_client.tools.delete(tool_id)
            except Exception:
                pass
