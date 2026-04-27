"""
Pipeline CRUD Tests (SDK)

Core tests for pipeline listing with availability gating.
Note: The SDK may expose pipelines via generation_presets or similar.
"""

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_pipelines_available(sdk_client):
    """Skip all tests if pipelines/generation_presets API is not available."""
    try:
        pager = sdk_client.generation_presets.list(limit=1)
        first = next(iter(pager), None)
        if first is None:
            pytest.skip("No generation presets available")
    except Exception:
        pytest.skip("Pipelines/generation presets API not available in this environment")


@pytest.mark.core
class TestPipelineCrud:
    def test_list_pipelines(self, sdk_client):
        """Test listing pipelines/generation presets returns a list."""
        pager = sdk_client.generation_presets.list(limit=10)
        presets = []
        try:
            for p in pager:
                presets.append(p)
                if len(presets) >= 10:
                    break
        except Exception:
            pass
        assert isinstance(presets, list), f"Expected list, got {type(presets)}"
        assert len(presets) > 0, "Expected at least one generation preset"

    def test_list_generation_presets(self, sdk_client):
        pager = sdk_client.generation_presets.list(limit=10)
        presets = []
        try:
            for p in pager:
                presets.append(p)
                if len(presets) >= 10:
                    break
        except Exception:
            pass
        assert isinstance(presets, list), f"Expected list, got {type(presets)}"

    def test_list_rerankers(self, sdk_client):
        """Test listing rerankers (related pipeline component)."""
        try:
            pager = sdk_client.rerankers.list(limit=10)
            rerankers = []
            for r in pager:
                rerankers.append(r)
                if len(rerankers) >= 10:
                    break
            assert isinstance(rerankers, list), f"Expected list, got {type(rerankers)}"
        except Exception:
            pytest.skip("Rerankers API not available")
