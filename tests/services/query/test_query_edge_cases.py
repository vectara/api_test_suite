"""
Query Filtering and Edge Case Tests

Regression-level tests for empty results, special characters, unicode,
long queries, response time, and querying non-existent corpora.
"""

import pytest


@pytest.mark.regression
class TestQueryFiltering:
    """Regression checks for query edge cases and filtering."""

    def test_query_empty_results(self, client, seeded_shared_corpus):
        """Test query that returns no relevant results."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="quantum teleportation through wormholes in the 15th century",
            limit=5,
        )

        assert response.success, f"Query failed: {response.status_code}"
        results = response.data.get("search_results", response.data.get("results", []))
        assert isinstance(results, list), f"Expected search_results list, got: {type(results)}"
        # Query should succeed even with no/few relevant results

    def test_query_special_characters(self, client, seeded_shared_corpus):
        """Test query with special characters."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="What's the purpose of AI & machine-learning?",
            limit=3,
        )

        assert response.success, f"Query with special characters failed: {response.status_code}"
        assert "search_results" in response.data or "results" in response.data, \
            f"Response missing search_results key: {list(response.data.keys()) if isinstance(response.data, dict) else type(response.data)}"

    def test_query_unicode(self, client, seeded_shared_corpus):
        """Test query with unicode characters."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="intelig\u00eancia artificial e aprendizado de m\u00e1quina",
            limit=3,
        )

        assert response.success, f"Query with unicode failed: {response.status_code}"
        assert "search_results" in response.data or "results" in response.data, \
            f"Response missing search_results key: {list(response.data.keys()) if isinstance(response.data, dict) else type(response.data)}"

    def test_query_long_text(self, client, seeded_shared_corpus):
        """Test query with longer query text."""
        long_query = (
            "I am interested in learning about how artificial intelligence and "
            "machine learning technologies are being applied in various industries "
            "such as healthcare and finance. Can you provide information about "
            "the latest developments in deep learning and neural networks?"
        )

        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text=long_query,
            limit=5,
        )

        assert response.success, f"Long query failed: {response.status_code}"
        assert "search_results" in response.data or "results" in response.data, \
            f"Response missing search_results key: {list(response.data.keys()) if isinstance(response.data, dict) else type(response.data)}"

    def test_query_response_time(self, client, seeded_shared_corpus):
        """Test that queries complete in acceptable time."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="artificial intelligence",
            limit=5,
        )

        assert response.success, f"Query failed: {response.status_code}"
        assert response.elapsed_ms < 5000, f"Query took too long: {response.elapsed_ms:.1f}ms"

    def test_query_nonexistent_corpus(self, client):
        """Test querying a non-existent corpus."""
        response = client.query(
            corpus_key="nonexistent_corpus_xyz123",
            query_text="test query",
            limit=5,
        )

        assert not response.success, "Query to non-existent corpus should fail"
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"
