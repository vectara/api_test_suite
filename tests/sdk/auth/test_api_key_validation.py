"""
API Key Validation Tests (SDK)

Sanity-level checks that the configured SDK client is valid and that
basic operations work.
"""

import time

import pytest
from vectara import Vectara


@pytest.mark.sanity
class TestApiKeyValidation:
    """Sanity checks for API key validity via SDK."""

    def test_health_check(self, sdk_client):
        """Test that the SDK client can connect by listing corpora."""
        pager = sdk_client.corpora.list(limit=1)
        corpora = list(pager)
        # If we get here without exception, the API key is valid
        assert isinstance(corpora, list), f"Expected list, got: {type(corpora)}"

    def test_invalid_api_key_rejected(self, config):
        """Test that invalid API keys are properly rejected."""
        invalid_client = Vectara(api_key="invalid_key_12345")

        with pytest.raises(Exception):
            # Any SDK call with an invalid key should raise
            pager = invalid_client.corpora.list(limit=1)
            list(pager)

    def test_response_time_acceptable(self, sdk_client):
        """Test that authentication response time is acceptable."""
        start = time.monotonic()
        pager = sdk_client.corpora.list(limit=1)
        list(pager)
        elapsed_s = time.monotonic() - start

        # Authentication should complete within 5 seconds
        assert elapsed_s < 5, f"Authentication took too long: {elapsed_s * 1000:.1f}ms"
