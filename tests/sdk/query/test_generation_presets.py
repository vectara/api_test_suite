"""
Generation Preset Tests (SDK)

Tests for listing and using generation presets via the Vectara Python SDK.
"""

import pytest

from vectara.types import (
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
)


@pytest.fixture(scope="module", autouse=True)
def check_presets_available(sdk_client):
    """Skip all tests if generation presets API is not available."""
    try:
        presets = list(sdk_client.generation_presets.list(limit=1))
        if not presets:
            pytest.skip("No generation presets available")
    except Exception:
        pytest.skip("Generation presets API not available")


@pytest.mark.core
class TestGenerationPresets:
    """Generation preset listing and usage."""

    def test_list_generation_presets(self, sdk_client):
        """Test listing generation presets with proper structure."""
        presets = list(sdk_client.generation_presets.list(limit=50))
        assert isinstance(presets, list)
        assert len(presets) > 0, "Expected at least one generation preset"
        first = presets[0]
        assert hasattr(first, "name") and first.name is not None, "Preset should have 'name' field"

    def test_query_with_preset(self, sdk_client, sdk_seeded_shared_corpus):
        """Test querying with a specific generation preset."""
        presets = list(sdk_client.generation_presets.list(limit=50))
        enabled_presets = [p for p in presets if getattr(p, "enabled", False)]
        if not enabled_presets:
            pytest.skip("No enabled generation presets available")

        preset_name = enabled_presets[0].name
        response = sdk_client.query(
            query="artificial intelligence",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
            generation=GenerationParameters(generation_preset_name=preset_name),
        )
        assert response.summary is not None, "Expected summary in response"
