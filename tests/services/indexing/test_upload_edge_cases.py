"""
Upload Edge Case Tests

Tests for file upload error handling and metadata attachment including
uploads with metadata, uploads to non-existent corpora, and uploads
without a proper filename.
"""

import os
import tempfile

import pytest

from utils.waiters import wait_for


@pytest.mark.core
class TestUploadWithMetadata:
    """Core tests for file upload with metadata."""

    def test_upload_with_metadata_fields(self, client, test_corpus):
        """Upload a file with metadata, wait for indexing, GET doc, and verify metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Semantic search uses vector embeddings to find relevant documents.")
            temp_path = f.name

        try:
            metadata = {"author": "test_suite", "category": "technology", "version": "1"}

            response = client.upload_file(
                corpus_key=test_corpus,
                file_path=temp_path,
                metadata=metadata,
            )
            assert response.success, f"File upload failed: {response.status_code} - {response.data}"

            doc_id = response.data.get("id")
            assert doc_id, f"No document ID in upload response: {response.data}"

            wait_for(
                lambda: client.get_document(test_corpus, doc_id).success,
                timeout=15,
                interval=1,
                description="uploaded file to appear as document",
            )

            doc_response = client.get_document(test_corpus, doc_id)
            assert doc_response.success, f"Get document failed: {doc_response.status_code} - {doc_response.data}"

            doc_metadata = doc_response.data.get("metadata", {})
            assert doc_metadata.get("author") == "test_suite", f"Expected author='test_suite' in metadata, got: {doc_metadata}"
            assert doc_metadata.get("category") == "technology", f"Expected category='technology' in metadata, got: {doc_metadata}"
        finally:
            os.unlink(temp_path)


@pytest.mark.regression
class TestUploadErrors:
    """Regression tests for file upload error cases."""

    def test_upload_to_nonexistent_corpus_returns_404(self, client):
        """Upload a file to a non-existent corpus key and expect 404."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This file should not be indexed anywhere.")
            temp_path = f.name

        try:
            response = client.upload_file(
                corpus_key="nonexistent_corpus_xyz123",
                file_path=temp_path,
            )
            assert response.status_code == 404, f"Expected 404 for non-existent corpus, got {response.status_code} - {response.data}"
        finally:
            os.unlink(temp_path)

    def test_upload_without_filename_returns_400(self, client, test_corpus):
        """Upload without a proper file to verify the API rejects it."""
        response = client.post(
            f"/v2/corpora/{test_corpus}/upload_file",
            data={},
        )

        assert response.status_code in (400, 415, 422), f"Expected 400/415/422 for upload without file, got {response.status_code} - {response.data}"
