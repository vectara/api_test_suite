"""
Document Operations Tests (SDK)

Tests for document parts listing, bulk delete, and special character handling
using the Vectara Python SDK.
"""

import pytest

from vectara.errors import NotFoundError
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


@pytest.mark.core
class TestDocumentOperations:
    """Document operations tests."""

    def test_list_document_parts(self, sdk_client, sdk_test_corpus, unique_id):
        """Test that a document with multiple parts shows proper structure."""
        corpus_key = sdk_test_corpus.key
        doc_id = f"parts_doc_{unique_id}"

        sdk_client.documents.create(
            corpus_key,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text="First part about artificial intelligence.",
                        metadata={"section": "intro"},
                    ),
                    CoreDocumentPart(
                        text="Second part about machine learning.",
                        metadata={"section": "body"},
                    ),
                ],
            ),
        )

        wait_for(
            lambda: _document_exists(sdk_client, corpus_key, doc_id),
            timeout=15,
            interval=1,
            description="document to be indexed",
        )

        fetched = sdk_client.documents.get(corpus_key, doc_id)
        assert fetched.id == doc_id, f"Document id mismatch: expected {doc_id}, got {fetched.id}"

    def test_bulk_delete_documents(self, sdk_client, sdk_test_corpus, unique_id):
        """Test bulk deleting documents by ID."""
        corpus_key = sdk_test_corpus.key
        doc_ids = [f"bulk_{unique_id}_{i}" for i in range(3)]

        for doc_id in doc_ids:
            sdk_client.documents.create(
                corpus_key,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[CoreDocumentPart(text=f"Content for {doc_id}")],
                ),
            )

        wait_for(
            lambda: all(_document_exists(sdk_client, corpus_key, d) for d in doc_ids),
            timeout=20,
            interval=2,
            description="all documents to be indexed",
        )

        sdk_client.documents.bulk_delete(
            corpus_key,
            document_ids=",".join(doc_ids),
            async_=False,
        )

        wait_for(
            lambda: all(_document_gone(sdk_client, corpus_key, d) for d in doc_ids),
            timeout=30,
            interval=2,
            description="all documents to be deleted",
        )


@pytest.mark.regression
class TestDocumentEdgeCases:
    """Document edge case tests."""

    def test_delete_document_with_special_chars(self, sdk_client, sdk_test_corpus, unique_id):
        """Test deleting a document with special characters in ID."""
        corpus_key = sdk_test_corpus.key
        doc_id = f"doc-special-chars_{unique_id}"

        sdk_client.documents.create(
            corpus_key,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[CoreDocumentPart(text="Content with special ID")],
            ),
        )

        wait_for(
            lambda: _document_exists(sdk_client, corpus_key, doc_id),
            timeout=15,
            interval=1,
            description="document to be indexed",
        )

        sdk_client.documents.delete(corpus_key, doc_id)


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False


def _document_gone(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return False
    except NotFoundError:
        return True
    except Exception:
        return False
