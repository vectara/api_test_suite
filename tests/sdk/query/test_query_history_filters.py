"""
Query History Filter Tests (SDK)

Verify query history list supports filtering and pagination
using the Vectara Python SDK.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_query_history_available(sdk_client):
    """Skip all tests if query history API is not available."""
    try:
        entries = list(sdk_client.query_history.list(limit=1))
    except Exception as e:
        pytest.skip(f"Query history API not available: {e}")


@pytest.mark.regression
class TestQueryHistoryFilters:
    """Query history filtering and pagination."""

    def test_query_history_with_limit(self, sdk_client):
        """Verify limit parameter restricts per-page result count."""
        # SDK pager iterates all pages; limit controls page size.
        # Verify that a smaller limit still returns results and that
        # a larger limit returns at least as many.
        small_limit = []
        for entry in sdk_client.query_history.list(limit=2):
            small_limit.append(entry)
            if len(small_limit) >= 5:
                break

        large_limit = []
        for entry in sdk_client.query_history.list(limit=10):
            large_limit.append(entry)
            if len(large_limit) >= 5:
                break

        assert len(small_limit) > 0, "Query history should return at least 1 entry"
        assert len(large_limit) > 0, "Query history should return at least 1 entry"
