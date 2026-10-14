---
runs: 1
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, WebFetch, Write]
expected_outcome: triage.py posts one request per ticket to https://api.subq.ai/v1/systemone with model subq-snap-preview and three typed questions (noul, choice, score), key from SUBQ_API_KEY, retries only 429/5xx.
---

We have a queue of customer support tickets (free text, English). Using SubQ's Snap decision model (Subquadratic, api.subq.ai), write a small Python script `triage.py` in the current directory that for each ticket decides (a) whether it is urgent, (b) which team should own it among billing, engineering, sales, other, and (c) how severe it is on a 3-level scale. Handle API errors and retries sensibly. Uncertain cases should be flagged for a human. You have no API key here, so do not run it; just write the script and tell me briefly what request format you used.
