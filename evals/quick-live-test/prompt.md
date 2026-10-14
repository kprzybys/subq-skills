---
runs: 1
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Skill, Bash, Write]
expected_outcome: The agent sends one decision with the skill's bundled snap_client.py as a command (request JSON in a file or on stdin), behind the with-subq-key wrapper, instead of writing its own HTTP client or glue script; no key value appears.
---

Quick sanity check of my SubQ Snap setup: send one test decision asking whether this customer review asks for a refund, and show me the answer. Review: "The kettle arrived with a cracked lid. I want my money back." In this environment the API key is injected only by the wrapper `with-subq-key <command>`; it may be missing here, so if the run fails because of the wrapper or the key, show me the exact command you ran and stop.
