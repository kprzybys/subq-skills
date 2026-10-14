---
type: llm
weight: 2
focus: { source: file, path: triage.py }
---

You are grading a Python script that calls the SubQ Decisions API.

PASS only if ALL of the following hold:
1. For each ticket the script sends ONE request whose JSON body has `model`, `state` and a `questions` object containing three named questions, each with `type`, `instructions` and `criteria` (a noul for urgency, a choice with options billing/engineering/sales/other, a score with 3 ordered levels). Three separate requests per ticket, or a body built around fields like `input`, `question`, `choices` or `prompt`, is a FAIL.
2. Answers are read from `answers.<question name>` (fields `noul`, `choice`, `probabilities`, `confidence`, `score`).
3. Retries happen only for HTTP 429 and 5xx (and timeouts or connection errors), with a backoff; 400, 401, 402, 403 and 422 are not retried.
4. Uncertain results (for example a noul near 0.5 or low `confidence`) are flagged for human review.

FAIL if any item is missing or if the script invents a different endpoint, model name or request shape.
