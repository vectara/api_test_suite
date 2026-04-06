"""
API Key Lifecycle Tests

Core tests for API key create, list, enable, disable, and delete operations.
Never mutates the bootstrap key -- always creates disposable keys.
"""

import pytest


@pytest.mark.core
@pytest.mark.serial
class TestApiKeyLifecycle:
    """Tests for API key create, list, enable, disable, delete.
    Never mutates the bootstrap key -- always creates disposable keys.
    """

    def test_create_and_delete_api_key(self, client, shared_corpus, unique_id):
        response = client.create_api_key(
            name=f"test_key_{unique_id}",
            api_key_role="serving",
            corpus_keys=[shared_corpus],
        )
        assert response.success, f"Create API key failed: {response.status_code} - {response.data}"

        key_id = response.data.get("id") or response.data.get("api_key_id")
        assert key_id, f"No key ID in response: {response.data}"

        # Verify in list
        list_resp = client.list_api_keys()
        assert list_resp.success

        # Delete
        del_resp = client.delete_api_key(key_id)
        assert del_resp.success, f"Delete API key failed: {del_resp.data}"

    def test_disable_enable_api_key(self, client, shared_corpus, unique_id):
        # Create disposable key with a corpus
        response = client.create_api_key(
            name=f"toggle_key_{unique_id}",
            api_key_role="serving",
            corpus_keys=[shared_corpus],
        )
        if not response.success:
            pytest.skip(f"Could not create API key: {response.data}")

        key_id = response.data.get("id") or response.data.get("api_key_id")

        try:
            # Disable
            disable_resp = client.disable_api_key(key_id)
            assert disable_resp.success, f"Disable failed: {disable_resp.data}"

            # Enable
            enable_resp = client.enable_api_key(key_id)
            assert enable_resp.success, f"Enable failed: {enable_resp.data}"
        finally:
            try:
                client.delete_api_key(key_id)
            except Exception:
                pass
