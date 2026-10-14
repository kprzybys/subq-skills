"""Minimal client for the SubQ Decisions API (POST /v1/systemone), standard library only.

Usage as a script (key from the environment, never from a file or argument):
    export SUBQ_API_KEY=...   # or run through a secrets-manager wrapper
    python3 snap_client.py            # sends the demo request and prints the answers

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

import http.client
import json
import os
import random
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


if __name__ == "__main__":
    t0 = time.perf_counter()
    result = decide(DEMO_STATE, DEMO_QUESTIONS)
    ms = (time.perf_counter() - t0) * 1000
    a = result["answers"]
    print(f"model={result['model']} input_tokens={result['usage']['input_tokens']} latency={ms:.0f} ms")
    print(f"urgent   noul={a['urgent']['noul']:.2f}")
    print(f"team     choice={a['team']['choice']} confidence={a['team']['confidence']:.2f}")
    print(f"severity score={a['severity']['score']:.2f} confidence={a['severity']['confidence']:.2f}")
