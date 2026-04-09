"""
Document Operations Tests

Tests for document parts listing, bulk delete, and special character handling.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestDocumentOperations:
    """Document operations tests."""

    def test_list_document_parts(self, client, test_corpus, unique_id):
        """Test that a document with multiple parts shows proper structure."""
        doc_id = f"parts_doc_{unique_id}"
        parts = [
            {"text": "First part about artificial intelligence.", "metadata": {"section": "intro"}},
            {"text": "Second part about machine learning.", "metadata": {"section": "body"}},
        ]
        index_resp = client.index_document_parts(test_corpus, doc_id, parts)
        assert index_resp.success, f"Index failed: {index_resp.status_code}"

        wait_for(
            lambda: client.get_document(test_corpus, doc_id).success,
            timeout=15, interval=1,
            description="document to be indexed",
        )

        get_resp = client.get_document(test_corpus, doc_id)
        assert get_resp.success, f"GET document failed: {get_resp.status_code} - {get_resp.data}"
        assert get_resp.data.get("id") == doc_id, \
            f"Document id mismatch: expected {doc_id}, got {get_resp.data.get('id')}"

    def test_bulk_delete_documents(self, client, test_corpus, unique_id):
        """Test bulk deleting documents by ID."""
        doc_ids = [f"bulk_{unique_id}_{i}" for i in range(3)]
        for doc_id in doc_ids:
            resp = client.index_document(test_corpus, doc_id, f"Content for {doc_id}")
            assert resp.success, f"Index {doc_id} failed: {resp.status_code}"

        wait_for(
            lambda: all(client.get_document(test_corpus, d).success for d in doc_ids),
            timeout=20, interval=2,
            description="all documents to be indexed",
        )

        delete_resp = client.bulk_delete_documents(
            test_corpus,
            document_ids=doc_ids,
            async_mode=False,
        )
        assert delete_resp.success or delete_resp.status_code == 202, \
            f"Bulk delete failed: {delete_resp.status_code} - {delete_resp.data}"

        wait_for(
            lambda: all(client.get_document(test_corpus, d).status_code == 404 for d in doc_ids),
            timeout=30, interval=2,
            description="all documents to be deleted",
        )


@pytest.mark.regression
class TestDocumentEdgeCases:
    """Document edge case tests."""

    def test_delete_document_with_special_chars(self, client, test_corpus, unique_id):
        """Test deleting a document with special characters in ID."""
        doc_id = f"doc-special-chars_{unique_id}"
        resp = client.index_document(test_corpus, doc_id, "Content with special ID")
        assert resp.success, f"Index failed: {resp.status_code}"

        wait_for(
            lambda: client.get_document(test_corpus, doc_id).success,
            timeout=15, interval=1,
            description="document to be indexed",
        )

        delete_resp = client.delete_document(test_corpus, doc_id)
        assert delete_resp.success, f"Delete failed: {delete_resp.status_code}"
