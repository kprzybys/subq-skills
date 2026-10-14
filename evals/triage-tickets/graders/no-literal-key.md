---
type: regex
pattern: 'Bearer sk-[A-Za-z0-9]{6,}'
match: not_contains
target: { source: file, path: triage.py }
arm: both
---
