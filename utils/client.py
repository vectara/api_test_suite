"""
Vectara API Client wrapper for the test suite.

Provides a clean interface for all Vectara API operations with:
- Automatic authentication via API key
- Request/response logging
- Retry logic with exponential backoff
- Response time tracking
"""

import time
import logging
from typing import Any, Optional
from dataclasses import dataclass, field

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config


@dataclass
class APIResponse:
    """Wrapper for API responses with metadata."""
    status_code: int
    data: Any
    elapsed_ms: float
    headers: dict = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return 200 <= self.status_code < 300


class VectaraClient:
    """HTTP client for Vectara API with authentication and retry support."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session with retry configuration."""
        if self._session is None:
            self._session = requests.Session()

            # Configure retry strategy
            retry_strategy = Retry(
                total=self.config.max_retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("https://", adapter)
            self._session.mount("http://", adapter)

            # Set default headers
            self._session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-api-key": self.config.api_key or "",
            })

        return self._session

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        base = self.config.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/{endpoint}"

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> APIResponse:
        """
        Make an API request with timing and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body (will be JSON encoded)
            params: Query parameters
            headers: Additional headers

        Returns:
            APIResponse with status, data, and timing
        """
        url = self._build_url(endpoint)
        request_headers = {**(headers or {})}

        self.logger.debug(f"{method} {url}")

        start_time = time.time()

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.config.request_timeout,
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text

            self.logger.debug(f"Response: {response.status_code} ({elapsed_ms:.1f}ms)")

            return APIResponse(
                status_code=response.status_code,
                data=response_data,
                elapsed_ms=elapsed_ms,
                headers=dict(response.headers),
            )

        except requests.exceptions.Timeout:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Request timeout after {elapsed_ms:.1f}ms")
            return APIResponse(
                status_code=408,
                data=None,
                elapsed_ms=elapsed_ms,
                error="Request timeout",
            )

        except requests.exceptions.ConnectionError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Connection error: {e}")
            return APIResponse(
                status_code=0,
                data=None,
                elapsed_ms=elapsed_ms,
                error=f"Connection error: {str(e)}",
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Unexpected error: {e}")
            return APIResponse(
                status_code=0,
                data=None,
                elapsed_ms=elapsed_ms,
                error=f"Unexpected error: {str(e)}",
            )

    # -------------------------------------------------------------------------
    # Convenience methods for HTTP verbs
    # -------------------------------------------------------------------------

    def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> APIResponse:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[dict] = None, **kwargs) -> APIResponse:
        """Make a POST request."""
        return self._request("POST", endpoint, data=data, **kwargs)

    def put(self, endpoint: str, data: Optional[dict] = None, **kwargs) -> APIResponse:
        """Make a PUT request."""
        return self._request("PUT", endpoint, data=data, **kwargs)

    def patch(self, endpoint: str, data: Optional[dict] = None, **kwargs) -> APIResponse:
        """Make a PATCH request."""
        return self._request("PATCH", endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    # -------------------------------------------------------------------------
    # Vectara API Operations - Corpora
    # -------------------------------------------------------------------------

    def list_corpora(self, limit: int = 100, page_key: Optional[str] = None) -> APIResponse:
        """List all corpora for the customer."""
        params = {"limit": limit}
        if page_key:
            params["page_key"] = page_key
        return self.get("/v2/corpora", params=params)

    def create_corpus(self, name: str, description: str = "", **kwargs) -> APIResponse:
        """Create a new corpus."""
        data = {
            "key": name.lower().replace(" ", "_"),
            "name": name,
            "description": description,
            **kwargs,
        }
        return self.post("/v2/corpora", data=data)

    def get_corpus(self, corpus_key: str) -> APIResponse:
        """Get corpus details by key."""
        return self.get(f"/v2/corpora/{corpus_key}")

    def delete_corpus(self, corpus_key: str) -> APIResponse:
        """Delete a corpus by key."""
        return self.delete(f"/v2/corpora/{corpus_key}")

    def update_corpus(self, corpus_key: str, **kwargs) -> APIResponse:
        """Update corpus properties."""
        return self.patch(f"/v2/corpora/{corpus_key}", data=kwargs)

    # -------------------------------------------------------------------------
    # Vectara API Operations - Documents (Indexing)
    # -------------------------------------------------------------------------

    def index_document(
        self,
        corpus_key: str,
        document_id: str,
        text: str,
        metadata: Optional[dict] = None,
        **kwargs,
    ) -> APIResponse:
        """Index a single document into a corpus."""
        data = {
            "id": document_id,
            "type": "core",
            "document_parts": [
                {
                    "text": text,
                    "metadata": metadata or {},
                }
            ],
            **kwargs,
        }
        return self.post(f"/v2/corpora/{corpus_key}/documents", data=data)

    def list_documents(
        self,
        corpus_key: str,
        limit: int = 100,
        page_key: Optional[str] = None,
    ) -> APIResponse:
        """List documents in a corpus."""
        params = {"limit": limit}
        if page_key:
            params["page_key"] = page_key
        return self.get(f"/v2/corpora/{corpus_key}/documents", params=params)

    def get_document(self, corpus_key: str, document_id: str) -> APIResponse:
        """Get a specific document."""
        return self.get(f"/v2/corpora/{corpus_key}/documents/{document_id}")

    def delete_document(self, corpus_key: str, document_id: str) -> APIResponse:
        """Delete a document from a corpus."""
        return self.delete(f"/v2/corpora/{corpus_key}/documents/{document_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Query (Search)
    # -------------------------------------------------------------------------

    def query(
        self,
        corpus_key: str,
        query_text: str,
        limit: int = 10,
        offset: int = 0,
        **kwargs,
    ) -> APIResponse:
        """Execute a query against a corpus."""
        data = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
                "limit": limit,
                "offset": offset,
            },
            **kwargs,
        }
        return self.post("/v2/query", data=data)

    def query_with_summary(
        self,
        corpus_key: str,
        query_text: str,
        summarizer: str = None,
        max_results: int = 10,
        **kwargs,
    ) -> APIResponse:
        """Execute a query with RAG summarization.

        If summarizer is None, uses the instance's default generation preset.
        """
        generation_config = {
            "max_used_search_results": max_results,
        }
        if summarizer:
            generation_config["generation_preset_name"] = summarizer

        data = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
                "limit": max_results,
            },
            "generation": generation_config,
            **kwargs,
        }
        return self.post("/v2/query", data=data)

    # -------------------------------------------------------------------------
    # Vectara API Operations - Chat
    # -------------------------------------------------------------------------

    def create_chat(self, corpus_key: str, query_text: str, **kwargs) -> APIResponse:
        """Start a new chat conversation.

        Note: Omits generation config to use instance defaults and avoid rephraser issues.
        """
        data = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
            },
            "chat": {"store": True},
            **kwargs,
        }
        return self.post("/v2/chats", data=data)

    def list_chats(self, limit: int = 100) -> APIResponse:
        """List all chat conversations."""
        return self.get("/v2/chats", params={"limit": limit})

    def get_chat(self, chat_id: str) -> APIResponse:
        """Get a specific chat conversation."""
        return self.get(f"/v2/chats/{chat_id}")

    def delete_chat(self, chat_id: str) -> APIResponse:
        """Delete a chat conversation."""
        return self.delete(f"/v2/chats/{chat_id}")

    def add_chat_turn(self, chat_id: str, query_text: str, corpus_key: str, **kwargs) -> APIResponse:
        """Add a turn to an existing chat."""
        data = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
            },
            **kwargs,
        }
        return self.post(f"/v2/chats/{chat_id}/turns", data=data)

    # -------------------------------------------------------------------------
    # Vectara API Operations - API Keys (Admin)
    # -------------------------------------------------------------------------

    def list_api_keys(self) -> APIResponse:
        """List all API keys."""
        return self.get("/v2/api_keys")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Jobs
    # -------------------------------------------------------------------------

    def list_jobs(self, limit: int = 100) -> APIResponse:
        """List background jobs."""
        return self.get("/v2/jobs", params={"limit": limit})

    def get_job(self, job_id: str) -> APIResponse:
        """Get job status."""
        return self.get(f"/v2/jobs/{job_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Agents
    # -------------------------------------------------------------------------

    def list_agents(self, limit: int = 100) -> APIResponse:
        """List all agents."""
        return self.get("/v2/agents", params={"limit": limit})

    def create_agent(
        self,
        name: str,
        corpus_keys: list[str] = None,
        description: str = "",
        model_name: str = "gpt-4o",
        agent_key: str = None,
        **kwargs,
    ) -> APIResponse:
        """Create a new agent for conversational AI.

        Args:
            name: Agent name (display name)
            corpus_keys: Optional list of corpus keys for RAG search tool
            description: Agent description
            model_name: LLM model name (default: gpt-4o)
            agent_key: Unique key for the agent (auto-generated if not provided)
        """
        import uuid

        # Generate agent key if not provided
        if not agent_key:
            agent_key = f"test_agent_{uuid.uuid4().hex[:8]}"

        # Build first_step with type "conversational" and required output_parser
        first_step = {
            "type": "conversational",
            "output_parser": {
                "type": "default",
            },
        }

        # Build model configuration
        model = {
            "name": model_name,
        }

        data = {
            "key": agent_key,
            "name": name,
            "description": description,
            "model": model,
            "first_step": first_step,
            **kwargs,
        }

        # Note: corpus_keys parameter is accepted but not used in agent creation
        # Corpus association for agents is handled through tool configuration
        # which requires additional setup. Basic agents work without it.

        return self.post("/v2/agents", data=data)

    def get_agent(self, agent_id: str) -> APIResponse:
        """Get agent details."""
        return self.get(f"/v2/agents/{agent_id}")

    def delete_agent(self, agent_id: str) -> APIResponse:
        """Delete an agent."""
        return self.delete(f"/v2/agents/{agent_id}")

    def update_agent(self, agent_id: str, **kwargs) -> APIResponse:
        """Update agent properties."""
        return self.patch(f"/v2/agents/{agent_id}", data=kwargs)

    def create_agent_session(self, agent_key: str) -> APIResponse:
        """Create a new session for an agent."""
        return self.post(f"/v2/agents/{agent_key}/sessions", data={})

    def execute_agent(
        self,
        agent_id: str,
        query_text: str,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute a query against an agent.

        If no session_id is provided, creates a new session first.
        """
        # If no session provided, create one first
        if not session_id:
            session_response = self.create_agent_session(agent_id)
            if not session_response.success:
                return session_response
            session_id = session_response.data.get("key") or session_response.data.get("session_key")
            if not session_id:
                return APIResponse(
                    status_code=500,
                    data={"error": "Could not get session key from response"},
                    elapsed_ms=0,
                )

        # Send message to agent session
        data = {
            "type": "input_message",
            "messages": [
                {
                    "type": "text",
                    "content": query_text,
                }
            ],
            **kwargs,
        }
        return self.post(f"/v2/agents/{agent_id}/sessions/{session_id}/events", data=data)

    def list_agent_sessions(self, agent_id: str, limit: int = 100) -> APIResponse:
        """List sessions for an agent."""
        return self.get(f"/v2/agents/{agent_id}/sessions", params={"limit": limit})

    def get_agent_session(self, agent_id: str, session_id: str) -> APIResponse:
        """Get a specific agent session."""
        return self.get(f"/v2/agents/{agent_id}/sessions/{session_id}")

    def delete_agent_session(self, agent_id: str, session_id: str) -> APIResponse:
        """Delete an agent session."""
        return self.delete(f"/v2/agents/{agent_id}/sessions/{session_id}")

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    def health_check(self) -> APIResponse:
        """Verify API connectivity and authentication."""
        return self.list_corpora(limit=1)
