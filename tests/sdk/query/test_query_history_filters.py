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
        """Verify limit parameter restricts first-page result count."""
        # Use pager.items to get just the first page (respects limit)
        pager = sdk_client.query_history.list(limit=10)
        full_count = len(pager.items or [])
        if full_count < 3:
            pytest.skip(f"Need at least 3 history entries for limit test, have {full_count}")

        limited_pager = sdk_client.query_history.list(limit=2)
        limited_items = limited_pager.items or []
        assert len(limited_items) <= 2, f"Limit=2 should return at most 2 entries, got {len(limited_items)}"
