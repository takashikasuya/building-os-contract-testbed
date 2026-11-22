"""The release gate's scanners detect what they claim to. Sample secrets are assembled at run time so that this file
itself never contains one."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import release_gate as gate  # noqa: E402


def matches(patterns, text):
    return {name for name, pattern in patterns.items() if re.search(pattern, text)}


def test_secret_patterns_detect_samples():
    samples = {
        "private key block": "-----BEGIN " + "PRIVATE KEY-----",
        "AWS access key id": "AKIA" + "Z" * 16,
        "GitHub token": "ghp_" + "a1" * 18,
        "credential assignment": "password" + ' = "' + "x" * 8 + '"',
        "URL with credentials": "https://" + "user:pw" + "@host/x",
    }
    for name, text in samples.items():
        assert name in matches(gate.SECRET_PATTERNS, text), name


def test_private_patterns_detect_samples_and_skip_versions():
    assert "private IPv4 (RFC 1918)" in matches(gate.PRIVATE_PATTERNS, "addr " + "192.168" + ".1.20")
    assert "private IPv4 (RFC 1918)" in matches(gate.PRIVATE_PATTERNS, "172.20" + ".0.3")
    assert "home directory path" in matches(gate.PRIVATE_PATTERNS, "/home" + "/someone/x")
    assert not matches(gate.PRIVATE_PATTERNS, "version 10.0.1 and 0.095 % and sha 8c87146")


def test_forbidden_tokens_are_matched_by_hash_inside_longer_words():
    import hashlib
    token = "zq" + "xwvu"  # a stand-in; the real tokens are only known by their hashes
    hashed = [{"length": len(token), "sha256": hashlib.sha256(token.encode()).hexdigest()}]
    assert gate.forbidden_hits("prefix" + token.upper() + "suffix", hashed) == 1
    assert gate.forbidden_hits("unrelated text", hashed) == 0
