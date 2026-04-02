"""
Corpus CRUD Tests

Tests for corpus create, read, update, and delete operations.
Grouped by depth marker into separate classes.
"""

import pytest
import time


@pytest.mark.sanity
class TestCorpusCreate:
    """Corpus creation checks."""

    def test_create_corpus(self, client, unique_id):
        """Test creating a new corpus."""
        import uuid
        corpus_key = f"crud_test_{uuid.uuid4().hex}"
        response = client.create_corpus(
            name=f"Test Corpus {unique_id}",
            key=corpus_key,
            description="Created by API test suite",
        )

        assert response.success, (
            f"Corpus creation failed: {response.status_code} - {response.data}"
        )

        # Get the actual key returned by the API
        actual_key = response.data.get("key")
        assert actual_key, "No key returned in corpus creation response"

        # Cleanup using the actual key
        try:
            client.delete_corpus(actual_key)
        except Exception:
            pass


@pytest.mark.core
class TestCorpusCrud:
    """Corpus get, update, and delete checks."""

    def test_get_corpus(self, client, test_corpus):
        """Test retrieving corpus details."""
        response = client.get_corpus(test_corpus)

        assert response.success, (
            f"Get corpus failed: {response.status_code} - {response.data}"
        )
        assert response.data.get("key") == test_corpus, (
            f"Corpus key mismatch: expected {test_corpus}"
        )

    def test_update_corpus_description(self, client, test_corpus):
        """Test updating corpus description."""
        new_description = f"Updated at {time.time()}"

        response = client.update_corpus(
            corpus_key=test_corpus,
            description=new_description,
        )

        assert response.success, (
            f"Corpus update failed: {response.status_code} - {response.data}"
        )

        # Verify update
        get_response = client.get_corpus(test_corpus)
        assert get_response.data.get("description") == new_description, (
            "Description update not reflected"
        )

    def test_delete_corpus(self, client, unique_id):
        """Test corpus deletion."""
        import uuid
        corpus_key = f"del_test_{uuid.uuid4().hex}"
        # Create corpus to delete
        create_response = client.create_corpus(
            name=f"Delete Test {unique_id}",
            key=corpus_key,
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


@pytest.mark.regression
class TestCorpusErrorCases:
    """Corpus error and edge case checks."""

    def test_create_duplicate_key_corpus_fails(self, client, test_corpus):
        """Test that creating a corpus with an existing key fails."""
        # Attempt to create corpus with the same key as test_corpus
        response = client.post("/v2/corpora", data={
            "key": test_corpus,
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

    def test_corpus_operations_response_times(self, client, test_corpus):
        """Test that corpus operations complete in acceptable time."""
        # Get operation should be fast
        response = client.get_corpus(test_corpus)

        assert response.elapsed_ms < 3000, (
            f"Get corpus took too long: {response.elapsed_ms:.1f}ms"
        )

        # List operation may take longer but should still be reasonable
        list_response = client.list_corpora(limit=10)

        assert list_response.elapsed_ms < 5000, (
            f"List corpora took too long: {list_response.elapsed_ms:.1f}ms"
        )
