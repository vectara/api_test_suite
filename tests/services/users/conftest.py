"""Users test fixtures."""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_users_available(client):
    """Skip all user tests if the users API is not available."""
    resp = client.list_users(limit=1)
    if not resp.success:
        pytest.skip("Users API not available (may require admin permissions)")
