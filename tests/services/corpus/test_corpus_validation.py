"""
Corpus Validation Tests

Tests for corpus creation input validation.
"""

import pytest


@pytest.mark.regression
class TestCorpusValidation:
    """Corpus input validation."""

    def test_invalid_corpus_key_characters(self, client):
        """Test that creating a corpus with invalid key characters returns 400."""
        resp = client.create_corpus(name="Invalid Key Test", key="invalid!@#$%^&*()")
        assert not resp.success, "Creating corpus with invalid key chars should fail"
        assert resp.status_code == 400, f"Expected 400 for invalid key chars, got {resp.status_code}"

    def test_corpus_key_length_limit(self, client):
        """Test that creating a corpus with an excessively long key returns 400."""
        long_key = "a" * 300
        resp = client.create_corpus(name="Long Key Test", key=long_key)
        assert not resp.success, "Creating corpus with 300+ char key should fail"
        assert resp.status_code == 400, f"Expected 400 for key length violation, got {resp.status_code}"
