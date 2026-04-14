"""
Generation Preset Override Tests (SDK)

Verify querying with different generation presets produces valid responses
using the Vectara Python SDK.
"""

import pytest
from vectara.types import (
    GenerationParameters,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)


@pytest.fixture(scope="module", autouse=True)
def check_multiple_presets_available(sdk_client):
    """Skip if fewer than 2 enabled presets."""
    try:
        presets = list(sdk_client.generation_presets.list(limit=50))
        enabled = [p for p in presets if getattr(p, "enabled", False)]
        if len(enabled) < 2:
            pytest.skip(f"Need at least 2 enabled presets, found {len(enabled)}")
    except Exception:
        pytest.skip("Generation presets API not available")


@pytest.mark.regression
class TestGenerationPresetOverride:
    """Generation preset override mechanism."""

    def test_query_with_different_presets(self, sdk_client, sdk_seeded_shared_corpus):
        """Query with two different presets, verify both return summaries."""
        presets = list(sdk_client.generation_presets.list(limit=50))
        enabled = [p for p in presets if getattr(p, "enabled", False)]

        preset_a = enabled[0].name
        preset_b = enabled[1].name

        resp_a = sdk_client.query(
            query="artificial intelligence",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
            generation=GenerationParameters(generation_preset_name=preset_a),
        )
        summary_a = resp_a.summary or ""
        assert len(summary_a) > 20, f"Preset {preset_a} should produce substantive summary: {summary_a[:50]!r}"

        resp_b = sdk_client.query(
            query="artificial intelligence",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
            generation=GenerationParameters(generation_preset_name=preset_b),
        )
        summary_b = resp_b.summary or ""
        assert len(summary_b) > 20, f"Preset {preset_b} should produce substantive summary: {summary_b[:50]!r}"

    def test_default_vs_explicit_preset(self, sdk_client, sdk_seeded_shared_corpus):
        """Query with default generation vs explicit preset, both should work."""
        default_resp = sdk_client.query(
            query="machine learning",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
            generation=GenerationParameters(),
        )
        assert default_resp.summary is not None and len(default_resp.summary) > 0, "Default should produce summary"

        presets = list(sdk_client.generation_presets.list(limit=50))
        enabled = [p for p in presets if getattr(p, "enabled", False)]

        explicit_resp = sdk_client.query(
            query="machine learning",
            search=SearchCorporaParameters(
                corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                limit=5,
            ),
            generation=GenerationParameters(generation_preset_name=enabled[0].name),
        )
        assert explicit_resp.summary is not None and len(explicit_resp.summary) > 0, "Explicit preset should produce summary"
