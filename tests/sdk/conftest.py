"""
Shared fixtures for SDK-level tests.

Provides sdk_client (session-scoped Vectara instance), per-test corpus
isolation, and module-scoped shared corpus fixtures.
"""

import logging
import uuid

import pytest

from vectara import Vectara
from vectara.environment import VectaraEnvironment
from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core
from vectara.core.request_options import RequestOptions

from utils.waiters import wait_for

logger = logging.getLogger(__name__)

# Default request options with retries matching the HTTP test suite (3 retries)
SDK_REQUEST_OPTIONS: RequestOptions = {"max_retries": 3}


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sdk_client(config):
    """Provide an authenticated Vectara SDK client with retry configuration."""
    import vectara.core.http_client as _http

    # Patch default retry count to 3 (matching HTTP test suite)
    _orig_request = _http.HttpClient.request
    _orig_request_fn = _orig_request

    def _patched_request(self, *args, request_options=None, **kwargs):
        if request_options is None:
            request_options = SDK_REQUEST_OPTIONS
        elif "max_retries" not in request_options:
            request_options = {**request_options, **SDK_REQUEST_OPTIONS}
        return _orig_request_fn(self, *args, request_options=request_options, **kwargs)

    _http.HttpClient.request = _patched_request

    # Use custom environment if base_url is not the default production URL
    base_url = config.base_url
    if base_url and base_url != "https://api.vectara.io":
        env = VectaraEnvironment(
            default=base_url,
            auth=base_url.replace("api.", "auth."),
        )
        return Vectara(api_key=config.api_key, environment=env)

    return Vectara(api_key=config.api_key)


# ---------------------------------------------------------------------------
# Per-test corpus fixtures
# ---------------------------------------------------------------------------


def _sdk_corpus_is_queryable(sdk_client, corpus_key):
    """Return True once a corpus responds to a get request."""
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False


@pytest.fixture
def sdk_test_corpus(sdk_client, unique_id):
    """Create a disposable corpus for a single test and delete it on teardown.

    Yields the Corpus object.
    """
    corpus_key = f"sdk_test_{uuid.uuid4().hex}"

    corpus = sdk_client.corpora.create(
        name=f"sdk_test_{unique_id}",
        key=corpus_key,
        description="Automated SDK test corpus - safe to delete",
    )

    wait_for(
        lambda: _sdk_corpus_is_queryable(sdk_client, corpus.key),
        timeout=10,
        interval=1,
        description="corpus to become queryable",
    )

    try:
        yield corpus
    finally:
        try:
            sdk_client.corpora.delete(corpus.key)
        except Exception:
            pass


@pytest.fixture(scope="module")
def sdk_shared_corpus(sdk_client):
    """Module-scoped corpus shared by all tests in a module.

    Yields the corpus key string.
    """
    corpus_key = f"sdk_shared_{uuid.uuid4().hex}"

    corpus = sdk_client.corpora.create(
        name=f"sdk_shared_{uuid.uuid4().hex[:8]}",
        key=corpus_key,
        description="Shared SDK module test corpus - safe to delete",
    )

    actual_key = corpus.key

    wait_for(
        lambda: _sdk_corpus_is_queryable(sdk_client, actual_key),
        timeout=10,
        interval=1,
        description="shared corpus to become queryable",
    )

    yield actual_key

    try:
        sdk_client.corpora.delete(actual_key)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper for seeding documents via SDK
# ---------------------------------------------------------------------------


def _sdk_documents_indexed(sdk_client, corpus_key, expected_count):
    """Return the document list once at least *expected_count* docs are present."""
    try:
        docs = list(sdk_client.documents.list(corpus_key, limit=100))
        if len(docs) >= expected_count:
            return docs
        return None
    except Exception:
        return None


def _seed_documents(sdk_client, corpus_key, docs):
    """Index a list of doc dicts into a corpus, return list of successfully seeded IDs."""
    doc_ids = []
    for doc in docs:
        try:
            sdk_client.documents.create(
                corpus_key,
                request=CreateDocumentRequest_Core(
                    id=doc["id"],
                    document_parts=[CoreDocumentPart(text=doc["text"], metadata=doc.get("metadata"))],
                    metadata=doc.get("metadata"),
                ),
            )
            doc_ids.append(doc["id"])
        except Exception:
            logger.warning("Failed to seed document %s", doc["id"], exc_info=True)
    return doc_ids


# ---------------------------------------------------------------------------
# Seeded corpus fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sdk_seeded_corpus(sdk_client, sdk_test_corpus):
    """Seed *sdk_test_corpus* with three sample documents and yield the Corpus object.

    Documents are removed during teardown (best-effort).
    """
    corpus_key = sdk_test_corpus.key

    docs = [
        {
            "id": f"seed_doc_{uuid.uuid4().hex[:8]}",
            "text": "Artificial intelligence is transforming industries by enabling machines to learn from data and make decisions.",
            "metadata": {"topic": "ai", "source": "seed"},
        },
        {
            "id": f"seed_doc_{uuid.uuid4().hex[:8]}",
            "text": "Vector databases store high-dimensional embeddings and support fast similarity search for semantic retrieval.",
            "metadata": {"topic": "databases", "source": "seed"},
        },
        {
            "id": f"seed_doc_{uuid.uuid4().hex[:8]}",
            "text": "Cloud computing provides scalable infrastructure that allows organizations to deploy applications globally.",
            "metadata": {"topic": "cloud", "source": "seed"},
        },
    ]

    doc_ids = _seed_documents(sdk_client, corpus_key, docs)

    wait_for(
        lambda: _sdk_documents_indexed(sdk_client, corpus_key, len(doc_ids)),
        timeout=15,
        interval=1,
        description="seeded documents to be indexed",
    )

    try:
        yield sdk_test_corpus
    finally:
        for doc_id in doc_ids:
            try:
                sdk_client.documents.delete(corpus_key, doc_id)
            except Exception:
                logger.warning("Failed to clean up seeded document %s", doc_id, exc_info=True)


@pytest.fixture(scope="module")
def sdk_seeded_shared_corpus(sdk_client, sdk_shared_corpus):
    """Module-scoped corpus with 5 sample documents seeded.

    For read-only query/search tests. Do NOT mutate or delete these docs in tests.
    """
    corpus_key = sdk_shared_corpus

    docs = [
        {
            "id": f"seed_{uuid.uuid4().hex[:8]}",
            "text": "Artificial intelligence and machine learning are transforming industries. Deep learning neural networks can process vast amounts of data to find patterns.",
            "metadata": {"category": "technology", "topic": "ai"},
        },
        {
            "id": f"seed_{uuid.uuid4().hex[:8]}",
            "text": "Vector databases enable semantic search capabilities. Unlike keyword search, vector search understands meaning and context of queries.",
            "metadata": {"category": "technology", "topic": "databases"},
        },
        {
            "id": f"seed_{uuid.uuid4().hex[:8]}",
            "text": "Climate change is affecting weather patterns around the world. Renewable energy sources like solar and wind are becoming more important.",
            "metadata": {"category": "science", "topic": "climate"},
        },
        {
            "id": f"seed_{uuid.uuid4().hex[:8]}",
            "text": "The Python programming language is popular for data science. Libraries like NumPy, Pandas, and TensorFlow make it easy to work with data.",
            "metadata": {"category": "technology", "topic": "programming"},
        },
        {
            "id": f"seed_{uuid.uuid4().hex[:8]}",
            "text": "Space exploration has led to many technological innovations. NASA and SpaceX are working on missions to Mars.",
            "metadata": {"category": "science", "topic": "space"},
        },
    ]

    doc_ids = _seed_documents(sdk_client, corpus_key, docs)

    wait_for(
        lambda: _sdk_documents_indexed(sdk_client, corpus_key, len(doc_ids)),
        timeout=15,
        interval=1,
        description="shared corpus documents to be indexed",
    )

    # Corpus deletion by sdk_shared_corpus fixture handles full cleanup.
    yield sdk_shared_corpus
