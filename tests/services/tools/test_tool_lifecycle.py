"""
Tool Lifecycle Tests

Tests for tool enable/disable operations.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestToolLifecycle:
    """Tool lifecycle operations."""

    def test_enable_disable_tool(self, client, unique_id):
        """Test disabling and re-enabling a tool."""
        tool_name = f"test_tool_{unique_id}"
        create_resp = client.create_tool(
            name=tool_name,
            title=f"Test Tool {unique_id}",
            description="A test tool for lifecycle testing",
            code="def process(request): return {'result': 'ok'}",
        )
        if not create_resp.success:
            pytest.skip(f"Could not create tool: {create_resp.data}")

        tool_id = create_resp.data.get("id") or create_resp.data.get("name")
        try:
            disable_resp = client.update_tool(tool_id, type="lambda", enabled=False)
            assert disable_resp.success, f"Disable tool failed: {disable_resp.status_code} - {disable_resp.data}"
            assert disable_resp.data.get("enabled") is False, \
                f"Expected enabled=False, got: {disable_resp.data.get('enabled')}"

            enable_resp = client.update_tool(tool_id, type="lambda", enabled=True)
            assert enable_resp.success, f"Enable tool failed: {enable_resp.status_code} - {enable_resp.data}"
            assert enable_resp.data.get("enabled") is True, \
                f"Expected enabled=True, got: {enable_resp.data.get('enabled')}"
        finally:
            if tool_id:
                try:
                    client.delete_tool(tool_id)
                except Exception:
                    pass
