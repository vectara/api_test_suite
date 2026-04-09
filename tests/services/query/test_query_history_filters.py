"""
Query History Filter Tests

Verify query history list supports filtering and pagination.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_query_history_available(client):
    """Skip all tests if query history API is not available."""
    resp = client.list_query_histories(limit=1)
    if not resp.success:
        pytest.skip(f"Query history API not available: {resp.status_code}")


@pytest.mark.regression
class TestQueryHistoryFilters:
    """Query history filtering and pagination."""

    def test_query_history_with_limit(self, client):
        """Verify limit parameter restricts result count."""
        full_resp = client.list_query_histories(limit=10)
        assert full_resp.success
        full_count = len(full_resp.data.get("queries", []))
        if full_count < 3:
            pytest.skip(f"Need at least 3 history entries for limit test, have {full_count}")

        limited_resp = client.list_query_histories(limit=2)
        assert limited_resp.success
        limited_entries = limited_resp.data.get("queries", [])
        assert len(limited_entries) <= 2, \
            f"Limit=2 should return at most 2 entries, got {len(limited_entries)}"

