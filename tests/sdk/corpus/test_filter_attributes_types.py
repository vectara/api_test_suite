"""
Filter Attribute Types Tests (SDK)

Test multiple filter attribute types (text, integer, boolean) working together
using the Vectara Python SDK.
"""

import uuid

import pytest
from vectara.corpora.types import QueryCorporaRequestSearch
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core, FilterAttribute

from utils.waiters import wait_for


@pytest.mark.regression
class TestFilterAttributeTypes:
    """Multiple filter types on a single corpus."""

    def test_text_integer_boolean_filters(self, sdk_client, unique_id):
        """Create corpus with 3 filter types, query with each, verify correct results."""
        corpus_key = f"filter_types_{unique_id}"
        corpus = sdk_client.corpora.create(
            name=f"Filter Types {unique_id}",
            key=corpus_key,
            filter_attributes=[
                FilterAttribute(name="category", level="part", type="text", indexed=True),
                FilterAttribute(name="priority", level="part", type="integer", indexed=True),
                FilterAttribute(name="is_public", level="part", type="boolean", indexed=True),
            ],
        )

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, corpus.key),
                timeout=10,
                interval=1,
                description="corpus available",
            )

            doc1_id = f"tech_doc_{unique_id}"
            sdk_client.documents.create(
                corpus.key,
                request=CreateDocumentRequest_Core(
                    id=doc1_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Advanced quantum computing research enables faster drug discovery.",
                            metadata={"category": "tech", "priority": 1, "is_public": True},
                        ),
                    ],
                ),
            )

            doc2_id = f"science_doc_{unique_id}"
            sdk_client.documents.create(
                corpus.key,
                request=CreateDocumentRequest_Core(
                    id=doc2_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Confidential climate modeling data shows accelerating ice melt patterns.",
                            metadata={"category": "science", "priority": 5, "is_public": False},
                        ),
                    ],
                ),
            )

            wait_for(
                lambda: (_document_exists(sdk_client, corpus.key, doc1_id) and _document_exists(sdk_client, corpus.key, doc2_id)),
                timeout=20,
                interval=2,
                description="both documents indexed",
            )

            # Text filter query
            text_resp = sdk_client.corpora.query(
                corpus.key,
                query="research and data",
                search=QueryCorporaRequestSearch(
                    metadata_filter="part.category = 'tech'",
                    limit=10,
                ),
            )
            text_results = text_resp.search_results or []
            assert len(text_results) > 0, "Text filter should return results"
            assert all(
                "quantum" in r.text.lower() for r in text_results
            ), f"Text filter for 'tech' should only return tech doc: {[r.text[:50] for r in text_results]}"

            # Integer filter query
            int_resp = sdk_client.corpora.query(
                corpus.key,
                query="research and data",
                search=QueryCorporaRequestSearch(
                    metadata_filter="part.priority >= 3",
                    limit=10,
                ),
            )
            int_results = int_resp.search_results or []
            assert len(int_results) > 0, "Integer filter should return results"
            assert all(
                "climate" in r.text.lower() for r in int_results
            ), f"Integer filter >= 3 should only return science doc: {[r.text[:50] for r in int_results]}"

            # Boolean filter query
            bool_resp = sdk_client.corpora.query(
                corpus.key,
                query="research and data",
                search=QueryCorporaRequestSearch(
                    metadata_filter="part.is_public = true",
                    limit=10,
                ),
            )
            bool_results = bool_resp.search_results or []
            assert len(bool_results) > 0, "Boolean filter should return results"
            assert all(
                "quantum" in r.text.lower() for r in bool_results
            ), f"Boolean filter is_public=true should only return tech doc: {[r.text[:50] for r in bool_results]}"
        finally:
            try:
                sdk_client.corpora.delete(corpus.key)
            except Exception:
                pass


def _corpus_exists(sdk_client, corpus_key):
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False
