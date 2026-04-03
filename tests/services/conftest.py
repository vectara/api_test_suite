"""
Shared fixtures for service-level tests.

Provides per-test corpus isolation so that each test function gets its own
fresh corpus that is cleaned up automatically.

Also provides module-scoped shared fixtures for tests that just need a corpus
as a container (indexing, query, chat) but don't test corpus CRUD itself.
"""

import logging
import uuid

import pytest

from utils.waiters import wait_for

logger = logging.getLogger(__name__)


def _corpus_is_queryable(client, corpus_key):
    """Return True once a corpus responds to a get request."""
    resp = client.get_corpus(corpus_key)
    return resp.success


def _documents_indexed(client, corpus_key, expected_count):
    """Return the document list once at least *expected_count* docs are present."""
    resp = client.list_documents(corpus_key, limit=100)
    if not resp.success:
        return None
    docs = resp.data.get("documents", [])
    if len(docs) >= expected_count:
        return docs
    return None


@pytest.fixture
def test_corpus(client, unique_id):
    """Create a disposable corpus for a single test and delete it on teardown.

    Yields the corpus key string.
    """
    corpus_name = f"svc_test_{unique_id}"
    corpus_key = f"svc_test_{uuid.uuid4().hex}"

    response = client.create_corpus(
        name=corpus_name,
        key=corpus_key,
        description="Automated service test corpus - safe to delete",
    )

    if not response.success:
        pytest.skip(f"Could not create test corpus: {response.data}")

    corpus_key = response.data.get("key")
    if not corpus_key:
        pytest.skip(f"Corpus created but no key returned: {response.data}")

    wait_for(lambda: _corpus_is_queryable(client, corpus_key), timeout=10, interval=1, description="corpus to become queryable")

    try:
        yield corpus_key
    finally:
        client.delete_corpus(corpus_key)


@pytest.fixture
def seeded_corpus(client, test_corpus):
    """Seed *test_corpus* with three sample documents and yield the corpus key.

    The documents are removed during teardown (best-effort) so that other
    fixtures or tests don't see leftover data.
    """
    doc_ids = []

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

    for doc in docs:
        resp = client.index_document(
            corpus_key=test_corpus,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if resp.success:
            doc_ids.append(doc["id"])
        else:
            logger.warning("Failed to seed document %s: %s", doc["id"], resp.data)

    wait_for(lambda: _documents_indexed(client, test_corpus, len(doc_ids)), timeout=15, interval=1, description="seeded documents to be indexed")

    try:
        yield test_corpus
    finally:
        for doc_id in doc_ids:
            try:
                client.delete_document(test_corpus, doc_id)
            except Exception:
                logger.warning("Failed to clean up seeded document %s", doc_id, exc_info=True)


@pytest.fixture(scope="module")
def shared_corpus(client):
    """Module-scoped corpus shared by all tests in a module.

    Use for tests that need a corpus as a container (indexing, query, chat)
    but don't test corpus CRUD itself. Each test should use unique doc IDs
    and clean up after itself.
    """
    corpus_key = f"shared_{uuid.uuid4().hex}"
    corpus_name = f"shared_test_{uuid.uuid4().hex[:8]}"

    response = client.create_corpus(
        name=corpus_name,
        key=corpus_key,
        description="Shared module test corpus - safe to delete",
    )

    if not response.success:
        pytest.skip(f"Could not create shared corpus: {response.data}")

    actual_key = response.data.get("key", corpus_key)

    wait_for(lambda: _corpus_is_queryable(client, actual_key), timeout=10, interval=1, description="shared corpus to become queryable")

    yield actual_key

    try:
        client.delete_corpus(actual_key)
    except Exception:
        pass


@pytest.fixture(scope="module")
def seeded_shared_corpus(client, shared_corpus):
    """Module-scoped corpus with sample documents seeded.

    For read-only query/chat tests. Do NOT mutate or delete these docs in tests.
    """
    doc_ids = []
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

    for doc in docs:
        resp = client.index_document(
            corpus_key=shared_corpus,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if resp.success:
            doc_ids.append(doc["id"])

    wait_for(lambda: _documents_indexed(client, shared_corpus, len(doc_ids)), timeout=15, interval=1, description="shared corpus documents to be indexed")

    # Corpus deletion by shared_corpus fixture handles full cleanup.
    yield shared_corpus
