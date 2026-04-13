"""
API Key Lifecycle Tests (SDK)

Core tests for API key create, list, enable, disable, and delete operations.
Never mutates the bootstrap key -- always creates disposable keys.
"""

import pytest

from vectara.types import ApiKeyRole


@pytest.mark.core
@pytest.mark.serial
class TestApiKeyLifecycle:
    """Tests for API key create, list, enable, disable, delete.
    Never mutates the bootstrap key -- always creates disposable keys.
    """

    def test_create_and_delete_api_key(self, sdk_client, sdk_shared_corpus, unique_id):
        response = sdk_client.api_keys.create(
            name=f"test_key_{unique_id}",
            api_key_role=ApiKeyRole.SERVING,
            corpus_keys=[sdk_shared_corpus],
        )

        assert response.api_key is not None, "Response should contain api_key"
        key_id = response.id
        assert key_id is not None, f"No key ID in response"

        # Verify in list
        pager = sdk_client.api_keys.list()
        keys = list(pager)
        key_ids = [getattr(k, "id", None) for k in keys]
        assert key_id in key_ids, f"Created key {key_id} not found in list: {key_ids}"

        # Delete
        sdk_client.api_keys.delete(key_id)

    def test_disable_enable_api_key(self, sdk_client, sdk_shared_corpus, unique_id):
        # Create disposable key with a corpus
        response = sdk_client.api_keys.create(
            name=f"toggle_key_{unique_id}",
            api_key_role=ApiKeyRole.SERVING,
            corpus_keys=[sdk_shared_corpus],
        )

        key_id = response.id

        try:
            # Disable
            sdk_client.api_keys.update(key_id, enabled=False)

            # Verify disabled state
            retrieved = sdk_client.api_keys.get(key_id)
            assert retrieved.enabled is False, f"Key should be disabled: {retrieved.enabled}"

            # Enable
            sdk_client.api_keys.update(key_id, enabled=True)

            # Verify enabled state
            retrieved2 = sdk_client.api_keys.get(key_id)
            assert retrieved2.enabled is True, f"Key should be enabled: {retrieved2.enabled}"
        finally:
            try:
                sdk_client.api_keys.delete(key_id)
            except Exception:
                pass
