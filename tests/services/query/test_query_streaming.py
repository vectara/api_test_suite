"""
Query Streaming Tests

Tests for Server-Sent Events (SSE) streaming query responses.
"""

import pytest
from utils.waiters import read_sse_events


@pytest.fixture(scope="module", autouse=True)
def check_streaming_available(client, seeded_shared_corpus):
    """Skip all tests if streaming query is not supported."""
    try:
        raw = client.query_stream(
            corpus_key=seeded_shared_corpus,
            query_text="test",
        )
        if raw.status_code not in (200, 201):
            pytest.skip(f"Streaming query not supported: {raw.status_code}")
        raw.close()
    except Exception as e:
        pytest.skip(f"Streaming query not available: {e}")


@pytest.mark.core
class TestQueryStreaming:
    """Streaming query tests."""

    def test_streaming_query_events(self, client, seeded_shared_corpus):
        """Test that streaming query returns valid SSE events."""
        raw = client.query_stream(
            corpus_key=seeded_shared_corpus,
            query_text="artificial intelligence",
        )

        try:
            assert raw.status_code == 200, f"Stream request failed: {raw.status_code}"
            events = list(read_sse_events(raw))
            assert len(events) > 0, "Expected at least one SSE event"

            has_content = any(
                e.get("data") is not None and e.get("data") != ""
                for e in events
            )
            assert has_content, f"Expected at least one event with data, got event types: {[e.get('event', '') for e in events]}"
        finally:
            raw.close()

    def test_streaming_query_fcs(self, client, seeded_shared_corpus):
        """Test that streaming query with FCS enabled returns a score."""
        raw = client.query_stream(
            corpus_key=seeded_shared_corpus,
            query_text="artificial intelligence",
            generation_config={
                "enable_factual_consistency_score": True,
            },
        )

        try:
            assert raw.status_code == 200, f"Stream request failed: {raw.status_code}"
            events = list(read_sse_events(raw))

            fcs_found = False
            for event in events:
                data = event.get("data", {})
                if isinstance(data, dict) and "factual_consistency_score" in data:
                    score = data["factual_consistency_score"]
                    assert 0.0 <= score <= 1.0, f"FCS score out of range: {score}"
                    fcs_found = True
                    break

            if not fcs_found:
                pytest.skip("FCS not returned in streaming response -- may not be enabled for this account")
        finally:
            raw.close()
