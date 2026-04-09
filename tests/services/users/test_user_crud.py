"""
User CRUD Tests

Tests for user create, read, update, and delete operations.
"""

import uuid

import pytest

from utils.waiters import wait_for


def _extract_username(create_resp, email=None):
    """Extract the username/handle for GET/PATCH/DELETE operations.

    The User API operates by handle (username). The create response may
    return empty strings for username/email fields even on success.
    When that happens, fall back to the email that was sent in the request.
    """
    data = create_resp.data or {}
    username = data.get("username")
    if username:
        return username
    resp_email = data.get("email")
    if resp_email:
        return resp_email
    if email:
        return email
    return data.get("id")


@pytest.mark.core
@pytest.mark.serial
class TestUserCrud:
    """User management CRUD operations."""

    def test_create_user(self, client, unique_id):
        """Test creating a new user and verifying response contains the sent fields."""
        email = f"test_{unique_id}@example.com"
        description = f"Test user {unique_id}"
        resp = client.create_user(email=email, description=description)

        try:
            assert resp.success, f"Create user failed: {resp.status_code} - {resp.data}"
            assert resp.data.get("id") is not None, f"Response should contain 'id': {resp.data}"

            assert resp.data.get("email") == email, f"Create response should echo back email: expected {email!r}, got {resp.data.get('email')!r}"
            assert (
                resp.data.get("description") == description
            ), f"Create response should echo back description: expected {description!r}, got {resp.data.get('description')!r}"
        finally:
            username = _extract_username(resp, email) if resp.success else None
            if username:
                try:
                    client.delete_user(username)
                except Exception:
                    pass

    def test_list_users(self, client, unique_id):
        """Test that a created user appears in the user list."""
        email = f"test_list_{unique_id}@example.com"
        create_resp = client.create_user(email=email)
        assert create_resp.success, f"Create user failed: {create_resp.status_code} - {create_resp.data}"

        username = _extract_username(create_resp, email)
        try:
            list_resp = client.list_users()
            assert list_resp.success, f"List users failed: {list_resp.status_code}"
            users = list_resp.data.get("users", list_resp.data if isinstance(list_resp.data, list) else [])
            found = any(u.get("username") == username or u.get("id") == username or u.get("email") == email for u in users)
            assert found, f"User {username} (email={email}) not found in listing"
        finally:
            try:
                client.delete_user(username)
            except Exception:
                pass

    def test_get_user(self, client, unique_id):
        """Test retrieving a specific user."""
        email = f"test_get_{unique_id}@example.com"
        create_resp = client.create_user(email=email)
        assert create_resp.success, f"Create user failed: {create_resp.status_code} - {create_resp.data}"

        username = _extract_username(create_resp, email)
        try:
            get_resp = client.get_user(username)
            assert get_resp.success, f"Get user failed: {get_resp.status_code} - {get_resp.data}"
            assert get_resp.data.get("email") == email, f"Expected email={email}, got: {get_resp.data.get('email')}"
        finally:
            try:
                client.delete_user(username)
            except Exception:
                pass

    def test_update_user_description(self, client, unique_id):
        """Test updating a user's description."""
        email = f"test_update_{unique_id}@example.com"
        create_resp = client.create_user(email=email, description="Original")
        assert create_resp.success, f"Create user failed: {create_resp.status_code} - {create_resp.data}"

        username = _extract_username(create_resp, email)
        try:
            new_desc = f"Updated {unique_id}"
            update_resp = client.update_user(username, description=new_desc)
            assert update_resp.success, f"Update user failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_user(username)
            assert get_resp.success
            assert get_resp.data.get("description") == new_desc
        finally:
            try:
                client.delete_user(username)
            except Exception:
                pass

    def test_disable_enable_user(self, client, unique_id):
        """Test disabling and re-enabling a user."""
        email = f"test_toggle_{unique_id}@example.com"
        create_resp = client.create_user(email=email)
        assert create_resp.success, f"Create user failed: {create_resp.status_code} - {create_resp.data}"

        username = _extract_username(create_resp, email)
        try:
            disable_resp = client.update_user(username, enabled=False)
            assert disable_resp.success, f"Disable user failed: {disable_resp.status_code} - {disable_resp.data}"

            get_resp = client.get_user(username)
            assert get_resp.success
            assert get_resp.data.get("enabled") is False, f"Expected disabled, got: {get_resp.data.get('enabled')}"

            enable_resp = client.update_user(username, enabled=True)
            assert enable_resp.success

            get_resp2 = client.get_user(username)
            assert get_resp2.data.get("enabled") is True
        finally:
            try:
                client.delete_user(username)
            except Exception:
                pass

    def test_delete_user(self, client, unique_id):
        """Test deleting a user and verifying 404."""
        email = f"test_delete_{unique_id}@example.com"
        create_resp = client.create_user(email=email)
        assert create_resp.success, f"Create user failed: {create_resp.status_code} - {create_resp.data}"

        username = _extract_username(create_resp, email)

        delete_resp = client.delete_user(username)
        assert delete_resp.success, f"Delete user failed: {delete_resp.status_code} - {delete_resp.data}"

        get_resp = client.get_user(username)
        assert get_resp.status_code == 404, f"Deleted user should return 404, got {get_resp.status_code}"
