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

    def test_query_history_filter_by_corpus(self, client):
        """Verify corpus_key filter returns only matching entries."""
        full_resp = client.list_query_histories(limit=10)
        entries = full_resp.data.get("queries", [])
        if not entries:
            pytest.skip("No query history entries")

        corpus_keys = {e.get("corpus_key") for e in entries if e.get("corpus_key")}
        if not corpus_keys:
            pytest.skip("No corpus_key in history entries")

        target_key = next(iter(corpus_keys))
        filtered_resp = client.list_query_histories(limit=10, corpus_key=target_key)
        assert filtered_resp.success
        filtered_entries = filtered_resp.data.get("queries", [])
        for entry in filtered_entries:
            assert entry.get("corpus_key") == target_key, \
                f"Filtered entry should have corpus_key={target_key}, got: {entry.get('corpus_key')}"
