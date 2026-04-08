"""
Agent Guardrails Tests

Verify guardrails configuration persists on agents.
"""

import uuid

import pytest


@pytest.fixture(scope="module", autouse=True)
def check_guardrails_available(client):
    """Skip all tests if guardrails API is not available."""
    resp = client.list_guardrails(limit=1)
    if not resp.success:
        pytest.skip(f"Guardrails API not available: {resp.status_code}")
    guardrails = resp.data.get("guardrails", [])
    if not guardrails:
        pytest.skip("No guardrails configured")


@pytest.mark.regression
class TestAgentGuardrails:
    """Guardrails configuration on agents."""

    def test_create_agent_with_guardrails(self, client, unique_id):
        """Create agent with guardrails config, verify it persists."""
        guardrails_resp = client.list_guardrails(limit=10)
        guardrails = guardrails_resp.data.get("guardrails", [])
        first_key = guardrails[0].get("key")

        agent_key = f"guardrail_agent_{unique_id}"
        resp = client.create_agent(
            name=f"Guardrail Agent {unique_id}",
            agent_key=agent_key,
            guardrails={
                "enabled": [{"guardrail_key": first_key}],
                "max_retries": 2,
            },
        )
        assert resp.success, f"Create agent with guardrails failed: {resp.status_code} - {resp.data}"

        try:
            get_resp = client.get_agent(agent_key)
            assert get_resp.success, f"GET agent failed: {get_resp.status_code}"

            agent_guardrails = get_resp.data.get("guardrails", {})
            enabled = agent_guardrails.get("enabled", [])
            assert len(enabled) > 0, f"Agent should have guardrails enabled: {agent_guardrails}"

            enabled_keys = [g.get("guardrail_key") for g in enabled]
            assert first_key in enabled_keys, \
                f"Expected guardrail {first_key} in enabled list: {enabled_keys}"
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass
