# Vectara API Test Suite

A Python-based test suite for validating Vectara API functionality. Designed for deployment verification, smoke testing, and regression testing.

## Prerequisites

- Python 3.10 or higher
- Vectara Personal API key

## Installation

```bash
pip install -r requirements.txt
```

## Running Tests

### Quick Start

```bash
export VECTARA_API_KEY=your_api_key_here
python run_tests.py --profile sanity
```

### Profiles

```bash
python run_tests.py --profile sanity       # Fast deploy gate (~30s, 7 tests)
python run_tests.py --profile core         # Post-deploy verification (~5 min, 40 tests)
python run_tests.py --profile regression   # Edge cases + core (~56 tests)
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

## Project Structure

```
tests/
├── conftest.py                  # Marker registration, shared fixtures
├── services/
│   ├── conftest.py              # Shared corpus fixtures
│   ├── auth/                    # API key validation, permissions
│   ├── corpus/                  # Corpus CRUD, filter attributes, pagination
│   ├── indexing/                # Document CRUD, metadata, large docs
│   ├── query/                   # Semantic search, RAG, edge cases
│   ├── chat/                    # Multi-turn conversations
│   └── agents/                  # Agent CRUD, execution, sessions
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
| `auth` | API key validation, permissions |
| `corpus` | Corpus CRUD, filter attributes, pagination |
| `indexing` | Document CRUD, metadata, special characters |
| `query` | Semantic search, RAG summary, pagination |
| `chat` | Multi-turn conversations |
| `agents` | Agent CRUD, execution, sessions |

## Troubleshooting

### "API authentication failed"
- Verify your API key is correct and is a Personal API key
- Check if the key has expired or been disabled

### "Connection error"
- Verify the base URL is correct
- For on-premise: ensure the instance is running

## License

Internal use only.
