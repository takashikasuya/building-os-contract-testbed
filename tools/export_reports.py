"""Maintainer-only: import the allowlisted reports from the private source repository (public-export.yaml).

Third parties never need this script; tests, CI and the release gate work on this tree alone.

It reads each `transform: redact` file from a fixed commit with `git show <commit>:<path>` (the source working tree
is never read or modified), applies the redactions, rewrites relative Markdown links to files that are also imported,
turns links to non-imported files into plain text, and refuses to write when

  * the multiset of digit sequences changes (a number would have been altered), or
  * a forbidden token survives the redaction.

    python tools/export_reports.py --source /path/to/building-os-e2e --rules /path/to/building-os-e2e/public-export/redaction-rules.yaml [--check]

The rules file holds the concrete patterns (the identifiers being removed) and is kept outside this tree:

    redactions: [{category, pattern, replacement}, ...]
    forbidden_after_redaction: [token, ...]

`--check` recomputes everything and fails if a published file differs (no write).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / "public-export.yaml"
PROVENANCE = ROOT / "release/export-provenance.json"
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
DIGITS = re.compile(r"\d+")


def digits(text: str) -> Counter:
    return Counter(DIGITS.findall(text))


def redact(text: str, rules: list[dict]) -> tuple[str, dict]:
    counts = {}
    for rule in rules:
        counts[rule["category"]] = counts.get(rule["category"], 0) + text.count(rule["pattern"])
        text = text.replace(rule["pattern"], rule["replacement"])
    return text, counts


def relink(text: str, src: str, path_map: dict[str, str], dst: str) -> tuple[str, int, int]:
    rewritten = delinked = 0

    def sub(match):
        nonlocal rewritten, delinked
        label, target = match.group(1), match.group(2)
        if re.match(r"^[a-z]+://", target) or target.startswith("#") or target.startswith("mailto:"):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(src), path))
        if resolved in path_map:
            new = posixpath.relpath(path_map[resolved], posixpath.dirname(dst))
            rewritten += 1
            return f"[{label}]({new}{'#' + anchor if anchor else ''})"
        delinked += 1
        return f"{label} (`{target}`, not exported)"

    return LINK.sub(sub, text), rewritten, delinked


def build(source: Path, rules_path: Path) -> dict[str, dict]:
    spec = yaml.safe_load(ALLOWLIST.read_text())
    rules = yaml.safe_load(rules_path.read_text())
    if rules_path.resolve().is_relative_to(ROOT):
        raise SystemExit("the rules file must live outside the public tree")
    categories = {c["category"] for c in spec["redaction_categories"]}
    if {r["category"] for r in rules["redactions"]} - categories:
        raise SystemExit("a rule has a category not declared in public-export.yaml")
    commit = spec["source"]["commit"]
    items = [i for i in spec["imported"] if i["transform"] == "redact"]
    path_map = {i["src"]: i["dst"] for i in items}
    outputs = {}
    for item in items:
        raw = subprocess.run(["git", "-C", str(source), "show", f"{commit}:{item['src']}"], check=True,
                             capture_output=True).stdout
        original = raw.decode("utf-8")
        text, counts = redact(original, rules["redactions"])
        if item["dst"].endswith(".md"):
            text, rewritten, delinked = relink(text, item["src"], path_map, item["dst"])
        else:
            rewritten = delinked = 0
        if digits(text) != digits(original):
            missing = digits(original) - digits(text)
            extra = digits(text) - digits(original)
            raise SystemExit(f"{item['src']}: digit sequences changed (missing {dict(missing)}, extra {dict(extra)})")
        lowered = text.lower()
        for token in rules["forbidden_after_redaction"]:
            if token in lowered:
                raise SystemExit(f"{item['src']}: a forbidden token survives redaction; review by hand")
        outputs[item["dst"]] = {
            "text": text,
            "record": {"src": item["src"], "dst": item["dst"], "source_commit": commit,
                       "source_sha256": hashlib.sha256(raw).hexdigest(),
                       "published_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                       "redactions": {k: v for k, v in counts.items() if v}, "links_rewritten": rewritten,
                       "links_delinked": delinked, "digit_sequences_preserved": True}}
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, required=True, help="a clone of the private source repository")
    parser.add_argument("--rules", type=Path, required=True, help="private redaction rules (outside this tree)")
    parser.add_argument("--check", action="store_true", help="verify only; do not write")
    args = parser.parse_args()
    outputs = build(args.source, args.rules)
    records = [o["record"] for o in outputs.values()]
    if args.check:
        bad = [d for d, o in outputs.items() if not (ROOT / d).is_file() or (ROOT / d).read_text("utf-8") != o["text"]]
        print(json.dumps({"files": len(outputs), "differs": bad}, indent=1))
        return 1 if bad else 0
    for dst, out in outputs.items():
        path = ROOT / dst
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out["text"], encoding="utf-8")
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(json.dumps({"generated_by": "tools/export_reports.py", "files": records}, indent=1,
                                     ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} files; provenance in {PROVENANCE.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
