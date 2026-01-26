# Vectara API Test Suite

A comprehensive Python-based test suite for validating Vectara API functionality. Designed for customers running on-premise deployments to verify system integrity after version upgrades.

## Features

- **Comprehensive API Coverage**: Tests for Authentication, Corpus Management, Indexing, Query/Search, and Agents APIs
- **Simple Authentication**: Command-line argument or environment variable
- **Detailed Reporting**: HTML and JSON reports with response times and error diagnostics
- **Parallel Execution**: Run tests in parallel for faster validation
- **CI/CD Ready**: Easy integration with automated pipelines

## Prerequisites

- Python 3.10 or higher
- Vectara Personal API key

## Installation

1. Navigate to the test suite directory:

```bash
cd vectara-api-tests
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Test Account Setup

Before running tests, you need a Vectara Personal API key.

### Step 1: Copy an API Key

1. Choose the account you want to test
2. Log into the Vectara Console as the **Account Owner**
3. Ensure you are comfortable testing within this account
4. Use your **Personal API key** for this account

## Running Tests

### Command-Line Argument

```bash
python run_tests.py --api-key YOUR_API_KEY
```

### Environment Variable (Recommended for CI/CD)

```bash
export VECTARA_API_KEY=your_api_key_here
python run_tests.py
```

### For On-Premise Deployments

Specify your custom API endpoint:

```bash
python run_tests.py --api-key YOUR_KEY --base-url https://your-vectara-instance.com
```

Or via environment variable:

```bash
export VECTARA_API_KEY=your_key
export VECTARA_BASE_URL=https://your-vectara-instance.com
python run_tests.py
```

## Test Categories

Run specific test categories:

```bash
# Authentication tests only
python run_tests.py --api-key YOUR_KEY --tests auth

# Multiple categories
python run_tests.py --api-key YOUR_KEY --tests corpus,indexing

# All tests (default)
python run_tests.py --api-key YOUR_KEY --tests all
```

Available categories:
- `auth` - Authentication and authorization tests
- `corpus` - Corpus CRUD operations
- `indexing` - Document indexing tests
- `query` - Query, search, and RAG tests
- `agents` - Conversational AI agent tests
- `all` - Run all tests

## Reporting

### HTML Report

```bash
python run_tests.py --api-key YOUR_KEY --html-report
```

Reports are saved to `reports/test_report_YYYYMMDD_HHMMSS.html`

### JSON Report (for CI/CD)

```bash
python run_tests.py --api-key YOUR_KEY --json-report
```

### Parallel Execution

Speed up test runs with parallel workers:

```bash
python run_tests.py --api-key YOUR_KEY --parallel 4
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VECTARA_API_KEY` | Your Personal API key | Yes |
| `VECTARA_BASE_URL` | API URL for on-premise deployments | No (defaults to SaaS) |
| `VECTARA_TIMEOUT` | Request timeout in seconds | No (default: 30) |
| `VECTARA_CORPUS_PREFIX` | Prefix for test corpora | No (default: `api_test_`) |

## Project Structure

```
vectara-api-tests/
├── tests/
│   ├── test_01_authentication.py
│   ├── test_02_corpus_management.py
│   ├── test_03_indexing.py
│   ├── test_04_query_search.py
│   └── test_05_agents.py
├── utils/
│   ├── client.py           # Vectara API client
│   └── config.py           # Configuration management
├── fixtures/               # Test data
├── reports/                # Generated test reports
├── conftest.py             # Pytest fixtures
├── run_tests.py            # Test runner script
├── requirements.txt
└── README.md
```

## Test Coverage

| API Category | Endpoints Tested | Scenarios |
|-------------|------------------|-----------|
| Authentication | API key validation | Valid/invalid keys, permissions |
| Corpus Management | Create, Get, List, Update, Delete | CRUD operations, pagination, error handling |
| Indexing | Index, Get, List, Delete documents | Single/bulk docs, metadata, special characters |
| Query/Search | Query, Summary, Chat | Semantic search, RAG, pagination, filters |
| Agents | Create, Execute, Sessions | Conversational AI, multi-turn, context |

## Troubleshooting

### "API authentication failed"
- Verify your API key is correct
- Ensure you're using a Personal API key from an Account Owner
- Check if the key has expired

### "Connection error"
- Verify the base URL is correct
- Check network connectivity to Vectara servers
- For on-premise: ensure the instance is running

### "Permission denied"
- Verify you're using a Personal API key (not an index/query-specific key)
- Check account-level permissions

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Vectara API Tests

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          VECTARA_API_KEY: ${{ secrets.VECTARA_API_KEY }}
        run: python run_tests.py --html-report --json-report

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: reports/
```

## License

Internal use only. For Vectara on-premise customers.
