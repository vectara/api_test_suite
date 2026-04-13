"""
Single Document Indexing Tests (SDK)

Tests for indexing, retrieving, deleting, and updating individual documents
using the Vectara Python SDK.
"""

import pytest

from vectara.errors import NotFoundError
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core


@pytest.mark.sanity
class TestDocumentIndex:
    """Document indexing checks."""

    def test_index_single_document(self, sdk_client, sdk_shared_corpus, unique_id, sample_document):
        """Test indexing a single document."""
        doc_id = f"single_doc_{unique_id}"

        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text=sample_document["text"],
                        metadata=sample_document["metadata"],
                    ),
                ],
                metadata=sample_document["metadata"],
            ),
        )

        assert doc.id is not None, f"Index response should contain document id, got: {doc}"


@pytest.mark.core
class TestDocumentCrud:
    """Document get, delete, and update operations."""

    def test_get_document(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test retrieving an indexed document."""
        doc_id = f"get_doc_{unique_id}"

        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Document for retrieval test."),
                ],
            ),
        )

        # Retrieve the document
        doc = sdk_client.documents.get(sdk_shared_corpus, doc_id)

        assert doc.id == doc_id, f"Document ID mismatch: expected {doc_id}"

    def test_delete_document(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test deleting a document."""
        doc_id = f"delete_doc_{unique_id}"

        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Document to be deleted."),
                ],
            ),
        )

        # Delete document
        sdk_client.documents.delete(sdk_shared_corpus, doc_id)

        # Verify deletion - should raise NotFoundError
        with pytest.raises(NotFoundError):
            sdk_client.documents.get(sdk_shared_corpus, doc_id)

    def test_update_document_by_delete_and_reindex(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test updating a document by deleting and re-indexing."""
        doc_id = f"update_doc_{unique_id}"

        # Index original document
        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Original content."),
                ],
                metadata={"version": 1},
            ),
        )

        # Delete the original document
        sdk_client.documents.delete(sdk_shared_corpus, doc_id)

        # Re-index with updated content
        updated_doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Updated content with new information."),
                ],
                metadata={"version": 2},
            ),
        )

        assert updated_doc.id is not None, f"Document re-index should return document id"
