"""
Agent Session Compaction Tests (SDK)

Tests for compaction config on agents.
"""

import pytest

from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage

from utils.waiters import wait_for


def _session_exists(sdk_client, agent_key, session_key):
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


@pytest.mark.core
class TestCompactionConfig:
    """Agent compaction configuration tests."""

    def test_create_agent_and_verify_config(self, sdk_client, sdk_shared_agent):
        """Verify agent can be retrieved with expected fields."""
        retrieved = sdk_client.agents.get(sdk_shared_agent)
        assert retrieved.key == sdk_shared_agent
        assert retrieved.name is not None

    def test_update_agent_description(self, sdk_client, sdk_shared_agent):
        """Verify agent description can be updated."""
        # Save original description to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_description = original.description

        try:
            sdk_client.agents.update(sdk_shared_agent, description="Updated compaction config")

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.description == "Updated compaction config"
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)


@pytest.mark.core
class TestManualCompaction:
    """Manual compaction via multi-turn sessions."""

    def test_multi_turn_session(self, sdk_client, sdk_shared_agent):
        """Create session on shared agent, send multiple turns, verify events accumulate."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            wait_for(
                lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
                timeout=10,
                interval=0.5,
                description="session available",
            )

            for msg in ["Tell me about AI", "What about machine learning?", "How do neural networks work?"]:
                sdk_client.agent_events.create(
                    sdk_shared_agent,
                    session_key,
                    request=CreateAgentEventsRequestBody_InputMessage(
                        messages=[{"type": "text", "content": msg}],
                        stream_response=False,
                    ),
                )

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) >= 3, (
                f"Expected at least 3 events after 3 turns, got {len(events)}"
            )
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
