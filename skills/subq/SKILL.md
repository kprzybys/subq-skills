---
name: subq
license: MIT
description: >
  Build with the SubQ Decisions API: SubQ Snap (model subq-snap-preview) turns
  text, JSON state and images into typed judgments with probabilities (noul
  yes/no, choice one-of-N, score on ordered levels) that code can act on. Use
  when a task mentions SubQ, Subquadratic, Snap, api.subq.ai, the Decisions
  API or /v1/systemone; when routing, ranking, triage, extraction or
  verification could become a structured decision instead of an LLM
  prompt-and-parse step; or when switching between TypeSafe Jev and Snap,
  which share the same request contract. Read the live docs as the source of
  truth and keep API keys out of chat, code and files.
---

# Build with SubQ Snap

SubQ Snap (`subq-snap-preview`) is a **decision model**, not a text generator.
It reads a `state` (text, JSON, or up to 4 images) and answers typed questions
with probabilities. Code owns the workflow; the model supplies the judgments
code cannot make. Summaries, explanations and free text stay with an LLM.

SubQ also offers `subq-preview`, a long-context chat model behind
OpenAI-compatible Chat Completions and Responses endpoints. It is **early
access**: a key without that access gets `403`. Build on it only after
`GET /v1/models` lists it for the key you are using.

## Read the live docs first

**The live SubQ docs are the source of truth.** This skill gives direction and
the facts that were verified when it was written (October 2026); the docs carry
the current contract, limits and examples.

- Start with the index: https://docs.subq.ai/llms.txt. It lists every page as
  Markdown with its release stage.
- Every page is served as Markdown under `https://docs.subq.ai/markdown/<path>.md`,
  for example the [Decisions API](https://docs.subq.ai/markdown/endpoints/decisions-api.md)
  and [Models](https://docs.subq.ai/markdown/using-the-api/models.md).
  Fetch the `.md` URL directly; a summarised fetch of the HTML page drops the code.
- Before writing an integration, read the Decisions API page. Before sending
  anything sensitive, read [Data retention](https://docs.subq.ai/markdown/using-the-api/data-retention.md).
- If the docs are unreachable, say so and use the facts below; do not invent
  version-dependent details.

| Task | Start here |
| --- | --- |
| Request and response shape, limits, errors | [Decisions API](https://docs.subq.ai/markdown/endpoints/decisions-api.md) |
| Model IDs, status, pricing | [Models](https://docs.subq.ai/markdown/using-the-api/models.md), [Models API](https://docs.subq.ai/markdown/endpoints/models-api.md) |
| Keys and auth | [Authentication](https://docs.subq.ai/markdown/using-the-api/authentication.md) |
| What is stored and for how long | [Data retention](https://docs.subq.ai/markdown/using-the-api/data-retention.md) |
| Chat / Responses with `subq-preview` (early access only) | the "SubQ Preview" section of the index |

## The contract (verified against the docs, October 2026)

```text
POST https://api.subq.ai/v1/systemone
Authorization: Bearer $SUBQ_API_KEY
Content-Type: application/json
```

```json
{
  "model": "subq-snap-preview",
  "state": "Customer writes: my invoice shows a charge I never approved and the app crashes on login.",
  "questions": {
    "urgent": {
      "type": "noul",
      "instructions": "Does this ticket need a response within the hour?",
      "criteria": { "true": "Outage, data loss, security issue or blocked payment", "false": "Anything that can wait for the next business day" }
    },
    "team": {
      "type": "choice",
      "instructions": "Which team should own this ticket?",
      "criteria": { "billing": "Charges, invoices, refunds", "engineering": "Bugs, crashes, errors", "sales": "Pricing, plans, upgrades", "other": null }
    },
    "severity": {
      "type": "score",
      "instructions": "How badly is the customer blocked?",
      "criteria": ["Cosmetic or a question", "Broken but there is a workaround", "Cannot use the product"]
    }
  }
}
```

Answers come back under `answers.<question name>`:

- **noul** → `noul`: probability of yes, 0 to 1. A value near 0.5 means the model
  is unsure, not "medium". Optional `criteria.true` / `criteria.false` describe
  both outcomes.
- **choice** → `choice`, `probabilities` (one per option) and `confidence`.
  2 to 255 named options; a description may be `null`.
- **score** → probability-weighted `score` (can fall between levels), `legend`,
  `probabilities`, `confidence`. 2 to 10 ordered levels, listed from lowest to highest.

Limits and billing from the docs:

- 1 to 16 questions per request; question names up to 100 characters.
- Context window 384K tokens (393,216) per request, state plus questions plus
  images. Over or close to the limit → `400`.
- Images: up to 4, PNG/JPEG/WebP, plain base64 without a `data:` prefix, 4 MiB
  decoded each and 8 MiB total, request body up to 13 MiB; about 64–256 tokens
  per image. No video: sample up to 4 frames.
- Price: $0.05 per 1M input tokens, output free. `usage.input_tokens` is what
  you pay for; `usage.output_tokens` is always 0.
- Public preview: the model and its behaviour can change before general availability.

Errors use `{"detail": {"error_type": "...", "message": "..."}}`, not the
OpenAI `error` shape.

| Status | Meaning | Retry? |
| --- | --- | --- |
| 400 | input over the token limit, or a request the model rejects | no, shrink the state |
| 401 | missing or invalid key | no |
| 402 | no credits | no |
| 403 | the key cannot use this model (for example `subq-preview` without early access) | no |
| 422 | invalid request: bad question, bad image, non-decision model | no, fix the request |
| 429 | rate limit | yes, backoff |
| 5xx (503 = temporarily unavailable) | server error | yes, backoff |

Retry with exponential backoff and jitter and a bounded number of attempts.
Set an explicit timeout; after a timeout or a dropped connection the outcome is
unknown, and retrying is safe because a decision request has no side effects.
Do not follow redirects: Python's `urllib` and some other clients resend the
`Authorization` header to the redirect target, which would leak the key.
`examples/snap_client.py` in this skill's directory is a minimal client that
follows these rules, with tests in `examples/test_snap_client.py`.

## Design the questions

Start from the behaviour the application needs: what will it show, route,
rank, accept or hand to a person? Work backward to the judgments. Keep rules,
lookups and arithmetic in code; ask the model only for what code cannot decide.

| Need | Type | Notes |
| --- | --- | --- |
| Whether a condition holds | noul | One noul per label when several labels may apply at once |
| One of a defined set | choice | Include a no-match option such as `other: null` when nothing may fit |
| Degree along a dimension | score | Each level must describe a concrete situation and stand on its own |

- **One judgment per question.** Split "is it urgent and who owns it" into a
  noul and a choice. Code combines the answers.
- **Put the whole meaning in `instructions` and `criteria`.** Do not rely on
  the question name to carry meaning. Name the state field a question is about
  when the state has several parts.
- **Prefer a JSON `state` with named fields** when the context has several
  parts (ticket text, customer tier, policy excerpt).
- **Prefer one choice over a list to many nouls about its items.** To pick the
  best of N candidates, send one choice with the candidates as options; to rank
  them, send one comparable score (or noul) per candidate and sort by the
  probabilities.
- **Ask independent questions about the same state in one request** (up to 16).
  Treat them as independent: the SubQ docs say only that the state is sent once
  and the answers come back by name, so do not write a question that assumes
  another question's answer. A second request is needed when an answer decides
  what to fetch or ask next.
- **Send only what the decision needs.** Trim the state; large states cost
  tokens and time.

## Use the probabilities

- Thresholds come from your own labelled cases, not from examples. Run the
  questions over cases you already know the answer to and pick cutoffs from
  the results, separately for each question.
- Route low `confidence`, a noul near 0.5, or a costly mistake to a person or
  to a larger model. Typed output guarantees the shape, not the truth.
- Outputs can differ between requests. Do not treat a single answer as a
  constant; measure accuracy on a sample before automating.
- Keep raw probabilities in your data so that thresholds and weights can
  change without rerunning inference.

## Keys and secrets

- Read the key from the `SUBQ_API_KEY` environment variable (the docs'
  convention). Never paste a key into chat, source, notebooks, logs or docs,
  and never commit one. A value shown once in the console cannot be retrieved later.
- If the environment provides a secrets-manager wrapper that exports the
  variable for one process (for example `with-<vendor>-key <command>`), run
  scripts through it instead of exporting the key in a shell.
- Check a key with `GET /v1/models`: it lists the model IDs the key may use.
- Keep the key server-side in web apps; call the API from a backend.
- Data goes to a cloud API. Before sending personal or confidential data, read
  the data-retention page and confirm the retention setting of your organisation.

## SubQ Snap vs TypeSafe Jev

Snap and Jev speak the same `POST /v1/systemone` contract: `model`, `state`,
named `questions` of type noul / choice / score with `instructions` and
`criteria`. Moving between them is a change of URL, model ID and key variable,
plus the differences below. Facts marked *docs* are from the vendors'
documentation; facts marked *measured* come from the author's benchmarks
(October 2026, single runs, public datasets; code and numbers at
https://github.com/kprzybys/snap-vs-jev-swe).

| | SubQ Snap | TypeSafe Jev |
| --- | --- | --- |
| Endpoint | `https://api.subq.ai/v1/systemone` | `https://api.typesafe.ai/v1/systemone` |
| Model ID | `subq-snap-preview` | `jev-latest` (alias of `jev-1.13.0`) |
| Key variable | `SUBQ_API_KEY` | `TYPESAFE_API_KEY` |
| Context (*docs*) | 384K tokens per request | 64k per request (state plus all questions); 32k per question (state plus any one question) |
| Questions per request (*docs*) | 1–16 | no separate limit; the request must fit both context limits |
| Images (*docs*) | up to 4 | text only |
| Price (*docs*) | $0.05 / 1M input tokens, output free | $0.042 / 1M input tokens, output free |
| Error body (*docs*) | `{"detail": {"error_type", "message"}}` | HTTP status with a JSON body |
| Retry (*docs*) | 429, 5xx | 429, 529 |
| Median latency (*measured*, 8,631 short cases) | 453 ms | 255 ms |
| Accuracy (*measured*) | a few points higher on most classification sets; biggest edge where one request must read a lot (SWE-bench file localisation with 10 whole files, ~71k tokens: 87.5%) | cannot take inputs above its context limit |

Rules of thumb from those measurements: pick Snap when accuracy or long
context matters; pick Jev when latency or cost per call matters. Thresholds
tuned for one model do not transfer to the other; recalibrate on your data.
TypeSafe's own skill (`typesafe-ai`) and docs (https://docs.typesafe.ai/llms.txt)
cover Jev; this skill covers SubQ.

## Build and verify

1. Confirm access: `GET /v1/models` with the key; expect `subq-snap-preview`.
2. Design the state and questions as above; write them down with the expected answers for a handful of cases.
3. Send one request per state with all independent questions; parse `answers` by question name; keep `usage.input_tokens` and latency.
4. Handle errors as in the table: fix `400`/`422`, retry `429`/`5xx` with backoff, stop on `401`/`402`/`403`.
5. Evaluate on labelled cases; set thresholds; route the uncertain remainder to a person.
6. Estimate cost from measured `input_tokens` × $0.05 per 1M before scaling up.

When something fails, inspect the exact state, questions, answers and
composition, and separate missing evidence, model errors, code errors and
service failures.
