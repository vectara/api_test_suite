"""
Polling helpers and SSE stream parser for the Vectara API test suite.
"""

import json
import time
from typing import Any, Callable, Iterator

import requests


def wait_for(
    predicate: Callable[[], Any],
    timeout: float = 30,
    interval: float = 1,
    description: str = "condition",
) -> Any:
    """Poll *predicate* until it returns a truthy value or *timeout* expires.

    Args:
        predicate: A zero-argument callable. Called repeatedly until it returns
            a truthy value or the timeout is reached.
        timeout: Maximum wall-clock seconds to keep polling.
        interval: Seconds to sleep between attempts.
        description: Human-readable label used in the ``TimeoutError`` message.

    Returns:
        The first truthy value returned by *predicate*.

    Raises:
        TimeoutError: If *predicate* never returns a truthy value within
            *timeout* seconds.  The message includes *description* and the
            last value returned by *predicate*.
    """
    deadline = time.monotonic() + timeout
    last_result = None

    while True:
        last_result = predicate()
        if last_result:
            return last_result

        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out after {timeout}s waiting for {description}. " f"Last state: {last_result!r}")

        remaining = deadline - time.monotonic()
        time.sleep(min(interval, max(remaining, 0)))


def read_sse_events(response: requests.Response) -> Iterator[dict]:
    """Parse Server-Sent Events from a streaming ``requests.Response``.

    The response **must** have been made with ``stream=True``.  Each yielded
    dict contains:

    * ``event`` -- the SSE event type (empty string if none was set)
    * ``data``  -- the concatenated data payload (parsed as JSON when
      possible, otherwise kept as a raw string)

    Args:
        response: A :class:`requests.Response` opened with ``stream=True``.

    Yields:
        ``dict`` with ``event`` and ``data`` keys for every complete SSE
        message in the stream.
    """
    event_type = ""
    data_lines: list[str] = []

    for raw_line in response.iter_lines(decode_unicode=True):
        # iter_lines strips the trailing newline; an empty string means a
        # blank line, which is the SSE event delimiter.
        if raw_line is None:
            continue

        line: str = raw_line  # already decoded

        if line == "":
            # End of an event block -- emit if we collected any data lines.
            if data_lines:
                joined = "\n".join(data_lines)
                try:
                    parsed = json.loads(joined)
                except (json.JSONDecodeError, ValueError):
                    parsed = joined

                yield {"event": event_type, "data": parsed}

            # Reset for the next event.
            event_type = ""
            data_lines = []
            continue

        if line.startswith(":"):
            # SSE comment -- ignore.
            continue

        if ":" in line:
            field, _, value = line.partition(":")
            # Per the SSE spec, strip a single leading space from value.
            if value.startswith(" "):
                value = value[1:]
        else:
            field = line
            value = ""

        if field == "event":
            event_type = value
        elif field == "data":
            data_lines.append(value)
        # Other fields (id, retry, etc.) are silently ignored.

    # Flush any trailing event that wasn't followed by a blank line.
    if data_lines:
        joined = "\n".join(data_lines)
        try:
            parsed = json.loads(joined)
        except (json.JSONDecodeError, ValueError):
            parsed = joined

        yield {"event": event_type, "data": parsed}
