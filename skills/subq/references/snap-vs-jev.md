# SubQ Snap vs TypeSafe Jev

Snap and Jev speak the same `POST /v1/systemone` contract: `model`, `state`,
named `questions` of type noul / choice / score with `instructions` and
`criteria`. Moving between them is a change of URL, model ID and key variable,
plus the differences below. Facts marked *docs* are from the vendors'
documentation; facts marked *measured* come from the author's benchmarks
(October 2026, single runs, public datasets; code and numbers at
https://github.com/kprzybys/snap-vs-jev-swe).

| | SubQ Snap | TypeSafe Jev |
| --- | --- | --- |
| Endpoint | `https://api.subq.ai/v1/systemone` | `https://api.typesafe.ai/v1/systemone` |
| Model ID | `subq-snap-preview` | `jev-latest` (alias of `jev-1.13.0`) |
| Key variable | `SUBQ_API_KEY` | `TYPESAFE_API_KEY` |
| Context (*docs*) | 384K tokens per request | 64k per request (state plus all questions); 32k per question (state plus any one question) |
| Questions per request (*docs*) | 1–16 | no separate limit; the request must fit both context limits |
| Images (*docs*) | up to 4 | text only |
| Price (*docs*) | $0.05 / 1M input tokens, output free | $0.042 / 1M input tokens, output free |
| Error body (*docs*) | `{"detail": {"error_type", "message"}}` | HTTP status with a JSON body |
| Retry (*docs*) | 429, 5xx | 429, 529 |
| Median latency (*measured*, 8,631 short cases) | 453 ms | 255 ms |
| Accuracy (*measured*) | a few points higher on most classification sets; biggest edge where one request must read a lot (SWE-bench file localisation with 10 whole files, ~71k tokens: 87.5%) | cannot take inputs above its context limit |

Rules of thumb from those measurements: pick Snap when accuracy or long
context matters; pick Jev when latency or cost per call matters. Thresholds
tuned for one model do not transfer to the other; recalibrate on your data.
TypeSafe's own skill (`typesafe-ai`) and docs (https://docs.typesafe.ai/llms.txt)
cover Jev; this skill covers SubQ.
