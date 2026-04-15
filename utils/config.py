"""
Configuration management for Vectara API Test Suite.

Uses environment variables for all configuration to support
multiple deployment targets (SaaS, staging, on-premise).
"""

import os
from typing import Optional


class Config:
    """Configuration manager using environment variables."""

    def __init__(self):
        pass

    @property
    def api_key(self) -> Optional[str]:
        """Get Personal API key from environment."""
        return os.environ.get("VECTARA_API_KEY")

    @property
    def base_url(self) -> str:
        """Get API base URL from environment or use default."""
        return os.environ.get("VECTARA_BASE_URL", "https://api.vectara.io")

    @property
    def request_timeout(self) -> int:
        """Get request timeout in seconds."""
        return int(os.environ.get("VECTARA_TIMEOUT", "30"))

    @property
    def max_retries(self) -> int:
        """Get maximum retry count."""
        return int(os.environ.get("VECTARA_MAX_RETRIES", "3"))

    @property
    def corpus_prefix(self) -> str:
        """Get test corpus name prefix."""
        return os.environ.get("VECTARA_CORPUS_PREFIX", "api_test_")

    @property
    def generation_preset(self) -> Optional[str]:
        """Get generation preset name from environment."""
        return os.environ.get("VECTARA_GENERATION_PRESET")

    @property
    def llm_name(self) -> Optional[str]:
        """Get LLM name from environment."""
        return os.environ.get("VECTARA_LLM_NAME")

    def set_api_key(self, api_key: str) -> None:
        """Set API key programmatically."""
        os.environ["VECTARA_API_KEY"] = api_key

    def get_vectara_environment(self):
        """Return a VectaraEnvironment for non-production base URLs, or None for default."""
        from vectara.environment import VectaraEnvironment

        base_url = self.base_url
        if base_url and base_url != "https://api.vectara.io":
            return VectaraEnvironment(default=base_url, auth=base_url.replace("api.", "auth."))
        return None  # Use default production environment

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate required configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not self.api_key:
            errors.append("API key is required. Set VECTARA_API_KEY environment variable " "or provide via --api-key")

        return len(errors) == 0, errors
