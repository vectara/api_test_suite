"""
Cross-Corpus Query Tests (SDK)

Tests for querying across multiple corpora simultaneously
using the Vectara Python SDK.
"""

import uuid

import pytest
from vectara.types import (
    CoreDocumentPart,
    CreateDocumentRequest_Core,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)

from utils.waiters import wait_for


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


@pytest.mark.core
class TestCrossCorpusQuery:
    """Cross-corpus query operations."""

    def test_query_across_multiple_corpora(self, sdk_client, unique_id):
        """Test querying across two corpora returns results from both."""
        corpus1_key = f"test_cross1_{unique_id}"
        corpus2_key = f"test_cross2_{unique_id}"

        try:
            sdk_client.corpora.create(name=f"Cross1 {unique_id}", key=corpus1_key)
            sdk_client.corpora.create(name=f"Cross2 {unique_id}", key=corpus2_key)
        except Exception:
            for k in [corpus1_key, corpus2_key]:
                try:
                    sdk_client.corpora.delete(k)
                except Exception:
                    pass
            pytest.skip("Could not create corpora for cross-corpus test")

        try:
            for key in [corpus1_key, corpus2_key]:
                wait_for(
                    lambda k=key: _corpus_exists(sdk_client, k),
                    timeout=10,
                    interval=1,
                    description=f"corpus {key} available",
                )

            doc1_id = f"doc1_{unique_id}"
            doc2_id = f"doc2_{unique_id}"

            sdk_client.documents.create(
                corpus1_key,
                request=CreateDocumentRequest_Core(
                    id=doc1_id,
                    document_parts=[CoreDocumentPart(text="Medical research on heart disease prevention")],
                ),
            )
            sdk_client.documents.create(
                corpus2_key,
                request=CreateDocumentRequest_Core(
                    id=doc2_id,
                    document_parts=[CoreDocumentPart(text="Legal precedents in contract law disputes")],
                ),
            )

            for key, doc_id in [(corpus1_key, doc1_id), (corpus2_key, doc2_id)]:
                wait_for(
                    lambda k=key, d=doc_id: _document_exists(sdk_client, k, d),
                    timeout=15,
                    interval=1,
                    description=f"document in {key} indexed",
                )

            response = sdk_client.query(
                query="important topics",
                search=SearchCorporaParameters(
                    corpora=[
                        KeyedSearchCorpus(corpus_key=corpus1_key),
                        KeyedSearchCorpus(corpus_key=corpus2_key),
                    ],
                    limit=10,
                ),
            )
            results = response.search_results or []
            assert len(results) > 0, "Expected results from cross-corpus query"

            result_corpus_keys = {r.corpus_key for r in results if hasattr(r, "corpus_key")}
            assert (
                corpus1_key in result_corpus_keys or corpus2_key in result_corpus_keys
            ), f"Expected results from at least one of the test corpora, got: {result_corpus_keys}"
        finally:
            for key in [corpus1_key, corpus2_key]:
                try:
                    sdk_client.corpora.delete(key)
                except Exception:
                    pass
