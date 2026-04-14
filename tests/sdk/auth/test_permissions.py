"""
Permission Tests (SDK)

Core-level checks that the SDK client has the correct permissions
for query and index operations, and that basic corpus listing works.
"""

import uuid

import pytest
from vectara import Vectara
from vectara.environment import VectaraEnvironment
from vectara.types import (
    CoreDocumentPart,
    CreateDocumentRequest_Core,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)


@pytest.mark.core
class TestPermissions:
    """Core checks for API key permissions via SDK."""

    def test_sdk_client_has_query_permission(self, sdk_client, sdk_shared_corpus):
        """Test that SDK client can query (has QueryService permission)."""
        # Index a document first
        doc_id = f"auth_test_doc_{uuid.uuid4().hex[:8]}"
        try:
            sdk_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Test document for permission check",
                            metadata={"source": "test_suite"},
                        )
                    ],
                ),
            )
        except Exception:
            pass  # Document might already exist

        # Test query permission
        result = sdk_client.corpora.search(
            corpus_key=sdk_shared_corpus,
            query="test query",
            limit=1,
        )
        assert result is not None, "Query should return a result"

    def test_sdk_client_has_index_permission(self, sdk_client, sdk_shared_corpus):
        """Test that SDK client can index (has IndexService permission)."""
        doc_id = f"auth_permission_test_{uuid.uuid4().hex[:8]}"
        doc = sdk_client.documents.create(
            sdk_shared_corpus,
            request=CreateDocumentRequest_Core(
                id=doc_id,
                document_parts=[
                    CoreDocumentPart(
                        text="Testing IndexService permission via SDK",
                    )
                ],
            ),
        )
        assert doc is not None, "Index response should not be None"

    def test_api_key_has_query_permission(self, sdk_client, sdk_shared_corpus, unique_id, config):
        """Test that a scoped API key with serving role can query."""
        # Create a scoped API key with serving role
        key_resp = sdk_client.api_keys.create(
            name=f"query_perm_key_{unique_id}",
            api_key_role="serving",
            corpus_keys=[sdk_shared_corpus],
        )
        key_id = key_resp.id
        api_key_str = key_resp.secret_key

        try:
            # Create a client using the scoped key
            base_url = config.base_url
            if base_url and base_url != "https://api.vectara.io":
                env = VectaraEnvironment(default=base_url, auth=base_url.replace("api.", "auth."))
                scoped_client = Vectara(api_key=api_key_str, environment=env)
            else:
                scoped_client = Vectara(api_key=api_key_str)

            # Index a doc first so there's something to query
            doc_id = f"auth_query_perm_{uuid.uuid4().hex[:8]}"
            try:
                sdk_client.documents.create(
                    sdk_shared_corpus,
                    request=CreateDocumentRequest_Core(
                        id=doc_id,
                        document_parts=[
                            CoreDocumentPart(
                                text="Document for query permission test",
                            )
                        ],
                    ),
                )
            except Exception:
                pass

            # Query using the scoped key
            result = scoped_client.corpora.search(
                corpus_key=sdk_shared_corpus,
                query="query permission test",
                limit=1,
            )
            assert result is not None, "Scoped serving key should be able to query"
            assert isinstance(result.search_results, list), f"Expected search_results list, got: {type(result.search_results)}"
        finally:
            try:
                sdk_client.api_keys.delete(key_id)
            except Exception:
                pass

    def test_api_key_has_index_permission(self, sdk_client, sdk_shared_corpus, unique_id, config):
        """Test that a scoped API key with serving_and_indexing role can index."""
        # Create a scoped API key with serving_and_indexing role
        key_resp = sdk_client.api_keys.create(
            name=f"index_perm_key_{unique_id}",
            api_key_role="serving_and_indexing",
            corpus_keys=[sdk_shared_corpus],
        )
        key_id = key_resp.id
        api_key_str = key_resp.secret_key

        try:
            # Create a client using the scoped key
            base_url = config.base_url
            if base_url and base_url != "https://api.vectara.io":
                env = VectaraEnvironment(default=base_url, auth=base_url.replace("api.", "auth."))
                scoped_client = Vectara(api_key=api_key_str, environment=env)
            else:
                scoped_client = Vectara(api_key=api_key_str)

            doc_id = f"auth_index_perm_{uuid.uuid4().hex[:8]}"
            doc = scoped_client.documents.create(
                sdk_shared_corpus,
                request=CreateDocumentRequest_Core(
                    id=doc_id,
                    document_parts=[
                        CoreDocumentPart(
                            text="Testing index permission with scoped key",
                        )
                    ],
                ),
            )
            assert doc is not None, "Scoped serving_and_indexing key should be able to index"
        finally:
            try:
                sdk_client.api_keys.delete(key_id)
            except Exception:
                pass

    def test_list_corpora_works(self, sdk_client):
        """Test basic corpus listing (requires valid authentication)."""
        pager = sdk_client.corpora.list(limit=10)
        corpora = list(pager)
        assert isinstance(corpora, list), "Expected corpora list"
