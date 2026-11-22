# License candidates and rights record

**No license has been chosen.** Choosing one is the rights holder's decision. Record it in
[release/approvals.yaml](../release/approvals.yaml) and add a `LICENSE` file. Until then, the release gate reports
BLOCKED.

## Facts established

| Question | Finding |
|---|---|
| License of the source repository | none (no LICENSE file; GitHub `licenseInfo: null`) |
| Rights holder | **not confirmed**. Commits use one person's identities, but employment or organisation terms may give the rights to someone else. Not inferred. |
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

All three are compatible with the dependencies. Whatever is chosen, the cited test identifiers of other projects
remain names, not licensed content. Each owning project should still confirm that citing them is acceptable.

## Checklist before choosing

- [ ] Rights holder identified (person or organisation), with the basis (employment or contract terms)
- [ ] Organisations with a claim agree to publication (employer, GUTP consortium if applicable, funders)
- [ ] Co-authors of the unpublished paper agree to disclose the contract suite and results before publication
- [ ] Owners of Building OS RI and tenant-portal have no objection to the cited test identifiers
- [ ] License for code and for docs/results selected; LICENSE file added; `pyproject.toml` and `CITATION.cff` updated
