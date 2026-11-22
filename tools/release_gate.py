"""Release gate for the public repository. Runs on this tree alone (no private access).

Exit status: 0 PASS, 1 FAIL (a check failed), 2 BLOCKED (no check failed, but a required human approval is missing).
`--allow-blocked` turns BLOCKED into exit 0 for CI, never FAIL.

    python tools/release_gate.py [--allow-blocked] [--clean-install] [--out report.json]
    python tools/release_gate.py --update-manifest   # rewrite the file list and hashes of manifest.public.yaml
"""
from __future__ import annotations

import argparse
import fnmatch
from importlib import metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist", ".mypy_cache", ".ruff_cache"}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".cff", ".txt", ".cfg", ".ini", ""}

SECRET_PATTERNS = {
    "private key block": r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
    "AWS access key id": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "GitHub token": r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b",
    "Slack token": r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "OpenAI/Anthropic-style key": r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b",
    "JSON Web Token": r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
    "credential assignment": r"(?i)\b(?:password|passwd|client_secret|api_key|secret_key|access_token)\b\s*[:=]\s*['\"][^'\"\s]{6,}['\"]",
    "URL with credentials": r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@",
}
PRIVATE_PATTERNS = {
    "private IPv4 (RFC 1918)": r"(?<![\d.])(?:10\.(?:\d{1,3}\.){2}\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})(?![\d.])",
    "home directory path": r"(?:/home/[a-z][a-z0-9_-]*/|/Users/[A-Za-z][A-Za-z0-9_-]*/|C:\\\\Users\\\\)",
    "e-mail address": r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "internal hostname": r"\b[a-z0-9-]+\.(?:internal|corp|lan|intranet)\b",
}
ALLOWED_EMAILS = {"noreply@anthropic.com"}


def tree_files() -> list[str]:
    if (ROOT / ".git").exists():
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout.split("\n")
        return sorted(p for p in out if p and (ROOT / p).is_file())
    files = []
    for path in ROOT.rglob("*"):
        if path.is_file() and not any(part in SKIP_DIRS or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts):
            files.append(path.relative_to(ROOT).as_posix())
    return sorted(files)


def read_text(rel: str) -> str | None:
    path = ROOT / rel
    if path.suffix not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text("utf-8")
    except UnicodeDecodeError:
        return None


class Gate:
    def __init__(self):
        self.checks = []

    def add(self, name, status, details=None):
        self.checks.append({"check": name, "status": status, "details": details or []})

    @property
    def verdict(self):
        statuses = {c["status"] for c in self.checks}
        return "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"


MANIFEST = ROOT / "manifest.public.yaml"


def file_hashes(files):
    import hashlib
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files if f != "manifest.public.yaml"}


def update_manifest(files):
    doc = yaml.safe_load(MANIFEST.read_text())
    doc["files"] = file_hashes(files)
    header = MANIFEST.read_text().split("\n# --- generated below")[0]
    MANIFEST.write_text(header + "\n# --- generated below by tools/release_gate.py --update-manifest ---\n"
                        + yaml.safe_dump({"files": doc["files"]}, sort_keys=True, allow_unicode=True))


def check_manifest(gate, files):
    recorded = (yaml.safe_load(MANIFEST.read_text()) or {}).get("files") or {}
    actual = file_hashes(files)
    diff = sorted(f"{f}: {'missing from manifest' if f not in recorded else 'hash differs'}" for f in actual if recorded.get(f) != actual[f])
    diff += sorted(f"{f}: listed but absent" for f in recorded if f not in actual)
    gate.add("manifest.public.yaml: file list and sha256 match the tree", "FAIL" if diff else "PASS", diff)


def check_allowlist(gate, files, spec):
    allowed = {i["dst"] for i in spec["imported"]}
    patterns = [a.split("#")[0].strip() for a in spec["authored"]]
    unlisted = [f for f in files if f not in allowed and not any(fnmatch.fnmatchcase(f, p) for p in patterns)]
    missing = sorted(a for a in allowed if not (ROOT / a).is_file())
    missing += sorted(p for p in patterns if not any(fnmatch.fnmatchcase(f, p) for f in files))
    gate.add("allowlist: every file is listed", "FAIL" if unlisted else "PASS", unlisted)
    gate.add("allowlist: every listed file exists", "FAIL" if missing else "PASS", missing)
    review = sorted(i["dst"] for i in spec["imported"] if i.get("class") == "REVIEW")
    gate.add("allowlist: REVIEW-class files need a recorded disclosure approval", "INFO", review)


def forbidden_hits(line: str, hashed: list[dict]) -> int:
    import hashlib
    wanted = {(h["length"], h["sha256"]) for h in hashed}
    lengths = {h["length"] for h in hashed}
    hits = 0
    for run in re.findall(r"[a-z0-9]+", line.lower()):
        for n in lengths:
            for i in range(len(run) - n + 1):
                if (n, hashlib.sha256(run[i:i + n].encode()).hexdigest()) in wanted:
                    hits += 1
    return hits


def scan(gate, files, spec):
    secrets, private, forbidden = [], [], []
    hashed = spec["forbidden_token_sha256"]
    for rel in files:
        text = read_text(rel)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, line):
                    secrets.append(f"{rel}:{lineno}: {name}")
            for name, pattern in PRIVATE_PATTERNS.items():
                for m in re.finditer(pattern, line):
                    if name == "e-mail address" and m.group(0) in ALLOWED_EMAILS:
                        continue
                    private.append(f"{rel}:{lineno}: {name}: {m.group(0)}")
            if forbidden_hits(line, hashed):
                forbidden.append(f"{rel}:{lineno}: a forbidden identifier (matched by sha256)")
    gate.add("secret scan (working tree)", "FAIL" if secrets else "PASS", secrets)
    gate.add("private URL / internal IP / personal data scan", "FAIL" if private else "PASS", private)
    gate.add("redaction: forbidden identifiers absent", "FAIL" if forbidden else "PASS", forbidden)


def check_links(gate, files):
    broken = []
    link = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)")
    for rel in files:
        if not rel.endswith(".md"):
            continue
        for lineno, line in enumerate((ROOT / rel).read_text("utf-8").splitlines(), 1):
            for target in link.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                path = target.split("#")[0]
                if not (ROOT / rel).parent.joinpath(path).resolve().exists():
                    broken.append(f"{rel}:{lineno}: {target}")
    gate.add("documentation: relative links resolve", "FAIL" if broken else "PASS", broken)


def check_results(gate):
    doc = yaml.safe_load((ROOT / "results/experiments.yaml").read_text())
    problems = []
    for e in doc["experiments"]:
        for r in e["results"]:
            text = (ROOT / doc["reports_root"] / r["source"]).read_text("utf-8")
            if r["quote"] not in text:
                problems.append(f"{e['id']}: quote not in {r['source']}")
            if r["status"] not in {"Pass", "Fail", "Skip", "Not Tested", "Not Applicable"}:
                problems.append(f"{e['id']}: status {r['status']!r}")
            if r["status"] == "Pass" and re.search(r"Not Tested|Skip|not executed", r["item"].replace("is Not Tested)", "")):
                problems.append(f"{e['id']}: an unexecuted item is marked Pass: {r['item']}")
        if e["reproducibility"] == "live" and "offline-public" in json.dumps(e):
            problems.append(f"{e['id']}: live experiment claims offline reproducibility")
    prov = json.loads((ROOT / "release/export-provenance.json").read_text())
    import hashlib
    for f in prov["files"]:
        if hashlib.sha256((ROOT / f["dst"]).read_bytes()).hexdigest() != f["published_sha256"]:
            problems.append(f"{f['dst']}: differs from the exported (redacted) report")
    gate.add("results: traceable to reports; strict Pass/Fail/Skip/Not Tested; no live claim of reproducibility",
             "FAIL" if problems else "PASS", problems)


def check_licenses(gate, approvals):
    license_file = next((p for p in ("LICENSE", "LICENSE.md", "LICENSE.txt") if (ROOT / p).is_file()), None)
    chosen = (approvals.get("license") or {}).get("spdx")
    if not license_file or not chosen:
        gate.add("license: LICENSE file present and selected by the rights holder", "BLOCKED",
                 [f"LICENSE file: {license_file or 'absent'}", f"approved SPDX id: {chosen or 'none'}",
                  "candidates: docs/license-candidates.md"])
    else:
        gate.add("license: LICENSE file present and selected by the rights holder", "PASS", [license_file, chosen])
    permissive = {"MIT", "MIT License", "BSD", "BSD License", "Apache-2.0", "Apache Software License", "PSF", "ISC"}
    deps = []
    for name in ("PyYAML", "pytest"):
        try:
            meta = metadata.metadata(name)
            lic = meta.get("License-Expression") or meta.get("License") or ""
            classifiers = [c.split(" :: ")[-1] for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
            deps.append({"package": name, "version": meta["Version"], "license": lic[:40], "classifiers": classifiers})
        except metadata.PackageNotFoundError:
            deps.append({"package": name, "version": None, "license": "not installed", "classifiers": []})
    bad = [d for d in deps if not ({d["license"], *d["classifiers"]} & permissive)]
    gate.add("dependency licenses are permissive (compatible with every candidate)",
             "FAIL" if bad else "PASS", deps)


def check_tests(gate, clean_install):
    if clean_install:
        with tempfile.TemporaryDirectory() as tmp:
            venv = Path(tmp) / "venv"
            steps = [[sys.executable, "-m", "venv", str(venv)],
                     [str(venv / "bin/python"), "-m", "pip", "install", "-q", "-e", f"{ROOT}[test]"],
                     [str(venv / "bin/python"), "-m", "pytest", "-q", "tests/offline", "tests/contract"]]
            for step in steps:
                proc = subprocess.run(step, cwd=ROOT, capture_output=True, text=True)
                if proc.returncode:
                    gate.add("clean-environment install and offline tests", "FAIL", [" ".join(step[-3:]), proc.stdout[-2000:], proc.stderr[-2000:]])
                    return
            gate.add("clean-environment install and offline tests", "PASS", [proc.stdout.strip().splitlines()[-1]])
            return
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/offline", "tests/contract"], cwd=ROOT,
                          capture_output=True, text=True)
    tail = proc.stdout.strip().splitlines()[-1:] if proc.stdout.strip() else [proc.stderr[-500:]]
    gate.add("offline tests (current environment)", "FAIL" if proc.returncode else "PASS", tail)
    gate.add("clean-environment install", "INFO", ["not run here; pass --clean-install (CI installs from scratch)"])


def check_git(gate):
    if not (ROOT / ".git").exists():
        gate.add("git: history starts from a new root commit", "BLOCKED", ["repository not initialised"])
        return
    run = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
    roots = run("rev-list", "--max-parents=0", "HEAD").stdout.split()
    remotes = run("remote").stdout.split()
    identities = sorted(set(run("log", "--format=%an <%ae>", "HEAD").stdout.splitlines()))
    gate.add("git: history starts from a single new root commit", "PASS" if len(roots) == 1 else "FAIL", roots)
    gate.add("git: no remote configured before approval", "PASS" if not remotes else "INFO", remotes)
    gate.add("git: commit identities to be published (needs approval)", "INFO", identities)


def check_approvals(gate, approvals):
    pending = [k for k, v in approvals.items() if k != "schema_version" and not (isinstance(v, dict) and v.get("approved") is True)]
    gate.add("human approvals recorded (release/approvals.yaml)", "BLOCKED" if pending else "PASS", pending)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--allow-blocked", action="store_true")
    parser.add_argument("--clean-install", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--update-manifest", action="store_true")
    args = parser.parse_args()
    spec = yaml.safe_load((ROOT / "public-export.yaml").read_text())
    approvals = yaml.safe_load((ROOT / "release/approvals.yaml").read_text()) or {}
    files = tree_files()
    if args.update_manifest:
        update_manifest(files)
        print(f"manifest.public.yaml: {len(files) - 1} files")
        return 0
    gate = Gate()
    check_allowlist(gate, files, spec)
    check_manifest(gate, files)
    scan(gate, files, spec)
    check_links(gate, files)
    check_results(gate)
    check_licenses(gate, approvals)
    check_tests(gate, args.clean_install)
    check_git(gate)
    check_approvals(gate, approvals)
    report = {"verdict": gate.verdict, "files": len(files), "checks": gate.checks}
    text = json.dumps(report, indent=1, ensure_ascii=False)
    if args.out:
        args.out.write_text(text + "\n")
    for c in gate.checks:
        print(f"[{c['status']:7}] {c['check']}")
        for d in c["details"][:15] if c["status"] in {"FAIL", "BLOCKED"} else []:
            print(f"           - {d}")
    print(f"\nVERDICT: {gate.verdict}")
    if gate.verdict == "FAIL":
        return 1
    if gate.verdict == "BLOCKED":
        return 0 if args.allow_blocked else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
