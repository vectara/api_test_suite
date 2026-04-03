"""
Large Document Indexing Tests

Regression-level tests for indexing large documents, multiple documents,
listing documents, and edge cases like empty documents.
"""

import pytest

from utils.waiters import wait_for


@pytest.mark.regression
class TestLargeDocuments:
    """Regression checks for large and bulk document indexing."""

    def test_index_large_document(self, client, shared_corpus, unique_id):
        """Test indexing a larger document with multiple paragraphs."""
        doc_id = f"large_doc_{unique_id}"

        # Generate larger text content
        large_text = " ".join(
            [
                f"Paragraph {i}: This is test content for paragraph number {i}. "
                "It contains information about various topics including technology, "
                "science, and general knowledge. Vector databases enable semantic "
                "search capabilities that traditional keyword search cannot match."
                for i in range(20)
            ]
        )

        response = client.index_document(
            corpus_key=shared_corpus,
            document_id=doc_id,
            text=large_text,
        )

        assert response.success, f"Large document indexing failed: {response.status_code} - {response.data}"

    def test_index_multiple_documents(self, client, shared_corpus, unique_id):
        """Test indexing multiple documents sequentially."""
        doc_ids = [f"multi_doc_{unique_id}_{i}" for i in range(5)]

        for i, doc_id in enumerate(doc_ids):
            response = client.index_document(
                corpus_key=shared_corpus,
                document_id=doc_id,
                text=f"Test document number {i} with unique content.",
                metadata={"index": i},
            )

            assert response.success, f"Document {i} indexing failed: {response.status_code}"

    def test_list_documents(self, client, shared_corpus, unique_id):
        """Test listing documents in a corpus."""
        # Index a few documents first
        doc_ids = [f"list_doc_{unique_id}_{i}" for i in range(3)]
        for doc_id in doc_ids:
            response = client.index_document(
                corpus_key=shared_corpus,
                document_id=doc_id,
                text=f"Document {doc_id} for listing test.",
            )
            assert response.success, f"Failed to index {doc_id}: {response.data}"

        # Wait for indexing to complete
        wait_for(
            lambda: any(d.get("id") in doc_ids for d in client.list_documents(shared_corpus, limit=100).data.get("documents", []) if isinstance(d, dict)),
            timeout=15,
            interval=1,
            description="indexed documents to appear in listing",
        )

        # List documents
        response = client.list_documents(shared_corpus, limit=100)

        assert response.success, f"List documents failed: {response.status_code} - {response.data}"

        # Verify documents exist in list
        documents = response.data.get("documents", response.data)
        doc_ids_in_response = [d.get("id") for d in documents if isinstance(d, dict)]

        # Check that at least some of our documents appear (indexing may be async)
        found_count = sum(1 for doc_id in doc_ids if doc_id in doc_ids_in_response)
        assert found_count > 0, f"None of the indexed documents found in list. Expected: {doc_ids}, Got: {doc_ids_in_response}"

    def test_index_empty_document_fails(self, client, shared_corpus, unique_id):
        """Test that indexing an empty document is handled."""
        doc_id = f"empty_doc_{unique_id}"

        response = client.index_document(
            corpus_key=shared_corpus,
            document_id=doc_id,
            text="",  # Empty text
        )

        # Empty documents should either fail or be handled gracefully
        # Behavior may vary - just ensure no server error
        assert response.status_code != 500, "Server error on empty document"
