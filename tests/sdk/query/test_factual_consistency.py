"""
Factual Consistency Score Tests (SDK)

Tests for verifying factual consistency scoring in RAG responses
using the Vectara Python SDK.

FCS is enabled by default (OpenAPI spec: default=true) when generation is requested.
"""

import pytest

from vectara.types import (
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
)

from utils.waiters import wait_for


@pytest.mark.core
class TestFactualConsistency:
    """Factual consistency score validation."""

    def test_rag_returns_fcs_score(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that RAG query returns a valid factual consistency score."""
        # Wait for corpus to return search results
        wait_for(
            lambda: _has_search_results(sdk_client, sdk_seeded_shared_corpus),
            timeout=20,
            interval=2,
            description="seeded corpus to return search results",
        )

        response = sdk_client.query(
            query="artificial intelligence and machine learning",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=10,
            ),
            generation=GenerationParameters(),
        )

        score = response.factual_consistency_score
        assert score is not None, (
            f"Expected factual_consistency_score in response, got summary={response.summary is not None}"
        )
        assert 0.0 <= score <= 1.0, f"FCS score out of range [0, 1]: {score}"


def _has_search_results(sdk_client, corpus_key):
    """Check if corpus returns search results."""
    try:
        resp = sdk_client.query(
            query="technology",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=corpus_key)],
                limit=5,
            ),
        )
        return resp.search_results is not None and len(resp.search_results) > 0
    except Exception:
        return False
