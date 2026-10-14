# Changelog

## Unreleased
- Skill: the Snap vs Jev table and benchmarks moved to `references/snap-vs-jev.md`; SKILL.md keeps the switch
  summary and says when to read the reference (about 300 fewer words loaded on every use).
- Example client is now a command: `snap_client.py request.json|-` prints the response JSON, `--demo` sends the
  built-in request, exit codes 0/1/2; the skill tells the agent to use it instead of writing glue code; 6 new tests.
- Skill: Jev limits follow the reworded TypeSafe models page (per-request and per-question context, no separate
  limit on the number of questions); docs snapshot refreshed.
- Evals: `jev-to-snap` facts checked by regex graders instead of one long llm rubric (the haiku judge rejected
  correct answers); rubric wording no longer penalises a redirect guard or example thresholds; run history in
  `evals/history/LOG.md` (five runs on 2026-10-14).

## 0.1.1 — 2026-10-14
- Example client: no redirects (urllib forwarded the key to the redirect target), retries also on dropped
  connections, `attempts` validated, injectable I/O, 12 unit tests.
- Skill: question independence no longer stated as a SubQ-documented fact; SWE-bench figure 87.5%; note on redirects.
- Evals: `no-literal-key` grader catches any literal bearer token; run history in `evals/history/`.

## 0.1.0 — 2026-10-14
- First version: skill `subq`, example client, three eval cases.
