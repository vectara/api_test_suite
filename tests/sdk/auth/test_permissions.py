"""
Permission Tests (SDK)

Core-level checks that the SDK client has the correct permissions
for query and index operations, and that basic corpus listing works.
"""

import uuid

import pytest
from vectara.types import (
    CoreDocumentPart,
    CreateDocumentRequest_Core,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)


@pytest.mark.core
class TestPermissions:
    """Core checks for API key permissions via SDK."""

    def test_sdk_client_has_query_permission(self, sdk_client, sdk_shared_corpus):
        """Test that SDK client can query (has QueryService permission)."""
        # Index a document first
        doc_id = f"auth_test_doc_{uuid.uuid4().hex[:8]}"
        try:
            sdk_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Test document for permission check",
                            metadata={"source": "test_suite"},
                        )
                    ],
                ),
            )
        except Exception:
            pass  # Document might already exist

        # Test query permission
        result = sdk_client.corpora.search(
            corpus_key=sdk_shared_corpus,
            query="test query",
            limit=1,
        )
        assert result is not None, "Query should return a result"

    def test_sdk_client_has_index_permission(self, sdk_client, sdk_shared_corpus):
        """Test that SDK client can index (has IndexService permission)."""
        doc_id = f"auth_permission_test_{uuid.uuid4().hex[:8]}"
        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text="Testing IndexService permission via SDK",
                    )
                ],
            ),
        )
        assert doc is not None, "Index response should not be None"

    def test_list_corpora_works(self, sdk_client):
        """Test basic corpus listing (requires valid authentication)."""
        pager = sdk_client.corpora.list(limit=10)
        corpora = list(pager)
        assert isinstance(corpora, list), "Expected corpora list"
