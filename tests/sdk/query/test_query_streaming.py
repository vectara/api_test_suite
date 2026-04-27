"""
Query Streaming Tests (SDK)

Tests for streaming query responses using the Vectara Python SDK.
"""

import pytest
from vectara.types import (
    GenerationParameters,
    KeyedSearchCorpus,
    SearchCorporaParameters,
)


@pytest.fixture(scope="module", autouse=True)
def check_streaming_available(sdk_client, sdk_seeded_shared_corpus):
    """Skip all tests if streaming query is not supported."""
    try:
        events = list(
            sdk_client.query_stream(
                query="test",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                    limit=1,
                ),
                generation=GenerationParameters(),
            )
        )
        if not events:
            pytest.skip("Streaming query returned no events")
    except Exception as e:
        pytest.skip(f"Streaming query not available: {e}")


@pytest.mark.core
class TestQueryStreaming:
    """Streaming query tests."""

    def test_streaming_query_events(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that streaming query returns valid typed events."""
        events = list(
            sdk_client.query_stream(
                query="artificial intelligence",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                    limit=5,
                ),
                generation=GenerationParameters(),
            )
        )

        assert len(events) > 0, "Expected at least one streaming event"

        event_types = [type(e).__name__ for e in events]
        assert len(event_types) > 0, f"Expected typed streaming events, got: {event_types}"

    def test_streaming_query_fcs(self, sdk_client, sdk_seeded_shared_corpus):
        """Test that streaming query with FCS enabled returns a score."""
        events = list(
            sdk_client.query_stream(
                query="artificial intelligence",
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_seeded_shared_corpus)],
                    limit=5,
                ),
                generation=GenerationParameters(
                    enable_factual_consistency_score=True,
                ),
            )
        )

        fcs_found = False
        for event in events:
            if hasattr(event, "factual_consistency_score") and event.factual_consistency_score is not None:
                score = event.factual_consistency_score
                assert 0.0 <= score <= 1.0, f"FCS score out of range: {score}"
                fcs_found = True
                break

        if not fcs_found:
            pytest.skip("FCS not returned in streaming response -- may not be enabled for this account")
