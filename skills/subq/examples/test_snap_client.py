"""Characterisation tests for snap_client.decide: retry policy, error mapping, redirects, key handling.

Run: python3 -m unittest test_snap_client
"""

from __future__ import annotations

import http.client
import io
import json
import os
import unittest
import urllib.error
from unittest import mock

import snap_client
from snap_client import SnapError, decide

OK = {
    "model": "subq-snap-preview",
    "answers": {"q": {"type": "noul", "noul": 0.9}},
    "usage": {"input_tokens": 10, "output_tokens": 0},
}
QUESTIONS = {"q": {"type": "noul", "instructions": "Is it urgent?"}}


def http_error(code: int, body: dict | str = "") -> urllib.error.HTTPError:
    raw = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
    return urllib.error.HTTPError(snap_client.URL, code, "err", {}, io.BytesIO(raw))


class FakeOpen:
    """Returns or raises the queued outcomes in order and records every request."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def __call__(self, request, timeout_s):
        self.requests.append((request, timeout_s))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class DecideTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {"SUBQ_API_KEY": "test-key"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sleeps: list[float] = []

    def call(self, fake: FakeOpen, **kw):
        return decide("state", QUESTIONS, open_fn=fake, sleep=self.sleeps.append, **kw)

    def test_success_sends_model_state_questions_and_bearer_key(self):
        fake = FakeOpen(OK)
        self.assertEqual(self.call(fake), OK)
        request, timeout_s = fake.requests[0]
        self.assertEqual(request.full_url, snap_client.URL)
        expected = {"model": "subq-snap-preview", "state": "state", "questions": QUESTIONS}
        self.assertEqual(json.loads(request.data), expected)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(timeout_s, 60.0)
        self.assertEqual(self.sleeps, [])

    def test_429_and_5xx_are_retried_with_backoff(self):
        rate_limited = http_error(429, {"detail": {"error_type": "rate_limit", "message": "slow down"}})
        fake = FakeOpen(rate_limited, http_error(503), OK)
        self.assertEqual(self.call(fake), OK)
        self.assertEqual(len(fake.requests), 3)
        self.assertEqual(len(self.sleeps), 2)
        self.assertTrue(all(0 <= s <= 2 for s in self.sleeps))

    def test_422_is_not_retried_and_maps_the_detail_body(self):
        fake = FakeOpen(http_error(422, {"detail": {"error_type": "validation_error", "message": "questions/q: bad"}}))
        with self.assertRaises(SnapError) as ctx:
            self.call(fake)
        self.assertEqual((ctx.exception.status, ctx.exception.error_type), (422, "validation_error"))
        self.assertIn("questions/q: bad", str(ctx.exception))
        self.assertEqual(len(fake.requests), 1)

    def test_400_401_402_403_are_not_retried(self):
        for code in (400, 401, 402, 403):
            fake = FakeOpen(http_error(code))
            with self.assertRaises(SnapError) as ctx:
                self.call(fake)
            self.assertEqual(ctx.exception.status, code)
            self.assertEqual(len(fake.requests), 1)

    def test_attempts_are_bounded_and_the_last_error_is_raised(self):
        fake = FakeOpen(*[http_error(503)] * 3)
        with self.assertRaises(SnapError) as ctx:
            self.call(fake, attempts=3)
        self.assertEqual(ctx.exception.status, 503)
        self.assertEqual(len(fake.requests), 3)
        self.assertEqual(len(self.sleeps), 2)

    def test_dropped_connection_and_timeout_are_retried(self):
        fake = FakeOpen(
            http.client.IncompleteRead(b""),
            ConnectionResetError(),
            TimeoutError(),
            urllib.error.URLError("dns"),
            OK,
        )
        self.assertEqual(self.call(fake), OK)
        self.assertEqual(len(fake.requests), 5)

    def test_network_failure_after_last_attempt_is_a_snap_error(self):
        fake = FakeOpen(TimeoutError(), TimeoutError())
        with self.assertRaises(SnapError) as ctx:
            self.call(fake, attempts=2)
        self.assertEqual((ctx.exception.status, ctx.exception.error_type), (None, "network"))

    def test_redirect_is_an_error_not_a_retry(self):
        fake = FakeOpen(http_error(302))
        with self.assertRaises(SnapError) as ctx:
            self.call(fake)
        self.assertEqual(ctx.exception.status, 302)
        self.assertEqual(len(fake.requests), 1)

    def test_opener_does_not_follow_redirects(self):
        handler = snap_client._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "Found", {}, "https://evil.example/"))

    def test_missing_key_is_reported_before_any_request(self):
        fake = FakeOpen(OK)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SnapError) as ctx:
                self.call(fake)
        self.assertEqual(ctx.exception.error_type, "no_key")
        self.assertEqual(fake.requests, [])

    def test_attempts_below_one_is_rejected(self):
        with self.assertRaises(ValueError):
            self.call(FakeOpen(OK), attempts=0)

    def test_images_are_included_only_when_given(self):
        fake = FakeOpen(OK, OK)
        self.call(fake)
        self.call(fake, images=[{"mediaType": "image/png", "base64": "AAAA"}])
        self.assertNotIn("images", json.loads(fake.requests[0][0].data))
        sent = json.loads(fake.requests[1][0].data)["images"]
        self.assertEqual(sent, [{"mediaType": "image/png", "base64": "AAAA"}])


class MainTests(unittest.TestCase):
    """The command-line wrapper: request parsing, exit codes, output streams."""

    def run_main(self, argv, stdin_text="", decide_fn=None):
        self.calls = []

        def fake_decide(state, questions, images=None):
            self.calls.append((state, questions, images))
            return json.loads(json.dumps(OK))

        out, err = io.StringIO(), io.StringIO()
        code = snap_client.main(argv, stdin=io.StringIO(stdin_text), stdout=out, stderr=err,
                                decide_fn=decide_fn or fake_decide)
        return code, out.getvalue(), err.getvalue()

    def test_stdin_request_prints_response_with_latency(self):
        code, out, err = self.run_main(["-"], json.dumps({"state": "s", "questions": QUESTIONS}))
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [("s", QUESTIONS, None)])
        result = json.loads(out)
        self.assertEqual(result["answers"], OK["answers"])
        self.assertIn("latency_ms", result)
        self.assertIn("input_tokens=10", err)

    def test_images_are_passed_through(self):
        images = [{"mediaType": "image/png", "base64": "AAAA"}]
        self.run_main(["-"], json.dumps({"state": "s", "questions": QUESTIONS, "images": images}))
        self.assertEqual(self.calls[0][2], images)

    def test_bad_request_exits_2_without_calling_the_api(self):
        bad = ["not json", "[]", json.dumps({"state": "s"}), json.dumps({"state": "s", "questions": {}}),
               json.dumps({"state": "s", "questions": QUESTIONS, "model": "jev-latest"})]
        for text in bad:
            with self.subTest(text=text):
                code, out, err = self.run_main(["-"], text)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("snap_client:"))
        self.assertEqual(self.calls, [])

    def test_api_error_exits_1_with_message_on_stderr(self):
        def failing(*a, **kw):
            raise SnapError(402, "payment_required", "no credits")

        code, out, err = self.run_main(["-"], json.dumps({"state": "s", "questions": QUESTIONS}), failing)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("402 payment_required", err)

    def test_demo_sends_the_demo_request(self):
        code, _, _ = self.run_main(["--demo"])
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [(snap_client.DEMO_STATE, snap_client.DEMO_QUESTIONS, None)])

    def test_request_or_demo_is_required(self):
        with self.assertRaises(SystemExit) as ctx, mock.patch("sys.stderr", io.StringIO()):
            self.run_main([])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
