"""
Corpus CRUD Tests (SDK)

Tests for corpus create, read, update, and delete operations using the Vectara Python SDK.
Grouped by depth marker into separate classes.
"""

import time
import uuid

import pytest
from vectara.errors import ConflictError, NotFoundError


@pytest.mark.sanity
class TestCorpusCreate:
    """Corpus creation checks."""

    def test_create_corpus(self, sdk_client, unique_id):
        """Test creating a new corpus."""
        corpus_key = f"crud_test_{uuid.uuid4().hex}"
        corpus = sdk_client.corpora.create(
            name=f"Test Corpus {unique_id}",
            key=corpus_key,
            description="Created by SDK test suite",
        )

        assert corpus.key, "No key returned in corpus creation response"

        # Cleanup using the actual key
        try:
            sdk_client.corpora.delete(corpus.key)
        except Exception:
            pass


@pytest.mark.core
class TestCorpusCrud:
    """Corpus get, update, and delete checks."""

    def test_get_corpus(self, sdk_client, sdk_test_corpus):
        """Test retrieving corpus details."""
        corpus = sdk_client.corpora.get(sdk_test_corpus.key)

        assert corpus.key == sdk_test_corpus.key, f"Corpus key mismatch: expected {sdk_test_corpus.key}"

    def test_update_corpus_description(self, sdk_client, sdk_test_corpus):
        """Test updating corpus description."""
        new_description = f"Updated at {time.time()}"

        sdk_client.corpora.update(
            sdk_test_corpus.key,
            description=new_description,
        )

        # Verify update
        updated = sdk_client.corpora.get(sdk_test_corpus.key)
        assert updated.description == new_description, "Description update not reflected"

    def test_delete_corpus(self, sdk_client, unique_id):
        """Test corpus deletion."""
        corpus_key = f"del_test_{uuid.uuid4().hex}"
        corpus = sdk_client.corpora.create(
            name=f"Delete Test {unique_id}",
            key=corpus_key,
            description="Will be deleted",
        )

        actual_key = corpus.key
        assert actual_key, "No key returned in corpus creation response"

        # Delete the corpus
        sdk_client.corpora.delete(actual_key)

        # Verify deletion - should raise NotFoundError
        with pytest.raises(NotFoundError):
            sdk_client.corpora.get(actual_key)


@pytest.mark.regression
class TestCorpusErrorCases:
    """Corpus error and edge case checks."""

    def test_create_duplicate_key_corpus_fails(self, sdk_client, sdk_test_corpus):
        """Test that creating a corpus with an existing key fails."""
        with pytest.raises((ConflictError, Exception)):
            sdk_client.corpora.create(
                key=sdk_test_corpus.key,
                name="Duplicate Key Test",
            )

    def test_get_nonexistent_corpus_returns_404(self, sdk_client):
        """Test that requesting a non-existent corpus raises NotFoundError."""
        with pytest.raises(NotFoundError):
            sdk_client.corpora.get("nonexistent_corpus_xyz123")

    def test_corpus_operations_response_times(self, sdk_client, sdk_test_corpus):
        """Test that corpus operations complete in acceptable time."""
        start = time.monotonic()
        sdk_client.corpora.get(sdk_test_corpus.key)
        get_elapsed = (time.monotonic() - start) * 1000

        assert get_elapsed < 3000, f"Get corpus took too long: {get_elapsed:.1f}ms"

        start = time.monotonic()
        list(sdk_client.corpora.list(limit=10))
        list_elapsed = (time.monotonic() - start) * 1000

        assert list_elapsed < 5000, f"List corpora took too long: {list_elapsed:.1f}ms"
