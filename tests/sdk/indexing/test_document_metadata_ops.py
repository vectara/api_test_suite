"""
Document Metadata Operations Tests (SDK)

Tests for document metadata PATCH (merge) and PUT (replace) operations,
as well as multipart document indexing using the Vectara Python SDK.
"""

import pytest

from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core


@pytest.mark.core
class TestDocumentMetadataOps:
    """Core tests for document metadata update operations."""

    def test_index_multipart_document(self, sdk_client, sdk_shared_corpus, unique_id):
        """Index a document with multiple parts and metadata."""
        doc_id = f"multipart_{unique_id}"
        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text="This is the first part about artificial intelligence.",
                        metadata={"section": "intro", "importance": "high"},
                    ),
                    CoreDocumentPart(
                        text="This is the second part about machine learning applications.",
                        metadata={"section": "details", "importance": "medium"},
                    ),
                ],
                metadata={"title": "AI Overview", "lang": "en"},
            ),
        )
        assert doc.id is not None, "Multipart index should return document id"

        # Verify document was indexed with correct metadata
        fetched = sdk_client.documents.get(sdk_shared_corpus, doc_id)
        doc_metadata = fetched.metadata or {}
        assert doc_metadata.get("title") == "AI Overview", f"Expected title 'AI Overview', got: {doc_metadata}"

        # Cleanup
        try:
            sdk_client.documents.delete(sdk_shared_corpus, doc_id)
        except Exception:
            pass

    def test_patch_document_metadata(self, sdk_client, sdk_shared_corpus, unique_id):
        """PATCH document metadata -- should merge with existing."""
        doc_id = f"patch_meta_{unique_id}"
        # Index with initial metadata
        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Document for metadata patching."),
                ],
                metadata={"title": "Original", "lang": "en"},
            ),
        )

        # PATCH with new key (update merges metadata)
        patched = sdk_client.documents.update(
            sdk_shared_corpus,
            doc_id,
            metadata={"new_key": "new_value"},
        )

        patched_metadata = patched.metadata or {}
        assert "new_key" in str(patched_metadata), f"New key not in PATCH response: {patched_metadata}"

        # Verify via GET that new key is persisted
        fetched = sdk_client.documents.get(sdk_shared_corpus, doc_id)
        doc_metadata = fetched.metadata or {}
        assert doc_metadata.get("new_key") == "new_value", f"New key not persisted after PATCH: {doc_metadata}"

        # Cleanup
        try:
            sdk_client.documents.delete(sdk_shared_corpus, doc_id)
        except Exception:
            pass

    def test_replace_document_metadata(self, sdk_client, sdk_shared_corpus, unique_id):
        """PUT document metadata -- should replace entirely."""
        doc_id = f"replace_meta_{unique_id}"
        # Index with initial metadata
        sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(text="Document for metadata replacement."),
                ],
                metadata={"title": "Original", "lang": "en", "extra": "will_be_removed"},
            ),
        )

        # PUT replaces all metadata
        new_metadata = {"title": "Replaced", "lang": "fr"}
        replaced = sdk_client.documents.update_metadata(
            sdk_shared_corpus,
            doc_id,
            metadata=new_metadata,
        )

        # Verify: PUT replaces entirely -- old keys removed, new keys present
        fetched = sdk_client.documents.get(sdk_shared_corpus, doc_id)
        doc_metadata = fetched.metadata or {}
        assert doc_metadata.get("title") == "Replaced", f"Title not replaced: {doc_metadata}"
        assert doc_metadata.get("lang") == "fr", f"Lang not updated: {doc_metadata}"
        assert "extra" not in doc_metadata, f"Old 'extra' key should be removed after PUT: {doc_metadata}"

        # Cleanup
        try:
            sdk_client.documents.delete(sdk_shared_corpus, doc_id)
        except Exception:
            pass
