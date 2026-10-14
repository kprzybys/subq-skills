"""Compare the live SubQ docs pages the skill relies on with the copies in docs-snapshot/.

Exit 0 when every page is identical, 1 when a page changed or could not be fetched (so CI fails and someone
re-reads the page and updates SKILL.md). `--update` rewrites the snapshot from the live pages.

Usage: python3 scripts/check_docs.py [--update]
"""

from __future__ import annotations

import difflib
import sys
import urllib.error
import urllib.request
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / "docs-snapshot"
PAGES = {
    "llms.txt": "https://docs.subq.ai/llms.txt",
    "endpoints_decisions-api.md": "https://docs.subq.ai/markdown/endpoints/decisions-api.md",
    "endpoints_models-api.md": "https://docs.subq.ai/markdown/endpoints/models-api.md",
    "using-the-api_models.md": "https://docs.subq.ai/markdown/using-the-api/models.md",
    "using-the-api_authentication.md": "https://docs.subq.ai/markdown/using-the-api/authentication.md",
    "using-the-api_data-retention.md": "https://docs.subq.ai/markdown/using-the-api/data-retention.md",
    "typesafe_models.md": "https://docs.typesafe.ai/models.md",
    "typesafe_api.md": "https://docs.typesafe.ai/api.md",
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "subq-skills docs check"})
    with urllib.request.urlopen(request, timeout=30) as r:
        return r.read().decode("utf-8")


def main(update: bool) -> int:
    SNAPSHOT.mkdir(exist_ok=True)
    changed = 0
    for name, url in PAGES.items():
        path = SNAPSHOT / name
        try:
            live = fetch(url)
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as e:
            print(f"FETCH FAILED {name}: {e}")
            changed += 1
            continue
        if update or not path.exists():
            path.write_text(live, encoding="utf-8")
            print(f"saved   {name}")
            continue
        old = path.read_text(encoding="utf-8")
        if old == live:
            print(f"same    {name}")
            continue
        changed += 1
        print(f"CHANGED {name} ({url})")
        diff = difflib.unified_diff(old.splitlines(), live.splitlines(), "snapshot", "live", lineterm="", n=1)
        print("\n".join(list(diff)[:80]))
    if changed and not update:
        print(f"\n{changed} page(s) changed or unavailable: re-read them and update SKILL.md, then run with --update.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(update="--update" in sys.argv[1:]))
