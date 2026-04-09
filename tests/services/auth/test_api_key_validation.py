"""
API Key Validation Tests

Sanity-level checks that the configured API key is valid, that invalid
keys are rejected, and that authentication response time is acceptable.
"""

import pytest

from utils.client import VectaraClient
from utils.config import Config


@pytest.mark.sanity
class TestApiKeyValidation:
    """Sanity checks for API key validity."""

    def test_health_check(self, client):
        """Test that the API key is valid and can connect."""
        response = client.health_check()

        assert response.success, f"API authentication failed: {response.status_code} - {response.data}"
        assert response.data is not None, "Health check returned no data"
        assert "corpora" in response.data or isinstance(response.data, list), f"Expected corpora structure, got: {type(response.data)}"

    def test_invalid_api_key_rejected(self, config):
        """Test that invalid API keys are properly rejected."""
        # Create client with invalid key
        invalid_config = Config()
        invalid_config.set_api_key("invalid_key_12345")

        invalid_client = VectaraClient(invalid_config)
        response = invalid_client.health_check()

        assert not response.success, "Invalid API key should be rejected"
        assert response.status_code in [401, 403], f"Expected 401 or 403 for invalid key, got {response.status_code}"

    def test_response_time_acceptable(self, client):
        """Test that authentication response time is acceptable."""
        response = client.health_check()

        # Authentication should complete within 5 seconds
        assert response.elapsed_ms < 5000, f"Authentication took too long: {response.elapsed_ms:.1f}ms"
