"""
App Client Lifecycle Tests (SDK)

Tests for app client create, read, update, and delete operations.
"""

import pytest

from vectara.types import ApiRole
from vectara.errors import NotFoundError

from utils.waiters import wait_for


@pytest.fixture(scope="module", autouse=True)
def check_app_clients_available(sdk_client):
    """Skip all tests if app clients API is not available."""
    try:
        pager = sdk_client.app_clients.list(limit=1)
        list(pager)
    except Exception:
        pytest.skip("App clients API not available")


@pytest.mark.core
@pytest.mark.serial
class TestAppClientLifecycle:
    """App client CRUD operations."""

    def test_create_app_client(self, sdk_client, unique_id):
        """Test creating a client_credentials app client."""
        name = f"test_client_{unique_id}"
        app_client = sdk_client.app_clients.create(
            name=name,
            api_roles=[ApiRole.SERVING],
        )

        try:
            assert app_client.id is not None, "Response should contain 'id'"
            assert app_client.client_id is not None, "Response should contain 'client_id'"
            assert app_client.client_secret is not None, "Response should contain 'client_secret'"
        finally:
            if app_client.id:
                try:
                    sdk_client.app_clients.delete(app_client.id)
                except Exception:
                    pass

    def test_list_app_clients(self, sdk_client, unique_id):
        """Test listing app clients contains a created client."""
        name = f"test_list_client_{unique_id}"
        app_client = sdk_client.app_clients.create(
            name=name,
            api_roles=[ApiRole.SERVING],
        )

        client_id = app_client.id
        try:
            wait_for(
                lambda: _client_in_list(sdk_client, client_id),
                timeout=10,
                interval=1,
                description="app client to appear in listing",
            )

            pager = sdk_client.app_clients.list()
            clients = list(pager)
            client_ids = [getattr(c, "id", None) for c in clients]
            assert client_id in client_ids, f"Created client {client_id} not in listing"
        finally:
            if client_id:
                try:
                    sdk_client.app_clients.delete(client_id)
                except Exception:
                    pass

    def test_get_app_client(self, sdk_client, unique_id):
        """Test retrieving a specific app client."""
        name = f"test_get_client_{unique_id}"
        app_client = sdk_client.app_clients.create(
            name=name,
            api_roles=[ApiRole.SERVING],
        )

        client_id = app_client.id
        try:
            retrieved = sdk_client.app_clients.get(client_id)
            assert retrieved.id == client_id
            assert retrieved.name == name
        finally:
            if client_id:
                try:
                    sdk_client.app_clients.delete(client_id)
                except Exception:
                    pass

    def test_update_app_client(self, sdk_client, unique_id):
        """Test updating an app client description."""
        name = f"test_update_client_{unique_id}"
        app_client = sdk_client.app_clients.create(
            name=name,
            api_roles=[ApiRole.SERVING],
        )

        client_id = app_client.id
        try:
            new_desc = f"Updated description {unique_id}"
            sdk_client.app_clients.update(client_id, description=new_desc)

            retrieved = sdk_client.app_clients.get(client_id)
            assert retrieved.description == new_desc, (
                f"Description not persisted: {retrieved.description!r}"
            )
        finally:
            if client_id:
                try:
                    sdk_client.app_clients.delete(client_id)
                except Exception:
                    pass

    def test_delete_app_client(self, sdk_client, unique_id):
        """Test deleting an app client and verifying 404."""
        name = f"test_delete_client_{unique_id}"
        app_client = sdk_client.app_clients.create(
            name=name,
            api_roles=[ApiRole.SERVING],
        )

        client_id = app_client.id

        sdk_client.app_clients.delete(client_id)

        with pytest.raises(NotFoundError):
            sdk_client.app_clients.get(client_id)


def _client_in_list(sdk_client, client_id):
    """Return True if client_id appears in the app clients listing."""
    try:
        pager = sdk_client.app_clients.list()
        clients = list(pager)
        return any(getattr(c, "id", None) == client_id for c in clients)
    except Exception:
        return False
