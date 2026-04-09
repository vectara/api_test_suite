"""
Query History Tests

Verify that queries are recorded and retrievable via the query history API.
"""

import pytest
from utils.waiters import wait_for


@pytest.fixture(scope="module", autouse=True)
def check_query_history_available(client):
    """Skip all tests if query history API is not available."""
    resp = client.list_query_histories(limit=1)
    if not resp.success:
        pytest.skip(f"Query history API not available: {resp.status_code}")


@pytest.mark.core
class TestQueryHistory:
    """Query history tracking and retrieval."""

    def test_list_query_histories(self, client):
        """List query histories returns valid structure."""
        resp = client.list_query_histories(limit=10)
        assert resp.success, f"List query histories failed: {resp.status_code}"
        entries = resp.data.get("queries", [])
        assert isinstance(entries, list), f"Expected list of queries, got: {type(entries)}"

        if entries:
            first = entries[0]
            assert "id" in first, f"History entry should have 'id': {first}"
            assert "query" in first, f"History entry should have 'query': {first}"
            assert "started_at" in first, f"History entry should have 'started_at': {first}"

    def test_query_history_contains_generation(self, client):
        """Verify query history entries include generation/answer content."""
        hist_resp = client.list_query_histories(limit=5)
        entries = hist_resp.data.get("queries", [])
        if not entries:
            pytest.skip("No query history entries available")

        entries_with_gen = [e for e in entries if e.get("generation")]
        assert len(entries_with_gen) > 0, \
            f"Expected at least one entry with generation content, got keys: {[list(e.keys()) for e in entries[:2]]}"
