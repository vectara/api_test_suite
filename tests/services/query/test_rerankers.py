"""
Reranker Tests

Tests for listing and using rerankers.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_rerankers_available(client):
    """Skip all tests if rerankers API is not available."""
    resp = client.list_rerankers(limit=1)
    if not resp.success:
        pytest.skip("Rerankers API not available")


@pytest.mark.core
class TestRerankers:
    """Reranker listing and usage."""

    def test_list_rerankers(self, client):
        """Test listing rerankers with proper structure."""
        resp = client.list_rerankers(limit=50)
        assert resp.success, f"List rerankers failed: {resp.status_code}"
        rerankers = resp.data.get("rerankers", [])
        assert isinstance(rerankers, list)
        assert len(rerankers) > 0, "Expected at least one reranker"
        first = rerankers[0]
        assert "id" in first or "name" in first, "Reranker should have 'id' or 'name' field"

    def test_query_with_mmr_reranker(self, client, seeded_shared_corpus):
        """Test querying with the MMR reranker."""
        query_resp = client.post(
            "/v2/query",
            data={
                "query": "artificial intelligence",
                "search": {
                    "corpora": [{"corpus_key": seeded_shared_corpus}],
                    "limit": 10,
                    "reranker": {
                        "type": "mmr",
                        "diversity_bias": 0.3,
                    },
                },
            },
        )
        assert query_resp.success, f"Query with MMR reranker failed: {query_resp.status_code} - {query_resp.data}"
        results = query_resp.data.get("search_results", [])
        assert isinstance(results, list)
        assert len(results) > 0, "Expected results with MMR reranker"
