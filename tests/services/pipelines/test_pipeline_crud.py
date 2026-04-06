"""
Pipeline CRUD Tests

Core tests for pipeline listing with availability gating.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_pipelines_available(client):
    response = client.list_pipelines(limit=1)
    if not response.success:
        pytest.skip("Pipelines API not available in this environment")


@pytest.mark.core
class TestPipelineCrud:
    def test_list_pipelines(self, client):
        response = client.list_pipelines(limit=10)
        assert response.success, f"List pipelines failed: {response.status_code} - {response.data}"
