"""
Pytest configuration and shared fixtures for Vectara API Test Suite.
"""

import os
import sys
import uuid
import logging
import time
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import Config
from utils.client import VectaraClient


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--api-key",
        action="store",
        default=None,
        help="Vectara Personal API key",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Vectara API base URL (for on-premise deployments)",
    )


def pytest_configure(config):
    """Configure logging and environment from command-line options."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Apply command-line options to environment
    if config.getoption("--api-key"):
        os.environ["VECTARA_API_KEY"] = config.getoption("--api-key")

    if config.getoption("--base-url"):
        os.environ["VECTARA_BASE_URL"] = config.getoption("--base-url")


@pytest.fixture(scope="session")
def config():
    """Provide configuration object."""
    return Config()


@pytest.fixture(scope="session")
def client(config):
    """Provide authenticated Vectara API client."""
    return VectaraClient(config)


@pytest.fixture(scope="session")
def test_run_id():
    """Generate unique identifier for this test run."""
    return str(uuid.uuid4())[:8]


@pytest.fixture(scope="session")
def test_corpus_key(client, config, test_run_id):
    """
    Create a test corpus for the session and clean up after.

    This fixture creates a dedicated corpus for testing and ensures
    it's deleted after all tests complete.
    """
    corpus_name = f"API Test Corpus {test_run_id}"

    # Create test corpus
    response = client.create_corpus(
        name=corpus_name,
        description="Automated test corpus - safe to delete",
    )

    if response.success:
        # Use the key returned by the API (not the one we generated)
        actual_key = response.data.get("key")
        if not actual_key:
            pytest.skip(f"Corpus created but no key returned: {response.data}")

        # Allow time for corpus to be ready
        time.sleep(1)

        yield actual_key

        # Cleanup: delete test corpus using the actual key
        client.delete_corpus(actual_key)
    else:
        # If corpus creation fails, skip tests that need it
        pytest.skip(f"Could not create test corpus: {response.data}")


@pytest.fixture
def unique_id():
    """Generate a unique ID for test data."""
    return str(uuid.uuid4())[:12]


@pytest.fixture
def sample_document():
    """Provide sample document content for indexing tests."""
    return {
        "title": "Test Document",
        "text": "This is a sample document for testing the Vectara API. "
                "It contains information about artificial intelligence and "
                "machine learning technologies. Vector search enables semantic "
                "understanding of text content.",
        "metadata": {
            "source": "test_suite",
            "category": "technology",
        },
    }


@pytest.fixture
def sample_query():
    """Provide sample query for search tests."""
    return "What is vector search?"


# -------------------------------------------------------------------------
# Report hooks
# -------------------------------------------------------------------------

def pytest_html_report_title(report):
    """Set custom report title."""
    report.title = "Vectara API Test Suite Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Add custom summary to HTML report."""
    prefix.extend([
        "<p>This report validates Vectara API functionality for upgrade verification.</p>",
        "<p>Tests cover: Authentication, Corpus Management, Indexing, Query/Search, and Agents APIs.</p>",
    ])
