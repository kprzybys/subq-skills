---
runs: 1
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, WebFetch, Write]
expected_outcome: check_photos.py sends one Snap request per return with all photos (at most 4) as plain base64 images, a noul for "damaged" and the damage type as a choice with a no-match option or one noul per type; retries only 429/5xx, does not retry 400/422 and reports them; key from SUBQ_API_KEY; uncertain cases go to a person.
---

Customers attach up to 3 photos when they return a product. Use SubQ to decide, for each return, whether the photos show a damaged product and, if so, what kind of damage it is (cracked, scratched, dented, missing part). Write `check_photos.py` in the current directory that takes a folder of JPEG/PNG files per return. Some returns may come with a short video instead of photos. Make it robust to API errors, and say which errors it retries and which it does not. Uncertain cases should go to a person. You have no API key here, so do not run it; just write the script and tell me briefly what request format you used.
