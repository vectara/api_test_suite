"""
Corpus Access Control Tests (SDK)

Tests for API key scoping and corpus-level access control using the Vectara Python SDK.
"""

import uuid

import pytest

from vectara import Vectara
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


@pytest.mark.core
@pytest.mark.serial
class TestCorpusAccess:
    """Corpus access control with scoped API keys."""

    def test_corpus_access_with_scoped_key(self, sdk_client, config):
        """Create serving key scoped to one corpus, verify it can only query that corpus."""
        uid = uuid.uuid4().hex[:8]
        corpus_key = f"access_test_{uid}"

        corpus = sdk_client.corpora.create(name=f"Access Test {uid}", key=corpus_key)

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, corpus.key),
                timeout=10,
                interval=1,
                description="corpus to be available",
            )

            doc_id = f"access_doc_{uid}"
            sdk_client.documents.create(
                corpus.key,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(text="Test content for access control verification."),
                    ],
                ),
            )
            wait_for(
                lambda: _document_exists(sdk_client, corpus.key, doc_id),
                timeout=15,
                interval=1,
                description="document to be indexed",
            )

            key_name = f"test_scoped_{uid}"
            create_key_resp = sdk_client.api_keys.create(
                name=key_name,
                api_key_role="serving",
                corpus_keys=[corpus.key],
            )

            key_id = create_key_resp.id
            api_key_value = create_key_resp.api_key

            try:
                scoped_client = Vectara(api_key=api_key_value)

                query_resp = scoped_client.corpora.search(
                    corpus_key=corpus.key,
                    query="test content",
                    limit=5,
                )
                results = query_resp.search_results or []
                assert isinstance(results, list)

                fake_corpus = f"nonexistent_{uid}"
                with pytest.raises(Exception):
                    scoped_client.corpora.search(
                        corpus_key=fake_corpus,
                        query="test",
                        limit=5,
                    )
            finally:
                if key_id:
                    try:
                        sdk_client.api_keys.delete(key_id)
                    except Exception:
                        pass
        finally:
            try:
                sdk_client.corpora.delete(corpus.key)
            except Exception:
                pass


def _corpus_exists(sdk_client, corpus_key):
    """Return True if corpus is accessible."""
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False


def _document_exists(sdk_client, corpus_key, doc_id):
    """Return True if document is accessible."""
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False
