# SubQ agent skill

A [Claude Code](https://claude.com/claude-code) plugin with one skill, `subq`, that teaches an agent to use the
[SubQ Decisions API](https://docs.subq.ai) (SubQ Snap, model `subq-snap-preview`) correctly: question types
(noul / choice / score), the request contract, limits, errors and retries, how Snap differs from TypeSafe Jev,
and how to handle the API key. It mirrors the structure of TypeSafe's [`typesafe-ai` skill](https://github.com/typesafe-ai/skills).

The live docs (https://docs.subq.ai/llms.txt) are the source of truth; the skill points the agent there and
carries only facts verified against the docs or measured by the author (October 2026). Not affiliated with
Subquadratic or TypeSafe.

## Install

```bash
claude plugin marketplace add kprzybys/subq-skills
claude plugin install subq@subq-skills
```

Invoke explicitly with `/subq:subq`, or just ask, for example:

> Use SubQ Snap to route support tickets by team, with human review for uncertain cases.

`skills/subq/examples/snap_client.py` is a minimal standard-library client that follows the retry rules in the skill
(no redirects, bounded retries with jitter). Its tests: `cd skills/subq/examples && python3 -m unittest test_snap_client`.

## Evals

`evals/` holds `claude plugin eval` cases (ticket triage, Jev → Snap migration, question design); past runs and
observations are logged in `evals/history/LOG.md`. Run from the repository root (each run costs about $1.2):

```bash
claude plugin eval . --trust-plugin --allow-tools Write WebFetch --no-publish -j 3
```

## License

[MIT](LICENSE).
