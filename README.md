# Vectara API Test Suite

A Python-based test suite for validating Vectara API functionality. Designed for deployment verification, smoke testing, and regression testing.

## Prerequisites

- Python 3.14 (matches the lock file resolver; install with `pip install -r requirements.txt` also works on 3.9+ since the lock file contains markers for older versions)
- Vectara Personal API key

## Installation

```bash
pip install -r requirements.txt
```

`requirements.txt` is a pinned, hashed lock file generated from `requirements.in`. To add or bump a dependency:

1. Edit `requirements.in` (loose constraints).
2. Regenerate the lock:
   ```bash
   pip install pip-tools
   pip-compile --generate-hashes --output-file=requirements.txt requirements.in
   ```
3. Commit both files. CI verifies they stay in sync.

## Running Tests

### Quick Start

```bash
export VECTARA_API_KEY=your_api_key_here
export VECTARA_BASE_URL=https://api.vectara.io
python run_tests.py --profile sanity
```

### Profiles

```bash
python run_tests.py --profile sanity       # Fast deploy gate
python run_tests.py --profile core         # Post-deploy verification
python run_tests.py --profile regression   # Edge cases + core
python run_tests.py --profile full         # Everything including workflows
```

### Select by Service

```bash
python run_tests.py --service auth
python run_tests.py --service agents,query
python run_tests.py --service corpus --profile sanity
```

### On-Premise Deployments

```bash
export VECTARA_BASE_URL=https://your-vectara-instance.com
python run_tests.py --profile core
```

### Reporting

```bash
python run_tests.py --profile core --html-report          # HTML report
python run_tests.py --profile core --json-report           # JSON report
python run_tests.py --profile core --html-report --json-report  # Both
```

Reports are saved to `reports/` with descriptive names like `test_report_20260403_core.html`.

### Parallel Execution

```bash
python run_tests.py --profile core -p 4
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VECTARA_API_KEY` | Personal API key | Yes |
| `VECTARA_BASE_URL` | API URL (default: `https://api.vectara.io`) | No |
| `VECTARA_TIMEOUT` | Request timeout in seconds (default: 30) | No |
| `VECTARA_LLM_NAME` | LLM model name for generation | No |
| `VECTARA_GENERATION_PRESET` | Generation preset name | No |
| `OPENAI_API_KEY` | OpenAI key for BYOL LLM tests (regression only) | No |

## Project Structure

```
tests/
├── conftest.py                  # Marker registration, shared fixtures
├── services/
│   ├── conftest.py              # Shared corpus/agent fixtures
│   ├── agents/                  # Agent CRUD, execution, sessions, compaction, context, corpora search
│   ├── auth/                    # API key validation, permissions, app clients
│   ├── chat/                    # Chat turns, multi-turn, validation
│   ├── corpus/                  # Corpus CRUD, lifecycle, access, filter attributes, validation
│   ├── indexing/                # Document CRUD, lifecycle, metadata, upload, bulk ops
│   ├── llm/                     # LLM CRUD
│   ├── pipelines/               # Pipeline listing
│   ├── query/                   # Semantic search, RAG, streaming, filters, rerankers, FCS, pagination, history
│   ├── tools/                   # Tool CRUD, lifecycle
│   └── users/                   # User CRUD
└── workflows/                   # Cross-service E2E flows
utils/
├── client.py                    # Vectara API client
├── config.py                    # Environment-based configuration
└── waiters.py                   # Polling helpers, SSE reader
```

## Test Markers

Every service test requires exactly one depth marker:
- `@pytest.mark.sanity` — fast health checks
- `@pytest.mark.core` — critical path operations
- `@pytest.mark.regression` — edge cases, error handling

Workflow tests use `@pytest.mark.workflow`.

## Services

| Service | What it tests |
|---------|-------------|
| `agents` | Agent CRUD, corpora search tool, sessions CRUD/update, compaction, context preservation, execution, streaming, event visibility, forking, error cases |
| `auth` | API key validation/lifecycle, permissions, app client CRUD, corpus access scoping |
| `chat` | Chat CRUD, turns CRUD, multi-turn verification, validation |
| `corpus` | Corpus CRUD, lifecycle (enable/disable/reset/compute size), filter attributes, access control, pagination, validation |
| `indexing` | Document CRUD, lifecycle, metadata, upload, bulk delete, custom dimensions, file upload |
| `query` | Semantic search, RAG, streaming (SSE), filters, rerankers, FCS, pagination, cross-corpus, generation presets, query history |
| `users` | User CRUD, roles, enable/disable |
| `tools` | Tool CRUD, enable/disable |
| `llm` | LLM list, BYOL create/delete |
| `pipelines` | Pipeline listing |

## Test Design Principles

- **Assert content, not just status codes** — every test verifies actual response fields, not just HTTP 200
- **Core API failures FAIL, not skip** — if agent/corpus/user creation returns 500, the test fails. Skip is only for optional features (OpenAI key not set, internal-only APIs, plan limitations)
- **wait_for() after stateful operations** — polling instead of sleep for eventual consistency
- **try/finally cleanup** — all created resources are cleaned up even on test failure
- **Capability gating** — optional APIs use module-level probe fixtures that skip gracefully

## Expected Skips

| Test | Reason |
|------|--------|
| `test_custom_dimensions_boost` | Account plan doesn't support custom dimensions |
| `test_create_and_delete_llm` | Requires funded `OPENAI_API_KEY` |

## Troubleshooting

### "API authentication failed"
- Verify your API key is correct and is a Personal API key
- Check if the key has expired or been disabled
- For staging: set `VECTARA_BASE_URL` to your staging endpoint

### "Connection error"
- Verify the base URL is correct
- For on-premise: ensure the instance is running

## License

Internal use only.
