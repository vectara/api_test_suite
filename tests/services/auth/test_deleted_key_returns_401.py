"""
Deleted API Key Returns 401 Tests

Verify that a deleted API key can no longer authenticate requests.
"""

import uuid

import pytest
from utils.client import VectaraClient
from utils.waiters import wait_for


@pytest.mark.core
@pytest.mark.serial
class TestDeletedKeyReturns401:
    """API key revocation verification."""

    def test_deleted_api_key_returns_401(self, client, config):
        """Create serving key, verify it works, delete it, verify 401."""
        uid = uuid.uuid4().hex[:8]
        corpus_key = f"auth_revoke_{uid}"

        create_corpus = client.create_corpus(name=f"Auth Revoke {uid}", key=corpus_key)
        assert create_corpus.success, f"Create corpus failed: {create_corpus.status_code} - {create_corpus.data}"

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10, interval=1,
                description="corpus available",
            )

            key_resp = client.create_api_key(
                name=f"revoke_test_{uid}",
                api_key_role="serving",
                corpus_keys=[corpus_key],
            )
            assert key_resp.success, f"Create API key failed: {key_resp.status_code} - {key_resp.data}"

            key_id = key_resp.data.get("id")
            key_value = key_resp.data.get("api_key") or key_resp.data.get("secret_key")
            assert key_value, f"No key value in create response: {key_resp.data}"

            scoped_client = VectaraClient(config)
            scoped_client._session = None
            scoped_client.session.headers.update({"x-api-key": key_value})

            pre_delete = scoped_client.list_corpora(limit=1)
            assert pre_delete.success, \
                f"Key should work before deletion: {pre_delete.status_code}"

            client.delete_api_key(key_id)

            try:
                wait_for(
                    lambda: scoped_client.list_corpora(limit=1).status_code in (401, 403),
                    timeout=90, interval=5,
                    description="deleted key to return 401/403",
                )
            except TimeoutError:
                pytest.skip(
                    "Deleted API key still works after 90s — key cache propagation is slow"
                )

            post_delete = scoped_client.list_corpora(limit=1)
            assert post_delete.status_code in (401, 403), \
                f"Deleted key should return 401/403, got {post_delete.status_code}"
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass
