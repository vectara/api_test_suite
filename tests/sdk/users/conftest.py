"""Users SDK test fixtures."""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_users_available(sdk_client):
    """Skip all user tests if the users API is not available."""
    try:
        pager = sdk_client.users.list(limit=1)
        list(pager)
    except Exception:
        pytest.skip("Users API not available (may require admin permissions)")
