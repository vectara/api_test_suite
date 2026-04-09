"""
Filter Attribute Types Tests

Test multiple filter attribute types (text, integer, boolean) working together.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.regression
class TestFilterAttributeTypes:
    """Multiple filter types on a single corpus."""

    def test_text_integer_boolean_filters(self, client, unique_id):
        """Create corpus with 3 filter types, query with each, verify correct results."""
        corpus_key = f"filter_types_{unique_id}"
        create_resp = client.create_corpus(
            name=f"Filter Types {unique_id}",
            key=corpus_key,
            filter_attributes=[
                {"name": "category", "level": "part", "type": "text", "indexed": True},
                {"name": "priority", "level": "part", "type": "integer", "indexed": True},
                {"name": "is_public", "level": "part", "type": "boolean", "indexed": True},
            ],
        )
        assert create_resp.success, f"Create corpus with filters failed: {create_resp.status_code} - {create_resp.data}"

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10, interval=1,
                description="corpus available",
            )

            doc1_id = f"tech_doc_{unique_id}"
            client.index_document(
                corpus_key, doc1_id,
                "Advanced quantum computing research enables faster drug discovery.",
                metadata={"category": "tech", "priority": 1, "is_public": True},
            )

            doc2_id = f"science_doc_{unique_id}"
            client.index_document(
                corpus_key, doc2_id,
                "Confidential climate modeling data shows accelerating ice melt patterns.",
                metadata={"category": "science", "priority": 5, "is_public": False},
            )

            wait_for(
                lambda: (
                    client.get_document(corpus_key, doc1_id).success
                    and client.get_document(corpus_key, doc2_id).success
                ),
                timeout=20, interval=2,
                description="both documents indexed",
            )

            text_query = client.post("/v2/query", data={
                "query": "research and data",
                "search": {
                    "corpora": [{"corpus_key": corpus_key, "metadata_filter": "part.category = 'tech'"}],
                    "limit": 10,
                },
            })
            assert text_query.success, f"Text filter query failed: {text_query.status_code}"
            text_results = text_query.data.get("search_results", [])
            assert len(text_results) > 0, "Text filter should return results"
            assert all("quantum" in r.get("text", "").lower() for r in text_results), \
                f"Text filter for 'tech' should only return tech doc: {[r.get('text', '')[:50] for r in text_results]}"

            int_query = client.post("/v2/query", data={
                "query": "research and data",
                "search": {
                    "corpora": [{"corpus_key": corpus_key, "metadata_filter": "part.priority >= 3"}],
                    "limit": 10,
                },
            })
            assert int_query.success, f"Integer filter query failed: {int_query.status_code}"
            int_results = int_query.data.get("search_results", [])
            assert len(int_results) > 0, "Integer filter should return results"
            assert all("climate" in r.get("text", "").lower() for r in int_results), \
                f"Integer filter >= 3 should only return science doc: {[r.get('text', '')[:50] for r in int_results]}"

            bool_query = client.post("/v2/query", data={
                "query": "research and data",
                "search": {
                    "corpora": [{"corpus_key": corpus_key, "metadata_filter": "part.is_public = true"}],
                    "limit": 10,
                },
            })
            assert bool_query.success, f"Boolean filter query failed: {bool_query.status_code}"
            bool_results = bool_query.data.get("search_results", [])
            assert len(bool_results) > 0, "Boolean filter should return results"
            assert all("quantum" in r.get("text", "").lower() for r in bool_results), \
                f"Boolean filter is_public=true should only return tech doc: {[r.get('text', '')[:50] for r in bool_results]}"
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass
