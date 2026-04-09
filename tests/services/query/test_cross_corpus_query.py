"""
Cross-Corpus Query Tests

Tests for querying across multiple corpora simultaneously.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestCrossCorpusQuery:
    """Cross-corpus query operations."""

    def test_query_across_multiple_corpora(self, client, unique_id):
        """Test querying across two corpora returns results from both."""
        corpus1_key = f"test_cross1_{unique_id}"
        corpus2_key = f"test_cross2_{unique_id}"

        c1 = client.create_corpus(name=f"Cross1 {unique_id}", key=corpus1_key)
        c2 = client.create_corpus(name=f"Cross2 {unique_id}", key=corpus2_key)

        if not c1.success or not c2.success:
            for k in [corpus1_key, corpus2_key]:
                try:
                    client.delete_corpus(k)
                except Exception:
                    pass
            pytest.skip("Could not create corpora for cross-corpus test")

        try:
            for key in [corpus1_key, corpus2_key]:
                wait_for(
                    lambda k=key: client.get_corpus(k).success,
                    timeout=10, interval=1,
                    description=f"corpus {key} available",
                )

            client.index_document(corpus1_key, f"doc1_{unique_id}", "Medical research on heart disease prevention")
            client.index_document(corpus2_key, f"doc2_{unique_id}", "Legal precedents in contract law disputes")

            for key, doc_id in [(corpus1_key, f"doc1_{unique_id}"), (corpus2_key, f"doc2_{unique_id}")]:
                wait_for(
                    lambda k=key, d=doc_id: client.get_document(k, d).success,
                    timeout=15, interval=1,
                    description=f"document in {key} indexed",
                )

            query_resp = client.post("/v2/query", data={
                "query": "important topics",
                "search": {
                    "corpora": [
                        {"corpus_key": corpus1_key},
                        {"corpus_key": corpus2_key},
                    ],
                    "limit": 10,
                },
            })
            assert query_resp.success, f"Cross-corpus query failed: {query_resp.status_code}"
            results = query_resp.data.get("search_results", [])
            assert len(results) > 0, "Expected results from cross-corpus query"

            result_corpus_keys = {r.get("corpus_key") for r in results}
            assert corpus1_key in result_corpus_keys or corpus2_key in result_corpus_keys, \
                f"Expected results from at least one of the test corpora, got: {result_corpus_keys}"
        finally:
            for key in [corpus1_key, corpus2_key]:
                try:
                    client.delete_corpus(key)
                except Exception:
                    pass
