"""
Agent Execution Streaming Tests

Tests for agent execution event responses, verifying events arrive correctly.
The agent events endpoint returns JSON with an events array (not SSE).
"""

import pytest


@pytest.mark.core
class TestAgentExecutionStreaming:
    """Core tests for agent execution event responses."""

    def test_execute_agent_sse(self, client, shared_agent):
        """Send message to agent and verify events arrive in response."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        from utils.waiters import wait_for

        wait_for(
            lambda: client.get_agent_session(shared_agent, session_key).success,
            timeout=10,
            interval=0.5,
            description="session to be available",
        )

        response = client.execute_agent(shared_agent, "What is Vectara?", session_id=session_key)

        assert response.success, f"Agent execution failed: {response.status_code} - {response.data}"

        events = response.data.get("events", [])
        assert len(events) > 0, f"Expected at least one event, got: {response.data}"

        event_types = [e.get("type") for e in events]
        has_output = any("output" in et or "message" in et for et in event_types if et)
        assert has_output, f"No output event found. Event types: {event_types}"

        output_events = [e for e in events if "output" in e.get("type", "") or "message" in e.get("type", "")]
        has_content = any(e.get("content") or e.get("data") or e.get("messages") for e in output_events)
        assert has_content, f"Output events have no content: {output_events}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass
