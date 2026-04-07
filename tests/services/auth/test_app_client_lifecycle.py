"""
App Client Lifecycle Tests

Tests for app client create, read, update, and delete operations.
"""

import pytest
from utils.waiters import wait_for


@pytest.fixture(scope="module", autouse=True)
def check_app_clients_available(client):
    """Skip all tests if app clients API is not available."""
    resp = client.list_app_clients(limit=1)
    if not resp.success:
        pytest.skip("App clients API not available")


@pytest.mark.core
@pytest.mark.serial
class TestAppClientLifecycle:
    """App client CRUD operations."""

    def test_create_app_client(self, client, unique_id):
        """Test creating a client_credentials app client."""
        name = f"test_client_{unique_id}"
        response = client.create_app_client(name=name, type="client_credentials")

        try:
            assert response.success, f"Create app client failed: {response.status_code} - {response.data}"
            assert response.data.get("id") is not None, "Response should contain 'id'"
            assert response.data.get("client_id") is not None, "Response should contain 'client_id'"
            assert response.data.get("client_secret") is not None, "Response should contain 'client_secret'"
        finally:
            client_id = response.data.get("id")
            if client_id:
                try:
                    client.delete_app_client(client_id)
                except Exception:
                    pass

    def test_list_app_clients(self, client, unique_id):
        """Test listing app clients contains a created client."""
        name = f"test_list_client_{unique_id}"
        create_resp = client.create_app_client(name=name, type="client_credentials")
        if not create_resp.success:
            pytest.skip(f"Could not create app client: {create_resp.data}")

        client_id = create_resp.data.get("id")
        try:
            wait_for(
                lambda: any(
                    c.get("id") == client_id
                    for c in client.list_app_clients().data.get("app_clients", [])
                ),
                timeout=10,
                interval=1,
                description="app client to appear in listing",
            )

            list_resp = client.list_app_clients()
            assert list_resp.success, f"List app clients failed: {list_resp.status_code}"
            clients = list_resp.data.get("app_clients", [])
            client_ids = [c.get("id") for c in clients]
            assert client_id in client_ids, f"Created client {client_id} not in listing"
        finally:
            if client_id:
                try:
                    client.delete_app_client(client_id)
                except Exception:
                    pass

    def test_get_app_client(self, client, unique_id):
        """Test retrieving a specific app client."""
        name = f"test_get_client_{unique_id}"
        create_resp = client.create_app_client(name=name, type="client_credentials")
        if not create_resp.success:
            pytest.skip(f"Could not create app client: {create_resp.data}")

        client_id = create_resp.data.get("id")
        try:
            get_resp = client.get_app_client(client_id)
            assert get_resp.success, f"Get app client failed: {get_resp.status_code}"
            assert get_resp.data.get("id") == client_id
            assert get_resp.data.get("name") == name
        finally:
            if client_id:
                try:
                    client.delete_app_client(client_id)
                except Exception:
                    pass

    def test_update_app_client(self, client, unique_id):
        """Test updating an app client description."""
        name = f"test_update_client_{unique_id}"
        create_resp = client.create_app_client(name=name, type="client_credentials")
        if not create_resp.success:
            pytest.skip(f"Could not create app client: {create_resp.data}")

        client_id = create_resp.data.get("id")
        try:
            new_desc = f"Updated description {unique_id}"
            update_resp = client.update_app_client(client_id, description=new_desc)
            assert update_resp.success, f"Update app client failed: {update_resp.status_code}"

            get_resp = client.get_app_client(client_id)
            assert get_resp.success
            assert get_resp.data.get("description") == new_desc, \
                f"Description not persisted: {get_resp.data.get('description')!r}"
        finally:
            if client_id:
                try:
                    client.delete_app_client(client_id)
                except Exception:
                    pass

    def test_delete_app_client(self, client, unique_id):
        """Test deleting an app client and verifying 404."""
        name = f"test_delete_client_{unique_id}"
        create_resp = client.create_app_client(name=name, type="client_credentials")
        if not create_resp.success:
            pytest.skip(f"Could not create app client: {create_resp.data}")

        client_id = create_resp.data.get("id")

        delete_resp = client.delete_app_client(client_id)
        assert delete_resp.success, f"Delete app client failed: {delete_resp.status_code}"

        get_resp = client.get_app_client(client_id)
        assert get_resp.status_code == 404, \
            f"Deleted app client should return 404, got {get_resp.status_code}"
