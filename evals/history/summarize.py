"""Summarise a `claude plugin eval --json <file>` result: one line per case and arm, with the graders that failed."""
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"duration {d['durationSeconds']} s, cost ${d['costUsd']:.2f}, partial={d['partial']}")
print(f"aggregates={d['aggregates']}")
for c in d["cases"]:
    print(f"\n{c['name']}: {c['aggregates']}")
    for arm, a in c["arms"].items():
        for r in a if isinstance(a, list) else a.get("runs", [a]):
            failed = [g["name"] for g in r.get("graders", []) if not g.get("passed")]
            notes = [
                f"{g['name']}: {g.get('reason', '')[:80]}"
                for g in r.get("graders", [])
                if g.get("type") == "llm" or "votes" in str(g.get("reason", ""))
            ]
            line = f"  {arm:8} score={r.get('score')} turns={r.get('turns')} cost=${r.get('costUsd', 0):.2f}"
            print(f"{line} failed={failed or '-'} | {'; '.join(notes)}")
