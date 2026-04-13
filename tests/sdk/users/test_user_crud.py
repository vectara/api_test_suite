"""
User CRUD Tests (SDK)

Tests for user create, read, update, and delete operations.
"""

import uuid

import pytest

from vectara.errors import NotFoundError

from utils.waiters import wait_for


def _extract_username(user, email=None):
    """Extract the username/handle for GET/PATCH/DELETE operations.

    The User API operates by handle (username). The create response may
    return empty strings for username/email fields even on success.
    """
    username = getattr(user, "username", None)
    if username:
        return username
    resp_email = getattr(user, "email", None)
    if resp_email:
        return resp_email
    if email:
        return email
    return getattr(user, "id", None)


@pytest.mark.core
@pytest.mark.serial
class TestUserCrud:
    """User management CRUD operations."""

    def test_create_user(self, sdk_client, unique_id):
        """Test creating a new user and verifying response contains the sent fields."""
        email = f"test_{unique_id}@example.com"
        description = f"Test user {unique_id}"

        user = sdk_client.users.create(
            email=email,
            username=email,
            api_roles=[],
        )

        try:
            assert user is not None, "Create user should return a user object"
            assert getattr(user, "email", None) == email, (
                f"Create response should echo back email: expected {email!r}, "
                f"got {getattr(user, 'email', None)!r}"
            )
        finally:
            username = _extract_username(user, email)
            if username:
                try:
                    sdk_client.users.delete(username)
                except Exception:
                    pass

    def test_list_users(self, sdk_client, unique_id):
        """Test that a created user appears in the user list."""
        email = f"test_list_{unique_id}@example.com"

        user = sdk_client.users.create(
            email=email,
            username=email,
            api_roles=[],
        )

        username = _extract_username(user, email)
        try:
            pager = sdk_client.users.list()
            users = list(pager)
            found = any(
                getattr(u, "username", None) == username
                or getattr(u, "email", None) == email
                for u in users
            )
            assert found, f"User {username} (email={email}) not found in listing"
        finally:
            try:
                sdk_client.users.delete(username)
            except Exception:
                pass

    def test_get_user(self, sdk_client, unique_id):
        """Test retrieving a specific user."""
        email = f"test_get_{unique_id}@example.com"

        user = sdk_client.users.create(
            email=email,
            username=email,
            api_roles=[],
        )

        username = _extract_username(user, email)
        try:
            retrieved = sdk_client.users.get(username)
            assert getattr(retrieved, "email", None) == email, (
                f"Expected email={email}, got: {getattr(retrieved, 'email', None)}"
            )
        finally:
            try:
                sdk_client.users.delete(username)
            except Exception:
                pass

    def test_disable_enable_user(self, sdk_client, unique_id):
        """Test disabling and re-enabling a user."""
        email = f"test_toggle_{unique_id}@example.com"

        user = sdk_client.users.create(
            email=email,
            username=email,
            api_roles=[],
        )

        username = _extract_username(user, email)
        try:
            sdk_client.users.update(username, enabled=False)

            retrieved = sdk_client.users.get(username)
            assert retrieved.enabled is False, f"Expected disabled, got: {retrieved.enabled}"

            sdk_client.users.update(username, enabled=True)

            retrieved2 = sdk_client.users.get(username)
            assert retrieved2.enabled is True
        finally:
            try:
                sdk_client.users.delete(username)
            except Exception:
                pass

    def test_delete_user(self, sdk_client, unique_id):
        """Test deleting a user and verifying 404."""
        email = f"test_delete_{unique_id}@example.com"

        user = sdk_client.users.create(
            email=email,
            username=email,
            api_roles=[],
        )

        username = _extract_username(user, email)

        sdk_client.users.delete(username)

        with pytest.raises(NotFoundError):
            sdk_client.users.get(username)
