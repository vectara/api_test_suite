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
        key_ids = [k.get("id") for k in list_resp.data.get("api_keys", [])]
        assert key_id in key_ids, f"Created key {key_id} not found in list: {key_ids}"

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

            # Verify disabled state
            list_resp = client.list_api_keys()
            assert list_resp.success
            disabled_key = next((k for k in list_resp.data.get("api_keys", []) if k.get("id") == key_id), None)
            assert disabled_key is not None, f"Key {key_id} not found in list"
            assert disabled_key.get("enabled") is False, f"Key should be disabled: {disabled_key}"

            # Enable
            enable_resp = client.enable_api_key(key_id)
            assert enable_resp.success, f"Enable failed: {enable_resp.data}"

            # Verify enabled state
            list_resp2 = client.list_api_keys()
            assert list_resp2.success
            enabled_key = next((k for k in list_resp2.data.get("api_keys", []) if k.get("id") == key_id), None)
            assert enabled_key is not None, f"Key {key_id} not found after enable"
            assert enabled_key.get("enabled") is True, f"Key should be enabled: {enabled_key}"
        finally:
            try:
                client.delete_api_key(key_id)
            except Exception:
                pass
