"""
Corpus Lifecycle Tests

Core-level tests for corpus lifecycle operations including enable/disable,
replace filter attributes, compute size, and reset.
"""

import uuid

import pytest

from utils.waiters import wait_for


@pytest.mark.core
class TestCorpusLifecycle:
    """Core checks for corpus lifecycle operations."""

    def test_enable_disable_corpus(self, client, test_corpus):
        """Disable a corpus, verify via GET, then re-enable."""
        disable_response = client.update_corpus(
            corpus_key=test_corpus,
            enabled=False,
        )
        assert disable_response.success, \
            f"Disable corpus failed: {disable_response.status_code} - {disable_response.data}"

        def corpus_is_disabled():
            resp = client.get_corpus(test_corpus)
            if resp.success and resp.data.get("enabled") is False:
                return True
            return None

        wait_for(corpus_is_disabled, timeout=10, interval=1, description="corpus to become disabled")

        get_response = client.get_corpus(test_corpus)
        assert get_response.success, f"Get corpus failed: {get_response.status_code}"
        assert get_response.data.get("enabled") is False, \
            f"Expected enabled=False, got: {get_response.data.get('enabled')}"

        enable_response = client.update_corpus(
            corpus_key=test_corpus,
            enabled=True,
        )
        assert enable_response.success, \
            f"Re-enable corpus failed: {enable_response.status_code} - {enable_response.data}"

        def corpus_is_enabled():
            resp = client.get_corpus(test_corpus)
            if resp.success and resp.data.get("enabled") is True:
                return True
            return None

        wait_for(corpus_is_enabled, timeout=10, interval=1, description="corpus to become enabled")

    def test_replace_filter_attributes(self, client, test_corpus):
        """Replace filter attributes on a corpus and verify job_id is returned."""
        response = client.replace_filter_attributes(
            corpus_key=test_corpus,
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

        assert response.success, \
            f"Replace filter attributes failed: {response.status_code} - {response.data}"
        assert response.data.get("job_id") is not None, \
            f"Expected job_id in response, got: {response.data}"

    def test_compute_corpus_size(self, client, seeded_corpus):
        """Compute size of a seeded corpus and verify fields are present and > 0."""
        response = client.compute_corpus_size(seeded_corpus)

        assert response.success, \
            f"Compute size failed: {response.status_code} - {response.data}"

        size_data = response.data
        assert size_data.get("used_docs") is not None, \
            f"Expected used_docs in response, got: {size_data}"
        assert size_data["used_docs"] > 0, \
            f"Expected used_docs > 0, got: {size_data['used_docs']}"
        assert size_data.get("used_parts") is not None, \
            f"Expected used_parts in response, got: {size_data}"
        assert size_data["used_parts"] > 0, \
            f"Expected used_parts > 0, got: {size_data['used_parts']}"

    def test_reset_corpus(self, client, seeded_corpus):
        """Reset a seeded corpus and verify all documents are gone."""
        docs_before = client.list_documents(seeded_corpus, limit=100)
        assert docs_before.success, f"List docs failed: {docs_before.status_code}"
        before_count = len(docs_before.data.get("documents", []))
        assert before_count > 0, "Seeded corpus should have documents before reset"

        reset_response = client.reset_corpus(seeded_corpus)
        assert reset_response.success, \
            f"Reset corpus failed: {reset_response.status_code} - {reset_response.data}"

        def documents_are_gone():
            resp = client.list_documents(seeded_corpus, limit=100)
            if resp.success and len(resp.data.get("documents", [])) == 0:
                return True
            return None

        wait_for(documents_are_gone, timeout=30, interval=2, description="documents to be removed after reset")

        docs_after = client.list_documents(seeded_corpus, limit=100)
        assert docs_after.success, f"List docs after reset failed: {docs_after.status_code}"
        assert len(docs_after.data.get("documents", [])) == 0, \
            f"Expected 0 documents after reset, got: {len(docs_after.data.get('documents', []))}"
