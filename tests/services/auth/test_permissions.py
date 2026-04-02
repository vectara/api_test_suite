"""
Permission Tests

Core-level checks that the API key has the correct permissions
for QueryService and IndexService operations, and that basic
corpus listing works.
"""

import pytest


@pytest.mark.core
class TestPermissions:
    """Core checks for API key permissions."""

    def test_api_key_has_query_permission(self, client, test_corpus, sample_document):
        """Test that API key has QueryService permission."""
        # First index a document to ensure there's something to query
        doc_response = client.index_document(
            corpus_key=test_corpus,
            document_id="auth_test_doc",
            text=sample_document["text"],
            metadata=sample_document["metadata"],
        )

        # Now test query permission
        response = client.query(
            corpus_key=test_corpus,
            query_text="test query",
            limit=1,
        )

        assert response.success, (
            f"QueryService permission check failed: {response.status_code}. "
            f"Ensure API key has QueryService role enabled."
        )

    def test_api_key_has_index_permission(self, client, test_corpus):
        """Test that API key has IndexService permission."""
        response = client.index_document(
            corpus_key=test_corpus,
            document_id="auth_permission_test",
            text="Testing IndexService permission",
        )

        assert response.success, (
            f"IndexService permission check failed: {response.status_code}. "
            f"Ensure API key has IndexService role enabled."
        )

    def test_list_corpora_works(self, client):
        """Test basic corpus listing (requires valid authentication)."""
        response = client.list_corpora(limit=10)

        assert response.success, (
            f"List corpora failed: {response.status_code} - {response.data}"
        )
        assert "corpora" in response.data or isinstance(response.data, list), (
            "Expected corpora list in response"
        )
