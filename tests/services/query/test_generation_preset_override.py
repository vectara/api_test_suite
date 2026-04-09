"""
Generation Preset Override Tests

Verify querying with different generation presets produces valid responses.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_multiple_presets_available(client):
    """Skip if fewer than 2 enabled presets."""
    resp = client.list_generation_presets(limit=50)
    if not resp.success:
        pytest.skip("Generation presets API not available")
    presets = resp.data.get("generation_presets", [])
    enabled = [p for p in presets if p.get("enabled")]
    if len(enabled) < 2:
        pytest.skip(f"Need at least 2 enabled presets, found {len(enabled)}")


@pytest.mark.regression
class TestGenerationPresetOverride:
    """Generation preset override mechanism."""

    def test_query_with_different_presets(self, client, seeded_shared_corpus):
        """Query with two different presets, verify both return summaries."""
        presets_resp = client.list_generation_presets(limit=50)
        enabled = [p for p in presets_resp.data.get("generation_presets", []) if p.get("enabled")]

        preset_a = enabled[0]["name"]
        preset_b = enabled[1]["name"]

        resp_a = client.post(
            "/v2/query",
            data={
                "query": "artificial intelligence",
                "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 5},
                "generation": {"generation_preset_name": preset_a},
            },
        )
        assert resp_a.success, f"Query with preset {preset_a} failed: {resp_a.status_code}"
        summary_a = resp_a.data.get("summary", "")
        assert len(summary_a) > 20, f"Preset {preset_a} should produce substantive summary: {summary_a[:50]!r}"

        resp_b = client.post(
            "/v2/query",
            data={
                "query": "artificial intelligence",
                "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 5},
                "generation": {"generation_preset_name": preset_b},
            },
        )
        assert resp_b.success, f"Query with preset {preset_b} failed: {resp_b.status_code}"
        summary_b = resp_b.data.get("summary", "")
        assert len(summary_b) > 20, f"Preset {preset_b} should produce substantive summary: {summary_b[:50]!r}"

    def test_default_vs_explicit_preset(self, client, seeded_shared_corpus):
        """Query with default generation vs explicit preset, both should work."""
        default_resp = client.post(
            "/v2/query",
            data={
                "query": "machine learning",
                "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 5},
                "generation": {},
            },
        )
        assert default_resp.success, f"Default generation failed: {default_resp.status_code}"
        assert len(default_resp.data.get("summary", "")) > 0, "Default should produce summary"

        presets_resp = client.list_generation_presets(limit=50)
        enabled = [p for p in presets_resp.data.get("generation_presets", []) if p.get("enabled")]

        explicit_resp = client.post(
            "/v2/query",
            data={
                "query": "machine learning",
                "search": {"corpora": [{"corpus_key": seeded_shared_corpus}], "limit": 5},
                "generation": {"generation_preset_name": enabled[0]["name"]},
            },
        )
        assert explicit_resp.success, f"Explicit preset failed: {explicit_resp.status_code}"
        assert len(explicit_resp.data.get("summary", "")) > 0, "Explicit preset should produce summary"
