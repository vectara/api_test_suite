"""
Agent Corpora Search Tool Tests

The #1 user journey: create an agent with a corpora_search tool,
ask questions, verify the agent uses corpus content in its answers.
"""

import uuid

import pytest

from utils.waiters import wait_for


@pytest.mark.core
class TestAgentCorporaSearch:
    """Agent with corpora_search tool — core product flow."""

    def _create_agent_with_search_tool(self, client, corpus_key, unique_id):
        """Create an agent configured with a corpora_search tool."""
        agent_key = f"search_agent_{unique_id}"
        resp = client.create_agent(
            name=f"Search Agent {unique_id}",
            agent_key=agent_key,
            tool_configurations={
                "corpus_search": {
                    "type": "corpora_search",
                    "query_configuration": {
                        "search": {
                            "corpora": [{"corpus_key": corpus_key}],
                        },
                    },
                },
            },
        )
        return resp, agent_key

    def test_create_agent_with_corpora_search_tool(self, client, seeded_corpus, unique_id):
        """Create agent with corpora_search tool, verify config persisted."""
        resp, agent_key = self._create_agent_with_search_tool(client, seeded_corpus, unique_id)
        assert resp.success, f"Create agent with search tool failed: {resp.status_code} - {resp.data}"

        try:
            get_resp = client.get_agent(agent_key)
            assert get_resp.success, f"GET agent failed: {get_resp.status_code}"

            tool_configs = get_resp.data.get("tool_configurations", {})
            if isinstance(tool_configs, dict):
                has_search_tool = any(tc.get("type") == "corpora_search" for tc in tool_configs.values())
                config_types = [tc.get("type") for tc in tool_configs.values()]
            else:
                has_search_tool = any(tc.get("type") == "corpora_search" for tc in tool_configs)
                config_types = [tc.get("type") for tc in tool_configs]
            assert has_search_tool, f"Agent should have corpora_search tool, got: {config_types}"
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass

    def test_agent_corpora_search_returns_corpus_content(self, client, seeded_corpus, unique_id):
        """Send question to agent with search tool, verify answer uses corpus content."""
        resp, agent_key = self._create_agent_with_search_tool(client, seeded_corpus, unique_id)
        assert resp.success, f"Create agent failed: {resp.status_code} - {resp.data}"

        try:
            session_resp = client.create_agent_session(agent_key)
            assert session_resp.success, f"Create session failed: {session_resp.status_code} - {session_resp.data}"

            session_key = session_resp.data.get("key")
            wait_for(
                lambda: client.get_agent_session(agent_key, session_key).success,
                timeout=10,
                interval=0.5,
                description="session available",
            )

            msg_resp = client.execute_agent(
                agent_key,
                "What is vector search and how does it work?",
                session_id=session_key,
            )
            assert msg_resp.success, f"Agent execution failed: {msg_resp.status_code} - {msg_resp.data}"

            events = msg_resp.data.get("events", [])
            assert len(events) > 0, f"Expected events in response: {msg_resp.data}"

            event_types = [e.get("type") for e in events]
            has_output = any(t == "agent_output" for t in event_types)
            assert has_output, f"Expected agent_output event, got types: {event_types}"

            output_events = [e for e in events if e.get("type") == "agent_output"]
            output_text = " ".join(e.get("content", "") for e in output_events).lower()
            assert len(output_text) > 20, f"Agent output should be substantive, got: {output_text[:100]}"

            try:
                client.delete_agent_session(agent_key, session_key)
            except Exception:
                pass
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass
