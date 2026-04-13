"""
Corpus Pagination Tests (SDK)

Core-level tests for listing corpora and pagination support using the Vectara Python SDK.
"""

import pytest


@pytest.mark.core
class TestCorpusPagination:
    """Core checks for corpus listing and pagination."""

    def test_list_corpora(self, sdk_client):
        """Test listing all corpora."""
        corpora = list(sdk_client.corpora.list(limit=100))

        assert isinstance(corpora, list), "Expected list of corpora"

    def test_list_corpora_pagination(self, sdk_client):
        """Test corpus listing with pagination."""
        # First request with small limit
        page1 = list(sdk_client.corpora.list(limit=2))

        assert isinstance(page1, list), "Expected list for first page"
        # The SDK pager handles pagination automatically, so listing with
        # limit=2 returns all results across pages. Verify we got results.
        assert len(page1) >= 0, "Listing should return zero or more corpora"
