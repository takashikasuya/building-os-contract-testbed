# Publication audit

Status: **BLOCKED** until the approvals in [release/approvals.yaml](../release/approvals.yaml) are recorded by a human.
Prepared 2026-11-22. This audit decides only what *may* be published. It publishes nothing.

## 1. Source inventory

| Item | Value |
|---|---|
| Source repository | `building-os-e2e` (private, GitHub visibility `PRIVATE`, no LICENSE file) |
| Default branch / commit | `bootstrap/initial-testbed` @ `e7e020dfa9ecf1df5afbcb555b84f3f055473943` (2026-11-22, merge of PR #73) |
| How it was read | `git fetch` followed by `git archive` / `git show` of that commit. The private working tree was not modified, so the local checkout is still 34 commits behind. |
| Not included | Draft PR #74 (PX4 stage 2, plant A live) and any other unmerged branch |
| Tracked files at the commit | 515 (101 verification reports, 25 preregistrations, 67 config proposals, ~150 scripts, 66 tests, manifest 286 kB) |
| Commits (all refs) | 429, by 2 author identities. The history is **not** exported. |
| Runtime dependencies of the source | pytest 9.1.1, PyYAML 6.0.3, rdflib 7.6.0, pyarrow 25.0.0, plus Go, .NET and TypeScript lab code and product checkouts |
| Runtime dependencies of this package | PyYAML (MIT), plus pytest (MIT) for tests |

## 2. Secret scan

| Scope | Tool | Result |
|---|---|---|
| Full history of the source (`git log --all -p`, 5.98 MB) | detect-secrets (via uvx) + regexes | 73 detector hits. **No real credential found.** The hits are sha256/SHA pins (45 hex), test fixtures (`hunter2`, `s3cr3t`, `fixture-only`, a dummy AWS-format key id, a dummy JWT, a private-key header string inside a redaction test), and names of secret *files* in lab code. |
| Sensitive file names ever committed (`*.pem`, `*.key`, `*.env`, `*.db`, `*credentials*`, …) | `git rev-list --all --objects` | none |
| This repository's tree | `tools/release_gate.py` | see the gate output (PASS on secrets at the time of writing) |

This scan is regex- and entropy-based. A real credential in an unusual format could still be missed. The history is not exported, which removes that risk for the public repository.

## 3. Classification

PUBLIC = may be published after the gate passes. REVIEW = staged here, but needs a recorded human decision. PRIVATE = never exported.

| Class | What | Why |
|---|---|---|
| PUBLIC | Ported contract predicates: `checks.py` (byte-identical), `layers.py`, `v3.py`, `lifecycle.py`, `suite.py` | Pure stdlib/PyYAML logic, written by the source repository's author, with no environment data |
| PUBLIC | Ported unit tests (synthetic traces) and new offline tests | Hand-written values only |
| PUBLIC | Authored docs, synthetic fixtures, release gate, CI | Written for this repository |
| REVIEW | 8 verification reports, 13 preregistrations, contract-suite README and YAML (redacted, numbers unchanged) | They support an **unpublished paper** (co-author disclosure). The suite YAML is derived from that paper's Table 5 and names test ids of third-party/owner repositories. |
| PRIVATE | Git history, branches, tags, issues, PRs | Constraint 2. History contains personal e-mail addresses and home paths. |
| PRIVATE | `manifest.yaml` | Approval records naming a person, local checkout paths, private repository URLs, image digests of the local lab |
| PRIVATE | `configs/proposals/**` (67) | Deployment and Safety profiles of the lab, approval hashes |
| PRIVATE | `scripts/*_lab/**`, `scripts/verify_*.py`, Go/.NET/TS lab code, Dockerfiles, compose files, `nats.conf`, `go.sum`, offline wheels | Require product checkouts, Docker networks or live stacks. 20 files carry RFC 1918 addresses of lab networks, 16 carry home-directory paths. |
| PRIVATE | `policies/**`, `.codex/**`, `.claude/**`, `AGENTS.md`, `CLAUDE.md`, `docs/agents/**` | Agent and tooling configuration of the private workspace |
| PRIVATE | `docs/approval/**`, the other 93 verification reports, plans, issue drafts, ADRs | Approval procedure records, internal planning, issue drafts for private trackers. These are not needed to verify the published contracts. |
| PRIVATE | `artifacts/`, logs, DBs, parquet, bundles, certificates, worktrees, product checkouts | Not tracked in the source. They are never exported. |

The machine-readable allowlist is [public-export.yaml](../public-export.yaml). The gate fails on any file that is not listed.

## 4. Rights inventory (not decided here)

| Material | Origin | Status |
|---|---|---|
| Testbed code, tests, reports | Author of the private repository. **Rights holder not confirmed** (personal vs. employer or organisation). | `copyright_holder`, `organization_publication_permission` pending |
| Contract model C(o) and Table 5 conditions | Unpublished paper (`bde-paper`, private) | `results_disclosure` pending |
| Contract suite test ids (`ri-unit:*`) | Building OS RI (`gutp-bim/gutp-building-os-ri`, public on GitHub; GitHub reports **no detected license**) | Only test *names* are cited, no code. `third_party_material` pending. |
| Test ids `tp:*` | tenant-portal (private) | names only. Pending. |
| Product names: BOPTEST, Nexus Gateway, Building OS RI, BDE, SBCO Data Model Builder, hvac-sim | respective owners | named for identification only (NOTICE.md) |
| Synthetic fixtures | written for this repository | no third-party data |
| Datasets, weather files, images, specifications | none exported | — |

## 5. Verified vs. unverified scope (B11, B12, B13, PX4)

See [results/summary.md](../results/summary.md) and [results/experiments.yaml](../results/experiments.yaml). In short:

- **B11**: offline re-judgment over private traces. It ran as preregistered (Pass). The layer logic is re-runnable here on synthetic traces. The recorded counts are not.
- **B12**: live injections. 11 Tested. R1/R2 attempts 1–2 were Not Tested (testbed defects) and attempt 3 was Tested. Not reproducible here.
- **B13**: scenarios 1/2/3/5 are an offline re-organisation (no pass/fail). For scenario 4, run 1 was Not Tested and the retry was Pass on BACnet reads. The plant-internal divergence is unresolved (hvac-sim #992).
- **PX4**: stage 1 exploratory (no pass/fail). Stage 2 offline is report-only. In stage 2 live, plant B passed questions 1 and 2. Plant A is **Not Tested** in this release, so questions 1–2 overall are Not Tested.

## 6. Decision

**Publication on hold (BLOCKED).** Technical checks can pass, but these items are unresolved: approval of the selected license (Apache-2.0 code, CC-BY-4.0 docs/results; texts added 2026-11-23), rights holder, organisation permission, co-author consent to disclose the results, third-party review, commit identity, and push/visibility approval.
