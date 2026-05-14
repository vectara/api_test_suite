"""
Query Filter Tests

Tests for metadata filter expressions in queries.
"""

import uuid

import pytest

from utils.waiters import wait_for


@pytest.mark.core
class TestQueryFiltersCore:
    """Query with metadata filter tests."""

    def test_query_with_valid_metadata_filter(self, client, unique_id):
        """Test querying with a valid metadata filter returns matching results."""
        corpus_key = f"test_filter_{unique_id}"

        create_resp = client.create_corpus(
            name=f"Filter Test {unique_id}",
            key=corpus_key,
            filter_attributes=[
                {"name": "topic", "level": "part", "type": "text", "indexed": True},
            ],
        )
        if not create_resp.success:
            pytest.skip(f"Could not create corpus: {create_resp.data}")

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10,
                interval=1,
                description="corpus to be available",
            )

            doc_id = f"filter_doc_{unique_id}"
            index_resp = client.index_document(
                corpus_key=corpus_key,
                document_id=doc_id,
                text="Artificial intelligence is transforming industries worldwide.",
                metadata={"topic": "ai"},
            )
            assert index_resp.success, f"Index failed: {index_resp.status_code} - {index_resp.data}"

            wait_for(
                lambda: client.get_document(corpus_key, doc_id).success,
                timeout=15,
                interval=1,
                description="document to be indexed",
            )

            def _query_returns_results():
                resp = client.post(
                    "/v2/query",
                    data={
                        "query": "artificial intelligence",
                        "search": {
                            "corpora": [{"corpus_key": corpus_key, "metadata_filter": "part.topic = 'ai'"}],
                            "limit": 10,
                        },
                    },
                )
                if not resp.success:
                    return None
                if not resp.data.get("search_results"):
                    return None
                return resp

            query_resp = wait_for(
                _query_returns_results,
                timeout=30,
                interval=2,
                description="filter query to return results",
            )
            assert query_resp.success, f"Query failed: {query_resp.status_code} - {query_resp.data}"
            results = query_resp.data.get("search_results", [])
            assert len(results) > 0, "Expected at least one result for valid filter"
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass

    def test_query_empty_corpus_returns_empty_results(self, client, unique_id):
        """Test that querying an empty corpus returns an empty results list."""
        corpus_key = f"test_empty_{unique_id}"

        create_resp = client.create_corpus(
            name=f"Empty Corpus {unique_id}",
            key=corpus_key,
        )
        if not create_resp.success:
            pytest.skip(f"Could not create corpus: {create_resp.data}")

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10,
                interval=1,
                description="corpus to be available",
            )

            query_resp = client.query(
                corpus_key=corpus_key,
                query_text="anything at all",
                limit=10,
            )
            assert query_resp.success, f"Query failed: {query_resp.status_code}"
            results = query_resp.data.get("search_results", [])
            assert isinstance(results, list), f"Expected list, got: {type(results)}"
            assert len(results) == 0, f"Expected empty results for empty corpus, got {len(results)}"
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass


@pytest.mark.regression
class TestQueryFilterErrors:
    """Query filter error handling tests."""

    def test_query_with_invalid_filter_returns_400(self, seeded_corpus, client):
        """Test that an invalid filter expression returns 400."""
        query_resp = client.post(
            "/v2/query",
            data={
                "query": "test",
                "search": {
                    "corpora": [{"corpus_key": seeded_corpus, "metadata_filter": "part.nonexistent_field = 'value'"}],
                    "limit": 10,
                },
            },
        )
        assert not query_resp.success, "Invalid filter should fail"
        assert query_resp.status_code == 400, f"Expected 400 for invalid filter, got {query_resp.status_code}"
