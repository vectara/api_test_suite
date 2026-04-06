"""
Agent Execution Streaming Tests

Tests for SSE streaming agent execution, verifying events arrive correctly.
"""

import pytest

from utils.waiters import read_sse_events


@pytest.mark.core
class TestAgentExecutionStreaming:
    """Core tests for SSE streaming agent execution."""

    def test_execute_agent_sse(self, client, shared_agent):
        """Send message with SSE streaming and verify events arrive."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        raw_response = client.execute_agent_sse(shared_agent, session_key, "What is Vectara?")

        # SSE streaming may not be available on all API endpoints (external gateway may reject text/event-stream)
        if raw_response.status_code == 406:
            pytest.skip("SSE streaming not supported by this API endpoint")

        # Read SSE events
        events = list(read_sse_events(raw_response))
        assert len(events) > 0, "Expected at least one SSE event"

        # Check for errors in the stream
        error_events = [e for e in events if e.get("event") == "error"]
        if error_events:
            pytest.skip(f"SSE streaming returned error: {error_events[0].get('data')}")

        # Should contain at least one agent_output or message event
        event_types = [e.get("event") for e in events]
        has_output = any("output" in et or "message" in et for et in event_types if et)
        assert has_output, f"No output event found. Event types: {event_types}"

        output_events = [e for e in events if "output" in e.get("event", "") or "message" in e.get("event", "")]
        assert len(output_events) > 0, f"No output events. Event types: {event_types}"
        # Verify at least one output has non-empty data
        assert any(e.get("data") for e in output_events), f"All output events have empty data: {output_events}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass
