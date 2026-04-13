"""
Corpus Lifecycle Tests (SDK)

Core-level tests for corpus lifecycle operations including enable/disable,
replace filter attributes, compute size, and reset.
"""

import pytest

from vectara.types import FilterAttribute

from utils.waiters import wait_for


@pytest.mark.core
class TestCorpusLifecycle:
    """Core checks for corpus lifecycle operations."""

    def test_enable_disable_corpus(self, sdk_client, sdk_test_corpus):
        """Disable a corpus, verify via GET, then re-enable."""
        corpus_key = sdk_test_corpus.key

        sdk_client.corpora.update(corpus_key, enabled=False)

        def corpus_is_disabled():
            c = sdk_client.corpora.get(corpus_key)
            if c.enabled is False:
                return True
            return None

        wait_for(corpus_is_disabled, timeout=10, interval=1, description="corpus to become disabled")

        disabled = sdk_client.corpora.get(corpus_key)
        assert disabled.enabled is False, f"Expected enabled=False, got: {disabled.enabled}"

        sdk_client.corpora.update(corpus_key, enabled=True)

        def corpus_is_enabled():
            c = sdk_client.corpora.get(corpus_key)
            if c.enabled is True:
                return True
            return None

        wait_for(corpus_is_enabled, timeout=10, interval=1, description="corpus to become enabled")

    def test_replace_filter_attributes(self, sdk_client, sdk_test_corpus):
        """Replace filter attributes on a corpus and verify job_id is returned."""
        response = sdk_client.corpora.replace_filter_attributes(
            sdk_test_corpus.key,
            filter_attributes=[
                FilterAttribute(name="category", level="document", type="text"),
                FilterAttribute(name="priority", level="document", type="integer"),
            ],
        )

        assert response.job_id is not None, f"Expected job_id in response, got: {response}"

    def test_compute_corpus_size(self, sdk_client, sdk_seeded_corpus):
        """Compute size of a seeded corpus and verify fields are present and > 0."""
        response = sdk_client.corpora.compute_size(sdk_seeded_corpus.key)

        assert response.used_docs is not None, f"Expected used_docs in response, got: {response}"
        assert response.used_docs > 0, f"Expected used_docs > 0, got: {response.used_docs}"
        assert response.used_parts is not None, f"Expected used_parts in response, got: {response}"
        assert response.used_parts > 0, f"Expected used_parts > 0, got: {response.used_parts}"

    def test_reset_corpus(self, sdk_client, sdk_seeded_corpus):
        """Reset a seeded corpus and verify all documents are gone."""
        corpus_key = sdk_seeded_corpus.key

        docs_before = list(sdk_client.documents.list(corpus_key, limit=100))
        assert len(docs_before) > 0, "Seeded corpus should have documents before reset"

        sdk_client.corpora.reset(corpus_key)

        def documents_are_gone():
            docs = list(sdk_client.documents.list(corpus_key, limit=100))
            if len(docs) == 0:
                return True
            return None

        wait_for(documents_are_gone, timeout=30, interval=2, description="documents to be removed after reset")

        docs_after = list(sdk_client.documents.list(corpus_key, limit=100))
        assert len(docs_after) == 0, f"Expected 0 documents after reset, got: {len(docs_after)}"
