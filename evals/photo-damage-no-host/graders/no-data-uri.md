---
type: regex
pattern: 'data:image/'
match: not_contains
target: { source: file, path: check_photos.py }
---
