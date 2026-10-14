# Case log: the `subq` plugin with and without

Purpose: collect `claude plugin eval` runs and other observations, to judge later what the plugin really adds and
what needs fixing. Each entry: date, command, scores, what failed without the plugin, caveats. Raw data sits next to
the entry: `<date>-runN.json` (full result) and `<date>-runN-report.html` (report with answers and judge votes).
Summarise a JSON file with `python3 evals/history/summarize.py <file.json>`.

## 2026-10-14, run1 — first run after building the plugin (0.1.0)

Command: `claude plugin eval . --trust-plugin --allow-tools Write WebFetch --no-publish -j 3` (1 run per arm,
default judge = haiku, 3 votes). 163 s, $1.21. Claude Code 2.1.299.

| case | with plugin | without | what failed without the plugin |
|---|---|---|---|
| triage-tickets | 1.0 | 1.0 | nothing: the prompt names `api.subq.ai`, and the agent with WebFetch read the Decisions API page itself |
| jev-to-snap | 1.0 | 0.6 | Snap described correctly from the docs; on the Jev side "could not find the price or the limit" (both are on docs.typesafe.ai/models.md: $0.042, 64k/32k); retrying 429/503 called "my guess" although the SubQ docs state it |
| question-design | 1.0 | 0.0 | the agent did not use WebFetch, said it does not know SubQ, invented its own format (`binary`, `single_choice`, `rating`, `prompt`, `options`); assumed 40 options is "probably over the limit" (the limit is 255) and split the task into a shortlist of 8 or a 6-request tournament |

Mean Δ +0.47. "Skill fired" indicator in the with-arm: 3/3.

Baseline before the evals (a Sonnet agent, no network, no skill, same prompt as triage-tickets): endpoint `/v1/snap`,
model `snap`, request shape `input/question/choices`, 3 requests per ticket instead of 1, no noul/choice/score types.

Conclusions:
- The plugin gives (1) certainty that the agent reads the SubQ docs instead of guessing, (2) facts the agent does not
  assemble by itself: the comparison with Jev, the limits that shape question design (16 questions, 255 options), the retry rules.
- When the prompt names the API host and the agent has network access, the difference disappears (triage-tickets).

Caveats: one run per arm; the haiku judge voted FAIL once with the plugin too (jev-to-snap: PASS PASS FAIL); the prompts
and the skill were written by the same person (risk of teaching to the test).

Live test the same day: `skills/subq/examples/snap_client.py` run with the key injected by a wrapper → HTTP 200, 246 input tokens, 629 ms.

## 2026-10-14, run2 — after the code review (0.1.1)

Changes before the run (own review plus `/code-review` at high effort): the client no longer follows redirects (urllib
forwarded `Authorization` to another host; checked locally before and after), retries cover dropped connections
(`OSError`, `http.client.HTTPException`), `attempts<1` → `ValueError`, 12 unit tests (`test_snap_client.py`), ruff clean;
SKILL.md no longer states "questions cannot see each other's answers" as a fact (not in the SubQ docs), 87% → 87.5%;
the `no-literal-key` grader catches any literal token after `Bearer`, not only `sk-`.

Command as in the README, 1 run per arm. 192 s, $1.30.

| case | with plugin | without | notes |
|---|---|---|---|
| triage-tickets | 1.0 | 1.0 | as in run1 |
| jev-to-snap | 1.0 | 1.0 | **unlike run1 (0.6)**: this time the agent without the plugin found the Jev price and limit in the TypeSafe docs |
| question-design | 1.0 | 0.0 | as in run1: without the plugin the agent does not read the docs and invents a format |

Mean Δ +0.33 (run1: +0.47). Conclusion: the jev-to-snap gap without the plugin is luck (whether the agent lands on
the Models page of the TypeSafe docs); question-design is the stable case of plugin advantage. Single runs are not
enough for numbers; keep collecting runs in this file. Raw: `2026-10-14-run2.json`, `2026-10-14-run2-report.html`.

## 2026-10-14, run3x3 — three runs per arm, before publishing (0.1.1)

Command as in the README plus `--runs 3 -j 4`. 360 s, $3.85. Overall score 0.84, mean Δ +0.30.

| case | with plugin (3 runs) | without (3 runs) | notes |
|---|---|---|---|
| triage-tickets | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 | stable, no difference |
| jev-to-snap | 1.0, 0.6, 0.6 | 0.6, 0.6, 0.6 | without the plugin the Jev side (price, limit) was missing in all three runs this time |
| question-design | 0.33, 1.0, 1.0 | 0, 0, 0 | without the plugin: no docs read, invented format, every time |

**The with-arm failures were rubric rejections of correct answers, not skill errors** (checked by reading the
report): in jev-to-snap runs 2 and 3 the agent added a redirect guard around the call, which the skill (0.1.1)
recommends, and the rubric said "changes only the URL, model and key variable"; in question-design run 1 the agent
gave thresholds explicitly labelled as examples ("for example above 0.9"), and the rubric said "does not present a
fixed threshold". Both rubrics were reworded to allow exactly that (hardening around an unchanged request body;
example numbers marked as examples). This is a grader fix, not a loosening of the facts checked. Re-run follows
as run4x3. Raw: `2026-10-14-run3x3.json`, `2026-10-14-run3x3-report.html`.

## 2026-10-14, run4x3 — after the rubric fix, three runs per arm

351 s, $3.74. Overall 0.91, mean Δ +0.38.

| case | with plugin (3 runs) | without (3 runs) |
|---|---|---|
| triage-tickets | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 |
| jev-to-snap | 1.0, 0.6, 0.6 | 0.6, 0.6, 0.6 |
| question-design | 1.0, 1.0, 1.0 | 0, 0, 0 |

question-design is now stable at 3/3 with the plugin. jev-to-snap still loses `differences` in 2 of 3 with-runs,
and reading the rejected answers shows every required fact present and correct (384K vs 64k/32k, $0.05 vs $0.042,
`detail` body, 429/5xx vs 429/529, body unchanged, redirect guard added). The haiku judge fails long, list-shaped
answers, exactly what the Claude Code docs warn about ("llm judges are noisy on long inputs, prefer a regex grader").
Fix: the facts are now six `regex` graders on the final message (context sizes, both prices, `detail`, 5xx/529), and
the `llm` grader only checks that the request body is unchanged and that no contradicting figure or key appears.
Re-run of this case follows as run5. Raw: `2026-10-14-run4x3.json`, `2026-10-14-run4x3-report.html`.

## 2026-10-14, run5 — jev-to-snap only, regex fact graders, three runs per arm

162 s, $1.39. With plugin 1.0, 1.0, 1.0; without 1.0, 1.0, 1.0; Δ 0.

With deterministic graders the case no longer discriminates: an agent with WebFetch finds the Snap and Jev figures
by itself in most runs (in run1 it missed the Jev price once). Earlier "without" failures on this case were partly
judge noise too. Honest summary of what the evals show so far, 2026-10-14:

- **question-design** is the stable, measurable advantage: 3/3 with the plugin, 0/3 without, in every run.
  Without the plugin the agent does not read the docs, invents a question format and splits a 40-option choice.
- **triage-tickets** and **jev-to-snap** pass with and without, because the prompts name the API hosts and the agent
  has network access. Without network (the pre-eval baseline) the no-plugin agent invents endpoint, model and format.
- The plugin's remaining value in those two cases is not visible to the graders: it makes the agent read the docs
  every time instead of most times, and adds the redirect guard, the retry semantics and the calibration warning.

Next cases worth adding: a prompt without any host name ("use SubQ for ..."), an image request, a 400/422 handling
task, and a Jev → Snap migration judged on thresholds and calibration rather than on figures.
Raw: `2026-10-14-run5-jev-to-snap.json`, `2026-10-14-run5-jev-to-snap-report.html`.
