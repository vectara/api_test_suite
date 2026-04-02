"""
Semantic Search Tests

Tests for basic semantic search, relevance, limit, and offset operations.
"""

import pytest


@pytest.mark.sanity
class TestSemanticSearchSanity:
    """Sanity-level semantic search checks."""

    def test_basic_query(self, client, seeded_shared_corpus):
        """Test basic semantic search query."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="What is artificial intelligence?",
            limit=5,
        )

        assert response.success, (
            f"Query failed: {response.status_code} - {response.data}"
        )

        # Should return search results
        assert "search_results" in response.data or "results" in response.data, (
            "Expected search results in response"
        )


@pytest.mark.core
class TestSemanticSearchCore:
    """Core-level semantic search checks."""

    def test_query_returns_relevant_results(self, client, seeded_shared_corpus):
        """Test that query returns semantically relevant results."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="machine learning and neural networks",
            limit=3,
        )

        assert response.success, f"Query failed: {response.status_code}"

        # Results should be returned
        results = response.data.get("search_results", response.data.get("results", []))
        assert len(results) > 0, "Expected at least one search result"

    def test_query_with_limit(self, client, seeded_shared_corpus):
        """Test query with result limit."""
        response = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="technology",
            limit=2,
        )

        assert response.success, f"Query failed: {response.status_code}"

        results = response.data.get("search_results", response.data.get("results", []))
        assert len(results) <= 2, f"Expected at most 2 results, got {len(results)}"

    def test_query_with_offset(self, client, seeded_shared_corpus):
        """Test query with pagination offset."""
        # First query without offset
        response1 = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="science and technology",
            limit=2,
            offset=0,
        )

        # Second query with offset
        response2 = client.query(
            corpus_key=seeded_shared_corpus,
            query_text="science and technology",
            limit=2,
            offset=2,
        )

        assert response1.success and response2.success, "Queries failed"

        # Results should be different (pagination working)
        results1 = response1.data.get("search_results", response1.data.get("results", []))
        results2 = response2.data.get("search_results", response2.data.get("results", []))

        if len(results1) > 0 and len(results2) > 0:
            # First result of each page should be different
            id1 = results1[0].get("document_id", results1[0].get("id"))
            id2 = results2[0].get("document_id", results2[0].get("id"))
            assert id1 != id2, "Offset pagination not working correctly"
