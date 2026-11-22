# License candidates and rights record

**Selected 2026-11-23: option A, Apache-2.0 for code and CC-BY-4.0 for docs, results, fixtures and data** (see the
README for the file-level split). `LICENSE` and `LICENSES/CC-BY-4.0.txt` hold the texts. Rights holder: Takashi KASUYA
(confirmed by the author, 2026-11-23). Approvals are recorded in [release/approvals.yaml](../release/approvals.yaml).

## Facts established

| Question | Finding |
|---|---|
| License of the source repository | none (no LICENSE file; GitHub `licenseInfo: null`) |
| Rights holder | Takashi KASUYA (personal), confirmed by the author on 2026-11-23 |
| Third-party code copied | none. `checks.py`, `layers.py`, `v3.py`, `lifecycle.py`, `suite.py` and the ported tests come from the private testbed itself. |
| Third-party text cited | test *identifiers* of Building OS RI (public repository, no license detected) and tenant-portal (private), inside the suite YAML |
| Unpublished work | the contract model's Table 5 and the experiment results support an unpublished paper |
| Dependencies | PyYAML (MIT), pytest (MIT), both permissive |

## Candidates (for the rights holder to choose)

| Option | Code | Docs, results, fixtures | Notes |
|---|---|---|---|
| A | Apache-2.0 | CC-BY-4.0 | explicit patent grant; common for research software with separate data/docs license |
| B | MIT | CC-BY-4.0 | shortest; no patent clause |
| C | BSD-3-Clause | CC-BY-4.0 | close to BOPTEST's family of licenses (BOPTEST license not verified here) |

### Recommendation (adopted 2026-11-23)

**Option A: Apache-2.0 for code, CC-BY-4.0 for docs, results and fixtures.** Reasons:

- The commit identity is an organisational address. Corporate legal reviews usually prefer Apache-2.0: it has an
  explicit patent grant and patent-retaliation clause, and its NOTICE mechanism fits the existing `NOTICE.md`.
- Splitting code and documentation lets third parties reuse the reports and the contract suite with attribution,
  while the reports keep their author credit (the results support a paper).
- It is compatible with the MIT-licensed dependencies and with permissive licenses used nearby in the building-data
  ecosystem (e.g. BSD-style licenses). Those licenses were not verified here.

If it is chosen, the rights holder adds `LICENSE` (Apache-2.0 text), `LICENSES/CC-BY-4.0.txt`, a copyright line in
`NOTICE.md`, `license = "Apache-2.0"` in `pyproject.toml`, `license: Apache-2.0` in `CITATION.cff`, and records the
choice in `release/approvals.yaml`.

All three are compatible with the dependencies. Whatever is chosen, the cited test identifiers of other projects
remain names, not licensed content. Each owning project should still confirm that citing them is acceptable.

## Checklist before choosing

- [x] Rights holder identified (person or organisation), with the basis (employment or contract terms)
- [x] Organisations with a claim agree to publication (employer, GUTP consortium if applicable, funders)
- [x] Co-authors of the unpublished paper agree to disclose the contract suite and results before publication
- [x] Owners of Building OS RI and tenant-portal have no objection to the cited test identifiers
- [x] License for code and for docs/results selected; LICENSE file added; `pyproject.toml` and `CITATION.cff` updated
