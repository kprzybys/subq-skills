---
runs: 1
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Skill, WebFetch]
expected_outcome: noul for spam, choice over 6 categories, score with 5 levels, one choice over the 40 catalogue items (not 40 nouls); first three in one request, the catalogue match in its own request; thresholds from labelled data and human review for uncertain cases.
---

I'm adding SubQ Snap to a product-review pipeline. For each review I need to know: (1) is it spam, (2) which of our 6 categories it belongs to (kitchen, audio, outdoor, toys, office, other), (3) how angry the customer is on a 1–5 scale. Separately, for each search query I need the single best-matching item among 40 catalogue items (I have their titles and descriptions). Which SubQ question types should I use for each, how many requests does that take, and how do I decide when to trust the answer? Draft the questions as JSON.
