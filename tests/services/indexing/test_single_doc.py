"""
Single Document Indexing Tests

Tests for indexing, retrieving, deleting, and updating individual documents.
"""

import pytest


@pytest.mark.sanity
class TestSingleDocSanity:
    """Sanity-level single document indexing checks."""

    def test_index_single_document(self, client, test_corpus, unique_id, sample_document):
        """Test indexing a single document."""
        doc_id = f"single_doc_{unique_id}"

        response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc_id,
            text=sample_document["text"],
            metadata=sample_document["metadata"],
        )

        assert response.success, (
            f"Document indexing failed: {response.status_code} - {response.data}"
        )


@pytest.mark.core
class TestSingleDocCore:
    """Core-level single document operations."""

    def test_get_document(self, client, test_corpus, unique_id):
        """Test retrieving an indexed document."""
        doc_id = f"get_doc_{unique_id}"

        # First index a document
        index_response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc_id,
            text="Document for retrieval test.",
        )
        assert index_response.success, "Setup: Document indexing failed"

        # Retrieve the document
        response = client.get_document(test_corpus, doc_id)

        assert response.success, (
            f"Get document failed: {response.status_code} - {response.data}"
        )
        assert response.data.get("id") == doc_id, (
            f"Document ID mismatch: expected {doc_id}"
        )

    def test_delete_document(self, client, test_corpus, unique_id):
        """Test deleting a document."""
        doc_id = f"delete_doc_{unique_id}"

        # Index document
        index_response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc_id,
            text="Document to be deleted.",
        )
        assert index_response.success, "Setup: Document indexing failed"

        # Delete document
        delete_response = client.delete_document(test_corpus, doc_id)

        assert delete_response.success, (
            f"Document deletion failed: {delete_response.status_code} - {delete_response.data}"
        )

        # Verify deletion - should get 404
        get_response = client.get_document(test_corpus, doc_id)
        assert get_response.status_code == 404, (
            f"Deleted document should return 404, got {get_response.status_code}"
        )

    def test_update_document_by_delete_and_reindex(self, client, test_corpus, unique_id):
        """Test updating a document by deleting and re-indexing."""
        doc_id = f"update_doc_{unique_id}"

        # Index original document
        original_response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc_id,
            text="Original content.",
            metadata={"version": 1},
        )
        assert original_response.success, "Setup: Original document indexing failed"

        # Delete the original document
        delete_response = client.delete_document(test_corpus, doc_id)
        assert delete_response.success, f"Delete failed: {delete_response.data}"

        # Re-index with updated content
        update_response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc_id,
            text="Updated content with new information.",
            metadata={"version": 2},
        )

        assert update_response.success, (
            f"Document re-index failed: {update_response.status_code} - {update_response.data}"
        )
