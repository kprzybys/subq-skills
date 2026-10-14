---
type: regex
pattern: 'Bearer\s+[A-Za-z0-9_.\-]{12,}'
match: not_contains
target: { source: file, path: triage.py }
arm: both
---
