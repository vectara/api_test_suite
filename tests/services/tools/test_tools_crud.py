"""
Tools CRUD Tests

Core tests for tool creation, update, and deletion.
"""

import pytest


@pytest.mark.core
class TestToolsList:
    def test_list_tools(self, client):
        response = client.list_tools(limit=10)
        assert response.success, f"List tools failed: {response.status_code} - {response.data}"
        assert "tools" in response.data, f"Expected 'tools' key: {response.data.keys()}"


@pytest.mark.core
class TestToolsCrud:
    def test_create_update_delete_tool(self, client, unique_id):
        # Create
        response = client.create_tool(
            name=f"test_tool_{unique_id}",
            title=f"Test Tool {unique_id}",
            description="A test lambda tool",
            code="def process(value: str) -> dict:\n    return {'result': value}",
        )
        assert response.success, f"Create tool failed: {response.status_code} - {response.data}"

        tool_id = response.data.get("id")
        assert tool_id, f"No tool ID in response: {response.data}"

        # Update
        update_resp = client.update_tool(tool_id, type="lambda", description="Updated description")
        assert update_resp.success, f"Update tool failed: {update_resp.data}"

        # Verify update took effect
        updated_desc = update_resp.data.get("description", "")
        assert updated_desc == "Updated description", f"Description not updated: {updated_desc}"

        # Delete
        del_resp = client.delete_tool(tool_id)
        assert del_resp.success, f"Delete tool failed: {del_resp.data}"
