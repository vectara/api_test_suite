"""
Document Lifecycle Tests (SDK)

Full lifecycle: index -> query finds it -> delete -> query no longer finds it.
Uses the Vectara Python SDK.
"""

import pytest

from vectara.errors import NotFoundError
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


@pytest.mark.core
class TestDocumentLifecycle:
    """Document lifecycle with query verification."""

    def test_index_query_delete_query_cycle(self, sdk_client, sdk_test_corpus, unique_id):
        """Index a doc, verify query finds it, delete it, verify query no longer finds it."""
        corpus_key = sdk_test_corpus.key
        doc_id = f"lifecycle_{unique_id}"
        doc_text = "The Krakatoa volcano erupted in 1883 causing massive tsunamis across the Indian Ocean."

        sdk_client.documents.create(
            corpus_key,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[CoreDocumentPart(text=doc_text)],
            ),
        )

        wait_for(
            lambda: _document_exists(sdk_client, corpus_key, doc_id),
            timeout=15,
            interval=1,
            description="document to be indexed",
        )

        query_resp = sdk_client.corpora.search(corpus_key, query="Krakatoa volcano eruption", limit=10)
        results = query_resp.search_results or []
        found = any("krakatoa" in r.text.lower() for r in results)
        assert found, f"Expected to find Krakatoa doc in results, got {len(results)} results"

        sdk_client.documents.delete(corpus_key, doc_id)

        wait_for(
            lambda: _document_gone(sdk_client, corpus_key, doc_id),
            timeout=15,
            interval=1,
            description="document to be deleted",
        )

        def _krakatoa_gone():
            qr = sdk_client.corpora.search(corpus_key, query="Krakatoa volcano eruption", limit=10)
            hits = qr.search_results or []
            return not any("krakatoa" in r.text.lower() for r in hits)

        wait_for(_krakatoa_gone, timeout=30, interval=3, description="Krakatoa to disappear from search")

        final_query = sdk_client.corpora.search(corpus_key, query="Krakatoa volcano eruption", limit=10)
        final_results = final_query.search_results or []
        assert not any(
            "krakatoa" in r.text.lower() for r in final_results
        ), f"Deleted doc should not appear in results, but found Krakatoa in {len(final_results)} results"


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False


def _document_gone(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return False
    except NotFoundError:
        return True
    except Exception:
        return False
