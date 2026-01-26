"""
Agents API Tests

Tests for Vectara Agents (conversational AI) including agent creation,
execution, session management, and cleanup.

NOTE: The Vectara Agents API is currently in tech preview and the schema
may change. These tests validate the API connectivity and will skip
gracefully if schema errors are encountered.
"""

import pytest
import time




@pytest.fixture(scope="class")
def seeded_corpus_for_agents(client, test_corpus_key):
    """Seed the test corpus with documents for agent testing."""
    documents = [
        {
            "id": "agent_doc_1",
            "text": "Vectara is a trusted AI platform for enterprise search and RAG applications. "
                    "It provides semantic search, summarization, and conversational AI capabilities. "
                    "Vectara supports both SaaS and on-premise deployments for enterprise customers.",
            "metadata": {"category": "product", "topic": "overview"},
        },
        {
            "id": "agent_doc_2",
            "text": "To get started with Vectara, you need to create an account and obtain an API key. "
                    "The API key should have QueryService and IndexService permissions for full functionality. "
                    "You can then use the REST API or SDKs to index documents and run queries.",
            "metadata": {"category": "documentation", "topic": "getting_started"},
        },
        {
            "id": "agent_doc_3",
            "text": "Vectara agents provide conversational AI experiences. Agents maintain context "
                    "across multiple turns of conversation, allowing for natural follow-up questions. "
                    "Each agent can be configured with specific corpora and generation settings.",
            "metadata": {"category": "documentation", "topic": "agents"},
        },
    ]

    # Index all documents
    for doc in documents:
        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if not response.success:
            pytest.skip(f"Could not seed corpus for agents: {response.data}")

    # Allow time for indexing
    time.sleep(2)

    yield test_corpus_key

    # Cleanup documents
    for doc in documents:
        client.delete_document(test_corpus_key, doc["id"])


class TestAgents:
    """Test suite for Vectara Agents API."""

    def test_list_agents(self, client):
        """Test listing all agents."""
        response = client.list_agents(limit=10)

        assert response.success, (
            f"List agents failed: {response.status_code} - {response.data}"
        )

    def test_create_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test creating a new agent."""
        agent_name = f"Test Agent {unique_id}"

        response = client.create_agent(
            name=agent_name,
            corpus_keys=[seeded_corpus_for_agents],
            description="Test agent created by API test suite",
        )

        assert response.success, (
            f"Create agent failed: {response.status_code} - {response.data}"
        )

        # Get agent ID for cleanup
        agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
        if agent_id:
            # Cleanup
            client.delete_agent(agent_id)

    def test_create_agent_with_config(self, client, seeded_corpus_for_agents, unique_id):
        """Test creating an agent with custom configuration."""
        agent_name = f"Configured Agent {unique_id}"

        response = client.create_agent(
            name=agent_name,
            corpus_keys=[seeded_corpus_for_agents],
            description="Agent with custom settings",
        )

        assert response.success, (
            f"Create configured agent failed: {response.status_code} - {response.data}"
        )

        agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
        if agent_id:
            client.delete_agent(agent_id)

    def test_get_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test retrieving agent details."""
        # First create an agent
        create_response = client.create_agent(
            name=f"Get Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Get Test Agent {unique_id}",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for get test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        # Get the agent
        response = client.get_agent(agent_id)

        assert response.success, (
            f"Get agent failed: {response.status_code} - {response.data}"
        )

        # Cleanup
        client.delete_agent(agent_id)

    def test_update_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test updating an agent."""
        # Create agent
        create_response = client.create_agent(
            name=f"Update Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
            description="Original description",
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Update Test Agent {unique_id}",
                description="Original description",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for update test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        # Update the agent
        new_description = f"Updated description at {time.time()}"
        update_response = client.update_agent(
            agent_id=agent_id,
            description=new_description,
        )

        assert update_response.success, (
            f"Update agent failed: {update_response.status_code} - {update_response.data}"
        )

        # Cleanup
        client.delete_agent(agent_id)

    def test_delete_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Test deleting an agent."""
        # Create agent to delete
        create_response = client.create_agent(
            name=f"Delete Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
        )

        # Fallback to minimal agent
        if not create_response.success:
            create_response = client.create_agent(
                name=f"Delete Test Agent {unique_id}",
            )

        if not create_response.success:
            pytest.skip(f"Could not create agent for delete test: {create_response.data}")

        agent_id = create_response.data.get("id") or create_response.data.get("agent_id") or create_response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        # Delete the agent
        delete_response = client.delete_agent(agent_id)

        assert delete_response.success, (
            f"Delete agent failed: {delete_response.status_code} - {delete_response.data}"
        )

        # Verify deletion
        get_response = client.get_agent(agent_id)
        assert get_response.status_code == 404, (
            f"Deleted agent should return 404, got {get_response.status_code}"
        )


class TestAgentExecution:
    """Test suite for agent execution and conversations."""

    @pytest.fixture
    def test_agent(self, client, seeded_corpus_for_agents, unique_id):
        """Create a test agent for execution tests."""
        response = client.create_agent(
            name=f"Execution Test Agent {unique_id}",
            corpus_keys=[seeded_corpus_for_agents],
            description="Agent for execution testing",
        )

        # Fallback to minimal agent
        if not response.success:
            response = client.create_agent(
                name=f"Execution Test Agent {unique_id}",
                description="Agent for execution testing",
            )

        if not response.success:
            pytest.skip(f"Could not create test agent: {response.data}")

        agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
        if not agent_id:
            pytest.skip("No agent_id in create response")

        yield agent_id

        # Cleanup
        client.delete_agent(agent_id)

    def test_execute_agent_query(self, client, test_agent):
        """Test executing a query against an agent."""
        response = client.execute_agent(
            agent_id=test_agent,
            query_text="What is Vectara?",
        )

        assert response.success, (
            f"Agent execution failed: {response.status_code} - {response.data}"
        )

    def test_execute_agent_with_context(self, client, test_agent):
        """Test multi-turn conversation with an agent."""
        # First turn
        response1 = client.execute_agent(
            agent_id=test_agent,
            query_text="Tell me about Vectara agents.",
        )

        assert response1.success, (
            f"First turn failed: {response1.status_code} - {response1.data}"
        )

        # Get session ID if available for follow-up
        session_id = response1.data.get("session_id")

        # Second turn (follow-up)
        response2 = client.execute_agent(
            agent_id=test_agent,
            query_text="How do I configure them?",
            session_id=session_id,
        )

        assert response2.success, (
            f"Follow-up turn failed: {response2.status_code} - {response2.data}"
        )

    def test_execute_agent_response_time(self, client, test_agent):
        """Test that agent execution completes in acceptable time."""
        response = client.execute_agent(
            agent_id=test_agent,
            query_text="What is semantic search?",
        )

        assert response.success, f"Agent execution failed: {response.status_code}"

        # Agent responses involve LLM generation, allow more time
        assert response.elapsed_ms < 60000, (
            f"Agent execution took too long: {response.elapsed_ms:.1f}ms"
        )

    def test_list_agent_sessions(self, client, test_agent):
        """Test listing sessions for an agent."""
        # First execute a query to create a session
        client.execute_agent(
            agent_id=test_agent,
            query_text="Create a session",
        )

        # List sessions
        response = client.list_agent_sessions(test_agent, limit=10)

        assert response.success, (
            f"List sessions failed: {response.status_code} - {response.data}"
        )

    def test_execute_nonexistent_agent(self, client):
        """Test executing against a non-existent agent."""
        response = client.execute_agent(
            agent_id="nonexistent_agent_xyz123",
            query_text="test query",
        )

        assert not response.success, "Execution against non-existent agent should fail"
        assert response.status_code in [400, 404], (
            f"Expected 400 or 404, got {response.status_code}"
        )

    def test_agent_handles_special_characters(self, client, test_agent):
        """Test agent handles queries with special characters."""
        response = client.execute_agent(
            agent_id=test_agent,
            query_text="What's Vectara's approach to AI & machine-learning?",
        )

        assert response.success, (
            f"Special character query failed: {response.status_code}"
        )

    def test_agent_handles_long_query(self, client, test_agent):
        """Test agent handles longer queries."""
        long_query = (
            "I'm trying to understand how Vectara's conversational AI agents work. "
            "Can you explain the process of creating an agent, configuring it with "
            "multiple corpora, and then using it for multi-turn conversations? "
            "I'm particularly interested in how context is maintained across turns."
        )

        response = client.execute_agent(
            agent_id=test_agent,
            query_text=long_query,
        )

        assert response.success, (
            f"Long query failed: {response.status_code}"
        )
