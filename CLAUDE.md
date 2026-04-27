# Development Guidelines

## Build Commands
- Install deps: `pip install -r requirements.txt`
- Run all tests: `python run_tests.py --profile full`
- Run sanity tests: `python run_tests.py --profile sanity`
- Run core tests: `python run_tests.py --profile core`
- Run single service: `python run_tests.py --service auth`
- Run single test: `python -m pytest tests/services/auth/test_api_key_validation.py::TestApiKeyValidation::test_health_check -v`
- Run by keyword: `python -m pytest tests/services/ -k "test_health_check" -v`
- Run SDK tests: `python run_tests.py --suite sdk --profile core`
- Run both suites: `python run_tests.py --suite both --profile core`
- Run SDK single service: `python run_tests.py --suite sdk --service agents`

## Environment Variables
- `VECTARA_API_KEY` — required, Personal API key
- `VECTARA_BASE_URL` — defaults to `https://api.vectara.io`

## Project Structure
- `tests/services/<service>/` — HTTP-level test files organized by API service (auth, corpus, indexing, query, chat, agents)
- `tests/sdk/<service>/` — SDK-level tests using the `vectara` Python SDK (same service layout)
- `tests/workflows/` — cross-service end-to-end flow tests
- `utils/client.py` — Vectara API client (single class, all HTTP methods)
- `utils/waiters.py` — polling helpers and SSE reader
- `utils/config.py` — environment-based configuration
- `fixtures/sample_data.py` — test data
- `run_tests.py` — CLI runner with `--suite`, `--profile`, and `--service` flags

## Test Markers
- Every service test must have exactly one depth marker: `@pytest.mark.sanity`, `@pytest.mark.core`, or `@pytest.mark.regression`
- Workflow tests use `@pytest.mark.workflow`
- Tests without markers fail collection
- `@pytest.mark.serial` for tests that must not run in parallel

## Code Style
- Python: PEP8, type hints, snake_case for variables/functions, CamelCase for classes
- Imports: Group by standard library, third-party, then local imports
- Do not add trivial comments. Write self-documenting code with clear naming. Do not delete old explanatory comments though, they are good.
- Do add docstrings for modules and classes.
- Fully implement functionality, do not leave stubs "for later".
- Do not modify tests to make them pass — fix the code under test.
- Error handling: Use appropriate exceptions, avoid catching generic exceptions.
- Before creating a new class/type, search for existing types that serve a similar purpose. Extend existing types rather than creating near-duplicates.
- When modifying a class, modify methods directly rather than adding duplicate methods.
- Strongly prefer explicit types over `None` sentinels.

## Test Conventions
- Each test is self-contained via fixtures. No test depends on another test having run.
- Use `unique_id` fixture for resource names to avoid collisions.
- Always use explicit UUID keys when creating corpora (`key=f"test_{uuid.uuid4().hex}"`).
- Never mutate the bootstrap API key used to run the suite.
- Use `wait_for()` from `utils/waiters.py` instead of `time.sleep()` for async operations.
- Cleanup resources in `try/finally` blocks.
- Module-scoped fixtures for shared corpora (read-heavy tests), function-scoped for CRUD tests.
- **Assertions must verify actual behavior, not just HTTP status.** Always verify response data, field values, and state changes — not just `response.success`.
- **SDK tests** (`tests/sdk/`) use `sdk_client` and `sdk_shared_agent` fixtures from `tests/sdk/conftest.py`. Tests that mutate shared fixtures must be marked `@pytest.mark.serial`.
- SDK tests require `vectara>=0.4.3`. Use `--suite sdk` or `--suite both` to include them.

## General Behavior
- Treat the user as an expert.
- Be pithy — use short summaries of actions.
- When refactoring, spawn sub agents for manual updates rather than using sed/grep/awk.
