"""
Document Metadata Operations Tests

Tests for document metadata PATCH (merge) and PUT (replace) operations,
as well as multipart document indexing.
"""

import pytest


@pytest.mark.core
class TestDocumentMetadataOps:
    """Core tests for document metadata update operations."""

    def test_index_multipart_document(self, client, shared_corpus, unique_id):
        """Index a document with multiple parts and metadata."""
        doc_id = f"multipart_{unique_id}"
        parts = [
            {
                "text": "This is the first part about artificial intelligence.",
                "metadata": {"section": "intro", "importance": "high"},
            },
            {
                "text": "This is the second part about machine learning applications.",
                "metadata": {"section": "details", "importance": "medium"},
            },
        ]
        response = client.index_document_parts(
            corpus_key=shared_corpus,
            document_id=doc_id,
            parts=parts,
            metadata={"title": "AI Overview", "lang": "en"},
        )
        assert response.success, f"Multipart index failed: {response.status_code} - {response.data}"

        # Verify document was indexed with correct metadata
        get_resp = client.get_document(shared_corpus, doc_id)
        assert get_resp.success, f"Get indexed doc failed: {get_resp.data}"
        doc_metadata = get_resp.data.get("metadata", {})
        assert doc_metadata.get("title") == "AI Overview", f"Expected title 'AI Overview', got: {doc_metadata}"

        # Cleanup
        try:
            client.delete_document(shared_corpus, doc_id)
        except Exception:
            pass

    def test_patch_document_metadata(self, client, shared_corpus, unique_id):
        """PATCH document metadata -- should merge with existing."""
        doc_id = f"patch_meta_{unique_id}"
        # Index with initial metadata
        client.index_document(
            corpus_key=shared_corpus,
            document_id=doc_id,
            text="Document for metadata patching.",
            metadata={"title": "Original", "lang": "en"},
        )

        # PATCH with new key
        response = client.update_document_metadata(
            corpus_key=shared_corpus,
            document_id=doc_id,
            metadata={"new_key": "new_value"},
        )
        assert response.success, f"PATCH metadata failed: {response.status_code} - {response.data}"

        # Verify PATCH response contains the new key
        patched = response.data.get("metadata", response.data)
        assert "new_key" in str(patched), f"New key not in PATCH response: {patched}"

        # Verify via GET that new key is persisted
        get_resp = client.get_document(shared_corpus, doc_id)
        assert get_resp.success, f"Get doc after PATCH failed: {get_resp.data}"
        doc_metadata = get_resp.data.get("metadata", {})
        assert doc_metadata.get("new_key") == "new_value", f"New key not persisted after PATCH: {doc_metadata}"

        # Cleanup
        try:
            client.delete_document(shared_corpus, doc_id)
        except Exception:
            pass

    def test_replace_document_metadata(self, client, shared_corpus, unique_id):
        """PUT document metadata -- should replace entirely."""
        doc_id = f"replace_meta_{unique_id}"
        # Index with initial metadata
        client.index_document(
            corpus_key=shared_corpus,
            document_id=doc_id,
            text="Document for metadata replacement.",
            metadata={"title": "Original", "lang": "en", "extra": "will_be_removed"},
        )

        # PUT replaces all metadata
        new_metadata = {"title": "Replaced", "lang": "fr"}
        response = client.replace_document_metadata(
            corpus_key=shared_corpus,
            document_id=doc_id,
            metadata=new_metadata,
        )
        assert response.success, f"PUT metadata failed: {response.status_code} - {response.data}"

        # Verify: PUT replaces entirely — old keys removed, new keys present
        get_response = client.get_document(shared_corpus, doc_id)
        assert get_response.success, f"Get doc after PUT failed: {get_response.data}"
        doc_metadata = get_response.data.get("metadata", {})
        assert doc_metadata.get("title") == "Replaced", f"Title not replaced: {doc_metadata}"
        assert doc_metadata.get("lang") == "fr", f"Lang not updated: {doc_metadata}"
        assert "extra" not in doc_metadata, f"Old 'extra' key should be removed after PUT: {doc_metadata}"

        # Cleanup
        try:
            client.delete_document(shared_corpus, doc_id)
        except Exception:
            pass
