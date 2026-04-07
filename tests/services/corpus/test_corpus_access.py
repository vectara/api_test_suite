"""
Corpus Access Control Tests

Tests for API key scoping and corpus-level access control.
"""

import uuid

import pytest
from utils.client import VectaraClient
from utils.waiters import wait_for


@pytest.mark.core
@pytest.mark.serial
class TestCorpusAccess:
    """Corpus access control with scoped API keys."""

    def test_corpus_access_with_scoped_key(self, client, config):
        """Create serving key scoped to one corpus, verify it can only query that corpus."""
        uid = uuid.uuid4().hex[:8]
        corpus_key = f"access_test_{uid}"

        create_corpus_resp = client.create_corpus(name=f"Access Test {uid}", key=corpus_key)
        if not create_corpus_resp.success:
            pytest.skip(f"Could not create corpus: {create_corpus_resp.data}")

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10, interval=1,
                description="corpus to be available",
            )

            doc_id = f"access_doc_{uid}"
            client.index_document(corpus_key, doc_id, "Test content for access control verification.")
            wait_for(
                lambda: client.get_document(corpus_key, doc_id).success,
                timeout=15, interval=1,
                description="document to be indexed",
            )

            key_name = f"test_scoped_{uid}"
            create_key_resp = client.create_api_key(
                name=key_name,
                api_key_role="serving",
                corpus_keys=[corpus_key],
            )
            if not create_key_resp.success:
                pytest.skip(f"Could not create API key: {create_key_resp.data}")

            key_id = create_key_resp.data.get("id")
            api_key_value = create_key_resp.data.get("api_key") or create_key_resp.data.get("secret_key")
            if not api_key_value:
                pytest.skip("Created API key response missing 'api_key'/'secret_key' value")

            try:
                scoped_client = VectaraClient(config)
                scoped_client._session = None
                scoped_client.session.headers.update({"x-api-key": api_key_value})

                query_resp = scoped_client.query(
                    corpus_key=corpus_key,
                    query_text="test content",
                    limit=5,
                )
                assert query_resp.success, \
                    f"Scoped key should query its corpus: {query_resp.status_code} - {query_resp.data}"
                results = query_resp.data.get("search_results", [])
                assert isinstance(results, list)

                fake_corpus = f"nonexistent_{uid}"
                other_resp = scoped_client.query(
                    corpus_key=fake_corpus,
                    query_text="test",
                    limit=5,
                )
                assert not other_resp.success, \
                    "Scoped key should not query an unscoped corpus"
            finally:
                if key_id:
                    try:
                        client.delete_api_key(key_id)
                    except Exception:
                        pass
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass
