"""
Tools CRUD Tests (SDK)

Core tests for tool listing, creation, update, and deletion.
"""

import pytest

from vectara.types import CreateLambdaToolRequest, UpdateLambdaToolRequest


@pytest.mark.core
class TestToolsList:
    def test_list_tools(self, sdk_client):
        pager = sdk_client.tools.list(limit=10)
        tools = list(pager)
        assert isinstance(tools, list), f"Expected list, got {type(tools)}"


@pytest.mark.core
class TestToolsCrud:
    def test_create_update_delete_tool(self, sdk_client, unique_id):
        # Create
        tool = sdk_client.tools.create(
            request=CreateLambdaToolRequest(
                name=f"test_tool_{unique_id}",
                title=f"Test Tool {unique_id}",
                description="A test lambda tool",
                code="def process(value: str) -> dict:\n    return {'result': value}",
            ),
        )

        tool_name = getattr(tool, "name", None) or getattr(tool, "id", None)
        assert tool_name, f"No tool name/id in response"

        # Update
        updated = sdk_client.tools.update(
            tool_name,
            request=UpdateLambdaToolRequest(
                description="Updated description",
            ),
        )

        updated_desc = getattr(updated, "description", "")
        assert updated_desc == "Updated description", f"Description not updated: {updated_desc}"

        # Delete
        sdk_client.tools.delete(tool_name)
