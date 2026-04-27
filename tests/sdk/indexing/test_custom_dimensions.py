"""
Custom Dimensions Tests (SDK)

Tests for indexing and querying documents with custom dimension weights
using the Vectara Python SDK. Uses a dedicated corpus with custom dimensions configured.
"""

import uuid

import pytest
from vectara.corpora.types import QueryCorporaRequestSearch
from vectara.types import (
    CoreDocumentPart,
    CorpusCustomDimension,
    CreateDocumentRequest_Core,
)

from utils.waiters import wait_for


@pytest.fixture
def sdk_custom_dims_corpus(sdk_client):
    """Function-scoped corpus with custom dimensions configured."""
    corpus_key = f"dims_test_{uuid.uuid4().hex}"
    try:
        corpus = sdk_client.corpora.create(
            name=f"Custom Dims Test {uuid.uuid4().hex[:8]}",
            key=corpus_key,
            description="Corpus with custom dimensions for testing",
            custom_dimensions=[
                CorpusCustomDimension(name="importance", indexing_default=0, querying_default=0),
                CorpusCustomDimension(name="recency", indexing_default=0, querying_default=0),
            ],
        )
    except Exception as e:
        if "412" in str(e) or "custom dimensions" in str(e).lower() or "Plan does not support" in str(e):
            pytest.skip("Plan does not support custom dimensions in corpora")
        raise

    wait_for(
        lambda: _corpus_exists(sdk_client, corpus.key),
        timeout=10,
        interval=1,
        description="custom dims corpus to become queryable",
    )
    yield corpus

    try:
        sdk_client.corpora.delete(corpus.key)
    except Exception:
        pass


@pytest.mark.core
class TestCustomDimensions:
    """Core tests for custom dimension indexing and querying."""

    def test_custom_dimensions_boost(self, sdk_client, sdk_custom_dims_corpus, unique_id):
        """Custom dimensions should boost relevant parts in query results."""
        corpus_key = sdk_custom_dims_corpus.key
        doc_id = f"dims_doc_{unique_id}"

        sdk_client.documents.create(
            corpus_key,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text="This is a high-importance document about quantum computing breakthroughs.",
                        metadata={"section": "important"},
                        custom_dimensions={"importance": 0.95, "recency": 0.85},
                    ),
                    CoreDocumentPart(
                        text="This is a low-importance note about office supplies.",
                        metadata={"section": "filler"},
                        custom_dimensions={"importance": 0.1, "recency": 0.2},
                    ),
                ],
            ),
        )

        # Wait for indexing
        wait_for(
            lambda: len(list(sdk_client.documents.list(corpus_key, limit=1))) > 0,
            timeout=15,
            interval=1,
            description="custom dims doc to be indexed",
        )

        # Query with dimension weights that favor importance
        query_response = sdk_client.corpora.query(
            corpus_key,
            query="What are the latest breakthroughs?",
            search=QueryCorporaRequestSearch(
                limit=5,
                custom_dimensions={"importance": 0.8, "recency": 0.5},
            ),
        )

        results = query_response.search_results or []
        assert len(results) > 0, "Expected at least one result"

        # First result should be the high-importance part
        first_result_text = results[0].text
        assert (
            "quantum computing" in first_result_text.lower() or "high-importance" in first_result_text.lower()
        ), f"Expected high-importance part first, got: {first_result_text[:100]}"

        # Cleanup
        try:
            sdk_client.documents.delete(corpus_key, doc_id)
        except Exception:
            pass


def _corpus_exists(sdk_client, corpus_key):
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False
