"""
RAG Summary Tests

Core-level tests for query-with-summary (RAG) operations
and summary response time.
"""

import pytest


@pytest.mark.core
class TestRagSummary:
    """Core checks for RAG summarization."""

    def test_query_with_summary(self, client, seeded_shared_corpus):
        """Test query with RAG summarization."""
        response = client.query_with_summary(
            corpus_key=seeded_shared_corpus,
            query_text="How is AI being used today?",
            max_results=3,
        )

        assert response.success, f"Query with summary failed: {response.status_code} - {response.data}"

        # Should contain generated summary
        assert "summary" in response.data or "generation" in response.data, "Expected summary/generation in response"

    def test_summary_response_time(self, client, seeded_shared_corpus):
        """Test that RAG summarization completes in acceptable time."""
        response = client.query_with_summary(
            corpus_key=seeded_shared_corpus,
            query_text="What are the main topics covered?",
            max_results=3,
        )

        assert response.success, f"Summary query failed: {response.status_code}"
        # RAG takes longer due to LLM generation
        assert response.elapsed_ms < 30000, f"Summary took too long: {response.elapsed_ms:.1f}ms"
