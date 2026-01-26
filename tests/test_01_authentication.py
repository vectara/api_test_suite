"""
Authentication API Tests

Tests for verifying API key authentication and authorization.
Validates that the provided API key has correct permissions for
QueryService and IndexService operations.
"""

import pytest


class TestAuthentication:
    """Test suite for authentication and authorization."""

    def test_api_key_valid(self, client):
        """Test that the API key is valid and can connect."""
        response = client.health_check()

        assert response.success, (
            f"API authentication failed: {response.status_code} - {response.data}"
        )

    def test_api_key_has_query_permission(self, client, test_corpus_key, sample_document):
        """Test that API key has QueryService permission."""
        # First index a document to ensure there's something to query
        doc_response = client.index_document(
            corpus_key=test_corpus_key,
            document_id="auth_test_doc",
            text=sample_document["text"],
            metadata=sample_document["metadata"],
        )

        # Now test query permission
        response = client.query(
            corpus_key=test_corpus_key,
            query_text="test query",
            limit=1,
        )

        assert response.success, (
            f"QueryService permission check failed: {response.status_code}. "
            f"Ensure API key has QueryService role enabled."
        )

    def test_api_key_has_index_permission(self, client, test_corpus_key):
        """Test that API key has IndexService permission."""
        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id="auth_permission_test",
            text="Testing IndexService permission",
        )

        assert response.success, (
            f"IndexService permission check failed: {response.status_code}. "
            f"Ensure API key has IndexService role enabled."
        )

        # Cleanup
        client.delete_document(test_corpus_key, "auth_permission_test")

    def test_invalid_api_key_rejected(self, config):
        """Test that invalid API keys are properly rejected."""
        from utils.client import VectaraClient

        # Create client with invalid key
        invalid_config = Config()
        invalid_config.set_api_key("invalid_key_12345")

        invalid_client = VectaraClient(invalid_config)
        response = invalid_client.health_check()

        assert not response.success, (
            "Invalid API key should be rejected"
        )
        assert response.status_code in [401, 403], (
            f"Expected 401 or 403 for invalid key, got {response.status_code}"
        )

    def test_response_time_acceptable(self, client):
        """Test that authentication response time is acceptable."""
        response = client.health_check()

        # Authentication should complete within 5 seconds
        assert response.elapsed_ms < 5000, (
            f"Authentication took too long: {response.elapsed_ms:.1f}ms"
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


# Import Config for the invalid key test
from utils.config import Config
