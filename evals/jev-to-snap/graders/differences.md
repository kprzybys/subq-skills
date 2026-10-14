---
type: llm
weight: 2
---

Grade the final answer about moving a decision request from TypeSafe Jev to SubQ Snap.

PASS only if ALL hold:
1. The rewritten code keeps the same request shape (`model`, `state`, named `questions` with `type`/`instructions`/`criteria`) and changes only the URL to https://api.subq.ai/v1/systemone, the model to `subq-snap-preview` and the key variable to `SUBQ_API_KEY`.
2. The list of differences mentions, with the right direction: Snap's larger context window (384K tokens, versus Jev's 64k per request / 32k for state plus longest question), Snap's price of $0.05 per 1M input tokens versus Jev's $0.042 (output free for both), Snap's error body as a `detail` object, and that Snap retries 429 and 5xx while Jev documents 429 and 529.
3. No API key value appears, and no numbers are presented as facts that contradict the ones above (for example a different price or context size stated as certain).

FAIL if the code shape is changed to an OpenAI-style chat request, if a made-up endpoint or model name is used, or if the price or context figures are wrong or missing.
