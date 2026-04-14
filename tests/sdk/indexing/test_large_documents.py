"""
Large Document Indexing Tests (SDK)

Regression-level tests for indexing large documents, multiple documents,
listing documents, and edge cases like empty documents using the Vectara Python SDK.
"""

import pytest
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


@pytest.mark.regression
class TestLargeDocuments:
    """Regression checks for large and bulk document indexing."""

    def test_index_large_document(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test indexing a larger document with multiple paragraphs."""
        doc_id = f"large_doc_{unique_id}"

        large_text = " ".join(
            [
                f"Paragraph {i}: This is test content for paragraph number {i}. "
                "It contains information about various topics including technology, "
                "science, and general knowledge. Vector databases enable semantic "
                "search capabilities that traditional keyword search cannot match."
                for i in range(20)
            ]
        )

        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[CoreDocumentPart(text=large_text)],
            ),
        )

        assert doc.id is not None, f"Index response should contain document id, got: {doc}"

    def test_index_multiple_documents(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test indexing multiple documents sequentially."""
        doc_ids = [f"multi_doc_{unique_id}_{i}" for i in range(5)]

        for i, doc_id in enumerate(doc_ids):
            doc = sdk_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(
                            text=f"Test document number {i} with unique content.",
                            metadata={"index": i},
                        ),
                    ],
                    metadata={"index": i},
                ),
            )
            assert doc.id is not None, f"Document {i} indexing failed"

        def _docs_indexed():
            docs = list(sdk_client.documents.list(sdk_shared_corpus, limit=100))
            return len(docs) >= len(doc_ids)

        wait_for(_docs_indexed, timeout=30, interval=2, description="all documents to be indexed")

        listed = list(sdk_client.documents.list(sdk_shared_corpus, limit=100))
        listed_ids = [d.id for d in listed]
        for did in doc_ids:
            assert did in listed_ids, f"Document {did} not found in listing"

    def test_list_documents(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test listing documents in a corpus."""
        doc_ids = [f"list_doc_{unique_id}_{i}" for i in range(3)]
        for doc_id in doc_ids:
            sdk_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(text=f"Document {doc_id} for listing test."),
                    ],
                ),
            )

        # Wait for indexing to complete
        wait_for(
            lambda: any(d.id in doc_ids for d in sdk_client.documents.list(sdk_shared_corpus, limit=100)),
            timeout=15,
            interval=1,
            description="indexed documents to appear in listing",
        )

        documents = list(sdk_client.documents.list(sdk_shared_corpus, limit=100))
        doc_ids_in_response = [d.id for d in documents]

        found_count = sum(1 for doc_id in doc_ids if doc_id in doc_ids_in_response)
        assert found_count > 0, f"None of the indexed documents found in list. Expected: {doc_ids}, Got: {doc_ids_in_response}"

    def test_index_empty_document_fails(self, sdk_client, sdk_shared_corpus, unique_id):
        """Test that indexing an empty document is handled."""
        doc_id = f"empty_doc_{unique_id}"

        # Empty documents should either fail or be handled gracefully
        try:
            sdk_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[CoreDocumentPart(text="")],
                ),
            )
        except Exception as e:
            # Any client error is acceptable; just ensure no 500
            assert "500" not in str(e), f"Server error on empty document: {e}"
