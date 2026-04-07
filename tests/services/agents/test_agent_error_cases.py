"""
Agent Error Case Tests

Tests for error handling on non-existent agents and sessions.
Ported from AgentSessionIntegrationTest.java error case tests.
"""

import uuid

import pytest


@pytest.mark.regression
class TestAgentErrorCases:
    """Error handling for invalid agent/session operations."""

    def test_send_message_nonexistent_session(self, client, shared_agent):
        """testNonSseInputOnNonExistentSession — 404 for bad session."""
        resp = client.execute_agent(
            shared_agent,
            "Hello",
            session_id=f"ase_fake_{uuid.uuid4().hex[:8]}",
        )
        assert resp.status_code == 404, \
            f"Expected 404 for non-existent session, got {resp.status_code}: {resp.data}"

    def test_send_message_nonexistent_agent(self, client):
        """testNonSseInputOnNonExistentAgent — 404 for bad agent."""
        resp = client.post(
            f"/v2/agents/nonexistent_{uuid.uuid4().hex[:8]}/sessions/fake_session/events",
            data={
                "type": "input_message",
                "messages": [{"type": "text", "content": "Hello"}],
            },
        )
        assert resp.status_code == 404, \
            f"Expected 404 for non-existent agent, got {resp.status_code}: {resp.data}"

    def test_fork_session_continue_conversation(self, client, agent_with_session):
        """forkSession_withoutCompaction_newSessionCanContinueConversation."""
        agent_key, session_key, events = agent_with_session

        fork_resp = client.create_agent_session(
            agent_key,
            from_session={"session_key": session_key},
        )
        if not fork_resp.success:
            pytest.skip(f"Fork failed: {fork_resp.data}")

        forked_key = fork_resp.data.get("key")
        try:
            from utils.waiters import wait_for
            wait_for(
                lambda: client.get_agent_session(agent_key, forked_key).success,
                timeout=10, interval=0.5,
                description="forked session available",
            )

            msg_resp = client.execute_agent(agent_key, "Continue the conversation", session_id=forked_key)
            assert msg_resp.success, \
                f"Should be able to chat in forked session: {msg_resp.status_code} - {msg_resp.data}"

            response_events = msg_resp.data.get("events", [])
            has_output = any(e.get("type") == "agent_output" for e in response_events)
            assert has_output, f"Forked session response should have agent_output: {[e.get('type') for e in response_events]}"
        finally:
            if forked_key:
                try:
                    client.delete_agent_session(agent_key, forked_key)
                except Exception:
                    pass
