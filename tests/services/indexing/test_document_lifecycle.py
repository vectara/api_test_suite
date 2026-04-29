"""
Document Lifecycle Tests

Full lifecycle: index → query finds it → delete → query no longer finds it.
"""

import pytest

from utils.waiters import wait_for


@pytest.mark.core
class TestDocumentLifecycle:
    """Document lifecycle with query verification."""

    def test_index_query_delete_query_cycle(self, client, test_corpus, unique_id):
        """Index a doc, verify query finds it, delete it, verify query no longer finds it."""
        doc_id = f"lifecycle_{unique_id}"
        doc_text = "The Krakatoa volcano erupted in 1883 causing massive tsunamis across the Indian Ocean."

        index_resp = client.index_document(test_corpus, doc_id, doc_text)
        assert index_resp.success, f"Index failed: {index_resp.status_code} - {index_resp.data}"

        wait_for(
            lambda: client.get_document(test_corpus, doc_id).success,
            timeout=15,
            interval=1,
            description="document to be indexed",
        )

        def _krakatoa_in_results():
            qr = client.query(test_corpus, "Krakatoa volcano eruption", limit=10)
            if not qr.success:
                return None
            hits = qr.data.get("search_results", [])
            if any("krakatoa" in r.get("text", "").lower() for r in hits):
                return qr
            return None

        query_resp = wait_for(
            _krakatoa_in_results,
            timeout=30,
            interval=2,
            description="Krakatoa to appear in search",
        )
        assert query_resp.success, f"Query failed: {query_resp.status_code}"
        results = query_resp.data.get("search_results", [])
        found = any("krakatoa" in r.get("text", "").lower() for r in results)
        assert found, f"Expected to find Krakatoa doc in results, got {len(results)} results"

        delete_resp = client.delete_document(test_corpus, doc_id)
        assert delete_resp.success, f"Delete failed: {delete_resp.status_code}"

        wait_for(
            lambda: client.get_document(test_corpus, doc_id).status_code == 404,
            timeout=15,
            interval=1,
            description="document to be deleted",
        )

        def _krakatoa_gone():
            qr = client.query(test_corpus, "Krakatoa volcano eruption", limit=10)
            if not qr.success:
                return False
            hits = qr.data.get("search_results", [])
            return not any("krakatoa" in r.get("text", "").lower() for r in hits)

        wait_for(_krakatoa_gone, timeout=30, interval=3, description="Krakatoa to disappear from search")

        final_query = client.query(test_corpus, "Krakatoa volcano eruption", limit=10)
        assert final_query.success
        final_results = final_query.data.get("search_results", [])
        assert not any(
            "krakatoa" in r.get("text", "").lower() for r in final_results
        ), f"Deleted doc should not appear in results, but found Krakatoa in {len(final_results)} results"
