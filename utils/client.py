"""
Vectara API Client wrapper for the test suite.

Provides a clean interface for all Vectara API operations with:
- Automatic authentication via API key
- Request/response logging
- Retry logic with exponential backoff
- Response time tracking
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

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
        self.generation_preset = self.config.generation_preset
        self.llm_name = self.config.llm_name

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
            self._session.headers.update(
                {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "x-api-key": self.config.api_key or "",
                }
            )

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

    def _request_raw(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        files: Optional[dict] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Make an API request and return the raw :class:`requests.Response`.

        This is useful for streaming responses (SSE) or multipart uploads
        where the caller needs direct access to the underlying response.

        When *files* is provided the request is sent as ``multipart/form-data``
        (using ``data=`` instead of ``json=``), and the ``Content-Type`` header
        is left for *requests* to set automatically so that the multipart
        boundary is included.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path.
            data: Request body.  Sent as JSON unless *files* is provided.
            params: Query parameters.
            headers: Additional headers (merged on top of session defaults).
            files: Mapping suitable for ``requests``' *files* parameter.
            stream: If ``True`` the response body is not downloaded eagerly.

        Returns:
            The raw :class:`requests.Response` object.
        """
        url = self._build_url(endpoint)
        request_headers = {**(headers or {})}

        self.logger.debug(f"{method} {url}")

        kwargs: dict = {
            "method": method,
            "url": url,
            "params": params,
            "headers": request_headers,
            "timeout": self.config.request_timeout,
            "stream": stream,
        }

        if files is not None:
            # Multipart upload -- use data= (not json=) and let requests
            # generate the Content-Type with the correct boundary.
            kwargs["data"] = data
            kwargs["files"] = files
            # Set Content-Type to None to override the session-level default
            # (application/json). This tells requests to omit it entirely and
            # auto-generate the multipart boundary.
            kwargs["headers"]["Content-Type"] = None
        else:
            kwargs["json"] = data

        return self.session.request(**kwargs)

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
    # Generation Config Helper
    # -------------------------------------------------------------------------

    def _build_generation_config(
        self,
        max_results: Optional[int] = None,
        preset: Optional[str] = None,
        llm_name: Optional[str] = None,
    ) -> dict:
        """Build generation config with preset and/or llm_name.

        Args:
            max_results: Maximum search results to use for generation (only added if provided).
            preset: Generation preset name (overrides instance default).
            llm_name: LLM model name (overrides instance default).

        Returns:
            Generation config dict for API request.
        """
        config = {}

        if max_results is not None:
            config["max_used_search_results"] = max_results

        # Use provided values or fall back to instance defaults
        preset = preset or self.generation_preset
        llm_name = llm_name or self.llm_name

        if preset:
            config["generation_preset_name"] = preset
        if llm_name:
            config["model_parameters"] = {"llm_name": llm_name}

        return config

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

    def replace_filter_attributes(
        self,
        corpus_key: str,
        filter_attributes: list[dict],
    ) -> APIResponse:
        """Replace the filter attributes of a corpus.

        Args:
            corpus_key: Target corpus key.
            filter_attributes: New filter attribute definitions.

        Returns:
            APIResponse with job_id and status (async operation).
        """
        return self.post(
            f"/v2/corpora/{corpus_key}/replace_filter_attributes",
            data={"filter_attributes": filter_attributes},
        )

    def compute_corpus_size(self, corpus_key: str) -> APIResponse:
        """Compute the current size of a corpus.

        Returns document count, part count, and character statistics.
        """
        return self.post(f"/v2/corpora/{corpus_key}/compute_size")

    def reset_corpus(self, corpus_key: str) -> APIResponse:
        """Remove all documents and data from a corpus."""
        return self.post(f"/v2/corpora/{corpus_key}/reset")

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

    def update_document_metadata(
        self,
        corpus_key: str,
        document_id: str,
        metadata: dict,
    ) -> APIResponse:
        """Update (merge) metadata on an existing document.

        Args:
            corpus_key: Target corpus key.
            document_id: Document to update.
            metadata: Metadata fields to merge into the document.

        Returns:
            APIResponse with the update result.
        """
        return self.patch(
            f"/v2/corpora/{corpus_key}/documents/{document_id}",
            data={"metadata": metadata},
        )

    def replace_document_metadata(
        self,
        corpus_key: str,
        document_id: str,
        metadata: dict,
    ) -> APIResponse:
        """Fully replace metadata on an existing document.

        Args:
            corpus_key: Target corpus key.
            document_id: Document whose metadata will be replaced.
            metadata: Complete metadata dict that replaces the current one.

        Returns:
            APIResponse with the replacement result.
        """
        return self.put(
            f"/v2/corpora/{corpus_key}/documents/{document_id}/metadata",
            data={"metadata": metadata},
        )

    def bulk_delete_documents(
        self,
        corpus_key: str,
        document_ids: Optional[list[str]] = None,
        metadata_filter: Optional[str] = None,
        async_mode: bool = True,
    ) -> APIResponse:
        """Bulk delete documents from a corpus.

        Args:
            corpus_key: Target corpus key.
            document_ids: List of document IDs to delete.
            metadata_filter: SQL-like filter expression for deletion.
            async_mode: If True (default), returns 202 with job_id.
                If False, waits for completion and returns 200.

        Returns:
            APIResponse with deletion result or job_id.
        """
        params: dict = {}
        if document_ids is not None:
            params["document_ids"] = ",".join(document_ids)
        if metadata_filter is not None:
            params["metadata_filter"] = metadata_filter
        if not async_mode:
            params["async"] = "false"
        return self._request("DELETE", f"/v2/corpora/{corpus_key}/documents", params=params)

    def index_document_parts(
        self,
        corpus_key: str,
        document_id: str,
        parts: list[dict],
        metadata: Optional[dict] = None,
        **kwargs,
    ) -> APIResponse:
        """Index a document with explicit parts into a corpus.

        Each part is a dict that must contain ``text`` and may optionally
        include ``metadata``, ``custom_dimensions``, and ``context``.

        Args:
            corpus_key: Target corpus key.
            document_id: Unique document identifier.
            parts: List of document part dicts.
            metadata: Optional document-level metadata.

        Returns:
            APIResponse with the indexing result.
        """
        data = {
            "id": document_id,
            "type": "core",
            "metadata": metadata or {},
            "document_parts": parts,
            **kwargs,
        }
        return self.post(f"/v2/corpora/{corpus_key}/documents", data=data)

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

    def query_corpus(
        self,
        corpus_key: str,
        query_text: str,
        limit: int = 10,
        custom_dimensions: Optional[dict] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute a query scoped to a single corpus via its dedicated endpoint.

        Unlike :meth:`query` which uses the global ``/v2/query`` endpoint,
        this hits ``/v2/corpora/{corpus_key}/query`` directly.

        Args:
            corpus_key: The corpus to query.
            query_text: The query text.
            limit: Maximum number of search results.
            custom_dimensions: Optional custom dimension weights for the search.

        Returns:
            APIResponse with search results.
        """
        search: dict = {"limit": limit}
        if custom_dimensions is not None:
            search["custom_dimensions"] = custom_dimensions

        data: dict = {
            "query": query_text,
            "search": search,
            **kwargs,
        }
        return self.post(f"/v2/corpora/{corpus_key}/query", data=data)

    def query_with_summary(
        self,
        corpus_key: str,
        query_text: str,
        summarizer: Optional[str] = None,
        llm_name: Optional[str] = None,
        max_results: int = 10,
        **kwargs,
    ) -> APIResponse:
        """Execute a query with RAG summarization.

        Args:
            corpus_key: The corpus to query.
            query_text: The query text.
            summarizer: Generation preset name (overrides instance default).
            llm_name: LLM model name (overrides instance default).
            max_results: Maximum search results.

        If neither summarizer nor llm_name is provided, uses instance defaults.
        """
        generation_config = self._build_generation_config(
            max_results=max_results,
            preset=summarizer,
            llm_name=llm_name,
        )

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

    def query_stream(
        self,
        corpus_key: str,
        query_text: str,
        generation_config: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """Execute a streaming query and return the raw SSE response.

        Streaming requires ``stream_response: true`` in the request body
        and ``Accept: text/event-stream`` header.

        Args:
            corpus_key: The corpus to query.
            query_text: The query text.
            generation_config: Optional generation configuration dict.

        Returns:
            Raw streaming :class:`requests.Response`.
        """
        data: dict = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
            },
            "stream_response": True,
            **kwargs,
        }
        if generation_config is not None:
            data["generation"] = generation_config
        elif self.generation_preset or self.llm_name:
            data["generation"] = self._build_generation_config()

        return self._request_raw(
            method="POST",
            endpoint="/v2/query",
            data=data,
            headers={"Accept": "text/event-stream"},
            stream=True,
        )

    # -------------------------------------------------------------------------
    # Vectara API Operations - Chat
    # -------------------------------------------------------------------------

    def create_chat(self, corpus_key: str, query_text: str, **kwargs) -> APIResponse:
        """Start a new chat conversation.

        If generation_preset or llm_name is configured on the client, adds generation config.
        """
        data = {
            "query": query_text,
            "search": {
                "corpora": [{"corpus_key": corpus_key}],
            },
            "chat": {"store": True},
            **kwargs,
        }

        # Only add generation config if preset or llm_name is configured
        if self.generation_preset or self.llm_name:
            data["generation"] = self._build_generation_config()

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

    def list_chat_turns(self, chat_id: str) -> APIResponse:
        """List turns in a chat."""
        return self.get(f"/v2/chats/{chat_id}/turns")

    def get_chat_turn(self, chat_id: str, turn_id: str) -> APIResponse:
        """Get a specific turn in a chat."""
        return self.get(f"/v2/chats/{chat_id}/turns/{turn_id}")

    def update_chat_turn(self, chat_id: str, turn_id: str, **kwargs) -> APIResponse:
        """Update a turn in a chat (e.g., disable it)."""
        return self.patch(f"/v2/chats/{chat_id}/turns/{turn_id}", data=kwargs)

    def delete_chat_turn(self, chat_id: str, turn_id: str) -> APIResponse:
        """Delete a turn from a chat."""
        return self.delete(f"/v2/chats/{chat_id}/turns/{turn_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - API Keys (Admin)
    # -------------------------------------------------------------------------

    def list_api_keys(self) -> APIResponse:
        """List all API keys."""
        return self.get("/v2/api_keys")

    def create_api_key(
        self,
        name: str,
        api_key_role: str = "serving",
        corpus_keys: Optional[list[str]] = None,
        **kwargs,
    ) -> APIResponse:
        """Create a new API key.

        Args:
            name: Display name for the key.
            api_key_role: Role for the key (``serving`` or ``personal``).
            corpus_keys: Optional list of corpus keys to scope the key to.
        """
        data: dict = {
            "name": name,
            "api_key_role": api_key_role,
            **kwargs,
        }
        if corpus_keys is not None:
            data["corpus_keys"] = corpus_keys
        return self.post("/v2/api_keys", data=data)

    def delete_api_key(self, api_key_id: str) -> APIResponse:
        """Delete an API key by ID."""
        return self.delete(f"/v2/api_keys/{api_key_id}")

    def enable_api_key(self, api_key_id: str) -> APIResponse:
        """Enable a disabled API key."""
        return self.patch(f"/v2/api_keys/{api_key_id}", data={"enabled": True})

    def disable_api_key(self, api_key_id: str) -> APIResponse:
        """Disable an API key."""
        return self.patch(f"/v2/api_keys/{api_key_id}", data={"enabled": False})

    # -------------------------------------------------------------------------
    # Vectara API Operations - App Clients
    # -------------------------------------------------------------------------

    def create_app_client(
        self,
        name: str,
        type: str = "client_credentials",
        description: str = "",
        api_roles: Optional[list[dict]] = None,
        corpus_roles: Optional[list[dict]] = None,
        agent_roles: Optional[list[dict]] = None,
        **kwargs,
    ) -> APIResponse:
        """Create an app client.

        Args:
            name: Display name for the app client.
            type: Client type (default ``client_credentials``).
            description: Optional description.
            api_roles: Optional customer-level role assignments.
            corpus_roles: Optional corpus-specific role assignments.
            agent_roles: Optional agent-specific role assignments.
        """
        data: dict = {"name": name, "type": type, "description": description, **kwargs}
        if api_roles is not None:
            data["api_roles"] = api_roles
        if corpus_roles is not None:
            data["corpus_roles"] = corpus_roles
        if agent_roles is not None:
            data["agent_roles"] = agent_roles
        return self.post("/v2/app_clients", data=data)

    def list_app_clients(self, limit: int = 100) -> APIResponse:
        """List all app clients."""
        return self.get("/v2/app_clients", params={"limit": limit})

    def get_app_client(self, app_client_id: str) -> APIResponse:
        """Get an app client by ID."""
        return self.get(f"/v2/app_clients/{app_client_id}")

    def update_app_client(self, app_client_id: str, **kwargs) -> APIResponse:
        """Update an app client."""
        return self.patch(f"/v2/app_clients/{app_client_id}", data=kwargs)

    def delete_app_client(self, app_client_id: str) -> APIResponse:
        """Delete an app client by ID."""
        return self.delete(f"/v2/app_clients/{app_client_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Users
    # -------------------------------------------------------------------------

    def create_user(
        self,
        email: str,
        username: Optional[str] = None,
        api_roles: Optional[list[dict]] = None,
        corpus_roles: Optional[list[dict]] = None,
        agent_roles: Optional[list[dict]] = None,
        description: str = "",
        **kwargs,
    ) -> APIResponse:
        """Create a user in the current customer account.

        Args:
            email: User email address (required).
            username: Username (defaults to email if not provided).
            api_roles: Optional customer-level role assignments.
            corpus_roles: Optional corpus-specific role assignments.
            agent_roles: Optional agent-specific role assignments.
            description: Optional user description.
        """
        data: dict = {"email": email, "description": description, **kwargs}
        if username is not None:
            data["username"] = username
        if api_roles is not None:
            data["api_roles"] = api_roles
        if corpus_roles is not None:
            data["corpus_roles"] = corpus_roles
        if agent_roles is not None:
            data["agent_roles"] = agent_roles
        return self.post("/v2/users", data=data)

    def list_users(self, limit: int = 100) -> APIResponse:
        """List users in the account."""
        return self.get("/v2/users", params={"limit": limit})

    def get_user(self, username: str) -> APIResponse:
        """Get a user by username."""
        return self.get(f"/v2/users/{username}")

    def update_user(self, username: str, **kwargs) -> APIResponse:
        """Update a user.

        Supported fields: enabled, api_roles, corpus_roles, agent_roles, description.
        """
        return self.patch(f"/v2/users/{username}", data=kwargs)

    def delete_user(self, username: str) -> APIResponse:
        """Delete a user by username."""
        return self.delete(f"/v2/users/{username}")

    def reset_user_password(self, username: str) -> APIResponse:
        """Reset the password for a user."""
        return self.post(f"/v2/users/{username}/reset_password", data={})

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
        corpus_keys: Optional[list[str]] = None,
        description: str = "",
        model_name: Optional[str] = None,
        agent_key: Optional[str] = None,
        tool_configurations: Optional[dict] = None,
        **kwargs,
    ) -> APIResponse:
        """Create a new agent for conversational AI.

        Args:
            name: Agent name (display name)
            corpus_keys: Optional list of corpus keys for RAG search tool
            description: Agent description
            model_name: LLM model name (uses instance llm_name or defaults to gpt-4o)
            agent_key: Unique key for the agent (auto-generated if not provided)
            tool_configurations: Optional list of tool config dicts (e.g. corpora_search, web_search)
        """
        import uuid

        # Generate agent key if not provided
        if not agent_key:
            agent_key = f"test_agent_{uuid.uuid4().hex[:8]}"

        # Use provided model_name, fall back to instance llm_name, then default
        model_name = model_name or self.llm_name or "gpt-4o"

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

        if tool_configurations is not None:
            data["tool_configurations"] = tool_configurations

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

    def create_agent_session(
        self,
        agent_key: str,
        metadata: Optional[dict] = None,
        from_session: Optional[dict] = None,
    ) -> APIResponse:
        """Create a new session for an agent.

        Args:
            agent_key: The agent's unique key.
            metadata: Optional metadata dict to attach to the session.
            from_session: Optional dict to fork from an existing session.
                Must contain ``session_key`` and may optionally include
                ``include_up_to_event_id`` and/or ``compact_up_to_event_id``.

        Returns:
            APIResponse with the created session details.
        """
        data: dict = {}
        if metadata is not None:
            data["metadata"] = metadata
        if from_session is not None:
            data["from_session"] = from_session
        return self.post(f"/v2/agents/{agent_key}/sessions", data=data)

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
                    data={"error": f"No session key in response: {session_response.data}"},
                    elapsed_ms=0,
                )

            # Wait for session to be committed and queryable
            from utils.waiters import wait_for

            try:
                wait_for(
                    lambda: self.get_agent_session(agent_id, session_id).success,
                    timeout=10,
                    interval=0.5,
                    description=f"agent session {session_id} to become available",
                )
            except TimeoutError:
                return APIResponse(
                    status_code=500,
                    data={"error": f"Session {session_id} created but not available after 10s"},
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

    def update_agent_session(self, agent_key: str, session_key: str, **kwargs) -> APIResponse:
        """Update an agent session.

        Supported fields: name, description, metadata, enabled, tti_minutes.
        """
        return self.patch(f"/v2/agents/{agent_key}/sessions/{session_key}", data=kwargs)

    def compact_session(
        self,
        agent_key: str,
        session_key: str,
        compact_up_to_event_id: Optional[str] = None,
    ) -> APIResponse:
        """Send a manual compaction request to a session.

        Args:
            agent_key: The agent's unique key.
            session_key: The session's unique key.
            compact_up_to_event_id: Optional event ID to compact up to.
        """
        data: dict = {"type": "compact"}
        if compact_up_to_event_id is not None:
            data["compact_up_to_event_id"] = compact_up_to_event_id
        return self.post(f"/v2/agents/{agent_key}/sessions/{session_key}/events", data=data)

    def list_session_events(
        self,
        agent_key: str,
        session_key: str,
        limit: int = 100,
        include_hidden: bool = False,
    ) -> APIResponse:
        """List events in an agent session.

        Args:
            agent_key: The agent's unique key.
            session_key: The session's unique key.
            limit: Maximum number of events to return.
            include_hidden: If True, include hidden events in results.

        Returns:
            APIResponse with the list of session events.
        """
        params: dict = {"limit": limit}
        if include_hidden:
            params["include_hidden"] = True
        return self.get(
            f"/v2/agents/{agent_key}/sessions/{session_key}/events",
            params=params,
        )

    def hide_event(
        self,
        agent_key: str,
        session_key: str,
        event_id: str,
    ) -> APIResponse:
        """Hide an event in an agent session.

        Args:
            agent_key: The agent's unique key.
            session_key: The session's unique key.
            event_id: The event to hide.

        Returns:
            APIResponse with the hide result.
        """
        return self.post(
            f"/v2/agents/{agent_key}/sessions/{session_key}/events/{event_id}/hide",
            data={},
        )

    def unhide_event(
        self,
        agent_key: str,
        session_key: str,
        event_id: str,
    ) -> APIResponse:
        """Unhide an event in an agent session.

        Args:
            agent_key: The agent's unique key.
            session_key: The session's unique key.
            event_id: The event to unhide.

        Returns:
            APIResponse with the unhide result.
        """
        return self.post(
            f"/v2/agents/{agent_key}/sessions/{session_key}/events/{event_id}/unhide",
            data={},
        )

    def get_agent_identity(self, agent_key: str) -> APIResponse:
        """Get the identity configuration of an agent.

        Args:
            agent_key: The agent's unique key.

        Returns:
            APIResponse with the agent identity details.
        """
        return self.get(f"/v2/agents/{agent_key}/identity")

    def update_agent_identity(self, agent_key: str, **kwargs) -> APIResponse:
        """Update the identity configuration of an agent.

        Args:
            agent_key: The agent's unique key.
            **kwargs: Identity fields to update.

        Returns:
            APIResponse with the updated identity.
        """
        return self.patch(f"/v2/agents/{agent_key}/identity", data=kwargs)

    # -------------------------------------------------------------------------
    # Vectara API Operations - LLMs
    # -------------------------------------------------------------------------

    def list_llms(self, limit: int = 100) -> APIResponse:
        """List all LLMs configured for the account."""
        return self.get("/v2/llms", params={"limit": limit})

    def create_llm(
        self,
        name: str,
        model: str,
        uri: str,
        bearer_token: Optional[str] = None,
        llm_type: str = "openai-compatible",
        **kwargs,
    ) -> APIResponse:
        """Create a custom LLM configuration.

        Args:
            name: Display name for the LLM.
            model: Model identifier (e.g. ``gpt-4o-mini``).
            uri: Endpoint URI for the LLM API.
            bearer_token: Optional bearer token for authentication.
            llm_type: LLM type (default ``openai-compatible``).
        """
        data: dict = {
            "type": llm_type,
            "name": name,
            "model": model,
            "uri": uri,
            **kwargs,
        }
        if bearer_token is not None:
            data["auth"] = {"type": "bearer", "token": bearer_token}
        return self.post("/v2/llms", data=data)

    def delete_llm(self, llm_id: str) -> APIResponse:
        """Delete a custom LLM by ID."""
        return self.delete(f"/v2/llms/{llm_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Tools
    # -------------------------------------------------------------------------

    def list_tools(self, limit: int = 100) -> APIResponse:
        """List all tools configured for the account."""
        return self.get("/v2/tools", params={"limit": limit})

    def create_tool(
        self,
        name: str,
        title: str,
        description: str,
        code: str,
        execution_time: int = 30,
        max_memory: int = 128,
        **kwargs,
    ) -> APIResponse:
        """Create a lambda tool.

        Args:
            name: Unique tool name (letters, numbers, hyphens, underscores).
            title: Human-readable title.
            description: Tool description.
            code: Python function code.
            execution_time: Maximum execution time in seconds.
            max_memory: Maximum memory in MB.
        """
        data: dict = {
            "type": "lambda",
            "name": name,
            "title": title,
            "description": description,
            "code": code,
            "execution_configuration": {
                "max_execution_time_seconds": execution_time,
            },
            **kwargs,
        }
        return self.post("/v2/tools", data=data)

    def update_tool(self, tool_id: str, **kwargs) -> APIResponse:
        """Update tool properties."""
        return self.patch(f"/v2/tools/{tool_id}", data=kwargs)

    def delete_tool(self, tool_id: str) -> APIResponse:
        """Delete a tool by ID."""
        return self.delete(f"/v2/tools/{tool_id}")

    # -------------------------------------------------------------------------
    # Vectara API Operations - Pipelines
    # -------------------------------------------------------------------------

    def list_pipelines(self, limit: int = 100) -> APIResponse:
        """List all pipelines."""
        return self.get("/v2/pipelines", params={"limit": limit})

    def create_pipeline(
        self,
        name: str,
        key: str,
        source: dict,
        trigger: dict,
        transform: dict,
        **kwargs,
    ) -> APIResponse:
        """Create a new pipeline.

        Args:
            name: Pipeline display name.
            key: Unique pipeline key.
            source: Source configuration dict.
            trigger: Trigger configuration dict.
            transform: Transform configuration dict.
        """
        data: dict = {
            "name": name,
            "key": key,
            "source": source,
            "trigger": trigger,
            "transform": transform,
            **kwargs,
        }
        return self.post("/v2/pipelines", data=data)

    def delete_pipeline(self, pipeline_key: str) -> APIResponse:
        """Delete a pipeline by key."""
        return self.delete(f"/v2/pipelines/{pipeline_key}")

    def get_pipeline(self, pipeline_key: str) -> APIResponse:
        """Get a pipeline by key."""
        return self.get(f"/v2/pipelines/{pipeline_key}")

    def update_pipeline(self, pipeline_key: str, **kwargs) -> APIResponse:
        """Partially update a pipeline."""
        return self.patch(f"/v2/pipelines/{pipeline_key}", data=kwargs)

    def replace_pipeline(self, pipeline_key: str, **kwargs) -> APIResponse:
        """Fully replace a pipeline definition."""
        return self.put(f"/v2/pipelines/{pipeline_key}", data=kwargs)

    # -------------------------------------------------------------------------
    # Vectara API Operations - Generation Presets
    # -------------------------------------------------------------------------

    def list_generation_presets(self, limit: int = 100) -> APIResponse:
        """List generation presets available for the account."""
        return self.get("/v2/generation_presets", params={"limit": limit})

    # -------------------------------------------------------------------------
    # Vectara API Operations - Rerankers
    # -------------------------------------------------------------------------

    def list_rerankers(self, limit: int = 100) -> APIResponse:
        """List rerankers available for the account."""
        return self.get("/v2/rerankers", params={"limit": limit})

    # -------------------------------------------------------------------------
    # Vectara API Operations - Guardrails
    # -------------------------------------------------------------------------

    def list_guardrails(self, limit: int = 100) -> APIResponse:
        """List available guardrails."""
        return self.get("/v2/guardrails", params={"limit": limit})

    # -------------------------------------------------------------------------
    # Vectara API Operations - Query History
    # -------------------------------------------------------------------------

    def list_query_histories(
        self,
        limit: int = 100,
        corpus_key: Optional[str] = None,
        **kwargs,
    ) -> APIResponse:
        """List query histories.

        Args:
            limit: Maximum number of results.
            corpus_key: Optional corpus key to filter by.
            **kwargs: Additional query params (chat_id, page_key).
        """
        params: dict = {"limit": limit, **kwargs}
        if corpus_key is not None:
            params["corpus_key"] = corpus_key
        return self.get("/v2/queries", params=params)

    def get_query_history(self, query_id: str) -> APIResponse:
        """Get a specific query history entry."""
        return self.get(f"/v2/queries/{query_id}")

    # -------------------------------------------------------------------------
    # File Upload
    # -------------------------------------------------------------------------

    def upload_file(
        self,
        corpus_key: str,
        file_path: str,
        metadata: Optional[dict] = None,
        table_extraction_config: Optional[dict] = None,
    ) -> APIResponse:
        """Upload a file to a corpus via multipart form-data.

        Args:
            corpus_key: Target corpus key.
            file_path: Local filesystem path to the file to upload.
            metadata: Optional metadata dict to attach to the document.
            table_extraction_config: Optional table-extraction configuration dict.

        Returns:
            :class:`APIResponse` with the upload result.
        """
        import json as _json

        path = Path(file_path)
        endpoint = f"/v2/corpora/{corpus_key}/upload_file"

        start_time = time.time()

        try:
            with open(path, "rb") as fh:
                import mimetypes

                mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                files: dict = {"file": (path.name, fh, mime_type)}
                if metadata is not None:
                    files["metadata"] = (None, _json.dumps(metadata), "application/json")
                if table_extraction_config is not None:
                    files["table_extraction_config"] = (None, _json.dumps(table_extraction_config), "application/json")

                raw = self._request_raw(
                    method="POST",
                    endpoint=endpoint,
                    files=files,
                )

            elapsed_ms = (time.time() - start_time) * 1000

            try:
                response_data = raw.json()
            except ValueError:
                response_data = raw.text

            return APIResponse(
                status_code=raw.status_code,
                data=response_data,
                elapsed_ms=elapsed_ms,
                headers=dict(raw.headers),
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(f"File upload error: {e}")
            return APIResponse(
                status_code=0,
                data=None,
                elapsed_ms=elapsed_ms,
                error=f"File upload error: {str(e)}",
            )

    # -------------------------------------------------------------------------
    # Agent SSE Streaming
    # -------------------------------------------------------------------------

    def execute_agent_sse(
        self,
        agent_key: str,
        session_key: str,
        message: str,
    ) -> requests.Response:
        """Send a message to an agent session and return the raw SSE stream.

        The returned :class:`requests.Response` has ``stream=True`` so the
        caller can iterate over Server-Sent Events with
        :func:`utils.waiters.read_sse_events`.

        Args:
            agent_key: The agent's unique key.
            session_key: The session's unique key.
            message: User message text.

        Returns:
            Raw streaming :class:`requests.Response`.
        """
        endpoint = f"/v2/agents/{agent_key}/sessions/{session_key}/events"
        data = {
            "type": "input_message",
            "messages": [
                {
                    "type": "text",
                    "content": message,
                }
            ],
        }

        return self._request_raw(
            method="POST",
            endpoint=endpoint,
            data=data,
            stream=True,
        )

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    def health_check(self) -> APIResponse:
        """Verify API connectivity and authentication."""
        return self.list_corpora(limit=1)
