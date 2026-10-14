---
runs: 1
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Skill, WebFetch]
expected_outcome: Rewritten snippet uses https://api.subq.ai/v1/systemone, model subq-snap-preview and SUBQ_API_KEY; the answer lists the verified differences (context window, price, error body, retry codes) without inventing numbers.
---

This Python snippet calls TypeSafe Jev. I want to run the same decision on SubQ Snap instead. Rewrite the snippet for Snap and tell me, in a short list, what else changes between the two (limits, price, errors, retries). Only state things you can back with the vendors' docs; say when something is unknown.

```python
import json, os, urllib.request

req = urllib.request.Request(
    "https://api.typesafe.ai/v1/systemone",
    data=json.dumps({
        "model": "jev-latest",
        "state": {"review": "The blender died after two uses and support never replied."},
        "questions": {
            "refund": {"type": "noul", "instructions": "Does the customer ask for a refund or replacement?"},
            "tone": {"type": "score", "instructions": "How angry is `review`?", "criteria": ["Calm", "Annoyed", "Furious"]},
        },
    }).encode(),
    headers={"Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}", "Content-Type": "application/json"},
)
print(json.load(urllib.request.urlopen(req, timeout=30))["answers"])
```
