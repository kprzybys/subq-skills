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
sent to a person depends on the cutoff chosen on labelled data; severity rounds to level 2, "cannot use the product". `python3 skills/subq/examples/snap_client.py --demo`
sends exactly this request and follows the retry rules from the skill. To send your own, put `state` and
`questions` in a JSON file (or pipe it on stdin); the full response JSON goes to stdout:

```bash
echo '{"state": "The kettle arrived cracked. I want my money back.",
       "questions": {"refund": {"type": "noul", "instructions": "Does the customer ask for a refund?"}}}' \
  | python3 skills/subq/examples/snap_client.py -
```

## Day-to-day uses from Claude Code

Each scenario: the situation, the Snap question(s), and what the agent or a hook does with the probability.
"Measured" points to our own numbers; "untested" means it follows from the contract but we have not run it.

1. **Which file holds the bug** (measured). Before reading a repository for a reported issue, the agent sends the
   issue text plus each candidate file (path, header, or the whole file) and asks one **noul** per file, "must this
   file change to fix the issue?", or one **choice** over all candidates in a single request. It then reads the top
   files first. On 200 SWE-bench Verified issues with 10 candidates: top-1 85.5% per file (AUROC 0.98), 87.5% with all
   10 files in one request (~71k tokens). Details in [snap-vs-jev-swe](https://github.com/kprzybys/snap-vs-jev-swe).
2. **Triage of CI failures and issues** (untested). For each failure: a **choice** "which area or team" and a
   **noul** "is this a flaky test rather than a regression". Above a confidence cutoff set on past, labelled failures
   the agent proceeds on its own; below it, it asks a person instead of guessing.
3. **A gate before `git commit`** (untested as a hook; one question costs a fraction of a cent and takes under a
   second). A Claude Code `PreToolUse` hook on `git commit` sends the staged diff and the message and asks a **noul**
   "does the message describe this diff?" and another "does the diff touch authentication or payments?". A low
   first answer or a high second one makes the hook exit with code 2, which blocks the command and shows the reason
   to the agent. Sketch: the hook script reads the diff with `git diff --cached`, calls `snap_client.decide`, and
   prints the reason to stderr.
4. **Checking the agent's own claims** (measured on Jev, same contract; Snap untested). Before reporting, the agent
   pairs each claim about the system ("the tests pass", "the endpoint returns 200") with the tool output from the
   same turn and asks one **choice**: supports / contradicts / says nothing. "Contradicts" or "says nothing" means
   the claim is reworded as unverified. With Jev this separated supported from unsupported claims in 34 of 34 cases
   in a one-session trial, in about 260 ms per claim.
5. **Tagging thousands of notes, mails or messages** (classification measured on public datasets; your labels
   untested). A **choice** from a closed label list and a **score** for urgency, in batches, at $0.05 per 1M input
   tokens: a thousand 500-token notes cost about 2.5 cents. The agent gets a ready list instead of reading everything,
   and Snap gave identical answers on repeated identical requests within a day in our runs.
6. **Does a docs change touch the API contract?** (idea). The weekly docs-freshness workflow in this repository
   only diffs pages. A **noul** over the diff, "does this change alter the request or response contract, limits or
   pricing?", would separate wording changes from ones that need an edit to the skill.

Two limits apply to all of them. Everything in `state` goes to the SubQ API, so do not send private code or data
without agreement and the right data-retention setting (zero data retention is enabled per organisation on request).
And Snap only judges: writing the summary, the commit message or the explanation stays with an LLM.

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
- **Evals**: `evals/` holds `claude plugin eval` cases (ticket triage, Jev → Snap migration, question design,
  photo damage check without a host name, quick live test). One run costs about $1.2 per arm:

  ```bash
  claude plugin eval . --trust-plugin --allow-tools Write WebFetch --no-publish -j 3
  ```

  `quick-live-test` also needs `Bash` in `--allow-tools`; the eval sandbox refuses Bash on a machine whose
  `~/.ssh` contains a symbolic link.

  Past runs and what they showed are logged in `evals/history/LOG.md`.
- **Docs freshness**: `python3 scripts/check_docs.py` diffs the live SubQ and TypeSafe pages the skill relies on
  against `docs-snapshot/`. A weekly workflow does the same and opens an issue when a page changed. After
  re-reading a changed page and updating `SKILL.md`, run the script with `--update`.
- **Versioning**: bump `version` in `.claude-plugin/plugin.json` and add a `CHANGELOG.md` entry with every change
  to the skill text, so installed copies pick it up on `claude plugin update`.

## License

[MIT](LICENSE).
