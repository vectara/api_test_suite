"""
Indexing API Tests

Tests for document indexing operations including single document
indexing, bulk operations, and document management.
"""

import pytest
import time


class TestIndexing:
    """Test suite for document indexing operations."""

    def test_index_single_document(self, client, test_corpus_key, unique_id, sample_document):
        """Test indexing a single document."""
        doc_id = f"single_doc_{unique_id}"

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text=sample_document["text"],
            metadata=sample_document["metadata"],
        )

        assert response.success, (
            f"Document indexing failed: {response.status_code} - {response.data}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_index_document_with_metadata(self, client, test_corpus_key, unique_id):
        """Test indexing a document with custom metadata."""
        doc_id = f"meta_doc_{unique_id}"

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Document with rich metadata for testing.",
            metadata={
                "author": "Test Suite",
                "category": "technology",
                "priority": 1,
                "tags": ["test", "api", "indexing"],
                "timestamp": time.time(),
            },
        )

        assert response.success, (
            f"Document with metadata indexing failed: {response.status_code} - {response.data}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_index_large_document(self, client, test_corpus_key, unique_id):
        """Test indexing a larger document with multiple paragraphs."""
        doc_id = f"large_doc_{unique_id}"

        # Generate larger text content
        large_text = " ".join([
            f"Paragraph {i}: This is test content for paragraph number {i}. "
            "It contains information about various topics including technology, "
            "science, and general knowledge. Vector databases enable semantic "
            "search capabilities that traditional keyword search cannot match."
            for i in range(20)
        ])

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text=large_text,
        )

        assert response.success, (
            f"Large document indexing failed: {response.status_code} - {response.data}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_index_multiple_documents(self, client, test_corpus_key, unique_id):
        """Test indexing multiple documents sequentially."""
        doc_ids = [f"multi_doc_{unique_id}_{i}" for i in range(5)]

        for i, doc_id in enumerate(doc_ids):
            response = client.index_document(
                corpus_key=test_corpus_key,
                document_id=doc_id,
                text=f"Test document number {i} with unique content.",
                metadata={"index": i},
            )

            assert response.success, (
                f"Document {i} indexing failed: {response.status_code}"
            )

        # Cleanup
        for doc_id in doc_ids:
            client.delete_document(test_corpus_key, doc_id)

    def test_get_document(self, client, test_corpus_key, unique_id):
        """Test retrieving an indexed document."""
        doc_id = f"get_doc_{unique_id}"

        # First index a document
        index_response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Document for retrieval test.",
        )
        assert index_response.success, "Setup: Document indexing failed"

        # Retrieve the document
        response = client.get_document(test_corpus_key, doc_id)

        assert response.success, (
            f"Get document failed: {response.status_code} - {response.data}"
        )
        assert response.data.get("id") == doc_id, (
            f"Document ID mismatch: expected {doc_id}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_list_documents(self, client, test_corpus_key, unique_id):
        """Test listing documents in a corpus."""
        # Index a few documents first
        doc_ids = [f"list_doc_{unique_id}_{i}" for i in range(3)]
        for doc_id in doc_ids:
            response = client.index_document(
                corpus_key=test_corpus_key,
                document_id=doc_id,
                text=f"Document {doc_id} for listing test.",
            )
            assert response.success, f"Failed to index {doc_id}: {response.data}"

        # Wait for indexing to complete (documents may not be immediately available)
        time.sleep(3)

        # List documents
        response = client.list_documents(test_corpus_key, limit=100)

        assert response.success, (
            f"List documents failed: {response.status_code} - {response.data}"
        )

        # Verify documents exist in list
        documents = response.data.get("documents", response.data)
        doc_ids_in_response = [d.get("id") for d in documents if isinstance(d, dict)]

        # Check that at least some of our documents appear (indexing may be async)
        found_count = sum(1 for doc_id in doc_ids if doc_id in doc_ids_in_response)
        assert found_count > 0, (
            f"None of the indexed documents found in list. Expected: {doc_ids}, Got: {doc_ids_in_response}"
        )

        # Cleanup
        for doc_id in doc_ids:
            client.delete_document(test_corpus_key, doc_id)

    def test_delete_document(self, client, test_corpus_key, unique_id):
        """Test deleting a document."""
        doc_id = f"delete_doc_{unique_id}"

        # Index document
        index_response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Document to be deleted.",
        )
        assert index_response.success, "Setup: Document indexing failed"

        # Delete document
        delete_response = client.delete_document(test_corpus_key, doc_id)

        assert delete_response.success, (
            f"Document deletion failed: {delete_response.status_code} - {delete_response.data}"
        )

        # Verify deletion - should get 404
        get_response = client.get_document(test_corpus_key, doc_id)
        assert get_response.status_code == 404, (
            f"Deleted document should return 404, got {get_response.status_code}"
        )

    def test_update_document_by_delete_and_reindex(self, client, test_corpus_key, unique_id):
        """Test updating a document by deleting and re-indexing."""
        doc_id = f"update_doc_{unique_id}"

        # Index original document
        original_response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Original content.",
            metadata={"version": 1},
        )
        assert original_response.success, "Setup: Original document indexing failed"

        # Delete the original document
        delete_response = client.delete_document(test_corpus_key, doc_id)
        assert delete_response.success, f"Delete failed: {delete_response.data}"

        # Re-index with updated content
        update_response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Updated content with new information.",
            metadata={"version": 2},
        )

        assert update_response.success, (
            f"Document re-index failed: {update_response.status_code} - {update_response.data}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_index_document_special_characters(self, client, test_corpus_key, unique_id):
        """Test indexing document with special characters."""
        doc_id = f"special_doc_{unique_id}"

        special_text = (
            "Testing special characters: "
            "Unicode: \u00e9\u00e8\u00ea \u00f1 \u00fc "
            "Symbols: @#$%^&*() "
            "Quotes: 'single' \"double\" "
            "Newlines:\nLine 1\nLine 2\n"
            "Tabs:\tColumn1\tColumn2"
        )

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text=special_text,
        )

        assert response.success, (
            f"Special characters document indexing failed: {response.status_code} - {response.data}"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_indexing_response_time(self, client, test_corpus_key, unique_id):
        """Test that indexing completes in acceptable time."""
        doc_id = f"perf_doc_{unique_id}"

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="Performance test document for measuring indexing speed.",
        )

        assert response.success, f"Indexing failed: {response.status_code}"
        assert response.elapsed_ms < 10000, (
            f"Indexing took too long: {response.elapsed_ms:.1f}ms"
        )

        # Cleanup
        client.delete_document(test_corpus_key, doc_id)

    def test_index_empty_document_fails(self, client, test_corpus_key, unique_id):
        """Test that indexing an empty document is handled."""
        doc_id = f"empty_doc_{unique_id}"

        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc_id,
            text="",  # Empty text
        )

        # Empty documents should either fail or be handled gracefully
        # Behavior may vary - just ensure no server error
        assert response.status_code != 500, (
            "Server error on empty document"
        )
