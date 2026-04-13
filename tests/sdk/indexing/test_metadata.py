"""
Document Metadata Indexing Tests (SDK)

Core-level tests for indexing documents with custom metadata,
special characters, and verifying indexing response times using the Vectara Python SDK.
"""

import time

import pytest

from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


@pytest.mark.core
class TestDocumentMetadata:
    """Core checks for document metadata indexing."""

    def test_index_document_with_metadata(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test indexing a document with custom metadata."""
        doc_id = f"meta_doc_{unique_id}"

        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Document with rich metadata for testing."),
                ],
                metadata={
                    "author": "Test Suite",
                    "category": "technology",
                    "priority": 1,
                    "tags": ["test", "api", "indexing"],
                    "timestamp": time.time(),
                },
            ),
        )

        wait_for(
            lambda: _document_exists(sdk_client, sdk_shared_corpus, doc_id),
            timeout=15,
            interval=1,
            description="document to be available",
        )

        fetched = sdk_client.documents.get(sdk_shared_corpus, doc_id)
        assert fetched.id == doc_id, f"Document id mismatch: expected {doc_id}, got {fetched.id}"

    def test_index_document_special_characters(self, sdk_client, sdk_shared_corpus, unique_id):
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

        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[CoreDocumentPart(text=special_text)],
            ),
        )

        assert doc.id is not None, f"Index response should contain document id, got: {doc}"

    def test_indexing_response_time(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test that indexing completes in acceptable time."""
        doc_id = f"perf_doc_{unique_id}"

        start = time.monotonic()
        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Performance test document for measuring indexing speed."),
                ],
            ),
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        assert doc.id is not None, "Indexing failed"
        assert elapsed_ms < 10000, f"Indexing took too long: {elapsed_ms:.1f}ms"


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False
