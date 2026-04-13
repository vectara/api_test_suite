"""
Query Filtering and Edge Case Tests (SDK)

Regression-level tests for empty results, special characters, unicode,
long queries, response time, and querying non-existent corpora
using the Vectara Python SDK.
"""

import time

import pytest

from vectara.types import SearchCorporaParameters, KeyedSearchCorpus
from vectara.errors import NotFoundError, BadRequestError


@pytest.mark.regression
class TestQueryFiltering:
    """Regression checks for query edge cases and filtering."""

    def test_query_empty_results(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query that returns no relevant results."""
        response = sdk_client.query(
            query="quantum teleportation through wormholes in the 15th century",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
        )

        results = response.search_results or []
        assert isinstance(results, list), f"Expected search_results list, got: {type(results)}"

    def test_query_special_characters(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with special characters."""
        response = sdk_client.query(
            query="What's the purpose of AI & machine-learning?",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=3,
            ),
        )

        assert response.search_results is not None, "Response missing search_results"

    def test_query_unicode(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with unicode characters."""
        response = sdk_client.query(
            query="intelig\u00eancia artificial e aprendizado de m\u00e1quina",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=3,
            ),
        )

        assert response.search_results is not None, "Response missing search_results"

    def test_query_long_text(self, sdk_client, sdk_seeded_shared_corpus):
        """Test query with longer query text."""
        long_query = (
            "I am interested in learning about how artificial intelligence and "
            "machine learning technologies are being applied in various industries "
            "such as healthcare and finance. Can you provide information about "
            "the latest developments in deep learning and neural networks?"
        )

        response = sdk_client.query(
            query=long_query,
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
        )

        assert response.search_results is not None, "Response missing search_results"

    def test_query_response_time(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that queries complete in acceptable time."""
        start = time.monotonic()
        response = sdk_client.query(
            query="artificial intelligence",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        assert response.search_results is not None, "Query returned no results"
        assert elapsed_ms < 5000, f"Query took too long: {elapsed_ms:.1f}ms"

    def test_query_nonexistent_corpus(self, sdk_client):
        """Test querying a non-existent corpus."""
        with pytest.raises((NotFoundError, BadRequestError)):
            sdk_client.query(
                query="test query",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key="nonexistent_corpus_xyz123")],
                    limit=5,
                ),
            )
