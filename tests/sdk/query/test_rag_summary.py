"""
RAG Summary Tests (SDK)

Core-level tests for query-with-summary (RAG) operations
and summary response time using the Vectara Python SDK.
"""

import time

import pytest
from vectara.types import (
    GenerationParameters,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)


@pytest.mark.core
class TestRagSummary:
    """Core checks for RAG summarization."""

    def test_query_with_summary(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with RAG summarization."""
        response = sdk_client.query(
            query="How is AI being used today?",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=3,
            ),
            generation=GenerationParameters(),
        )

        assert response.summary is not None, "Expected summary in response"
        assert len(response.summary) > 0, "Expected non-empty summary"

    def test_summary_response_time(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that RAG summarization completes in acceptable time."""
        start = time.monotonic()
        response = sdk_client.query(
            query="What are the main topics covered?",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=3,
            ),
            generation=GenerationParameters(),
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        assert response.summary is not None, "Expected summary in response"
        assert elapsed_ms < 30000, f"Summary took too long: {elapsed_ms:.1f}ms"
