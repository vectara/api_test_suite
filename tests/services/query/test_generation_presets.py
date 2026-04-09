"""
Generation Preset Tests

Tests for listing and using generation presets.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_presets_available(client):
    """Skip all tests if generation presets API is not available."""
    resp = client.list_generation_presets(limit=1)
    if not resp.success:
        pytest.skip("Generation presets API not available")


@pytest.mark.core
class TestGenerationPresets:
    """Generation preset listing and usage."""

    def test_list_generation_presets(self, client):
        """Test listing generation presets with proper structure."""
        resp = client.list_generation_presets(limit=50)
        assert resp.success, f"List presets failed: {resp.status_code}"
        presets = resp.data.get("generation_presets", [])
        assert isinstance(presets, list)
        assert len(presets) > 0, "Expected at least one generation preset"
        first = presets[0]
        assert "name" in first, "Preset should have 'name' field"

    def test_query_with_preset(self, client, seeded_shared_corpus):
        """Test querying with a specific generation preset."""
        list_resp = client.list_generation_presets(limit=50)
        if not list_resp.success:
            pytest.skip("Could not list presets")
        presets = list_resp.data.get("generation_presets", [])
        enabled_presets = [p for p in presets if p.get("enabled")]
        if not enabled_presets:
            pytest.skip("No enabled generation presets available")

        preset_name = enabled_presets[0]["name"]
        query_resp = client.query_with_summary(
            corpus_key=seeded_shared_corpus,
            query_text="artificial intelligence",
            summarizer=preset_name,
        )
        assert query_resp.success, \
            f"Query with preset failed: {query_resp.status_code} - {query_resp.data}"
        assert query_resp.data.get("summary") is not None or query_resp.data.get("generation") is not None, \
            "Expected summary/generation in response"
