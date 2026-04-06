"""
Agent Session Advanced Tests

Core tests for agent session creation with metadata and message sending.
"""

import pytest


@pytest.mark.core
class TestAgentSessionAdvanced:
    def test_create_session_with_metadata(self, client, shared_agent):
        resp = client.create_agent_session(shared_agent, metadata={"topic": "astronomy", "test": True})
        assert resp.success, f"Create session with metadata failed: {resp.data}"
        session_key = resp.data.get("key")

        # Verify session exists and metadata returned
        get_resp = client.get_agent_session(shared_agent, session_key)
        assert get_resp.success
        session_metadata = get_resp.data.get("metadata", {})
        assert session_metadata.get("topic") == "astronomy", f"Expected metadata topic=astronomy, got: {session_metadata}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass

    def test_send_message_to_session(self, client, shared_agent):
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")
        session_key = session_resp.data.get("key")

        # Send message via execute_agent with explicit session
        exec_resp = client.execute_agent(
            agent_id=shared_agent,
            query_text="Tell me about vector search",
            session_id=session_key,
        )
        assert exec_resp.success, f"Send message failed: {exec_resp.data}"

        # Verify response has events with content
        events = exec_resp.data.get("events", [])
        assert len(events) > 0, f"Expected events in response, got: {exec_resp.data.keys()}"

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass
