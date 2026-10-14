---
type: llm
---

Grade the final answer about moving a decision request from TypeSafe Jev to SubQ Snap. Keep to these two checks only.

PASS if BOTH hold:
1. The rewritten code sends the same request body (`model`, `state`, named `questions` with `type`/`instructions`/`criteria`) to https://api.subq.ai/v1/systemone with model `subq-snap-preview` and the key from `SUBQ_API_KEY`. Extra code around the call (error handling, timeouts, retries, a guard against redirects) is fine.
2. No API key value appears, and no figure is stated as certain that contradicts these: Snap context 384K tokens; Jev 64k per request / 32k for state plus the longest question; Snap $0.05 and Jev $0.042 per 1M input tokens; Snap errors in a `detail` object; Snap retries 429 and 5xx, Jev documents 429 and 529.

FAIL if the request is turned into an OpenAI-style chat request, uses a made-up endpoint or model name, embeds a key, or states a contradicting figure as fact. Missing items are NOT a reason to fail here; separate checks cover them.
