# Changelog

## 0.2.0 — 2026-10-14
- Example client is now a command: `snap_client.py request.json` (or `-` for stdin) sends one decision and prints
  the response JSON with `latency_ms`; `--demo` sends the built-in request; exit codes 0 / 1 (API or network) /
  2 (bad request file). The skill tells the agent to run it for one-off requests instead of writing glue code.
  Six new tests (18 in total).
- Skill: the Snap vs Jev table and benchmarks moved to `references/snap-vs-jev.md`, read only before a migration
  or a model choice (about 300 fewer words loaded on every use).
- Skill: Jev limits follow the reworded TypeSafe models page (per-request and per-question context, no separate
  limit on the number of questions); docs snapshot refreshed.
- Evals: new cases `photo-damage-no-host` (no host name in the prompt, images, 400/422 handling) and
  `quick-live-test` (bundled client behind the key wrapper); `jev-to-snap` facts checked by regex graders instead
  of one long llm rubric. Runs 1–7 with notes in `evals/history/LOG.md`.

## 0.1.1 — 2026-10-14
- Example client: no redirects (urllib forwarded the key to the redirect target), retries also on dropped
  connections, `attempts` validated, injectable I/O, 12 unit tests.
- Skill: question independence no longer stated as a SubQ-documented fact; SWE-bench figure 87.5%; note on redirects.
- Evals: `no-literal-key` grader catches any literal bearer token; run history in `evals/history/`.

## 0.1.0 — 2026-10-14
- First version: skill `subq`, example client, three eval cases.
