"""
Shared fixtures for service-level tests.

Provides per-test corpus isolation so that each test function gets its own
fresh corpus that is cleaned up automatically.
"""

import time
import uuid
import logging

import pytest

logger = logging.getLogger(__name__)


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

    # Give the corpus a moment to become queryable.
    time.sleep(1)

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
            "text": (
                "Artificial intelligence is transforming industries by enabling "
                "machines to learn from data and make decisions."
            ),
            "metadata": {"topic": "ai", "source": "seed"},
        },
        {
            "id": f"seed_doc_{uuid.uuid4().hex[:8]}",
            "text": (
                "Vector databases store high-dimensional embeddings and support "
                "fast similarity search for semantic retrieval."
            ),
            "metadata": {"topic": "databases", "source": "seed"},
        },
        {
            "id": f"seed_doc_{uuid.uuid4().hex[:8]}",
            "text": (
                "Cloud computing provides scalable infrastructure that allows "
                "organizations to deploy applications globally."
            ),
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

    # Allow indexing to propagate.
    time.sleep(2)

    try:
        yield test_corpus
    finally:
        for doc_id in doc_ids:
            try:
                client.delete_document(test_corpus, doc_id)
            except Exception:
                logger.warning("Failed to clean up seeded document %s", doc_id, exc_info=True)
