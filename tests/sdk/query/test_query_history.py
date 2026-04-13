"""
Query History Tests (SDK)

Verify that queries are recorded and retrievable via the query history API
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


@pytest.mark.core
class TestQueryHistory:
    """Query history tracking and retrieval."""

    def test_list_query_histories(self, sdk_client):
        """List query histories returns valid structure."""
        entries = list(sdk_client.query_history.list(limit=10))
        assert isinstance(entries, list), f"Expected list of queries, got: {type(entries)}"

        if entries:
            first = entries[0]
            assert first.id is not None, f"History entry should have 'id': {first}"
            assert first.query is not None, f"History entry should have 'query': {first}"
            assert first.started_at is not None, f"History entry should have 'started_at': {first}"

    def test_query_history_contains_generation(self, sdk_client):
        """Verify query history entries include generation/answer content."""
        entries = list(sdk_client.query_history.list(limit=5))
        if not entries:
            pytest.skip("No query history entries available")

        entries_with_gen = [e for e in entries if getattr(e, "generation", None)]
        assert len(entries_with_gen) > 0, (
            f"Expected at least one entry with generation content"
        )
