"""
Query Filter Tests (SDK)

Tests for metadata filter expressions in queries using the Vectara Python SDK.
"""

import uuid

import pytest
from vectara.errors import BadRequestError, NotFoundError
from vectara.types import (
    CoreDocumentPart,
    CreateDocumentRequest_Core,
    FilterAttribute,
    FilterAttributeLevel,
    FilterAttributeType,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)

from utils.waiters import wait_for


@pytest.mark.core
class TestQueryFiltersCore:
    """Query with metadata filter tests."""

    def test_query_with_valid_metadata_filter(self, sdk_client, unique_id):
        """Test querying with a valid metadata filter returns matching results."""
        corpus_key = f"test_filter_{unique_id}"

        try:
            corpus = sdk_client.corpora.create(
                name=f"Filter Test {unique_id}",
                key=corpus_key,
                filter_attributes=[
                    FilterAttribute(
                        name="topic",
                        level=FilterAttributeLevel.PART,
                        type=FilterAttributeType.TEXT,
                        indexed=True,
                    ),
                ],
            )
        except Exception as e:
            pytest.skip(f"Could not create corpus: {e}")

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, corpus_key),
                timeout=10,
                interval=1,
                description="corpus to be available",
            )

            doc_id = f"filter_doc_{unique_id}"
            sdk_client.documents.create(
                corpus_key,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Artificial intelligence is transforming industries worldwide.",
                            metadata={"topic": "ai"},
                        )
                    ],
                ),
            )

            wait_for(
                lambda: _document_exists(sdk_client, corpus_key, doc_id),
                timeout=15,
                interval=1,
                description="document to be indexed",
            )

            response = sdk_client.query(
                query="artificial intelligence",
                search=SearchCorporaParameters(
                    corpora=[
                        KeyedSearchCorpus(
                            corpus_key=corpus_key,
                            metadata_filter="part.topic = 'ai'",
                        )
                    ],
                    limit=10,
                ),
            )
            results = response.search_results or []
            assert len(results) > 0, "Expected at least one result for valid filter"
        finally:
            try:
                sdk_client.corpora.delete(corpus_key)
            except Exception:
                pass

    def test_query_empty_corpus_returns_empty_results(self, sdk_client, unique_id):
        """Test that querying an empty corpus returns an empty results list."""
        corpus_key = f"test_empty_{unique_id}"

        try:
            sdk_client.corpora.create(
                name=f"Empty Corpus {unique_id}",
                key=corpus_key,
            )
        except Exception as e:
            pytest.skip(f"Could not create corpus: {e}")

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, corpus_key),
                timeout=10,
                interval=1,
                description="corpus to be available",
            )

            response = sdk_client.query(
                query="anything at all",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=corpus_key)],
                    limit=10,
                ),
            )
            results = response.search_results or []
            assert isinstance(results, list), f"Expected list, got: {type(results)}"
            assert len(results) == 0, f"Expected empty results for empty corpus, got {len(results)}"
        finally:
            try:
                sdk_client.corpora.delete(corpus_key)
            except Exception:
                pass


@pytest.mark.regression
class TestQueryFilterErrors:
    """Query filter error handling tests."""

    def test_query_with_invalid_filter_returns_error(self, sdk_seeded_corpus, sdk_client):
        """Test that an invalid filter expression raises BadRequestError."""
        corpus_key = sdk_seeded_corpus.key if hasattr(sdk_seeded_corpus, "key") else sdk_seeded_corpus

        with pytest.raises(BadRequestError):
            sdk_client.query(
                query="test",
                search=SearchCorporaParameters(
                    corpora=[
                        KeyedSearchCorpus(
                            corpus_key=corpus_key,
                            metadata_filter="part.nonexistent_field = 'value'",
                        )
                    ],
                    limit=10,
                ),
            )


def _corpus_exists(sdk_client, corpus_key):
    """Check if corpus exists."""
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False


def _document_exists(sdk_client, corpus_key, doc_id):
    """Check if document exists."""
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False
