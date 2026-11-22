# Security policy

## Scope

This repository holds offline predicates, synthetic fixtures and documents. It opens no network connection, needs no
credentials and controls no equipment. Its test suite runs fully offline.

It must never contain credentials, certificates, private keys, tokens, internal endpoints or addresses, or records
from real buildings. `tools/release_gate.py` scans every tracked file for these before a release, and CI runs the same
scan on every push.

## Reporting

Use GitHub's private vulnerability reporting: "Report a vulnerability" under the repository's Security tab. Do not
open a public issue for a suspected leak of credentials or internal information.

Please include the file, the line, and why you believe it is sensitive. A suspected leak is handled by removing the
material, rotating any affected credential in the owning system, and rewriting history if needed.

## Not in scope

Vulnerabilities of BOPTEST, Nexus Gateway, Building OS RI, BDE or other products belong to their own projects.
