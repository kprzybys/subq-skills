# SubQ agent skill

A [Claude Code](https://claude.com/claude-code) plugin with one skill, `subq`, that teaches an agent to use the
[SubQ Decisions API](https://docs.subq.ai) (SubQ Snap, model `subq-snap-preview`) correctly: question types
(noul / choice / score), the request contract, limits, errors and retries, how Snap differs from TypeSafe Jev,
and how to handle the API key. It mirrors the structure of TypeSafe's [`typesafe-ai` skill](https://github.com/typesafe-ai/skills).

The live docs (https://docs.subq.ai/llms.txt) are the source of truth; the skill points the agent there and
carries only facts verified against the docs or measured by the author (October 2026). A weekly workflow compares
the pages the skill relies on with `docs-snapshot/` and opens an issue when they change.

> **Disclosure.** Not affiliated with Subquadratic or TypeSafe. The author is an early tester of SubQ Snap and takes
> part in SubQ's Snap creator challenge (which has prizes). The measurements quoted in the skill are the author's own
> ([snap-vs-jev-swe](https://github.com/kprzybys/snap-vs-jev-swe)).

## Install

```bash
claude plugin marketplace add kprzybys/subq-skills
claude plugin install subq@subq-skills
```

Update later with `claude plugin marketplace update subq-skills` and `claude plugin update subq@subq-skills`.
To work on the skill itself, add the marketplace from a local clone instead (`claude plugin marketplace add ./subq-skills`);
Claude Code then reads the files from disk.

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

## Keeping it current

- `python3 scripts/check_docs.py` diffs the live docs against `docs-snapshot/`; after re-reading a changed page and
  updating `SKILL.md`, run it with `--update`.
- `CHANGELOG.md` lists what changed per version; bump `version` in `.claude-plugin/plugin.json` with every change
  to the skill text, so installed copies pick it up on `claude plugin update`.

## License

[MIT](LICENSE).
