"""
Corpus Validation Tests (SDK)

Tests for corpus creation input validation using the Vectara Python SDK.
"""

import pytest

from vectara.errors import BadRequestError


@pytest.mark.regression
class TestCorpusValidation:
    """Corpus input validation."""

    def test_invalid_corpus_key_characters(self, sdk_client):
        """Test that creating a corpus with invalid key characters raises BadRequestError."""
        with pytest.raises(BadRequestError):
            sdk_client.corpora.create(name="Invalid Key Test", key="invalid!@#$%^&*()")

    def test_corpus_key_length_limit(self, sdk_client):
        """Test that creating a corpus with an excessively long key raises BadRequestError."""
        long_key = "a" * 300
        with pytest.raises(BadRequestError):
            sdk_client.corpora.create(name="Long Key Test", key=long_key)
