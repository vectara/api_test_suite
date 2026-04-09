"""
Factual Consistency Score Tests

Tests for verifying factual consistency scoring in RAG responses.
FCS is enabled by default (OpenAPI spec: default=true) when generation is requested.
"""

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestFactualConsistency:
    """Factual consistency score validation."""

    def test_rag_returns_fcs_score(self, client, seeded_shared_corpus):
        """Test that RAG query returns a valid factual consistency score."""
        wait_for(
            lambda: len(
                client.post("/v2/query", data={
                    "query": "technology",
                    "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 5},
                }).data.get("search_results", [])
            ) > 0,
            timeout=20, interval=2,
            description="seeded corpus to return search results",
        )

        resp = client.post("/v2/query", data={
            "query": "artificial intelligence and machine learning",
            "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 10},
            "generation": {},
        })
        assert resp.success, f"RAG query failed: {resp.status_code} - {resp.data}"

        score = resp.data.get("factual_consistency_score")
        assert score is not None, \
            f"Expected factual_consistency_score in response, got keys: {list(resp.data.keys())}"
        assert 0.0 <= score <= 1.0, f"FCS score out of range [0, 1]: {score}"
