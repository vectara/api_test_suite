"""
Root pytest configuration for the restructured Vectara API test suite.

Registers depth-profile markers (sanity / core / regression), enforces that
every service test carries exactly one of them, and provides session- and
per-test fixtures shared across all test directories.
"""

import os
import sys
import uuid
import logging
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup -- allow ``from utils.config import Config`` etc. regardless of
# where pytest is invoked from.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import Config
from utils.client import VectaraClient


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------

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
    parser.addoption(
        "--generation-preset",
        action="store",
        default=None,
        help="Generation preset name for summarization (e.g., mockingbird-2.0)",
    )
    parser.addoption(
        "--llm-name",
        action="store",
        default=None,
        help="LLM model name to override preset's model (e.g., gpt-4o)",
    )


# ---------------------------------------------------------------------------
# Configuration & marker registration
# ---------------------------------------------------------------------------

DEPTH_MARKERS = {"sanity", "core", "regression"}

def pytest_configure(config):
    """Set env vars from CLI options and register custom markers."""
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Forward CLI options into the environment so Config picks them up.
    if config.getoption("--api-key", default=None):
        os.environ["VECTARA_API_KEY"] = config.getoption("--api-key")
    if config.getoption("--base-url", default=None):
        os.environ["VECTARA_BASE_URL"] = config.getoption("--base-url")
    if config.getoption("--generation-preset", default=None):
        os.environ["VECTARA_GENERATION_PRESET"] = config.getoption("--generation-preset")
    if config.getoption("--llm-name", default=None):
        os.environ["VECTARA_LLM_NAME"] = config.getoption("--llm-name")

    # Register markers
    config.addinivalue_line("markers", "sanity: quick smoke-test (< 30 s)")
    config.addinivalue_line("markers", "core: standard validation (minutes)")
    config.addinivalue_line("markers", "regression: exhaustive coverage")
    config.addinivalue_line("markers", "workflow: end-to-end multi-service workflow")
    config.addinivalue_line("markers", "serial: must not run in parallel")


# ---------------------------------------------------------------------------
# Collection-time validation
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(config, items):
    """Fail collection for any service test that has zero or multiple depth markers.

    Tests under ``tests/workflows/`` are exempt from this rule.
    """
    errors: list[str] = []

    for item in items:
        # Workflow tests are exempt from depth-marker enforcement.
        if "/workflows/" in str(item.fspath):
            continue

        # Only enforce on service tests (under tests/services/).
        if "/services/" not in str(item.fspath):
            continue

        marker_names = {m.name for m in item.iter_markers()}
        depth_hits = marker_names & DEPTH_MARKERS

        if len(depth_hits) == 0:
            errors.append(
                f"{item.nodeid}: missing depth marker (add @pytest.mark.sanity, "
                f"@pytest.mark.core, or @pytest.mark.regression)"
            )
        elif len(depth_hits) > 1:
            errors.append(
                f"{item.nodeid}: multiple depth markers ({', '.join(sorted(depth_hits))}); "
                f"use exactly one"
            )

    if errors:
        msg = "Depth-marker violations:\n  " + "\n  ".join(errors)
        raise pytest.UsageError(msg)


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

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
    """Generate a unique identifier for this test run."""
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Per-test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def unique_id():
    """Generate a unique ID for test data."""
    return str(uuid.uuid4())[:12]


@pytest.fixture
def sample_document():
    """Provide sample document content for indexing tests."""
    return {
        "title": "Test Document",
        "text": (
            "This is a sample document for testing the Vectara API. "
            "It contains information about artificial intelligence and "
            "machine learning technologies. Vector search enables semantic "
            "understanding of text content."
        ),
        "metadata": {
            "source": "test_suite",
            "category": "technology",
        },
    }


@pytest.fixture
def sample_query():
    """Provide sample query for search tests."""
    return "What is vector search?"


# ---------------------------------------------------------------------------
# HTML report hooks
# ---------------------------------------------------------------------------

def pytest_html_report_title(report):
    """Set custom report title."""
    report.title = "Vectara API Test Suite Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Add custom summary to HTML report."""
    prefix.extend([
        "<p>This report validates Vectara API functionality for upgrade verification.</p>",
        "<p>Tests cover: Authentication, Corpus Management, Indexing, Query/Search, and Agents APIs.</p>",
    ])
