"""
Agent Session CRUD Tests

Tests for session create, get, update, delete operations and error cases.
Ported from AgentSessionIntegrationTest.java.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestSessionCrud:
    """Session create, get, update, delete operations."""

    def test_create_session_returns_key(self, client, shared_agent):
        """testCreateSession — verify session key is returned."""
        resp = client.create_agent_session(shared_agent)
        assert resp.success, f"Create session failed: {resp.status_code} - {resp.data}"

        session_key = resp.data.get("key")
        assert session_key is not None, f"Response should contain 'key': {resp.data}"
        assert resp.data.get("agent_key") == shared_agent

        try:
            client.delete_agent_session(shared_agent, session_key)
        except Exception:
            pass

    def test_create_session_default_values(self, client, shared_agent):
        """testCreateSessionDefaultValues — verify defaults are set."""
        resp = client.create_agent_session(shared_agent)
        assert resp.success

        session_key = resp.data.get("key")
        try:
            assert resp.data.get("enabled") is True, f"New session should be enabled: {resp.data}"
        finally:
            if session_key:
                try:
                    client.delete_agent_session(shared_agent, session_key)
                except Exception:
                    pass

    def test_create_session_agent_not_found(self, client):
        """testCreateSessionAgentNotFound — non-existent agent returns 404."""
        resp = client.create_agent_session(f"nonexistent_{uuid.uuid4().hex[:8]}")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.data}"

    def test_get_session(self, client, shared_agent):
        """testGetSession — verify all expected fields present."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            get_resp = client.get_agent_session(shared_agent, session_key)
            assert get_resp.success, f"Get session failed: {get_resp.status_code}"
            assert get_resp.data.get("key") == session_key
            assert get_resp.data.get("agent_key") == shared_agent
            assert "enabled" in get_resp.data
            assert "created_at" in get_resp.data
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_get_session_not_found(self, client, shared_agent):
        """testGetSessionNotFound — non-existent session returns 404."""
        resp = client.get_agent_session(shared_agent, f"ase_fake_{uuid.uuid4().hex[:8]}")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_delete_session(self, client, shared_agent):
        """testDeleteSession — delete and verify 404."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        del_resp = client.delete_agent_session(shared_agent, session_key)
        assert del_resp.success, f"Delete failed: {del_resp.status_code}"

        get_resp = client.get_agent_session(shared_agent, session_key)
        assert get_resp.status_code == 404

    def test_delete_session_not_found(self, client, shared_agent):
        """testDeleteSessionNotFound — delete non-existent returns 404."""
        resp = client.delete_agent_session(shared_agent, f"ase_fake_{uuid.uuid4().hex[:8]}")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


@pytest.mark.core
class TestSessionUpdate:
    """Session update operations — partial PATCH tests."""

    def test_update_session_description(self, client, shared_agent):
        """testUpdateSessionPartialUpdateDescriptionOnly."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            new_desc = f"Updated desc {uuid.uuid4().hex[:8]}"
            update_resp = client.update_agent_session(shared_agent, session_key, description=new_desc)
            assert update_resp.success, f"Update failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_agent_session(shared_agent, session_key)
            assert get_resp.data.get("description") == new_desc, \
                f"Description not persisted: {get_resp.data.get('description')}"
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_update_session_name(self, client, shared_agent):
        """testUpdateSessionNameOnly."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            new_name = f"Session {uuid.uuid4().hex[:8]}"
            update_resp = client.update_agent_session(shared_agent, session_key, name=new_name)
            assert update_resp.success, f"Update failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_agent_session(shared_agent, session_key)
            assert get_resp.data.get("name") == new_name
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_update_session_enabled(self, client, shared_agent):
        """testUpdateSessionEnabledOnly — disable then re-enable."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            disable_resp = client.update_agent_session(shared_agent, session_key, enabled=False)
            assert disable_resp.success, f"Disable failed: {disable_resp.status_code} - {disable_resp.data}"

            get_resp = client.get_agent_session(shared_agent, session_key)
            assert get_resp.data.get("enabled") is False

            enable_resp = client.update_agent_session(shared_agent, session_key, enabled=True)
            assert enable_resp.success

            get_resp2 = client.get_agent_session(shared_agent, session_key)
            assert get_resp2.data.get("enabled") is True
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_update_session_metadata(self, client, shared_agent):
        """testUpdateSessionMetadataOnly."""
        create_resp = client.create_agent_session(shared_agent, metadata={"initial": "value"})
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            new_meta = {"priority": "high", "status": "escalated"}
            update_resp = client.update_agent_session(shared_agent, session_key, metadata=new_meta)
            assert update_resp.success, f"Update failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_agent_session(shared_agent, session_key)
            metadata = get_resp.data.get("metadata", {})
            assert metadata.get("priority") == "high", f"Metadata not updated: {metadata}"
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_update_session_nonexistent(self, client, shared_agent):
        """testUpdateSessionNonexistent — update non-existent returns 404."""
        resp = client.update_agent_session(
            shared_agent, f"ase_fake_{uuid.uuid4().hex[:8]}", description="nope"
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_update_session_with_special_characters(self, client, shared_agent):
        """testUpdateSessionWithSpecialCharacters — unicode in name/description."""
        create_resp = client.create_agent_session(shared_agent)
        if not create_resp.success:
            pytest.skip(f"Could not create session: {create_resp.data}")

        session_key = create_resp.data.get("key")
        try:
            update_resp = client.update_agent_session(
                shared_agent, session_key,
                name="Session with emojis \U0001f680\U0001f4a1",
                description="Description with accents: caf\u00e9, na\u00efve, r\u00e9sum\u00e9",
            )
            assert update_resp.success, f"Update with special chars failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_agent_session(shared_agent, session_key)
            assert "\U0001f680" in get_resp.data.get("name", "")
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass
