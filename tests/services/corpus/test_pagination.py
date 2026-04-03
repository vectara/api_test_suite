"""
Corpus Pagination Tests

Core-level tests for listing corpora and pagination support.
"""

import pytest


@pytest.mark.core
class TestCorpusPagination:
    """Core checks for corpus listing and pagination."""

    def test_list_corpora(self, client):
        """Test listing all corpora."""
        response = client.list_corpora(limit=100)

        assert response.success, f"List corpora failed: {response.status_code} - {response.data}"

        # Response should contain corpora list
        data = response.data
        assert "corpora" in data or isinstance(data, list), "Expected corpora in response"

    def test_list_corpora_pagination(self, client):
        """Test corpus listing with pagination."""
        # First request with small limit
        response1 = client.list_corpora(limit=2)

        assert response1.success, f"Paginated list failed: {response1.status_code}"

        # If there's a next page, test pagination
        if response1.data.get("metadata", {}).get("page_key"):
            page_key = response1.data["metadata"]["page_key"]
            response2 = client.list_corpora(limit=2, page_key=page_key)

            assert response2.success, f"Second page request failed: {response2.status_code}"
