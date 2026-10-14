# SubQ agent skill

A [Claude Code](https://claude.com/claude-code) plugin for developers who want their coding agent to use the
[SubQ Decisions API](https://docs.subq.ai) correctly.

## What SubQ Snap is

SubQ Snap (`subq-snap-preview`) is a **decision model**, not a text generator. You send it a `state` (text, JSON,
or up to 4 images) and named questions of three types, and it returns typed answers with probabilities:

- **noul**: a yes/no question, answered with the probability of "yes";
- **choice**: pick one of 2–255 named options, answered with the option, a probability per option and a confidence;
- **score**: a position on 2–10 ordered levels, answered with a probability-weighted score.

Your code owns the workflow and uses the probabilities to decide what happens next. It is the same request
contract as TypeSafe Jev, so the skill also covers moving between the two.

## Why the skill

Without it, an agent asked to "use SubQ Snap" guesses. In our baseline run it invented the endpoint
(`/v1/snap`), the model name (`snap`) and the request format (`input` / `question` / `choices`), sent three
requests per item instead of one, and never used the question types. Even with web access it tends to skip the
docs, split a 40-option choice into several requests, and present its own retry rules as the vendor's.

With the skill the agent reads the live docs first, uses the real contract and limits, designs the questions
properly (one judgment per question, one choice over a list instead of many yes/no questions, a no-match option),
retries only what the docs say to retry, keeps the key out of code and chat, and knows how Snap differs from Jev.
The `evals/` directory measures this; see [Development](#development).

## Example

Prompt to the agent:

> Triage support tickets with SubQ Snap: is it urgent, which team owns it, how severe is it. Flag uncertain cases.

Request the agent builds (one per ticket, three questions about the same state):

```json
{
  "model": "subq-snap-preview",
  "state": "Customer writes: my invoice shows a charge I never approved and the app crashes on login.",
  "questions": {
    "urgent":   { "type": "noul",   "instructions": "Does this ticket need a response within the hour?",
                  "criteria": { "true": "Outage, data loss, security issue or blocked payment",
                                "false": "Anything that can wait for the next business day" } },
    "team":     { "type": "choice", "instructions": "Which team should own this ticket?",
                  "criteria": { "billing": "Charges, invoices, refunds", "engineering": "Bugs, crashes, errors",
                                "sales": "Pricing, plans, upgrades", "other": null } },
    "severity": { "type": "score",  "instructions": "How badly is the customer blocked?",
                  "criteria": ["Cosmetic or a question", "Broken but there is a workaround", "Cannot use the product"] }
  }
}
```

Answer from the API (a real response, probabilities rounded; 246 input tokens, about 0.6 s):

```json
{ "answers": {
    "urgent":   { "type": "noul",   "noul": 0.81 },
    "team":     { "type": "choice", "choice": "billing", "confidence": 0.62,
                  "probabilities": { "billing": 0.71, "engineering": 0.21, "sales": 0.01, "other": 0.06 } },
    "severity": { "type": "score",  "score": 1.92, "confidence": 0.88,
                  "legend": { "0": "Cosmetic or a question", "1": "Broken but there is a workaround", "2": "Cannot use the product" },
                  "probabilities": { "0": 0.02, "1": 0.04, "2": 0.94 } } },
  "usage": { "input_tokens": 246, "output_tokens": 0 } }
```

What the code does with it: urgent (0.81 above the threshold set on labelled tickets) goes to the top of the queue;
the team choice has moderate confidence (0.62, billing 0.71 vs engineering 0.21), so whether it is auto-assigned or
sent to a person depends on the cutoff chosen on labelled data; severity rounds to level 2, "cannot use the product". `skills/subq/examples/snap_client.py` sends
exactly this request and follows the retry rules from the skill.

## Install

```bash
claude plugin marketplace add kprzybys/subq-skills
claude plugin install subq@subq-skills
```

Then just ask, for example "Use SubQ Snap to route support tickets by team, with human review for uncertain
cases", or invoke the skill explicitly with `/subq:subq`. The key is read from the `SUBQ_API_KEY` environment
variable; the skill never asks you to paste it.

Update later with `claude plugin marketplace update subq-skills` and `claude plugin update subq@subq-skills`.

> **Disclosure.** Not affiliated with Subquadratic or TypeSafe. The author is an early tester of SubQ Snap and takes
> part in SubQ's Snap creator challenge (which has prizes). The live docs (https://docs.subq.ai/llms.txt) are the
> source of truth; the skill carries only facts verified against them or measured by the author in October 2026
> ([snap-vs-jev-swe](https://github.com/kprzybys/snap-vs-jev-swe)).

## Development

To work on the skill, add the marketplace from a local clone (`claude plugin marketplace add ./subq-skills`);
Claude Code then reads the files from disk.

- **Tests and lint**: `cd skills/subq/examples && python3 -m unittest test_snap_client`, and
  `ruff check --select E,F,W,I,B,UP,N --line-length 120 skills scripts evals/history`. CI runs both plus
  `claude plugin validate .`.
- **Evals**: `evals/` holds `claude plugin eval` cases (ticket triage, Jev → Snap migration, question design).
  Each run costs about $1.2 per run per arm:

  ```bash
  claude plugin eval . --trust-plugin --allow-tools Write WebFetch --no-publish -j 3
  ```

  Past runs and what they showed are logged in `evals/history/LOG.md`.
- **Docs freshness**: `python3 scripts/check_docs.py` diffs the live SubQ and TypeSafe pages the skill relies on
  against `docs-snapshot/`. A weekly workflow does the same and opens an issue when a page changed. After
  re-reading a changed page and updating `SKILL.md`, run the script with `--update`.
- **Versioning**: bump `version` in `.claude-plugin/plugin.json` and add a `CHANGELOG.md` entry with every change
  to the skill text, so installed copies pick it up on `claude plugin update`.

## License

[MIT](LICENSE).
