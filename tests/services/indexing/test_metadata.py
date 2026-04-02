"""
Document Metadata Indexing Tests

Core-level tests for indexing documents with custom metadata,
special characters, and verifying indexing response times.
"""

import pytest
import time


@pytest.mark.core
class TestDocumentMetadata:
    """Core checks for document metadata indexing."""

    def test_index_document_with_metadata(self, client, shared_corpus, unique_id):
        """Test indexing a document with custom metadata."""
        doc_id = f"meta_doc_{unique_id}"

        response = client.index_document(
            corpus_key=shared_corpus,
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

    def test_index_document_special_characters(self, client, shared_corpus, unique_id):
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
            corpus_key=shared_corpus,
            document_id=doc_id,
            text=special_text,
        )

        assert response.success, (
            f"Special characters document indexing failed: {response.status_code} - {response.data}"
        )

    def test_indexing_response_time(self, client, shared_corpus, unique_id):
        """Test that indexing completes in acceptable time."""
        doc_id = f"perf_doc_{unique_id}"

        response = client.index_document(
            corpus_key=shared_corpus,
            document_id=doc_id,
            text="Performance test document for measuring indexing speed.",
        )

        assert response.success, f"Indexing failed: {response.status_code}"
        assert response.elapsed_ms < 10000, (
            f"Indexing took too long: {response.elapsed_ms:.1f}ms"
        )
