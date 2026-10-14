"""Minimal client for the SubQ Decisions API (POST /v1/systemone), standard library only.

Usage as a command (key from the environment, never from a file or argument; run it through a
secrets-manager wrapper when one exists):
    python3 snap_client.py request.json    # or "-" to read stdin
    python3 snap_client.py --demo          # sends the built-in support-ticket request
The request file holds {"state": ..., "questions": {...}} and optionally "images"; the model is fixed.
The full JSON response goes to stdout with "latency_ms" added; a one-line summary goes to stderr.
Exit codes: 0 answered, 1 the API or network failed (message on stderr), 2 bad usage or bad request file.

Usage from code:
    from snap_client import decide
    answers = decide(state, questions)["answers"]

Rules the client follows (see https://docs.subq.ai/markdown/endpoints/decisions-api.md):
- explicit timeout; a timed-out or dropped connection has an unknown outcome and is retried,
  which is safe because a decision request has no side effects;
- 429 and 5xx are retried with exponential backoff and full jitter, bounded attempts;
- 400 / 401 / 402 / 403 / 422 are not retried: they need a fixed request, key or credits;
- redirects are never followed: urllib would otherwise resend the Authorization header to the new host;
- the error body is {"detail": {"error_type", "message"}}.

Tests: python3 -m unittest test_snap_client  (run in this directory)
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

URL = "https://api.subq.ai/v1/systemone"
MODEL = "subq-snap-preview"


class SnapError(Exception):
    """The request did not produce a decision. `status` is the HTTP status, or None for a local/network failure."""

    def __init__(self, status: int | None, error_type: str, message: str) -> None:
        super().__init__(f"{status} {error_type}: {message}")
        self.status = status
        self.error_type = error_type


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001 - urllib signature
        return None  # urllib then raises HTTPError for the 3xx response


_OPENER = urllib.request.build_opener(_NoRedirect)


def _open(request: urllib.request.Request, timeout_s: float) -> dict:
    with _OPENER.open(request, timeout=timeout_s) as response:
        return json.load(response)


def decide(
    state: str | dict | list,
    questions: dict,
    *,
    images: list[dict] | None = None,
    attempts: int = 5,
    timeout_s: float = 60.0,
    base_delay_s: float = 1.0,
    max_delay_s: float = 30.0,
    open_fn: Callable[[urllib.request.Request, float], dict] = _open,
    sleep: Callable[[float], Any] = time.sleep,
) -> dict:
    """One Decisions request. Returns the parsed response (model, answers, usage).

    `open_fn` and `sleep` exist so tests can inject failures and skip real waiting.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    key = os.environ.get("SUBQ_API_KEY")
    if not key:
        raise SnapError(None, "no_key", "SUBQ_API_KEY is not set")
    body: dict = {"model": MODEL, "state": state, "questions": questions}
    if images:
        body["images"] = images
    data = json.dumps(body).encode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    for attempt in range(attempts):
        last = attempt == attempts - 1
        try:
            return open_fn(urllib.request.Request(URL, data=data, headers=headers), timeout_s)
        except urllib.error.HTTPError as e:
            detail = _detail(e)
            retryable = e.code == 429 or e.code >= 500
            if not retryable or last:
                raise SnapError(e.code, detail.get("error_type", "http_error"), detail.get("message", "")) from e
        except (OSError, http.client.HTTPException) as e:
            # URLError, timeouts, connection resets, truncated bodies: outcome unknown, retry.
            if last:
                raise SnapError(None, "network", f"{type(e).__name__}: {e}") from e
        sleep(random.uniform(0, min(max_delay_s, base_delay_s * 2**attempt)))
    raise SnapError(None, "internal", "retry loop ended without a result")  # not reachable with attempts >= 1


def _detail(e: urllib.error.HTTPError) -> dict:
    try:
        payload = json.load(e)
    except ValueError:
        return {"error_type": "http_error", "message": ""}
    detail = payload.get("detail") if isinstance(payload, dict) else None
    return detail if isinstance(detail, dict) else {"error_type": "http_error", "message": str(payload)[:200]}


DEMO_STATE = "Customer writes: my invoice shows a charge I never approved and the app crashes on login."
DEMO_QUESTIONS = {
    "urgent": {
        "type": "noul",
        "instructions": "Does this ticket need a response within the hour?",
        "criteria": {
            "true": "Outage, data loss, security issue or blocked payment",
            "false": "Anything that can wait for the next business day",
        },
    },
    "team": {
        "type": "choice",
        "instructions": "Which team should own this ticket?",
        "criteria": {
            "billing": "Charges, invoices, refunds",
            "engineering": "Bugs, crashes, errors",
            "sales": "Pricing, plans, upgrades",
            "other": None,
        },
    },
    "severity": {
        "type": "score",
        "instructions": "How badly is the customer blocked?",
        "criteria": ["Cosmetic or a question", "Broken but there is a workaround", "Cannot use the product"],
    },
}


REQUEST_KEYS = {"state", "questions", "images"}


def load_request(text: str) -> dict:
    """Parse and check a command-line request: {"state", "questions"} plus optional "images"."""
    try:
        request = json.loads(text)
    except ValueError as e:
        raise ValueError(f"request is not valid JSON: {e}") from e
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    unknown = set(request) - REQUEST_KEYS
    if unknown:
        raise ValueError(f"unknown keys {sorted(unknown)}; allowed: {sorted(REQUEST_KEYS)} (the model is fixed)")
    if "state" not in request or not isinstance(request.get("questions"), dict) or not request["questions"]:
        raise ValueError('request needs "state" and a non-empty "questions" object')
    return request


def main(argv: list[str] | None = None, *, stdin=None, stdout=None, stderr=None, decide_fn=None) -> int:
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    decide_fn = decide_fn or decide
    parser = argparse.ArgumentParser(description="Send one SubQ Snap decision request and print the JSON response.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("request", nargs="?", help='JSON file with "state" and "questions", or "-" for stdin')
    group.add_argument("--demo", action="store_true", help="send the built-in support-ticket request")
    args = parser.parse_args(argv)

    if args.demo:
        request = {"state": DEMO_STATE, "questions": DEMO_QUESTIONS}
    else:
        try:
            text = stdin.read() if args.request == "-" else open(args.request, encoding="utf-8").read()
            request = load_request(text)
        except (OSError, ValueError) as e:
            print(f"snap_client: {e}", file=stderr)
            return 2

    t0 = time.perf_counter()
    try:
        result = decide_fn(request["state"], request["questions"], images=request.get("images"))
    except SnapError as e:
        print(f"snap_client: {e}", file=stderr)
        return 1
    result["latency_ms"] = round((time.perf_counter() - t0) * 1000)
    json.dump(result, stdout, ensure_ascii=False, indent=2)
    stdout.write("\n")
    tokens = result.get("usage", {}).get("input_tokens")
    print(f"model={result.get('model')} input_tokens={tokens} latency={result['latency_ms']} ms", file=stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
