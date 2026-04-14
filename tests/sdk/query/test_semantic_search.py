"""
Semantic Search Tests (SDK)

Tests for basic semantic search, relevance, limit, and offset operations
using the Vectara Python SDK.
"""

import pytest
from vectara.types import KeyedSearchCorpus, SearchCorporaParameters


@pytest.mark.sanity
class TestSemanticSearchBasic:
    """Basic semantic search checks."""

    def test_basic_query(self, sdk_client, sdk_seeded_shared_corpus):
        """Test basic semantic search query."""
        response = sdk_client.query(
            query="What is artificial intelligence?",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
        )

        assert response.search_results is not None, "Expected search_results in response"


@pytest.mark.core
class TestSemanticSearchPagination:
    """Semantic search relevance, limit, and offset checks."""

    def test_query_returns_relevant_results(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that query returns semantically relevant results."""
        response = sdk_client.query(
            query="machine learning and neural networks",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=3,
            ),
        )

        assert response.search_results is not None, "Expected search_results in response"
        assert len(response.search_results) > 0, "Expected at least one search result"

    def test_query_with_limit(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with result limit."""
        response = sdk_client.query(
            query="technology",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=2,
            ),
        )

        assert response.search_results is not None, "Expected search_results"
        assert len(response.search_results) <= 2, f"Expected at most 2 results, got {len(response.search_results)}"

    def test_query_with_offset(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with pagination offset."""
        response1 = sdk_client.query(
            query="science and technology",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=2,
                offset=0,
            ),
        )

        response2 = sdk_client.query(
            query="science and technology",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=2,
                offset=2,
            ),
        )

        results1 = response1.search_results or []
        results2 = response2.search_results or []

        if len(results1) > 0 and len(results2) > 0:
            id1 = results1[0].document_id
            id2 = results2[0].document_id
            assert id1 != id2, "Offset pagination not working correctly"
