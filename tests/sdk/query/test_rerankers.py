"""
Reranker Tests (SDK)

Tests for listing and using rerankers via the Vectara Python SDK.
"""

import pytest

from vectara.types import (
    SearchCorporaParameters,
    KeyedSearchCorpus,
    SearchReranker_Mmr,
)


@pytest.fixture(scope="module", autouse=True)
def check_rerankers_available(sdk_client):
    """Skip all tests if rerankers API is not available."""
    try:
        rerankers = list(sdk_client.rerankers.list(limit=1))
        if not rerankers:
            pytest.skip("No rerankers available")
    except Exception:
        pytest.skip("Rerankers API not available")


@pytest.mark.core
class TestRerankers:
    """Reranker listing and usage."""

    def test_list_rerankers(self, sdk_client):
        """Test listing rerankers with proper structure."""
        rerankers = list(sdk_client.rerankers.list(limit=50))
        assert isinstance(rerankers, list)
        assert len(rerankers) > 0, "Expected at least one reranker"
        first = rerankers[0]
        assert hasattr(first, "id") or hasattr(first, "name"), "Reranker should have 'id' or 'name' field"

    def test_query_with_mmr_reranker(self, sdk_client, sdk_seeded_shared_corpus):
        """Test querying with the MMR reranker."""
        response = sdk_client.query(
            query="artificial intelligence",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=10,
                reranker=SearchReranker_Mmr(diversity_bias=0.3),
            ),
        )
        results = response.search_results or []
        assert isinstance(results, list)
        assert len(results) > 0, "Expected results with MMR reranker"
