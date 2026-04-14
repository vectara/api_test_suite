"""
Upload Edge Case Tests (SDK)

Tests for file upload error handling and metadata attachment including
uploads with metadata, uploads to non-existent corpora, and uploads
without a proper filename using the Vectara Python SDK.
"""

import os
import tempfile

import pytest

from vectara.errors import NotFoundError

from utils.waiters import wait_for


@pytest.mark.core
class TestUploadWithMetadata:
    """Core tests for file upload with metadata."""

    def test_upload_with_metadata_fields(self, sdk_client, sdk_test_corpus):
        """Upload a file with metadata, wait for indexing, GET doc, and verify metadata."""
        corpus_key = sdk_test_corpus.key

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Semantic search uses vector embeddings to find relevant documents.")
            temp_path = f.name

        try:
            metadata = {"author": "test_suite", "category": "technology", "version": "1"}

            with open(temp_path, "rb") as fh:
                content = fh.read()
            doc = sdk_client.upload.file(
                corpus_key,
                file=("test_metadata.txt", content, "text/plain"),
                metadata=metadata,
            )
            assert doc.id, f"No document ID in upload response: {doc}"

            wait_for(
                lambda: _document_exists(sdk_client, corpus_key, doc.id),
                timeout=15,
                interval=1,
                description="uploaded file to appear as document",
            )

            fetched = sdk_client.documents.get(corpus_key, doc.id)
            doc_metadata = fetched.metadata or {}
            assert doc_metadata.get("author") == "test_suite", f"Expected author='test_suite' in metadata, got: {doc_metadata}"
            assert doc_metadata.get("category") == "technology", f"Expected category='technology' in metadata, got: {doc_metadata}"
        finally:
            os.unlink(temp_path)


@pytest.mark.regression
class TestUploadErrors:
    """Regression tests for file upload error cases."""

    def test_upload_to_nonexistent_corpus_returns_404(self, sdk_client):
        """Upload a file to a non-existent corpus key and expect NotFoundError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This file should not be indexed anywhere.")
            temp_path = f.name

        try:
            with pytest.raises(NotFoundError):
                with open(temp_path, "rb") as fh:
                    content = fh.read()
                sdk_client.upload.file(
                    "nonexistent_corpus_xyz123",
                    file=("test.txt", content, "text/plain"),
                )
        finally:
            os.unlink(temp_path)

    def test_upload_without_filename_returns_error(self, sdk_client, sdk_test_corpus):
        """Upload without a proper file to verify the API rejects it."""
        corpus_key = sdk_test_corpus.key

        with pytest.raises(Exception):
            sdk_client.upload.file(
                corpus_key,
                file=b"",
            )


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False
