"""
Corpus Management API Tests

Tests for corpus CRUD operations including creation, retrieval,
update, and deletion of corpora.
"""

import pytest
import time


class TestCorpusManagement:
    """Test suite for corpus management operations."""

    def test_create_corpus(self, client, unique_id):
        """Test creating a new corpus."""
        response = client.create_corpus(
            name=f"Test Corpus {unique_id}",
            description="Created by API test suite",
        )

        assert response.success, (
            f"Corpus creation failed: {response.status_code} - {response.data}"
        )

        # Get the actual key returned by the API
        actual_key = response.data.get("key")
        assert actual_key, "No key returned in corpus creation response"

        # Cleanup using the actual key
        client.delete_corpus(actual_key)

    def test_create_corpus_with_metadata(self, client, unique_id):
        """Test creating a corpus with custom filter attributes."""
        response = client.create_corpus(
            name=f"Metadata Corpus {unique_id}",
            description="Corpus with filter attributes",
            filter_attributes=[
                {
                    "name": "category",
                    "level": "document",
                    "type": "text",
                },
                {
                    "name": "priority",
                    "level": "document",
                    "type": "integer",
                },
            ],
        )

        assert response.success, (
            f"Corpus creation with metadata failed: {response.status_code} - {response.data}"
        )

        # Cleanup using the actual key
        actual_key = response.data.get("key")
        if actual_key:
            client.delete_corpus(actual_key)

    def test_get_corpus(self, client, test_corpus_key):
        """Test retrieving corpus details."""
        response = client.get_corpus(test_corpus_key)

        assert response.success, (
            f"Get corpus failed: {response.status_code} - {response.data}"
        )
        assert response.data.get("key") == test_corpus_key, (
            f"Corpus key mismatch: expected {test_corpus_key}"
        )

    def test_list_corpora(self, client):
        """Test listing all corpora."""
        response = client.list_corpora(limit=100)

        assert response.success, (
            f"List corpora failed: {response.status_code} - {response.data}"
        )

        # Response should contain corpora list
        data = response.data
        assert "corpora" in data or isinstance(data, list), (
            "Expected corpora in response"
        )

    def test_list_corpora_pagination(self, client):
        """Test corpus listing with pagination."""
        # First request with small limit
        response1 = client.list_corpora(limit=2)

        assert response1.success, (
            f"Paginated list failed: {response1.status_code}"
        )

        # If there's a next page, test pagination
        if response1.data.get("metadata", {}).get("page_key"):
            page_key = response1.data["metadata"]["page_key"]
            response2 = client.list_corpora(limit=2, page_key=page_key)

            assert response2.success, (
                f"Second page request failed: {response2.status_code}"
            )

    def test_update_corpus_description(self, client, test_corpus_key):
        """Test updating corpus description."""
        new_description = f"Updated at {time.time()}"

        response = client.update_corpus(
            corpus_key=test_corpus_key,
            description=new_description,
        )

        assert response.success, (
            f"Corpus update failed: {response.status_code} - {response.data}"
        )

        # Verify update
        get_response = client.get_corpus(test_corpus_key)
        assert get_response.data.get("description") == new_description, (
            "Description update not reflected"
        )

    def test_delete_corpus(self, client, unique_id):
        """Test corpus deletion."""
        # Create corpus to delete
        create_response = client.create_corpus(
            name=f"Delete Test {unique_id}",
            description="Will be deleted",
        )
        assert create_response.success, f"Setup: Corpus creation failed: {create_response.data}"

        # Get the actual key returned by the API
        actual_key = create_response.data.get("key")
        assert actual_key, "No key returned in corpus creation response"

        # Delete the corpus using the actual key
        delete_response = client.delete_corpus(actual_key)

        assert delete_response.success, (
            f"Corpus deletion failed: {delete_response.status_code} - {delete_response.data}"
        )

        # Verify deletion - should get 404
        get_response = client.get_corpus(actual_key)
        assert get_response.status_code == 404, (
            f"Deleted corpus should return 404, got {get_response.status_code}"
        )

    def test_create_duplicate_key_corpus_fails(self, client, test_corpus_key):
        """Test that creating a corpus with an existing key fails."""
        # Attempt to create corpus with the same key as test_corpus_key
        response = client.post("/v2/corpora", data={
            "key": test_corpus_key,
            "name": "Duplicate Key Test",
        })

        # Should fail with conflict (409) or bad request (400)
        assert response.status_code in [400, 409], (
            f"Duplicate key corpus creation should fail, got {response.status_code}"
        )

    def test_get_nonexistent_corpus_returns_404(self, client):
        """Test that requesting a non-existent corpus returns 404."""
        response = client.get_corpus("nonexistent_corpus_xyz123")

        assert response.status_code == 404, (
            f"Expected 404 for non-existent corpus, got {response.status_code}"
        )

    def test_corpus_operations_response_times(self, client, test_corpus_key):
        """Test that corpus operations complete in acceptable time."""
        # Get operation should be fast
        response = client.get_corpus(test_corpus_key)

        assert response.elapsed_ms < 3000, (
            f"Get corpus took too long: {response.elapsed_ms:.1f}ms"
        )

        # List operation may take longer but should still be reasonable
        list_response = client.list_corpora(limit=10)

        assert list_response.elapsed_ms < 5000, (
            f"List corpora took too long: {list_response.elapsed_ms:.1f}ms"
        )
