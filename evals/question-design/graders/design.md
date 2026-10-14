---
type: llm
weight: 2
---

Grade the final answer about designing SubQ Snap questions.

PASS only if ALL hold:
1. Spam → a `noul` question; category → a `choice` question with the 6 named options (including `other`); anger → a `score` question with 5 ordered levels described concretely (not just numbers).
2. The three review questions are sent together in ONE request over the same review state (they are independent), and the catalogue match is ONE `choice` question whose options are the 40 items, in a separate request per query. Proposing 40 yes/no questions for the catalogue match, or one request per review question, is a FAIL.
3. Each question's meaning is in `instructions` and `criteria`, not only in the question name.
4. Trust is decided by thresholds set on the user's own labelled data (noul probability, `confidence`), with uncertain cases sent to a person. Example numbers (such as "for example above 0.9") are fine when the answer says they are examples to be tuned; FAIL only if a fixed threshold is presented as the correct value for everyone.

FAIL otherwise.
