---
type: llm
weight: 2
focus: { source: file, path: check_photos.py }
---

You are grading a Python script that sends product-return photos to the SubQ Decisions API.

PASS only if ALL of the following hold:
1. One request per return: a JSON body with `model`, `state`, a `questions` object and an `images` list holding all of that return's photos (never more than 4), each image as plain base64 with its media type (no `data:` URI prefix). One request per photo is a FAIL.
2. The questions are typed: a noul for whether the product is damaged, and the damage type either as a choice that includes a no-match or "none/other" option, or as one noul per damage type (damage types can co-occur, so both are correct). Extra nouls (for example "is the product clearly visible") are fine. Answers are read from `answers.<question name>`.
3. Video is not sent as video: the script samples at most 4 frames as images, or rejects/flags video for a person.
4. Retries happen only for HTTP 429 and 5xx (and timeouts or dropped connections), with backoff; 400 and 422 are not retried and are reported (for example oversized or invalid images), and 401/402/403 stop.
5. Uncertain results (a noul near 0.5 or low `confidence`) go to a person.

FAIL if any item is missing or if the script uses an OpenAI-style chat request, a made-up endpoint or model name, or embeds a key.
