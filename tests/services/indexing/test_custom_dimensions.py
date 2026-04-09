"""
Custom Dimensions Tests

Tests for indexing and querying documents with custom dimension weights.
Uses a dedicated corpus with custom dimensions configured.
"""

import uuid

import pytest

from utils.waiters import wait_for


@pytest.fixture
def custom_dims_corpus(client):
    """Function-scoped corpus with custom dimensions configured."""
    corpus_key = f"dims_test_{uuid.uuid4().hex}"
    response = client.create_corpus(
        name=f"Custom Dims Test {uuid.uuid4().hex[:8]}",
        key=corpus_key,
        description="Corpus with custom dimensions for testing",
        custom_dimensions=[
            {"name": "importance", "indexing_default": 0, "querying_default": 0},
            {"name": "recency", "indexing_default": 0, "querying_default": 0},
        ],
    )
    if not response.success:
        pytest.skip(f"Could not create custom dims corpus: {response.data}")

    actual_key = response.data.get("key", corpus_key)
    wait_for(
        lambda: client.get_corpus(actual_key).success,
        timeout=10,
        interval=1,
        description="custom dims corpus to become queryable",
    )
    yield actual_key

    try:
        client.delete_corpus(actual_key)
    except Exception:
        pass


@pytest.mark.core
class TestCustomDimensions:
    """Core tests for custom dimension indexing and querying."""

    def test_custom_dimensions_boost(self, client, custom_dims_corpus, unique_id):
        """Custom dimensions should boost relevant parts in query results."""
        doc_id = f"dims_doc_{unique_id}"
        parts = [
            {
                "text": "This is a high-importance document about quantum computing breakthroughs.",
                "metadata": {"section": "important"},
                "custom_dimensions": {"importance": 0.95, "recency": 0.85},
            },
            {
                "text": "This is a low-importance note about office supplies.",
                "metadata": {"section": "filler"},
                "custom_dimensions": {"importance": 0.1, "recency": 0.2},
            },
        ]

        index_response = client.index_document_parts(
            corpus_key=custom_dims_corpus,
            document_id=doc_id,
            parts=parts,
        )
        assert index_response.success, f"Index failed: {index_response.status_code} - {index_response.data}"

        # Wait for indexing
        wait_for(
            lambda: client.list_documents(custom_dims_corpus, limit=1).data.get("documents", []),
            timeout=15,
            interval=1,
            description="custom dims doc to be indexed",
        )

        # Query with dimension weights that favor importance
        query_response = client.query_corpus(
            corpus_key=custom_dims_corpus,
            query_text="What are the latest breakthroughs?",
            limit=5,
            custom_dimensions={"importance": 0.8, "recency": 0.5},
        )
        assert query_response.success, f"Query failed: {query_response.status_code} - {query_response.data}"

        results = query_response.data.get("search_results", [])
        assert len(results) > 0, "Expected at least one result"

        # First result should be the high-importance part
        first_result_text = results[0].get("text", "")
        assert (
            "quantum computing" in first_result_text.lower() or "high-importance" in first_result_text.lower()
        ), f"Expected high-importance part first, got: {first_result_text[:100]}"

        # Cleanup
        try:
            client.delete_document(custom_dims_corpus, doc_id)
        except Exception:
            pass
